# Marine GeoLLM 현재 상태와 다음 작업

기준일: 2026-09-22  
재개 원칙: 다음 접속에서는 아래 `P0 미비점`부터 처리한다.

## 완료된 작업

### 1. 정의형 질의의 범용 라우팅

- `란/이란/뜻/정의/의미/개념`을 정의 신호로 사용한다.
- 날짜·시간·장소·반경·조회/검색 같은 실행 슬롯이 있으면 정의형보다 실행형을 우선한다.
- 정의 근거는 `definition_term_registry`, 해양용어사전, S-101 catalogue를 통합한다.
- 실제 서비스에서 `조석예보란`, `S-101 Feature란`, `정박지란`을 검증했다.
- `9월 인천 조석예보`는 정의형이 아니라 외부 시계열 자료 요구 경로를 유지한다.

### 2. 훈련 데이터 확장 프레임워크

- canonical case 계약, Pydantic/JSON Schema 검증, registry ID/enum 정규화를 추가했다.
- component/end-to-end view, 실행 결과, EvidenceBundle, lineage, registry snapshot, prompt version을 포함한다.
- 중복·오염 검증과 소규모 dry run을 추가했다.
- 관련 파일은 `marine_geollm_training_schema.yaml`, `SEED_EXPANSION_PROMPT.md`, `Training Prompt.md`, `configs/training/`, `scripts/training/`, `training/`, `docs/training/`에 있다.

### 3. 통항위험 원인 분석 라우팅

- `통항/항행/항로 + 위험 + 왜/이유/원인/요인/설명/분석`을 `navigation_risk_explanation` 분석형으로 분류한다.
- `이 해역`은 현재 지도 중심에서 `place_geometry_registry`의 가장 가까운 항만으로 해소한다.
- 해당 항만의 `legal_notice_registry` 통항 고시와 PostGIS AIS/V-Pass 통항 집계를 결합한다.
- registry exact hit와 답변 정확도를 분리하고 의도 적합도, 근거 적합도, 분석 완결도를 별도로 낸다.
- 부산 지도 범위 실제 API 검증: 최근접 부산항 약 506.3m, 부산항 항법 규칙 1건, AIS/V-Pass 집계 성공.

## P0 미비점 — 다음 접속에서 먼저 처리

1. **회귀 테스트 완성**
   - `test_navigation_risk_routing.py`를 컨테이너에서 실행한다.
   - 인천 지도 중심, 명시적 항만명, 지도 문맥 없음, 통항 테이블 없음 케이스를 추가한다.
   - 정의형 테스트와 전체 관련 테스트를 다시 실행한다.

2. **응답 메타데이터 일관성 확인**
   - 재시작 후 `agent_name=Navigation Risk Analysis Agent`와 통항 도구 목록을 확인한다.
   - quality/citation/UI 어디에도 의미 정확도 100%가 표시되지 않는지 확인한다.
   - 상위 `parsed_intent`가 아직 `KNOWLEDGE_SEARCH`로 남는 현상을 `ANALYSIS`와 일치시킨다.

3. **최근접 항만 해소 범위 확장**
   - 현재 curated port point를 전국 authoritative gazetteer 또는 PostGIS 항만 레이어로 확대한다.
   - 최근접 거리가 과도하면 임계값을 두고 `NEEDS_CLARIFICATION`으로 전환한다.
   - 선택 feature/클릭 위치/viewport polygon/지도 중심의 우선순위를 계약으로 확정한다.

4. **위험 분석 근거 확장**
   - 사고이력, 수심/UKC, 기상·파고·조류를 같은 시공간으로 추가한다.
   - AIS/V-Pass 수치는 격자·월별 집계 합계이며 고유 선박 수가 아님을 UI와 답변에 표시한다.
   - 고시의 규제 존재를 실제 사고 확률로 해석하지 않는다.

5. **구조 리팩터링**
   - `graph.py` helper를 별도 모듈로 분리하고 정의 라우터의 중복 helper를 제거한다.
   - 전용 `navigation_risk_analysis_node`로 복합 분석을 분리한다.

## P1 Ollama 의도 보조와 QLoRA 보강

### 현재 확인된 한계

- `query_candidate_broker`는 Ollama 필요 여부만 계산하고 실제 호출·채택을 수행하지 않는다.
- 현재 모드는 `dry_run_no_execution_change`여서 Ollama 판단이 실행 경로를 바꾸지 않는다.
- Ollama semantic prior는 장소 유형 후보에 치우쳐 있고, route vector 초기화도 비활성화돼 있다.
- 기존 LLM fallback은 위치·거리·대상 슬롯 추출 중심이며 복합 분석과 필요 근거를 판단하지 않는다.

### 1단계: 기반 Ollama 보완

1. Pydantic `IntentAmbiguityJudgement` 계약을 만든다. 출력은 후보 의도, 선택 의도, 분석 유형, 문맥 참조, 필요 근거, 누락 슬롯, reason code, confidence로 제한한다.
2. 상위 route 점수 차이가 작거나, 지시어가 있거나, 정의·실행 표현이 섞이거나, 복수 근거 결합이 필요하거나, 규칙과 registry/KG가 충돌할 때만 호출한다.
3. trace에 `needed`, `called`, `used`, `accepted`, `rejected_reason`, `latency_ms`, `model_version`, `prompt_version`을 기록한다.
4. Ollama 출력은 후보일 뿐이며 registry ID, capability, 필수 슬롯 검증 후에만 최종 경로로 승격한다.
5. 타임아웃·JSON 오류·검증 실패 시 결정론 경로 또는 clarification으로 복귀한다.
6. 먼저 shadow mode로 gold-label과 비교하고 기준 통과 후 실행 경로에 반영한다.

### 2단계: 평가 데이터 축적

- 정의/실행 경계, 지시어와 대화 문맥, 복합 분석·근거 선택, 근거 부족, 유사 용어·부정·다중 의도를 hard case로 확대한다.
- 규칙 결과, Ollama 결과, 최종 채택 결과, 사용자 피드백을 함께 저장한다.
- 학습/검증/holdout을 lineage로 분리하고 합성 데이터 near-duplicate 오염을 차단한다.

### 3단계: QLoRA 적용 조건

QLoRA는 즉시 적용하지 않고 다음 조건을 모두 만족할 때 진행한다.

- prompt와 few-shot 보완 후에도 반복 오류가 남는다.
- 사람이 검수한 충분한 gold-label과 독립 holdout이 확보된다.
- 오류가 지식 부족이 아니라 의도·슬롯·근거 선택 패턴의 일관된 실패다.
- 기반 모델·라이선스·GPU·양자화·adapter 배포 및 rollback 절차가 확정된다.

학습 목표는 자유 답변이 아니라 intent/analysis type, 문맥 참조, 슬롯, EvidenceBundle 종류, clarification 판정으로 제한한다. 법령 내용, 좌표, 실제 통항량은 adapter가 생성하지 않고 registry·PostGIS·도구 결과로만 확정한다.

### QLoRA 평가·승격 기준

- 규칙 단독, 기반 Ollama, prompt 개선 Ollama, QLoRA adapter를 동일 holdout에서 비교한다.
- intent macro-F1, slot exact match/F1, evidence-selection F1, clarification precision/recall, schema validity, latency, fallback rate를 측정한다.
- 정의형→실행형, 분석형→문서검색형 같은 중대 오류를 별도 집계한다.
- 전체 점수뿐 아니라 중대 오류 감소와 미관측 도메인 일반화를 확인한다.
- adapter의 base model, dataset snapshot, prompt/schema version, 평가 보고서를 registry에 등록하고 즉시 rollback 가능하게 한다.

## 다음 실행 순서

1. `docker compose -f docker/docker-compose.yml restart backend`
2. `python -m py_compile services/orchestrator/graph.py`
3. `python -m pytest tests/unit/test_definition_router.py tests/unit/test_navigation_risk_routing.py -q`
4. 부산/인천 지도 범위로 실제 `/api/v1/tasks` 검증
5. P0-2 메타데이터 불일치 수정
6. P0-3 전국 항만 resolver 확장
7. P0-4 사고·수심·기상 근거 결합
8. Ollama ambiguity resolver를 shadow mode로 구현하고 gold-label 평가
9. prompt 보완 후에도 남는 반복 오류가 확인된 경우에만 QLoRA 실험

## 검증 시 주의사항

- 2023년 통항자료를 현재 실시간 위험도라고 표현하지 않는다.
- `estimated_accuracy`는 gold-label 정확도가 아니라 라우팅·근거 기반 추정치다.
- 고시 polygon이 `pending_geometry_ingest`이면 적용 공간을 확정했다고 표현하지 않는다.
- 지도 문맥과 명시 항만명이 모두 없으면 특정 항만을 임의 선택하지 않는다.
