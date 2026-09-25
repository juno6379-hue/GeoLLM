"""Output obligations shared by intent parsing and execution dispatch.

Topic aliases identify candidate evidence, not the operation requested by a user.
This gate prevents topical legal/document hits from satisfying execution requests.
"""
import re


def requires_execution(query: str) -> bool:
    text = str(query or "").casefold()
    # Explicit document objects retain retrieval semantics, even with 'find'.
    document = re.search(r"법령|고시|규칙|규정|통항령|통항명령|dceg|정의|카탈로그|catalogue|definition|근거|출처", text)
    action = re.search(r"분석|집계|계산|표시|이동|좌표|위치|찾아|보여|가까운|nearest|closest|통항량|교통량|밀도|항적|가장 높은|최대|월별|구역별|반경|이내|주변|nearby|traffic volume", text)
    executable_output = re.search(r"통항량|교통량|집계|계산|월별|구역별|지도.*표시", text)
    return bool(action and (not document or executable_output))


def permits_document_answer(query: str) -> bool:
    return not requires_execution(query)
