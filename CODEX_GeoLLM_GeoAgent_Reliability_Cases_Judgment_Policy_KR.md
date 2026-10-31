# CODEX Prompt
## GeoLLM / Marine GeoAgent Reliability Case Matrix & Judgment Policy
### 실제 GeoAgent 신뢰성 문제의 체계적 식별, 정책화, 구현 감사 및 SCIE 실험 반영

---

# 0. 목적

이 작업의 목적은 GeoLLM에서 발생할 수 있는 신뢰성 문제를 단순 예외 목록으로 나열하는 것이 아니다.

다음 네 가지를 동시에 수행한다.

1. 실제 해양 GeoAgent에서 발생 가능한 신뢰성 실패 유형을 체계적으로 정의한다.
2. 각 실패 유형에 대해 현재 GeoLLM이 어떤 판단을 내려야 하는지 명시한다.
3. 현재 production 코드가 그 판단을 실제로 구현하는지 감사한다.
4. 그 실패 유형을 SCIE 논문의 RQ1~RQ5 실험과 연결한다.

핵심 관점:

> GeoAgent 신뢰성은 올바른 Feature를 선택하는 것만으로 확보되지 않는다.
> 자연어 의미, 공간 연산, 기준기하, 데이터 범위, 스키마, 도구, 실행상태,
> 복합작업 완료조건, evidence 및 recovery 이후 의미 보존까지 모두 통제되어야 한다.

---

# 1. 현재 GeoLLM 구현을 우선 기준으로 삼는다

반드시 현재 Git HEAD를 다시 읽고 `git_sha`, `git_dirty`를 기록한다.

우선 감사 대상:

```text
shared/schemas/agent.py
services/orchestrator/execution_validator.py
services/orchestrator/schema_binding_adapter.py
services/orchestrator/context_resolver.py
services/orchestrator/s101_radius_execution.py
services/orchestrator/evidence_builder.py
services/orchestrator/kg_ontology_validator.py

data/capability_registry.yaml
data/agent_capability_registry.yaml
data/query_template_registry.yaml
data/tool_registry.yaml
data/validation_rule_registry.yaml
data/kg_ontology_contract.yaml
data/s101_feature_catalogue_v2_parsed.json

research/marine_geollm_scie/
```

현재 코드에서 확인되는 핵심 상태:

```text
PlanStatus:
- DRAFT
- NEEDS_USER_INPUT
- BLOCKED_CONFIG
- BLOCKED_DATA
- BLOCKED_POLICY
- PLAN_READY
- EXECUTION_READY
```

QEC는 최소 다음 정보를 가진다.

```text
original_query
slots.location_text
slots.reference_geometry
slots.crs
slots.distance_m
slots.spatial_relation
slots.target_features
slots.resolved_target_set
slots.query_template
slots.tool
slots.unresolved_slots

feature_bindings
data_bindings
tool_bindings
spatial
route_plan
readiness
blockers
warnings
snapshot_versions
provenance
```

ExecutionValidator 승인 후 QEC가 바뀌면 기존 승인이 무효화되어야 한다.

현재 핵심 authorization 원칙:

```text
EXECUTION_READY
+ blockers 없음
+ validator authority
+ validation input_hash == current QEC input_hash
```

---

# 2. 사례별 하드코딩 금지

금지:

```text
if location == "독도":
    radius = 1000

if location == "부산항":
    use_lv5_boundary = True
```

대신 공통 우선순위:

```text
1. 사용자 명시 조건
2. 자연어에서 명확히 추출된 spatial operator
3. 권위 있는 reference geometry
4. 사전 정의된 interpretation policy
5. dataset coverage / runtime capability 확인
6. 그래도 결정 불가하면 clarification / block
```

모든 default는 provenance를 남긴다.

```text
distance_m = 1000
distance_source = DEFAULT_POLICY
policy_id = NEARBY_DEFAULT_1KM
```

사용자 명시값은:

```text
distance_source = USER_EXPLICIT
```

로 구분한다.

---

# 3. GeoAgent Reliability Taxonomy

## R-A. Semantic Grounding Failure

### R-A1. Wrong Feature

예:

```text
사용자: 침선을 찾아줘
잘못된 plan: Obstruction
정답: Wreck
```

우리 시스템 판단:

```text
semantic binding 불일치
→ PLAN_READY 이전에 수정 또는 BLOCK
```

실험: RQ1 / RQ2

---

### R-A2. Semantic Over-expansion

예:

```text
사용자: Wreck만 찾아줘
plan:
- Wreck
- Obstruction
- Rock
- FoulGround
```

기술적으로 실행 가능해도 사용자 의도보다 넓다.

판단:

```text
semantic intent mismatch
→ REVIEW_NEEDED 또는 BLOCK
```

LLM Reviewer 강점 후보.

---

### R-A3. Ambiguous Marine Term

예:

```text
"등대"
```

가능한 의미:

```text
Landmark / Building 구조물
LightAllAround / LightSectored 등화
시설 전체 개념
```

판단:

```text
definition query → 조건부 복수 후보 설명 가능
spatial search → 실행 대상 집합 + dedup policy 필요
```

결과를 실질적으로 바꾸는 모호성이면:

```text
NEEDS_USER_INPUT
```

---

# 4. Spatial Interpretation Failure

## R-B1. NEAREST를 Radius로 잘못 변환

질의:

```text
독도 부근에서 가장 가까운 등대를 찾아줘.
```

잘못된 해석:

```text
dwithin 1 km
```

정답:

```text
spatial_relation = nearest
radius = null
top_k = 1
```

판단 원칙:

```text
explicit operator > vague proximity default
```

---

## R-B2. Vague proximity without explicit distance

질의:

```text
독도 부근의 등대를 찾아줘.
```

운영정책을 사전 고정했다면:

```text
spatial_relation = dwithin
distance_m = 1000
distance_source = DEFAULT_POLICY
```

정책이 없으면:

```text
NEEDS_USER_INPUT
```

---

## R-B3. Missing Selected Area

질의:

```text
Find wrecks intersecting the selected area.
```

selected geometry가 없음.

정답:

```text
readiness = NEEDS_USER_INPUT
blocker = MISSING_REFERENCE_GEOMETRY
execution_attempted = false
tool_called = false
sql_executed = false
```

임의 AOI 생성 금지.

사용자에게 영역 요청만 했는지가 아니라,
실제 실행이 발생하지 않았음을 instrumentation으로 증명한다.

---

## R-B4. Wrong Reference Geometry

질의:

```text
부산항 영역 안의 정박지
```

가능한 geometry:

```text
부산항 대표점
centroid
항계 polygon
여러 축척 boundary
```

판단:

질의가 “영역 안”이면 점으로 축약하지 않는다.

```text
reference_geometry_type = authoritative polygon
```

여러 boundary가 있으면 canonical policy를 사전 고정하고 기록:

```text
source
layer
scale/version
feature_id
geometry_hash
CRS
```

---

## R-B5. Boundary Predicate Ambiguity

경계 접촉 객체를:

```text
within
covered_by
intersects
```

중 무엇으로 처리할지 사전 정책이 필요하다.

정책이 없고 결과가 바뀔 수 있으면:

```text
BLOCKED_CONFIG
```

또는 research harness에서 `UNRESOLVED_POLICY`.

---

## R-B6. Polygon Distance Error

질의:

```text
부산항 주변 2 km의 정박지
```

잘못된 방식:

```text
centroid ↔ centroid
```

권장:

```text
geometry-to-geometry minimum geodesic distance
```

현재 `feature_search_by_radius`의 geography 기반 `ST_DWithin` / `ST_Distance`와 일치하는지 감사한다.

---

# 5. Dataset Coverage Failure

## R-C1. Out-of-Coverage를 Empty Result로 오해

연구 snapshot 예:

```text
등대 source = 부산청 항로표지
Wreck = 부산권
query = 독도
```

0건이 나와도:

```text
REAL_WORLD_EMPTY
```

로 결론 내리지 않는다.

정답:

```text
coverage_status = OUT_OF_COVERAGE
readiness = BLOCKED_DATA
result_count = UNKNOWN
```

사용자 응답:

```text
현재 연결된 데이터 범위로는 독도 지역의 존재 여부를 확정할 수 없습니다.
```

실험:

```text
Safe Abstention Accuracy
False Ready Rate
Coverage Awareness
```

---

## R-C2. Partial Coverage

예:

```text
제한구역 source = entry-restricted subset
query = 제한구역 전체
```

판단:

```text
PARTIAL + source_scope disclosure
```

또는 완전성이 필수면:

```text
BLOCKED_DATA
```

---

## R-C3. Stale Dataset Snapshot

질의:

```text
현재 제한구역
```

snapshot이 과거라면 freshness requirement를 확인한다.

충족되지 않으면:

```text
BLOCKED_DATA
```

또는 명시적 temporal limitation.

---

# 6. Schema / Catalogue Reliability

## R-D1. Feature Not in Catalogue

예:

```text
feature = Lighthouse
```

실제 독립 S-101 Feature가 없다면:

```text
FEATURE_NOT_IN_CATALOGUE
→ semantic re-resolution 또는 BLOCKED_CONFIG
```

---

## R-D2. Attribute Not Allowed for Feature

예:

```text
Wreck.imaginaryDepthValue
```

Feature Catalogue attributeBinding 검사.

```text
ATTRIBUTE_NOT_IN_FEATURE
→ BLOCK
```

---

## R-D3. CodeList Misuse

예:

```text
restriction(RESTRN)
vs
categoryOfRestrictedArea(CATREA)
```

attribute identity + permitted_values + feature binding을 모두 검사한다.

---

## R-D4. Schema vs Instance Confusion

질의:

```text
이 Wreck의 S-101 속성을 설명해줘.
```

잘못된 답:

```text
Wreck는 categoryOfWreck, status, valueOfSounding을 가질 수 있습니다.
```

이는 schema 설명일 뿐 특정 객체 값이 아니다.

올바른 연결:

```text
object W123
→ actual DB attributes
→ categoryOfWreck = 2
→ FC code list 2 = Dangerous Wreck
→ source/version/locator
```

구분:

```text
SCHEMA_ALLOWED_ATTRIBUTE
INSTANCE_ATTRIBUTE_VALUE
```

---

# 7. CRS / Unit / Numeric Reliability

## R-E1. Unit Normalization

```text
5 km
5000 m
```

동일 실행계약:

```text
distance_m = 5000
```

원 단위와 변환 provenance 저장.

---

## R-E2. Invalid Distance

현재 validator의 radius 제한 등 실제 코드 정책을 사용한다.

예:

```text
distance < 0
distance > MAX_RADIUS_M
```

정책 위반이면 실행 금지.

---

## R-E3. CRS Mismatch

geometry SRID와 tool/query template 기대 SRID 불일치.

안전하고 승인된 transformation만 허용.

그 외:

```text
BLOCKED_CONFIG
```

---

# 8. Tool / Runtime Reliability

## R-F1. Tool Unavailable

tool registry/runtime에서 unavailable:

```text
BLOCKED_CONFIG
```

승인된 semantic-equivalent fallback이 있을 때만 recovery 대상.

---

## R-F2. Query Template Missing

필수 template 없음:

```text
BLOCKED_CONFIG
```

---

## R-F3. Runtime Schema Drift

registry와 DB column/schema 불일치:

```text
SCHEMA_CHANGED
→ BLOCKED_CONFIG
```

자동 SQL 추측 금지.

---

## R-F4. Permission / Security Scope

권한 부족:

```text
BLOCKED_POLICY
```

Recovery로 권한 우회 금지.

---

# 9. Validation Staleness / TOCTOU

## R-G1. Validated Plan Mutated After Approval

승인 당시:

```text
distance = 1000
```

승인 후:

```text
distance = 5000
```

현재 GeoLLM 원칙:

```text
QEC patch
→ revision 증가
→ readiness = DRAFT
→ old execution_validation 제거
```

실행 시:

```text
stored input_hash != current input_hash
→ execution_authorized = false
```

이 사례는 deterministic reliability 핵심 실험으로 사용한다.

---

# 10. Composite Task Reliability

## R-H1. Partial Composite Completion

질의:

```text
독도 주변 5 km의 등대와 난파선을 찾아 각각의 근거를 알려줘.
```

subtasks:

```text
A = lighthouse search
B = Wreck search
C = lighthouse evidence
D = Wreck evidence
```

full success:

```text
A spatial correct
AND B spatial correct
AND C evidence correct
AND D evidence correct
```

일부만 완료:

```text
PARTIAL
```

---

## R-H2. Composite Comparison Incomplete

질의:

```text
부산항 주변 2 km의 정박지와 제한구역을 찾아 비교해줘.
```

필수:

```text
AnchorageArea result
RestrictedArea result
comparison
source scope
```

검색만 하고 비교를 안 하면 incomplete.

---

## R-H3. Cross-subtask Scope Mismatch

한쪽은 full dataset,
다른 쪽은 subset일 경우 단순 count 비교를 전체 비교처럼 표현하면 안 된다.

```text
comparison_scope_compatible = false
```

---

# 11. Duplicate Real-world Entity Reliability

## R-I1. Same Lighthouse Represented by Multiple Features

예:

```text
Landmark
+
LightAllAround
```

동일 실재 시설일 수 있음.

질의:

```text
가장 가까운 등대 1개
```

시설 수준 query라면:

```text
dedup_scope = REAL_WORLD_FACILITY
```

정책이 필요하다.

---

# 12. Empty Result Reliability

다음을 반드시 분리한다.

```text
SUCCESS_EMPTY
OUT_OF_COVERAGE
FAILED_QUERY
```

- `SUCCESS_EMPTY`: coverage 충분 + 실행 성공 + 실제 0건
- `OUT_OF_COVERAGE`: 질의영역을 dataset이 커버하지 않음
- `FAILED_QUERY`: tool/schema/runtime 실패

세 상태를 모두 “0건”으로 표현하는 것을 금지한다.

현재 `TaskResultStatus.SUCCESS_EMPTY`가 executor와 final answer까지 올바르게 전파되는지 감사한다.

---

# 13. Evidence Reliability

## R-J1. Correct Object, Wrong Source

Spatial correctness와 Evidence correctness를 분리한다.

---

## R-J2. KG Evidence Used as Official Definition

사용자가 공식 원문을 요구하면:

```text
FC / DCEG / official source locator
```

가 필요하다.

KG derived description만으로 대체 금지.

---

## R-J3. Version Mismatch

Feature 설명과 evidence edition/version 불일치:

```text
WRONG_VERSION
```

---

# 14. Recovery Reliability

## R-K1. Valid Recovery

예:

```text
5 km → 5000 m
```

semantic intent 보존.

---

## R-K2. Semantic Drift During Recovery

원래:

```text
Wreck
```

Recovery 후:

```text
Wreck + Rock + Obstruction
```

이면:

```text
recovery_success = true
semantic_preserved = false
```

full success가 아니다.

---

## R-K3. Recovery Must Not Override Missing Data

독도 data가 없는데 부산 data로 대체 검색 금지.

정답:

```text
BLOCKED_DATA
```

---

## R-K4. Recovery Must Not Override Policy

permission denied를 다른 tool로 우회 금지.

```text
BLOCKED_POLICY
```

---

# 15. Result Limit / Truncation Reliability

현재 radius template는 result_limit을 가진다.

예:

```text
실제 = 87
returned = 30
```

30개만 보여주며 “총 30개”라고 답하면 오류.

반드시:

```text
total_count
returned_count
truncated
offset/page
```

를 구분한다.

---

# 16. Temporal Reliability

## R-L1. Current vs Historical Data

질의:

```text
현재 선박 통항
```

dataset이 historical snapshot이면:

```text
BLOCKED_DATA
```

또는 historical limitation 공개.

---

## R-L2. Required Time Range Missing

temporal operation이 기간을 요구하나 query에 없음.

정책 default가 없으면:

```text
NEEDS_USER_INPUT
```

---

# 17. Default Policy Reliability

Default 자체가 잘못은 아니다.

문제:

```text
숨겨진 default
사용자 의미보다 우선하는 default
실험 중 변경되는 default
```

모든 default 기록:

```text
field
value
source = USER_EXPLICIT | DEFAULT_POLICY | RESOLVER | RECOVERY
policy_id
policy_version
```

우선순위:

```text
USER_EXPLICIT
>
EXPLICIT_SEMANTIC_OPERATOR
>
AUTHORITATIVE_RESOLUTION
>
DEFAULT_POLICY
```

---

# 18. 우리 시스템의 공통 판단 상태

## EXECUTION_READY

다음이 확인된 경우만:

```text
semantic binding valid
required QEC fields complete
reference geometry valid
dataset coverage adequate
schema/tool/template valid
security allowed
execution validation hash current
```

## NEEDS_USER_INPUT

사용자만 결정할 수 있는 핵심 의미/기하가 비어 있음.

예:

```text
selected area missing
실질적 결과를 바꾸는 의미 모호성
```

## BLOCKED_DATA

필요한 권위 data 없음/범위 밖/불충분.

## BLOCKED_CONFIG

schema/tool/template/CRS/policy configuration 문제.

## BLOCKED_POLICY

권한/보안/승인정책 위반.

## PARTIAL

복합작업 중 일부만 완료되고 이를 명확히 공개할 수 있는 경우.

현재 `PlanStatus`, `AgentStatus`, `TaskResultStatus` 중 PARTIAL 표현 위치를 감사하고 일관성 여부를 보고한다.

---

# 19. Reliability Decision Matrix를 machine-readable로 생성

생성:

```text
research/marine_geollm_scie/reliability/
  reliability_case_registry.yaml
  reliability_policy_registry.yaml
  reliability_gap_audit.json
```

예:

```yaml
case_id: COVERAGE_OUT_OF_SCOPE
category: dataset_coverage
trigger:
  query_area_outside_dataset_coverage: true
expected_decision:
  readiness: BLOCKED_DATA
  execution_attempted: false
forbidden_behavior:
  - return_zero_as_real_world_empty
metrics:
  - safe_abstention_accuracy
  - false_ready_rate
rq:
  - RQ2
  - RQ3
```

---

# 20. Production 구현상태 분류

각 case:

```text
IMPLEMENTED
PARTIALLY_IMPLEMENTED
NOT_IMPLEMENTED
NOT_APPLICABLE
```

표:

| Reliability Case | Required Behavior | Current Code | Status | Gap | Proposed Minimal Change |
|---|---|---|---|---|---|

새 기능을 바로 production에 넣지 않는다.

먼저:

```text
product change
research-only instrumentation
evaluation policy
```

를 분리한다.

---

# 21. QEC 확장 필요성 감사

현재 QEC에 없는 다음 개념의 필요성을 감사한다.

```text
distance_source
interpretation_policy_id
reference_geometry_source
reference_geometry_version
geometry_hash
coverage_status
coverage_geometry_ref
boundary_policy
distance_calculation_policy
dedup_policy
result_scope
source_scope
```

무조건 typed field를 추가하지 않는다.

먼저 기존:

```text
spatial
context
data_discovery
provenance
snapshot_versions
```

에 구조화 가능 여부를 검토한다.

deterministic validation에 typed contract가 반드시 필요한 경우만 schema 확장을 제안한다.

---

# 22. Primary Detector 분류

각 case에 다음을 지정한다.

```text
LLM_REVIEW_PRIMARY
DETERMINISTIC_PRIMARY
HYBRID
POST_EXECUTION_PRIMARY
```

예:

```text
Semantic over-expansion → LLM_REVIEW_PRIMARY
Attribute not in feature → DETERMINISTIC_PRIMARY
Out-of-coverage → DETERMINISTIC_PRIMARY
Recovery semantic drift → HYBRID
Wrong spatial result after successful execution → POST_EXECUTION_PRIMARY
```

RQ2 fault taxonomy와 직접 연결한다.

---

# 23. 8개 Method 설계와 연결

```text
B0 Direct LLM
B1 Text RAG
B2 Ontology/KG
B3 Generic Tool Agent

B4 = frozen B3 initial plan + LLM Review only
P0 = frozen B3 initial plan + lossless QEC compilation + Deterministic Validator only
H  = frozen B3 initial plan + LLM Review + Deterministic Validator

P1 = Full Marine GeoLLM end-to-end
```

B4/P0/H는 반드시 동일 `plan_hash`.

P0의 QEC compilation은 plan을 고치면 안 된다.

없는 값은:

```text
MISSING
```

으로 유지하고 Validator가 검출하게 한다.

---

# 24. RQ별 활용

## RQ1
조건별 기술 효과:

```text
semantic ambiguity
unseen synonym
composite task
coverage condition
spatial operator
```

## RQ2
오류 검출 주체:

```text
semantic over-expansion
feature/attribute/codelist
CRS
missing geometry
coverage
tool/schema
permission
```

## RQ3
Execution Success vs Spatial Correctness:

```text
wrong reference geometry
wrong boundary policy
centroid distance error
duplicate real-world entity
truncation
false empty
```

## RQ4
Recovery + Semantic Preservation:

```text
unit normalization
CRS repair
tool fallback
feature re-resolution
semantic drift
forbidden recovery
```

## RQ5
Reliability Cost:

```text
latency
false block
false ready
tool calls
LLM tokens
human escalation
```

---

# 25. 반드시 추가할 대표 test cases

최소 다음을 benchmark/fault injection에 추가한다.

```text
01. "가라앉은 배를 찾아줘" → Wreck semantic grounding
02. "Wreck만 찾아줘"인데 hazard 전체로 확장
03. "독도 부근의 등대" → vague proximity default
04. "독도에서 가장 가까운 등대" → nearest, no radius
05. selected area + geometry 없음
06. 부산항 within + 경계 접촉 객체
07. 부산항 2km + centroid/min-distance 차이
08. 독도 query + 부산-only dataset
09. partial RestrictedArea coverage
10. Wreck invalid attribute
11. RESTRN vs CATREA 혼동
12. 5 km vs 5000 m equivalence
13. radius > MAX policy
14. CRS mismatch
15. tool unavailable
16. query template missing
17. DB schema drift
18. permission denied
19. validated QEC mutation after approval
20. Lighthouse + Wreck composite partial completion
21. Anchorage + RestrictedArea comparison scope mismatch
22. Wreck actual attribute vs FC allowed attribute confusion
23. same lighthouse represented by Landmark + Light
24. valid empty result
25. out-of-coverage false empty
26. result_limit truncation
27. wrong evidence source
28. wrong standard version
29. recovery semantic drift
30. recovery attempts to bypass missing data/policy
```

---

# 26. 출력물

```text
research/marine_geollm_scie/reliability/
  GEOAGENT_RELIABILITY_CASES.md
  RELIABILITY_DECISION_MATRIX.md
  IMPLEMENTATION_GAP_AUDIT.md
  reliability_case_registry.yaml
  reliability_policy_registry.yaml
```

각 case에는:

```text
Case ID
사용자 질의 예
실패 시나리오
왜 위험한가
현재 GeoLLM 관련 코드
필요 QEC 정보
정답 decision
금지 행동
Primary detector
관련 metric
관련 RQ
현재 구현상태
```

를 기록한다.

---

# 27. 최종 요약에서 반드시 답할 질문

1. 현재 GeoLLM이 이미 잘 통제하는 reliability failure는 무엇인가?
2. partially implemented인 것은 무엇인가?
3. 현재 가장 위험한 silent failure는 무엇인가?
4. dataset coverage를 deterministic gate로 검증하는가?
5. reference geometry policy가 deterministic하게 고정되어 있는가?
6. default distance가 provenance와 함께 관리되는가?
7. boundary/distance/dedup 정책이 명시되어 있는가?
8. composite task의 partial/full success가 구분되는가?
9. SUCCESS_EMPTY와 OUT_OF_COVERAGE가 구분되는가?
10. recovery 이후 semantic preservation을 측정 가능한가?
11. evidence가 object-level로 trace 가능한가?
12. RQ1~RQ5를 production instrumentation으로 실제 측정 가능한가?

---

# 28. Scientific Integrity

- 특정 benchmark case만 통과시키는 하드코딩 금지.
- GOLD를 보고 사례별 policy를 튜닝하지 않는다.
- data coverage가 없으면 0건으로 만들지 않는다.
- LLM judge로 spatial GOLD를 대체하지 않는다.
- execution success를 spatial correctness로 간주하지 않는다.
- partial task를 full success로 세지 않는다.
- semantic drift recovery를 성공만으로 보고하지 않는다.
- baseline과 proposed에 다른 data snapshot을 주지 않는다.
- B4/P0/H initial plan은 동일하게 고정한다.
- policy 변경 시 version/hash를 새 run manifest에 기록한다.

---

# 29. 최종 연구 목적

최종적으로 다음 명제를 실험 가능하게 만들어야 한다.

> Marine GeoAgent의 실패는 LLM의 언어 오류에만 국한되지 않는다.
> 공간 연산 해석, 기준기하 선택, 데이터 범위, S-101 schema,
> runtime capability, 복합과업 완료조건, evidence provenance 및 recovery 과정에서도
> silent failure가 발생할 수 있다.
> Marine GeoLLM은 이러한 실행 의미를 typed QEC로 명시하고,
> deterministic validation, post-execution validation 및 bounded recovery를 통해
> 오류 유형별로 통제한다.

단, 실제 실험결과가 이를 지지할 때만 최종 논문 결론으로 사용한다.
