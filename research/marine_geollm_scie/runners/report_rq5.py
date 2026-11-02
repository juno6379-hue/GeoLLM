"""Post-run RQ5 accounting. No model, DB, GOLD, or holdout access."""
import argparse,hashlib,json
from pathlib import Path
from collections import defaultdict
from ..evaluation.rq5_costs import event_ledger,numeric
from ..evaluation.metrics import distribution
from ..evaluation.v2_observations import normalize

METHODS=('B0','B1','B2','B3','B4','P0','H','P1')
FIELDS=('latency_seconds','input_tokens','output_tokens','embedding_input_tokens','model_calls','tool_calls','spatial_tool_calls','sql_calls','retries','identity_check_retries')

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def key(row):return (row['method'],row['case_id'],row.get('repeat',row.get('repeat_id',0)))
def rate(values):
    return {'value':sum(v is True for v in values)/len(values) if values and all(type(v) is bool for v in values) else None,
            'denominator':len(values),'measured':sum(type(v) is bool for v in values),'missing':sum(type(v) is not bool for v in values)}

def evidence_presence(row):
    observed=normalize(row)
    if not observed.get('output_available') or observed.get('schema_errors'):
        return {'value':None,'returned_objects':None,'with_provenance':None,'scope':'OUTPUT_UNAVAILABLE_OR_MALFORMED'}
    answer=observed['answer'];checks=[]
    for task in answer.get('spatial_tasks',{}).values():
        ids=task.get('object_ids')
        if not isinstance(ids,list):continue
        evidence=task.get('object_evidence') or {}
        for identifier in ids:
            link=evidence.get(str(identifier)) or evidence.get(identifier) or {}
            checks.append(str(link.get('object_id'))==str(identifier) and
                          isinstance(link.get('source_snapshot_sha256'),str) and len(link['source_snapshot_sha256'])==64)
    return {'value':all(checks) if checks else None,'returned_objects':len(checks),'with_provenance':sum(checks),
            'scope':'RETURNED_OBJECT_SOURCE_HASH_AND_ID_PRESENCE_ONLY; not claim support or hash correctness',
            'full_answer_evidence_completeness':None,'end_to_end_provenance_correctness':None}

def summarize(rows,scored=(),judgments=(),expected_cases=18):
    seen=set();scored_index={key(r):r for r in scored};judged_index={key(r):r for r in judgments}
    if len(scored_index)!=len(scored) or len(judged_index)!=len(judgments):raise ValueError('Duplicate score/judgment')
    for row in rows:
        if key(row) in seen or row['method'] not in METHODS:raise ValueError('Duplicate/unknown method observation')
        seen.add(key(row))
    if set(scored_index)-seen or set(judged_index)-seen:raise ValueError('Score/judgment outside observation cohort')
    cases={r['case_id'] for r in rows};repeats={r.get('repeat',r.get('repeat_id',0)) for r in rows}
    if len(repeats)>1:raise ValueError('K1 RQ5 report expects exactly one repeat; repeated report requires frozen aggregation contract')
    ledger=event_ledger(rows);results={};details=[]
    for method in METHODS:
        batch=[r for r in rows if r['method']==method]
        complete=len(batch)==expected_cases and {r['case_id'] for r in batch}==cases and len(cases)==expected_cases
        reliability=[];false_ready=[];false_block=[];evidence=[];bindings=[];unknown_eligibility=0
        for row in batch:
            score=scored_index.get(key(row),{});judged=judged_index.get(key(row),{})
            if judged and (not row.get('raw_artifact_sha256') or judged.get('raw_artifact_sha256')!=row['raw_artifact_sha256']):
                raise ValueError('Judgment must bind this exact raw answer artifact')
            sem=judged.get('semantic_correct');ev=judged.get('evidence_correct')
            spatial=score.get('spatial_correctness');execution=score.get('execution_succeeded')
            applicable=score.get('execution_correctness_gap_applicable')
            components=[sem,ev,judged.get('plan_valid'),execution,spatial]
            evqsr=all(components) if applicable is True and all(type(v) is bool for v in components) else None
            if applicable is True:reliability.append(evqsr)
            elif applicable is not False:unknown_eligibility+=1
            executable=judged.get('executable_gold');ready=judged.get('execution_ready')
            if executable is False:false_ready.append(ready if type(ready) is bool else None)
            if executable is True:false_block.append(not ready if type(ready) is bool else None)
            presence=evidence_presence(row);evidence.append(presence['value'])
            evidence_checks={k:v for k,v in score.get('checks',{}).items() if 'evidence' in k or 'binding' in k or k.endswith('_source')}
            bindings.append(all(evidence_checks.values()) if evidence_checks and all(type(v) is bool for v in evidence_checks.values()) else None)
            details.append({'method':method,'case_id':row['case_id'],'repeat':key(row)[2],'EVQSR':evqsr,
                'evidence_provenance_presence':presence,'machine_evidence_binding_checks':evidence_checks,
                'independent_semantic_correctness':sem,'independent_evidence_correctness':ev})
        method_result={'observations':len(batch),'expected_observations':expected_cases,'cohort_complete':complete,
            'costs':{f:distribution([numeric((r.get('costs') or {}).get(f))
                if f!='sql_calls' or isinstance((r.get('costs') or {}).get('all_sql_events'),list) else None for r in batch]) for f in FIELDS},
            'human_escalation':rate([(r.get('costs') or {}).get('human_escalation') for r in batch]),
            'returned_object_provenance_presence':rate(evidence),'EVQSR':rate(reliability),
            'machine_evidence_binding_checks_pass':rate(bindings),
            'False_Ready':rate(false_ready),'False_Block':rate(false_block),
            'executable_gold_missing':sum(type(judged_index.get(key(r),{}).get('executable_gold')) is not bool for r in batch),
            'tool_call_scope':sorted({(r.get('costs') or {}).get('tool_call_scope','UNMEASURED') for r in batch}),
            'sql_call_scope':sorted({str((r.get('costs') or {}).get('sql_call_scope','UNMEASURED')) for r in batch})}
        method_result['EVQSR']['unknown_eligible_membership']=unknown_eligibility
        if unknown_eligibility:method_result['EVQSR']['value']=None
        if method_result['executable_gold_missing']:
            method_result['False_Ready']['value']=None;method_result['False_Block']['value']=None
        if not complete:
            method_result['status']='INCOMPLETE_COHORT; distributions describe observed subset, no whole-cohort rate claim'
            for name in ('human_escalation','returned_object_provenance_presence','machine_evidence_binding_checks_pass','EVQSR','False_Ready','False_Block'):method_result[name]['value']=None
        results[method]=method_result
    return {'version':'rq5_report.v1','status':'COMPLETE_OBSERVATION_COHORT' if all(v['cohort_complete'] for v in results.values()) else 'INCOMPLETE_COHORT',
            'methods':results,'event_ledger':ledger,'details':details,'model_calls_for_report':0,
            'limitations':['P1 logical graph operations differ from baseline bounded tools; expose scopes rather than claiming equivalent tool-call units.',
            'SQL calls count submissions including metadata, not every statement inside atomic guard/transaction.',
            'File evidence packet retrieval performs no SQL; measured generation pre-processing latency includes file retrieval.',
            'Returned-object provenance presence is not source correctness, full-answer evidence completeness, or semantic truth.',
            'EVQSR requires independent exact-answer semantic/evidence labels plus spatial eligibility; absent labels remain null.',
            'False Ready/False Block need independent executable labels and actual Ready decisions; spatial failure alone is insufficient.',
            'Shared model latency allocation represents work, not end-user response time; P50/P95 use standalone latency.']}

def run(observations,output,*,scores=None,judgments=None,expected_cases=18):
    source=Path(observations);before=sha(source);rows=[json.loads(x) for x in source.read_text(encoding='utf8').splitlines() if x.strip()]
    def bound(path):
        if not path:return []
        location=Path(path)
        if location.is_dir():
            payload=json.loads((location/'manifest.json').read_text(encoding='utf8'))
            if payload.get('observations_sha256')!=before or payload.get('report_files',{}).get('scores.jsonl')!=sha(location/'scores.jsonl'):
                raise ValueError('Score report provenance mismatch')
            return [json.loads(x) for x in (location/'scores.jsonl').read_text(encoding='utf8').splitlines() if x.strip()]
        payload=json.loads(location.read_text(encoding='utf8'))
        if payload.get('observations_sha256')!=before:raise ValueError('Scores/judgments not bound to these raw observations')
        return payload['rows']
    scored,labels=bound(scores),bound(judgments)
    from .report_eight import verify_raw
    for row in rows:verify_raw(source.parent.resolve(),row)
    report=summarize(rows,scored,labels,expected_cases)
    report['raw_artifacts_verified']=len(rows)
    report['observations_sha256']=before;report['source_path']=str(source.resolve())
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    (out/'rq5_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    def display(value):return '미측정' if value is None else str(round(value,4))
    lines=['# RQ5 신뢰도와 비용','',report['status'],'','|방법|관측|P95 latency(s)|모델 호출 평균|SQL 호출 평균|EVQSR|','|---|---:|---:|---:|---:|---:|']
    for method,data in report['methods'].items():
        c=data['costs'];lines.append(f"|{method}|{data['observations']}/{expected_cases}|{display(c['latency_seconds'].get('p95'))}|{display(c['model_calls'].get('mean'))}|{display(c['sql_calls'].get('mean'))}|{display(data['EVQSR']['value'])}|")
    lines+=['','각 비용의 measured/missing과 계측 범위는 JSON에 기록했습니다. 공유 호출의 독립 실행 비용을 합산하지 않습니다.','',*['- '+v for v in report['limitations']]]
    (out/'rq5_report_KR.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    if sha(source)!=before:raise ValueError('Observation source changed during report')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--observations',required=True);p.add_argument('--output',required=True)
    p.add_argument('--scores');p.add_argument('--judgments');p.add_argument('--expected-cases',type=int,default=18);a=p.parse_args()
    run(a.observations,a.output,scores=a.scores,judgments=a.judgments,expected_cases=a.expected_cases)
