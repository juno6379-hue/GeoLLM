"""RQ metrics: independent approval gates, explicit denominators and paired units."""
from collections import Counter, defaultdict
import math
import random
import statistics
from .metrics import distribution, object_sets, quantile
from .statistics import mcnemar_exact

COMPONENTS=('semantic_correct','plan_valid','execution_success','spatial_correct','evidence_correct')


def approved(record):
    user_assisted=record.get('review_kind')=='USER_APPROVED_AI_ASSISTED' and record.get('independent_expert_review') is False
    return (record.get('review_kind')!='AI_PRE_REVIEW' and record.get('annotation_status',record.get('review_status'))=='GOLD'
        and record.get('human_approval') is True and record.get('adjudication_status')=='APPROVED'
        and bool(record.get('annotator_ids')) and (user_assisted or not any(str(v).upper().startswith(('AI','GPT','LLM','CODEX')) for v in record.get('annotator_ids',[])))
        and bool(record.get('gold_sha256')))


def rate(values):
    valid=[v for v in values if isinstance(v,bool)]
    return {'value':sum(valid)/len(values) if values and len(valid)==len(values) else None,
            'denominator':len(values),'measured':len(valid),'missing':len(values)-len(valid)}


def approval_basis(records):
    eligible=[r for r in records if approved(r)]
    if not eligible:return 'UNAVAILABLE'
    if any(r.get('review_kind')=='USER_APPROVED_AI_ASSISTED' for r in eligible):return 'USER_APPROVED_AI_ASSISTED_NOT_INDEPENDENT_EXPERT'
    return 'INDEPENDENT_EXPERT_APPROVAL_DECLARED'


def _lookup(obj,key):
    for part in key.split('.'):
        if not isinstance(obj,dict) or part not in obj:return None,False
        obj=obj[part]
    return obj,True


def derive(row, gold=None):
    """Raw self-reported correctness is never a scientific label.

    Accepted approved expectations: semantics.labels, qec_fields (dotted keys),
    spatial.object_ids, evidence.required_refs, expected_behavior, expected_invalid.
    Independent recovery evaluation uses the original semantics/spatial reference.
    """
    result={k:None for k in (*COMPONENTS,'false_ready','false_block','silent_spatial_failure',
        'semantic_preservation','semantic_drift','full_success','safe_abstention_correct','spatial_f1','spatial_exact',
        'semantic_label_exact','semantic_label_f1','reference_completeness','qec_field_accuracy','qec_reference_exact')}
    result['execution_success']=row.get('execution_success') if isinstance(row.get('execution_success'),bool) else None
    result['gold_approved']=approved(gold or {})
    if not result['gold_approved']: return result
    predicted=row.get('predicted_semantics')
    expected=(gold.get('semantics') or {}).get('labels')
    observed=predicted.get('labels') if isinstance(predicted,dict) else None
    if isinstance(expected,list) and isinstance(observed,list):
        match=object_sets(expected,observed)
        result['semantic_label_exact']=match['exact_match'];result['semantic_label_f1']=match['f1']
        # An exact label set is only a component score unless the approved reference
        # explicitly declares it to encode the complete original semantic contract.
        if gold['semantics'].get('label_set_is_complete_semantic_contract') is True:
            result['semantic_correct']=match['exact_match']
    plan=row.get('predicted_qec',row.get('full_qec'))
    qec=gold.get('qec_fields')
    if isinstance(qec,dict) and qec and isinstance(plan,dict):
        matches=[_lookup(plan,k)==(v,True) for k,v in qec.items()]
        result['qec_reference_exact']=all(matches);result['qec_field_accuracy']=sum(matches)/len(matches)
        if gold.get('qec_reference_is_complete_execution_contract') is True:result['plan_valid']=all(matches)
    spatial=gold.get('spatial') or {}
    snapshot=row.get('snapshot_sha256',row.get('dataset_snapshot_sha256'))
    if isinstance(spatial.get('object_ids'),list) and isinstance(row.get('returned_object_ids'),list) and spatial.get('oracle_sha256') and snapshot and spatial.get('dataset_snapshot_sha256')==snapshot and row.get('source_binding_verified') is not False and row.get('oracle_sha256',spatial['oracle_sha256'])==spatial['oracle_sha256']:
        match=object_sets(spatial['object_ids'],row['returned_object_ids'])
        result.update(spatial_correct=match['exact_match'],spatial_exact=match['exact_match'],spatial_f1=match['f1'])
    references=gold.get('evidence') or {}
    actual=row.get('verified_evidence_refs')
    if isinstance(references.get('required_refs'),list) and isinstance(actual,list):
        # Caller must provide independently verified references, not generated citation strings.
        result['reference_completeness']=set(references['required_refs']).issubset(set(actual))
        verification=row.get('evidence_verification') or {}
        if verification.get('verification_artifact_sha256') and all(isinstance(verification.get(k),bool) for k in ('claim_support_verified','source_version_verified')):
            result['evidence_correct']=(result['reference_completeness'] and verification['claim_support_verified'] and verification['source_version_verified'])
    invalid=gold.get('expected_invalid'); predicted_invalid=row.get('predicted_invalid')
    if isinstance(invalid,bool) and isinstance(predicted_invalid,bool):
        result['false_ready']=invalid and not predicted_invalid
        result['false_block']=not invalid and predicted_invalid
    behavior=gold.get('expected_behavior')
    decision=row.get('validator_decision',row.get('decision'))
    if behavior in ('BLOCK','NEEDS_USER_INPUT','HITL') and isinstance(decision,str):
        result['safe_abstention_correct']=decision==behavior
    if result['execution_success'] is True and isinstance(result['spatial_correct'],bool):
        result['silent_spatial_failure']=not result['spatial_correct']
    if row.get('recovery_attempted') is True and isinstance(result['semantic_correct'],bool):
        result['semantic_preservation']=result['semantic_correct']
        result['semantic_drift']=not result['semantic_correct']
    if all(isinstance(result[k],bool) for k in COMPONENTS):
        result['full_success']=all(result[k] for k in COMPONENTS)
    return result


def spatial_gap(rows, gold_by_case):
    cohort=[r for r in rows if approved(gold_by_case.get(r['case_id'],{}))
            and gold_by_case[r['case_id']].get('expected_behavior')=='EXECUTE']
    scored=[derive(r,gold_by_case[r['case_id']]) for r in cohort]
    executed=[r for r in scored if r['execution_success'] is True]
    esr=rate([r['execution_success'] for r in scored])
    # End-to-end correctness: a known failed execution is false, not missing spatial evaluation.
    joint=[False if r['execution_success'] is False else r['spatial_correct'] if r['execution_success'] is True else None for r in scored]
    scr=rate(joint); cge=rate([r['spatial_correct'] for r in executed])
    ssfr=rate([r['silent_spatial_failure'] for r in executed])
    return {'executable_rows':len(cohort),'successful_execution_rows':len(executed),
        'distinct_cases':len({r['case_id'] for r in cohort}),'equivalence_groups':len({r.get('equivalence_group',r['case_id']) for r in cohort}),
        'approval_basis':approval_basis([gold_by_case[r['case_id']] for r in cohort]),
        'ESR':esr['value'],'SCR':scr['value'],'CGE':cge['value'] if esr['missing']==0 else None,
        'SSFR':ssfr['value'] if esr['missing']==0 else None,
        'execution_correctness_gap':esr['value']-scr['value'] if esr['value'] is not None and scr['value'] is not None else None,
        'missing_execution':esr['missing'],'missing_spatial':scr['missing'],
        'status':'PILOT_ONLY' if cohort and scr['value'] is not None else 'NOT_READY'}


def semantic_set_scores(rows,gold_by_case):
    """Micro/macro F1 of explicitly approved required labels; not full task meaning."""
    pairs=[];missing=0
    for row in rows:
        gold=gold_by_case.get(row['case_id'],{})
        expected=(gold.get('semantics') or {}).get('labels')
        if not approved(gold) or not isinstance(expected,list):continue
        predicted=(row.get('predicted_semantics') or {}).get('labels')
        if not isinstance(predicted,list):missing+=1;continue
        pairs.append((set(expected),set(predicted)))
    result={'eligible':len(pairs)+missing,'measured':len(pairs),'missing':missing,
            'micro_f1':None,'macro_f1':None,'scope':'EXPLICIT_REQUIRED_LABEL_SET_ONLY_NOT_FULL_SEMANTICS'}
    if not pairs or missing:return result
    labels=set().union(*(a|b for a,b in pairs));counts=[]
    for label in labels:
        counts.append((sum(label in a and label in b for a,b in pairs),sum(label not in a and label in b for a,b in pairs),sum(label in a and label not in b for a,b in pairs)))
    tp,fp,fn=(sum(c[i] for c in counts) for i in range(3))
    result['micro_f1']=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None
    result['macro_f1']=statistics.mean(2*t/(2*t+f+n) for t,f,n in counts) if counts else None
    return result


def fault_detection(rows, gold_by_case, *, diagnostic=False):
    cohort=[]
    for r in rows:
        g=gold_by_case.get(r['case_id'],{})
        if not diagnostic and not approved(g):continue
        truth=r.get('expected_invalid') if diagnostic else g.get('expected_invalid')
        if isinstance(truth,bool):cohort.append((truth,r.get('predicted_invalid'),g.get('severity')))
    c=Counter();missing=0
    for truth,prediction,_ in cohort:
        if not isinstance(prediction,bool):missing+=1;continue
        c['TP' if truth and prediction else 'FN' if truth else 'FP' if prediction else 'TN']+=1
    def quotient(a,b):return a/b if b and not missing else None
    critical=[(t,p) for t,p,s in cohort if t and s=='CRITICAL']
    return {'eligible':len(cohort),'missing_predictions':missing,**{k:c[k] for k in ('TP','FP','FN','TN')},
        'approval_basis':'DRAFT_DIAGNOSTIC' if diagnostic else approval_basis([gold_by_case.get(r['case_id'],{}) for r in rows]),
        'precision':quotient(c['TP'],c['TP']+c['FP']),'recall':quotient(c['TP'],c['TP']+c['FN']),
        'f1':quotient(2*c['TP'],2*c['TP']+c['FP']+c['FN']),
        'false_ready':quotient(c['FN'],c['TP']+c['FN']),'false_block':quotient(c['FP'],c['FP']+c['TN']),
        'critical_false_ready':rate([not p if isinstance(p,bool) else None for _,p in critical])['value'],
        'label_kind':'DRAFT_FAULT_DIAGNOSTIC' if diagnostic else 'APPROVED_GOLD_ONLY'}


def recovery(rows,gold_by_case):
    cohort=[r for r in rows if approved(gold_by_case.get(r['case_id'],{})) and gold_by_case[r['case_id']].get('recovery_eligible') is True]
    attempted=[r for r in cohort if r.get('recovery_attempted') is True]
    scored=[derive(r,gold_by_case[r['case_id']]) for r in attempted]
    recovered=[s for r,s in zip(attempted,scored) if r.get('recovery_success') is True]
    missing_recovery=sum(not isinstance(r.get('recovery_success'),bool) for r in attempted)
    result={'eligible':len(cohort),'attempted_measured':len(attempted),
        'approval_basis':approval_basis([gold_by_case[r['case_id']] for r in cohort]),
        'detection_rate':rate([r.get('error_detected') for r in cohort])['value'],
        'attempt_rate':rate([r.get('recovery_attempted') for r in cohort])['value'],
        'execution_recovery_rate':rate([r.get('recovery_success') for r in attempted])['value'],
        'SPR':rate([r['semantic_preservation'] for r in scored])['value'],
        'SDR':rate([r['semantic_drift'] for r in scored])['value'],
        'recovered_rows':len(recovered),'missing_recovery_success':missing_recovery,
        'RSC':rate([r['spatial_correct'] for r in recovered])['value'] if missing_recovery==0 else None,
        'spatial_correct_all_attempts':rate([r['spatial_correct'] for r in scored])['value'],
        'denominator_note':'SPR/SDR use all attempted recoveries; RSC uses recovery_success=true rows; joint success uses all attempts.',
        'escalation_rate':rate([r.get('escalated') for r in cohort])['value'],
        'first_repair_success':rate([r.get('recovery_success') and r['repair_iterations']==1 if isinstance(r.get('recovery_success'),bool) and isinstance(r.get('repair_iterations'),int) else None for r in attempted])['value'],
        'repair_iterations_mean':distribution([r.get('repair_iterations') for r in attempted])['mean']}
    joint=[all(r.get(k) is True for k in ('error_detected','recovery_success')) and s['spatial_correct'] and s['semantic_preservation']
           if all(isinstance(r.get(k),bool) for k in ('error_detected','recovery_success')) and isinstance(s['spatial_correct'],bool) and isinstance(s['semantic_preservation'],bool) else None for r,s in zip(attempted,scored)]
    result['meaning_preserved_spatial_recovery_rate']=rate(joint)['value']
    return result


def costs(rows):
    out={'rows':len(rows),'distinct_cases':len({r.get('case_id') for r in rows})}
    for field,alias in [('total_latency_ms','latency_ms'),('input_tokens',None),('output_tokens',None),
        ('tool_calls','tool_calls_executed'),('DB_queries',None),('retries',None),('repair_iterations',None),('model_calls',None)]:
        measured=[]
        for r in rows:
            v=r.get(field,r.get(alias) if alias else None)
            measured.append(v if isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) and v>=0 else None)
        out.update({field+'_'+k:v for k,v in distribution(measured).items()})
    totals=[r['input_tokens']+r['output_tokens'] if all(isinstance(r.get(k),(int,float)) and not isinstance(r[k],bool) and math.isfinite(r[k]) and r[k]>=0 for k in ('input_tokens','output_tokens')) else None for r in rows]
    out.update({'total_tokens_'+k:v for k,v in distribution(totals).items()})
    out['timeout_rows']=sum('TIMEOUT' in str(r.get('status','')).upper() or 'TIMED_OUT' in str(r.get('status','')).upper() for r in rows)
    out['error_rows']=sum(str(r.get('status','')).upper() in ('ERROR','FAILED') for r in rows)
    out['timeout_rate']=out['timeout_rows']/len(rows) if rows else None
    out['cold_start_measured']=sum(r.get('latency_phase')=='cold_start' for r in rows)
    out['steady_state_measured']=sum(r.get('latency_phase')=='steady_state' for r in rows)
    out['stage_timing_rows']=sum(isinstance(r.get('latency_by_stage'),dict) for r in rows)
    return out


def _paired(a,b,field):
    def index(rows):
        out={}
        for r in rows:
            key=(r['case_id'],r.get('repeat_id',r.get('repeat',0)))
            if key in out:raise ValueError('Duplicate case/repeat in a paired cohort')
            v=r.get(field)
            if not isinstance(v,(bool,int,float)) or not math.isfinite(v):raise ValueError('Missing/nonfinite paired outcome')
            out[key]=(float(v),r.get('equivalence_group',r['case_id']))
        return out
    x,y=index(a),index(b)
    if not x or x.keys()!=y.keys():raise ValueError('Identical nonempty case/repeat cohorts required')
    if any(x[k][1]!=y[k][1] for k in x):raise ValueError('Group assignments differ')
    return x,y


def cluster_bootstrap(a,b,field,*,samples=2000,seed=20261030):
    """B-A; repeats averaged within case, resampling equivalence groups as clusters."""
    x,y=_paired(a,b,field)
    if samples<100:raise ValueError('At least 100 bootstrap samples required')
    case=defaultdict(list); groups={}
    for key in x:
        case[key[0]].append(y[key][0]-x[key][0]);groups[key[0]]=x[key][1]
    clusters=defaultdict(list)
    for cid,values in case.items():clusters[groups[cid]].append(statistics.mean(values))
    if len(clusters)<2:return {'status':'NOT_READY','reason':'Fewer than two independent groups','clusters':len(clusters),'ci95':None}
    rng=random.Random(seed); blocks=list(clusters.values())
    bootstrap=[]
    for _ in range(samples):
        selected=[v for _ in blocks for v in rng.choice(blocks)]
        bootstrap.append(statistics.mean(selected))
    return {'status':'DESCRIPTIVE_PILOT','difference_B_minus_A':statistics.mean([statistics.mean(v) for v in case.values()]),
        'ci95':[quantile(bootstrap,.025),quantile(bootstrap,.975)],'clusters':len(clusters),'cases':len(case),
        'paired_rows':len(x),'seed':seed,'bootstrap_samples':samples,
        'limitation':'Few clusters; unstable CI, not confirmatory evidence' if len(clusters)<10 else None}


def paired_mcnemar(a,b,field,*,repeat_id):
    """One explicitly selected repeat per case; selection timing must be disclosed."""
    aa=[r for r in a if r.get('repeat_id',r.get('repeat',0))==repeat_id]
    bb=[r for r in b if r.get('repeat_id',r.get('repeat',0))==repeat_id]
    x,y=_paired(aa,bb,field)
    if len({v[1] for v in x.values()})!=len(x):
        return {'status':'NOT_READY','reason':'Equivalent cases are dependent; use cluster bootstrap'}
    if not all(isinstance(r.get(field),bool) for r in aa+bb):raise ValueError('McNemar requires binary outcomes')
    return {**mcnemar_exact({k[0]:bool(v[0]) for k,v in x.items()},{k[0]:bool(v[0]) for k,v in y.items()}),
            'selected_repeat':repeat_id,'selection_timing':'CALLER_MUST_DISCLOSE','status':'DESCRIPTIVE_PILOT'}
