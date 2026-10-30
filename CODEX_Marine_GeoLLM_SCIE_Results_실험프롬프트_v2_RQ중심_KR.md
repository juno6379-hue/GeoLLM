# Codex 개발 지시서 v2
## Marine GeoLLM SCIE 논문 Results — 조건별 신뢰성·오류유형·공간정답·복구·비용 실험

### 논문 제목

**국문**  
**S-100 기반 해양공간 질의를 위한 온톨로지 기반 의미 정합과 실행 검증형 Marine GeoLLM 프레임워크**

**영문**  
**An Ontology-Grounded and Execution-Validated Marine GeoLLM Framework for S-100-Based Marine Geospatial Queries**

---

# 0. 이번 실험의 핵심 방향

이번 논문의 목적은 다음과 같은 단순 결론을 보여주는 것이 아니다.

```text
RAG 추가 → 성능 향상
Ontology 추가 → 더 향상
Validator 추가 → 더 향상
Recovery 추가 → 더 향상
```

이런 계단식 결과만으로는 연구 기여가 약하다.

이번 논문은 다음 **5개의 비자명한 연구질문**에 실제 실험으로 답해야 한다.

> **RQ1. 어떤 조건에서 어떤 기술이 효과적인가?**

> **RQ2. 어떤 오류는 LLM Review로 해결되고, 어떤 오류는 Deterministic Validation이 필요한가?**

> **RQ3. Execution Success와 Spatial Correctness 사이에 얼마나 큰 gap이 존재하는가?**

> **RQ4. Recovery는 실행을 복구하면서 원래 사용자의 의미도 보존하는가?**

> **RQ5. 더 높은 신뢰성을 얻기 위해 latency, token, tool-call, false block 등의 비용을 얼마나 지불하는가?**

논문의 최종 주장은 다음 방향이어야 한다.

> Marine GeoLLM의 핵심 가치는 단순히 더 많은 모듈을 추가하여 평균 성공률을 높이는 데 있지 않다.  
> S-100/S-101 의미 정합, typed execution contract, deterministic validation, post-execution validation 및 bounded recovery는 서로 다른 실패 유형을 담당하며, 이들을 조합함으로써 실행 성공과 실제 공간정답 사이의 silent failure를 줄일 수 있다.

---

# 1. GOLD는 이미 제공된 고정 입력이다

**중요: GOLD annotation은 이미 사용자로부터 전달된 상태이다.**

Codex는 GOLD를 새로 생성하거나 수정하거나 재해석하지 않는다.

GOLD는 실험의 독립된 정답 입력이며 다음 목적으로만 사용한다.

```text
Semantic GOLD
QEC GOLD
Spatial Result GOLD
Evidence GOLD
Fault/Error GOLD
```

반드시 실행 시작 시 실제 GOLD 파일 경로와 hash를 찾아 `manifest.json`에 기록한다.

예:

```text
gold_semantics_sha256
gold_qec_sha256
gold_spatial_results_sha256
gold_evidence_sha256
fault_gold_sha256
```

### GOLD 보호 원칙

- GOLD를 모델 prompt에 직접 제공하지 않는다.
- GOLD를 system output 생성에 사용하지 않는다.
- GOLD를 이용해 runtime rule을 자동 수정하지 않는다.
- GOLD 기반 오류 분석 후 production code를 수정했다면 반드시 **새 run ID**로 다시 측정한다.
- test 결과를 본 뒤 GOLD 자체를 유리하게 수정하지 않는다.
- GOLD 변경 시 benchmark version을 올리고 기존 run과 직접 혼합하지 않는다.

---

# 2. 기존 시스템을 그대로 측정 대상으로 사용한다

현재 GeoLLM의 실제 production 요소를 최대한 재사용한다.

특히 다음을 우선 감사한다.

```text
shared/schemas/agent.py
services/orchestrator/execution_validator.py
services/orchestrator/kg_ontology_validator.py
services/orchestrator/evidence_builder.py
services/orchestrator/s101_radius_execution.py
services/orchestrator/route_planner.py
services/orchestrator/schema_binding_adapter.py

data/s101_feature_catalogue_v2_parsed.json
data/kg_ontology_contract.yaml
data/capability_registry.yaml
data/agent_capability_registry.yaml
data/query_template_registry.yaml

research/marine_geollm_scie/
```

새 실험을 위해 production logic을 복제하지 않는다.

Research layer가 production component를 호출하도록 한다.

Production은 research package를 import하면 안 된다.

---

# 3. 비교 방법 — 단순 누적이 아니라 역할별 직접 비교

최종 실험에서는 다음 실험 프로파일을 사용한다.

## B0 — Direct LLM

```text
Natural Language
→ LLM
→ plan / answer
```

목적:

- 최소 baseline
- 외부 grounding과 execution gate 없이 LLM 자체가 얼마나 하는지 측정

---

## B1 — Text RAG

```text
Natural Language
→ S-100/S-101 문서 검색
→ LLM
```

목적:

- 관련 문서를 가져오는 것만으로 의미정합이 충분한지 측정

---

## B2 — Ontology/KG Grounding

```text
Natural Language
→ Ontology/KG
→ verified semantic concepts
→ plan
```

목적:

- lexical/semantic gap이 큰 질의에서 ontology가 RAG보다 실제로 유리한지 측정

---

## B3 — Generic Tool Agent

```text
Natural Language
→ plan
→ capability/tool selection
→ GIS execution
```

목적:

- 일반적인 GeoAgent/Tool Agent 방식의 planning + execution 성능 측정
- S-100-aware deterministic execution gate는 사용하지 않음

---

## B4 — LLM Self-Reviewer

```text
plan candidate
→ LLM reviewer
→ PASS / BLOCK / REVISE
```

목적:

- LLM의 self-review가 어떤 오류에 강하고 어떤 오류에 약한지 측정

**중요:** 가능하면 Proposed 시스템과 동일한 주 LLM 또는 동급 모델을 사용한다.  
너무 작은 모델만 B4에 사용하여 Proposed에 유리한 비교를 만들지 않는다.

---

## P0 — QEC + Deterministic Validator

```text
Semantic Grounding
→ Typed QEC
→ Deterministic ExecutionValidator
→ GIS execution
→ Post Validation
```

Recovery는 비활성화.

목적:

- deterministic validation 자체의 효과를 분리 측정

---

## P1 — Full Marine GeoLLM

```text
Ontology/KG
→ Capability Retriever / Resolver
→ Typed QEC
→ Deterministic Validator
→ GIS execution
→ Post Validation
→ Recovery / Re-planning
→ EvidenceBundle
```

목적:

- 최종 proposed framework의 end-to-end 성능 측정

---

## H — Hybrid Review + Deterministic Validation

가능하면 다음 hybrid 조건도 추가한다.

```text
LLM Review
+
Deterministic Validator
```

목적:

- LLM Review와 Deterministic Validator가 대체관계가 아니라 상보관계인지 검증

---

# 4. RQ1 — 어떤 조건에서 어떤 기술이 효과적인가?

## 4.1 핵심 가설

평균 정확도 하나만 비교하지 않는다.

각 query를 여러 **조건(stratum)** 으로 분류하여 어떤 조건에서 각 기술의 효과가 커지는지 측정한다.

---

## 4.2 조건 분류

GOLD/benchmark metadata에 다음 조건 라벨을 생성하거나 이미 있는 값을 사용한다.

### A. 용어 난이도

```text
OFFICIAL_TERM
DOMAIN_KOREAN
COLLOQUIAL
UNSEEN_SYNONYM
MIXED_KO_EN
```

예:

```text
OFFICIAL_TERM:
Wreck의 정의를 알려줘

DOMAIN_KOREAN:
침선을 찾아줘

COLLOQUIAL:
가라앉은 배를 찾아줘

UNSEEN_SYNONYM:
바닷속에 잠겨 못 쓰게 된 배를 찾아줘

MIXED_KO_EN:
부산항 주변 Wreck 찾아줘
```

---

### B. 질의 복잡도

```text
SINGLE_CONCEPT
SINGLE_SPATIAL_OPERATOR
MULTI_CONSTRAINT
COMPOSITE_MULTI_TASK
MULTI_SOURCE
```

---

### C. 공간연산 종류

```text
NONE
WITHIN
INTERSECTS
NEAREST
DWITHIN_RADIUS
MULTI_SPATIAL
```

---

### D. 정보 가용성

```text
DATA_COMPLETE
DATA_PARTIAL
DATA_UNAVAILABLE
REFERENCE_GEOMETRY_MISSING
TOOL_UNAVAILABLE
```

---

### E. 모호성

```text
UNAMBIGUOUS
SEMANTIC_AMBIGUITY
LOCATION_AMBIGUITY
ATTRIBUTE_AMBIGUITY
```

---

## 4.3 RQ1 핵심 비교

다음 비교를 반드시 별도로 산출한다.

### RAG vs Ontology/KG

질문:

> semantic gap이 커질수록 Ontology/KG 효과가 커지는가?

표:

```text
Query Condition
B1 Text-RAG Semantic F1
B2 Ontology/KG Semantic F1
Delta
95% CI
```

특히:

```text
OFFICIAL_TERM
DOMAIN_KOREAN
COLLOQUIAL
UNSEEN_SYNONYM
```

별로 비교한다.

---

### Tool Agent의 역할

질문:

> semantic understanding이 맞더라도 capability/tool planning에서 실패하는가?

비교:

```text
B2 Ontology only
vs
B3 Generic Tool Agent
```

측정:

```text
Capability Selection Accuracy
Tool Binding Accuracy
QEC Field Accuracy
Execution Success Rate
```

---

### QEC/Validator의 역할

비교:

```text
B3 Generic Tool Agent
vs
P0 QEC + Deterministic Validator
```

질문:

> 실행계약과 gate가 semantic correctness보다 operational correctness를 얼마나 개선하는가?

---

## 4.4 RQ1 최종 출력

### Table RQ1-A
조건별 semantic grounding 결과

### Table RQ1-B
조건별 planning/execution 결과

### Figure RQ1
각 조건에서 B0/B1/B2/B3/P0/P1의 성능 변화

**핵심 해석은 평균 순위가 아니라 interaction이다.**

예:

```text
공식 용어에서는 RAG와 Ontology 차이가 작음
구어체/미등록 동의어에서는 Ontology 효과가 커짐
복합질의에서는 Tool Agent가 의미정합보다 실행계획 성능에 더 큰 영향을 줌
```

실제 데이터가 그렇게 나올 때만 이 결론을 쓴다.

---

# 5. RQ2 — 어떤 오류는 LLM Review가 잡고, 어떤 오류는 Deterministic Validator가 잡는가?

## 5.1 오류 유형을 명확히 구분한다

다음 taxonomy를 사용한다.

### Semantic errors

```text
SEMANTIC_WRONG_FEATURE
SEMANTIC_WRONG_ATTRIBUTE
SEMANTIC_OVER_EXPANSION
SEMANTIC_MISSING_CONCEPT
AMBIGUOUS_MEANING
```

### S-100/S-101 schema errors

```text
FEATURE_NOT_IN_CATALOGUE
ATTRIBUTE_NOT_IN_FEATURE
INVALID_CODELIST_VALUE
INVALID_MULTIPLICITY
INVALID_FEATURE_RELATION
```

### Spatial execution errors

```text
GEOMETRY_OPERATOR_MISMATCH
CRS_MISMATCH
UNIT_ERROR
INVALID_DISTANCE
MISSING_REFERENCE_GEOMETRY
INVALID_BOUNDARY_POLICY
```

### Runtime errors

```text
DATASET_UNAVAILABLE
SCHEMA_CHANGED
TOOL_UNAVAILABLE
QUERY_TEMPLATE_MISSING
PERMISSION_DENIED
```

### Evidence errors

```text
EVIDENCE_MISSING
WRONG_SOURCE
WRONG_VERSION
UNTRACEABLE_RESULT
```

---

## 5.2 반드시 같은 오류 세트를 비교한다

동일 fault case를 다음 세 방법에 입력한다.

```text
B4 LLM Reviewer
P0 Deterministic Validator
H  Hybrid
```

각 방법에 대해 계산:

```text
TP
FP
FN
TN
Precision
Recall
F1
False Ready Rate
False Block Rate
```

---

## 5.3 핵심은 전체 F1이 아니라 오류유형별 matrix다

### Table RQ2

| Error Type | LLM Review Recall | Deterministic Recall | Hybrid Recall | False Ready | False Block |
|---|---:|---:|---:|---:|---:|

예상 결론을 미리 고정하지 않는다.

가능한 연구발견:

```text
Semantic ambiguity → LLM review 강점
Schema/CRS/tool error → deterministic validator 강점
Hybrid → 전체 오류 coverage 개선
```

실제 결과가 반대이면 그대로 보고한다.

---

## 5.4 오류 심각도

오류를 다음으로 분리한다.

```text
CRITICAL
MAJOR
MINOR
```

특히 CRITICAL 오류의 False Ready Rate를 별도 보고한다.

예:

```text
CRITICAL_FALSE_READY_RATE
```

전체 F1보다 안전성 관점에서 중요한 지표로 사용한다.

---

# 6. RQ3 — Execution Success와 Spatial Correctness 사이의 gap은 얼마인가?

이 실험은 논문의 핵심 결과 중 하나이다.

---

## 6.1 서로 다른 두 개념을 절대 합치지 않는다

### Execution Success

```text
Tool/SQL/GIS가 예외 없이 실행 완료됨
```

### Spatial Correctness

```text
실행 결과가 GOLD object/geometry/distance/relation과 일치함
```

---

## 6.2 반드시 다음 4개 값을 분리한다

```text
Execution Success Rate (ESR)
Spatial Correctness Rate (SCR)
Correctness Given Execution (CGE)
Silent Spatial Failure Rate (SSFR)
```

정의:

```text
ESR =
successful executions / executable cases

CGE =
spatially correct executions / successful executions

SSFR =
executed but spatially incorrect / successful executions
```

추가 요약지표:

```text
Execution-Correctness Gap =
ESR - End-to-End Spatial Correct Rate
```

단, 분모가 다르면 별도 표에서 명확히 설명한다.

---

## 6.3 Spatial task별 평가

### Object-set query

```text
Precision
Recall
F1
Exact Set Match
```

### Distance/radius

```text
absolute distance error
relative error
tolerance pass
```

### Polygon

```text
IoU
predicate correctness
```

### Nearest

```text
top-1 correctness
rank correctness
distance error
```

### Valid empty

정답이 0개인 query는:

```text
VALID_EMPTY
```

로 인정한다.

빈 결과를 실패로 처리하지 않는다.

---

## 6.4 반드시 방법별 silent failure를 비교한다

비교:

```text
B0
B1
B2
B3
P0
P1
```

### Table RQ3

| Method | ESR | Spatial Correct | CGE | Silent Spatial Failure |
|---|---:|---:|---:|---:|

### Figure RQ3

각 방법에서:

```text
Execution Success
Spatial Correctness
```

를 나란히 표시한다.

논문에서 가장 중요한 질문:

> “성공적으로 실행된 것처럼 보이는 결과 중 실제 공간적으로 틀린 결과가 얼마나 존재하는가?”

---

# 7. RQ4 — Recovery가 성공하면서 원래 의미를 보존하는가?

Recovery를 단순 성공률로 평가하지 않는다.

---

## 7.1 Recovery 성공의 정의

다음 4개 조건을 모두 봐야 한다.

```text
1. 오류를 탐지했는가?
2. 실행 가능 상태로 복구했는가?
3. Spatial GOLD와 맞는 결과를 냈는가?
4. 원래 사용자의 semantic intent를 보존했는가?
```

---

## 7.2 Semantic Preservation

Recovery 전 GOLD intent/QEC와 Recovery 후 plan을 비교한다.

다음 지표를 추가한다.

```text
Semantic Preservation Rate (SPR)
Semantic Drift Rate (SDR)
Recovered Spatial Correctness (RSC)
```

예:

원 질의:

```text
침선만 찾아줘
```

잘못된 recovery:

```text
navigation_hazard_object 전체 검색
```

이 경우 실행은 성공해도:

```text
Recovery Execution Success = 1
Semantic Preservation = 0
```

이다.

---

## 7.3 Recovery error group

### Recoverable

```text
unit normalization
alias resolution
wrong feature candidate
CRS mismatch
missing optional binding
tool fallback when semantically equivalent
```

### Must not auto-recover

```text
permission denied
irreducible semantic ambiguity
missing authoritative data
safety/policy restriction
```

이 경우 정답 행동은:

```text
BLOCK
NEEDS_USER_INPUT
HITL
```

일 수 있다.

자동복구율을 무조건 높이는 것이 목적이 아니다.

---

## 7.4 Recovery 지표

```text
Detection Rate
Recovery Attempt Rate
Recovery Success Rate
First Repair Success
Mean Repair Iterations
Semantic Preservation Rate
Semantic Drift Rate
Recovered Spatial Correctness
Escalation Rate
```

### Table RQ4

오류유형별 recovery 결과를 작성한다.

---

# 8. RQ5 — 신뢰성 향상 비용은 얼마인가?

신뢰성 개선은 무료가 아니다.

반드시 성능과 비용을 함께 측정한다.

---

## 8.1 측정 비용

### Latency

```text
P50
P95
IQR
cold-start
steady-state
```

가능하면 다음 stage별:

```text
normalization
RAG
ontology grounding
capability retrieval
resolver
QEC construction
LLM review
deterministic validation
GIS execution
post validation
recovery
evidence assembly
total
```

---

### LLM 비용

실제 제공되는 경우만:

```text
input_tokens
output_tokens
total_tokens
```

추정값을 측정값처럼 사용하지 않는다.

---

### Tool 비용

```text
tool_calls
DB_queries
retries
repair_iterations
```

---

### Operational cost

```text
False Block Rate
Human Escalation Rate
Timeout Rate
```

---

## 8.2 비용 대비 신뢰성

각 방법에 대해:

```text
EVQSR
Spatial Correctness
False Ready
False Block
P50 latency
P95 latency
tokens
tool calls
```

을 함께 표시한다.

### Table RQ5

| Method | EVQSR | Spatial Correct | False Ready | False Block | P50 | P95 | Tokens |
|---|---:|---:|---:|---:|---:|---:|---:|

### Figure RQ5

Pareto-style scatter:

```text
X = latency or token cost
Y = reliability (EVQSR / Spatial Correctness)
```

가능하면:

```text
점 크기 = False Ready
```

또는 별도 figure로 표현한다.

---

# 9. 논문의 핵심 metric

## 9.1 Semantic

```text
Feature Grounding Accuracy
Attribute Grounding Accuracy
Relation/Operator Accuracy
Semantic Exact Match
Macro-F1
Micro-F1
```

---

## 9.2 Planning / QEC

```text
QEC Field Accuracy
QEC Exact Match
Required Slot Completeness
DataBinding Accuracy
ToolBinding Accuracy
QEC Schema Validity Rate
```

---

## 9.3 Validation

```text
Precision
Recall
F1
False Ready Rate
False Block Rate
Critical False Ready Rate
```

---

## 9.4 Execution / Spatial

```text
ESR
Spatial F1
Exact Set Match
CGE
SSFR
```

---

## 9.5 Recovery

```text
Recovery Rate
First Repair Success
Semantic Preservation Rate
Semantic Drift Rate
Recovered Spatial Correctness
Escalation Rate
```

---

## 9.6 Evidence

```text
Evidence Completeness
Valid Source Rate
Provenance Trace Success
```

---

## 9.7 End-to-End

EVQSR은 최종 composite 지표로 사용한다.

```text
EVQSR =
mean(
SemanticCorrect
× PlanValid
× ExecutionSuccess
× SpatialCorrect
× EvidenceCorrect
)
```

EVQSR 하나만 보고하지 않는다.

각 구성요소를 반드시 함께 보고한다.

---

# 10. Ablation의 목적도 바꾼다

단순:

```text
Full
- Ontology
- Validator
- Recovery
```

만 보고 끝내지 않는다.

각 ablation이 **어떤 오류 유형과 조건에 영향을 주는지** 분석한다.

예:

```text
w/o Ontology
→ colloquial/unseen synonym에서 성능 저하?

w/o QEC
→ parameter/schema 오류 증가?

w/o Validator
→ False Ready 증가?

w/o Post Validation
→ Silent Spatial Failure 증가?

w/o Recovery
→ recoverable fault에서 task completion 감소?

w/o Evidence
→ answer accuracy는 유지되지만 provenance completeness 감소?
```

### Table Ablation-by-Failure-Type

| Removed Component | Semantic Error | Schema Error | Spatial Error | Runtime Error | Evidence Error |
|---|---:|---:|---:|---:|---:|

이 표가 매우 중요하다.

---

# 11. 실험 설계는 paired comparison을 기본으로 한다

동일 case를 모든 비교방법에 사용한다.

즉:

```text
case_001:
B0
B1
B2
B3
B4/P0/H
P1
```

결과를 case_id 기준으로 pair한다.

무작위로 다른 query set을 방법별로 사용하면 안 된다.

---

# 12. 반복 실행

LLM을 포함하는 stochastic 조건:

```text
K = 5
```

권장.

temperature, seed, model version을 기록한다.

Deterministic validator는 동일 case를 5번 반복한 것을 독립 sample 5개로 통계 처리하지 않는다.

---

# 13. 통계 분석

최소 다음을 구현한다.

### Paired binary outcome

```text
McNemar test
```

예:

```text
B4 vs P0 error detection
B3 vs P0 valid execution
```

### Metric difference

```text
paired bootstrap 95% CI
```

### Condition interaction

가능하면:

```text
bootstrap stratified comparison
또는
mixed-effects logistic regression
```

을 지원한다.

예:

```text
success ~ method * terminology_condition + complexity + (1|case_group)
```

구현이 과도하면 paired stratified CI까지 수행하고 limitation에 명시한다.

---

# 14. 데이터 누수 방지

이미 개발과 파일럿에 사용된 case와 최종 holdout을 구분한다.

각 case metadata에:

```text
split = development
split = validation
split = holdout
```

을 둔다.

최종 주요 성능은 반드시 `holdout`에서 보고한다.

동일 equivalence group의 표현 변형이 train/dev와 holdout에 동시에 들어가지 않도록 group-wise split한다.

지역도 가능하면 분리한다.

예:

```text
development: 부산항 중심
holdout: 인천항 / 여수항 / 독도 등
```

실제 dataset 가용성에 맞춰 적용하되, 적용 여부를 manifest에 기록한다.

---

# 15. 결과표 구조를 RQ 중심으로 변경한다

기존 R1~R7을 유지할 수 있지만 최종 논문 표는 다음처럼 재구성한다.

## Table 1 — Benchmark and GOLD composition

```text
category
condition
split
cases
gold_complete
```

---

## Table 2 — RQ1: Condition-specific technology effectiveness

```text
condition
method
semantic_f1
qec_accuracy
execution_success
spatial_correct
delta_vs_baseline
95CI
```

---

## Table 3 — RQ2: Error-type detection matrix

```text
error_type
LLM_Reviewer_recall
Deterministic_Validator_recall
Hybrid_recall
false_ready
false_block
```

---

## Table 4 — RQ3: Execution vs Spatial Correctness

```text
method
ESR
SpatialCorrect
CGE
SilentSpatialFailure
ExecutionCorrectnessGap
```

---

## Table 5 — RQ4: Recovery and semantic preservation

```text
error_type
attempted
recovered
recovery_rate
semantic_preservation
semantic_drift
spatial_correct_after_repair
escalation
```

---

## Table 6 — Ablation by failure category

```text
profile
semantic_error_rate
schema_error_rate
spatial_error_rate
runtime_error_rate
evidence_error_rate
EVQSR
```

---

## Table 7 — RQ5: Reliability-cost trade-off

```text
method
EVQSR
SpatialCorrect
FalseReady
FalseBlock
P50
P95
tokens
tool_calls
```

---

# 16. 핵심 Figure

## Figure 1
전체 Marine GeoLLM architecture

논문 Methods용.

---

## Figure 2 — Condition × Method

질의조건별 성능 변화.

예:

```text
Official
Domain Korean
Colloquial
Unseen synonym
Composite
```

---

## Figure 3 — Error Detection Heatmap

행:

```text
error type
```

열:

```text
LLM Review
Deterministic
Hybrid
```

---

## Figure 4 — Execution vs Spatial Correctness

방법별 두 막대:

```text
Execution Success
Spatial Correctness
```

가장 중요한 Figure 후보.

---

## Figure 5 — Recovery outcome

```text
Recovered + Meaning Preserved
Recovered + Semantic Drift
Not Recovered
Escalated
```

---

## Figure 6 — Reliability vs Latency

Scatter/Pareto.

---

## Figure 7 — Ablation by failure type

component removal에 따라 어떤 failure가 증가했는지 표현.

---

# 17. Raw record에 반드시 저장해야 하는 필드

각 run row에 최소 다음을 남긴다.

```text
run_id
case_id
repeat_id
method
split

query
query_condition
terminology_condition
complexity_condition
spatial_operator_condition
data_availability_condition
ambiguity_condition

gold_version
gold_hash

predicted_semantics
predicted_qec
validator_decision
validator_issue_codes
reviewer_decision

execution_attempted
execution_success
execution_error

returned_object_ids
returned_geometry_summary

semantic_correct
plan_valid
spatial_correct
evidence_correct

silent_spatial_failure

recovery_attempted
recovery_success
semantic_preserved
semantic_drift
repair_iterations
escalated

latency_by_stage
total_latency_ms

input_tokens
output_tokens
tool_calls

evidence_bundle

git_sha
model_name
model_version
dataset_snapshot
ontology_hash
feature_catalogue_hash
```

---

# 18. 중요한 파생 지표

다음 파생필드를 raw result에서 자동 생성한다.

```text
false_ready
false_block
silent_spatial_failure
execution_correctness_gap
semantic_preservation
full_success
```

수작업 입력 금지.

---

# 19. Full pipeline과 component experiment를 구분한다

현재 파일럿처럼:

```text
semantic component
validator component
radius component
```

를 별도로 측정할 수 있다.

그러나 최종 논문에서는 반드시:

```text
P1 Full Marine GeoLLM
```

의 end-to-end run도 포함한다.

Component-level result를 합쳐서 Full Pipeline 성능인 것처럼 계산하면 안 된다.

---

# 20. BLOCK / CLARIFICATION을 실패로 단순 처리하지 않는다

다음 상황에서 올바른 정답 행동이 실행하지 않는 것일 수 있다.

예:

```text
missing geometry
data unavailable
permission denied
irreducible ambiguity
invalid distance
```

GOLD expected behavior가:

```text
BLOCK
NEEDS_USER_INPUT
HITL
```

이라면 실제 시스템이 안전하게 멈춘 것은 correct behavior다.

따라서:

```text
Safe Abstention Accuracy
```

를 별도 측정한다.

---

# 21. 실험 종료 시 자동 분석 보고서

다음 파일을 자동 생성한다.

```text
results/<run_id>/reports/

RQ1_condition_effectiveness.md
RQ2_error_detection.md
RQ3_execution_spatial_gap.md
RQ4_recovery_semantic_preservation.md
RQ5_reliability_cost.md
ablation_failure_analysis.md
final_results_summary.md
```

각 보고서는 반드시 다음 순서로 작성한다.

```text
1. 무엇을 비교했는가
2. 실제 결과
3. 가장 큰 차이
4. 예상과 다른 결과
5. 오류 사례
6. 통계검정
7. 논문에 쓸 수 있는 결론
8. 아직 주장하면 안 되는 것
```

---

# 22. Codex가 최종적으로 답해야 하는 5개 질문

실험 완료 후 `final_results_summary.md` 첫 부분에 반드시 다음 질문에 **실제 수치**로 답한다.

## Q1

> 어떤 조건에서 RAG, Ontology/KG, Tool Agent, QEC/Validator가 각각 효과적이었는가?

---

## Q2

> 어떤 오류는 LLM Review가 더 잘 잡았고, 어떤 오류는 Deterministic Validator가 더 잘 잡았는가? Hybrid는 추가 이점이 있었는가?

---

## Q3

> 각 방법에서 Execution Success와 실제 Spatial Correctness 사이의 gap은 얼마였는가? Silent spatial failure는 얼마나 발생했는가?

---

## Q4

> Recovery된 사례 중 원래 semantic intent를 보존한 비율은 얼마였는가? 실행은 성공했지만 semantic drift가 발생한 경우는 얼마나 있었는가?

---

## Q5

> Proposed framework가 얻은 신뢰성 향상을 위해 추가된 latency, token, tool-call, false block, human escalation 비용은 얼마였는가?

---

# 23. 논문의 성공 기준

다음과 같은 결론을 미리 강제하지 않는다.

```text
Proposed가 모든 지표에서 최고다.
Ontology가 RAG보다 항상 좋다.
Deterministic Validator가 LLM Review보다 항상 좋다.
Recovery는 항상 이득이다.
```

오히려 다음과 같은 조건부 발견을 찾는다.

```text
Ontology는 semantic gap이 큰 질의에서 효과가 큼.
RAG는 공식 용어 기반 표준 설명에서는 충분할 수 있음.
LLM Review는 모호한 의미 이상을 잡는 데 도움될 수 있음.
Deterministic Validator는 schema/CRS/tool errors에서 강할 수 있음.
Hybrid가 양쪽의 오류 coverage를 보완할 수 있음.
Execution Success만 보면 실제 공간정확도를 과대평가할 수 있음.
Recovery는 일부 오류는 복구하지만 semantic drift 위험이 있음.
Reliability 향상에는 latency/false block 비용이 존재함.
```

**실제 실험결과가 지지할 때만 이런 문장을 사용한다.**

---

# 24. Scientific Integrity

절대로 다음을 하지 않는다.

- GOLD 수정
- 불리한 case 삭제
- timeout 제외 후 성공률만 재계산
- BLOCKED_DATA를 success로 세기
- safe block을 일반 failure와 혼합
- spatial correctness를 LLM judge로 판정
- 동일 case 반복을 독립 sample로 사용
- baseline마다 다른 데이터 snapshot 사용
- baseline prompt를 의도적으로 불리하게 구성
- Proposed에만 추가 data/evidence를 제공
- 결과를 본 뒤 condition label을 유리하게 변경
- 실패한 recovery를 숨김
- semantic drift가 있는 recovery를 성공으로만 보고

---

# 25. 재현성

모든 최종 run에 다음을 기록한다.

```text
git_sha
git_dirty
benchmark_hash
gold_hashes
model/digest
temperature
prompt hashes
ontology/KG hashes
S-101 FC hash
capability registry hash
query template hash
DB snapshot
Python/package versions
container image
random seed
```

최종 paper run은 가능하면:

```text
git_dirty = false
```

인 clean commit/tag에서 수행한다.

---

# 26. 실행 순서

Codex는 다음 순서로 수행한다.

## Phase 1 — Audit

현재 GOLD, benchmark, production pipeline, baseline, evaluator 상태 확인.

## Phase 2 — Condition labeling

GOLD case에 영향을 주지 않는 별도 metadata로 query-condition 분류.

## Phase 3 — Baselines

B0~B4와 가능한 H 구성.

## Phase 4 — P0/P1

QEC+Validator와 Full Marine GeoLLM end-to-end 실행.

## Phase 5 — Error matrix

동일 fault set에 B4/P0/H 적용.

## Phase 6 — Spatial gap

ESR vs Spatial Correctness 분석.

## Phase 7 — Recovery

bounded recovery + semantic preservation 평가.

## Phase 8 — Cost

latency/tokens/tool calls/false block 분석.

## Phase 9 — Ablation

failure-type별 module contribution 분석.

## Phase 10 — Statistics

paired CI/McNemar 등.

## Phase 11 — Tables/Figures

RQ 중심 표·그림 자동 생성.

---

# 27. 우선 구현 목표

모든 것을 한 번에 하지 말고 먼저 아래 5개가 실제 산출되는지 확인한다.

```text
1. RQ1 condition-stratified metric table
2. RQ2 LLM Review vs Deterministic vs Hybrid error matrix
3. RQ3 Execution Success vs Spatial Correctness table
4. RQ4 Recovery + Semantic Preservation table
5. RQ5 Reliability vs Latency/False Block table
```

이 5개 표가 실제 GOLD 기반 숫자로 생성되지 않으면 논문 Results 프레임워크는 완료된 것이 아니다.

---

# 28. 최종 Results 경로

최종 결과는 반드시 다음에서 확인 가능하게 한다.

```text
research/marine_geollm_scie/results/latest/tables/
research/marine_geollm_scie/results/latest/figures/
research/marine_geollm_scie/results/latest/reports/
research/marine_geollm_scie/results/latest/manifest.json
```

추가로 다음 파일을 생성한다.

```text
research/marine_geollm_scie/results/latest/reports/SCIE_RESULTS_INTERPRETATION.md
```

여기에는 반드시:

```text
가장 강한 연구발견 5개
가장 예상 밖의 결과 3개
실패 사례 유형
Reviewer가 공격할 가능성이 높은 한계
추가 실험 필요 여부
현재 결과로 주장 가능한 문장
현재 결과로 주장하면 안 되는 문장
```

을 작성한다.

---

# 29. 완료 조건

다음 질문 모두에 GOLD 기반 실제 수치로 답할 때만 완료로 간주한다.

- 어떤 조건에서 어떤 기술이 효과적인가?
- 어떤 오류는 LLM Review가 잡고 어떤 오류는 Deterministic Validator가 잡는가?
- Execution Success와 Spatial Correctness gap은 얼마인가?
- Recovery 후 semantic intent가 얼마나 보존되는가?
- Reliability 개선 비용은 얼마인가?
- Ablation에서 각 component가 어떤 failure type을 줄이는가?
- 결과가 holdout에서도 유지되는가?
- 통계적으로 차이가 있는가?
- 재현 가능한가?

단순히 R1~R7 파일이 생성됐다는 이유로 완료 처리하지 않는다.
