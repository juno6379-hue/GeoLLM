import re
from typing import Tuple, Dict, Any, List
from shared.observability.logger import get_logger
from services.spatial_analysis_agent.schemas import SpatialDSL

logger = get_logger("spatial_analysis_agent.validator")

# 허용된 레이어 목록 (Layer Registry 연동 전 하드코딩)
ALLOWED_LAYERS = {
    "marine_hazards", "restricted_zones", "ais_tracking", 
    "enc_features_v1", "v_enc_features", "dt", "t_wrn_tw_buoy"
}

def validate_dsl(dsl: SpatialDSL) -> Tuple[bool, List[str]]:
    """
    10대 필수 검증 로직을 수행합니다.
    """
    errors = []
    
    # 1. 원천 SQL 차단 (Pydantic이 1차로 막지만, 파라미터 내 인젝션 방어)
    sql_injection_pattern = re.compile(r"(SELECT|INSERT|UPDATE|DELETE|DROP|--|;)", re.IGNORECASE)
    for layer in dsl.target_layers:
        if sql_injection_pattern.search(layer):
            errors.append(f"Target layer contains illegal SQL keywords: {layer}")
            
    # 2. 허용된 레이어 검증
    for layer in dsl.target_layers:
        if layer not in ALLOWED_LAYERS:
            errors.append(f"Access denied to layer '{layer}'. Not in Layer Registry.")

    # 3. CRS 검증
    if not dsl.crs.upper().startswith("EPSG:"):
        errors.append(f"Invalid CRS format: {dsl.crs}. Must start with EPSG:")
        
    # 4. Geometry Validity & Type & Null Check (간이 검증, WKT 텍스트 기반)
    if dsl.base_geometry is not None:
        geom_upper = dsl.base_geometry.upper()
        if geom_upper in ("NULL", "", "EMPTY"):
            errors.append("Geometry cannot be null or empty string.")
        elif not any(geom_upper.startswith(t) for t in ["POINT", "LINESTRING", "POLYGON", "MULTIPOLYGON"]):
            errors.append("Invalid or unsupported Geometry Type. Expected WKT.")

    # 5. 거리 단위 검증
    if dsl.buffer_distance is not None:
        if dsl.distance_unit not in ["meters", "kilometers"]:
            errors.append(f"Unsupported distance unit '{dsl.distance_unit}' for metric operations.")
        if dsl.buffer_distance < 0:
            errors.append("Distance cannot be negative.")
        if dsl.buffer_distance > 1000000:  # 1000km 제한 (과도한 연산 방지)
            errors.append("Distance exceeds maximum allowed range (1000km).")

    return len(errors) == 0, errors

def validate_query_plan(qp: Any) -> Tuple[bool, List[str]]:
    """
    QueryPlan 검증 로직을 수행합니다.
    """
    errors = []
    
    if qp.analysis_type not in ["feature_dwithin", "feature_within_area", "nearest_feature"]:
        errors.append(f"Unsupported analysis_type: {qp.analysis_type}")
        
    if not qp.target.nftc_codes:
        errors.append("target.nftc_codes is empty.")
        
    if not qp.location.place_id and not qp.location.original_text:
        errors.append("location information (place_id or original_text) is missing.")
        
    if qp.analysis_type == "feature_dwithin":
        if qp.spatial.distance_m is None or qp.spatial.distance_m < 0:
            errors.append("Valid distance_m is required for feature_dwithin.")
            
    return len(errors) == 0, errors
