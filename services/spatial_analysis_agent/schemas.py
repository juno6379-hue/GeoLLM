from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field, model_validator, field_validator

class SpatialFunctionName(str, Enum):
    BUFFER = "buffer"
    DWITHIN = "dwithin"
    INTERSECTION = "intersection"
    OVERLAY = "overlay"
    UNION = "union"
    DIFFERENCE = "difference"
    CONTAINS = "contains"
    WITHIN = "within"
    TOUCHES = "touches"
    ADJACENCY = "adjacency"
    NEAREST = "nearest"
    SPATIAL_JOIN = "spatial_join"
    ROUTE_RISK = "route_risk"
    INFLUENCE_AREA = "influence_area"
    SUITABILITY_ANALYSIS = "suitability_analysis"
    AREA_STATISTICS = "area_statistics"
    DISTANCE_STATISTICS = "distance_statistics"
    OBJECT_COUNT = "object_count"
    RASTER_CLIP = "raster_clip"
    ZONAL_STATISTICS = "zonal_statistics"
    FEATURE_SEARCH_BY_AREA = "feature_search_by_area"
    FEATURE_SEARCH_BY_RADIUS = "feature_search_by_radius"
    FEATURE_OVERLAP_ANALYSIS = "feature_overlap_analysis"
    NEAREST_FEATURE_SEARCH = "nearest_feature_search"

class SpatialReference(BaseModel):
    type: str = Field(description="참조 타입: 'named_place', 'geometry', 'feature'")
    name: Optional[str] = Field(None, description="지명 (named_place일 때 필수)")
    geometry: Optional[str] = Field(None, description="WKT (geometry일 때 필수)")

class SpatialDSL(BaseModel):
    """LLM이 파싱하여 생성할 Spatial Domain Specific Language (DSL)"""
    tool_name: SpatialFunctionName = Field(description="실행할 공간 분석 함수의 종류")
    target_layers: List[str] = Field(description="조회할 대상 레이어(테이블) 목록. 예: ['feature', 'marine_hazards']")
    target_nftc_codes: Optional[List[int]] = Field(default_factory=list, description="조회할 대상 객체의 S-101 NFTC 코드 목록")
    target_feature_names: Optional[List[str]] = Field(default_factory=list, description="조회할 대상 객체의 S-101 Feature 이름 목록")
    source_feature_names: Optional[List[str]] = Field(default_factory=list, description="중첩 분석 시 기준이 되는 Feature 이름 목록")
    
    @field_validator('target_feature_names', 'target_nftc_codes', 'source_feature_names', mode='before')
    @classmethod
    def filter_nones(cls, v):
        if isinstance(v, list):
            return [item for item in v if item is not None]
        return v
    
    reference: Optional[SpatialReference] = Field(None, description="공간 기준 (지명, 도형 등)")
    base_geometry: Optional[str] = Field(None, description="공간 기준이 되는 형상의 WKT (Point, Polygon 등)")
    
    buffer_distance: Optional[float] = Field(None, description="거리, 반경, 버퍼 크기 파라미터 (단위: 미터)")
    distance_unit: str = Field("meters", description="거리 단위 (meters, kilometers, degrees)")
    crs: str = Field("EPSG:4326", description="입력 좌표계")
    target_attributes: List[str] = Field(default_factory=list, description="추출할 속성 컬럼 목록")
    conditions: Dict[str, Any] = Field(default_factory=dict, description="추가 필터링 조건 (예: {'type': 'WRECK'})")
    suitability_criteria: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="적지 분석 조건")
    time_range_start: Optional[str] = Field(None, description="분석 시작 시간 (ISO 8601 포맷, 예: '2025-07-01T00:00:00Z')")
    time_range_end: Optional[str] = Field(None, description="분석 종료 시간 (ISO 8601 포맷, 예: '2025-12-31T23:59:59Z')")
    reasoning: str = Field(description="이 함수와 파라미터를 선택한 논리적 이유 (검증 실패 시 프롬프트 보정용)")

    @model_validator(mode='after')
    def validate_spatial_rules(self) -> 'SpatialDSL':
        op = self.tool_name
        
        # 1. dwithin + distance_meters=None
        # (기존의 에러/자동 폴백 대신 None 허용. Orchestrator나 Agent 실행부에서 Clarification으로 넘김)
        if op == SpatialFunctionName.DWITHIN and self.buffer_distance is None:
            pass
            
        # 2. buffer + distance_meters=None
        if op == SpatialFunctionName.BUFFER and self.buffer_distance is None:
            pass
            
        # 3. suitability + suitability_criteria=[]
        if op == SpatialFunctionName.SUITABILITY_ANALYSIS and not self.suitability_criteria:
            raise ValueError("suitability_analysis 연산에는 suitability_criteria가 필수입니다.")
            
        # 4 & 5. reference type constraints
        if self.reference:
            if self.reference.type == "named_place" and not self.reference.name:
                raise ValueError("reference.type이 'named_place'인 경우 reference.name(지명)이 필수입니다.")
            if self.reference.type == "geometry" and not self.reference.geometry:
                raise ValueError("reference.type이 'geometry'인 경우 reference.geometry(도형)가 필수입니다.")
                
            # Populate base_geometry for backward compatibility
            if self.reference.geometry and not self.base_geometry:
                self.base_geometry = self.reference.geometry
                
        # 6. overlay + target_layers 1개
        if op == SpatialFunctionName.OVERLAY:
            has_base = self.base_geometry is not None or (self.reference and self.reference.geometry)
            if len(self.target_layers) < 2 and not has_base:
                # 대상 레이어가 1개이고 기준 도형도 없으면 오버레이가 불가능하므로,
                # 기본 영역 검색(INTERSECTION)으로 자동 롤백
                self.tool_name = SpatialFunctionName.INTERSECTION
                
        # 7. nearest + reference=None
        if op == SpatialFunctionName.NEAREST:
            has_ref = self.base_geometry is not None or self.reference is not None
            if not has_ref:
                raise ValueError("nearest 연산에는 기준점(reference 또는 base_geometry)이 필수입니다.")
                
        return self

class TargetInfo(BaseModel):
    original_term: Optional[str] = None
    concept_id: Optional[str] = None
    nftc_codes: List[int] = Field(default_factory=list)
    feature_names: List[str] = Field(default_factory=list)
    geometry_types: List[str] = Field(default_factory=list)
    resolution_status: Optional[str] = None
    confidence: Optional[float] = None

class LocationInfo(BaseModel):
    original_text: Optional[str] = None
    place_id: Optional[str] = None
    geometry_source: Optional[str] = None
    reference_mode: Optional[str] = None
    resolution_status: Optional[str] = None
    confidence: Optional[float] = None
    
class SpatialInfo(BaseModel):
    relation: Optional[str] = None
    distance_m: Optional[float] = None
    map_bounds_required: bool = False

class OutputInfo(BaseModel):
    format: str = "geojson"
    limit: int = 100
    include_attributes: bool = True

class QueryPlan(BaseModel):
    query_id: str = Field(description="Unique Query ID")
    intent: str = Field(description="Intent type, e.g. spatial_feature_proximity_search")
    analysis_type: str = Field(description="SQL Template name, e.g. feature_dwithin")
    target: TargetInfo
    location: LocationInfo
    spatial: SpatialInfo
    output: OutputInfo
    target_agent: str = "SpatialQueryAgent"
    required_tools: List[str] = Field(default_factory=list)
    unresolved_slots: List[str] = Field(default_factory=list)
    execution_status: str = "READY"
    conditions: Dict[str, Any] = Field(default_factory=dict)
    base_geometry: Optional[str] = None
