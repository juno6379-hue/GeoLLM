"""Live SSE contracts for grounded slots -> ontology/KG -> tool bindings."""
import argparse
import json
from pathlib import Path
from scripts.check_geollm_web_samples import observe

CASES = [
    ('missing_location', '위치 없이 부근 사고를 찾아줘'),
    ('excluded_accident', '사고 말고 침선만 반경1해리 이내에서 찾아줘'),
    ('absent_accidents', '사고가 없는 구역을 찾아줘'),
    ('invalid_radius', '부산항 반경 -1km 이내 침선을 찾아줘'),
    ('grounded_chain', '부산항 입구 반경1해리 이내 침선을 찾아줘'),
    ('executed_radius', '부산항 반경1해리 이내 침선을 찾아줘'),
    ('duration', '부산항 최근 12개월 AIS 통항량을 구역별로 요약해줘'),
    ('positive_accident', '기관손상 사고 이력을 찾아줘'),
]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        raise ValueError('Use a new run file')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    passed = 0
    for case, query in CASES:
        row = observe('http://localhost:8000', case, query)
        final = (row.get('completion') or {}).get('final_result') or {}
        if case == 'executed_radius' and final.get('error_code') == 'LOCATION_UNCONFIRMED':
            # This is an explicit evaluation choice of a real server-returned harbour,
            # not fabricated user context and not a change to production ambiguity policy.
            candidates = [c for c in final.get('clarification_options', [])
                          if c.get('source_ref') == 'projection.s101_feature_valid'
                          and str(c.get('place_id', '')).startswith('harbour:')]
            if len(candidates) == 1:
                initial = row
                selected = candidates[0]
                context = {k:selected[k] for k in ('place_id','place_version','base_location','geometry','crs') if k in selected}
                context['selected_place_evidence'] = selected
                row = observe('http://localhost:8000', case, query, context)
                row['evaluation_context_policy'] = 'Confirm the unique source-backed harbour option returned by the API'
                row['initial_observation'] = initial
                final = (row.get('completion') or {}).get('final_result') or {}
        orch = final.get('orchestrator_v2') or {}
        trace = orch.get('candidate_trace') or {}
        analysis = orch.get('korean_query_analysis') or trace.get('korean_query_analysis') or {}
        binding = trace.get('semantic_slot_binding') or {}
        expected = {'missing_location':'LOCATION_REQUIRED', 'excluded_accident':'NEGATION_EXECUTION_NOT_SUPPORTED',
                    'absent_accidents':'NEGATION_EXECUTION_NOT_SUPPORTED', 'invalid_radius':'INVALID_QUANTITY'}
        if case in expected:
            ok = final.get('error_code') == expected[case] and (orch.get('query_execution_context') or {}).get('execution_status') == 'NOT_RUN'
        elif case == 'grounded_chain':
            tools = binding.get('capability_bindings') or []
            ok = ('Wreck' in binding.get('target_features', []) and bool(binding.get('kg_seed_ids'))
                  and bool(binding.get('kg_relations')) and any(t.get('bound_inputs', {}).get('radius_m', {}).get('evidence', {}).get('normalized_value') == 1852 for t in tools))
        elif case == 'duration':
            ok = any(s.get('normalized_value') == 'P12M' for s in analysis.get('slots', [])) and final.get('error_code') == 'TRAFFIC_PERIOD_NOT_COVERED'
        elif case == 'executed_radius':
            structured = final.get('structured_result') or {}
            ok = (final.get('status') == 'COMPLETED' and structured.get('distance_m') == 1852
                  and bool(structured.get('query_execution_id'))
                  and structured.get('analysis_type') == 'feature_search_by_radius'
                  and structured.get('total_count') is not None)
        else:
            ok = final.get('status') == 'COMPLETED' and (final.get('structured_result') or {}).get('analysis_type') == 'accident_event_lookup'
        ok = bool(ok and analysis.get('analyzer', {}).get('status') == 'AVAILABLE')
        row['contract_check_passed'] = ok
        with args.output.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(row, ensure_ascii=False)+'\n')
        passed += ok
        print(json.dumps({'case':case,'passed':ok,'status':final.get('status'),'error':final.get('error_code'),'seconds':row['elapsed_seconds']},ensure_ascii=False),flush=True)
    print(f'{passed}/{len(CASES)} live contracts; not semantic accuracy')
    return 0 if passed == len(CASES) else 1


if __name__ == '__main__':
    raise SystemExit(main())
