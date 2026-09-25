import os
import json
import time
from typing import Dict, Any, List
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from services.spatial_analysis_agent.post_processors import get_processor
from shared.schemas.tool import ToolResult
from shared.schemas.map import MapLayerSpecification
from shared.observability.logger import get_logger
from shared.observability.audit_logger import log_data_access
from data.database import get_postgis_db, get_enc_db, get_s101_db
from services.spatial_analysis_agent.tool_registry import get_query_template
from services.spatial_analysis_agent.overlay_highlighter import apply_overlay_highlight

logger = get_logger("spatial_analysis_agent.tool_executor")

# Load Layer Registry
import yaml
LAYER_REGISTRY = {}
registry_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "layer_registry.yaml")
if os.path.exists(registry_path):
    try:
        with open(registry_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if data and "layers" in data:
                LAYER_REGISTRY = data["layers"]
        logger.info(f"Loaded Layer Registry from {registry_path}")
    except Exception as e:
        logger.error("Failed to load Layer Registry", error=str(e))

# 파일 저장 경로 설정 (대용량 데이터 대응)
RESULTS_DIR = os.path.join(os.environ.get("APP_DATA_DIR", "/tmp"), "geollm_results")
os.makedirs(RESULTS_DIR, exist_ok=True)

def execute_spatial_tool(dsl: Any, trace_id: str, task_id: str, user_id: str = "system", clearance_level: str = "PUBLIC") -> ToolResult:
    """
    DSL을 입력받아 검증된 Tool Registry 쿼리를 실행하고 대용량 파일 기반 응답을 생성합니다.
    """
    start_time = time.time()
    qec_payload = {}
    if hasattr(dsl, "conditions") and isinstance(getattr(dsl, "conditions", None), dict):
        qec_payload = dsl.conditions.get("_query_execution_context") or {}
    
    # 보안 등급 매핑
    clearance_map = {"PUBLIC": 1, "RESTRICTED": 2, "SECRET": 3}
    user_lvl = clearance_map.get(clearance_level.upper(), 1)
    
    features: List[Dict[str, Any]] = []
    
    from services.spatial_analysis_agent.schemas import QueryPlan
    if isinstance(dsl, QueryPlan):
        tool_name_map = {
            "feature_dwithin": "postgis.dwithin",
            "feature_search_by_radius": "postgis.dwithin",
            "feature_within_area": "postgis.intersection",
        }
        tool_name = tool_name_map.get(dsl.analysis_type, dsl.analysis_type)
        target_layer = "gbenc_feature"
    else:
        tool_name = dsl.tool_name.value if hasattr(dsl.tool_name, 'value') else str(dsl.tool_name)
        target_layer = dsl.target_layers[0] if dsl.target_layers else "marine_hazards"

    
    # 파라미터 바인딩
    params = {}
    if isinstance(dsl, QueryPlan):
        # QueryPlan의 경우 파라미터 바인딩은 sql_compiler 내부에서 생성함
        pass
    else:
        if dsl.base_geometry:
            geom_str = str(dsl.base_geometry).strip().upper()
            if not geom_str.startswith(("POINT", "LINESTRING", "POLYGON", "MULTIPOINT", "MULTILINESTRING", "MULTIPOLYGON", "GEOMETRYCOLLECTION")):
                # WKT가 아니면 에러를 던져서 오류 메시지에 한글 원문이 섞이지 않게 차단
                return ToolResult(
                    task_id=task_id,
                    trace_id=trace_id,
                    tool_name=tool_name,
                    tool_version="1.1",
                    status="FAILED",
                    error_code="INVALID_GEOMETRY",
                    errors=[f"Invalid WKT format for base_geometry: '{dsl.base_geometry}'. Must be POINT, POLYGON, etc."],
                    execution_time=(time.time() - start_time) * 1000
                )
            params["geom"] = dsl.base_geometry
            # 새 템플릿용 파라미터 매핑
            params["search_area_wkt"] = dsl.base_geometry
            params["center_wkt"] = dsl.base_geometry
            
            # lon, lat 추출 (POINT인 경우)
            if geom_str.startswith("POINT"):
                try:
                    # "POINT (129.04 35.10)" -> "129.04", "35.10"
                    coords = geom_str.replace("POINT", "").replace("(", "").replace(")", "").strip()
                    lon, lat = coords.split()
                    params["lon"] = float(lon)
                    params["lat"] = float(lat)
                except Exception as e:
                    logger.warning(f"Failed to parse lon/lat from POINT: {e}")
        if dsl.buffer_distance is not None:
            params["dist"] = dsl.buffer_distance
            params["distance_m"] = dsl.buffer_distance
        elif "dwithin" in tool_name or "buffer" in tool_name or "radius" in tool_name:
            return ToolResult(task_id=task_id, trace_id=trace_id, tool_name=tool_name,
                              tool_version="2.0", status="FAILED", error_code="DISTANCE_REQUIRED",
                              errors=["분석 반경을 입력해 주세요."])
            
        params["limit"] = dsl.conditions.get("limit", 100) # nearest 등을 위해
        params["input_srid"] = 4326
        
        # Feature Name 바인딩
        if hasattr(dsl, "target_feature_names") and dsl.target_feature_names:
            params["target_features"] = dsl.target_feature_names
        elif hasattr(dsl, "target_nftc_codes") and dsl.target_nftc_codes:
            params["target_features"] = dsl.target_nftc_codes
        else:
            # Fallback for old templates or when not provided
            params["target_features"] = []
            
        if hasattr(dsl, "source_feature_names") and dsl.source_feature_names:
            params["source_features"] = dsl.source_feature_names
        else:
            params["source_features"] = []
    
        map_bounds = dsl.conditions.get("map_bounds")
        has_bounds = False
        if map_bounds and len(map_bounds) == 4:
            # [minLng, minLat, maxLng, maxLat] -> WKT POLYGON
            w, s, e, n = map_bounds
            params["map_bounds_geom"] = f"POLYGON(({w} {s}, {e} {s}, {e} {n}, {w} {n}, {w} {s}))"
            has_bounds = True

    try:
        from services.spatial_analysis_agent.sql_compiler import compiler
        
        if isinstance(dsl, QueryPlan):
            compile_result = compiler.compile(dsl.dict())
            if "error" in compile_result:
                return ToolResult(
                    task_id=task_id,
                    trace_id=trace_id,
                    tool_name=tool_name,
                    tool_version="2.0",
                    status="FAILED",
                    error_code="SQL_TEMPLATE_NOT_FOUND" if "지원하지 않는" in compile_result["error"] else "SQL_SCHEMA_VALIDATION_FAILED",
                    errors=[compile_result["error"]],
                    execution_time=(time.time() - start_time) * 1000
                )
            sql = text(compile_result["sql"])
            params = compile_result["params"]
            db_route = compile_result.get("db_route", "gbenc")
            logger.info("Compiled QueryPlan SQL", sql=str(sql))
        else:
            sql_template = get_query_template(tool_name, target_layer, dsl.target_nftc_codes, has_bounds)
            sql = text(sql_template)
            # 레이어 레지스트리 기반 DB 라우팅 처리
            db_route = "postgis"
            if target_layer in LAYER_REGISTRY:
                db_route = LAYER_REGISTRY[target_layer].get("database_route", "postgis")
        
    
        if db_route == "gbenc":
            db_generator = get_s101_db()
            logger.info("Routing query to S-101 v2 DB", tool=tool_name, layer=target_layer)
        else:
            db_generator = get_postgis_db()
            logger.info("Routing query to PostGIS DB", tool=tool_name, layer=target_layer)
            
        db = None
        result = []
        try:
            db = next(db_generator)
            print(f"EXECUTING SQL: {sql}")
            print(f"PARAMS: {params}")
            result = db.execute(sql, params).mappings().all()
            print(f"RESULT COUNT: {len(result)}")
        except Exception as e_db:
            logger.error(f"DB connection/execution failed for {db_route}: {e_db}")
            if db:
                db.close()
            return ToolResult(
                task_id=task_id,
                trace_id=trace_id,
                tool_name=tool_name,
                tool_version="2.0",
                status="FAILED",
                error_code="SQL_EXECUTION_FAILED",
                errors=[str(e_db)],
                execution_time=(time.time() - start_time) * 1000
            )
            
        if db is not None:
            filtered_count = 0
            for row in result:
                # 결과 row에 clearance_level이 있을 경우 보안 필터 적용
                req_lvl = clearance_map.get(row.get("clearance_level", "PUBLIC"), 1)
                if user_lvl >= req_lvl:
                    feature = {"type": "Feature", "properties": dict(row)}
                    if "geojson" in feature["properties"]:
                        feature["geometry"] = json.loads(feature["properties"].pop("geojson"))
                    elif "geometry" in feature["properties"]:
                        geom = feature["properties"].pop("geometry")
                        if isinstance(geom, str):
                            feature["geometry"] = json.loads(geom)
                        else:
                            feature["geometry"] = geom
                        
                    # 형광펜(Overlay Highlight) 스타일 적용
                    feature = apply_overlay_highlight(feature, target_layer)
                    
                    # 태깅 추가
                    # Preserve every DB feature; only hazard-class requests get a dedicated overlay.
                    target_values = params.get("target_features", [])
                    if not target_values and isinstance(dsl, QueryPlan):
                        target_values = dsl.target.feature_names
                    target_text = json.dumps(target_values, ensure_ascii=False).lower()
                    hazard_markers = ("wreck", "obstruction", "hazard", "danger", "foul", "rock", "위험", "침선", "난파", "장애물")
                    layer_text = str(feature["properties"].get("layer_id") or "").lower()
                    feature["properties"]["role"] = "hazard_objects" if any(marker in target_text or marker in layer_text for marker in hazard_markers) else "objects"

                    
                    # 정책 메타데이터(Policy) 주입
                    fname = row.get("feature_name")
                    if fname:
                        render_styles = dsl.conditions.get("_render_styles", {})
                        popup_fields = dsl.conditions.get("_popup_fields", {})
                        post_processors = dsl.conditions.get("_post_processors", {})
                        
                        if fname in render_styles:
                            feature["properties"]["_render_style"] = render_styles[fname]
                        if fname in popup_fields:
                            feature["properties"]["_popup_fields"] = popup_fields[fname]
                            
                        # Post Processor 적용
                        if fname in post_processors:
                            processor_name = post_processors[fname]
                            processor = get_processor(processor_name)
                            if processor:
                                try:
                                    feature["properties"] = processor.process(feature["properties"])
                                except Exception as e:
                                    logger.error("Post processor failed", processor=processor_name, error=str(e))
                    
                    features.append(feature)
                else:
                    filtered_count += 1
                    
            # (중복 검색 반경 Point 제거)


            if filtered_count > 0:
                log_data_access(user_id, "READ", target_layer, clearance_level, "FILTERED", f"{filtered_count} records denied")
                
            db.close()

    except Exception as e:
        # psycopg2 등에서 발생하는 CP949 에러 메시지가 UTF-8로 디코딩되지 않는 문제 방어
        err_msg = ""
        try:
            err_msg = str(e)
        except Exception:
            try:
                err_msg = e.args[0].decode('cp949', errors='ignore') if len(e.args) > 0 and isinstance(e.args[0], bytes) else repr(e)
            except:
                err_msg = repr(e)
            
        logger.error("Spatial tool execution failed", error=err_msg)
        return ToolResult(
            task_id=task_id,
            trace_id=trace_id,
            tool_name=tool_name,
            tool_version="1.1",
            status="FAILED",
            error_code="SQL_EXECUTION_FAILED",
            errors=[err_msg],
            execution_time=(time.time() - start_time) * 1000
        )

    # 1000건 초과 시 파일로 저장 (API 응답 보호)
    output_references = []
    inline_geojson = None
    # 검색 반경/기준점 피처 추가 (결과가 0건이어도 지도가 해당 위치로 이동하도록)
    if dsl.base_geometry:
        try:
            import shapely.wkt
            import shapely.geometry
            geom = shapely.wkt.loads(dsl.base_geometry)
            buf_dist = getattr(dsl, "buffer_distance", None)
            if not buf_dist and hasattr(dsl, "spatial") and dsl.spatial:
                buf_dist = dsl.spatial.distance_m
            if buf_dist:
                # 대략적인 위경도 기반 버퍼 (1도 ≒ 111km) - 시각화 및 Bounds 맞춤 용도
                geom = geom.buffer(buf_dist / 111000.0)
            
            boundary_feature = {
                "type": "Feature",
                "properties": {
                    "is_search_boundary": True,
                    "role": "search_buffer",
                    "name": "검색 반경",
                    "style": {
                        "fillColor": "transparent",
                        "color": "#FF0000",
                        "weight": 2,
                        "dashArray": "5, 5"
                    }
                },
                "geometry": shapely.geometry.mapping(geom)
            }
            features.insert(0, boundary_feature)
        except Exception as e:
            logger.warning(f"Failed to generate search boundary feature: {e}")

    # 실제 데이터 건수 계산 (검색 반경 피처 제외)
    data_features = [f for f in features if not f.get("properties", {}).get("is_search_boundary")]
    feature_count = len(data_features)
    
    # 인라인 데이터를 무조건 담되, 너무 많을 경우(10000건 초과)에만 파일로 분리
    inline_geojson = {"type": "FeatureCollection", "features": features}
    
    if feature_count > 10000:
        file_path = os.path.join(RESULTS_DIR, f"{task_id}_{tool_name}.geojson")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(inline_geojson, f)
        output_references.append(f"file://{file_path}")
        logger.info(f"Large result saved to {file_path}")
        # 프론트엔드가 지도에 너무 많은 요소를 그려 뻗는 것을 방지하고자 한다면 여기서 inline_geojson을 None으로 할 수 있으나
        # 로컬 환경에서의 3~5천 건 표출은 보통 가능하므로 우선 전달합니다.
    
    # 실행된 SQL 쿼리를 구조화된 결과에 담아 전달
    executed_query = str(sql) if 'sql' in locals() else ""
    spatial_layer_evidence = []
    for binding in qec_payload.get("data_bindings", []) if isinstance(qec_payload, dict) else []:
        if binding.get("layer_type") and binding.get("dataset_id") != "GBENC_S101_feature":
            spatial_layer_evidence.append({
                "evidence_type": binding.get("layer_type") or "spatial_layer",
                "summary": f"{binding.get('dataset_id')} 공간 레이어 조회",
                "source_ref": binding.get("source_asset") or binding.get("relation"),
                "data": {
                    "dataset_id": binding.get("dataset_id"),
                    "relation": binding.get("relation"),
                    "geometry_column": binding.get("geometry_column"),
                    "source_asset": binding.get("source_asset"),
                    "execution_status": binding.get("execution_status"),
                    "query_template": tool_name,
                },
            })

    # Map Layer Specification 생성
    map_spec = MapLayerSpecification(
        layer_id=f"layer_{task_id}",
        task_id=task_id,
        title=f"Spatial Result: {tool_name}",
        description=getattr(dsl, "reasoning", "QueryPlan 기반 공간 분석"),
        geometry_type="GEOMETRY",
        source_type="GEOJSON",
        source_uri=output_references[0] if output_references else None,
        inline_geojson=inline_geojson
    )

    return ToolResult(
        task_id=task_id,
        trace_id=trace_id,
        tool_name=tool_name,
        tool_version="1.1",
        status="SUCCESS",
        error_code="EMPTY_RESULT" if feature_count == 0 else None,
        structured_result={
            "count": feature_count, 
            "map_spec": map_spec.model_dump(),
            "executed_query": executed_query,
            "spatial_layer_evidence": spatial_layer_evidence,
        },
        output_references=output_references,
        execution_time=(time.time() - start_time) * 1000
    )
