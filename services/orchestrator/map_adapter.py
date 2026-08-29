import json
from typing import Optional
from shared.schemas.map import MapLayerSpecification
from shared.schemas.agent import AgentResult

def convert_to_map_layer(agent_result: AgentResult, layer_id: str = "result-layer-1") -> Optional[MapLayerSpecification]:
    """
    Spatial Analysis Agent의 결과를 기존 Map Agent가 렌더링할 수 있는
    MapLayerSpecification 객체로 변환(Adapter)합니다.
    """
    # 1. Agent가 직접 MapLayerSpecification 딕셔너리를 반환한 경우 우선 적용
    if agent_result.output_layers and isinstance(agent_result.output_layers[0], dict):
        # dict to MapLayerSpecification
        try:
            return _normalize_layers(MapLayerSpecification(**agent_result.output_layers[0]))
        except Exception:
            pass
            
    if agent_result.structured_result and "map_spec" in agent_result.structured_result:
        try:
            return _normalize_layers(MapLayerSpecification(**agent_result.structured_result["map_spec"]))
        except Exception as e:
            from shared.observability.logger import get_logger
            logger = get_logger("map_adapter")
            logger.error(f"Failed to parse map_spec into MapLayerSpecification: {e}")
            pass

    # 2. 직접 반환하지 않았다면 기본 로직 사용
    if not agent_result.features:
        return None
        
    style = {
        "fill_color": "#FF0000",
        "stroke_color": "#FFFFFF",
        "opacity": 0.5
    }
    
    if agent_result.provenance and "query_template" in agent_result.provenance:
        if agent_result.provenance["query_template"] == "postgis.intersection":
            style["fill_color"] = "#0000FF"
            
    # S-101 렌더링 힌트 추가
    s101_rendering = False
    popup_fields = []
    intent_str = ""
    if agent_result.provenance and "dsl_query" in agent_result.provenance:
        dsl = agent_result.provenance["dsl_query"]
        if "enc_feature" in dsl.get("target_layers", []) or "gbenc_feature" in dsl.get("target_layers", []):
            s101_rendering = True
            style["s101_rendering"] = True
            popup_fields.append("feature_name")
        intent_str = f"\n[의도 파악 분석결과 (DSL)]\n{dsl}"
            
    desc = agent_result.summary
    if intent_str:
        desc += f"\n{intent_str}"
        
    layer_spec = MapLayerSpecification(
        layer_id=layer_id,
        task_id=agent_result.task_id,
        title=f"분석결과: {agent_result.summary[:20]}...",
        description=desc,
        geometry_type="GEOMETRY",
        source_type="geojson",
        source_uri=str(agent_result.features),
        style=style,
        popup_fields=popup_fields,
        visibility=True,
        feature_count=agent_result.structured_result.get("count") if agent_result.structured_result else None,
        metadata={
            "generated_count": agent_result.structured_result.get("count", 0)
            if agent_result.structured_result
            else 0
        }
    )
    
    return _normalize_layers(layer_spec)


def _normalize_layers(layer: MapLayerSpecification) -> MapLayerSpecification:
    """Keep all objects, expose hazards separately, and render one buffer."""
    geojson = layer.inline_geojson
    if not geojson or geojson.get("type") != "FeatureCollection":
        return layer

    features = geojson.get("features", [])
    buffers = []
    hazard_objects = []
    object_features = []
    seen_buffer_keys = set()

    for feature in features:
        properties = feature.get("properties", {}) or {}
        is_buffer = properties.get("is_search_boundary") or properties.get("role") == "search_buffer"
        if is_buffer:
            key = json.dumps(feature.get("geometry"), sort_keys=True, ensure_ascii=False)
            if key not in seen_buffer_keys:
                buffers.append(feature)
                seen_buffer_keys.add(key)
        else:
            object_features.append(feature)
            if properties.get("role") == "hazard_objects":
                hazard_objects.append(feature)

    if not buffers and not object_features:
        return layer

    # The primary layer contains every returned object, never only hazards.
    layer.inline_geojson = {"type": "FeatureCollection", "features": object_features}
    layer.feature_count = len(object_features)
    layer.metadata["layer_role"] = "all_objects"
    layer.metadata["geojson_feature_count"] = len(object_features)

    overlays = []
    if hazard_objects:
        hazard_layer = MapLayerSpecification(
            layer_id=f"{layer.layer_id}-hazard-objects",
            task_id=layer.task_id,
            title="Hazard Objects",
            description="Hazard features returned by the spatial query",
            geometry_type="GEOMETRY",
            source_type="geojson",
            inline_geojson={"type": "FeatureCollection", "features": hazard_objects},
            style={"fill_color": "#D90429", "stroke_color": "#7F1D1D", "opacity": 0.85},
            visibility=True,
            z_index=20,
            feature_count=len(hazard_objects),
            metadata={"layer_role": "hazard_objects", "geojson_feature_count": len(hazard_objects)},
        )
        overlays.append(hazard_layer.model_dump())

    if buffers:
        buffer_layer = MapLayerSpecification(
            layer_id=f"{layer.layer_id}-search-buffer",
            task_id=layer.task_id,
            title="Search Buffer",
            description="Search boundary for the spatial query",
            geometry_type="GEOMETRY",
            source_type="geojson",
            inline_geojson={"type": "FeatureCollection", "features": buffers},
            style={"fill_color": "transparent", "stroke_color": "#FF0000", "opacity": 0.35},
            visibility=True,
            z_index=10,
            metadata={"layer_role": "search_buffer", "feature_count": 1},
        )
        overlays.insert(0, buffer_layer.model_dump())

    if overlays:
        layer.metadata["overlay_layers"] = overlays

    return layer
