"""Measure added analysis cost and request-scoped reference deduplication."""
import argparse
import json
import math
import time
from pathlib import Path
from services.orchestrator.korean_query_analysis import analyze_query
from services.orchestrator.semantic_slot_binding import bind_semantic_slots
from services.orchestrator import query_candidate_broker as broker


def stats(values):
    ordered = sorted(values)
    return {'n':len(values),'p50_ms':ordered[math.ceil(len(ordered)*.5)-1], 'p95_ms':ordered[math.ceil(len(ordered)*.95)-1]}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():
        raise ValueError('Use a new run file')
    rows=[json.loads(line) for line in args.baseline.read_text(encoding='utf-8').splitlines()]
    first=analyze_query(rows[0]['query'])
    timings=[]
    bindings=[]
    for row in rows:
        trace=(((row.get('completion') or {}).get('final_result') or {}).get('orchestrator_v2') or {}).get('candidate_trace') or {}
        analysis=analyze_query(row['query'])
        binding=bind_semantic_slots(row['query'],analysis,trace.get('capability_candidates') or [])
        timings.append(analysis['latency_ms'])
        bindings.append(binding['latency_ms'])
    candidates=[]
    for row in rows:
        trace=(((row.get('completion') or {}).get('final_result') or {}).get('orchestrator_v2') or {}).get('candidate_trace') or {}
        if len(trace.get('capability_candidates') or []) > len(candidates):
            candidates=trace['capability_candidates']
    refs=[ref for c in candidates for ref in (c.get('authority_ref'),c.get('registry_ref'))]
    start=time.monotonic()
    for ref in refs:
        broker._verify_reference(ref)
    before=(time.monotonic()-start)*1000
    start=time.monotonic()
    broker._verify_candidates(candidates)
    after=(time.monotonic()-start)*1000
    report={'cold_analyzer_ms':first['latency_ms'],'analyzer':first['analyzer'],'warm_analyzer':stats(timings),
            'semantic_binding_including_first_index_build':stats(bindings),'first_binding_ms':bindings[0],
            'reference_probe':{'candidate_count':len(candidates),'before_calls':len(refs),'after_calls':len(set(refs)),
                               'before_ms':round(before,3),'after_ms':round(after,3)},
            'limitation':'One ordered reference probe, cache/order effects possible; no end-to-end speedup or accuracy claim'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))


if __name__ == '__main__':
    main()
