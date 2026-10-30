"""Reanalyse observed runs into RQ artifacts; never launch models or promote GOLD."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from ..evaluation.rq_metrics import (approved, derive, rate, spatial_gap, fault_detection,
    recovery, costs, cluster_bootstrap, paired_mcnemar, COMPONENTS, approval_basis, semantic_set_scores)
from ..evaluation.metrics import object_sets, quantile, mean_complete
from ..reporting.build_tables import write_table

ROOT=Path(__file__).resolve().parents[3]
RESEARCH=ROOT/'research/marine_geollm_scie'
CONDITIONS=ROOT/'outputs/scie_rq_v2_audit_20261030/condition_metadata.jsonl'
GOLD_AUDIT=ROOT/'outputs/scie_rq_v2_audit_20261030/gold_audit.json'
DEFAULT_SOURCES=[
 ('PLAN_ONLY','runs/20261030_comparison_v2b/comparison_rows.jsonl'),
 ('SEMANTIC_COMPONENT','runs/20261029_pilot/semantic_isolated/semantic_rows.jsonl'),
 ('FAULT_FIXTURE','runs/20261029_pilot/validator/validator_rows.jsonl'),
 ('SPATIAL_COMPONENT','runs/20261029_pilot/spatial/spatial_rows.jsonl')]
AXES={'terminology_condition':'용어','complexity':'복잡도','spatial_operator':'공간연산',
      'information_availability':'정보가용성','ambiguity':'모호성'}
METHODS=('B0','B1','B2','B3','B4','P0','P1','H')
SECTIONS=('무엇을 비교했는가','실제 결과','가장 큰 차이','예상과 다른 결과','오류 사례','통계검정','논문에 쓸 수 있는 결론','아직 주장하면 안 되는 것')


def read(path):
    path=Path(path)
    return [json.loads(s) for s in path.read_text(encoding='utf-8-sig').splitlines() if s.strip()]
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def jsonwrite(path,value):Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def serial(value):return json.dumps(value,ensure_ascii=False,allow_nan=False)


def _group(rows):
    out=defaultdict(list)
    for r in rows:out[(r['cohort'],r['method'])].append(r)
    return out


def tables_for(rows, conditions, gold):
    groups=_group(rows); rq1=[]; rq2=[]; rq3=[]; rq4=[]; rq5=[]; diagnostics=[]
    for (cohort,method),items in sorted(groups.items()):
        for axis in AXES:
            strata=defaultdict(list)
            for r in items:
                label=conditions.get(r['case_id'],{}).get(axis)
                labels=label if isinstance(label,list) else [label] if label else []
                for value in labels or ['UNMEASURED']:strata[value].append(r)
            for condition,subset in sorted(strata.items()):
                scientific=[derive(r,gold.get(r['case_id'])) for r in subset if approved(gold.get(r['case_id'],{}))]
                qec_scored=[derive(r,gold[r['case_id']]) for r in subset if approved(gold.get(r['case_id'],{})) and gold[r['case_id']].get('qec_fields')]
                abstention=[derive(r,gold[r['case_id']]) for r in subset if approved(gold.get(r['case_id'],{})) and gold[r['case_id']].get('expected_behavior') in ('BLOCK','NEEDS_USER_INPUT','HITL')]
                labels=semantic_set_scores(subset,gold)
                rq1.append({'cohort':cohort,'axis':axis,'condition':condition,'method':method,'rows':len(subset),
                    'cases':len({r['case_id'] for r in subset}),'approved_gold_rows':len(scientific),
                    'semantic_exact':rate([s['semantic_correct'] for s in scientific])['value'],
                    'semantic_f1':labels['micro_f1'],'semantic_macro_f1':labels['macro_f1'],
                    'semantic_label_reference_rows':labels['eligible'],'semantic_label_missing':labels['missing'],
                    'semantic_label_exact_component':rate([s['semantic_label_exact'] for s in scientific])['value'],
                    'qec_accuracy':mean_complete([s['qec_field_accuracy'] for s in qec_scored]),
                    'qec_declared_reference_rows':len(qec_scored),'qec_measured_rows':sum(s['qec_field_accuracy'] is not None for s in qec_scored),
                    'qec_exact':rate([s['qec_reference_exact'] for s in qec_scored])['value'],
                    'safe_abstention_accuracy':rate([s['safe_abstention_correct'] for s in abstention])['value'],
                    'safe_abstention_reference_rows':len(abstention),
                    'execution_success':spatial_gap(subset,gold)['ESR'],'spatial_correct':spatial_gap(subset,gold)['SCR'],
                    'delta_vs_baseline':None,'ci95':None,'status':'NOT_READY',
                    'approval_basis':approval_basis([gold.get(r['case_id'],{}) for r in subset]),
                    'condition_timing':'POST_HOC_DESCRIPTIVE_ONLY',
                    'scoring_scope':'semantic F1 is approved required-label component only; qec_accuracy is declared-field literal match, not whole-QEC or semantic correctness; aliases are not resolved'})
        if cohort=='FAULT_FIXTURE':
            error_groups=defaultdict(list)
            for r in items:error_groups[r.get('failure_code') or 'VALID_CONTROL'].append(r)
            for error,subset in error_groups.items():
                rq2.append({'cohort':cohort,'method':method,'error_type':error,**fault_detection(subset,gold),
                    'status':'NOT_READY','taxonomy_status':'LEGACY_CODES_NOT_RELABELED_AS_V2_GOLD'})
                diagnostics.append({'cohort':cohort,'method':method,'error_type':error,**fault_detection(subset,gold,diagnostic=True)})
        rq3.append({'cohort':cohort,'method':method,**spatial_gap(items,gold),
            'operational_execution_measured':rate([r.get('execution_success') for r in items])['measured'],
            'operational_execution_true':sum(r.get('execution_success') is True for r in items),
            'operational_scope_note':'명시적 실행 관측과 사용자 승인 공간 참조 대조를 구분; 독립 전문가 정답 또는 full pipeline 성능으로 간주하지 않음'})
        rq4.append({'cohort':cohort,'method':method,'error_type':'ALL',**recovery(items,gold),'status':'NOT_READY'})
        scientific=[derive(r,gold.get(r['case_id'])) for r in items if approved(gold.get(r['case_id'],{}))]
        rq5.append({'cohort':cohort,'method':method,**costs(items),
            'approval_basis':approval_basis([gold.get(r['case_id'],{}) for r in items]),
            'EVQSR':rate([s['full_success'] for s in scientific])['value'],
            **{k:rate([s[k] for s in scientific])['value'] for k in COMPONENTS},
            'SpatialCorrect':spatial_gap(items,gold)['SCR'],
            'FalseReady':fault_detection(items,gold)['false_ready'],'FalseBlock':fault_detection(items,gold)['false_block'],
            'HumanEscalation':None,'status':'OBSERVATIONAL_COST_ONLY'})
    # Required unmeasured profiles remain explicit, never substitute unrelated components.
    observed={r['method'] for r in rq3}
    for method in METHODS:
        if method not in observed:
            rq3.append({'cohort':'REQUIRED_PROFILE_NOT_MEASURED','method':method,**spatial_gap([],gold)})
    for method in ('B4','P0','H'):
        if not any(r['method']==method for r in rq2):
            rq2.append({'cohort':'MATCHED_GOLD_FAULT_SET_NOT_MEASURED','method':method,'error_type':'ALL',**fault_detection([],gold),'status':'NOT_READY'})
    ablation=[{'profile':p,'semantic_error_rate':None,'schema_error_rate':None,'spatial_error_rate':None,
        'runtime_error_rate':None,'evidence_error_rate':None,'EVQSR':None,'status':'NOT_MEASURED'} for p in
        ('w/o Ontology','w/o QEC','w/o Validator','w/o Post Validation','w/o Recovery','w/o Evidence')]
    return {'RQ1_condition_effectiveness':rq1,'RQ2_error_detection':rq2,'RQ3_execution_spatial_gap':rq3,
            'RQ4_recovery_semantic_preservation':rq4,'RQ5_reliability_cost':rq5,'ablation_failure_analysis':ablation,
            'DRAFT_fault_diagnostics':diagnostics}


def report_sections(path,comparison,actual,*,difference='확정된 내부 대조 범위 밖의 기술 효과 차이는 아직 산출할 수 없다.',cases='오류 행과 timeout을 삭제하지 않고 source record에 보존했다.',stats='독립 정답과 표본을 이용한 확증적 검정은 NOT_READY이다.'):
    contents=[comparison,actual,difference,'예상 방향을 고정하지 않았다. 정답 미확정 때문에 예상 대비 성능을 판정하지 않는다.',
        cases,stats,'현재 관측한 실행범위·비용·결측과 확보된 사용자 승인 참조 범위의 내부 대조를 기술할 수 있다. component 결과를 합쳐 full pipeline 결과로 쓰지 않는다.',
        'P1 우월성, 한글 의도분류 전체 정확도, silent failure 감소, recovery 의미보존 및 holdout 일반화는 주장할 수 없다.']
    path.write_text('# '+path.stem+'\n\n**진행 상태: NOT_READY — 논문 Results 완료 아님**\n\n'+
        '\n\n'.join(f'## {i}. {title}\n\n{body}' for i,(title,body) in enumerate(zip(SECTIONS,contents),1))+'\n',encoding='utf-8')


def gap_markdown(records):
    lines=['| 실행군 | 실행 / 대상 | 공간일치 / 대상 | ESR | SCR | CGE | SSFR | 동등질의군 |',
           '| --- | --- | --- | --- | --- | --- | --- | --- |']
    def percent(v):return '미측정' if v is None else f'{v:.1%}'
    for r in records:
        n=r['executable_rows'];correct='미측정' if r['SCR'] is None else str(round(r['SCR']*n))
        lines.append(f'| {r["cohort"]} | {r["successful_execution_rows"]}/{n} | {correct}/{n} | '+
            ' | '.join(percent(r[k]) for k in ('ESR','SCR','CGE','SSFR'))+f' | {r["equivalence_groups"]} |')
    return '\n'.join(lines)+'\n\n사용자 승인 고정 원천에 대한 내부 대조이며 독립 전문가 GOLD나 holdout 결과가 아니다.'


def diagnostic_statistics(rows):
    plan=[r for r in rows if r['cohort']=='PLAN_ONLY']
    out=[]
    for first,second in [('B1','B2'),('B2','B3'),('B3','B4')]:
        a=[r for r in plan if r['method']==first];b=[r for r in plan if r['method']==second]
        for metric in ('latency_ms','schema_valid'):
            try:result=cluster_bootstrap(a,b,metric,samples=2000)
            except ValueError as exc:result={'status':'NOT_READY','reason':str(exc)}
            out.append({'comparison':first+' vs '+second,'metric':metric,'scope':'PLANNING_OBSERVABLE_NOT_ACCURACY','test':'group_cluster_bootstrap',**result})
        try:result=paired_mcnemar(a,b,'schema_valid',repeat_id=0)
        except ValueError as exc:result={'status':'NOT_READY','reason':str(exc)}
        out.append({'comparison':first+' vs '+second,'metric':'schema_valid','scope':'PLANNING_OBSERVABLE_NOT_ACCURACY','test':'McNemar_repeat_0',**result,'selection_timing':'POST_HOC_REANALYSIS'})
    return out


def make_figures(folder,tables):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    names=['RQ1_conditions','RQ2_error_matrix','RQ3_execution_spatial_gap','RQ4_recovery','RQ5_reliability_cost','ablation_failure_types']
    figure_status={'scientific_figures':[{'name':name,'status':'NOT_READY_PLACEHOLDER_ONLY','reason':'complete evaluation contracts and controlled full-profile runs missing; available user-approved Q4 measurements are shown separately'} for name in names],
        'observational_figures':[{'name':'D1_observed_cost.png','status':'ACTUAL_MEASURED_COST_ONLY'}]}
    for name in names:
        fig,ax=plt.subplots(figsize=(8,4));ax.axis('off')
        ax.text(.5,.60,name,ha='center',fontsize=14)
        ax.text(.5,.38,'NOT_READY\nComplete metric contracts and controlled profiles pending',ha='center',fontsize=12)
        ax.text(.5,.13,'Missing values are not zero. No scientific performance claim.',ha='center',fontsize=10)
        fig.tight_layout();fig.savefig(folder/(name+'.png'),dpi=110);plt.close(fig)
    # Actual measured costs get a separate observational figure; no reliability axis invented.
    cost=tables['RQ5_reliability_cost'];fig,ax=plt.subplots(figsize=(10,5))
    for i,r in enumerate(cost):
        if r.get('total_latency_ms_p50') is not None:ax.scatter(r['total_latency_ms_p50'],i)
    ax.set_yticks(range(len(cost)),[r['cohort']+' / '+r['method'] for r in cost],fontsize=7)
    ax.set_xlabel('Observed P50 latency (ms); incomparable scopes, no speed ranking')
    ax.set_title('D1 Actual cost observations - PILOT')
    fig.tight_layout();fig.savefig(folder/'D1_observed_cost.png',dpi=130);plt.close(fig)
    available=[r for r in tables['RQ3_execution_spatial_gap'] if r.get('ESR') is not None and r.get('SCR') is not None]
    if available:
        write_table(folder/'D2_internal_spatial',available)
        fig,ax=plt.subplots(figsize=(10,5))
        at=list(range(len(available)))
        ax.bar([x-.18 for x in at],[r['ESR'] for r in available],width=.35,label='Execution success')
        ax.bar([x+.18 for x in at],[r['SCR'] for r in available],width=.35,label='End-to-end object-set correctness')
        ax.set_xticks(at,[r['cohort'] for r in available],fontsize=8,rotation=10)
        ax.set_ylim(0,1.12);ax.set_ylabel('Observed fraction')
        for i,r in enumerate(available):ax.text(i,1.03,f'n={r["executable_rows"]}; groups={r["equivalence_groups"]}',ha='center',fontsize=9)
        ax.legend(fontsize=8);ax.set_title('D2 User-approved internal reference comparison\nNot independent expert GOLD or holdout; no statistical generalization')
        fig.tight_layout();fig.savefig(folder/'D2_internal_spatial.png',dpi=130);plt.close(fig)
        figure_status['observational_figures'].append({'name':'D2_internal_spatial.png','status':'USER_APPROVED_INTERNAL_COMPARISON_NOT_HOLDOUT'})
    jsonwrite(folder/'status_manifest.json',figure_status)


def load_references(path):
    if path is None:return {}
    path=Path(path).resolve();file_hash=digest(path)
    references={}
    for record in read(path):
        if record['case_id'] in references:raise ValueError('Duplicate approved reference case ID')
        references[record['case_id']]={**record,'gold_sha256':file_hash}
    return references


def run(run_id, condition_path=None, gold_audit_path=None, extra_sources=(), reference_path=None):
    output=RESEARCH/'results'/run_id
    if output.exists():raise FileExistsError('Use a new run ID; preserve previous analyses')
    for folder in ('tables','reports','figures','metrics'): (output/folder).mkdir(parents=True,exist_ok=True)
    condition_path=Path(condition_path or CONDITIONS);gold_audit_path=Path(gold_audit_path or GOLD_AUDIT)
    conditions={r['case_id']:r for r in read(condition_path)} if condition_path.is_file() else {}
    audit=json.loads(gold_audit_path.read_text(encoding='utf-8-sig')) if gold_audit_path.is_file() else {'status':'AUDIT_NOT_AVAILABLE'}
    gold=load_references(reference_path)
    approved_count=sum(approved(g) for g in gold.values())
    user_count=sum(approved(g) and g.get('review_kind')=='USER_APPROVED_AI_ASSISTED' for g in gold.values())
    expert_count=approved_count-user_count
    approval_label=f'사용자 승인 AI보조 참조 {user_count}건 / 독립 전문가 승인 참조 {expert_count}건'
    sources=[{'cohort':scope,'path':str(RESEARCH/path)} for scope,path in DEFAULT_SOURCES]
    for item in extra_sources:
        sources.append(item if isinstance(item,dict) else {'cohort':'EXTRA_SCOPE_UNCONFIRMED','path':str(item)})
    rows=[]; provenance=[]
    benchmark=read(RESEARCH/'benchmark/query_cases_v1.jsonl');byid={r['case_id']:r for r in benchmark}
    for source in sources:
        path=Path(source['path']).resolve()
        if not path.is_file():
            provenance.append({**source,'status':'MISSING'});continue
        source_rows=read(path)
        parents=[]
        for candidate in (path.parent/'manifest.json',path.parent/'adapter_manifest.json',path.parent/'summary.json',path.parent/'snapshot_manifest.json'):
            if candidate.is_file():parents.append({'path':str(candidate.relative_to(ROOT)),'sha256':digest(candidate),'recorded':json.loads(candidate.read_text(encoding='utf-8-sig'))})
        provenance.append({**source,'sha256':digest(path),'rows':len(source_rows),'recorded_metadata':parents})
        for index,raw in enumerate(source_rows,1):
            row={**raw,'cohort':source['cohort'],'source_file':str(path.relative_to(ROOT)),'source_record':index}
            case=byid.get(row['case_id'],{})
            row['equivalence_group']=case.get('equivalence_group',row['case_id'])
            row['split']=case.get('split',row.get('split','UNRECORDED'))
            # Graph return is NOT evidence of successful execution. Preserve only explicit flag.
            rows.append(row)
    tables=tables_for(rows,conditions,gold)
    composition=[{'case_id':r['case_id'],'category':r['category'],'split':r['split'],'language':r.get('language'),
        'equivalence_group':r['equivalence_group'],'cases':1,'gold_complete':False,
        'reference_approved':approved(gold.get(r['case_id'],{})),
        'reference_kind':gold.get(r['case_id'],{}).get('review_kind'),
        'human_approval':gold.get(r['case_id'],{}).get('human_approval'),
        'independent_expert_review':gold.get(r['case_id'],{}).get('independent_expert_review'),
        'partial_qec_reference_fields':len(gold.get(r['case_id'],{}).get('qec_fields') or {}),
        'spatial_reference_available':isinstance((gold.get(r['case_id'],{}).get('spatial') or {}).get('object_ids'),list),
        'condition_labels':serial({k:conditions.get(r['case_id'],{}).get(k) for k in AXES}),
        'conditions_available':r['case_id'] in conditions} for r in benchmark]
    tables['benchmark_gold_composition']=composition
    for name,data in tables.items():write_table(output/'tables'/name,data)
    stats=diagnostic_statistics(rows);jsonwrite(output/'metrics'/'paired_diagnostic_statistics.json',stats)
    derived=[{'cohort':r['cohort'],'method':r['method'],'case_id':r['case_id'],'repeat_id':r.get('repeat_id',r.get('repeat')),
              'source_file':r['source_file'],'source_record':r['source_record'],**derive(r,gold.get(r['case_id']))} for r in rows]
    (output/'metrics'/'derived_rows.jsonl').write_text(''.join(serial(r)+'\n' for r in derived),encoding='utf-8')
    counts=dict(Counter(r['cohort'] for r in rows))
    plans=[r for r in rows if r['cohort']=='PLAN_ONLY'];planstatus=dict(Counter(r.get('status') for r in plans))
    error_examples=[{'cohort':r['cohort'],'method':r['method'],'case_id':r['case_id'],'source_record':r['source_record'],'source_file':r['source_file'],
        'status':r.get('status'),'graph_status':r.get('graph_status'),'execution_success':r.get('execution_success'),
        'expected_behavior':gold.get(r['case_id'],{}).get('expected_behavior'),
        'classification':'EXPECTED_EXECUTION_DID_NOT_RUN' if r.get('execution_success') is False and gold.get(r['case_id'],{}).get('expected_behavior')=='EXECUTE'
            else 'NON_EXECUTION_OR_ERROR_REQUIRES_CONTEXT'}
        for r in rows if str(r.get('status','')).upper() in ('ERROR','FAILED','TIMEOUT') or r.get('execution_success') is False]
    jsonwrite(output/'metrics'/'error_examples.json',error_examples)
    summary={'scientific_completion':False,'status':'NOT_READY','source_cohorts':counts,'planning_statuses':planstatus,
        'approved_reference_cases':approved_count,'user_approved_ai_assisted_cases':user_count,'independent_expert_gold_cases':expert_count,
        'approved_reference_components':{'semantic_labels':sum(approved(g) and isinstance((g.get('semantics') or {}).get('labels'),list) for g in gold.values()),
            'qec_partial_fields':sum(approved(g) and bool(g.get('qec_fields')) for g in gold.values()),
            'spatial_objects':sum(approved(g) and isinstance((g.get('spatial') or {}).get('object_ids'),list) for g in gold.values()),
            'evidence_reference_sets':sum(approved(g) and isinstance((g.get('evidence') or {}).get('required_refs'),list) for g in gold.values())},
        'holdout_cases':sum(r.get('split')=='holdout' for r in benchmark),'required_stochastic_repeats':5,
        'observed_planning_repeats':sorted({r.get('repeat') for r in plans}),'required_profiles_not_measured':['P0','P1','H'],
        'source_row_count':len(rows),'costs':tables['RQ5_reliability_cost'],
        'rq_answers':{'RQ1':'전체 의미 효과 차이 미측정. 제공된 확정 QEC 필드는 내부 승인 참조와 부분 비교할 수 있으나 전체 실행계약 정확도가 아니다.',
        'RQ2':'승인 fault GOLD 및 H 동일오류셋 실험 없음. DRAFT 진단은 별도 표.',
        'RQ3':'실제 반환 ID와 일치하는 승인 snapshot/oracle이 있는 범위만 평가한다. 계획 출력에는 공간 정답률을 부여하지 않는다.',
        'RQ4':'독립 recovery/GOLD 측정 없음: SPR/SDR/RSC 모두 null.',
        'RQ5':'실측 비용만 산출. 신뢰성 향상의 추가 비용은 미측정.'}}
    available_gaps=[r for r in tables['RQ3_execution_spatial_gap'] if any(r.get(k) is not None for k in ('ESR','SCR','CGE','SSFR'))]
    summary['rq_answers']['RQ3']+='\n\n'+(gap_markdown(available_gaps) if available_gaps else '현재 평가 가능한 ESR/SCR/CGE/SSFR 수치 0개; 값은 null.')
    summary['partially_scored_qec_rows']=sum(derive(r,gold.get(r['case_id']))['qec_field_accuracy'] is not None for r in rows)
    summary['rq_answers']['RQ1']+=f' 부분 QEC 필드 측정 행수={summary["partially_scored_qec_rows"]}.'
    jsonwrite(output/'metrics'/'summary.json',summary)
    for name in ('RQ1_condition_effectiveness','RQ2_error_detection','RQ3_execution_spatial_gap','RQ4_recovery_semantic_preservation','RQ5_reliability_cost','ablation_failure_analysis'):
        observed=serial(tables[name]) if name=='RQ5_reliability_cost' else f'표 {name}.csv 참조. {approval_label}. 미확정 성분은 null/NOT_READY. 사용자 승인 AI보조 참조는 독립 전문가 GOLD와 구분한다.'
        if name=='RQ5_reliability_cost':
            observed='\n\n'.join(f'- {r["cohort"]} / {r["method"]}: {r["rows"]}행, P50={r["total_latency_ms_p50"]}ms, P95={r["total_latency_ms_p95"]}ms, 토큰 측정={r["total_tokens_measured"]}, 누락={r["total_tokens_missing"]}.' for r in tables[name])
        if name=='RQ3_execution_spatial_gap' and available_gaps:observed=gap_markdown(available_gaps)
        if name=='RQ4_recovery_semantic_preservation':observed+='\n\n개발자가 코드를 수정한 뒤 별도 run으로 재실행한 결과는 runtime bounded recovery 성공으로 집계하지 않았다.'
        difference='확정된 내부 대조 범위 밖의 기술 효과 차이는 아직 산출할 수 없다.'
        if name=='RQ3_execution_spatial_gap' and available_gaps:
            difference='\n'.join(f'- {r["cohort"]}: 대상 {r["executable_rows"]}행 중 미실행/실행실패 {r["executable_rows"]-r["successful_execution_rows"]}행. 실제 실행된 결과의 공간일치(CGE)는 {r["CGE"]}.' for r in available_gaps)+'\n개발 수정 전후의 표현별 관측이며 다른 기술의 우열이나 통계적 개선으로 일반화하지 않는다.'
        report_sections(output/'reports'/(name+'.md'),f'{name}: 원시기록을 cohort·방법별로 분리해 비교한다. scope가 다른 component를 P0/P1로 대체하지 않았다.',observed,difference=difference,
            cases=serial(error_examples[:8])+'\n\n모든 오류 행의 원본 포인터는 metrics/error_examples.json에 보존했다.',
            stats='paired_diagnostic_statistics.json에 계획 출력 JSON schema 및 latency의 관측 검정을 기록했다. 과학적 정답 검정은 NOT_READY. 반복을 사례로 중복 계산하지 않았고 equivalence group을 bootstrap 단위로 사용했다. K=3이며 요구 K=5와 다르다. 표본군이 작고 사후 조건 라벨이므로 확증적 검정이 아니다.')
    answers='\n'.join(f'- {k}: {v}' for k,v in summary['rq_answers'].items())
    report_sections(output/'reports'/'final_results_summary.md','RQ1–RQ5, ablation, holdout 및 재현성 요구를 대조한다.',
        f'원시행 {len(rows)}개: {serial(counts)}. {approval_label}, holdout {summary["holdout_cases"]}건, 계획반복 K=3(요구5).\n\n'+answers,
        difference='성능 차이 미확정. 비용 차이는 위 RQ5 관측값만 사용하며 동일한 신뢰성을 확보했다는 가정을 하지 않는다.')
    final=output/'reports'/'final_results_summary.md'
    final.write_text('# 다섯 질문에 대한 현재 답변\n\n'+answers+f'\n\n숫자로 확인된 제한: {approval_label}, holdout {summary["holdout_cases"]}, 계획 K=3/요구5, 원시행 {len(rows)}.\n\n'+final.read_text(encoding='utf-8'),encoding='utf-8')
    interpretation='''# SCIE Results 해석 — NOT_READY

## 가장 강한 연구발견 5개
확정 연구발견은 0개다. 대신 검증 가능한 관측 5개를 구분한다.
1. 계획 출력과 실제 GIS 실행은 다른 실험이다.
2. 명시적 실행 성공과 공간정답의 일치 여부는 별도로 측정해야 한다.
3. DRAFT fault label에 대한 진단은 승인 오류검출 정확도가 아니다.
4. 비용 측정은 제공된 token·latency만 사용하며 미제공값을 0으로 만들지 않았다.
5. 현재 개발 노출 사례는 독립 holdout을 제공하지 않는다.

## 가장 예상 밖의 결과 3개
전체 방법 성능의 예상 대비 차이를 판정할 수 없다. 감사상 중요한 세 제한은 완전한 의미·근거·fault 정답 미확정, 공간 oracle의 제한된 대상 범위, P0/P1/H와 recovery 대조군 부재다.

## 실패 사례 유형
timeout/error 원본 행을 보존했다. 생성 성공, JSON schema 통과, GRAPH_RETURNED, SQL 일관성을 의미·공간정답으로 바꾸지 않았다.

## Reviewer가 공격할 가능성이 높은 한계
계획 표본은 영어5·한국어1의 편의 부분집합, K=3, holdout=0, 사후 조건 라벨이다. 작은 equivalence-group 수 때문에 CI가 불안정하다. 서로 다른 snapshot·하드웨어·component 범위를 합친 우열 비교는 불가능하다.

## 추가 실험 필요 여부
필요하다. 현재 승인 범위를 넘어 완전한 의미·실행계약·근거·fault 평가 참조를 확정하고, K=5 matched B0–B4/P0/P1/H, 독립 holdout, recovery 전후 의미·공간 oracle, 실패유형별 ablation을 확보해야 한다.

## 현재 결과로 주장 가능한 문장
기존 파일럿의 관측 비용과 결측 및 component 범위를 재현 가능한 RQ 형식으로 대조하였다. 확보된 사용자 승인 공간 참조는 그 대상·snapshot에 한정해 내부 비교하였다. 완전한 참조와 matched 비교조건·holdout이 없어 전반적인 기술 효과 판정은 유보하였다.

## 현재 결과로 주장하면 안 되는 문장
Ontology가 RAG보다 우수하다. P1이 silent failure를 줄였다. Recovery가 의미를 보존한다. 한글 의도분류 정확도나 holdout 성능이 입증되었다. 표 생성만으로 논문 Results가 완료되었다.
'''
    interpretation=interpretation.replace('승인 GOLD 부재','독립 전문가 GOLD 부재')
    interpretation+='\n\n## 이번 분석의 승인 수준\n'+approval_label+'\n사용자 승인은 AI 기원·파일럿 노출·불확실성을 없애지 않는다. 공간 참조는 일치하는 snapshot과 oracle hash가 있을 때만 비교한다.\n'
    coverage=summary['approved_reference_components']
    interpretation+=f'\n확보한 공간 객체 참조는 {coverage["spatial_objects"]}개 사례이며 Q4 동등질의군 범위이다. 그 밖의 공간 정답 coverage는 미확정이다. 확정 의미 label 집합 {coverage["semantic_labels"]}건, 부분 QEC 필드 {coverage["qec_partial_fields"]}건, 필수 근거 집합 {coverage["evidence_reference_sets"]}건이며 전체 의미·계획·근거 정확도로 대체하지 않는다.\n'
    if available_gaps:
        interpretation+='\n## 실제 내부 공간 대조 관측\n'+ '\n'.join(f'- {r["cohort"]}: 실행 {r["successful_execution_rows"]}/{r["executable_rows"]}, SCR={r["SCR"]}, CGE={r["CGE"]}, SSFR={r["SSFR"]}, 독립 equivalence group={r["equivalence_groups"]}.' for r in available_gaps)
        interpretation+='\n이는 승인된 고정 원천과의 내부 대조이다. 영어 표현의 실행 중단은 silent spatial failure와 다르다. 한 동등질의군의 표현별 결과로 방법 전체의 신뢰성 향상이나 통계적 유의성을 주장하지 않는다. 개발자의 코드 수정 후 재실행은 runtime bounded recovery의 성공 사례가 아니다.\n'
    (output/'reports'/'SCIE_RESULTS_INTERPRETATION.md').write_text(interpretation,encoding='utf-8')
    make_figures(output/'figures',tables)
    try:head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
    except subprocess.SubprocessError:head=None;dirty=None
    manifest={'run_id':run_id,'analysis_recorded_at':datetime.now(timezone.utc).isoformat(),'analysis_only':True,
        'status':'ANALYSIS_ARTIFACTS_COMPLETE_SCIENTIFIC_RESULTS_NOT_READY','scientific_completion':False,
        'git_sha_at_analysis':head,'git_dirty_at_analysis':dirty,'source_runs':provenance,
        'condition_metadata':{'path':str(condition_path),'sha256':digest(condition_path) if condition_path.is_file() else None,'post_hoc':True},
        'gold_audit':{'path':str(gold_audit_path),'sha256':digest(gold_audit_path) if gold_audit_path.is_file() else None,'audit':audit},
        'gold_scoring_adapter_status':'USER_APPROVED_INTERNAL_REFERENCE' if user_count else 'NO_APPROVED_REFERENCE_INPUT_SUPPLIED',
        'approved_reference_file':{'path':str(reference_path),'sha256':digest(reference_path)} if reference_path else None,
        'approved_reference_cases':approved_count,'user_approved_ai_assisted_cases':user_count,'independent_expert_gold_cases':expert_count,
        'evaluator_limitations':['semantic label-set score is not full semantic accuracy','reference completeness is not claim support',
            'semantic label F1 requires explicit approved labels; polygon/nearest oracle scoring is not enabled in this reanalysis runner',
            'McNemar repeat 0 was selected post hoc for this descriptive reanalysis; no preregistration claimed'],
        'required_missing':['complete independent semantic/spatial/evidence references','holdout','K5','matched P0/P1/H','recovery evaluation','controlled ablations'],
        'analysis_source_sha256':{str(p.relative_to(ROOT)):digest(p) for p in (Path(__file__),RESEARCH/'evaluation/rq_metrics.py')},
        'analysis_runner_made_model_calls':False,'analysis_runner_modified_production':False,
        'analysis_runner_modified_reference_files':False,'source_runs_may_span_production_revisions':True}
    jsonwrite(output/'manifest.json',manifest)
    latest=RESEARCH/'results/latest';latest.mkdir(parents=True,exist_ok=True)
    for folder in ('tables','reports','figures','metrics'):shutil.copytree(output/folder,latest/folder,dirs_exist_ok=True)
    shutil.copy2(output/'manifest.json',latest/'manifest.json')
    print(serial({'run_id':run_id,'rows':len(rows),'scientific_completion':False,'path':str(output)}))
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run-id',required=True);parser.add_argument('--conditions');parser.add_argument('--gold-audit');parser.add_argument('--extra-source',action='append',default=[]);parser.add_argument('--references')
    args=parser.parse_args()
    extra=[{'cohort':s.split('=',1)[0],'path':s.split('=',1)[1]} for s in args.extra_source]
    run(args.run_id,args.conditions,args.gold_audit,extra,args.references)
