"""Live API regression probes for requested outputs and actual tool execution."""
import argparse
import json
from pathlib import Path
from scripts.check_geollm_web_samples import observe


CASES = [
    ('feature_mapping', '정박지는 S-101에서 어떤 Feature야?'),
    ('current_period', '부산항 최근 12개월 AIS 통항량을 구역별로 요약해줘'),
    ('loaded_period', '부산항 최신 적재 월 AIS 통항량을 분석해줘'),
    ('missing_location', '최근 1년간 AIS/V-PASS 통항량을 분석해줘'),
    ('separation_geometry', '인천항 주변 통항분리구역을 표시해줘'),
    ('coverage', 'AIS와 V-PASS 데이터는 어느 기간까지 적재되어 있어?'),
    ('vector_operator', 'capability_embeddings 테이블과 pgvector top-k가 동작하는지 확인해줘'),
    ('trace_context', 'Ontology/KG validator가 후보를 제거한 이유를 설명해줘'),
    ('legal_document', '인천항 선박통항규칙을 찾아줘'),
    ('embedding_coverage', 'Dataset 폴더 안의 embedding 완료 현황을 요약해줘'),
    ('resolver_registry', 'Resolver Registry에서 사용 가능한 해양 resolver 목록을 보여줘'),
    ('accident_filters', '최근 사고 이력'),
    ('accident_filters', '사고 찾아줘'),
]


def check(case, final):
    structured = final.get('structured_result') or {}
    orch = final.get('orchestrator_v2') or {}
    plan = orch.get('route_plan') or {}
    if case == 'feature_mapping':
        return structured.get('feature_code') == 'AnchorageArea' and plan.get('intent') == 'DEFINITION'
    if case == 'current_period':
        return final.get('error_code') == 'TRAFFIC_PERIOD_NOT_COVERED' and plan.get('slots', {}).get('location_text') == '부산항'
    if case == 'loaded_period':
        tools = (orch.get('query_execution_context') or {}).get('tool_bindings') or []
        return final.get('status') == 'COMPLETED' and structured.get('monthly_breakdown') and any(t.get('status') == 'EXECUTED' and t.get('snapshot') for t in tools)
    if case == 'missing_location':
        return final.get('status') == 'NEEDS_CLARIFICATION' and final.get('error_code') == 'LOCATION_REQUIRED'
    if case == 'separation_geometry':
        return plan.get('intent') != 'TRAFFIC_ANALYSIS' and final.get('status') in {'NEEDS_CLARIFICATION', 'COMPLETED'}
    if case == 'coverage':
        return structured.get('analysis_type') == 'traffic_coverage' and all(r.get('months') for r in structured.get('rows', [])) and bool(structured.get('rows'))
    if case == 'vector_operator':
        return final.get('status') == 'PARTIAL' and len(structured.get('rows', [])) > 0
    if case == 'trace_context':
        return final.get('error_code') == 'DIAGNOSTIC_TASK_REQUIRED'
    if case == 'embedding_coverage':
        return final.get('status') == 'PARTIAL' and 'chunk_count' in (structured.get('rows') or [{}])[0]
    if case == 'resolver_registry':
        return final.get('status') == 'PARTIAL' and bool(structured.get('rows'))
    if case == 'accident_filters':
        return final.get('error_code') == 'ACCIDENT_FILTERS_REQUIRED' and final.get('status') == 'NEEDS_CLARIFICATION'
    return plan.get('intent') != 'TRAFFIC_ANALYSIS' and bool((final.get('evidence_bundle') or {}).get('regulatory_evidence'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--base-url', default='http://localhost:8000')
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        raise ValueError('Preserve prior evidence; choose a new output file')
    passed = 0
    for case, query in CASES:
        row = observe(args.base_url, case, query)
        final = (row.get('completion') or {}).get('final_result') or {}
        row['contract_check_passed'] = bool(check(case, final))
        passed += row['contract_check_passed']
        with args.output.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(row, ensure_ascii=False) + '\n')
        print(json.dumps({'case': case, 'passed': row['contract_check_passed'], 'status': final.get('status'), 'error': final.get('error_code')}, ensure_ascii=True), flush=True)
    print(f'Contract checks: {passed}/{len(CASES)}; not a semantic accuracy measurement')
    return 0 if passed == len(CASES) else 1


if __name__ == '__main__':
    raise SystemExit(main())
