너는 D:\An_GeoLLM 프로젝트의
“Marine GeoLLM Continuous Learning, Agent Expansion,
Benchmark & Self-Validation Framework”
개발 책임자다.

목표는 해양수산부 범용 GeoLLM이 다양한 실제 질의를 지속적으로 처리하면서

1. 어떤 질의를 잘 처리하는지 측정하고,
2. 어떤 질의에서 실패하는지 자동 분류하고,
3. 실패 원인을 Ontology / KG / Slot / Registry / Data / Tool / Agent / RAG / Evidence 수준에서 진단하고,
4. 기존 기능 보강으로 해결 가능한 경우 최소 변경으로 개선하고,
5. 반복적으로 독립된 capability가 필요한 경우에만 새로운 전문 Agent를 제안·구현하고,
6. 변경 전후 정확도를 Marine GeoLLM Benchmark로 비교하고,
7. 충분한 검증을 통과한 변경만 운영 후보로 승격하는

지속적 개선 체계를 구축하는 것이다.

이 Framework를 이하
“Marine GeoLLM Learning & Validation Loop”
라고 한다.

==================================================
0. 절대 원칙
==================================================

기존 정상 기능, DB, embedding, ontology, registry, KG,
Agent, Tool, RAG 자료를 우선 보존한다.

질의 한두 개가 실패했다고 새 Agent를 만들지 않는다.

실패 원인을 다음 우선순위로 진단한다.

1. Query Normalization
2. Slot Extraction
3. Semantic / Ontology Resolution
4. KG relation / Graph-RAG
5. Location Resolution
6. Data Binding
7. Registry Mapping
8. Query Template
9. Tool capability
10. Agent capability
11. RAG retrieval
12. Evidence assembly
13. Response generation / UX

가장 작은 수정으로 해결 가능한 문제는
상위 단계에서 수정한다.

예:

용어사전 문제인데 새 Agent 생성 금지.
Slot 문제인데 새 Tool 생성 금지.
DataBinding 문제인데 LLM prompt 수정으로 숨기지 않는다.
QueryTemplate 문제인데 새 Agent 생성 금지.

새 Agent 추가는 다음 조건을 모두 만족할 때만 허용한다.

- 기존 Agent capability로 표현하기 어렵다.
- 독립된 입력/출력 계약을 가진다.
- 서로 다른 질의 여러 개에서 반복된다.
- 독립적인 데이터 또는 Tool 조합이 필요하다.
- 최소 Benchmark 사례가 존재한다.
- 기존 Agent 확장보다 응집도가 높다.
- Orchestrator와 QueryExecutionContext 계약을 준수할 수 있다.

운영 경로에서는 mock 결과를 사실처럼 반환하지 않는다.

자동 개선 결과를 production에 자동 반영하지 않는다.

Ontology / KG / Registry 자동 변경은
proposal 생성까지만 허용한다.

사람의 승인 없이:
- registry 자동 병합 금지
- ontology VERIFIED 승격 금지
- executable 자동 승격 금지
- Agent 운영 활성화 금지
- 모델 weight 운영 반영 금지

==================================================
1. 전체 개선 Loop
==================================================

다음 Pipeline을 구현한다.

User / Benchmark Queries
        ↓
Query Evaluation Runner
        ↓
Execution Trace 수집
        ↓
Expected vs Actual 비교
        ↓
Failure Classifier
        ↓
Root Cause Analyzer
        ↓
Remediation Planner
        ↓
┌───────────────────────────────┐
│ Dictionary / Ontology 개선   │
│ KG / Registry 개선           │
│ Slot / Context 개선          │
│ Data Binding 개선            │
│ Tool / QueryTemplate 개선    │
│ Agent capability 개선        │
│ 신규 Agent 제안              │
│ RAG / Evidence 개선          │
└───────────────────────────────┘
        ↓
Patch Candidate
        ↓
Unit / Contract / Integration /
Benchmark / Safety Tests
        ↓
Before vs After 비교
        ↓
Improvement Proposal
        ↓
Human Approval
        ↓
승인 후 Merge Candidate

==================================================
2. Marine GeoLLM Benchmark 구조
==================================================

다음 Benchmark 체계를 구축한다.

tests/benchmark/

queries/
expected/
fixtures/
negative/
conversation/
cross_domain/
regression/
reports/

Benchmark case schema를 정의한다.

예:

{
  "case_id": "NAV_RADIUS_001",
  "query": "부산항 입구 3km 이내 위험객체를 찾아줘",

  "category": "spatial_derived_concept",

  "domains": [
    "navigation_safety"
  ],

  "expected_semantics": {
    "surface_term": "위험객체",
    "derived_concept": "navigation_hazard_object"
  },

  "expected_slots": {
    "location_text": "부산항 입구",
    "distance_m": 3000
  },

  "expected_feature_classes": [
    "Wreck",
    "Obstruction",
    "UnderwaterAwashRock"
  ],

  "expected_analysis_type": "feature_search_by_radius",

  "expected_agent": "SpatialAnalysisAgent",

  "expected_behavior": "EXECUTE",

  "expected_status": [
    "SUCCESS",
    "SUCCESS_EMPTY"
  ],

  "forbidden_behavior": [
    "MOCK_RESULT",
    "UNNECESSARY_CLARIFICATION",
    "INVENTED_FEATURE"
  ]
}

Golden Answer 문장 자체보다
Golden Execution을 중심으로 평가한다.

==================================================
3. 질의 분류 Benchmark
==================================================

최소 다음 카테고리를 지원한다.

A. Semantic
- 용어
- 동의어
- 자연어 표현
- Derived Concept

B. Spatial
- radius
- nearest
- within
- contains
- intersects
- overlap
- route proximity

C. Standard / RAG
- S-100
- S-101
- DCEG
- Feature Catalogue
- 법령
- 고시
- 표준

D. Traffic
- AIS
- V-PASS
- route
- density
- traffic pattern

E. Accident
- 사고 위치
- 사고 유형
- 사고 통계
- 공간관계
- 사고 다발해역

F. Observation
- 조위
- 조류
- 파랑
- 기상
- 관측
- 예보

G. Fisheries
- 어장
- 양식장
- 어초
- 조업
- 규제

H. Marine Environment
- 보호구역
- 오염
- 민감지역
- 투기장

I. Port / Logistics
- 항만
- 선석
- 정박
- 물류
- 통항

J. Marine Spatial Planning
- 입지
- 이용구역
- 개발제약
- 해상풍력

K. Cross-domain
- 환경 + 항로
- 수산 + 항만
- 사고 + AIS
- 해상풍력 + 어장 + 항로 + 보호구역

L. Conversation
- 후속질의
- 범위 변경
- 대상 변경
- 필터 추가
- 제외 조건

M. Exception
- 잘못된 단위
- 음수 거리
- 존재하지 않는 위치
- 데이터 없음
- 권한 부족
- 존재하지 않는 Feature
- 모호한 질의
- 시스템 실패

==================================================
4. 평가 결과 Schema
==================================================

각 질의마다 최소 다음을 저장한다.

{
  "case_id": "...",

  "semantic_result": {},
  "slot_result": {},
  "ontology_result": {},
  "kg_result": {},
  "data_binding_result": {},
  "tool_binding_result": {},
  "route_plan": {},
  "validator_result": {},
  "task_results": [],
  "evidence_bundle": {},
  "final_response": {},

  "metrics": {
    "intent_correct": true,
    "slot_correct": true,
    "concept_correct": true,
    "feature_binding_correct": true,
    "data_binding_correct": true,
    "tool_routing_correct": true,
    "execution_correct": true,
    "citation_valid": true,
    "unsafe_execution": false,
    "mock_leakage": false
  },

  "execution_trace_id": "...",

  "failure_categories": []
}

==================================================
5. Failure Taxonomy
==================================================

다음 표준 Failure Code를 정의한다.

QUERY_NORMALIZATION_ERROR
TERM_RESOLUTION_ERROR
SLOT_EXTRACTION_ERROR
LOCATION_RESOLUTION_ERROR
CONCEPT_RESOLUTION_ERROR

ONTOLOGY_MAPPING_MISSING
ONTOLOGY_MAPPING_WRONG
KG_EDGE_MISSING
KG_EDGE_UNVERIFIED
KG_OVER_EXPANSION

FEATURE_MAPPING_MISSING
FEATURE_CODE_MISMATCH

DATASET_NOT_REGISTERED
DATA_LAYER_NOT_FOUND
DATA_SCHEMA_MISMATCH
DATA_VERSION_MISMATCH

QUERY_TEMPLATE_MISSING
QUERY_TEMPLATE_ERROR

TOOL_NOT_REGISTERED
TOOL_CAPABILITY_MISMATCH
TOOL_EXECUTION_FAILED

AGENT_ROUTING_ERROR
AGENT_CAPABILITY_GAP

RAG_RETRIEVAL_ERROR
RAG_NO_EVIDENCE
RAG_CITATION_ERROR

EVIDENCE_MISSING
EVIDENCE_CONTRADICTION

UNNECESSARY_CLARIFICATION
MISSING_CLARIFICATION

UNSAFE_EXECUTION
MOCK_LEAKAGE
HALLUCINATED_DATA
UNSUPPORTED_CLAIM

CONVERSATION_CONTEXT_LOSS

UNKNOWN_FAILURE

Failure Code는
실행 trace와 실제 evidence를 기반으로 결정한다.

LLM의 추측만으로 failure category를 확정하지 않는다.

==================================================
6. Root Cause Analyzer
==================================================

실패 질의를 발견하면 다음 질문 순서로 분석한다.

1.
질문이 올바르게 정규화되었는가?

2.
사용자 표현이 올바른 canonical term으로 연결되었는가?

3.
필수 slot이 추출되었는가?

4.
Derived Concept가 맞는가?

5.
Ontology / KG에 필요한 mapping이 있는가?

6.
Feature Class와 Feature Instance를 혼동하지 않았는가?

7.
올바른 DataLayer가 선택되었는가?

8.
실제 DB schema와 registry가 일치하는가?

9.
적절한 QueryTemplate가 존재하는가?

10.
Tool이 해당 연산을 지원하는가?

11.
기존 Agent가 해당 capability를 지원하는가?

12.
RAG 검색이 필요한 질의인가?

13.
필요한 Evidence가 존재하는가?

14.
실패 상태가 정상적으로 사용자에게 전달되었는가?

분석 결과:

{
  "root_cause": "...",
  "root_cause_layer": "...",
  "confidence": 0.0,
  "supporting_trace": [],
  "recommended_fix_level": "..."
}

==================================================
7. Remediation Hierarchy
==================================================

문제 해결은 다음 순서를 따른다.

LEVEL 1
Dictionary / Alias 수정

LEVEL 2
Slot Extractor / Normalizer 수정

LEVEL 3
Ontology mapping 추가

LEVEL 4
KG edge / metadata 후보 추가

LEVEL 5
Registry mapping 추가

LEVEL 6
DataBinding Adapter 수정

LEVEL 7
QueryTemplate 추가 또는 수정

LEVEL 8
Tool Capability 확장

LEVEL 9
기존 Agent Capability 확장

LEVEL 10
신규 Agent 제안

LEVEL 11
모델 개선 / 학습 후보

항상 가장 낮은 LEVEL에서 해결 가능한지 먼저 확인한다.

==================================================
8. 신규 Agent 자동 제안 기준
==================================================

새 Agent는 자동 생성하지 말고 먼저 Proposal을 생성한다.

파일:

outputs/agent_learning/
agent_capability_proposals.jsonl

Schema 예:

{
  "proposal_id": "...",

  "suggested_agent":
    "MarineEnvironmentAnalysisAgent",

  "reason":
    "환경 관련 복합 공간분석 질의에서 기존 Agent 조합으로 반복 실패",

  "supporting_cases": [
    "...",
    "...",
    "..."
  ],

  "failure_pattern": "...",

  "required_inputs": [],

  "required_data": [],

  "required_tools": [],

  "required_analysis_types": [],

  "expected_output_schema": {},

  "overlap_with_existing_agents": [],

  "why_existing_agent_extension_is_insufficient": "...",

  "benchmark_cases_required": [],

  "status": "PROPOSED"
}

신규 Agent 생성 조건:

지원 Benchmark 질의 최소 5개 이상.

동일 root cause가 서로 다른 질의에서 반복될 것.

기존 Agent에 단순 capability 하나 추가하는 것보다
독립된 책임이 명확할 것.

승인되지 않은 Agent를
agent_registry.yaml의 executable Agent로 자동 등록하지 않는다.

==================================================
9. 승인 후 Agent 구현
==================================================

사람이 APPROVED로 변경한 Agent proposal만 구현 후보로 사용한다.

Agent는 반드시 공통 계약을 따른다.

Input:

QueryExecutionContext
ValidatedTaskPlan

Output:

TaskResult
EvidenceBundle
warnings
execution_trace

표준 경로:

QueryExecutionContext
→ ExecutionValidator
→ PASS
→ Agent
→ Registered Tool
→ Data
→ TaskResult
→ EvidenceBundle
→ Orchestrator

Agent 내부에서 원문 질문을 다시 자유롭게 해석하지 않는다.

Agent 내부 임의 mock fallback 금지.

Agent 내부 미등록 SQL 생성 금지.

==================================================
10. 지속적 Ontology / KG 학습
==================================================

Benchmark 실패와 실제 질의에서
새로운 용어 또는 concept 후보가 발견될 수 있다.

자동 반영하지 말고 Proposal을 생성한다.

outputs/ontology_learning/

term_mapping_proposals.jsonl
concept_proposals.jsonl
relation_proposals.jsonl
feature_mapping_proposals.jsonl
data_binding_proposals.jsonl

각 proposal에는 다음을 기록한다.

query_examples
candidate_mapping
existing_mapping
supporting_documents
supporting_KG_paths
supporting_data
confidence
conflicts
review_status

상태:

PROPOSED
REVIEW_REQUIRED
APPROVED
REJECTED
DEFERRED

APPROVED 상태만
Phase 8.3 승인 병합 단계의 입력 후보가 될 수 있다.

==================================================
11. RAG 기반 Self-Learning
==================================================

새로운 문서에서 발견된
Feature / Concept / Law / Standard relation은

자동 VERIFIED 처리하지 않는다.

다음 관계 후보만 만든다.

definedBy
supportsConcept
authorizedBy
constrainsActivity
appliesToArea
describesFeature

문서 chunk와 relation proposal 사이에는
반드시 citation과 source locator가 있어야 한다.

==================================================
12. Accuracy 개선 전략
==================================================

LLM prompt를 무조건 수정하지 않는다.

문제 원인을 구분한다.

예:

“침선”을 Wreck으로 못 찾음
→ Dictionary / ontology 문제

“3km”를 못 읽음
→ Slot 문제

Wreck를 찾았는데 DB 조회 실패
→ DataBinding / Template / Tool 문제

DB 결과는 정상인데 설명이 잘못됨
→ Evidence / Response 문제

모든 실패를 LLM Prompt 변경으로 해결하려 하지 않는다.

==================================================
13. 선택적 모델 학습 / Fine-Tuning 후보
==================================================

모델 weight 변경은 최후 단계다.

다음 조건을 만족할 때만 학습 후보를 만든다.

- Dictionary/Rules/Ontology로 해결하기 어려움.
- 충분한 실제 학습 사례가 존재함.
- 반복되는 semantic classification 문제임.
- 데이터 품질 검증 완료.
- train / validation / test 분리 가능.
- 개인정보·보안·저작권 검토 완료.

자동 fine-tuning 실행 금지.

대신:

outputs/model_learning/
training_candidate_report.md
training_dataset_candidate.jsonl

을 생성한다.

training / validation / test leakage를 방지한다.

Benchmark test set을
학습 데이터로 자동 재사용하지 않는다.

==================================================
14. Ollama / Local LLM 평가
==================================================

현재 Ollama를 사용하는 경우
LLM 자체의 역할도 평가 가능하게 한다.

모델별:

model_name
model_version
temperature
system_prompt_version
structured_output_success
latency
semantic_accuracy
slot_accuracy
routing_accuracy

를 기록한다.

가능하면 deterministic evaluation에서는
temperature를 낮게 설정한다.

하지만 모델 출력 정확도와
DB/Tool 실행 정확도를 분리해서 평가한다.

==================================================
15. 자체 검증(Self-Validation)
==================================================

Codex가 변경을 만들면 반드시 다음 검증을 수행한다.

A. Unit Test

B. Schema Contract Test

C. Ontology Validation

D. Registry Integrity Test

E. QueryExecutionContext Contract Test

F. Agent Routing Test

G. Spatial DB Test

H. RAG Retrieval Test

I. Evidence Validation

J. Negative / Exception Test

K. Conversation Context Test

L. Marine GeoLLM Benchmark Regression

변경 전:

baseline metrics

변경 후:

candidate metrics

를 비교한다.

==================================================
16. 개선 승인 기준
==================================================

변경은 다음 조건을 모두 만족할 때만
Improvement Candidate가 된다.

기존 Benchmark regression 없음.

새로운 Target Case 개선.

unsafe_execution 증가 없음.

mock_leakage = 0.

hallucinated_data = 0.

citation_validity 저하 없음.

실제 DB schema contract 통과.

Ontology / Registry integrity 통과.

승인 기준을 통과하지 못하면
변경을 자동 확정하지 않는다.

==================================================
17. Metric Dashboard
==================================================

다음 KPI를 계산한다.

Semantic Accuracy
Intent Accuracy
Slot Exact Match
Slot F1

Ontology Resolution Accuracy
Derived Concept Accuracy
Feature Mapping Accuracy

Data Binding Accuracy
Tool Routing Accuracy
Agent Routing Accuracy

Execution Success Rate

Clarification Precision
Clarification Recall

Citation Validity
Evidence Coverage

Conversation Context Retention

Mock Leakage Rate
Unsafe Execution Rate
Unsupported Claim Rate

Cross-domain Success Rate

End-to-End Success Rate

가장 중요한 Safety KPI:

Mock Leakage Rate = 0 목표
Unsafe Execution Rate = 0 목표
Unsupported Claim Rate = 0 목표

==================================================
18. Metamorphic Testing
==================================================

같은 의미의 다양한 표현에서
동일한 실행 의미가 유지되는지 검사한다.

예:

“부산항 입구 3km 이내 침선을 찾아줘”

“부산항 입구에서 반경 3km 안에 있는 침선 보여줘”

“부산항 입구 주변 3000m 이내 Wreck 검색”

다음은 동일해야 한다.

location
distance_m
feature class
analysis type
DataBinding

다음 표현도 테스트한다.

띄어쓰기 변형
한글/영문 혼용
단위 변형
존댓말
구어체
짧은 질의
후속질의

==================================================
19. Adversarial / Exception Testing
==================================================

다음을 반드시 자동 테스트한다.

잘못된 단위:
“3kg 이내 침선”

음수:
“-3km”

지나친 범위:
“100000km”

없는 Feature:
“ABCMarineObject”

없는 법령

없는 위치

권한 없는 문서

DB timeout

Vector DB unavailable

Embedding model mismatch

KG relation CANDIDATE only

Data Registry mismatch

Tool Registry mismatch

Agent failure

결과 0건

이 모든 경우 Mock 결과 생성 금지.

==================================================
20. Cross-domain Learning
==================================================

다음 복합 질의를 별도로 평가한다.

“해상풍력 후보지와 주요 어장, 항로,
보호수역이 충돌하는 지역을 찾아줘.”

필요 Domain:

marine spatial planning
fishery
navigation
environment

기존 Agent들을 병렬 조합할 수 있다면
새 Agent를 생성하지 않는다.

새로운 Agent가 필요한지는
반복되는 capability gap을 통해 판단한다.

==================================================
21. Conversation Learning
==================================================

후속 질의 테스트:

Q1:
부산항 입구 3km 이내 위험객체를 찾아줘.

Q2:
침선만 보여줘.

Q3:
5km로 늘려줘.

Q4:
그중 사고가 있었던 객체만 남겨줘.

각 단계에서 QueryExecutionContext revision을 관리한다.

사용자가 바꾸지 않은 값은 유지한다.

location 유지.
context 유지.
derived concept 의미 유지.

변경한 filter / distance만 갱신한다.

==================================================
22. Execution Trace 학습
==================================================

각 질의의 실행 trace를
개선 자료로 활용한다.

단:

private reasoning이나 chain-of-thought를 저장하지 않는다.

저장 대상:

module_name
input schema
output schema
selected IDs
state transitions
tool calls
DB result counts
evidence IDs
error codes
timing
status

이 구조화된 trace를 이용하여
실패 위치를 탐지한다.

==================================================
23. 자동 분석 Report
==================================================

매 Benchmark 실행 후 생성:

reports/benchmark/latest/

benchmark_summary.md
failure_analysis.md
root_cause_distribution.md
ontology_gaps.md
registry_gaps.md
agent_capability_gaps.md
rag_quality.md
evidence_quality.md
regression_report.md
improvement_candidates.md

또한 machine-readable 형식:

benchmark_results.jsonl
failure_cases.jsonl
improvement_proposals.jsonl

==================================================
24. Learning Queue
==================================================

개선해야 할 항목을 Priority Queue로 관리한다.

priority 산정:

frequency
× severity
× user_impact
× confidence

높은 예:

unsafe execution
hallucinated data
wrong legal citation
wrong spatial result

중간:

incorrect Agent routing
unnecessary clarification

낮은:

문체
UI 표현
비핵심 설명

==================================================
25. Phase별 개발
==================================================

Phase L1
Benchmark framework

Phase L2
Failure taxonomy + trace analyzer

Phase L3
Root Cause Analyzer

Phase L4
Ontology / Registry gap detector

Phase L5
Agent Capability Gap Analyzer

Phase L6
Remediation Planner

Phase L7
Self-validation runner

Phase L8
Before / After regression comparator

Phase L9
Human approval workflow

Phase L10
Continuous Improvement Dashboard

첫 실행에서는 L1~L3까지만 구현한다.

==================================================
26. 이번 첫 작업
==================================================

지금은 다음만 수행한다.

1.
현재 tests와 evaluation 관련 구조를 조사한다.

2.
Marine GeoLLM Benchmark schema를 설계한다.

3.
기존 질의를 재사용할 수 있는지 조사한다.

4.
최소 50개 seed benchmark case를 만든다.

이때 실제 DB 결과값을 임의로 만들지 않는다.

5.
Failure Taxonomy를 구현한다.

6.
Execution Trace에서 Failure Code를 추출하는
초기 Root Cause Analyzer를 구현한다.

7.
기존 코드에 최소 침습적으로 연결한다.

8.
Benchmark runner를 실행한다.

9.
현재 baseline 결과를 저장한다.

==================================================
27. 최소 Seed Benchmark
==================================================

50개 이상을 다음처럼 구성한다.

Simple Spatial
Derived Concept
Nearest / Within / Intersects
Standard / DCEG
Legal
AIS / V-PASS
Accident
Observation
Fishery
Environment
Port
Cross-domain
Conversation
Ambiguous
Invalid Input
Missing Data
No Evidence

실제 답을 알 수 없는 경우에는
정확한 객체 목록을 Golden Result로 만들지 않는다.

대신:

expected semantic
expected execution path
expected Agent
expected Tool
expected safety behavior

를 검증한다.

==================================================
28. 산출물
==================================================

docs/learning/

00_current_evaluation_inventory.md
01_benchmark_design.md
02_failure_taxonomy.md
03_root_cause_analysis.md
04_agent_expansion_policy.md
05_ontology_learning_policy.md
06_model_learning_policy.md
07_self_validation.md
08_continuous_improvement_architecture.md

tests/benchmark/
benchmark_cases_v1.jsonl

configs/evaluation/
failure_taxonomy.yaml
evaluation_metrics.yaml
agent_expansion_policy.yaml

scripts/
run_marine_benchmark.py
analyze_benchmark_failures.py
compare_benchmark_runs.py

outputs/learning/
baseline_metrics.json
failure_cases.jsonl
improvement_proposals.jsonl

==================================================
29. 최종 보고
==================================================

첫 실행 후 다음을 보고한다.

현재 Benchmark 가능 범위

실행한 질의 수

PASS 수
FAIL 수
BLOCKED 수
NOT_RUN 수

실패 유형 분포

Ontology gap

Registry gap

Data gap

Tool gap

Agent capability gap

RAG gap

Evidence gap

신규 Agent가 정말 필요한 영역

Agent 추가 없이 해결 가능한 영역

위험한 자동 fallback

Regression 위험

다음 Phase 권고

==================================================
30. 가장 중요한 판단 원칙
==================================================

이 Framework의 목표는

“질의가 들어올 때마다 Agent가 늘어나는 시스템”

을 만드는 것이 아니다.

목표는

“다양한 질의를 통해 시스템의 약점을 찾고,
가장 작은 적절한 계층을 보강하고,
새로운 독립 능력이 반복적으로 필요한 경우에만 Agent를 확장하며,
모든 변경을 Benchmark와 Evidence로 스스로 검증하는 GeoLLM”

을 만드는 것이다.

새로운 기능의 양보다
정확성, 추적 가능성, 안전성, 재현성을 우선한다.