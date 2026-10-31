# GeoAgent 신뢰성 사례와 적용 경계

이 문서는 연구 평가계약과 운영 감사 요구를 정의한다. 운영 코드에서 이 registry를 import하거나 자동 활성화하지 않는다. 정책 규격 완성은 운영 구현 완료나 논문 실험 완료가 아니다.

- `production_status: null`은 미감사이며 미구현으로 단정하지 않는다. 감사 후 코드·검증 근거가 있을 때만 네 구현상태 중 하나로 분류한다.
- Primary detector는 검증할 가설이며 검출 우월성이 입증된 결과가 아니다.
- 1km는 원문 예시일 뿐 채택한 기본값이 아니다. 연구 GOLD의 특정 부산항 polygon은 운영 전체 항계 정책이 아니다.
- 원시 trace 없는 실행 필드는 null이다. 비실행 false는 완전한 관측으로 확인한다. 문서/metadata SQL은 GIS SQL과 구분한다.
- 기존 GOLD·결과는 불변 유지하며 이 30개 대표 명세를 추가할 경우 별도 benchmark/fault-set 버전과 독립 Oracle 검증이 필요하다.
- PlanStatus에는 PARTIAL이 없고 AgentStatus.PARTIAL, TaskResultStatus.SUCCESS_EMPTY가 각각 결과 계층이다(shared/schemas/agent.py). 이 enum 존재만으로 종단 전파 완료를 주장하지 않는다.

## R-A1 — 잘못된 Feature

- 질의 예: 가라앉은 배를 찾아줘
- 실패/위험: 침선 요구에 Obstruction 계획. 사용자의 요청 범위·근거·실행 상태와 다른 답을 성공으로 신뢰하게 된다.
- 요구 판단: 의미 불일치 해결 전 실행 금지
- 금지: 다른 Feature로 성공 처리
- 필요 정보: original_query, target_features
- 감사 대상: services/orchestrator/kg_ontology_validator.py
- 검출 가설: HYBRID; RQ1, RQ2; 측정 항목: condition_contract_satisfaction, fault_detection_rate, false_ready_rate, false_block_rate
- 운영 상태: 미감사(null), 증거 없음. 운영 활성화 없음.

## R-A2 — 의미 과잉 확장

- 질의 예: Wreck만 찾아줘
- 실패/위험: Wreck를 hazard 전체로 확대. 사용자의 요청 범위·근거·실행 상태와 다른 답을 성공으로 신뢰하게 된다.
- 요구 판단: 대상 범위 불일치 검토 및 실행 보류
- 금지: Rock/Obstruction 묵시 추가
- 필요 정보: original_query, target_features
- 감사 대상: services/orchestrator/kg_ontology_validator.py
- 검출 가설: LLM_REVIEW_PRIMARY; RQ1, RQ2; 측정 항목: condition_contract_satisfaction, fault_detection_rate, false_ready_rate, false_block_rate
- 운영 상태: 미감사(null), 증거 없음. 운영 활성화 없음.

## R-A3 — 다의적 해양 용어

- 질의 예: 등대를 찾아줘
- 실패/위험: 구조물/등화/시설 해석에 따라 결과 변경. 사용자의 요청 범위·근거·실행 상태와 다른 답을 성공으로 신뢰하게 된다.
- 요구 판단: 집합·시설 중복 정책 해소 또는 NEEDS_USER_INPUT
- 금지: 모호한 시설을 단일 Feature로 확정
- 필요 정보: target_features, resolved_target_set, dedup_policy
- 감사 대상: services/orchestrator/kg_ontology_validator.py
- 검출 가설: HYBRID; RQ1, RQ2; 측정 항목: condition_contract_satisfaction, fault_detection_rate, false_ready_rate, false_block_rate
- 운영 상태: 미감사(null), 증거 없음. 운영 활성화 없음.

## R-B1 — 최근접의 반경 오해

- 질의 예: 독도에서 가장 가까운 등대
- 실패/위험: nearest를 임의 dwithin으로 치환. 사용자의 요청 범위·근거·실행 상태와 다른 답을 성공으로 신뢰하게 된다.
- 요구 판단: nearest/top_k=1 유지; coverage 별도 판단
- 금지: 임의 최대반경 주입
- 필요 정보: spatial_relation, distance_m, top_k
- 감사 대상: services/orchestrator/context_resolver.py, services/orchestrator/s101_radius_execution.py
- 검출 가설: HYBRID; RQ1, RQ2, RQ3; 측정 항목: condition_contract_satisfaction, fault_detection_rate, false_ready_rate, false_block_rate, execution_success, spatial_correctness_if_oracle_available, silent_spatial_failure_if_oracle_available, evidence_correctness
- 운영 상태: 미감사(null), 증거 없음. 운영 활성화 없음.

## R-B2 — 모호한 근접 표현

- 질의 예: 독도 부근의 등대
- 실패/위험: 반경 미명시. 사용자의 요청 범위·근거·실행 상태와 다른 답을 성공으로 신뢰하게 된다.
- 요구 판단: 승인된 일반 정책과 provenance 또는 NEEDS_USER_INPUT
- 금지: 사례별 숨은 1km 기본값
- 필요 정보: distance_m, distance_source, policy_id, policy_version
- 감사 대상: services/orchestrator/context_resolver.py, services/orchestrator/s101_radius_execution.py
- 검출 가설: HYBRID; RQ1, RQ2, RQ5; 측정 항목: condition_contract_satisfaction, fault_detection_rate, false_ready_rate, false_block_rate, latency_ms, input_tokens, output_tokens, tool_calls, human_escalation_rate
- 운영 상태: 미감사(null), 증거 없음. 운영 활성화 없음.

## R-B3 — 선택 영역 누락

- 질의 예: Find wrecks intersecting the selected area.
- 실패/위험: 선택 geometry 없음. 사용자의 요청 범위·근거·실행 상태와 다른 답을 성공으로 신뢰하게 된다.
- 요구 판단: NEEDS_USER_INPUT/MISSING_REFERENCE_GEOMETRY; GIS 미실행
- 금지: 임의 AOI 생성 또는 공간 SQL 실행
- 필요 정보: reference_geometry, execution_observation
- 감사 대상: services/orchestrator/context_resolver.py, services/orchestrator/s101_radius_execution.py
- 검출 가설: DETERMINISTIC_PRIMARY; RQ1, RQ2, RQ3; 측정 항목: condition_contract_satisfaction, fault_detection_rate, false_ready_rate, false_block_rate, execution_success, spatial_correctness_if_oracle_available, silent_spatial_failure_if_oracle_available, evidence_correctness
- 운영 상태: 미감사(null), 증거 없음. 운영 활성화 없음.

## R-B4 — 잘못된 기준기하

- 질의 예: 부산항 영역 안의 정박지
- 실패/위험: 면을 대표점으로 축약. 사용자의 요청 범위·근거·실행 상태와 다른 답을 성공으로 신뢰하게 된다.
- 요구 판단: 출처·버전·hash를 갖는 확정 polygon 사용
- 금지: centroid로 contains 대체
- 필요 정보: reference_geometry, geometry_hash, reference_geometry_source
- 감사 대상: services/orchestrator/context_resolver.py, services/orchestrator/s101_radius_execution.py
- 검출 가설: HYBRID; RQ2, RQ3; 측정 항목: fault_detection_rate, false_ready_rate, false_block_rate, execution_success, spatial_correctness_if_oracle_available, silent_spatial_failure_if_oracle_available, evidence_correctness
- 운영 상태: 미감사(null), 증거 없음. 운영 활성화 없음.

## R-B5 — 경계 술어 미확정

- 질의 예: 부산항 안의 경계 접촉 정박지
- 실패/위험: within/covers/intersects 미고정. 사용자의 요청 범위·근거·실행 상태와 다른 답을 성공으로 신뢰하게 된다.
- 요구 판단: BLOCKED_CONFIG 또는 연구 UNRESOLVED_POLICY
- 금지: 관측 결과를 보고 술어 변경
- 필요 정보: boundary_policy, spatial_relation
- 감사 대상: services/orchestrator/context_resolver.py, services/orchestrator/s101_radius_execution.py
- 검출 가설: DETERMINISTIC_PRIMARY; RQ2, RQ3; 측정 항목: fault_detection_rate, false_ready_rate, false_block_rate, execution_success, spatial_correctness_if_oracle_available, silent_spatial_failure_if_oracle_available, evidence_correctness
- 운영 상태: 미감사(null), 증거 없음. 운영 활성화 없음.

## R-B6 — 면 거리 계산 오류

- 질의 예: 부산항 주변 2km 정박지
- 실패/위험: centroid 거리 사용. 사용자의 요청 범위·근거·실행 상태와 다른 답을 성공으로 신뢰하게 된다.
- 요구 판단: polygon 대 geometry 최소 지오데식 거리
- 금지: 경계선 거리 또는 중심점 거리 대체
- 필요 정보: distance_calculation_policy, reference_geometry, crs
- 감사 대상: services/orchestrator/context_resolver.py, services/orchestrator/s101_radius_execution.py
- 검출 가설: POST_EXECUTION_PRIMARY; RQ3; 측정 항목: execution_success, spatial_correctness_if_oracle_available, silent_spatial_failure_if_oracle_available, evidence_correctness
- 운영 상태: 미감사(null), 증거 없음. 운영 활성화 없음.

## R-C1 — 자료 공간범위 밖

- 질의 예: 독도 등대 검색과 부산-only source
- 실패/위험: 질의영역 coverage 부족. 사용자의 요청 범위·근거·실행 상태와 다른 답을 성공으로 신뢰하게 된다.
- 요구 판단: BLOCKED_DATA; result_count=null
- 금지: 실세계 0건 선언
- 필요 정보: coverage_status, source_scope, coverage_geometry_ref
- 감사 대상: services/orchestrator/schema_binding_adapter.py
- 검출 가설: DETERMINISTIC_PRIMARY; RQ1, RQ2, RQ3, RQ5; 측정 항목: safe_abstention_accuracy, coverage_awareness, false_ready_rate, false_block_rate, latency_ms, input_tokens, output_tokens, tool_calls
- 운영 상태: 미감사(null), 증거 없음. 운영 활성화 없음.

## R-C2 — 부분 자료범위

- 질의 예: 제한구역 전체를 찾아줘
- 실패/위험: entry-restricted subset만 존재. 사용자의 요청 범위·근거·실행 상태와 다른 답을 성공으로 신뢰하게 된다.
- 요구 판단: 범위 공개 PARTIAL 또는 완전성 필수면 BLOCKED_DATA
- 금지: subset count를 전체 count로 표현
- 필요 정보: source_scope, result_scope
- 감사 대상: services/orchestrator/schema_binding_adapter.py
- 검출 가설: DETERMINISTIC_PRIMARY; RQ1, RQ2, RQ3; 측정 항목: condition_contract_satisfaction, fault_detection_rate, false_ready_rate, false_block_rate, execution_success, spatial_correctness_if_oracle_available, silent_spatial_failure_if_oracle_available, evidence_correctness
- 운영 상태: 미감사(null), 증거 없음. 운영 활성화 없음.

## R-C3 — 오래된 snapshot

- 질의 예: 현재 제한구역을 찾아줘
- 실패/위험: freshness 요구 불충족. 사용자의 요청 범위·근거·실행 상태와 다른 답을 성공으로 신뢰하게 된다.
- 요구 판단: BLOCKED_DATA 또는 허용된 과거 범위만 명시
- 금지: 과거 snapshot을 현재로 서술
- 필요 정보: snapshot_versions, temporal_requirement
- 감사 대상: services/orchestrator/schema_binding_adapter.py
- 검출 가설: DETERMINISTIC_PRIMARY; RQ1, RQ2, RQ5; 측정 항목: condition_contract_satisfaction, fault_detection_rate, false_ready_rate, false_block_rate, latency_ms, input_tokens, output_tokens, tool_calls, human_escalation_rate
- 운영 상태: 미감사(null), 증거 없음. 운영 활성화 없음.

## R-D1 — FC에 없는 Feature

- 질의 예: Lighthouse Feature를 검색해줘
- 실패/위험: 지정 FC에 Feature 없음. 사용자의 요청 범위·근거·실행 상태와 다른 답을 성공으로 신뢰하게 된다.
- 요구 판단: FEATURE_NOT_IN_CATALOGUE; 재해소 또는 BLOCKED_CONFIG
- 금지: 존재하지 않는 FC Feature로 실행
- 필요 정보: feature_bindings, catalogue_version
- 감사 대상: services/orchestrator/kg_ontology_validator.py, data/s101_feature_catalogue_v2_parsed.json
- 검출 가설: DETERMINISTIC_PRIMARY; RQ2; 측정 항목: fault_detection_rate, false_ready_rate, false_block_rate
- 운영 상태: 미감사(null), 증거 없음. 운영 활성화 없음.

## R-D2 — Feature에 없는 속성

- 질의 예: Wreck.imaginaryDepthValue
- 실패/위험: attributeBinding에 없음. 사용자의 요청 범위·근거·실행 상태와 다른 답을 성공으로 신뢰하게 된다.
- 요구 판단: ATTRIBUTE_NOT_IN_FEATURE 차단
- 금지: 허용 속성처럼 설명
- 필요 정보: feature_bindings, attributes
- 감사 대상: services/orchestrator/kg_ontology_validator.py, data/s101_feature_catalogue_v2_parsed.json
- 검출 가설: DETERMINISTIC_PRIMARY; RQ2; 측정 항목: fault_detection_rate, false_ready_rate, false_block_rate
- 운영 상태: 미감사(null), 증거 없음. 운영 활성화 없음.

## R-D3 — CodeList 혼동

- 질의 예: RESTRN과 CATREA를 알려줘
- 실패/위험: 속성 identity/code/Feature binding 혼동. 사용자의 요청 범위·근거·실행 상태와 다른 답을 성공으로 신뢰하게 된다.
- 요구 판단: 원천 FC identity 및 permitted_values 확인
- 금지: 다른 속성 코드 의미 전용
- 필요 정보: attributes, feature_bindings, snapshot_versions
- 감사 대상: services/orchestrator/kg_ontology_validator.py, data/s101_feature_catalogue_v2_parsed.json
- 검출 가설: DETERMINISTIC_PRIMARY; RQ2; 측정 항목: fault_detection_rate, false_ready_rate, false_block_rate
- 운영 상태: 미감사(null), 증거 없음. 운영 활성화 없음.

## R-D4 — 스키마와 실제 값 혼동

- 질의 예: 이 Wreck의 속성을 설명해줘
- 실패/위험: FC 허용 속성을 객체 실제값으로 표시. 사용자의 요청 범위·근거·실행 상태와 다른 답을 성공으로 신뢰하게 된다.
- 요구 판단: 실제 object 값과 FC 정의/코드/locator 연결
- 금지: 미수집 객체값 생성
- 필요 정보: object_id, instance_attributes, evidence
- 감사 대상: services/orchestrator/kg_ontology_validator.py, data/s101_feature_catalogue_v2_parsed.json
- 검출 가설: POST_EXECUTION_PRIMARY; RQ1, RQ3; 측정 항목: condition_contract_satisfaction, execution_success, spatial_correctness_if_oracle_available, silent_spatial_failure_if_oracle_available, evidence_correctness
- 운영 상태: 미감사(null), 증거 없음. 운영 활성화 없음.

## R-E1 — 단위 정규화

- 질의 예: 5km와 5000m 검색
- 실패/위험: 명시 단위 차이. 사용자의 요청 범위·근거·실행 상태와 다른 답을 성공으로 신뢰하게 된다.
- 요구 판단: 5000m 등가 변환 및 원문·변환 provenance
- 금지: 명시값 변경
- 필요 정보: distance_m, unit, provenance
- 감사 대상: services/orchestrator/execution_validator.py
- 검출 가설: DETERMINISTIC_PRIMARY; RQ2, RQ4; 측정 항목: fault_detection_rate, false_ready_rate, false_block_rate, recovery_success, semantic_preservation, joint_recovery_success
- 운영 상태: 미감사(null), 증거 없음. 운영 활성화 없음.

## R-E2 — 잘못된 거리

- 질의 예: 허용 최대반경을 넘겨 검색해줘
- 실패/위험: 음수/0/비유한/최대정책 초과. 사용자의 요청 범위·근거·실행 상태와 다른 답을 성공으로 신뢰하게 된다.
- 요구 판단: 현재 명시된 거리정책 위반 차단
- 금지: 자동 clamp 후 원문 실행 주장
- 필요 정보: distance_m, policy_version
- 감사 대상: services/orchestrator/execution_validator.py
- 검출 가설: DETERMINISTIC_PRIMARY; RQ2, RQ5; 측정 항목: fault_detection_rate, false_ready_rate, false_block_rate, latency_ms, input_tokens, output_tokens, tool_calls, human_escalation_rate
- 운영 상태: 미감사(null), 증거 없음. 운영 활성화 없음.

## R-E3 — CRS 불일치

- 질의 예: 다른 SRID geometry로 검색
- 실패/위험: 입력·source·tool CRS 불일치. 사용자의 요청 범위·근거·실행 상태와 다른 답을 성공으로 신뢰하게 된다.
- 요구 판단: 승인 변환 없으면 BLOCKED_CONFIG
- 금지: SRID 표기만 바꿔 실행
- 필요 정보: crs, data_bindings, reference_geometry
- 감사 대상: services/orchestrator/execution_validator.py
- 검출 가설: DETERMINISTIC_PRIMARY; RQ2, RQ4; 측정 항목: fault_detection_rate, false_ready_rate, false_block_rate, recovery_success, semantic_preservation, joint_recovery_success
- 운영 상태: 미감사(null), 증거 없음. 운영 활성화 없음.

## R-F1 — 도구 불가

- 질의 예: 사용 불가 도구로 검색
- 실패/위험: runtime tool unavailable. 사용자의 요청 범위·근거·실행 상태와 다른 답을 성공으로 신뢰하게 된다.
- 요구 판단: BLOCKED_CONFIG; 등가 fallback만 별도 검증
- 금지: 의미 다른 도구로 우회
- 필요 정보: tool, tool_bindings
- 감사 대상: services/orchestrator/schema_binding_adapter.py, services/orchestrator/execution_validator.py
- 검출 가설: DETERMINISTIC_PRIMARY; RQ2, RQ4, RQ5; 측정 항목: fault_detection_rate, false_ready_rate, false_block_rate, recovery_success, semantic_preservation, joint_recovery_success, latency_ms, input_tokens, output_tokens, tool_calls, human_escalation_rate
- 운영 상태: 미감사(null), 증거 없음. 운영 활성화 없음.

## R-F2 — 템플릿 누락

- 질의 예: 미등록 query template 실행
- 실패/위험: 필수 template 없음. 사용자의 요청 범위·근거·실행 상태와 다른 답을 성공으로 신뢰하게 된다.
- 요구 판단: BLOCKED_CONFIG
- 금지: SQL 추측 생성
- 필요 정보: query_template, tool_bindings
- 감사 대상: services/orchestrator/schema_binding_adapter.py, services/orchestrator/execution_validator.py
- 검출 가설: DETERMINISTIC_PRIMARY; RQ2; 측정 항목: fault_detection_rate, false_ready_rate, false_block_rate
- 운영 상태: 미감사(null), 증거 없음. 운영 활성화 없음.

## R-F3 — 스키마 변경

- 질의 예: 기존 열로 검색
- 실패/위험: 실DB column과 registry 불일치. 사용자의 요청 범위·근거·실행 상태와 다른 답을 성공으로 신뢰하게 된다.
- 요구 판단: SCHEMA_CHANGED/BLOCKED_CONFIG
- 금지: 실패를 0건으로 변환
- 필요 정보: data_bindings, snapshot_versions
- 감사 대상: services/orchestrator/schema_binding_adapter.py, services/orchestrator/execution_validator.py
- 검출 가설: DETERMINISTIC_PRIMARY; RQ2, RQ3; 측정 항목: fault_detection_rate, false_ready_rate, false_block_rate, execution_success, spatial_correctness_if_oracle_available, silent_spatial_failure_if_oracle_available, evidence_correctness
- 운영 상태: 미감사(null), 증거 없음. 운영 활성화 없음.

## R-F4 — 권한 부족

- 질의 예: 권한 없는 자료를 검색해줘
- 실패/위험: security scope 거부. 사용자의 요청 범위·근거·실행 상태와 다른 답을 성공으로 신뢰하게 된다.
- 요구 판단: BLOCKED_POLICY
- 금지: 대체 도구로 권한 우회
- 필요 정보: security, tool_bindings
- 감사 대상: services/orchestrator/schema_binding_adapter.py, services/orchestrator/execution_validator.py
- 검출 가설: DETERMINISTIC_PRIMARY; RQ2, RQ4; 측정 항목: fault_detection_rate, false_ready_rate, false_block_rate, recovery_success, semantic_preservation, joint_recovery_success
- 운영 상태: 미감사(null), 증거 없음. 운영 활성화 없음.

## R-G1 — 승인 후 계획 변경

- 질의 예: 승인 반경을 변경해 실행
- 실패/위험: current hash와 승인 hash 불일치. 사용자의 요청 범위·근거·실행 상태와 다른 답을 성공으로 신뢰하게 된다.
- 요구 판단: 승인 무효; 재검증 전 미실행
- 금지: 기존 승인 재사용
- 필요 정보: revision, provenance, slots
- 감사 대상: shared/schemas/agent.py, services/orchestrator/execution_validator.py
- 검출 가설: DETERMINISTIC_PRIMARY; RQ2, RQ3; 측정 항목: fault_detection_rate, false_ready_rate, false_block_rate, execution_success, spatial_correctness_if_oracle_available, silent_spatial_failure_if_oracle_available, evidence_correctness
- 운영 상태: 미감사(null), 증거 없음. 운영 활성화 없음.

## R-H1 — 복합 과업 부분 완료

- 질의 예: 등대와 Wreck 및 각각 근거
- 실패/위험: 일부 대상/근거만 완료. 사용자의 요청 범위·근거·실행 상태와 다른 답을 성공으로 신뢰하게 된다.
- 요구 판단: 필수 네 산출물 모두 충족 전 PARTIAL
- 금지: Wreck 성공만으로 full success
- 필요 정보: subtasks, task_results, evidence
- 감사 대상: services/orchestrator/graph.py, shared/schemas/agent.py
- 검출 가설: POST_EXECUTION_PRIMARY; RQ1, RQ3; 측정 항목: condition_contract_satisfaction, execution_success, spatial_correctness_if_oracle_available, silent_spatial_failure_if_oracle_available, evidence_correctness
- 운영 상태: 미감사(null), 증거 없음. 운영 활성화 없음.

## R-H2 — 비교 산출물 누락

- 질의 예: 정박지와 제한구역을 비교해줘
- 실패/위험: 두 검색만 있고 비교 없음. 사용자의 요청 범위·근거·실행 상태와 다른 답을 성공으로 신뢰하게 된다.
- 요구 판단: 비교 기준·결과·source scope 포함 전 PARTIAL
- 금지: 검색 완료를 비교 완료로 표시
- 필요 정보: subtasks, comparison, source_scope
- 감사 대상: services/orchestrator/graph.py, shared/schemas/agent.py
- 검출 가설: POST_EXECUTION_PRIMARY; RQ1, RQ3; 측정 항목: condition_contract_satisfaction, execution_success, spatial_correctness_if_oracle_available, silent_spatial_failure_if_oracle_available, evidence_correctness
- 운영 상태: 미감사(null), 증거 없음. 운영 활성화 없음.

## R-H3 — 하위작업 범위 불일치

- 질의 예: 두 유형의 개수를 비교해줘
- 실패/위험: 한쪽 전체 다른쪽 subset. 사용자의 요청 범위·근거·실행 상태와 다른 답을 성공으로 신뢰하게 된다.
- 요구 판단: comparison_scope_compatible=false와 한계 공개
- 금지: 전체 빈도 차이로 해석
- 필요 정보: source_scope, comparison
- 감사 대상: services/orchestrator/graph.py, shared/schemas/agent.py
- 검출 가설: POST_EXECUTION_PRIMARY; RQ1, RQ3; 측정 항목: condition_contract_satisfaction, execution_success, spatial_correctness_if_oracle_available, silent_spatial_failure_if_oracle_available, evidence_correctness
- 운영 상태: 미감사(null), 증거 없음. 운영 활성화 없음.

## R-I1 — 시설 중복

- 질의 예: 가장 가까운 등대 1개
- 실패/위험: 동일 시설 구조물/등화 복수 Feature. 사용자의 요청 범위·근거·실행 상태와 다른 답을 성공으로 신뢰하게 된다.
- 요구 판단: 사전 시설 식별·dedup 정책 적용
- 금지: Feature 수를 시설 수로 단정
- 필요 정보: dedup_policy, facility_id, object_id
- 감사 대상: services/orchestrator/s101_radius_execution.py
- 검출 가설: POST_EXECUTION_PRIMARY; RQ2, RQ3; 측정 항목: fault_detection_rate, false_ready_rate, false_block_rate, execution_success, spatial_correctness_if_oracle_available, silent_spatial_failure_if_oracle_available, evidence_correctness
- 운영 상태: 미감사(null), 증거 없음. 운영 활성화 없음.

## R-J1 — 객체와 근거 불일치

- 질의 예: 찾은 객체의 근거를 알려줘
- 실패/위험: ID는 맞지만 source locator 틀림. 사용자의 요청 범위·근거·실행 상태와 다른 답을 성공으로 신뢰하게 된다.
- 요구 판단: 객체별 근거 별도 실패 판정
- 금지: 공간 정답이면 evidence도 정답 처리
- 필요 정보: object_id, evidence, snapshot_versions
- 감사 대상: services/orchestrator/evidence_builder.py
- 검출 가설: POST_EXECUTION_PRIMARY; RQ3; 측정 항목: execution_success, spatial_correctness_if_oracle_available, silent_spatial_failure_if_oracle_available, evidence_correctness
- 운영 상태: 미감사(null), 증거 없음. 운영 활성화 없음.

## R-J2 — KG를 공식 정의로 대체

- 질의 예: 공식 FC 정의를 알려줘
- 실패/위험: 파생 KG 설명만 제공. 사용자의 요청 범위·근거·실행 상태와 다른 답을 성공으로 신뢰하게 된다.
- 요구 판단: 공식 원문 edition/locator 필요
- 금지: KG 요약을 공식 원문이라고 주장
- 필요 정보: evidence, source_scope
- 감사 대상: services/orchestrator/evidence_builder.py
- 검출 가설: HYBRID; RQ1, RQ3; 측정 항목: condition_contract_satisfaction, execution_success, spatial_correctness_if_oracle_available, silent_spatial_failure_if_oracle_available, evidence_correctness
- 운영 상태: 미감사(null), 증거 없음. 운영 활성화 없음.

## R-J3 — 근거 판 불일치

- 질의 예: S-101 해당 판 정의를 알려줘
- 실패/위험: Feature와 근거 edition 다름. 사용자의 요청 범위·근거·실행 상태와 다른 답을 성공으로 신뢰하게 된다.
- 요구 판단: WRONG_VERSION; 판 불일치 공개
- 금지: 다른 판을 같은 근거로 채점
- 필요 정보: snapshot_versions, evidence
- 감사 대상: services/orchestrator/evidence_builder.py
- 검출 가설: DETERMINISTIC_PRIMARY; RQ2, RQ3; 측정 항목: fault_detection_rate, false_ready_rate, false_block_rate, execution_success, spatial_correctness_if_oracle_available, silent_spatial_failure_if_oracle_available, evidence_correctness
- 운영 상태: 미감사(null), 증거 없음. 운영 활성화 없음.

## R-K1 — 의미 보존 복구

- 질의 예: 5km를 m 단위로 변환해 재시도
- 실패/위험: 단위만 불일치. 사용자의 요청 범위·근거·실행 상태와 다른 답을 성공으로 신뢰하게 된다.
- 요구 판단: 실행 성공과 의미 보존 모두 별도 확인
- 금지: 코드 수정 후 재실행을 runtime recovery로 집계
- 필요 정보: original_plan, recovered_plan, provenance
- 감사 대상: services/orchestrator/execution_validator.py
- 검출 가설: HYBRID; RQ4, RQ5; 측정 항목: recovery_success, semantic_preservation, joint_recovery_success, latency_ms, input_tokens, output_tokens, tool_calls, false_ready_rate, false_block_rate, human_escalation_rate
- 운영 상태: 미감사(null), 증거 없음. 운영 활성화 없음.

## R-K2 — 복구 중 의미 변형

- 질의 예: Wreck만 요청한 검색 복구
- 실패/위험: Wreck+Rock+Obstruction으로 변경. 사용자의 요청 범위·근거·실행 상태와 다른 답을 성공으로 신뢰하게 된다.
- 요구 판단: semantic_preserved=false; full recovery success 아님
- 금지: 실행 성공만으로 복구 성공 집계
- 필요 정보: original_plan, recovered_plan, subtasks
- 감사 대상: services/orchestrator/execution_validator.py
- 검출 가설: HYBRID; RQ4, RQ5; 측정 항목: recovery_success, semantic_preservation, joint_recovery_success, latency_ms, input_tokens, output_tokens, tool_calls, false_ready_rate, false_block_rate, human_escalation_rate
- 운영 상태: 미감사(null), 증거 없음. 운영 활성화 없음.

## R-K3 — 복구로 자료 부재 우회

- 질의 예: 독도 자료 없으면 다른 지역으로 검색
- 실패/위험: 원 source coverage 없음. 사용자의 요청 범위·근거·실행 상태와 다른 답을 성공으로 신뢰하게 된다.
- 요구 판단: BLOCKED_DATA 유지
- 금지: 부산 객체를 독도 답으로 대체
- 필요 정보: source_scope, coverage_status, original_plan
- 감사 대상: services/orchestrator/execution_validator.py
- 검출 가설: DETERMINISTIC_PRIMARY; RQ4; 측정 항목: recovery_success, semantic_preservation, joint_recovery_success
- 운영 상태: 미감사(null), 증거 없음. 운영 활성화 없음.

## R-K4 — 복구로 권한 우회

- 질의 예: 거부된 자료를 다른 도구로 조회
- 실패/위험: 권한 거부 이후 tool 변경. 사용자의 요청 범위·근거·실행 상태와 다른 답을 성공으로 신뢰하게 된다.
- 요구 판단: BLOCKED_POLICY 유지
- 금지: fallback 권한 우회
- 필요 정보: security, original_plan, recovered_plan
- 감사 대상: services/orchestrator/execution_validator.py
- 검출 가설: DETERMINISTIC_PRIMARY; RQ4; 측정 항목: recovery_success, semantic_preservation, joint_recovery_success
- 운영 상태: 미감사(null), 증거 없음. 운영 활성화 없음.

## R-L1 — 과거를 현재로 표현

- 질의 예: 현재 선박 통항을 알려줘
- 실패/위험: 과거 월별 dataset만 존재. 사용자의 요청 범위·근거·실행 상태와 다른 답을 성공으로 신뢰하게 된다.
- 요구 판단: BLOCKED_DATA 또는 과거 한계 명시
- 금지: 과거 집계를 실시간으로 표현
- 필요 정보: temporal_requirement, snapshot_versions
- 감사 대상: services/orchestrator/context_resolver.py
- 검출 가설: DETERMINISTIC_PRIMARY; RQ1, RQ2, RQ3; 측정 항목: condition_contract_satisfaction, fault_detection_rate, false_ready_rate, false_block_rate, execution_success, spatial_correctness_if_oracle_available, silent_spatial_failure_if_oracle_available, evidence_correctness
- 운영 상태: 미감사(null), 증거 없음. 운영 활성화 없음.

## R-L2 — 필수 시간 누락

- 질의 예: 기간별 통항 분석
- 실패/위험: 기간 필수이고 승인 default 없음. 사용자의 요청 범위·근거·실행 상태와 다른 답을 성공으로 신뢰하게 된다.
- 요구 판단: NEEDS_USER_INPUT
- 금지: 임의 기간 숨겨 적용
- 필요 정보: temporal, policy_version
- 감사 대상: services/orchestrator/context_resolver.py
- 검출 가설: DETERMINISTIC_PRIMARY; RQ1, RQ2; 측정 항목: condition_contract_satisfaction, fault_detection_rate, false_ready_rate, false_block_rate
- 운영 상태: 미감사(null), 증거 없음. 운영 활성화 없음.

## R-M1 — 빈 결과와 실패 혼동

- 질의 예: 해당 영역 객체를 모두 찾아줘
- 실패/위험: coverage 충분·SQL 성공·0건. 사용자의 요청 범위·근거·실행 상태와 다른 답을 성공으로 신뢰하게 된다.
- 요구 판단: SUCCESS_EMPTY; 범위와 실행 근거 공개
- 금지: 실패/범위 밖을 0건으로 표시
- 필요 정보: coverage_status, task_results, execution_observation
- 감사 대상: services/orchestrator/s101_radius_execution.py, shared/schemas/agent.py
- 검출 가설: POST_EXECUTION_PRIMARY; RQ3; 측정 항목: execution_success, spatial_correctness_if_oracle_available, silent_spatial_failure_if_oracle_available, evidence_correctness
- 운영 상태: 미감사(null), 증거 없음. 운영 활성화 없음.

## R-M2 — 결과 잘림

- 질의 예: 전체 객체를 찾아줘
- 실패/위험: result_limit으로 일부만 반환. 사용자의 요청 범위·근거·실행 상태와 다른 답을 성공으로 신뢰하게 된다.
- 요구 판단: total_count/returned_count/truncated/page 구분
- 금지: returned_count를 전체 개수로 선언
- 필요 정보: result_scope, total_count, returned_count, truncated
- 감사 대상: services/orchestrator/s101_radius_execution.py, shared/schemas/agent.py
- 검출 가설: POST_EXECUTION_PRIMARY; RQ3, RQ5; 측정 항목: execution_success, spatial_correctness_if_oracle_available, silent_spatial_failure_if_oracle_available, evidence_correctness, latency_ms, input_tokens, output_tokens, tool_calls, false_ready_rate, false_block_rate, human_escalation_rate
- 운영 상태: 미감사(null), 증거 없음. 운영 활성화 없음.

## R-M3 — 숨은 기본값

- 질의 예: 부근 자료를 찾아줘
- 실패/위험: default가 명시조건 우선 또는 provenance 없음. 사용자의 요청 범위·근거·실행 상태와 다른 답을 성공으로 신뢰하게 된다.
- 요구 판단: 명시조건 우선; field/value/source/policy/version 기록
- 금지: 실험 도중 default 변경
- 필요 정보: provenance, policy_id, policy_version
- 감사 대상: services/orchestrator/s101_radius_execution.py, shared/schemas/agent.py
- 검출 가설: HYBRID; RQ1, RQ2, RQ5; 측정 항목: condition_contract_satisfaction, fault_detection_rate, false_ready_rate, false_block_rate, latency_ms, input_tokens, output_tokens, tool_calls, human_escalation_rate
- 운영 상태: 미감사(null), 증거 없음. 운영 활성화 없음.

## 대표 30개 검증 명세

이는 실행 완료 테스트가 아니라 독립 검증할 fault/정상 control 목록이다.

| 명세 | 사례 | 실행 상태 |
|---|---|---|
| RC-T01 | R-A1 | NOT_EXECUTED |
| RC-T02 | R-A2 | NOT_EXECUTED |
| RC-T03 | R-B2 | NOT_EXECUTED |
| RC-T04 | R-B1 | NOT_EXECUTED |
| RC-T05 | R-B3 | NOT_EXECUTED |
| RC-T06 | R-B5 | NOT_EXECUTED |
| RC-T07 | R-B6 | NOT_EXECUTED |
| RC-T08 | R-C1 | NOT_EXECUTED |
| RC-T09 | R-C2 | NOT_EXECUTED |
| RC-T10 | R-D2 | NOT_EXECUTED |
| RC-T11 | R-D3 | NOT_EXECUTED |
| RC-T12 | R-E1 | NOT_EXECUTED |
| RC-T13 | R-E2 | NOT_EXECUTED |
| RC-T14 | R-E3 | NOT_EXECUTED |
| RC-T15 | R-F1 | NOT_EXECUTED |
| RC-T16 | R-F2 | NOT_EXECUTED |
| RC-T17 | R-F3 | NOT_EXECUTED |
| RC-T18 | R-F4 | NOT_EXECUTED |
| RC-T19 | R-G1 | NOT_EXECUTED |
| RC-T20 | R-H1 | NOT_EXECUTED |
| RC-T21 | R-H3 | NOT_EXECUTED |
| RC-T22 | R-D4 | NOT_EXECUTED |
| RC-T23 | R-I1 | NOT_EXECUTED |
| RC-T24 | R-M1 | NOT_EXECUTED |
| RC-T25 | R-C1 | NOT_EXECUTED |
| RC-T26 | R-M2 | NOT_EXECUTED |
| RC-T27 | R-J1 | NOT_EXECUTED |
| RC-T28 | R-J3 | NOT_EXECUTED |
| RC-T29 | R-K2 | NOT_EXECUTED |
| RC-T30 | R-K3, R-K4 | NOT_EXECUTED |
