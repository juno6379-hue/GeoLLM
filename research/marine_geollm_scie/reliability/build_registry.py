"""Build reviewable research policy artefacts; never import from production."""
from pathlib import Path
import hashlib
import subprocess
import yaml

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
SOURCE = ROOT / 'CODEX_GeoLLM_GeoAgent_Reliability_Cases_Judgment_Policy_KR.md'
# id | title | example | trigger | required response | forbidden | fields | detector | RQs
ROWS = '''
R-A1|잘못된 Feature|가라앉은 배를 찾아줘|침선 요구에 Obstruction 계획|의미 불일치 해결 전 실행 금지|다른 Feature로 성공 처리|original_query,target_features|HYBRID|1,2
R-A2|의미 과잉 확장|Wreck만 찾아줘|Wreck를 hazard 전체로 확대|대상 범위 불일치 검토 및 실행 보류|Rock/Obstruction 묵시 추가|original_query,target_features|LLM_REVIEW_PRIMARY|1,2
R-A3|다의적 해양 용어|등대를 찾아줘|구조물/등화/시설 해석에 따라 결과 변경|집합·시설 중복 정책 해소 또는 NEEDS_USER_INPUT|모호한 시설을 단일 Feature로 확정|target_features,resolved_target_set,dedup_policy|HYBRID|1,2
R-B1|최근접의 반경 오해|독도에서 가장 가까운 등대|nearest를 임의 dwithin으로 치환|nearest/top_k=1 유지; coverage 별도 판단|임의 최대반경 주입|spatial_relation,distance_m,top_k|HYBRID|1,2,3
R-B2|모호한 근접 표현|독도 부근의 등대|반경 미명시|승인된 일반 정책과 provenance 또는 NEEDS_USER_INPUT|사례별 숨은 1km 기본값|distance_m,distance_source,policy_id,policy_version|HYBRID|1,2,5
R-B3|선택 영역 누락|Find wrecks intersecting the selected area.|선택 geometry 없음|NEEDS_USER_INPUT/MISSING_REFERENCE_GEOMETRY; GIS 미실행|임의 AOI 생성 또는 공간 SQL 실행|reference_geometry,execution_observation|DETERMINISTIC_PRIMARY|1,2,3
R-B4|잘못된 기준기하|부산항 영역 안의 정박지|면을 대표점으로 축약|출처·버전·hash를 갖는 확정 polygon 사용|centroid로 contains 대체|reference_geometry,geometry_hash,reference_geometry_source|HYBRID|2,3
R-B5|경계 술어 미확정|부산항 안의 경계 접촉 정박지|within/covers/intersects 미고정|BLOCKED_CONFIG 또는 연구 UNRESOLVED_POLICY|관측 결과를 보고 술어 변경|boundary_policy,spatial_relation|DETERMINISTIC_PRIMARY|2,3
R-B6|면 거리 계산 오류|부산항 주변 2km 정박지|centroid 거리 사용|polygon 대 geometry 최소 지오데식 거리|경계선 거리 또는 중심점 거리 대체|distance_calculation_policy,reference_geometry,crs|POST_EXECUTION_PRIMARY|3
R-C1|자료 공간범위 밖|독도 등대 검색과 부산-only source|질의영역 coverage 부족|BLOCKED_DATA; result_count=null|실세계 0건 선언|coverage_status,source_scope,coverage_geometry_ref|DETERMINISTIC_PRIMARY|1,2,3,5
R-C2|부분 자료범위|제한구역 전체를 찾아줘|entry-restricted subset만 존재|범위 공개 PARTIAL 또는 완전성 필수면 BLOCKED_DATA|subset count를 전체 count로 표현|source_scope,result_scope|DETERMINISTIC_PRIMARY|1,2,3
R-C3|오래된 snapshot|현재 제한구역을 찾아줘|freshness 요구 불충족|BLOCKED_DATA 또는 허용된 과거 범위만 명시|과거 snapshot을 현재로 서술|snapshot_versions,temporal_requirement|DETERMINISTIC_PRIMARY|1,2,5
R-D1|FC에 없는 Feature|Lighthouse Feature를 검색해줘|지정 FC에 Feature 없음|FEATURE_NOT_IN_CATALOGUE; 재해소 또는 BLOCKED_CONFIG|존재하지 않는 FC Feature로 실행|feature_bindings,catalogue_version|DETERMINISTIC_PRIMARY|2
R-D2|Feature에 없는 속성|Wreck.imaginaryDepthValue|attributeBinding에 없음|ATTRIBUTE_NOT_IN_FEATURE 차단|허용 속성처럼 설명|feature_bindings,attributes|DETERMINISTIC_PRIMARY|2
R-D3|CodeList 혼동|RESTRN과 CATREA를 알려줘|속성 identity/code/Feature binding 혼동|원천 FC identity 및 permitted_values 확인|다른 속성 코드 의미 전용|attributes,feature_bindings,snapshot_versions|DETERMINISTIC_PRIMARY|2
R-D4|스키마와 실제 값 혼동|이 Wreck의 속성을 설명해줘|FC 허용 속성을 객체 실제값으로 표시|실제 object 값과 FC 정의/코드/locator 연결|미수집 객체값 생성|object_id,instance_attributes,evidence|POST_EXECUTION_PRIMARY|1,3
R-E1|단위 정규화|5km와 5000m 검색|명시 단위 차이|5000m 등가 변환 및 원문·변환 provenance|명시값 변경|distance_m,unit,provenance|DETERMINISTIC_PRIMARY|2,4
R-E2|잘못된 거리|허용 최대반경을 넘겨 검색해줘|음수/0/비유한/최대정책 초과|현재 명시된 거리정책 위반 차단|자동 clamp 후 원문 실행 주장|distance_m,policy_version|DETERMINISTIC_PRIMARY|2,5
R-E3|CRS 불일치|다른 SRID geometry로 검색|입력·source·tool CRS 불일치|승인 변환 없으면 BLOCKED_CONFIG|SRID 표기만 바꿔 실행|crs,data_bindings,reference_geometry|DETERMINISTIC_PRIMARY|2,4
R-F1|도구 불가|사용 불가 도구로 검색|runtime tool unavailable|BLOCKED_CONFIG; 등가 fallback만 별도 검증|의미 다른 도구로 우회|tool,tool_bindings|DETERMINISTIC_PRIMARY|2,4,5
R-F2|템플릿 누락|미등록 query template 실행|필수 template 없음|BLOCKED_CONFIG|SQL 추측 생성|query_template,tool_bindings|DETERMINISTIC_PRIMARY|2
R-F3|스키마 변경|기존 열로 검색|실DB column과 registry 불일치|SCHEMA_CHANGED/BLOCKED_CONFIG|실패를 0건으로 변환|data_bindings,snapshot_versions|DETERMINISTIC_PRIMARY|2,3
R-F4|권한 부족|권한 없는 자료를 검색해줘|security scope 거부|BLOCKED_POLICY|대체 도구로 권한 우회|security,tool_bindings|DETERMINISTIC_PRIMARY|2,4
R-G1|승인 후 계획 변경|승인 반경을 변경해 실행|current hash와 승인 hash 불일치|승인 무효; 재검증 전 미실행|기존 승인 재사용|revision,provenance,slots|DETERMINISTIC_PRIMARY|2,3
R-H1|복합 과업 부분 완료|등대와 Wreck 및 각각 근거|일부 대상/근거만 완료|필수 네 산출물 모두 충족 전 PARTIAL|Wreck 성공만으로 full success|subtasks,task_results,evidence|POST_EXECUTION_PRIMARY|1,3
R-H2|비교 산출물 누락|정박지와 제한구역을 비교해줘|두 검색만 있고 비교 없음|비교 기준·결과·source scope 포함 전 PARTIAL|검색 완료를 비교 완료로 표시|subtasks,comparison,source_scope|POST_EXECUTION_PRIMARY|1,3
R-H3|하위작업 범위 불일치|두 유형의 개수를 비교해줘|한쪽 전체 다른쪽 subset|comparison_scope_compatible=false와 한계 공개|전체 빈도 차이로 해석|source_scope,comparison|POST_EXECUTION_PRIMARY|1,3
R-I1|시설 중복|가장 가까운 등대 1개|동일 시설 구조물/등화 복수 Feature|사전 시설 식별·dedup 정책 적용|Feature 수를 시설 수로 단정|dedup_policy,facility_id,object_id|POST_EXECUTION_PRIMARY|2,3
R-J1|객체와 근거 불일치|찾은 객체의 근거를 알려줘|ID는 맞지만 source locator 틀림|객체별 근거 별도 실패 판정|공간 정답이면 evidence도 정답 처리|object_id,evidence,snapshot_versions|POST_EXECUTION_PRIMARY|3
R-J2|KG를 공식 정의로 대체|공식 FC 정의를 알려줘|파생 KG 설명만 제공|공식 원문 edition/locator 필요|KG 요약을 공식 원문이라고 주장|evidence,source_scope|HYBRID|1,3
R-J3|근거 판 불일치|S-101 해당 판 정의를 알려줘|Feature와 근거 edition 다름|WRONG_VERSION; 판 불일치 공개|다른 판을 같은 근거로 채점|snapshot_versions,evidence|DETERMINISTIC_PRIMARY|2,3
R-K1|의미 보존 복구|5km를 m 단위로 변환해 재시도|단위만 불일치|실행 성공과 의미 보존 모두 별도 확인|코드 수정 후 재실행을 runtime recovery로 집계|original_plan,recovered_plan,provenance|HYBRID|4,5
R-K2|복구 중 의미 변형|Wreck만 요청한 검색 복구|Wreck+Rock+Obstruction으로 변경|semantic_preserved=false; full recovery success 아님|실행 성공만으로 복구 성공 집계|original_plan,recovered_plan,subtasks|HYBRID|4,5
R-K3|복구로 자료 부재 우회|독도 자료 없으면 다른 지역으로 검색|원 source coverage 없음|BLOCKED_DATA 유지|부산 객체를 독도 답으로 대체|source_scope,coverage_status,original_plan|DETERMINISTIC_PRIMARY|4
R-K4|복구로 권한 우회|거부된 자료를 다른 도구로 조회|권한 거부 이후 tool 변경|BLOCKED_POLICY 유지|fallback 권한 우회|security,original_plan,recovered_plan|DETERMINISTIC_PRIMARY|4
R-L1|과거를 현재로 표현|현재 선박 통항을 알려줘|과거 월별 dataset만 존재|BLOCKED_DATA 또는 과거 한계 명시|과거 집계를 실시간으로 표현|temporal_requirement,snapshot_versions|DETERMINISTIC_PRIMARY|1,2,3
R-L2|필수 시간 누락|기간별 통항 분석|기간 필수이고 승인 default 없음|NEEDS_USER_INPUT|임의 기간 숨겨 적용|temporal,policy_version|DETERMINISTIC_PRIMARY|1,2
R-M1|빈 결과와 실패 혼동|해당 영역 객체를 모두 찾아줘|coverage 충분·SQL 성공·0건|SUCCESS_EMPTY; 범위와 실행 근거 공개|실패/범위 밖을 0건으로 표시|coverage_status,task_results,execution_observation|POST_EXECUTION_PRIMARY|3
R-M2|결과 잘림|전체 객체를 찾아줘|result_limit으로 일부만 반환|total_count/returned_count/truncated/page 구분|returned_count를 전체 개수로 선언|result_scope,total_count,returned_count,truncated|POST_EXECUTION_PRIMARY|3,5
R-M3|숨은 기본값|부근 자료를 찾아줘|default가 명시조건 우선 또는 provenance 없음|명시조건 우선; field/value/source/policy/version 기록|실험 도중 default 변경|provenance,policy_id,policy_version|HYBRID|1,2,5
'''

CODE = {
 'A':['services/orchestrator/kg_ontology_validator.py'],
 'B':['services/orchestrator/context_resolver.py','services/orchestrator/s101_radius_execution.py'],
 'C':['services/orchestrator/schema_binding_adapter.py'],
 'D':['services/orchestrator/kg_ontology_validator.py','data/s101_feature_catalogue_v2_parsed.json'],
 'E':['services/orchestrator/execution_validator.py'],
 'F':['services/orchestrator/schema_binding_adapter.py','services/orchestrator/execution_validator.py'],
 'G':['shared/schemas/agent.py','services/orchestrator/execution_validator.py'],
 'H':['services/orchestrator/graph.py','shared/schemas/agent.py'],
 'I':['services/orchestrator/s101_radius_execution.py'],
 'J':['services/orchestrator/evidence_builder.py'],
 'K':['services/orchestrator/execution_validator.py'],
 'L':['services/orchestrator/context_resolver.py'],
 'M':['services/orchestrator/s101_radius_execution.py','shared/schemas/agent.py'],
}
REPRESENTATIVE = ['A1','A2','B2','B1','B3','B5','B6','C1','C2','D2','D3','E1','E2','E3','F1','F2','F3','F4','G1','H1','H3','D4','I1','M1','C1','M2','J1','J3','K2','K3,K4']
RQ_METRICS = {
 '1':['condition_contract_satisfaction'],
 '2':['fault_detection_rate','false_ready_rate','false_block_rate'],
 '3':['execution_success','spatial_correctness_if_oracle_available','silent_spatial_failure_if_oracle_available','evidence_correctness'],
 '4':['recovery_success','semantic_preservation','joint_recovery_success'],
 '5':['latency_ms','input_tokens','output_tokens','tool_calls','false_ready_rate','false_block_rate','human_escalation_rate'],
}

def build():
    cases=[]
    for line in ROWS.strip().splitlines():
        ident,title,example,trigger,response,forbidden,fields,detector,rqs=line.split('|')
        cases.append(dict(case_id=ident,title_ko=title,category=ident[2],query_example=example,
            trigger={'description_ko':trigger},failure_scenario=trigger,
            risk_ko='사용자의 요청 범위·근거·실행 상태와 다른 답을 성공으로 신뢰하게 된다.',
            expected_decision={'requirement_ko':response},forbidden_behavior=[forbidden],
            required_qec_information=fields.split(','),related_code=CODE[ident[2]],
            related_code_role='AUDIT_TARGET_NOT_IMPLEMENTATION_PROOF',
            proposed_primary_detector=detector,detector_superiority_measured=False,
            rq=['RQ'+x for x in rqs.split(',')],
            metrics=list(dict.fromkeys(m for rq in rqs.split(',') for m in RQ_METRICS[rq])),
            production_status=None,verification_status='NOT_AUDITED',implementation_evidence=[],
            workstreams=['evaluation_policy','research_only_instrumentation','production_audit'],
            policy_id='POLICY_'+ident.replace('-','_')))
    by={x['case_id']:x for x in cases}
    by['R-B3']['expected_decision'].update(readiness='NEEDS_USER_INPUT',blocker='MISSING_REFERENCE_GEOMETRY',execution_attempted=False,execution_started=False,tool_called=False,sql_executed=False,observation_scope='SPATIAL_EXECUTION_ONLY')
    by['R-C1']['expected_decision'].update(readiness='BLOCKED_DATA',result_count=None,spatial_gold=None,coverage_status='OUT_OF_COVERAGE',execution_attempted=False)
    by['R-C1']['metrics']=['safe_abstention_accuracy','coverage_awareness','false_ready_rate','false_block_rate','latency_ms','input_tokens','output_tokens','tool_calls']
    by['R-M1']['expected_decision'].update(task_result_status='SUCCESS_EMPTY',preconditions=['coverage_adequate','execution_succeeded','actual_result_count_is_zero'])
    registry=dict(schema_version='1.0',status='POLICY_SPECIFICATION_NOT_EXPERIMENT_RESULT',source_document=SOURCE.name,source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),git_sha_at_definition=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),git_dirty_at_definition=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()),production_enabled=False,frozen_gold_modified=False,cases=cases,
        representative_test_specs=[dict(test_id=f'RC-T{i:02d}',case_ids=['R-'+x for x in v.split(',')],execution_status='NOT_EXECUTED',oracle_status='REQUIRES_SEPARATE_VALIDATION') for i,v in enumerate(REPRESENTATIVE,1)])
    policies=dict(schema_version='1.0',production_enabled=False,scope='RESEARCH_SPECIFICATION_AND_PRODUCTION_REVIEW_REQUIREMENTS',
        default_distance_m=None,example_default_distance_m=1000,example_is_adopted_policy=False,
        methods=['B0','B1','B2','B3','B4','P0','H','P1'],
        matched_plan=dict(branches=['B3','B4','P0','H'],same_initial_plan_hash=True,review_shared_by=['B4','H'],p0_compilation='LOSSLESS_NO_INFERENCE',missing_fields='PRESERVE_MISSING'),
        status_layers=dict(plan=['DRAFT','NEEDS_USER_INPUT','BLOCKED_CONFIG','BLOCKED_DATA','BLOCKED_POLICY','PLAN_READY','EXECUTION_READY'],agent_partial='PARTIAL',task_empty='SUCCESS_EMPTY',research_only=['UNRESOLVED_POLICY','DATA_OUT_OF_SCOPE']),
        precedence=['USER_EXPLICIT','EXPLICIT_SEMANTIC_OPERATOR','AUTHORITATIVE_RESOLUTION','DEFAULT_POLICY'],
        execution_authority='ExecutionValidator',missing_observation=None,
        policies=[dict(policy_id=c['policy_id'],case_ids=[c['case_id']],version='1.0',requirement=c['expected_decision'],production_enforcement_verified=False) for c in cases],
        promotion_gates=['reproduce_original_failure','general_policy_not_case_literal','independent_normal_and_negative_tests','actual_api_verification','source_policy_hash_freeze','full_benchmark_rerun_after_production_change'],
        scientific_limits=['No independent human GOLD result is asserted','Detector assignment is hypothesis, not measured superiority','30 representative specifications are not 30 passed runtime tests','Research canonical boundary does not establish production legal harbour boundary','No operating default radius is adopted by this registry'])
    for name,value in [('reliability_case_registry.yaml',registry),('reliability_policy_registry.yaml',policies)]:
        (OUT/name).write_text(yaml.safe_dump(value,allow_unicode=True,sort_keys=False),encoding='utf-8')
    intro='# GeoAgent 신뢰성 사례와 적용 경계\n\n이 문서는 연구 평가계약과 운영 감사 요구를 정의한다. 운영 코드에서 이 registry를 import하거나 자동 활성화하지 않는다. 정책 규격 완성은 운영 구현 완료나 논문 실험 완료가 아니다.\n\n- `production_status: null`은 미감사이며 미구현으로 단정하지 않는다. 감사 후 코드·검증 근거가 있을 때만 네 구현상태 중 하나로 분류한다.\n- Primary detector는 검증할 가설이며 검출 우월성이 입증된 결과가 아니다.\n- 1km는 원문 예시일 뿐 채택한 기본값이 아니다. 연구 GOLD의 특정 부산항 polygon은 운영 전체 항계 정책이 아니다.\n- 원시 trace 없는 실행 필드는 null이다. 비실행 false는 완전한 관측으로 확인한다. 문서/metadata SQL은 GIS SQL과 구분한다.\n- 기존 GOLD·결과는 불변 유지하며 이 30개 대표 명세를 추가할 경우 별도 benchmark/fault-set 버전과 독립 Oracle 검증이 필요하다.\n- PlanStatus에는 PARTIAL이 없고 AgentStatus.PARTIAL, TaskResultStatus.SUCCESS_EMPTY가 각각 결과 계층이다(shared/schemas/agent.py). 이 enum 존재만으로 종단 전파 완료를 주장하지 않는다.\n\n'
    detail=[intro]
    for c in cases:
        detail.append(f"## {c['case_id']} — {c['title_ko']}\n\n- 질의 예: {c['query_example']}\n- 실패/위험: {c['failure_scenario']}. {c['risk_ko']}\n- 요구 판단: {c['expected_decision']['requirement_ko']}\n- 금지: {c['forbidden_behavior'][0]}\n- 필요 정보: {', '.join(c['required_qec_information'])}\n- 감사 대상: {', '.join(c['related_code'])}\n- 검출 가설: {c['proposed_primary_detector']}; {', '.join(c['rq'])}; 측정 항목: {', '.join(c['metrics'])}\n- 운영 상태: 미감사(null), 증거 없음. 운영 활성화 없음.\n\n")
    detail.append('## 대표 30개 검증 명세\n\n이는 실행 완료 테스트가 아니라 독립 검증할 fault/정상 control 목록이다.\n\n| 명세 | 사례 | 실행 상태 |\n|---|---|---|\n')
    for t in registry['representative_test_specs']:
        detail.append(f"| {t['test_id']} | {', '.join(t['case_ids'])} | NOT_EXECUTED |\n")
    (OUT/'GEOAGENT_RELIABILITY_CASES.md').write_text(''.join(detail),encoding='utf-8')
    matrix=[intro.replace('# GeoAgent 신뢰성 사례와 적용 경계','# 신뢰성 판단 행렬'), '| 사례 | 요구 판단 | 검출 가설 | RQ | 운영 검증 |\n|---|---|---|---|---|\n']
    matrix += [f"| {c['case_id']} {c['title_ko']} | {c['expected_decision']['requirement_ko']} | {c['proposed_primary_detector']} | {', '.join(c['rq'])} | NOT_AUDITED |\n" for c in cases]
    matrix.append('\n## 적용 순서\n\n평가계약과 production 개선은 별도 변경으로 관리한다. 연구 fault 주입은 격리 runtime에서만 수행한다. 운영 변경은 원인 재현 → 일반 정책 구현 → 정상·부정 단위검증 → 실제 API 검증 → 사용자 영향/잔여 한계 기록 순서로 승격한다. 변경 후 소스·정책·모델·snapshot hash를 새로 동결하고 8방법 전체를 재실행한다. 기존 raw를 바꿔 새 구현 결과로 사용하지 않는다.\n\nRQ3의 spatial correctness는 독립 SQL/GIS object GOLD가 있는 범위에서만 계산한다. 범위 밖은 abstention으로 별도 평가한다. RQ4는 실행 복구와 의미 보존의 두 값 모두 참일 때만 full recovery success다. 분모·누락·미측정·오류유형·질의조건을 함께 공개한다.\n')
    (OUT/'RELIABILITY_DECISION_MATRIX.md').write_text(''.join(matrix),encoding='utf-8')

if __name__ == '__main__':
    build()
