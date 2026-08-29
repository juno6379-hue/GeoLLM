from typing import Optional
from shared.schemas.agent import Intent, SpatialContext

def parse_intent_mock(query: str) -> Intent:
    """
    MVP 용 임시 Intent Parser. 
    추후 LLM/LangChain을 통해 텍스트에서 분석 목적과 객체를 추출하도록 교체됩니다.
    """
    query_lower = query.lower()
    intent_type = "UNKNOWN"
    target_objects = []
    
    if "분석" in query_lower and "위험객체" in query_lower:
        intent_type = "SPATIAL_SEARCH"
        target_objects.append("위험객체")
        
    return Intent(intent_type=intent_type, target_objects=target_objects)

def parse_spatial_context_mock(query: str) -> Optional[SpatialContext]:
    """
    MVP 용 임시 Spatial Context Parser.
    추후 LLM 엔티티 추출 또는 GeoCoding API 연계를 통해 위치 정보를 추출합니다.
    """
    query_lower = query.lower()
    if "부산항" in query_lower:
        # 부산항 좌표 임시 하드코딩
        return SpatialContext(
            base_location="부산항",
            geometry="POINT(129.07 35.09)",
            buffer_distance=3000,
            crs="EPSG:4326"
        )
    return None
