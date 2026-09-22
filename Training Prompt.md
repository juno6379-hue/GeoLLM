D:\An_GeoLLM에 Marine GeoLLM Training Dataset Framework를 구축하라.

다음 두 파일을 기준 계약으로 사용한다.

1.
configs/training/marine_geollm_training_schema.yaml

2.
prompts/training/SEED_EXPANSION_PROMPT.md

이번 작업의 목적은 모델 fine-tuning을 바로 수행하는 것이 아니다.

목표는:

전문가 Golden Seed
→ Synthetic Candidate
→ 자동 검증
→ Human Approval
→ Approved Master Dataset
→ task-specific Training View

파이프라인을 먼저 구축하는 것이다.

기존 Marine Ontology, KG, Registry, Benchmark 구조를 재사용한다.

특히 다음 기존 자산을 조사하고 연결한다.

- marine_term_dictionary
- derived_concept_registry
- upper ontology
- MOF domain registry
- S-101 feature dictionary
- S-101 attribute dictionary
- agent capability registry
- tool registry
- data registry
- query template registry
- spatial layer registry
- legal notice registry
- execution validator
- semantic router
- feature resolver
- graph RAG
- existing benchmark/evaluation dataset

==================================================
1. Dataset Master Schema
==================================================

marine_geollm_training_schema.yaml을 canonical contract로 사용한다.

별도의 서로 다른 학습 데이터 구조를 중복 생성하지 않는다.

Master Case에는 최소:

input
expected_semantics
expected_slots
expected_routing
expected_data_bindings
expected_execution
expected_knowledge
expected_evidence
expected_answer
quality

가 있어야 한다.

Schema validation 코드를 작성한다.

==================================================
2. Seed Dataset
==================================================

training/seed/를 만든다.

도메인별 seed 파일:

navigation.yaml
standard.yaml
accident.yaml
traffic.yaml
legal.yaml
port.yaml
fisheries.yaml
environment.yaml
observation.yaml
cross_domain.yaml
exception.yaml
conversation.yaml

기존 benchmark/intent/context dataset에서
사람이 검증한 사례를 재사용할 수 있는지 조사한다.

자동으로 기존 데이터를 APPROVED 처리하지 않는다.

모든 신규 seed에는:

origin: human_seed
review_status: APPROVED 또는 REVIEW_REQUIRED

를 명시한다.

초기에는 최소 30개의 seed만 만든다.

각 seed는 자연어 답변이 아니라
Golden Execution을 중심으로 작성한다.

예:

query
→ semantic interpretation
→ slot
→ derived concept
→ feature
→ fast path
→ capability
→ resolver
→ agent
→ tool
→ data binding
→ execution status
→ evidence requirement

실시간 DB 결과 건수는 hard-code하지 않는다.

==================================================
3. Candidate Expansion
==================================================

SEED_EXPANSION_PROMPT.md를 사용하여
각 APPROVED seed에서 candidate를 생성할 수 있는 runner를 만든다.

생성 candidate는 반드시:

origin: synthetic_from_seed
review_status: CANDIDATE

로 저장한다.

자동 APPROVED 금지.

각 seed에서 생성:

- semantic paraphrase
- slot variation
- hard negative
- ambiguity/missing slot
- conversation follow-up
- cross-domain candidate

==================================================
4. Validation Pipeline
==================================================

candidate마다 다음 검사를 수행한다.

Schema Validation
Ontology Validation
Registry ID Validation
Tool Dependency Validation
Data Binding Validation
Execution Contract Validation
Semantic Consistency Validation

예:

navigation_hazard_object가 실제 derived concept인지 확인.

Wreck가 실제 S-101 Feature Class인지 확인.

postgis.dwithin가 Tool Registry에 존재하는지 확인.

SpatialAnalysisAgent가 실제 Agent Registry에 존재하는지 확인.

QueryTemplate가 존재하는지 확인.

없는 ID를 자동 생성하지 않는다.

==================================================
5. Hard Negative
==================================================

random negative를 만들지 않는다.

의미적으로 비슷하지만 실제로는 잘못된 후보를 만든다.

예:

질의:
“부산항 3km 이내 침선”

Positive:
- place_resolution
- s101_feature_resolution
- spatial_radius_search

Hard Negative:
- legal_search
- accident_density_analysis
- eo_segmentation

Hard Negative 이유를 metadata로 남긴다.

==================================================
6. Approved Master Dataset
==================================================

검증과 Human Review를 통과한 candidate만:

training/approved/marine_geollm_master_v1.jsonl

로 병합할 수 있게 한다.

자동 병합 금지.

approval state:

CANDIDATE
REVIEW_REQUIRED
APPROVED
REJECTED

를 유지한다.

==================================================
7. Training Views
==================================================

Master Dataset으로부터 자동으로 다음 view를 생성한다.

training/views/

fastpath_router.jsonl
capability_retriever.jsonl
slot_extractor.jsonl
planner.jsonl
execution_validator.jsonl
response_generator.jsonl

같은 사례를 사람이 각각 다시 작성하지 않는다.

==================================================
8. FastPath Router View
==================================================

입력:

query
+ optional semantic context

정답:

fast_path
required_capabilities

예:

{
  "input":
    "부산항 입구 3km 이내 침선을 찾아줘",

  "target": {
    "fast_path": "SPATIAL_PATH",
    "capabilities": [
      "place_resolution",
      "feature_resolution",
      "spatial_radius_search"
    ]
  }
}

==================================================
9. Capability Retriever View
==================================================

Contrastive / retrieval 학습이 가능하도록:

query
positive_capabilities
hard_negative_capabilities

를 생성한다.

가능하면:

resolver
tool
agent
dataset

각 capability type을 명확히 구분한다.

==================================================
10. Planner View
==================================================

입력:

QueryExecutionContext

정답:

resolver_chain
agent_chain
tool_chain
query_template

으로 구성한다.

아직 LoRA/QLoRA 학습은 수행하지 않는다.

==================================================
11. Benchmark 분리
==================================================

training에 사용되는 데이터와
Benchmark/Test 데이터를 엄격히 분리한다.

training/benchmark/
validation.jsonl
test.jsonl
holdout.jsonl

holdout 데이터는
candidate expansion이나 fine-tuning에 사용하지 않는다.

==================================================
12. Data Leakage 검사
==================================================

다음 leakage를 검사하는 script를 만든다.

exact duplicate
semantic near-duplicate
same seed family leakage
conversation continuation leakage

특히 같은 seed의 paraphrase가
train과 test에 나뉘지 않게 한다.

seed_family_id를 사용한다.

==================================================
13. Provenance
==================================================

각 case에:

case_id
parent_seed_id
seed_family_id
origin
created_by
created_at
schema_version
ontology_version
registry_version
review_status

를 기록한다.

==================================================
14. 산출물
==================================================

scripts/training/
validate_training_case.py
expand_seed_cases.py
build_training_views.py
check_dataset_leakage.py
approve_training_cases.py

training/
seed/
candidates/
approved/
views/
hard_negatives/
benchmark/

docs/training/
00_training_dataset_architecture.md
01_seed_policy.md
02_candidate_generation.md
03_validation_policy.md
04_training_views.md
05_future_finetuning_plan.md

==================================================
15. 이번 작업에서는 하지 말 것
==================================================

LoRA 실행 금지.
QLoRA 실행 금지.
Ollama 모델 weight 변경 금지.
기존 embedding 재생성 금지.
운영 Registry 자동 변경 금지.
Ontology 자동 VERIFIED 승격 금지.
Agent 자동 생성 금지.

==================================================
16. 첫 작업 완료조건
==================================================

1.
Master Schema 적용 완료

2.
Seed 30개 작성

3.
Candidate expansion runner 구현

4.
Validation pipeline 구현

5.
Training View 생성 확인

6.
Train/Test leakage 검사 구현

7.
샘플 3개 seed에 대해 candidate를 생성하여
CANDIDATE 상태로 저장

8.
결과 보고

최종 보고에는:

- 생성 파일
- 사용한 기존 Registry
- 발견한 taxonomy 충돌
- Seed 품질 문제
- 미등록 Capability
- validation failure
- 향후 FastPath / Capability Retriever 학습 가능성

을 정리하라.