"""Table 11 bridge from verified, unchanged eight-method raw observations."""
import argparse,hashlib,json
from pathlib import Path
from ..evaluation.rq3_contract import METHODS,method_table,paired_ci
from ..evaluation.v2_results import score_row,spatial_eligible
from .freeze_v2_benchmark import verify
from .report_eight import verify_raw

ROOT=Path(__file__).resolve().parents[3]
VERSION='rq3_method_table11.v1'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def identity(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def jsonl(path):return [json.loads(x) for x in Path(path).read_text(encoding='utf8').splitlines() if x.strip()]
def key(row):return row['method'],row['case_id'],row['repeat']

def build_cohort(rows,scores,contracts,queries,contract_hash,repeat):
    bycase={c['case_id']:c for c in contracts};querymap={q['case_id']:q['query'] for q in queries}
    if len(bycase)!=len(contracts) or len(querymap)!=len(queries) or set(bycase)!=set(querymap):
        raise ValueError('Benchmark case/query identity mismatch')
    indexed={key(r):r for r in rows};scored={key(r):r for r in scores}
    expected={(m,c,repeat) for m in METHODS for c in bycase}
    if len(indexed)!=len(rows) or len(scored)!=len(scores) or set(indexed)!=expected or set(scored)!=expected:
        raise ValueError('Exact same complete method/case/repeat cohort required')
    cases=[]
    for cid,contract in bycase.items():
        cases.append({'case_id':cid,'equivalence_group':contract.get('equivalence_group',cid),
            'eligible':spatial_eligible(contract),'query_sha256':hashlib.sha256(querymap[cid].encode()).hexdigest(),
            'oracle_sha256':identity(contract),'query_condition':contract.get('category'),
            'stratum':contract['evaluation_stratum'],
            'oracle_identity_scope':'FULL_CASE_ANSWER_CONTRACT_INCLUDING_SPATIAL_GOLD_AND_MACHINE_CHECKS'})
    caseindex={c['case_id']:c for c in cases};observations=[]
    for k,row in indexed.items():
        cid=row['case_id'];score=scored[k];case=caseindex[cid]
        if row.get('query')!=querymap[cid]:raise ValueError('Raw query differs from frozen query')
        if score.get('equivalence_group')!=case['equivalence_group'] or score.get('execution_correctness_gap_applicable') is not case['eligible']:
            raise ValueError('Scored eligibility/equivalence differs from GOLD contract')
        fresh=score_row(row,bycase[cid])
        for field in ('execution_succeeded','spatial_correctness','execution_correctness_gap_applicable','checks','equivalence_group','stratum'):
            if score.get(field)!=fresh.get(field):raise ValueError('Stored score not reproduced: '+field)
        observations.append({**case,'method':row['method'],'repeat_id':repeat,'contract_sha256':contract_hash,
            'raw_artifact_sha256':row['raw_artifact_sha256'],'execution_success':score['execution_succeeded'],
            'spatial_correct':score['spatial_correctness'],'semantic_correct':None,'evidence_correct':None})
    table=method_table(observations,cases,repeat_ids=(repeat,),contract_sha256=contract_hash)
    eligible={m:[r for r in observations if r['method']==m and r['eligible']] for m in METHODS}
    pairs={}
    for target in ('P0','P1'):
        pairs['B3_vs_'+target]=(paired_ci(eligible['B3'],eligible[target]) if eligible['B3'] else
            {'status':'UNMEASURED','reason':'NO_GOLD_SELECTED_SPATIAL_CASES'})
    return {'version':VERSION,'methods':table,'paired_comparisons':pairs,'cohort':cases,'observations':observations,
        'common_spatial_case_ids':[c['case_id'] for c in cases if c['eligible']],
        'excluded_case_ids':[c['case_id'] for c in cases if not c['eligible']],
        'contract_sha256':contract_hash,'model_calls':0,'fault_diagnostic_rows_included':0,
        'definitions':{
            'ESR':'Actual spatial execution success / same GOLD-selected eligible cohort including failures and missing measurements',
            'raw_spatial_correctness':'Spatial answer correctness under this frozen case contract, independent of whether execution succeeded',
            'Spatial_Correct':'Joint execution AND spatial correctness / same eligible cohort',
            'CGE':'Conditional spatial correctness among successful executions; NOT ESR minus spatial correctness',
            'SSFR':'Spatial incorrectness among successful executions; no successful executions means null, not zero',
            'execution_correctness_gap':'ESR minus joint execution/spatial correctness',
            'EVQSR':'Unmeasured: this bridge does not import independent exact-answer semantic/evidence judgments',
            'paired_CI':'B minus A: P0/P1 minus B3; paired equivalence-cluster bootstrap, 2000 draws, seed 20261103'},
        'limitations':['K1 development observations, not holdout or independent human semantic accuracy.',
            'Raw spatial correctness is limited to the frozen machine checks; no unmeasured geometry/relation criterion is invented.',
            'Missing E/S remains unknown; zero successful-execution denominator keeps CGE/SSFR null.',
            'Fault SQL diagnostic results are separate and never treated as method performance.',
            'Equivalent/paraphrased queries share clusters; few clusters yield unstable descriptive intervals.']}

def run(run_dir,base_report,benchmark,output):
    run_dir=Path(run_dir).resolve();base_report=Path(base_report).resolve();benchmark=Path(benchmark).resolve();output=Path(output)
    if output.exists():raise FileExistsError('Fresh RQ3 report output required')
    manifest=json.loads((base_report/'manifest.json').read_text(encoding='utf8'))
    run_manifest=json.loads((run_dir/'manifest.json').read_text(encoding='utf8'))
    verify(benchmark,expected_manifest_sha256=manifest['benchmark_sha256'])
    checks={run_dir/'manifest.json':manifest['run_manifest_sha256'],run_dir/'observations.jsonl':manifest['observations_sha256'],
        base_report/'scores.jsonl':manifest['report_files']['scores.jsonl']}
    for path,digest in checks.items():
        if sha(path)!=digest:raise ValueError('Base report input hash mismatch: '+str(path))
    for name,digest in manifest.get('source_hashes',{}).items():
        path=(ROOT/name).resolve()
        if not path.is_relative_to(ROOT) or sha(path)!=digest:raise ValueError('Base scoring code identity changed: '+name)
        checks[path]=digest
    if not manifest.get('source_hashes'):raise ValueError('Base scoring source identity required')
    repeats=run_manifest.get('repeats')
    if not isinstance(repeats,list) or len(repeats)!=1:raise ValueError('K1 single-repeat contract required')
    rows=jsonl(run_dir/'observations.jsonl');scores=jsonl(base_report/'scores.jsonl')
    for row in rows:
        path=verify_raw(run_dir,row);checks[path]=row['raw_artifact_sha256']
        if row.get('benchmark_sha256')!=manifest['benchmark_sha256'] or row.get('execution_identity')!=run_manifest.get('execution_identity'):
            raise ValueError('Method frozen execution identity mismatch')
    contract_hash=sha(benchmark/'answer_contracts.jsonl')
    result=build_cohort(rows,scores,jsonl(benchmark/'answer_contracts.jsonl'),jsonl(benchmark/'queries.jsonl'),contract_hash,repeats[0])
    result['provenance']={'observations_sha256':manifest['observations_sha256'],'scores_sha256':manifest['report_files']['scores.jsonl'],
        'benchmark_sha256':manifest['benchmark_sha256'],'base_report_manifest_sha256':sha(base_report/'manifest.json'),
        'raw_receipts_verified':len(rows),'source_hashes':{p:sha(ROOT/p) for p in (
            'research/marine_geollm_scie/runners/report_rq3_methods.py','research/marine_geollm_scie/evaluation/rq3_contract.py',
            'research/marine_geollm_scie/evaluation/execution_reliability_v1.py')}}
    checks[base_report/'manifest.json']=result['provenance']['base_report_manifest_sha256']
    for path,digest in checks.items():
        if sha(path)!=digest:raise ValueError('Source changed while reporting: '+str(path))
    verify(benchmark,expected_manifest_sha256=manifest['benchmark_sha256'])
    output.mkdir(parents=True,exist_ok=False)
    (output/'rq3_methods.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    def value(v):return '미측정' if v is None else f'{v:.4f}'
    lines=['# Table 11. 방법별 실행 성공과 공간 정답','',
        '같은 GOLD 공간 적격 문항을 사용합니다. CGE는 실행 성공에 조건부인 공간 정답률이며, ESR−joint gap과 다릅니다.',
        'raw spatial은 실행 여부와 별도의 원본 답안 검사이며, joint는 실행과 공간 정답을 모두 요구합니다.','',
        '|Method|N|ESR|Raw Spatial|Joint Spatial|CGE|SSFR|ESR−Joint gap|EVQSR|',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for method,metrics in result['methods'].items():
        cells=[metrics[k]['value'] for k in ('ESR','raw_spatial_correctness','Spatial_Correct','CGE','SSFR')]
        cells += [metrics['execution_correctness_gap'],metrics['EVQSR']['value']]
        lines.append('|'+method+'|'+str(metrics['observations'])+'|'+'|'.join(map(value,cells))+'|')
    lines+=['','## B3 대비 paired 차이와 95% CI','','차이는 P0 또는 P1 − B3입니다. 정의되지 않는 bootstrap draw를 제거하여 CI를 만들어 내지 않습니다.','',
            '|비교|지표|차이|95% CI|집단 수|','|---|---|---:|---|---:|']
    for pair,data in result['paired_comparisons'].items():
        for metric,entry in data.get('metrics',{}).items():
            ci=entry['ci95'];text='미측정' if ci is None else '['+', '.join(map(value,ci))+']'
            lines.append('|'+pair+'|'+metric+'|'+value(entry['difference_B_minus_A'])+'|'+text+'|'+str(data['clusters'])+'|')
    lines+=['','별도 8개 SQL fault 진단은 이 표에 포함하지 않습니다. 독립 의미·근거 판정이 없어 EVQSR는 미측정입니다.',
            '지표별 measured/missing, 성공 분모, case/equivalence/원본 hash는 rq3_methods.json에 기록했습니다.','',*['- '+x for x in result['limitations']]]
    (output/'table11_KR.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--observations',required=True);p.add_argument('--scores',required=True)
    p.add_argument('--benchmark',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    if Path(a.observations).name!='observations.jsonl':p.error('Verified comparison/observations.jsonl required')
    run(Path(a.observations).parent,a.scores,a.benchmark,a.output)
