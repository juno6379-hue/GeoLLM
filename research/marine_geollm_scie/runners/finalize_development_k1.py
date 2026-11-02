"""Finalize fresh Development K1 after raw-linked RQ1 annotation; no model calls.

Observation completion is distinct from independent human accuracy, K5,
ablation and untouched holdout completion. Old runs are never rewritten.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path

from .supervise_development_k1 import verify_frozen, sha, write, BENCHMARK, FAULTS
from .report_eight import verify_raw
from .rq1_reviewed_measurement import run as measure_rq1, CONTRACT_SHA256


def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def jsonl(path):return [json.loads(s) for s in Path(path).read_text(encoding='utf-8').splitlines() if s.strip()]


def inside(root,name):
    path=(Path(root)/name).resolve()
    if not path.is_relative_to(Path(root).resolve()):raise ValueError('Artifact path escapes run')
    return path


def verify_base(run):
    observations=run/'comparison/observations.jsonl'
    provenance=read(run/'base_report/manifest.json')
    if provenance['observations_sha256']!=sha(observations):raise ValueError('Base observation SHA mismatch')
    for name,digest in provenance['report_files'].items():
        if sha(inside(run/'base_report',name))!=digest:raise ValueError('Base report changed')
    rows=jsonl(observations)
    if Counter(r['method'] for r in rows)!=Counter(dict.fromkeys(('B0','B1','B2','B3','B4','P0','H','P1'),18)):
        raise ValueError('Expected 144 new method observations')
    summary=read(run/'base_report/summary.json')
    if summary['completion_gate']['observation_comparison_complete'] is not True:raise ValueError('Base completion gate failed')
    for row in rows:
        raw=read(verify_raw(observations.parent.resolve(),row))
        if raw.get('query')!=row.get('query'):raise ValueError('Raw query projection mismatch')
    # Recompute sharing/cohort gates; a preserved summary is not a verifier.
    from ..reliability.research_release_gate import report_gate
    manifest=read(run/'comparison/manifest.json');profile=read(run/'profiles/baseline_profile.json')
    bundle=read(run/'measurement_freeze.json')
    profile_path=(run/'profiles/baseline_profile.json').resolve()
    if not any(Path(e['path']).resolve()==profile_path and e['sha256']==sha(profile_path)
               for e in bundle.get('measurement_files',[])):
        raise ValueError('Baseline profile absent from measurement freeze')
    if (manifest.get('status')!='COMPLETED_OBSERVATIONS' or manifest.get('expected_rows')!=144 or
        manifest.get('profile_sha256')!=sha(profile_path)):
        raise ValueError('Comparison collection/profile gate failed')
    if provenance.get('run_manifest_sha256')!=sha(run/'comparison/manifest.json'):
        raise ValueError('Comparison manifest changed')
    if (manifest.get('execution_identity')!=profile.get('execution_identity') or
        profile.get('snapshot_manifest')!=bundle.get('snapshot_manifest') or
        profile.get('execution_identity',{}).get('source_snapshot_sha256')!=bundle['snapshot_manifest']['sha256'] or
        manifest.get('benchmark_sha256')!=bundle.get('benchmark_manifest_sha256') or
        provenance.get('benchmark_sha256')!=bundle.get('benchmark_manifest_sha256')):
        raise ValueError('Fresh execution identity differs from frozen profile/snapshot/GOLD')
    if manifest.get('repeats')!=[0]:raise ValueError('Development K1 requires exactly repeat zero')
    contracts=jsonl(BENCHMARK/'answer_contracts.jsonl')
    queries={r['case_id']:r['query'] for r in jsonl(BENCHMARK/'queries.jsonl')}
    if len(contracts)!=18:raise ValueError('Expected 18 development contracts')
    for row in rows:
        if row.get('query')!=queries.get(row['case_id']):raise ValueError('Frozen query mismatch')
        if row.get('execution_identity')!=profile['execution_identity']:
            raise ValueError('Recomputed base gate failed: full execution identity mismatch')
    gate=report_gate(case_ids=[r['case_id'] for r in contracts],repeats=[0],observations=rows,
        execution_identity=profile['execution_identity'],benchmark_sha256=bundle['benchmark_manifest_sha256'],
        raw_integrity_verified=True)
    if gate['observation_comparison_complete'] is not True:
        raise ValueError('Recomputed base gate failed: '+str(gate['errors']))
    return rows,summary


def verify_diagnostics(run):
    from .rq3_execution_faults import verify_contract,score_execution
    folder=run/'rq3_diagnostics';contract,digest=verify_contract(run/'rq3_contract')
    summary=read(folder/'summary.json');rows=read(folder/'observations.json')
    cases={c['case_id']:c for c in contract['cases']}
    if (summary.get('status')!='COMPLETED' or summary.get('observations')!=8 or
        summary.get('sources_unchanged') is not True or summary.get('contract_sha256')!=digest or
        summary.get('source_before')!=contract['frozen_code'] or summary.get('source_after')!=contract['frozen_code'] or
        len(cases)!=8 or len(rows)!=8 or {r['case_id'] for r in rows}!=set(cases)):
        raise ValueError('Spatial fault diagnostic cohort/source gate failed')
    for row in rows:
        case=cases[row['case_id']];rawpath=inside(folder,row['raw_file'])
        if sha(rawpath)!=row['raw_sha256']:raise ValueError('RQ3 diagnostic raw changed')
        raw=read(rawpath)
        if raw['observation']!={k:v for k,v in row.items() if k not in ('raw_file','raw_sha256')}:
            raise ValueError('RQ3 diagnostic projection differs from raw')
        expected_job={'method':'COMMON_EXECUTOR_DIAGNOSTIC','case_id':case['case_id'],'repeat_id':1,'plan':case['plan']}
        if (raw['job']!=expected_job or row['contract_sha256']!=digest or row['fault']!=case['fault'] or
            row.get('method')!='COMMON_EXECUTOR_DIAGNOSTIC' or row.get('repeat_id')!=1):
            raise ValueError('RQ3 diagnostic job/contract mismatch')
        oracle=read(inside(run/'rq3_contract',case['oracle_file']))
        score=score_execution(case,oracle,row['execution'],row['injections'])
        if any(row.get(k)!=v for k,v in score.items()):raise ValueError('RQ3 diagnostic score not reproduced')
        if score['execution_success'] is not True or score['spatial_correct'] is not (case['fault']=='clean'):
            raise ValueError('RQ3 actual SQL execution/Oracle gate failed')
    return rows


def finalize(run,reviews,output):
    run=Path(run).resolve();output=Path(output).resolve()
    if output.exists():raise FileExistsError('New report directory required')
    if output.is_relative_to(run/'comparison'):raise ValueError('Derived report must not enter raw comparison folder')
    preserved={p:sha(p) for p in run.rglob('*') if p.is_file()}
    reviews=Path(reviews).resolve();review_digest=sha(reviews)
    state=read(run/'status.json')
    if state['status']!='COLLECTED_PENDING_RQ1_ANNOTATION_AND_FINAL_REPORT':raise ValueError('Collection must finish successfully first')
    bundle=read(run/'measurement_freeze.json');verify_frozen(bundle)
    rows,base=verify_base(run)
    graph=read(run/'graph/model_graph_manifest.json')
    if graph.get('observed_rows')!=18 or graph.get('source_unchanged_after') is not True:
        raise ValueError('P1 graph completion/source gate failed')
    if (graph.get('snapshot_manifest_sha256')!=bundle['snapshot_manifest']['sha256'] or
        graph.get('profile_sha256')!=sha(run/'profiles/model_profile.json') or
        graph.get('benchmark_sha256')!=sha(run/'profiles/common_inputs.jsonl')):
        raise ValueError('P1 graph differs from frozen execution inputs')
    # Independently re-run the report verifier over preserved fault raw artifacts.
    output.mkdir(parents=True)
    from .expanded_fault_runner import report as fault_report
    faults=fault_report(run/'expanded_faults',FAULTS,output/'fault_reverification')
    if faults['raw_observation_rows']!=207:raise ValueError('Expected 207 expanded fault observations')
    if read(run/'expanded_faults/manifest.json').get('execution_identity')!=read(run/'profiles/baseline_profile.json')['execution_identity']:
        raise ValueError('Fault run differs from frozen execution identity')
    verify_diagnostics(run)
    # Recompute derived reports instead of trusting manually edited summaries.
    from .report_rq5 import run as report_costs
    costs=report_costs(run/'comparison/observations.jsonl',output/'rq5',scores=run/'base_report')
    if costs['status']!='COMPLETE_OBSERVATION_COHORT':raise ValueError('RQ5 cohort gate failed')
    from .report_rq3_methods import run as report_spatial
    report_spatial(run/'comparison',run/'base_report',BENCHMARK,output/'rq3_methods')
    measure_rq1(run/'comparison/observations.jsonl',output/'rq1',reviews=reviews,
        gold=BENCHMARK.parent/'grounding_atoms_20261102_v1/gold_atoms.jsonl')
    rq1=read(output/'rq1/status.json')
    if rq1.get('measured') is not True or rq1.get('observations')!=36 or rq1['contract_sha256']!=CONTRACT_SHA256:
        raise ValueError('New-answer RQ1 annotation gate failed')
    verify_frozen(bundle)
    if sha(reviews)!=review_digest or any(not p.is_file() or sha(p)!=digest for p,digest in preserved.items()):
        raise ValueError('Preserved run/reviews changed during finalization')
    result={'status':'DEVELOPMENT_K1_MEASUREMENT_COMPLETE','base_observations':len(rows),
        'fault_observations':faults['raw_observation_rows'],'spatial_fault_diagnostics':8,
        'rq1_raw_reviews':36,'rq1_ai_annotation':True,'human_new_answer_accuracy_complete':False,
        'k5_complete':False,'ablation_complete':False,'holdout_used':False,'scientific_completion':False,
        'source_run':str(run),'measurement_freeze_sha256':sha(run/'measurement_freeze.json'),
        'observations_sha256':sha(run/'comparison/observations.jsonl'),
        'review_file':str(Path(reviews).resolve()),'review_sha256':sha(reviews),
        'finished_at':datetime.now(timezone.utc).isoformat(),
        'limitations':['Development K1 only; no repeated-run variability estimate.',
            'RQ1 predictions are AI-reviewed atoms, not independent human answer labels.',
            'Three fault source bases; paired variants are not independent population samples.',
            'RQ3 injected SQL diagnostics are separate from method mitigation performance.',
            'Unknown semantic/evidence quality and unsupported metric denominators remain null.',
            'Ablation, K5 and final frozen holdout remain separate later gates.']}
    lines=['# RQ1–RQ5 Development K1 결과','',
        '새 동결 조건에서 8방법×18문항 144개, 별도 오류 대조 207개, 실제 SQL 진단 8개를 수집·검증했습니다.',
        'RQ1 새 답변 36개의 원문 연결 AI 측정주석을 완료했습니다. 독립 인간 답변 정확도와 구분합니다.','',
        '- RQ1 조건별 F1·Strict Match·paired CI: [조건별 비교](rq1/condition_comparison.json)',
        '- RQ2 오류 검출·목표 코드·정상 오차단 및 RQ4 객체 복원: [대조 결과](fault_reverification/comparison_KR.md)',
        '- RQ3 방법별 실행·공간 정답·격차와 CI: [방법별 산출물](rq3_methods/)',
        '- RQ5 실제 호출·토큰·SQL·지연 및 미측정: [비용 결과](rq5/rq5_report_KR.md)','',
        '기존 실험 원본과 운영 코드를 보존했습니다. 홀드아웃을 개발에 사용하지 않았습니다.','',
        *['- '+item for item in result['limitations']]]
    (output/'comparison_KR.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    result['report_files']={p.relative_to(output).as_posix():sha(p) for p in output.rglob('*') if p.is_file()}
    write(output/'manifest.json',result)
    state.update(status=result['status'],stage='FINALIZED',final_report=str(output),
        final_report_manifest_sha256=sha(output/'manifest.json'),scientific_completion=False,
        required_next=['K1_error_review','K5_after_frozen_contracts','final_system_freeze_then_untouched_holdout'])
    write(run/'status.json',state)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--reviews',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();print(json.dumps(finalize(a.run,a.reviews,a.output),ensure_ascii=False))
