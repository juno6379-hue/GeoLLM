"""Read-only runtime diagnostics, separate from document retrieval."""
import re
import json
import psycopg2
from psycopg2.extras import RealDictCursor


def diagnostic_request(query):
    text = str(query or '').casefold()
    if not re.search(r'확인|동작|적재|근거|이유|보여|설명|현황', text):
        return None
    if re.search(r'multi-label|validator|후보.*제거', text):
        return 'execution_trace'
    if 'capability_embeddings' in text or 'pgvector' in text:
        return 'capability_vector'
    if 'resolver' in text and re.search(r'registry|목록', text):
        return 'resolver_registry'
    if re.search(r'embedding|임베딩', text) and re.search(r'완료|현황|전체|coverage', text):
        return 'document_coverage'
    if re.search(r'ais|v-pass|vpass', text) and '적재' in text and re.search(r'기간|까지|월|언제', text) and not re.search(r'(통항량|교통량).*(분석|집계|요약|보여)', text):
        return 'traffic_coverage'
    return None


def diagnostic_response(state):
    from services.orchestrator.query_candidate_broker import _db_url
    from services.orchestrator.traffic_execution import _db_url as traffic_db_url
    from services.orchestrator.traffic_execution import TrafficProblem
    kind = diagnostic_request(state.get('query'))
    from services.orchestrator.execution_validator import validate_lookup_request, is_execution_authorized, execution_gate_failure, attach_execution_decision
    validated = None
    if kind != 'execution_trace':
        validated = validate_lookup_request(state, kind)
        if not is_execution_authorized(validated):
            return execution_gate_failure(state, validated)['final_dict']
    status, code, rows, relation, snapshot = 'COMPLETED', None, [], None, None
    if kind == 'execution_trace':
        status, code = 'NEEDS_CLARIFICATION', 'DIAGNOSTIC_TASK_REQUIRED'
        answer = '검토할 원래 질의 또는 작업 ID를 알려주세요. 해당 작업의 후보·슬롯·validator 기록이 있어야 제거·차단 이유를 판단할 수 있습니다.'
    elif kind == 'resolver_registry':
        from services.orchestrator.query_candidate_broker import _load_registry
        rows = [{key: entry.get(key) for key in ('capability_id','label','routes','input_slots','output_slots','authority_ref','registry_ref')}
                for entry in _load_registry().get('capabilities', []) if entry.get('object_type') == 'resolver_description']
        relation, status = 'data/capability_registry.yaml', 'PARTIAL'
        snapshot = {'source': relation, 'verification_scope': 'registry_declarations_only'}
        answer = f'실제 registry에 등록된 resolver {len(rows)}개와 입력·출력 계약을 반환했습니다. 등록 여부이며 개별 원천/도구의 현재 실행 가능 여부는 별도 검증이 필요합니다.'
    else:
        try:
            url = traffic_db_url() if kind == 'traffic_coverage' else _db_url()
            if not url:
                raise ValueError('DB_NOT_CONFIGURED')
            with psycopg2.connect(url, connect_timeout=3) as conn:
                conn.set_session(readonly=True, isolation_level='REPEATABLE READ')
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SET LOCAL statement_timeout = '5000ms'")
                    if kind == 'traffic_coverage':
                        relation = 'serving.dynamic_traffic_layer'
                        cur.execute("""SELECT layer_source, count(*) AS row_count,
                            min(observed_month) AS first_month, max(observed_month) AS last_month,
                            array_agg(DISTINCT to_char(observed_month,'YYYYMM') ORDER BY to_char(observed_month,'YYYYMM')) AS months
                            FROM serving.dynamic_traffic_layer GROUP BY layer_source ORDER BY layer_source""")
                    elif kind == 'document_coverage':
                        relation = 'knowledge.document_chunks'
                        cur.execute("""SELECT count(*) AS chunk_count, count(embedding) AS embedded_count,
                            count(*) FILTER (WHERE embedding IS NULL) AS missing_embedding_count,
                            count(DISTINCT coalesce(metadata->>'source_file',metadata->>'source_path')) AS source_count
                            FROM knowledge.document_chunks
                            WHERE replace(coalesce(metadata->>'source_file',metadata->>'source_path',''), chr(92), '/') ILIKE %s""", ('%Dataset/%',))
                    else:
                        relation = 'knowledge.capability_embeddings'
                        cur.execute("""WITH seed AS (SELECT id, embedding FROM knowledge.capability_embeddings
                            WHERE embedding IS NOT NULL ORDER BY id LIMIT 1)
                            SELECT c.id, c.object_id, c.label, c.embedding <=> seed.embedding AS cosine_distance,
                                   seed.id AS seed_id
                            FROM knowledge.capability_embeddings c CROSS JOIN seed
                            WHERE c.embedding IS NOT NULL ORDER BY c.embedding <=> seed.embedding, c.id LIMIT 5""")
                    rows = [dict(row) for row in cur.fetchall()]
                    cur.execute('SELECT transaction_timestamp()::text AS captured_at, txid_current_snapshot()::text AS snapshot')
                    snapshot = dict(cur.fetchone())
            if kind == 'traffic_coverage':
                answer = '\n'.join(f"{r['layer_source']}: {r['first_month']}~{r['last_month']}, {len(r['months'])}개월, {r['row_count']}행" for r in rows)
                answer += '\n실제 적재 월 목록을 함께 반환했습니다. 기간 사이의 연속 적재를 가정하지 않습니다.'
            elif kind == 'document_coverage':
                status = 'PARTIAL'
                r = rows[0]
                answer = f"메타데이터 원천 경로에 Dataset/이 기록된 {r['source_count']}개 원천, {r['chunk_count']}개 청크 중 embedding 보유 {r['embedded_count']}개, NULL {r['missing_embedding_count']}개입니다. 원천 경로가 누락된 청크와 아직 등록되지 않은 파일은 포함하지 않아 폴더 전체 완료로 판정하지 않습니다."
            else:
                status = 'PARTIAL'
                answer = f'실제 저장 벡터로 pgvector cosine top-k를 실행해 {len(rows)}개를 반환했습니다. DB 연산 확인이며 새 질의의 임베딩 생성과 라우팅 품질은 별도 검증이 필요합니다.'
            if not rows:
                status, code = 'BLOCKED', 'DIAGNOSTIC_NO_ROWS'
        except (psycopg2.Error, ValueError, TrafficProblem) as exc:
            status, code = 'BLOCKED', 'DIAGNOSTIC_DB_ERROR'
            answer = '진단 SQL을 완료하지 못했습니다. DB 연결·테이블·벡터 연산을 점검해야 합니다.'
            relation = None
    rows = json.loads(json.dumps(rows, default=str, ensure_ascii=False))
    tool = {'tool_id': 'diagnostics.' + kind, 'status': 'EXECUTED' if snapshot else 'BLOCKED', 'relation': relation, 'snapshot': snapshot}
    plan = {'intent': 'DATA_DISCOVERY', 'analysis_type': kind, 'slots': {'diagnostic_target': kind},
            'tools': [tool['tool_id']], 'outputs': ['DiagnosticEvidence'], 'status': status,
            'execution_ready': False, 'clarification_required': status == 'NEEDS_CLARIFICATION'}
    context = {'readiness': status, 'tool_bindings': [tool], 'data_bindings': [{'relation': relation}] if relation else [],
               'blockers': [code] if code else [], 'warnings': []}
    final = {'task_id': state['task_id'], 'status': status, 'error_code': code, 'answer_text': answer, 'summary': answer,
             'structured_result': {'analysis_type': kind, 'rows': rows, 'status': status},
             'orchestrator_v2': {'route_plan': plan, 'query_execution_context': context, 'fast_path': 'live_pipeline_diagnostics'},
             'evidence_bundle': {'diagnostic_evidence': [{'source_ref': relation, 'snapshot': snapshot, 'rows': rows}] if snapshot else []}}
    if status == 'NEEDS_CLARIFICATION':
        final['clarification_questions'] = [answer]
    if validated is not None:
        attach_execution_decision(final, validated)
    return final
