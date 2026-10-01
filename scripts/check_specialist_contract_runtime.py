"""Read-only live source/agent checks; not an HTTP or browser test."""
import argparse
import asyncio
import json
import os
from pathlib import Path
import time
import uuid

from shared.schemas.agent import AgentRequest, ExecutionSlots, QueryExecutionContext, SecurityContext
from services.orchestrator.agent_registry import registry


async def check(case):
    agent, operation, query = {
        'rag': ('Standard RAG Agent', 'document_search', '수로 측량 데이터 품질 관리 관련 근거 문서를 검색해줘'),
        'accident': ('Accident/Risk Agent', 'accident_relation_lookup', '선택한 객체의 사고 관계를 조회해줘'),
        'tidal': ('Time-Series Agent', 'observed_time_series_analysis', '수치조류 관측값을 분석해줘'),
        'fixture': ('Time-Series Agent', 'observed_time_series_analysis', '관측 시계열을 분석해줘'),
        'missing': ('Time-Series Agent', 'observed_time_series_analysis', '미등록 관측 시계열을 분석해줘'),
    }[case]
    task = 'source-check-' + str(uuid.uuid4())
    slots = ExecutionSlots()
    if case == 'accident':
        import psycopg2
        with psycopg2.connect(os.environ['S101_DB_URL'], connect_timeout=5) as conn:
            conn.set_session(readonly=True)
            with conn.cursor() as cursor:
                cursor.execute("SET LOCAL statement_timeout='10s'")
                cursor.execute('SELECT feature_instance_id FROM serving.accident_s101_relation_current WHERE feature_instance_id IS NOT NULL LIMIT 1')
                row = cursor.fetchone()
                if not row:
                    raise RuntimeError('No real accident relation source row available')
                slots.feature_instance_id = row[0]
    if case in {'tidal', 'fixture', 'missing'}:
        slots.filters = {'dataset_id': {'tidal': 'tidal_current_surface', 'fixture': 'sample_observation_timeseries',
                                       'missing': 'unregistered_observation'}[case]}
    qec = QueryExecutionContext(request_id=task, task_id=task, original_query=query,
        route_plan={'analysis_type': operation, 'primary_agent': agent}, slots=slots)
    request = AgentRequest(task_id=task, trace_id=task, user_id='runtime-contract-check', organization_id='test',
        original_query=query, agent_name=agent, security_context=SecurityContext(clearance_level='PUBLIC'),
        query_execution_context=qec)
    started = time.monotonic()
    result = await registry.get_execute_function(agent)(request)
    payload = result.model_dump(mode='json')
    receipt = payload.get('provenance', {}).get('execution_validation') or {}
    if case in {'tidal', 'fixture', 'missing'}:
        passed = payload['status'] == 'BLOCKED' and receipt.get('readiness') != 'EXECUTION_READY' and not payload.get('tool_calls')
    else:
        passed = payload['status'] == 'COMPLETED' and receipt.get('authority') == 'ExecutionValidator'
        count = payload.get('structured_result', {}).get('retrieved_count' if case == 'rag' else 'count', 0)
        passed = passed and count > 0
    return {'case': case, 'mode': 'live_agent_direct_not_http', 'seconds': round(time.monotonic()-started, 3),
            'passed': bool(passed), 'result': payload}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=['rag', 'accident', 'tidal', 'fixture', 'missing'], required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as output:
        try:
            row = asyncio.run(check(args.case))
        except Exception as exc:
            row = {'case': args.case, 'passed': False, 'error_type': type(exc).__name__}
        output.write(json.dumps(row, ensure_ascii=False, indent=2))
    print(json.dumps({k: v for k, v in row.items() if k != 'result'}, ensure_ascii=False), flush=True)
    raise SystemExit(0 if row['passed'] else 1)


if __name__ == '__main__':
    main()
