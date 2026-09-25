"""Compare observed pipeline stages without turning completion states into gold labels."""
import argparse
import json
from pathlib import Path

from services.orchestrator.intent_shadow import fingerprint
from scripts.check_geollm_web_samples import observed_status


def stages(row):
    final = (row.get('completion') or {}).get('final_result') or {}
    orch = final.get('orchestrator_v2') or {}
    trace = orch.get('candidate_trace') or {}
    plan = orch.get('route_plan') or {}
    qec = orch.get('query_execution_context') or {}
    structured = final.get('structured_result') or {}
    analysis = orch.get('korean_query_analysis') or trace.get('korean_query_analysis') or {}
    binding = trace.get('semantic_slot_binding') or {}
    return {'observation':row.get('observation'), 'task_id':row.get('task_id'),
            'status':observed_status(row), 'error_code':final.get('error_code'),
            'execution_error':(row.get('completion') or {}).get('error_message'),
            'route':plan.get('intent'), 'analysis_type':structured.get('analysis_type'),
            'plan_slots':plan.get('slots'), 'source_quantity_slots':analysis.get('slots'),
            'constraints':analysis.get('constraints'), 'candidate_routes':trace.get('route_candidates'),
            'capabilities':[c.get('candidate_id') for c in trace.get('capability_candidates',[])],
            'kg_seed_ids':binding.get('kg_seed_ids'), 'source_sha256':binding.get('source_sha256'),
            'capability_bindings':binding.get('capability_bindings'),
            'planned_tools':plan.get('tools'), 'tool_bindings':qec.get('tool_bindings'),
            'output_obligations':orch.get('output_obligations'),
            'execution_observation':{k:structured.get(k) for k in
                ('query_execution_id','result_id','count','total_count','returned_count','distance_m','target_features','source_ref')},
            'evidence_counts':{k:len(v) for k,v in (final.get('evidence_bundle') or {}).items() if isinstance(v,list)},
            'latency_seconds':row.get('elapsed_seconds')}


def read_rows(path):
    rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
    indexed = {r['sample']:r for r in rows}
    if len(indexed) != len(rows):
        raise ValueError('Duplicate case IDs')
    return indexed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before',type=Path,required=True)
    parser.add_argument('--after',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    before, after = read_rows(args.before), read_rows(args.after)
    if before.keys() != after.keys():
        raise ValueError('Compare the same case IDs; do not silently drop failures')
    cases = []
    for identifier in sorted(before):
        if before[identifier]['query'] != after[identifier]['query']:
            raise ValueError('Case query changed')
        left, right = stages(before[identifier]), stages(after[identifier])
        cases.append({'sample':identifier,'query':before[identifier]['query'],'before':left,'after':right,
                      'changed_stages':[k for k in ('status','error_code','route','analysis_type','planned_tools') if left[k]!=right[k]],
                      'review_status':'SEMANTIC_REVIEW_REQUIRED'})
    report = {'before_sha256':fingerprint(before),'after_sha256':fingerprint(after),'cases':cases,
              'semantic_accuracy':None,'used_for_execution':False,
              'limitations':['This is an observed stage comparison, not independent gold.',
                             'A tool binding is a request contract, not proof of execution.',
                             'Counts and execution IDs are preserved; completeness requires task-specific evidence review.']}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x',encoding='utf-8') as stream:
        json.dump(report,stream,ensure_ascii=False,indent=2)
    print(json.dumps({'cases':len(cases),'changed':sum(bool(c['changed_stages']) for c in cases),
                      'observation_errors':[c['sample'] for c in cases if c['after']['observation']!='COMPLETED_EVENT_RECEIVED']}))


if __name__=='__main__':
    main()
