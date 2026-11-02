"""Read-only Table 10–14 projection from one frozen eight-method run.

No re-scoring, pilot substitution, model calls, or inferred metric equivalence.
Missing observations and zero denominators are distinct and remain visible.
"""
from __future__ import annotations
from .rq3_development import load_rq3_development
from collections import defaultdict
import hashlib,json,math,re
from pathlib import Path

METHODS=('B0','B1','B2','B3','B4','P0','H','P1')
DETECTORS=('B4','P0','H')


def metric(value=None,numerator=None,denominator=None,reason='',unit='ratio',status=None,**extra):
    valid=isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)
    return dict(value=value if valid else None,numerator=numerator,denominator=denominator,
                status=status or ('MEASURED' if valid else 'UNMEASURED'),reason=reason,unit=unit,**extra)


def rate(values,reason,unknown_membership=0):
    n=len(values);known=[v for v in values if isinstance(v,bool)];yes=sum(v is True for v in known)
    missing=n-len(known)
    if unknown_membership:return metric(numerator=yes,denominator=n,reason='대상 집합 소속 미측정: '+reason,missing=missing,unknown_membership=unknown_membership)
    if not n:return metric(numerator=0,denominator=0,status='UNDEFINED',reason='분모 0: '+reason,missing=0)
    return metric(yes/n if not missing else None,yes,n,reason=reason if not missing else '관측 누락: '+reason,missing=missing)


def summary_rate(obj,reason):
    if not isinstance(obj,dict):return metric(reason='원본 지표 없음: '+reason)
    n=obj.get('denominator');missing=obj.get('missing');value=obj.get('value')
    if n==0:return metric(numerator=0,denominator=0,status='UNDEFINED',reason='분모 0: '+reason,missing=missing)
    numerator=None
    if isinstance(value,(float,int)) and not isinstance(value,bool) and isinstance(n,int) and math.isfinite(value) and abs(value*n-round(value*n))<1e-7:numerator=round(value*n)
    if missing or obj.get('unknown_attempt_membership'):value=None
    return metric(value,numerator,n,reason,missing=missing,measured=obj.get('measured'))


def statistic(obj,name,unit):
    if not isinstance(obj,dict):return metric(reason='비용 계측 없음',unit=unit)
    value=obj.get(name) if not obj.get('missing') else None
    return metric(value,denominator=obj.get('measured'),reason='원본 비용 '+name+'; 누락 포함이면 집계 미표시',unit=unit,missing=obj.get('missing'))


def conditional_correctness(method):
    """rq_metrics.spatial_gap CGE=P(spatial_correct | execution_success).

    For the v3 complete-success cohort this is exactly 1-SSFR, only when both
    execution membership and all conditional spatial observations are measured.
    It is neither raw SpatialCorrectness nor ESR minus joint success.
    """
    success=method.get('execution_success_all_eligible') or {}
    failure=method.get('silent_spatial_failure_given_success') or {}
    result=summary_rate(failure,'CGE=P(Spatial correct | Execution success), rq_metrics.spatial_gap')
    if (success.get('missing')!=0 or success.get('measured')!=success.get('denominator')
            or failure.get('missing')!=0 or failure.get('measured')!=failure.get('denominator')
            or failure.get('unknown_attempt_membership')):
        return metric(denominator=failure.get('denominator'),reason='성공 집합 소속 또는 공간 관측 누락')
    if result['status']=='MEASURED':
        result['value']=1-result['value']
        if result['numerator'] is not None:result['numerator']=result['denominator']-result['numerator']
    return result


def count_metric(value,reason='관측 개수'):
    return metric(value,reason=reason,unit='count')


def detector_metrics(rows):
    invalid=[r for r in rows if r.get('expected_invalid') is True]
    controls=[r for r in rows if r.get('expected_invalid') is False]
    unknown=sum(not isinstance(r.get('expected_invalid'),bool) for r in rows)
    return dict(recall=rate([r.get('predicted_invalid') for r in invalid],'실제 invalid 중 invalid 판정',unknown),
        false_ready=rate([not r['predicted_invalid'] if isinstance(r.get('predicted_invalid'),bool) else None for r in invalid],'실제 invalid 중 ready 판정',unknown),
        false_block=rate([r.get('predicted_invalid') for r in controls],'정상 control 중 invalid 판정',unknown))


def recovery_metrics(rows):
    eligible=[r for r in rows if r.get('recovery_eligible') is True]
    attempted=[r for r in eligible if r.get('recovery_attempted') is True]
    unknown_eligible=sum(not isinstance(r.get('recovery_eligible'),bool) for r in rows)
    unknown_attempt=sum(not isinstance(r.get('recovery_attempted'),bool) for r in eligible)
    kwargs=dict(eligible_n=count_metric(len(eligible)),attempted_n=count_metric(len(attempted)),
        recovery_success=rate([r.get('recovery_success') for r in attempted],'복구를 실제 시도한 적격 사례',unknown_eligible+unknown_attempt),
        semantic_preservation=rate([r.get('semantic_preservation') for r in attempted],'명시 task tuple 보존; 인간 자연어 의미 검수 아님',unknown_eligible+unknown_attempt),
        semantic_drift=rate([not r['semantic_preservation'] if isinstance(r.get('semantic_preservation'),bool) else None for r in attempted],'task tuple 변경; 보존 false의 보수적 반대',unknown_eligible+unknown_attempt),
        recovered_spatial_correctness=rate([r.get('spatial_correct') for r in attempted],'복구 시도 후 source-bound 공간 oracle',unknown_eligible+unknown_attempt),
        joint_recovery=rate([r.get('joint_success') for r in attempted],'실행·task tuple·공간 oracle 공동 성공',unknown_eligible+unknown_attempt),
        first_repair=metric(reason='회차 번호·첫 복구 시도 성공 전용 계측 없음'),
        escalation=metric(reason='명시 escalation 판정·분모 미계측'),
        safe_abstention=metric(reason='최종 사용자 안내까지 포함한 안전 중단 성공 계약 미측정'),
        forbidden_recovery_proposals=count_metric(sum(r.get('forbidden_recovery_proposed') is True for r in rows)))
    if unknown_eligible:kwargs['eligible_n']=metric(reason='복구 적격성 누락',unit='count')
    if unknown_attempt:kwargs['attempted_n']=metric(reason='복구 시도 여부 누락',unit='count')
    return kwargs


class Reader:
    def __init__(self,root,rid):
        if not re.fullmatch(r'\d{8}_gold_v2_eight_k\d+_v\d+',rid or ''):raise ValueError('Invalid selected run ID')
        self.root=Path(root).resolve();self.base=(self.root/'research/marine_geollm_scie/runs'/rid).resolve()
        if not self.base.is_relative_to(self.root):raise ValueError('Run outside root')
        self.sources=[];self.errors=[]
    def load(self,name,default):
        p=(self.base/name).resolve()
        if not p.is_relative_to(self.base):raise ValueError('Artifact outside selected run')
        source=dict(path=p.relative_to(self.root).as_posix(),sha256=None,status='MISSING')
        self.sources.append(source)
        if not p.is_file():return default
        raw=p.read_bytes();source.update(sha256=hashlib.sha256(raw).hexdigest(),status='AVAILABLE')
        try:
            text=raw.decode('utf-8-sig')
            value=[json.loads(s) for s in text.splitlines() if s.strip()] if p.suffix=='.jsonl' else json.loads(text)
            if isinstance(default,list) and (not isinstance(value,list) or any(not isinstance(x,dict) for x in value)):raise ValueError('Invalid row collection')
            if isinstance(default,dict) and not isinstance(value,dict):raise ValueError('Invalid object')
            return value
        except (ValueError,UnicodeError):
            source['status']='INVALID';self.errors.append(source['path']);return default


def table(title,columns,rows,notes,refs):
    return dict(title=title,columns=[dict(key=k,label=v) for k,v in columns],rows=rows,notes=notes,source_refs=refs)


def build_paper_tables(root,selected_run_id):
    # Missing research files are a supported dashboard state, not HTTP 500.
    # Reject unsafe IDs before opening any path and expose an unavailable block.
    if not isinstance(selected_run_id,str) or not re.fullmatch(r'\d{8}_gold_v2_eight_k\d+_v\d+',selected_run_id):
        return dict(schema_version='paper_tables_v1',run_id=None,tables={},sources=[],
                    errors=['NO_SELECTED_RUN' if selected_run_id is None else 'INVALID_SELECTED_RUN'],
                    status='UNAVAILABLE_SELECTED_RUN',source_only=True,models_called=False,
                    research_modified=False,completion_gate={},execution_identity={})
    try:reader=Reader(root,selected_run_id)
    except ValueError:
        return dict(schema_version='paper_tables_v1',run_id=None,tables={},sources=[],
                    errors=['INVALID_SELECTED_RUN_PATH'],status='UNAVAILABLE_SELECTED_RUN',
                    source_only=True,models_called=False,research_modified=False,
                    completion_gate={},execution_identity={})
    summary=reader.load('report_with_faults/summary.json',{})
    faults=reader.load('faults/rows.jsonl',[])
    identities=[(r.get('case_id'),r.get('method'),r.get('repeat',0)) for r in faults]
    if len(set(identities))!=len(identities):
        reader.errors.append('DUPLICATE_CONTROLLED_OBSERVATION');faults=[]
    # The comparison manifest supplies frozen lineage; raw answers are not parsed
    # into new semantic scores, nor are historical pilot metrics imported.
    manifest=reader.load('comparison/manifest.json',{})
    for contract in ['research/marine_geollm_scie/evaluation/rq_metrics.py','research/marine_geollm_scie/protocol/paper_metric_definitions.md']:
        p=(reader.root/contract).resolve()
        if not p.is_relative_to(reader.root):raise ValueError('Contract outside root')
        reader.sources.append(dict(path=contract,sha256=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None,status='AVAILABLE' if p.is_file() else 'MISSING',scope='DEFINITION_ONLY_NO_PILOT_RESULTS'))
    overall=summary.get('overall_by_method',{})
    source_refs=reader.sources
    grouped=defaultdict(list)
    for r in faults:
        if r.get('method') in DETECTORS:
            grouped[(r['method'],r.get('error_type','UNKNOWN'))].append(r)
            grouped[(r['method'],'ALL_CONTROLLED')].append(r)
    error_types=['ALL_CONTROLLED']+sorted({r.get('error_type','UNKNOWN') for r in faults})
    if not faults:error_types=['UNAVAILABLE']
    rows10=[];rows12=[]
    for error_type in error_types:
        for method in DETECTORS:
            rows=grouped[(method,error_type)]
            d=detector_metrics(rows); rec=recovery_metrics(rows)
            if not rows:
                d={k:metric(reason='해당 방법·오류유형 관측 없음') for k in d}
                rec={k:metric(reason='해당 방법·오류유형 관측 없음',unit=v.get('unit','ratio')) for k,v in rec.items()}
            rows10.append(dict(error_type=error_type,method=method,**d))
            role=('USER_INPUT_REQUIRED' if error_type=='geometry' else 'SOURCE_ABSTENTION_REQUIRED' if error_type=='source' else 'VALID_CONTROL' if error_type=='control' else 'MIXED_SCOPE' if error_type=='ALL_CONTROLLED' else 'RECOVERY_CONTRACT')
            rows12.append(dict(error_type=error_type,method=method,recovery_role=role,**rec))
    t10=table('Table 10. 오류 유형별 검출 성능', [('error_type','오류 유형'),('method','방법'),('recall','검출 Recall'),('false_ready','False Ready'),('false_block','False Block')],rows10,
        ['B4=LLM Review, P0=Deterministic Validator, H=Hybrid. 동일 통제 오류 8종과 정상 control 1개씩이며 일반 질의 정확도와 다릅니다.','Recall은 invalid/ready 이진 검출입니다. 입력 오류 유형별 집계이며 정확한 오류 사유 분류 Recall이 아닙니다. coverage 일괄 차단을 개별 오류 원인 진단 성공으로 확대하지 않습니다.','predicted_invalid는 common execution floor 적용 전 검출 판정입니다. 정상 control 분모는 오류별 행에서 0일 수 있습니다.','누락 판정을 제외하지 않습니다. 오류 유형별 N=1인 단회 관측의 일반화·신뢰구간을 주장하지 않습니다.'],source_refs)
    rows11=[];rows14=[]
    for method in METHODS:
        m=overall.get(method,{}); costs=m.get('costs',{})
        esr=summary_rate(m.get('execution_success_all_eligible'),'고정 공간 적격 질의 전체 분모')
        sc=summary_rate(m.get('spatial_correctness'),'source-bound 객체 oracle; 누락을 오답/정답으로 대체하지 않음')
        evqsr=metric(denominator=esr.get('denominator'),reason='공식 EVQSR=S∧P∧X∧G∧E; 동일 적격 사례의 semantic/plan/execution/spatial/evidence boolean 모두 연결된 관측 없음')
        rows11.append(dict(method=method,esr=esr,spatial_correctness=sc,joint_execution_spatial_success=summary_rate(m.get('joint_execution_spatial_success'),'실행과 공간 정답의 공동 성공; raw spatial 미측정과 별개'),cge=conditional_correctness(m),
            execution_correctness_gap=metric(m.get('execution_correctness_gap'),denominator=m.get('execution_success_all_eligible',{}).get('denominator'),reason='원본 gap=ESR−joint_execution_spatial_success; raw spatial_correctness와의 차이가 아님'),
            ssfr=summary_rate(m.get('silent_spatial_failure_given_success'),'실행 성공 조건부 silent spatial failure'),evqsr=evqsr,paired_delta_ci=metric(reason='반복·paired resampling CI 미계측')))
        detectors=detector_metrics(grouped[(method,'ALL_CONTROLLED')]) if method in DETECTORS and grouped[(method,'ALL_CONTROLLED')] else {k:metric(reason='해당 방법 통제 fault 관측 없음') for k in ['false_ready','false_block']}
        rows14.append(dict(method=method,evqsr=evqsr,spatial_correctness=sc,false_ready=detectors['false_ready'],false_block=detectors['false_block'],
            latency_p50=statistic(costs.get('latency_seconds'),'p50','seconds'),latency_p95=statistic(costs.get('latency_seconds'),'p95','seconds'),
            input_tokens=statistic(costs.get('input_tokens'),'mean','count'),output_tokens=statistic(costs.get('output_tokens'),'mean','count'),tool_calls=statistic(costs.get('tool_calls'),'mean','count'),
            escalation=metric(reason='전체 질의 escalation 계약 미계측'),evidence_completeness=metric(reason='근거 완전성 개별 판정·분모 미계측'),provenance_completeness=metric(reason='답변 provenance 완전성 미측정; 파일 hash 무결성과 별개')))
    t11=table('Table 11. 실행 성공과 공간 정답 분리', [('method','방법'),('esr','ESR'),('spatial_correctness','관측 Spatial Correctness'),('joint_execution_spatial_success','실행·공간 공동 성공'),('cge','CGE: 성공 조건부 공간 정답'),('execution_correctness_gap','원본 Execution–Correctness Gap'),('ssfr','SSFR'),('evqsr','EVQSR'),('paired_delta_ci','Paired Δ / CI')],rows11,
        [summary.get('execution_denominator_policy','공간 실행 분모 계약 미제공'),'CGE는 rq_metrics.spatial_gap의 P(공간 정답|실행 성공)이며 성공 집합·공간 관측이 완전할 때만 1−SSFR입니다. 성공 분모가 0이면 산출 불가입니다.','관측 Spatial Correctness의 null을 공동 성공 0으로 대체하지 않습니다. 원본 gap은 ESR−joint_execution_spatial_success이며 raw spatial_correctness와의 차이가 아닙니다.','EVQSR는 paper_metric_definitions의 S∧P∧X∧G∧E. 어느 필수 관측이든 누락되면 null입니다.','동일 의미 Q4 세 표현은 독립 표본 세 개가 아닙니다. K1이며 paired Δ/CI를 생성하지 않습니다.'],source_refs)
    t12=table('Table 12. 오류 유형별 복구와 의미 보존', [('error_type','오류 유형'),('method','방법'),('recovery_role','처리 구분'),('eligible_n','Eligible N'),('attempted_n','시도 N'),('recovery_success','Recovery Success'),('first_repair','First Repair'),('semantic_preservation','Semantic Preservation'),('semantic_drift','Semantic Drift'),('recovered_spatial_correctness','Recovered Spatial Correctness'),('joint_recovery','공동 복구 성공'),('escalation','Escalation'),('safe_abstention','Safe Abstention')],rows12,
        ['복구율 분모는 recovery_eligible=true 중 recovery_attempted=true인 실제 사례입니다. 적격·시도 수를 함께 표시합니다.','semantic_preservation은 명시 task tuple 비교이며 독립 인간 자연어 의미 정확도가 아닙니다.','geometry/source는 추가 입력·자료 확인이 필요한 별도 중단군입니다. 권한 오류 통제 사례는 이 run에 없습니다. 안전 중단을 복구 성공에 합산하지 않습니다.','첫 복구 회차·escalation·최종 안전 안내 전용 판정은 기록되지 않아 null입니다.'],source_refs)
    rows13=[]
    for name in ['Full P1','w/o Ontology','w/o Bounded KG','w/o QEC','w/o Validator','w/o Post-validation Recovery']:
        row=dict(configuration=name)
        for k in ['semantic_errors','schema_errors','spatial_errors','runtime_errors','evidence_errors']:
            row[k]=metric(reason='5종 오류 분류 계약·ablation 관측 없음',unit='count')
        row.update(evqsr=metric(reason='정의된 EVQSR의 5개 필수 관측 미완비'),spatial_correctness=summary_rate(overall.get('P1',{}).get('spatial_correctness'),'Full P1 원본 공간 지표') if name=='Full P1' else metric(reason='해당 제거 실험 미실행'),ablation_delta=metric(reason='실제 모듈 제거 실험 미실행'))
        if name=='Full P1':row['observed_machine_error_types']=overall.get('P1',{}).get('error_types',{})
        rows13.append(row)
    t13=table('Table 13. 구성요소 제거 실험 준비 상태', [('configuration','구성'),('semantic_errors','Semantic'),('schema_errors','Schema'),('spatial_errors','Spatial'),('runtime_errors','Runtime'),('evidence_errors','Evidence'),('evqsr','EVQSR'),('spatial_correctness','Spatial Correctness'),('ablation_delta','Ablation Δ')],rows13,
        ['Full P1 관측만 존재합니다. B0–H 방법 대조를 P1의 모듈 제거 실험으로 전용하지 않습니다.','5종 오류 범주 매핑은 사전 계약이 없어 기존 machine failure key를 임의 재분류하지 않습니다.'],source_refs)
    t14=table('Table 14. 신뢰성 및 비용', [('method','방법'),('evqsr','EVQSR'),('spatial_correctness','Spatial Correctness'),('false_ready','False Ready'),('false_block','False Block'),('latency_p50','Latency p50 (s)'),('latency_p95','Latency p95 (s)'),('input_tokens','평균 입력 토큰'),('output_tokens','평균 출력 토큰'),('tool_calls','평균 Tool Calls'),('escalation','Escalation'),('evidence_completeness','Evidence Completeness'),('provenance_completeness','Provenance Completeness')],rows14,
        ['지연·토큰·tool call은 18개 주 질의 원본 비용입니다. FR/FB는 별도 통제 fault 9개에서만 산출하므로 같은 모집단의 단일 비용효율 점수로 합치지 않습니다.','B4/H의 공유 review 비용을 서로 독립적인 모델 호출 비용으로 합산하지 않습니다.','근거 존재나 원본 파일 SHA 무결성을 근거 완전성·답변 provenance 완전성으로 대체하지 않습니다.'],source_refs)
    return dict(schema_version='paper_tables_v1',run_id=selected_run_id,tables=dict(table10=t10,table11=t11,table12=t12,table13=t13,table14=t14),sources=reader.sources,errors=reader.errors,source_only=True,models_called=False,research_modified=False,
                development_spatial=load_rq3_development(reader.root),completion_gate=summary.get('completion_gate',{}),execution_identity=manifest.get('execution_identity',{}))
