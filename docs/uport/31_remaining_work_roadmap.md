# Marine GeoLLM 현재 상태와 다음 작업

기준일: 2026-09-25
재개 원칙: 다음 접속에서는 아래 `P0 미비점`부터 처리한다.

## 2026-09-25 웹·DB 연동 및 현재 상태 검증

- DB, backend, tile-server, eta-history-collector 컨테이너가 실행 중이다.
- 웹 `/`, `/uport/`, `/health`가 HTTP 200이다. `/health`는 API 생존 확인만 하므로 DB 연결 성공과 구분한다.
- 웹은 동일 출처 `/api/v1/uport/map/berths`를 통해 `S101_DB_URL`의 `gbhd_s101`에 연결한다. 부산 bbox `128.98,35.02,129.18,35.18`에서 169건, 인천 bbox `126.50,37.35,126.70,37.55`에서 128건의 S-101 2.0 선석 GeoJSON을 반환했다. 잘못된 bbox와 과대 범위는 HTTP 422이다.
- DB 직접 조회: S-101 projection 787,102건, 사고 4,636건, RAG 8,413건 및 embedding 8,413건이다. 기존 체크포인트 중 이 수치만 이번에 재검증했으며 geometry validity/사고 관계 전체를 다시 검사한 것은 아니다.
- `POSTGIS_URL`은 `marine_geo`(KHOA 지명 테이블 존재), `S101_DB_URL`은 `gbhd_s101`을 사용한다. README의 단일 DB 예시를 실제 역할에 맞게 수정했다. 직접 psycopg2 접속과 호환되는 `postgresql://`를 문서화했다.
- `scripts/check_web_db_connection.py`를 추가했다. 호스트와 컨테이너 내부 모두 7개 점검이 통과했다. `start_geollm.bat`에 동일 점검을 추가했으며 명령 자체를 실제 실행했다. 배치 전체와 LiDAR UI 기동은 이번에 실행하지 않았다.
- 실행 이미지에는 pytest와 최신 테스트가 없었다. 현재 컨테이너에 pytest 8.4.2/pytest-asyncio 0.23.8을 설치하고 최신 tests를 복사하여 검증했다. Compose에는 tests read-only mount를 추가했다. 현재 컨테이너를 재생성하지 않았으므로 mount는 다음 recreate부터 적용되며, 개발 의존성의 영속 반영은 `up -d --build backend`가 필요하다.
- Browser 연결 목록이 비어 있어 실제 브라우저 렌더링·지도 조작은 미검증이다. HTTP/API 통과를 화면 검증 완료로 간주하지 않는다.

### 실제 질의 검증과 남은 문제

- `/api/v1/tasks`에 `이 해역의 통항위험이 높은 이유를 설명해줘`와 부산/인천 bbox를 각각 전달했다. 두 질의 모두 `COMPLETED`, `Navigation Risk Analysis Agent`, 통항자료 확보 성공이다. 최근접 거리는 부산 506.3m, 인천 751.6m이다.
- 두 응답 모두 `parsed_intent.intent_type=KNOWLEDGE_SEARCH`와 `route_plan.intent=ANALYSIS`가 불일치한다(P0-2 재현). `estimated_accuracy=0.868`은 gold-label 정확도가 아니다.
- 지도 문맥 없이 같은 질의를 보내면 `BLOCKED`, 항만 null, 통항자료 없음으로 응답한다. 임의 항만은 선택하지 않지만 위치 누락을 `NEEDS_CLARIFICATION`으로 설명하는 후속 개선이 필요하다.
- `조석예보란`은 정의 응답으로 완료됐다. 정의형도 상위 `KNOWLEDGE_SEARCH`와 최종 `DEFINITION`의 메타데이터 관계를 함께 정리해야 한다.
- 전국 항만 확대, 최근접 거리 제한, 명시 항만명과 지도 문맥의 우선순위, 사고·수심·기상 결합은 아직 미완료이다. 실시간 AIS는 provider 미설정 시 503을 반환하는 계약이며 선석/과거 통항자료가 실시간 관측을 대신하지 않는다.
- P1 코드 확인: `query_candidate_broker`는 여전히 `dry_run_no_execution_change`와 Ollama 필요 여부만 기록한다. 후보 점수 결합·calibration·gold-label 비교 실험을 완료한 상태가 아니며 QLoRA 착수 조건도 이번에 입증되지 않았다.
- 실제 질의 응답은 ignored `outputs/runtime-check/`에 저장했다. 기존 변경이 있던 `data/feedback/query_quality_issues.jsonl`과 이번 검증이 추가한 런타임 기록은 소스 커밋에서 제외한다.

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
   - 2026-09-25: 인천 지도 중심, 명시적 항만명, 지도 문맥 없음, 통항 실행 불가(mock exception) 4개 케이스를 추가했다. 실제 DB 테이블을 제거한 장애 실험은 수행하지 않았다.
   - 컨테이너에서 `python -m pytest tests/unit/test_definition_router.py tests/unit/test_navigation_risk_routing.py tests/unit/test_uport_map.py -q`: **23 passed**, deprecation warning 9개.
   - Compose `config --quiet`, `git diff --check` 통과. 전체 프로젝트 테스트는 실행하지 않았으므로 후속 라우팅 변경에 필요한 추가 회귀 범위는 확인해야 한다.

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

### Shadow-mode 후보 점수 결합 실험

Ollama에는 자유 의도 생성을 맡기지 않고 규칙·슬롯·registry가 생성한 동일 후보 2~4개를 전달한다. 각 후보의 의도·문맥 적합도, 필요 근거, 누락 슬롯, reason code를 구조화해 반환받는다.

```text
combined_score =
    w_rule      * deterministic_route_score
  + w_ollama   * calibrated_ollama_score
  + w_registry * registry_readiness
  + w_context  * context_completeness
```

- 초기에는 `w_ollama`를 낮게 제한하고 어떤 가중치도 고정된 정답으로 간주하지 않는다.
- Ollama 점수는 validation set에서 calibration한 뒤 규칙 점수와 비교한다.
- 실제 실행은 기존 안전 경로를 유지하고 shadow 결과만 trace와 평가 저장소에 기록한다.
- 규칙·Ollama·혼합 순위, 최종 실행 순위, disagreement type을 보존한다.
- 필수 슬롯·권위 근거가 없거나 점수원이 크게 충돌하면 실행에 반영하지 않는다.
- 규칙 단독, Ollama 단독, 단순 가중합, calibration 결합, registry/context gate 결합을 비교한다.
- 오류는 정의↔실행, 검색↔분석, 지시어 해소, 복합 근거 선택, 불필요 clarification, 위험한 과잉 실행으로 분류한다.

### 연구 가설과 논문화 조건

연구 가설은 "도메인 규칙, authoritative registry readiness, 공간·대화 문맥, 로컬 LLM 후보 재평가를 결합하면 단일 규칙 또는 단일 LLM보다 해양 GeoLLM의 모호·복합 의도 라우팅을 더 안전하고 정확하게 수행할 수 있다"이다.

논문 기여로 성립하려면 다음이 필요하다.

- 재현 가능한 marine geospatial ambiguity benchmark와 annotation guideline
- 규칙, embedding router, Ollama, 결합 방식의 공정한 baseline 비교
- 각 점수원과 gate를 제거하는 ablation study
- calibration error, selective prediction, clarification 품질, 심각 오류율 평가
- 미관측 항만·용어에 대한 domain generalization 평가
- latency, 로컬 배포 비용, privacy, failure-safe 동작 분석
- QLoRA 전후 비교와 사실 권위 분리 검증
- seed, prompt, model, registry snapshot, lineage를 포함한 재현성 패키지

논문 작업명은 `Authority-Grounded Hybrid Intent Routing for Maritime GeoLLM`으로 두며, 실제 제목과 기여 주장은 benchmark 결과 후 확정한다.

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

1. `python scripts/check_web_db_connection.py`로 웹/API/DB 연결 재확인
2. 컨테이너 재생성 시 `docker compose -f docker/docker-compose.yml up -d --build backend`로 개발 의존성·최신 tests mount 반영
3. P0-1 잔여 관련 회귀 범위를 확인하고 P0-2 `parsed_intent`/최종 경로/도구 메타데이터 불일치 수정
4. 수정 후 컨테이너 테스트와 부산/인천/명시 항만/지도 문맥 누락 실제 `/api/v1/tasks` 재검증
5. 지도 문맥 누락 clarification 및 명시 위치 우선순위·최근접 거리 제한 확정
6. P0-3 전국 항만 resolver 확장 및 브라우저 연결 후 화면 검증
7. P0-4 사고·수심·기상 근거 결합
8. Ollama ambiguity resolver를 shadow mode로 구현하고 gold-label 평가
9. prompt 보완 후에도 남는 반복 오류가 확인된 경우에만 QLoRA 실험

## 검증 시 주의사항

- 2023년 통항자료를 현재 실시간 위험도라고 표현하지 않는다.
- `estimated_accuracy`는 gold-label 정확도가 아니라 라우팅·근거 기반 추정치다.
- 고시 polygon이 `pending_geometry_ingest`이면 적용 공간을 확정했다고 표현하지 않는다.
- 지도 문맥과 명시 항만명이 모두 없으면 특정 항만을 임의 선택하지 않는다.
