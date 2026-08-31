import uuid
from typing import List
from datetime import datetime

import os
import csv
import json
from pathlib import Path
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from shared.schemas.agent import AgentRequest, AgentResult, AgentStatus, DatasetVersion
from shared.security.context import check_clearance, ClearanceLevel
from services.registry.catalog_service import build_live_catalog
from shared.observability.logger import get_logger
from services.llm_config import llm_api_enabled

logger = get_logger("data_discovery_agent")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFERRED_RELATIONS = ["nearFeature", "occurredIn", "overlapsFeature", "overlapsLayer", "supportsConcept"]

def _read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default

def _probe_s101_db():
    """Probe only an explicitly configured S101 v2 database; never the dev fallback DB."""
    url = os.getenv("S101_DB_URL")
    if url:
        kwargs = {"dsn": url, "connect_timeout": 2}
    elif os.getenv("S101_DB_HOST") and os.getenv("S101_DB_NAME"):
        kwargs = {"host": os.getenv("S101_DB_HOST"), "port": os.getenv("S101_DB_PORT", "5432"),
                  "dbname": os.getenv("S101_DB_NAME"), "user": os.getenv("S101_DB_USER", "postgres"),
                  "password": os.getenv("S101_DB_PASSWORD", ""), "connect_timeout": 2}
    else:
        return {"connected": False, "inventory_ready": False, "spatial_ready": False, "reason": "S101_DB_URL or S101_DB_* is not configured"}
    try:
        import psycopg2
        with psycopg2.connect(**kwargs) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT to_regclass('projection.s101_feature_current'),
                           to_regclass('projection.s101_feature_geojson'),
                           EXISTS (SELECT 1 FROM pg_extension WHERE extname='postgis')
                """)
                feature_table, geojson_table, postgis = cur.fetchone()
                if feature_table:
                    cur.execute("""
                        SELECT count(*),
                               count(geometry),
                               count(*) FILTER (WHERE geometry IS NULL),
                               count(*) FILTER (WHERE geometry IS NOT NULL AND ST_IsEmpty(geometry)),
                               count(*) FILTER (WHERE geometry IS NOT NULL AND ST_SRID(geometry) <> 4326)
                        FROM projection.s101_feature_current
                    """)
                    feature_count, geometry_count, null_geometry_count, empty_geometry_count, srid_mismatch_count = cur.fetchone()
                else:
                    feature_count = geometry_count = null_geometry_count = empty_geometry_count = srid_mismatch_count = 0
                cur.execute("""
                    SELECT EXISTS (
                        SELECT 1
                        FROM pg_indexes
                        WHERE schemaname = 'projection'
                          AND tablename = 's101_feature_current'
                          AND indexdef ILIKE '%USING gist%'
                          AND indexdef ILIKE '%geometry%'
                    )
                """)
                gist_index = cur.fetchone()[0]
        projection_ready = bool(feature_table and feature_count)
        spatial_ready = bool(
            projection_ready
            and geojson_table
            and geometry_count
            and postgis
            and gist_index
            and not null_geometry_count
            and not empty_geometry_count
            and not srid_mismatch_count
        )
        validation_report = _read_json(PROJECT_ROOT / "outputs/reports/s101_v2_db_validation.json", {})
        spatial_quality_ready = None
        invalid_geometry_count = None
        if validation_report.get("projection") == "projection.s101_feature_current":
            spatial_quality_ready = bool(validation_report.get("ready"))
            invalid_geometry_count = validation_report.get("summary", {}).get("invalid_geometry_count")
        reason = "S101 v2 projection probe succeeded"
        if projection_ready and not spatial_ready:
            reason = "S101 v2 projection is reachable, but spatial readiness checks are incomplete"
        elif spatial_quality_ready is False:
            reason = "S101 v2 projection is executable, but full geometry validation found issues"
        return {"connected": True, "inventory_ready": projection_ready,
                "spatial_ready": spatial_ready, "feature_count": feature_count,
                "geometry_count": geometry_count, "null_geometry_count": null_geometry_count,
                "empty_geometry_count": empty_geometry_count,
                "srid_mismatch_count": srid_mismatch_count,
                "postgis_enabled": bool(postgis), "gist_index": bool(gist_index),
                "geojson_projection_ready": bool(geojson_table),
                "spatial_quality_ready": spatial_quality_ready,
                "invalid_geometry_count": invalid_geometry_count,
                "reason": reason}
    except Exception as exc:
        return {"connected": False, "inventory_ready": False, "spatial_ready": False, "reason": f"S101 v2 database probe failed: {type(exc).__name__}"}

def build_discovery_snapshot():
    """Return deterministic Data Lake + KG availability without running spatial tools."""
    inv_path = PROJECT_ROOT / "outputs/inventories/dataset_inventory.csv"
    catalogue = PROJECT_ROOT / "data/s101_catalogue.json"
    registry_files = [PROJECT_ROOT / "data/derived_concept_registry_v2.yaml", PROJECT_ROOT / "data/data_registry.yaml", PROJECT_ROOT / "data/tool_registry.yaml"]
    rag_manifest = _read_json(PROJECT_ROOT / "outputs/rag/rag_manifest.json", {})
    graph_nodes = PROJECT_ROOT / "outputs/graph/kg_nodes_v2.jsonl"
    inventory_ready = inv_path.exists()
    catalogue_ready = catalogue.exists() and all(path.exists() for path in registry_files)
    chunks = []
    for name in rag_manifest.get("files", {}):
        path = PROJECT_ROOT / "outputs/rag" / name
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line:
                    item = _read_json(Path("/dev/null"), {}) if False else json.loads(line)
                    chunks.append(item.get("metadata", {}).get("extraction_status"))
    document_body_ready = bool(chunks) and all(status not in {"metadata_only", "archive_manifest"} for status in chunks)
    db = _probe_s101_db()
    if not inventory_ready:
        level = "METADATA_ONLY"
    elif catalogue_ready and not db["connected"]:
        level = "CATALOGUE_READY_DB_PENDING"
    elif db["connected"] and db["inventory_ready"] and not db["spatial_ready"]:
        level = "DB_CONNECTED_INVENTORY_READY"
    elif db["spatial_ready"]:
        level = "EXECUTION_READY"
    else:
        level = "METADATA_ONLY"
    available = []
    if inventory_ready: available.append("Dataset Inventory")
    if catalogue_ready: available.extend(["S-101 Feature Catalogue v2.0", "v2 Dictionary", "Derived Concept Registry", "Data Registry", "Tool Registry"])
    if rag_manifest: available.append(f"RAG manifest ({sum(v.get('chunk_count', 0) for v in rag_manifest.get('files', {}).values())} chunks)")
    if graph_nodes.exists(): available.append("Marine KG bootstrap nodes/edges")
    missing = []
    if not db["connected"]: missing.append("S101 v2 DB connection and Feature Geometry")
    if not db["spatial_ready"]: missing.append("PostGIS spatial index and verified layer geometry")
    if db.get("spatial_quality_ready") is False:
        missing.append("S-101 invalid geometry repair")
    if not document_body_ready: missing.append("parsed document body chunks")
    accident_inventory_ready = (PROJECT_ROOT / "outputs/inventories/accident_inventory.csv").exists()
    if not accident_inventory_ready:
        missing.append("geocoded accident location geometry")
    blocked = []
    for relation in DEFERRED_RELATIONS:
        if relation == "supportsConcept": status = "PENDING_DOCUMENT_PARSE" if not document_body_ready else "CANDIDATE"
        elif relation == "occurredIn":
            status = "PENDING_SPATIAL_JOIN" if accident_inventory_ready else "PENDING_ACCIDENT_GEOCODING"
        else:
            if not db["spatial_ready"]:
                status = "PENDING_DB_RESTORE"
            elif db.get("spatial_quality_ready") is False:
                status = "PENDING_GEOMETRY_REPAIR"
            else:
                status = "PENDING_LAYER_GEOMETRY"
        blocked.append({"relation": relation, "status": status, "verified": False, "reason": "No LLM-inferred verification"})
    candidate = [{"relation": x["relation"], "status": "CANDIDATE", "reason": "Requires evidence evaluation"} for x in blocked if x["status"] == "CANDIDATE"]
    can_execute = level == "EXECUTION_READY"
    return {"discovery_status": "READY" if available else "NO_DATA", "execution_level": level,
            "can_execute_spatial_query": can_execute,
            "can_verify_spatial_edges": can_execute and db.get("spatial_quality_ready") is not False,
            "available_data": available, "missing_data": missing, "blocked_relations": blocked,
            "candidate_data": candidate, "required_next_actions": ["Restore and configure S101 v2 DB", "Extract Feature/Layer geometry and create spatial indexes", "Parse document bodies and regenerate RAG chunks", "Geocode accident locations"] ,
            "provenance": {"inventory": "outputs/inventories/dataset_inventory.csv", "rag_manifest": "outputs/rag/rag_manifest.json", "kg": "outputs/graph/kg_nodes_v2.jsonl", "db_probe": db}}

class ExternalApiQuery(BaseModel):
    """LLM이 사용자 질의에서 외부 API 검색 조건(파라미터)을 추출하는 스키마"""
    requires_external_api: bool = Field(description="내부 GIS 데이터가 아닌 기상, 파고, 실시간 관측 등 외부 API 연동이 필요한지 여부")
    api_domain: str = Field(description="외부 API 도메인 (예: 기상청_해양관측, 해양조사원_조석)")
    search_keywords: List[str] = Field(description="검색을 위한 핵심 키워드 리스트 (예: 파고, 수온)")

async def execute_data_discovery(request: AgentRequest) -> AgentResult:
    """
    Data Discovery Agent Core Logic.
    질의 컨텍스트를 바탕으로 Dataset Registry 를 검색하고, 보안 등급으로 필터링합니다.
    """
    logger.info("Starting data discovery", task_id=request.task_id)
    
    available_datasets: List[DatasetVersion] = []
    
    user_clearance_str = request.security_context.clearance_level
    try:
        user_clearance = ClearanceLevel(user_clearance_str)
    except ValueError:
        user_clearance = ClearanceLevel.PUBLIC
        
    all_datasets = build_live_catalog()
    
    # 2. Context Match & LLM Parameter Extraction
    target_location = request.spatial_context.base_location if request.spatial_context else ""
    target_objects = request.parsed_intent.target_objects if request.parsed_intent else []
    query_text = request.original_query
    
    requires_external = False
    api_domain = ""
    extracted_keywords = target_objects.copy()
    
    try:
        if llm_api_enabled():
            model_name = os.environ.get("LLM_MODEL", "gpt-4o-mini")
            llm = ChatOpenAI(model=model_name, temperature=0)
            structured_llm = llm.with_structured_output(ExternalApiQuery)
            
            sys_msg = "당신은 해양 데이터 검색 에이전트입니다. 기상(파고, 풍속 등), 실시간 데이터 등은 외부 API가 필요합니다."
            result: ExternalApiQuery = await structured_llm.ainvoke([
                SystemMessage(content=sys_msg),
                HumanMessage(content=query_text)
            ])
            requires_external = result.requires_external_api
            api_domain = result.api_domain
            extracted_keywords.extend(result.search_keywords)
            logger.info("Data Discovery LLM Extracted", external=requires_external, domain=api_domain)
    except Exception as e:
        logger.warning("LLM extraction failed, using fallback", error=str(e))
        if "파고" in query_text or "기상" in query_text:
            requires_external = True
            extracted_keywords.append("파고")
            
    api_params = {}
    if requires_external:
        api_params = {"domain": api_domain, "extracted_keywords": extracted_keywords}
    
    for ds in all_datasets:
        # 1. Security Check
        ds_clearance = ClearanceLevel(ds.security_level)
        if not check_clearance(user_clearance, ds_clearance):
            continue
            
        # 2. Match external API intent
        if requires_external and ds.is_external_api:
            # 외부 API 연동이 필요하고, 해당 데이터셋이 외부 API일 경우 가산점
            available_datasets.append(DatasetVersion(dataset_id=ds.dataset_id, version=ds.version))
            continue
            
        # 3. Keyword Match
        match_score = 0
        if target_location and target_location in ds.keywords:
            match_score += 1
            
        for obj in extracted_keywords:
            if obj in ds.keywords:
                match_score += 1
                
        if match_score > 0 and not ds.is_external_api:
            available_datasets.append(DatasetVersion(dataset_id=ds.dataset_id, version=ds.version))
            
    # [NEW] Fetch data from matched CSVs
    fetched_data = {}
    import pandas as pd
    
    for ds_ver in available_datasets:
        # Find the original dataset entry
        ds_entry = next((d for d in all_datasets if d.dataset_id == ds_ver.dataset_id), None)
        if ds_entry and ds_entry.api_endpoint:
            if ds_entry.api_endpoint.endswith(".csv"):
                try:
                    # Read top 5 rows to provide a summary
                    df = pd.read_csv(ds_entry.api_endpoint, encoding="cp949", nrows=5)
                    fetched_data[ds_entry.dataset_id] = df.to_dict(orient="records")
                    logger.info(f"Successfully fetched data from {ds_entry.api_endpoint}")
                except Exception as e:
                    logger.error(f"Failed to fetch CSV data from {ds_entry.api_endpoint}", error=str(e))
                    try:
                        # Fallback encoding
                        df = pd.read_csv(ds_entry.api_endpoint, encoding="utf-8", errors="replace", nrows=5)
                        fetched_data[ds_entry.dataset_id] = df.to_dict(orient="records")
                    except Exception as e2:
                        fetched_data[ds_entry.dataset_id] = {"error": f"Failed to read CSV: {e2}"}
            
    discovery = build_discovery_snapshot()
    graph_dir = PROJECT_ROOT / "outputs/graph"
    graph_dir.mkdir(parents=True, exist_ok=True)
    (graph_dir / "deferred_edges_status.jsonl").write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in discovery["blocked_relations"]), encoding="utf-8")
    (graph_dir / "candidate_edges_from_discovery.jsonl").write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in discovery["candidate_data"]), encoding="utf-8")
    (graph_dir / "verified_edges_from_discovery.jsonl").write_text("", encoding="utf-8")
    summary = f"Total {len(available_datasets)} datasets discovered. Discovery level: {discovery['execution_level']}. Spatial execution: {discovery['can_execute_spatial_query']}."
    
    return AgentResult(
        task_id=request.task_id,
        trace_id=request.trace_id,
        agent_name="data-discovery-agent",
        agent_version="1.1.0-llm-fetch",
        status=AgentStatus.COMPLETED,
        summary=summary,
        structured_result={
            "discovered_count": len(available_datasets),
            "requires_external_api": requires_external,
            "api_params": api_params,
            "fetched_data": fetched_data,
            **discovery
        },
        source_dataset_versions=available_datasets,
        created_at=datetime.utcnow(),
        provenance=discovery["provenance"],
        recommended_next_actions=discovery["required_next_actions"]
    )
