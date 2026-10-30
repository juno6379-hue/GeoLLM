"""Descriptive research-only planner comparison, without invented gold accuracy."""
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
from importlib.metadata import version, PackageNotFoundError
import subprocess
from ..evaluation.metrics import distribution

RESEARCH = Path(__file__).resolve().parents[1]


def _schema(row):
    for key in ('output_schema_valid','schema_valid'):
        if isinstance(row.get(key), bool):
            return row[key]
    return None


def _actions(plan):
    """Only literal emitted identifiers; not semantic matching against expected actions."""
    if not isinstance(plan, dict):
        return []
    if isinstance(plan.get('action'),str):
        return [plan['action']]
    items = plan.get('actions', plan.get('steps', []))
    if not isinstance(items, list):
        return []
    values=[]
    for item in items:
        if isinstance(item,str):
            values.append(item)
        elif isinstance(item,dict):
            for key in ('action','capability','operation','tool'):
                if isinstance(item.get(key),str):
                    values.append(item[key]); break
    return values


def _clarify(row):
    plan=row.get('plan')
    if not isinstance(plan,dict):
        return None
    if plan.get('action') in ('explain','search','clarify','unsupported'):
        return plan['action']=='clarify'
    for key in ('needs_clarification','clarify','requires_clarification'):
        if isinstance(plan.get(key),bool):
            return plan[key]
    for key in ('decision','intent','action','status'):
        if isinstance(plan.get(key),str) and plan[key].upper() in ('CLARIFY','NEEDS_USER_INPUT','ASK_CLARIFICATION'):
            return True
    if any(a.upper() in ('CLARIFY','ASK_CLARIFICATION') for a in _actions(plan)):
        return True
    return None


def summarize(rows):
    results=[]
    for model,method in sorted({(str(r.get('model') or 'UNSPECIFIED'),str(r.get('method') or 'UNSPECIFIED')) for r in rows}):
        group=[r for r in rows if str(r.get('model') or 'UNSPECIFIED')==model and str(r.get('method') or 'UNSPECIFIED')==method]
        statuses=Counter(str(r.get('status','UNKNOWN')).upper() for r in group)
        schema=[_schema(r) for r in group]
        clarify=[_clarify(r) for r in group]
        actions=Counter(a for r in group for a in _actions(r.get('plan')))
        tools=Counter(call['tool_id'] for r in group if isinstance(r.get('plan'),dict)
            for call in (r['plan'].get('tool_calls') or []) if isinstance(call,dict) and isinstance(call.get('tool_id'),str))
        rec={'model':model,'method':method,'rows':len(group),'distinct_cases':len({r.get('case_id') for r in group}),
             'plan_objects':sum(isinstance(r.get('plan'),dict) for r in group),
             'schema_pass':sum(v is True for v in schema),'schema_fail':sum(v is False for v in schema),
             'schema_unmeasured':sum(v is None for v in schema),
             'schema_pass_rate_all_rows':sum(v is True for v in schema)/len(group) if all(v is not None for v in schema) else None,
             'clarify_true':sum(v is True for v in clarify),'clarify_false':sum(v is False for v in clarify),
             'clarify_unknown':sum(v is None for v in clarify),
             'timeout_rows':sum(n for s,n in statuses.items() if 'TIMEOUT' in s or 'TIMED_OUT' in s),
             'error_rows':sum(n for s,n in statuses.items() if 'ERROR' in s or s=='FAILED'),
             'rows_with_emitted_actions':sum(bool(_actions(r.get('plan'))) for r in group),
             'unique_emitted_actions':len(actions),'action_occurrences':json.dumps(dict(actions),ensure_ascii=False,sort_keys=True),
             'unique_emitted_tool_ids':len(tools),'tool_id_occurrences':json.dumps(dict(tools),ensure_ascii=False,sort_keys=True),
             'status_counts':json.dumps(dict(statuses),sort_keys=True),
             'planned_llm_calls_per_trial':2 if method=='B4' else None,
             'accuracy':None,'evqsr':None,'publication_status':'NOT_READY'}
        for field in ('latency_ms','input_tokens','output_tokens','llm_call_count'):
            values=[r.get(field,r.get('model_calls')) if field=='llm_call_count' else r.get(field) for r in group]
            rec.update({field+'_'+k:v for k,v in distribution(values).items()})
        results.append(rec)
    return results


def report_comparison(run_dir, rows_path=None, *, publish_latest=True):
    run=Path(run_dir).resolve()
    manifest_path=run/'manifest.json'
    manifest=json.loads(manifest_path.read_text(encoding='utf-8-sig'))
    if rows_path is None:
        candidates=[run/'comparison_rows.jsonl',run/'raw.jsonl']
        path=next((p for p in candidates if p.is_file()),candidates[0])
    else:
        path=Path(rows_path)
    rows=[json.loads(s) for s in path.read_text(encoding='utf-8-sig').splitlines() if s.strip()]
    coverage=sample_coverage(run/'cases.json')
    records=summarize(rows)
    output=run/'reports'; output.mkdir(exist_ok=True)
    fields=list(records[0]) if records else ['publication_status']
    with (output/'comparison_observables.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields); writer.writeheader(); writer.writerows(records)
    summary={'report_type':'PILOT — NOT FINAL PAPER RESULT','publication_status':'NOT_READY',
        'run_status':manifest.get('status','UNKNOWN'),
        'generated_at':datetime.now(timezone.utc).isoformat(),'run_id':run.name,'rows':len(rows),
        'manifest_sha256':hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        'raw_rows_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'verified_gold_count':0,'accuracy':None,'evqsr':None,'methods':records,
        'sample_coverage':coverage,
        'budget_notes':{'B4':'Two planned calls per trial (planner + reviewer); compare total observed token/latency budgets. Missing call totals remain unmeasured.',
                        'declared_run_budget':manifest.get('generation_budget',manifest.get('total_budget',manifest.get('budget')))},
        'distinct_cases':len({r.get('case_id') for r in rows}),
        'limitations':['Bounded convenience DRAFT subset from the 18-case source benchmark; no expert gold accuracy or EVQSR claims.',
            'B0-B4 are plan-only comparisons. B3 generic typed tool plans do not establish actual GIS baseline execution.',
            'P_current_production_no_llm has different execution conditions and must remain a separate cohort.',
            'Output JSON schema validity is explicit runner validation, not QEC semantic accuracy.',
            'Action occurrence is emitted vocabulary coverage, not correctness or required-action recall.',
            'Repeated trials do not increase independent case sample size.',
            'B4 must include both planner and reviewer costs; missing measurements are not zero.']}
    summary['limitations'] += coverage['limitations']
    (output/'comparison_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    text=['# 계획 비교 관측 보고서 — 예비실험', '', '**PILOT — NOT FINAL PAPER RESULT / 논문 상태: NOT_READY**', '',
        f'실행 상태: {summary["run_status"]}. COMPLETED 상태에서만 latest_comparison 요약을 갱신합니다.', '',
        f'총 실행 행: {len(rows)}, 고유 사례: {summary["distinct_cases"]}. 원본 18개 DRAFT 사례의 편의 부분집합에 대한 **계획 출력 비교**입니다. 독립적인 전문가 정답이 없어 정확도와 EVQSR은 null입니다.', '',
        f'선택 표본 언어: {json.dumps(coverage["language_counts"],ensure_ascii=False)}; 범주: {json.dumps(coverage["category_counts"],ensure_ascii=False)}. cases.json에 기록된 언어·범주를 집계하며, 누락 항목은 미기록으로 표시합니다.', '',
        '**표본 한계:** 모델 호출 전에 선택한 편의 부분집합이며 Wreck 질의에 편중되어 있습니다. 원본 18개의 언어 균형이 선택된 표본에 유지된다고 볼 수 없습니다. 위 언어 분포와 제한된 사례 수로는 결과를 한글 의도분류 전체 성능으로 일반화할 수 없습니다. 범주별 대표성과 통계적 층화 표본추출을 주장하지 않습니다.', '',
        'B3는 일반적인 타입 지정 도구 계획 출력이며 실제 GIS 실행 baseline이 아닙니다. P_current_production_no_llm은 실행 조건이 달라 별도 cohort로 해석해야 합니다.', '',
        'B4는 계획 생성과 검토의 **2회 호출 총예산**으로 비교해야 합니다. 토큰·지연은 두 호출 합계가 수집되었는지 실행 manifest와 함께 확인해야 하며, 누락은 0으로 채우지 않습니다.', '',
        '| 모델 | 방법 | 실행 | 출력 JSON 스키마 통과/실패/미측정 | 확인질문 true/false/unknown | timeout/error | 실제 평균 지연(ms) | 지연 중앙값(ms) |',
        '| --- | --- | --- | --- | --- | --- | --- | --- |']
    for r in records:
        median='미측정' if r['latency_ms_p50'] is None else f'{r["latency_ms_p50"]:.2f}'
        average='미측정' if r['latency_ms_mean'] is None else f'{r["latency_ms_mean"]:.2f}'
        text.append(f'| {r["model"]} | {r["method"]} | {r["rows"]} | {r["schema_pass"]}/{r["schema_fail"]}/{r["schema_unmeasured"]} | {r["clarify_true"]}/{r["clarify_false"]}/{r["clarify_unknown"]} | {r["timeout_rows"]}/{r["error_rows"]} | {average} | {median} |')
    text += ['', '출력 JSON 스키마 통과는 QEC 의미 정확도나 의미적 정답을 뜻하지 않습니다. action coverage는 출력된 동작 식별자의 종류·빈도이며 필수 작업 충족률이 아닙니다. 자세한 토큰·지연 측정수/누락수/IQR과 상태수는 CSV에 기록했습니다.', '',
        '원시 응답과 실행 계획은 이 요약에 복사하지 않습니다. 원본 manifest와 raw rows의 SHA-256을 JSON에 보존했습니다. prompt_trace_index.csv에는 호출별 prompt SHA-256과 원본 JSONL record/call 위치를 기록하며 프롬프트 원문은 raw에만 남깁니다. 반복 실행은 동일 사례의 반복 관측이며 독립 표본으로 계산하지 않습니다.', '']
    (output/'comparison_report_KR.md').write_text('\n'.join(text),encoding='utf-8')
    packet_path=run/'evidence_packets.json'
    packets=json.loads(packet_path.read_text(encoding='utf-8-sig')) if packet_path.is_file() else None
    write_provenance_audit(output, manifest, packets, manifest_path)
    build_query_comparison(output, rows, source_packet=packets)
    write_prompt_trace(output, rows, path)
    build_diagnostic_figure(output, records)
    if publish_latest and str(manifest.get('status','')).upper()=='COMPLETED':
        latest=RESEARCH/'latest_comparison'; latest.mkdir(exist_ok=True)
        for name in ('comparison_observables.csv','comparison_summary.json','comparison_report_KR.md','query_comparison_KR.md','prompt_trace_index.csv','provenance_audit.json','D2_comparison_observables.png','D2_comparison_observables.csv'):
            shutil.copy2(output/name,latest/name)
        shutil.copy2(manifest_path,latest/'manifest.json')
    return summary


def write_provenance_audit(output, manifest, packets, manifest_path):
    """Post-hoc audit: never claim the current environment was the run environment."""
    packages={}
    for name in ('jsonschema','pydantic','PyYAML'):
        try: packages[name]=version(name)
        except PackageNotFoundError: packages[name]=None
    try:
        branch=subprocess.check_output(['git','branch','--show-current'],cwd=RESEARCH,
            text=True,encoding='utf-8',stderr=subprocess.DEVNULL,timeout=5).strip()
    except (OSError,subprocess.SubprocessError): branch=None
    sources=[]
    if isinstance(packets,dict):
        for case_id,methods in packets.items():
            if not isinstance(methods,dict): continue
            for method,packet in methods.items():
                if not isinstance(packet,dict): continue
                for source in packet.get('sources',[]):
                    if not isinstance(source,dict): continue
                    sources.append({'case_id':case_id,'method':method,'path':source.get('path'),
                        'locator':source.get('locator'),'sha256_recorded_in_packet':source.get('sha256'),
                        'nodes_path':source.get('nodes_path'),'nodes_sha256_recorded_in_packet':source.get('nodes_sha256')})
    schema=manifest.get('plan_output_schema')
    schema_hash=hashlib.sha256(json.dumps(schema,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest() if schema is not None else None
    data={'audit_type':'POST_HOC_PROVENANCE_AUDIT','recorded_at':datetime.now(timezone.utc).isoformat(),
        'warning':'Current branch/package observations were measured after the run; they are not evidence of the runtime state at model-call time.',
        'original_manifest_sha256':hashlib.sha256(Path(manifest_path).read_bytes()).hexdigest(),
        'branch_recorded_at_run':manifest.get('git_branch',manifest.get('branch')),
        'current_branch_observed_at_audit':branch,
        'host_package_versions_observed_at_audit':packages,
        'plan_output_schema_sha256_canonical':schema_hash,
        'schema_hash_encoding':'UTF-8 JSON ensure_ascii=False, sort_keys=True, separators=(comma,colon)',
        'source_hash_basis':'Only hashes already recorded in source packets; source files were not re-read or re-hashed.',
        'packet_recorded_sources':sources,
        'prompt_template_hash_at_run':manifest.get('prompt_template_hash',manifest.get('template_hash')),
        'prompt_template_hash_status':'RECORDED' if manifest.get('prompt_template_hash',manifest.get('template_hash')) else 'NOT_RECORDED_AT_RUN',
        'prompt_trace_note':'Per-call exact prompt hashes are in prompt_trace_index.csv; these are not a shared template hash.',
        'embedding':{'status':'NOT_USED','scope':'B0-B4 lexical evidence retrieval; no embedding model inference in this comparison'},
        'database':{'status':'NOT_USED_B0_B4','scope':'Plan-only comparison; no GIS execution or database query'},
        'production_P':'Separate conditions: no database/embedding assumption is transferred to P_current_production_no_llm.'}
    (Path(output)/'provenance_audit.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    return data


def sample_coverage(cases_path):
    path=Path(cases_path)
    data=json.loads(path.read_text(encoding='utf-8-sig')) if path.is_file() else []
    cases=data if isinstance(data,list) else data.get('cases',[])
    return {'source':'cases.json','source_sha256':hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None,
        'case_count':len(cases),'case_ids':[c.get('case_id') for c in cases],
        'language_counts':dict(Counter(c.get('language') or 'UNRECORDED' for c in cases)),
        'category_counts':dict(Counter(c.get('category') or 'UNRECORDED' for c in cases)),
        'equivalence_group_counts':dict(Counter(c.get('equivalence_group') or 'UNRECORDED' for c in cases)),
        'selection':'Convenience subset selected before model calls; Wreck-heavy, not representative.',
        'limitations':['Selected cases are a convenience subset, not a statistically representative stratified sample.',
            'The selected language distribution and limited case count do not support claims about overall Korean intent classification.',
            'Wreck-heavy query coverage does not establish general marine-domain coverage.']}


def write_prompt_trace(output, rows, raw_path):
    """Hash prompts while retaining only pointers to the raw records, never prompt text."""
    raw_path=Path(raw_path)
    raw_digest=hashlib.sha256(raw_path.read_bytes()).hexdigest()
    records=[]
    # row_number is 1-based among nonempty JSONL records (not physical blank lines).
    for row_number,row in enumerate(rows,1):
        calls=row.get('calls')
        if not isinstance(calls,list): continue
        for call_index,call in enumerate(calls):
            prompt=call.get('prompt') if isinstance(call,dict) else None
            records.append({'raw_file':raw_path.name,'raw_file_sha256':raw_digest,
                'jsonl_record_number':row_number,'call_index_zero_based':call_index,
                'case_id':row.get('case_id'),'method':row.get('method'),'repeat':row.get('repeat'),
                'prompt_sha256':hashlib.sha256(prompt.encode('utf-8')).hexdigest() if isinstance(prompt,str) else None,
                'prompt_chars':len(prompt) if isinstance(prompt,str) else None,
                'trace_status':'RECORDED' if isinstance(prompt,str) else 'MISSING_PROMPT'})
    columns=('raw_file','raw_file_sha256','jsonl_record_number','call_index_zero_based','case_id','method','repeat','prompt_sha256','prompt_chars','trace_status')
    with (Path(output)/'prompt_trace_index.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=columns); writer.writeheader(); writer.writerows(records)


def build_query_comparison(output, rows, *, source_packet=None, answer_max_chars=800):
    """Human-readable candidate outputs, strictly outside gold annotation files."""
    def cell(value):
        if value is None: return '미측정'
        if not isinstance(value,str): value=json.dumps(value,ensure_ascii=False)
        return value.replace('|','\\|').replace('\n','<br>')
    queries={}
    benchmark=RESEARCH/'benchmark/query_cases_v1.jsonl'
    if benchmark.is_file():
        queries={r['case_id']:r.get('query','') for r in (json.loads(s) for s in benchmark.read_text(encoding='utf-8-sig').splitlines() if s.strip())}
    lines=['# 사례별 계획 후보 비교', '', '**모든 모델 답변은 미검증 후보입니다. 정답·승인된 근거·실행 완료를 뜻하지 않습니다.**', '',
        '이 문서는 모델 출력 검토용이며 GOLD 검수 양식과 분리했습니다. 근거 ID 조회는 식별자 연결 확인일 뿐, 답변과 근거 내용의 의미적 일치나 근거 정답률을 판정하지 않습니다.', '']
    for case_id in sorted({str(r.get('case_id','UNKNOWN')) for r in rows}):
        group=[r for r in rows if str(r.get('case_id','UNKNOWN'))==case_id]
        query=next((r.get('query') for r in group if r.get('query')),queries.get(case_id,'원문 미제공'))
        lines += [f'## {cell(case_id)}', '', f'질의: {cell(query)}', '',
            '| 방법 | 반복 | action | target_features | radius_m | missing_inputs | status |',
            '| --- | --- | --- | --- | --- | --- | --- |']
        for row in group:
            plan=row.get('plan') if isinstance(row.get('plan'),dict) else {}
            lines.append('| '+' | '.join(cell(v) for v in (row.get('method'),row.get('repeat'),plan.get('action'),plan.get('target_features'),plan.get('radius_m'),plan.get('missing_inputs'),row.get('status')))+' |')
        for row in group:
            plan=row.get('plan') if isinstance(row.get('plan'),dict) else {}
            lines += ['', f'### {cell(row.get("method"))} / 반복 {cell(row.get("repeat"))} — 미검증 후보', '']
            answer=plan.get('answer')
            if isinstance(answer,str):
                excerpt=answer[:answer_max_chars]
                lines.append('후보 답변: '+cell(excerpt))
                if len(answer)>answer_max_chars:
                    lines.append(f'**표시 길이 제한: 전체 {len(answer)}자 중 처음 {answer_max_chars}자만 표시했습니다.**')
            else: lines.append('구조화된 후보 답변 없음. raw 응답은 원시 실행 기록에 보존됩니다.')
            refs=plan.get('evidence_refs')
            packet=row.get('source_packet',source_packet)
            if isinstance(packet,dict) and case_id in packet:
                packet=packet[case_id].get(row.get('method'),{})
            lookup=packet if isinstance(packet,dict) else {}
            if isinstance(lookup.get('sources'),list):
                lookup={s['locator']:s for s in lookup['sources'] if isinstance(s,dict) and isinstance(s.get('locator'),str)}
            if isinstance(refs,list) and refs:
                lines.append('출력 근거 ID: '+cell(refs))
                for ref in refs:
                    if isinstance(ref,str) and ref in lookup:
                        lines.append(f'- {cell(ref)}: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.')
                        source=lookup[ref]
                        if isinstance(source,dict) and source.get('path'):
                            lines.append(f'  원천 경로: {cell(source["path"])}; SHA-256: {cell(source.get("sha256"))}')
                    else: lines.append(f'- {cell(ref)}: 제공 source packet으로 식별자 연결을 확인하지 못함.')
            initial=next((row[k] for k in ('first_plan','initial_plan','plan_before_review') if isinstance(row.get(k),dict)),None)
            if row.get('method')=='B4':
                if initial is None:
                    lines.append('B4 최초/검토후 계획 차이: 최초 계획 구조 미제공으로 비교 불가.')
                else:
                    keys=('action','target_features','attributes','spatial_relation','location_text','radius_m','crs','tool_calls','evidence_refs','missing_inputs','answer')
                    changed=[key for key in keys if initial.get(key)!=plan.get(key)]
                    lines.append('B4 최초→검토후 변경 필드: '+cell(changed))
                    lines.append('변경 유무는 개선·수정 성공을 뜻하지 않습니다.')
    (Path(output)/'query_comparison_KR.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


def build_diagnostic_figure(output, records):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    fonts={font.name for font in font_manager.fontManager.ttflist}
    korean='Malgun Gothic' in fonts
    if korean:
        plt.rcParams['font.family']='Malgun Gothic'
    columns=('model','method','rows','schema_pass','schema_fail','schema_unmeasured',
             'timeout_rows','error_rows','latency_ms_mean','latency_ms_p50','latency_ms_iqr','latency_ms_measured','latency_ms_missing')
    with (output/'D2_comparison_observables.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=columns,extrasaction='ignore'); writer.writeheader(); writer.writerows(records)
    fig,(left,right)=plt.subplots(1,2,figsize=(14,6))
    labels=[r['model']+' / '+r['method'] for r in records]
    bottom=[0]*len(records)
    for field,label,color in [('schema_pass','통과' if korean else 'pass','#4c8da8'),('schema_fail','실패' if korean else 'fail','#c45c4c'),('schema_unmeasured','미측정' if korean else 'unmeasured','#b0b0b0')]:
        values=[r[field] for r in records]
        left.barh(range(len(records)),values,left=bottom,label=label,color=color)
        bottom=[a+b for a,b in zip(bottom,values)]
    left.set_yticks(range(len(labels)),labels,fontsize=8); left.legend(fontsize=8)
    left.set_xlabel('출력 JSON 스키마 관측 행 수' if korean else 'Output JSON schema observations')
    for i,r in enumerate(records):
        if r['latency_ms_mean'] is not None: right.scatter(r['latency_ms_mean'],i,marker='o',color='#4c8da8',label=('평균' if korean else 'mean') if i==0 else None)
        if r['latency_ms_p50'] is not None: right.scatter(r['latency_ms_p50'],i,marker='x',color='#c45c4c',label=('중앙값' if korean else 'median') if i==0 else None)
    right.set_yticks(range(len(labels)),labels,fontsize=8)
    right.set_xlabel('실측 지연(ms); 호출 예산·실행 조건을 함께 해석' if korean else 'Measured latency (ms); account for call budgets')
    handles,_=right.get_legend_handles_labels()
    if handles: right.legend(fontsize=8)
    fig.suptitle('D2 계획 출력 관측 — 예비실험 / 정확도 아님\n호출 예산·실행 조건 차이로 속도 우열을 주장하지 않음' if korean else 'D2 Plan output observations - PILOT, not accuracy\nDifferent call budgets: no speed-superiority claim')
    fig.tight_layout(rect=(0,0,1,.90)); fig.savefig(output/'D2_comparison_observables.png',dpi=150); plt.close(fig)


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--run-dir',required=True); parser.add_argument('--rows-path')
    args=parser.parse_args()
    result=report_comparison(args.run_dir,args.rows_path)
    print(json.dumps({'rows':result['rows'],'publication_status':result['publication_status']}))
