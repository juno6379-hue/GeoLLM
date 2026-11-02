"""Output obligations shared by intent parsing and execution dispatch.

Topic aliases identify candidate evidence, not the operation requested by a user.
This gate prevents topical legal/document hits from satisfying execution requests.
"""
import re
from services.orchestrator.traffic_description import is_hypothetical_traffic_description


def requires_execution(query: str) -> bool:
    if is_hypothetical_traffic_description(query):
        return False
    text = str(query or "").casefold()
    operator = re.search(r"\b(?:within|intersects?)\b", text)
    explanation = re.search(r"정의|뜻|의미|연산자|\b(?:operator|predicate|mean(?:ing)?|definition)\b", text)
    concrete_task = re.search(r"찾|조회|검색|계산|지도.*표시|\b(?:find|search|retrieve|show)\b|\d+(?:\.\d+)?\s*(?:km|m)\b|selected\s+(?:area|polygon)", text)
    if operator and explanation and not concrete_task:
        return False
    if re.fullmatch(r"(?:within|intersects?|주변|반경)(?:\s*연산자)?(?:의)?\s*(?:정의|뜻|의미)(?:를)?\s*(?:알려줘|설명해줘)?[?.!]*", text.strip()):
        return False
    # A noun-phrase definition is not a request for that noun's values.
    if (re.fullmatch(r"[^,;.!?]+?(?:의)?\s*(?:정의|뜻|의미)(?:를|가|는)?\s*(?:알려줘|설명해줘|무엇인가요)?[?.!]*", text.strip())
            or re.fullmatch(r"what\s+is\s+(?:a\s+|an\s+|the\s+)?[^,;.!?]+[?.!]*", text.strip())) and not re.search(r"찾|조회|검색|표시|이동|\b(?:and|find|show|within|intersect\w*|nearest|closest)\b", text):
        return False
    if re.search(r"(?:좌표|위치)(?:를|을|와|과|도|는|가)?\s*(?:알려|보여|찾|조회|표시)|(?:좌표|위치)(?:와|과)\s*속성|(?:좌표|위치)를|지도.*(?:표시|보여|이동)|\b(?:navigate|move|(?:show|display)\b.*\bmap|(?:find|show|get|retrieve|give)\b.*\b(?:coordinates?|locations?)|(?:coordinates?|locations?)\s+and\s+attributes?)\b", text):
        return True
    # Spatial relations require execution even when an explanation is also asked.
    if re.search(r"\b(?:intersect(?:ing|s)?|within|nearest|closest)\b|교차|반경|주변|근처|\d+(?:\.\d+)?\s*(?:km|m)\b", text):
        return True
    if re.search(r"정의|어떤\s*객체|속성|허용\s*값|허용\s*기하|\b(?:definition|what is|attributes?)\b", text) and not re.search(r"좌표|지도.*표시|이동|집계|계산", text):
        return False
    # Explicit document objects retain retrieval semantics, even with 'find'.
    document = re.search(r"법령|고시|규칙|규정|통항령|통항명령|dceg|정의|카탈로그|catalogue|definition|근거|출처", text)
    action = re.search(r"분석|집계|계산|표시|이동|좌표|위치|찾아|보여|가까운|nearest|closest|통항량|교통량|밀도|항적|가장 높은|최대|월별|구역별|반경|이내|주변|nearby|traffic volume", text)
    executable_output = re.search(r"통항량|교통량|집계|계산|월별|구역별|지도.*표시", text)
    return bool(action and (not document or executable_output))


def permits_document_answer(query: str) -> bool:
    return not requires_execution(query)


def requests_map_output(query: str) -> bool:
    if is_hypothetical_traffic_description(query):
        return False
    return bool(re.search(r'지도(?:에|에서)?[^.!?\n]{0,60}(?:표시|보여|그려)|(?:표시|보여)[^.!?\n]{0,60}지도|\b(?:show|display|plot|draw)\b[^.!?\n]{0,100}\bmap\b', str(query or ''), re.I))


def missing_map_scope(query: str, context: dict | None) -> bool:
    if not requests_map_output(query):
        return False
    context = context or {}
    if any(context.get(k) for k in ('geometry', 'reference_geometry', 'map_bounds', 'bbox', 'bounds', 'viewport', 'selected_area', 'selected_feature', 'selected_features', 'clicked_point', 'place_id', 'base_location', 'location_text')):
        return False
    # An explicit reference phrase is input, even if not in a local gazetteer.
    # Its identity/geometry must subsequently be validated by the resolver.
    if re.search(r'\b(?:near|around|at|in)\s+(?!the\s+map\b)[A-Za-z]|\bwithin\s+\d+(?:\.\d+)?\s*(?:km|m)\s+of\s+\w+|[가-힣]{2,}(?:항|섬|도|만|해역)(?:의|을|를|에서|에|\s)|[가-힣]+\s*(?:주변|근처|부근)', query, re.I):
        return False
    from services.spatial_analysis_agent.place_resolver import load_catalog
    for item in load_catalog().get('candidates', []):
        for name in [item.get('label'), *(item.get('aliases') or [])]:
            if name and re.search(r'(?<![A-Za-z0-9_])'+re.escape(str(name))+r'(?![A-Za-z0-9_])', query, re.I):
                return False
    return True
