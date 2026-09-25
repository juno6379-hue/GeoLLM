# GeoLLM 현재 상태와 다음 작업

## 2026-09-25 후속: 샘플 파이프라인 수정 및 실행 검증

최종 검증: 관련 단위 **177 passed**, 실행 중 API 계약 **13/13** (`contracts-v7.jsonl`). 웹 샘플 `live-presets-v5`는 100/100 완료 이벤트 수신, 관측 timeout 0; COMPLETED 13 / PARTIAL 13 / NEEDS_CLARIFICATION 66 / BLOCKED 8. 상태 분포는 의미 정확도가 아니다. 아래 이전 실행 수치는 중간 이력으로 보존한다.

최종 재현에서 남은 P0: 샘플 46의 portrayal 매칭 대신 정의 반환, 47/48의 지도 객체 문맥 없이 문서 완료, 76의 원천 좌표 처리 방식 질문을 공간 검색으로 분류, 84의 '위치 없이'를 사고 필터 '없, 부근'으로 조회. 이 사례와 불필요한 clarification을 다음 작업의 출력·문맥·부정 표현 회귀 기준으로 삼는다. 상세 전후 trace: `outputs/pipeline-comparison/final-review/stage_matrix.json`.

상세 판단 근거: [pipeline_repair_review_20260925.md](pipeline_repair_review_20260925.md). 사용자 우선순위는 공통 GeoLLM 샘플의 **의도→슬롯→후보→실행 계획→실제 도구→결과** 검증이다. 브라우저 미연결은 이 검증의 차단 사유가 아니다.

- 항만 catalogue 대표점 SQL의 불필요한 unary union을 제거했다. 실제 73개 항만 그룹 조회 8.54초→0.13초. 정상 지명 원천과 장애 원천을 분리하고 동일 이름 불량 행/후보 자체 원천 장애는 계속 차단한다.
- 실행 산출물과 관련 문서 주제를 구분하고, 검증된 기존 후보를 요청 산출물에 따라 재선택한다. 장소 후보가 1위여도 traffic aggregation을 후보에서 배제하지 않는다. 검색 행동만으로 사고 후보를 만드는 신호를 제한하고 nearest 공간 신호를 보완했다.
- 최근 N개월은 현재 월 기준 source별 월 coverage를 검사한다. 과거 적재 기간으로 묵시적 대체하지 않는다. 최신 적재 월은 별도 의미로 보존한다. 고정 V-PASS 우세·12개월 문구, 임의 3km layer 반경을 제거했다.
- S-101 단일 Feature 매핑, 실제 traffic coverage/pgvector 진단, 작업 trace 문맥 부족 처리, SSE 도메인 결과·근거 보존을 구현했다. 적재 관련 문서 청크 조회만 수행한 응답은 PARTIAL이며 전체 적재 완료로 표시하지 않는다.
- 격리 환경 관련 회귀 **173 passed**. 실제 API 계약 검사 **9/9 통과** (`outputs/web-sample-review/contracts-v4.jsonl`). 최신 적재 월 부산항 AIS 조회는 실제 2023-12 자료 6개 교차 격자, 집계 합 6,847,473을 반환했다. 고유 선박 수 또는 현재 통항량이 아니다.
- 최초 Ollama 100개 결과는 기본 형식/인용 통과 69, 인용 불일치 27, JSON 실패 4. 슬롯·설명 오류가 남아 있으므로 정확도로 해석하지 않는다. 최초 lexical 후보 재생과 실제 서비스 후보는 다른 실험이다. `--live-candidates`로 후자를 분리했으며 동일 후보의 rule/Ollama/혼합 순위를 저장한다. human gold와 calibration 없이 실행 권한을 승격하지 않는다.
- 원시 출력은 `outputs/web-sample-review/`, `outputs/pipeline-comparison/`에 분리한다. 기존 사용자 변경 `data/feedback/query_quality_issues.jsonl`은 소스 커밋에 포함하지 않는다.

남은 P0: portrayal symbol 연결 근거 완결성, raw→표준화→serving 전체 lineage 진단, 복합 요구의 작업별 실행/누락/완료 계약, 최신 외부 예측 및 실제 LiDAR 엔진. 지명 한정어·동명이칭 추가 입력을 자동 좌표로 치환하지 않는다. 남은 P1: 사람이 검수한 독립 gold/holdout, 동일 후보·모델·prompt의 calibration과 ablation. QLoRA 조건은 여전히 미충족이다.

동일 서비스 후보 후속 8개 실험은 구조/인용 5개 통과, 3개 인용 실패였다. 통과 응답에도 무근거 반경·날짜가 남는다. 82/46번에서 후보 부족에 따른 ABSTAIN은 유용했지만 슬롯까지 신뢰할 수는 없다. 병행 부하 실험은 API 계약 6/9로 저하했고 timeout·항만 원천 시간 제한을 관측했다. 원본 `contracts-v5.jsonl`과 `live-candidates-v2/`를 보존했다. 후보/DB 동기 조회를 이벤트 루프 밖으로 이동했으며 상시 shadow 승격 전 자원 격리와 동시 요청 검증이 필요하다.

후속으로 사고 조회 필터가 없는 질의의 clarification 경로, 실제 Dataset 경로별 embedding NULL 집계, resolver registry 선언 목록을 추가했다. 해당 후속 단위 18개와 이벤트 루프 수정 후 관련 46개 회귀가 통과했다(앞의 173개와 중복 포함). 새 진단도 source coverage와 runtime availability를 구분하며 문서/등록 정보만으로 완료를 주장하지 않는다.

기준일: 2026-09-25
재개 원칙: 명시적 새 우선순위가 없으면 아래 `P0 미비점`부터 처리한다. 이번 세션은 사용자 지시에 따라 GeoLLM 공통 P1 Ollama shadow 실험을 우선 수행했다.

## 2026-09-25 GeoLLM 공통 shadow 실험 및 근거 평가

### 후속: 실제 웹 샘플 100개 응답 평가

- [웹 샘플 평가 보고서](web_sample_review_20260925.md): 실제 HTTP 페이지의 100개 preset을 웹과 같은 SSE API로 실행했다. COMPLETED 29 / BLOCKED 63 / NEEDS_CLARIFICATION 5 / 관측 timeout 3. **상태값은 정답률이 아니다.**
- Browser 연결 목록이 비어 화면 클릭·렌더링은 미검증이다. 사용자에게 연결을 요청했으며 지도 문맥은 임의로 넣지 않았다. SSE/API 관측과 브라우저 E2E를 구분한다.
- 샘플 21의 Feature 식별, 25의 구역 지도 표시, 28/30/31/32의 통항 집계, 79의 pgvector 동작 확인, 80/82의 판단 근거 요청이 관련 문서 답변으로 종료되는 **필수 결과 누락**을 확인했다. 28/30/31/32/33의 `traffic_analysis`는 null이다.
- 원천 장애 55건의 공통 경로를 확인했다. 실제 catalog에는 후보 1,985개가 있지만 항만 projection 집계가 5초 statement timeout으로 실패하고 전체 지명 해소에 전파된다. 원천별 격리·조회 비용 개선이 필요하다.
- 43/44의 정의는 로컬 FC 정의와 일치했다. 97/98은 공식 예측 원천 부재를 명시하고 차단했다. 이 제한된 성공을 전체 서비스 정확도로 확장하지 않는다.
- 원본은 `outputs/web-sample-review/live-presets-v1/`. 40/41/42는 30초 관측 timeout 후 기존 task가 RECEIVED로 남아 있었다. 관측 클라이언트 연결 종료의 영향과 실제 브라우저 동작을 분리해 재현해야 한다.
- 평가 수집기 `scripts/check_geollm_web_samples.py` 추가. 이번 평가는 운영 코드 수정 전 기준 결과이며, 운영 라우팅을 변경하지 않았다.

- 오프라인 shadow runner, Pydantic 계약 검증, 규칙/Ollama/혼합 순위·보정·원본 요청/응답·실행 관측·모델/prompt/registry/source 버전 기록을 구현했다. 운영 상시 관측이나 실행 결정권 승격은 아직 아니다.
- gemma2 9B는 180초 timeout 2회, 축약 입력 1회 307.9초. qwen2.5:1.5b 실제 16문항은 계약 통과 9/16, 중앙값 55.62초, 기존 API 관측 15건/관측 timeout 1건이다.
- 라벨은 AI 작성 REVIEW_REQUIRED이다. 단일 라벨 불일치를 오분류로 단정하지 않도록 `provisional_label_agreement`, `reference_label_coverage`로 수정했다. 의미 정확도·task coverage는 미측정이다. 공간 분석과 위치 조회처럼 같은 기능을 공유하는 route는 대안일 수 있다.
- [실험 결과](intent_shadow_evaluation.md), [16문항 판단 근거](intent_shadow_review.md)에 필수 작업, 기능 조합, 원문 보존, 관측 근거와 유보 사유를 기록했다. AI 의견은 human gold가 아니다.
- v1 입력 축약에서 반경 검색 설명이 빠진 문제를 수정했다. v2는 원문 인용·capability ID·판단 근거·미충족 작업을 필수로 받는다. calibration 2문항에서 구조·참조 통과 1건, 다른 후보 capability 참조 거부 1건. 내용 해석 문제는 남았으며 v2 전체 evaluation은 미수행이다.
- shadow/broker 회귀검증 **20 passed**. **QLoRA DEFER**: 독립 human gold/holdout, 반복 오류 분석, 모델·GPU·라이선스·rollback 조건 미충족.
- 원본 산출물은 `outputs/intent-shadow/{pilot-probe-v1,pilot-v2,qwen-pilot-v1,qwen-rationale-v2}`에 보존한다. runtime 로그·피드백은 소스 커밋과 구분한다.

## 2026-09-25 재수정 및 실제 검증 결과

### 웹·DB·서비스 상태

- `/`, `/uport/`, `/vision/react_lidar/`, 최신 LiDAR JS 번들 및 `/health` HTTP 200. `/health`만으로 DB 정상 여부를 판단하지 않는다.
- `POSTGIS_URL`은 `marine_geo`, `S101_DB_URL`은 `gbhd_s101`. 부산 선석 169건, 인천 선석 128건을 `projection.s101_feature_valid`에서 실제 조회했다. 잘못된 bbox/과대 bbox는 422.
- `python scripts/check_web_db_connection.py`: **11개 점검 모두 통과**. 실제 LiDAR 미등록 ID의 preprocess/classify는 모두 404이며 가짜 job을 만들지 않는다.
- LiDAR `lidar_datasets` 테이블이 없음을 발견했다. `python -m scripts.initialize_lidar_registry`로 빈 테이블을 생성했고 실제 조회 결과 **0건**이다. 샘플 데이터를 삽입하지 않았다. 파일 크기·점 수는 BigInteger이며 실제 메타데이터를 저장한다.
- Compose backend를 `up -d --no-build backend`로 재생성했다. tests와 ui의 읽기 전용 마운트가 적용돼 재시작 후에도 최신 웹 번들을 사용한다. DB/타일/ETA 서비스는 유지했다.
- 항만 조회가 재기동 후 5초 제한을 넘기는 오류를 실제 API에서 발견했다. `scripts/sql/20260925_navigation_port_index.sql`의 항만 전용 인덱스를 DB에 적용했다. EXPLAIN ANALYZE에서 **Index Scan**, 항만명 73개, 실행시간 **193.193ms**를 확인했다. 이후 실제 질의 7개가 모두 통과했다. projection을 재생성하는 환경에서는 이 인덱스도 적용해야 한다.

### 제거·수정한 실행 경로

- mock registry/client/VDB/S-111 DB, fake embedding, 합성 공간결과, LiDAR pilot 산출물 생성 코드를 제거했다. 단위검증에 사용하는 격리 fixture는 테스트 폴더에만 둔다.
- RAG 원천 장애는 `BLOCKED/RAG_SOURCE_UNAVAILABLE`로 반환한다. LLM 실패 시 실제 검색 문서 발췌만 사용하며 임의 규정 답변을 만들지 않는다.
- 임의 위험등급, 기본 흘수 8m, 근거 없는 UKC 10% 법적 주장과 LLM 위험등급 fallback을 제거했다. 검증된 위험규칙 엔진이 없으면 `UNKNOWN/NOT_EVALUATED`이다.
- 고정 정확도·품질 점수와 의미 없는 100% 표시를 제거했다. 측정하지 않은 점수는 null/미평가이며 registry hit·문서 수·도구 실행 여부는 관측값으로 따로 남긴다.
- `navigation_risk.py`, `port_context.py`, `quality.py`로 복합 분석·위치 해소·미평가 계약을 분리했다. `parsed_intent`와 최종 route가 분석은 `ANALYSIS`, 정의는 `DEFINITION`으로 일치한다.
- 위치는 명시 항만명을 우선하며, 지도 문맥은 선택 feature → 클릭 → 명시 geometry → viewport → 중심 순으로 해소한다. S-101 HarbourAreaAdministrative 실제 geometry/ID를 사용하고, 지도 최근접 항만은 기본 25km 정책 밖이면 clarification이다. DB에 수록된 항만 범위이며 전국 항만의 완전성을 보증하지 않는다.
- 통항 검색은 지정 geometry 또는 사용자가 준 반경으로 제한한다. 누락된 실행 결과를 통항량 0으로 대체하지 않는다. 격자·월 합계는 고유 선박 수/실시간 위험도가 아니라고 명시한다.
- 실패·부분 결과를 report 단계에서 COMPLETED로 덮어쓰지 않는다. UI도 실행하지 않은 단계를 모두 완료 처리하지 않는다.
- LiDAR UI의 날짜/장비/CRS/좌표/점 수/밀도/RGB 고정값, 대시보드 목업 및 이전 배포 번들을 제거했다. 실제 파일 헤더를 표시하고 값이 없으면 미확인·미측정으로 표시한다.
- 전처리는 실제 PDAL 산출물과 LAS 헤더 점 수를 확인한 경우에만 성공한다. 정합·CRS 변환·RMSE는 미수행/미측정이다. 분류·DEM/S-111 의미검색 등 미구현 기능은 명시적으로 차단한다. **실행 컨테이너에 PDAL은 미설치**이며 실제 엔진 성공 검증은 미완료다.

### 검증 범위

- 관련 단위/그래프/스트림/공간/장소/RAG/UI API 회귀 **257 passed**. 이후 LiDAR DB 저장 수정에 대해 파일 헤더→실제 SQLite 저장→동일 경로 재등록 ID 유지와 실패 경로 **12 passed**를 별도 확인했다(11개 중복 실행, 총 고유 테스트 258개). 전체 저장소 테스트를 통과했다고 주장하지 않는다.
- `python scripts/check_navigation_runtime.py`: **7/7 통과**. 부산/인천 bbox와 부산 지도+명시 인천항은 실제 통항자료가 있는 `PARTIAL`; 위치 없음/먼 좌표/없는 항만은 `NEEDS_CLARIFICATION`; `조석예보란`은 `COMPLETED/DEFINITION`이다. 의도·최종 상태·항만 ID·통항자료·미평가 계약을 함께 검사한다.
- 실제 항만 source ID: 부산 지도 599613, 인천 지도 623953, 명시 인천항 집계 대표 548868. 고정 입력 ID가 아니라 해당 실행에서 조회한 결과다.
- `npm run build`, Compose `config --quiet`, `git diff --check` 통과. 최신 번들은 실제 HTTP로 확인했다.
- Browser 연결 목록이 비어 있어 실제 화면 렌더링·클릭·지도 조작은 미검증이다. HTTP/API 검증과 구분한다.
- 기존 훈련 데이터 확장 프레임워크는 유지했다. 웹·DB 검증 당시 P1은 dry-run이었고 이후 위 기록의 오프라인 후보 점수 결합·잠정 calibration 실험을 수행했다. 독립 human gold 평가·운영 승격·QLoRA는 미수행이다.
- 기존 사용자 변경 및 런타임 기록 `data/feedback/query_quality_issues.jsonl`, ignored scratch/outputs 로그는 소스 커밋에서 제외한다.

## P0 미비점 — 다음 접속에서 먼저 처리

1. **시공간 입력과 실행 범위의 잔여 계약**
   - 항만 대표점 조회 비용과 전체 원천 장애 전파는 이번 수정으로 개선했다. 실제 항만 면 union은 유지하며 병행 부하에서의 시간 제한·자원 격리는 아직 검증이 필요하다. 필수 분석 결과 없이 문서 검색만으로 COMPLETED 처리되는 잔여 경로, 특히 portrayal·지도 선택 객체·복합 요구를 작업별 출력 계약으로 검증한다.
   - 파일럿 API에서 C02/C03/E01/E03/E04는 `GAZETTEER_UNAVAILABLE`. 위치 문맥 없는 E04는 누락 위치 clarification과 원천 장애를 구분해야 한다. E06 `내일 인천항 만조 시각을 알려줘`는 `COMPLETED`와 `error_code=BLOCKED_DATA`가 함께 관측돼 상태 정합성을 재검증해야 한다. E07 관측 timeout은 작업 자체 실패와 구분한다. 재현 질의·관측은 공통 검토 문서와 qwen-pilot-v1 원본에 보존했다.
   - 최근 N개월과 source별 월 coverage 계약을 수정하고 부정 사례를 추가했다. 일 단위·지원하지 않는 명시 날짜 표현은 월 자료로 실행한 척하지 않고 clarification한다. 정확한 일 단위 집계와 다양한 명시 날짜 구간의 지원은 남은 작업이다.
   - 항만 입구/출구는 항만 전체 geometry로 치환하지 않고 clarification한다. 사용자가 확인한 세부 위치를 재제출하는 UI 흐름과 다중 항만·광역 viewport를 실제 브라우저에서 확인해야 한다.
   - 분류기 단위 테스트의 사전 fixture 통과를 실제 모든 용어의 정의 근거 확보로 간주하지 않는다. 등록되지 않은 복합 용어와 다중 의도를 추가 검증한다.

2. **위험 분석 근거 확장**
   - 사고이력, 수심/UKC, 기상·파고·조류를 동일 시공간으로 결합해야 한다. 현재 통항+고시 결과는 `PARTIAL`이며 종합 위험점수·사고확률을 산정하지 않는다.
   - 실시간 AIS provider 미설정 시 503 계약을 유지한다. 2023년 등 과거 집계가 실시간 관측을 대신하지 않는다.

3. **LiDAR와 S-111 실제 엔진 완성**
   - PDAL 설치·고정 버전·실제 LAS/LAZ 성공 실행과 출력 품질 검증이 필요하다. 분류/DEM/정합/변화탐지는 구현 전 성공을 반환하지 않는다.
   - S-111 실제 원천·관측 인덱스·검색 근거 계약을 연결해야 한다.
   - LiDAR 원본이 변경된 동일 경로의 재등록 시 메타데이터 갱신/버전 정책, 처리 산출물의 웹 제공과 영속 작업 상태를 보강한다.

4. **구조·운영 검증**
   - graph.py의 남은 중복 helper와 다른 legacy 분석 경로를 순차 감사한다. 이번 수정 범위를 전체 저장소의 모든 stub 구현 완료로 간주하지 않는다.
   - Browser 연결 후 지도/폼의 실제 상호작용 검증. 서비스 재기동 직후에는 준비 완료를 기다린 뒤 smoke를 실행한다.

## P1 Ollama 의도 보조와 QLoRA 보강

### 현재 확인된 한계

- 운영 `query_candidate_broker`는 Ollama 필요 여부만 계산하고 실제 호출·채택을 수행하지 않는다. 별도 `scripts/run_intent_shadow.py`에서는 실제 Ollama 재평가를 구현·실험했다.
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

사용자 지정 P1 후속: AI 사후 검토를 사람이 확인해 **필수 작업·허용 capability 조합·슬롯·근거·clarification** 단위의 독립 평가셋을 만든다. route 이름을 정답으로 고정하지 않는다. 후보 설명 누락·공유 기능을 정비하고 고정한 prompt/model로 전체 calibration/evaluation을 재실험한다. 지연·실패 격리 확인 전 상시 shadow나 실행 권한을 승격하지 않는다. 별도 우선순위가 없으면 아래 P0 순서를 따른다.

1. 웹 준비 후 `python scripts/check_web_db_connection.py`와 `python scripts/check_navigation_runtime.py` 실행.
2. 새 DB에는 `docker exec geollm_backend python -m scripts.initialize_lidar_registry` 적용. S-101 projection에는 `scripts/sql/20260925_navigation_port_index.sql`을 S101 DB에 적용.
3. P0-1의 복합 요구·portrayal·선택 객체 출력 계약과 shadow/API 자원 격리를 우선 검증한다. 항만 세부위치 확인 흐름과 미지원 날짜 표현을 보강하고 관련 단위 테스트+실제 API 부정 사례를 검증한다.
4. 사고·수심·기상 근거 결합 및 LiDAR 실제 엔진을 각각 원천·산출물 검증과 함께 확장.
5. Browser 연결 후 화면·지도 조작 검증.
6. 구현된 오프라인 shadow를 근거·복수 기능 조합 기준의 독립 human gold/calibration 평가로 확장한다. v2 전체 평가와 상시 관측 연동은 미완료다. 승격 조건 충족 전 실행 결정권을 주지 않는다.
7. prompt 보완 후에도 반복 오류가 남고 holdout·rollback 조건이 충족될 때만 QLoRA 실험.

## 검증 시 주의사항

- 2023년 통항자료를 현재 실시간 위험도라고 표현하지 않는다.
- `estimated_accuracy`는 측정 전 null이다. registry exact match를 답변 정확도 100%라고 표현하지 않는다.
- 고시 polygon이 `pending_geometry_ingest`이면 적용 공간을 확정했다고 표현하지 않는다.
- 지도 문맥과 명시 항만명이 모두 없으면 특정 항만을 임의 선택하지 않는다.
