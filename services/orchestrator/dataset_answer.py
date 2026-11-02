"""Source passages in the actual answer, separate from spatial execution.

This adapter answers explicit informational requests with attributed quotations.
It does not infer coordinates, current conditions, or semantic completeness.
"""
import re

from services.orchestrator.coastal_knowledge import query_terms, retrieve
from services.orchestrator.execution_validator import is_execution_authorized, project_execution_decision
from services.orchestrator.request_semantics import requires_execution
from services.orchestrator.dataset_verification import load_receipts, verify_document
from shared.schemas.agent import QueryExecutionContext


def informational_request(query: str) -> bool:
    q = str(query or '').strip()
    # Existing specialised source/execution policies remain authoritative.
    if re.search(r'비공개|기밀|무단|실시간|예측|예보|오늘|내일|현재|최신|위험|안전|통항량|교통량|밀도|집계|계산|분석|비교|적재|임베딩|provenance|S[- ]?\d{3}|카탈로그|catalogue|DCEG|portrayal|법령|법률|고시|규정|제한\s*종류|속성|정의|어떤\s*객체|선택|클릭|(?:이|그|해당)\s*(?:객체|항만|수로|양식장)|\b(?:private|classified|forecast|risk|current|latest|attributes?|definition)\b', q, re.I):
        return False
    request = bool(re.search(r'(?:정보|안내|내용|설명|자료|문서|본문|출처)[^.!?\n]{0,35}(?:알려|설명|찾|검색|조회|보여)|(?:설명|요약)해\s*줘', q))
    if not request or not query_terms(q):
        return False
    # 'Find documents about X' retrieves text, whereas 'find X near Y' is spatial.
    rest = re.sub(r'(?:자료|문서|본문|출처)(?:를|을)?\s*(?:찾아줘|검색해줘|조회해줘|보여줘)', '', q)
    if requires_execution(q) and (rest == q or requires_execution(rest)):
        return False
    if re.search(r'이동|좌표|지도|위치|항로\s*(?:계획|생성)|\b(?:navigate|map|coordinates?)\b', rest, re.I):
        return False
    return True


def _source_passages(query, evidence):
    terms = query_terms(query)
    result, seen = [], set()
    for doc in evidence.get('documents') or []:
        if ((doc.get('metadata') or {}).get('retrieval_status') == 'SUPERSEDED'
                or (doc.get('source_text_verification') or {}).get('status') in ('AUDIT_SNAPSHOT_MISMATCH', 'CURRENT_CHUNK_SUPERSEDED')):
            continue
        content = str(doc.get('content') or '')
        title = str(doc.get('title') or '')
        h = str(doc.get('source_sha256') or '')
        if (not content.strip() or not doc.get('chunk_id') or not doc.get('source_id')
                or not re.fullmatch(r'[0-9a-f]{64}', h)
                or str(doc.get('document_type') or '').endswith('profile')
                or not all(term.casefold() in (title + ' ' + content).casefold() for term in terms)):
            continue
        key = (doc['source_id'], doc.get('page_no'), doc.get('section'))
        if key in seen:
            continue
        seen.add(key)
        positions = [content.casefold().find(t.casefold()) for t in terms]
        positions = [i for i in positions if i >= 0]
        start = max(0, min(positions) - 70) if positions else 0
        quote = content[start:start + 480].strip()
        if len(quote) < 15:
            continue
        result.append({'chunk_id':doc['chunk_id'], 'source_id':doc['source_id'],
                       'source_sha256':h, 'source_file':doc.get('source_file'),
                       'title':title, 'page_no':doc.get('page_no'), 'section':doc.get('section'),
                       'document_type':doc.get('document_type'), 'quote':quote,
                       'source_text_verification':doc.get('source_text_verification', {'status':'UNVERIFIED'}),
                       'edition':(doc.get('metadata') or {}).get('edition'),
                       'quote_verified_in_retrieved_content':quote in content})
        if len(result) == 3:
            break
    return result


def build_dataset_answer(state):
    query = str(state.get('query') or '')
    if not informational_request(query):
        return None
    try:
        evidence = retrieve(query, scope='dataset', include_spatial=False, request_state=state)
    except Exception as exc:
        # Source outages are not evidence that the corpus contains no matches.
        evidence = {'status':'UNAVAILABLE', 'documents':[], 'error_type':type(exc).__name__,
                    'document_lookup_status':'UNAVAILABLE', 'coordinate_authority':False}
    typed = None
    try:
        typed = QueryExecutionContext.model_validate(evidence.get('query_execution_context') or {})
    except (ValueError, TypeError):
        pass
    authorized = (typed is not None and is_execution_authorized(typed)
                  and typed.original_query == query
                  and (not state.get('task_id') or typed.request_id == str(state['task_id']))
                  and typed.route_plan.get('analysis_type') == 'dataset_document_lookup')
    receipts = load_receipts()
    for document in evidence.get('documents') or []:
        document['source_text_verification'] = verify_document(document, receipts)
    passages = _source_passages(query, evidence) if authorized else []
    verified_count = sum(p['source_text_verification']['status'] == 'AUDIT_SNAPSHOT_MATCH' for p in passages)
    diagnostic_documents = (evidence.get('documents') or []) + (evidence.get('excluded_audit_documents') or [])
    mismatch_count = sum((d.get('source_text_verification') or {}).get('status') == 'AUDIT_SNAPSHOT_MISMATCH'
                         for d in diagnostic_documents)
    superseded_count = sum((d.get('source_text_verification') or {}).get('status') == 'CURRENT_CHUNK_SUPERSEDED'
                           for d in diagnostic_documents)
    if passages:
        # Retrieval can support a useful attributed answer without proving that
        # every requested informational aspect has been explained.
        status, error = 'PARTIAL', None
        parts = ['저장된 Dataset 자료에서 요청 주제와 연결되는 원문을 찾았습니다. 다음은 출처가 확인된 발췌입니다.']
        parts.append(f'제시한 발췌의 감사 시점 원문 대조: 확인 {verified_count}건, 미검증 {len(passages)-verified_count}건. 현재 조회한 본문과 출처가 감사 기록과 같은 경우만 확인으로 표시합니다. 문서의 의미 정확성이나 실제 위치·좌표의 권위를 보증하지 않습니다.')
        derived = [p['source_text_verification'].get('derived_field_verification', {}) for p in passages]
        if any(derived):
            parts[0] = '저장된 Dataset 자료의 본문과 원천 기반 파생 설명을 찾았습니다. 아래 발췌는 각 자료의 작성 방식과 검증 범위를 구분해 제공합니다.'
        derived_matched = sum(d.get('status') == 'VERIFIED_DERIVED_FIELDS' for d in derived)
        incomplete = sum(d.get('status') == 'INCOMPLETE_DERIVED_FIELDS' for d in derived)
        if derived_matched:
            parts.append(f'파생 설명 {derived_matched}건은 감사 시점 원천 필드와 대조했습니다. 원문 그대로의 인용이나 현재 DB 재조회 완료를 뜻하지 않습니다.')
        if incomplete:
            parts.append(f'파생 설명 {incomplete}건에는 일부 원천 필드(속성 코드 또는 객체–속성 관계 등)가 빠져 있습니다. 해당 부분을 완전한 속성 설명으로 사용하지 않습니다.')
        if mismatch_count:
            parts.append(f'감사 원문과 불일치한 청크 {mismatch_count}건은 답변 발췌에서 제외했습니다.')
        if any(p['source_text_verification'].get('coordinate_literal_issues') for p in passages):
            parts.append('원문 좌표 표기에 검토가 필요한 항목이 있어 위치 기준으로 사용하지 않았습니다.')
        linked_objects = {link['source_id'] for p in passages
                          for link in p['source_text_verification'].get('object_links', [])}
        if linked_objects:
            parts.append(f'같은 원천의 항만 객체 연결 {len(linked_objects)}건이 있습니다. 대표점이며 입구 위치로 확인한 것은 아닙니다. 감사 시점의 연결이며 현재 DB 객체를 다시 조회하거나 지도 이동에 사용하지 않았습니다.')
        for i, passage in enumerate(passages, 1):
            locator = f"{passage['page_no']}쪽" if passage['page_no'] is not None else passage['section'] or '본문'
            parts.append(f"[{i}] {passage['title']} · {locator}\n{passage['quote']}")
        parts.append('위 내용은 해당 자료에 기록된 설명입니다. 자료 판·최신성과 질문의 모든 세부사항을 확인한 종합 답변은 아닙니다. 과거 사고·항만 안내를 현재 항행 조건으로 단정하지 않습니다. 위치 이동·공간 분석은 실행하지 않았습니다.')
        answer = '\n\n'.join(parts)
    elif authorized and evidence.get('document_lookup_status') == 'COMPLETED':
        status, error = 'BLOCKED', 'DATASET_DOCUMENT_EVIDENCE_NOT_FOUND'
        answer = '현재 연결된 Dataset 본문 검색에서 요청 대상과 출처가 함께 확인되는 근거를 찾지 못했습니다. 관련 없는 자료로 답변을 만들지 않았습니다. 이는 Dataset 전체에 자료가 없다는 판정은 아닙니다.'
        if mismatch_count and mismatch_count == len(evidence.get('documents') or []) + len(evidence.get('excluded_audit_documents') or []):
            error = 'DATASET_SOURCE_TEXT_MISMATCH_ONLY'
            answer = f'조회된 청크 {mismatch_count}건이 감사 당시 원문과 불일치하여 답변 근거에서 제외했습니다. 원문 대조가 필요하며, 검색 결과가 없거나 Dataset 전체에 자료가 없다는 뜻은 아닙니다.'
        elif mismatch_count:
            answer += f' 감사 원문과 불일치한 청크 {mismatch_count}건은 답변 근거에서 제외했습니다.'
        elif superseded_count:
            error = 'DATASET_SUPERSEDED_EVIDENCE_EXCLUDED'
            answer = f'현재 대체된 자료로 표시된 청크 {superseded_count}건은 답변 근거에서 제외했습니다. 활성 자료에서 사용할 수 있는 발췌를 확인하지 못했습니다.'
    else:
        status, error = 'BLOCKED', 'DATASET_DOCUMENT_SOURCE_UNAVAILABLE'
        answer = 'Dataset 본문 조회의 원천 또는 실행 검증을 확인하지 못했습니다. 검색 결과가 0건이라는 뜻은 아니며, 근거 없는 답변은 생성하지 않았습니다.'
    plan = {'analysis_type':'dataset_document_lookup', 'intent':'KNOWLEDGE_SEARCH',
            'outputs':['SourcePassages','Citations','Summary'], 'spatial_execution':False}
    if typed is not None:
        project_execution_decision(typed, plan)
    citations = [{**p, 'citation_id':str(i)} for i,p in enumerate(passages,1)]
    final = {'task_id':state.get('task_id'), 'status':status, 'summary':answer, 'answer_text':answer,
             'error_code':error, 'clarification_questions':[], 'clarification_options':[],
             'coastal_evidence':evidence,
             'structured_result':{'status':status, 'answer_scope':'source_passages_only',
                                  'source_passages':passages, 'citations':citations,
                                  'source_text_audit':{'verified_passages':verified_count,
                                      'unverified_passages':len(passages)-verified_count,
                                      'excluded_mismatch_chunks':mismatch_count,
                                      'excluded_superseded_chunks':superseded_count,
                                      'scope':'AUDIT_SNAPSHOT_ONLY', 'semantic_correctness_verified':False},
                                  'coverage_complete':False, 'coordinate_authority':False,
                                  'search_execution':{'status':'NOT_RUN','reason':'Document information request; no spatial operation'},
                                  'document_lookup_status':evidence.get('document_lookup_status',evidence.get('status'))},
             'rag_evidence':citations, 'evidence_bundle':{'rag_evidence':citations,'spatial_feature_evidence':[]},
             'orchestrator_v2':{'route_plan':plan, 'query_execution_context':typed.model_dump(mode='json') if typed else None,
                                'fast_path':'dataset_source_passages'},
             'contract_version':'geollm.execution.v1'}
    return {'final_dict':final, 'status':status, 'task_plan':plan, 'error_message':None,
            'clarification_questions':[], 'query_execution_context':typed.model_dump(mode='json') if typed else None,
            'dataset_information_handled':True}
