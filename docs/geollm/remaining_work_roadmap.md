# GeoLLM 현재 상태와 다음 작업

## 2026-10-06 웹 재기동·상태 확인

- Docker 엔진 중지 상태에서 Docker Desktop을 시작했고 기존 backend/DB가 기동했다. `/` HTTP 200, 일반 Dataset 근거 API 5/5 요청 정상(부산항 입구/해양공간관리계획/양식장/수로/없는 자료), 없는 자료 0건을 재확인했다. 이번에는 Qwen 재평가·벡터 전체 검증·브라우저 렌더링 검증을 하지 않았다.
- 실제 DB snapshot: 본문 23,215개, 임베딩 17,593개. 기존 16,853개 대비 신규 740/6,362개이며 5,622개 미완료다. 이전 진행 파일의 RUNNING은 현재 worker 생존 증거가 아니다. Docker 재기동으로 이전 detached worker는 자동 재개되지 않는다.
- 다음 작업: 신규 임베딩 worker 재개·완료 확인 → 벡터 및 실제 웹 질의 검증 → OCR/원천 완전성/수치조류 사양 → canonical 의미 관계 검수. Phase A 전체 완료, 독립 gold/calibration, QLoRA 승격은 계속 보류한다.

## 2026-10-02 Dataset 전체 원천 대조·본문/공간 연결 확대

- 종료 전 관측: 신규 임베딩 worker 재개 후 72/6,362개(6,290개 대기). 전체 완료가 아니다. 최종 API 검증과 별개로 브라우저 탭 새로고침은 CDP timeout으로 새 UI 결과 확인을 완료하지 못했다. 다음 세션에서 실제 웹 재질의 확인이 필요하다.
- 사용자 우선순위로 Dataset 전체 244개 파일의 SHA-256을 대조했다. [구현·실제 관측·재개 명령](dataset_pipeline_20261002.md). 기존 profile/partial hash/파일명 추정을 본문 완료로 보지 않는 원본별 audit를 추가했다.
- 기존 항로서지·소형선항만 8,440개는 DB에서 모두 1,024차원 임베딩 완료 확인. 이전 10월 1일의 이 항목은 해소됐다. 새 문서 32개에서 6,362개 본문을 추가 적재했으며 신규 벡터는 별도 worker 진행 중이다.
- 누락 정적 SHP 37개 member 209,952행, CSV 17개 고유 원본 1,128,824행을 추출했다. **추출 수와 최종 DB 적재 수는 구분한다.** `outputs/dataset_pipeline/finalize.log`, `spatial_loaded.json`, `live_snapshot.json`, `audit.json` 및 실제 DB를 대조한다. Windows 대용량 bind mount 읽기 병목으로 `/tmp` 사본을 사용한다.
- 원본 해시/본문/record collection을 연결하고 Dataset 근거·Qwen 인용 API를 웹 분석 아래와 SSE에 반영했다. ExecutionValidator의 read-only 승인만 사용하며 좌표·canonical/ontology 의미 관계를 자동 승인하지 않는다. CSV 좌표는 추론하지 않는다.
- 실제 `해양공간관리계획`은 적재 전 0건→적재 후 원문 5건, 해양사고심판 사례집도 검색됨. Qwen 원문 없는 설명은 일반론·길이 제한 잘림이 있었고, 근거 기반 인용과 분리 보존했다. 대량 적재 중 HTTP 500 관측 후 공간 조회 실패를 별도 PARTIAL로 격리했다. 최신 API 재검증 결과는 후속 기록을 따른다.
- P0: 신규 6,362개 임베딩 전체 완료·벡터 조회, 대량 적재 최종 행/geometry 검사, 빈 페이지 OCR 여부, 기존 본문 완전성 및 중첩 archive/바이너리·dump 검증. 수치조류의 grid/time/수치 인코딩 사양은 아직 없으며 전체 Dataset 완료가 아니다. P1: canonical 연결·원천 판 검수 및 독립 human gold. Qwen shadow/QLoRA DEFER.
- 다음 시작점: worker/DB 확인 → `dataset_pipeline snapshot`/`audit` → `check_dataset_pipeline --model`/`--semantic`. 컨테이너 restart는 worker를 중단한다. 재개 명령은 상세 문서에 있다. 런타임 산출물과 사용자/관리자 UI의 기존 미커밋 변경은 소스 커밋에서 제외한다.
- 최종 적재 확인: 정적 공간 209,952행(유효성·범위 통과 206,120, 제외 3,832), CSV 1,128,824행. 출처 그래프 23,418 노드/23,232 관계. Python 확장 31 passed, 후속 조회 실패 격리 관련 6 passed(중복), Node 5 passed. 검색 인덱스를 추가했다. 이 수치를 신규 임베딩 완료나 전체 Dataset 의미 연결 완료로 해석하지 않는다.
- 최종 재배포 API: lexical 5/5 요청 완료(0.319~5.262초), 실제 bge-m3/pgvector 5/5 완료(0.560~2.703초), HTTP 오류 0. 부산항/해양공간관리계획/양식장/수로와 없는 자료를 확인했고 negative는 문서·공간 기록 모두 0건이다. 벡터 조회는 현재 임베딩된 자료에 한정된다. 신규 6,362개 전체 벡터 완료가 아니다.

## 2026-10-01 항로서지·소형선항만 본문·공간·지식 연결

- 사용자 우선순위로 두 원천을 처리했다. [변경·검증·재개 방법](coastal_knowledge_20261001.md). PDF 30/HWP 28, PDF 1,644쪽, 본문 청크 8,440개를 추출·적재했다. 소형선항만 439건의 EPSG:5179→4326 변환·유효성을 확인했다. 전체 Dataset 완료가 아니다.
- 출처/hash/페이지·section을 유지한 지식 그래프 9,758 노드·10,327 관계. 원문 지명 언급 및 항만 원천 record 연결이며, 입구 geometry/방파제 관계를 자동 승인하지 않는다.
- 새 원문 조회 API와 웹 분석 근거, Qwen 원문 발췌 선택, 최종 SSE·저장 결과 근거 연결. ExecutionValidator는 문서 조회만 승인하며 기존 공간 clarification을 유지한다. 늦은 이전 질의 응답을 차단한다.
- Python 26 passed, Node 5 passed. 실제 원문 질의 부산항/다대포항/울릉도 각 발췌 5개, 없는 지명 0개. Qwen 자유 인용의 지명 혼합 실패를 기록하고 ID 선택 방식으로 수정해 원문 일치 인용 3개를 검증했다. 부분 벡터 검색도 실제 bge-m3/pgvector 결과 5개를 확인했다.
- **P0 미완료: 전체 8,440개 임베딩**. CPU worker는 배치별 DB 저장/재개 가능하며 `outputs/coastal_knowledge/embedding_progress.json`, worker 로그와 DB COUNT(embedding)을 반드시 대조한다. 컨테이너 재시작은 worker를 중단하므로 문서의 `--embed` 명령으로 재개한다. 문서 검색 가능과 전체 임베딩 완료를 구분한다.
- 추가 미비: 텍스트 없는 PDF 61쪽의 OCR 필요 여부, DBF 394개 기록의 잘린 필드 원천 보완, 문서 판·최신성, 동명 항만 식별, 실제 입구 geometry 및 의미 관계 검수. 상시 운영/Qwen 학습 승격은 하지 않았다. 다음 첫 작업은 worker 생존/DB 진행 확인 → 전체 임베딩 완료·벡터 검증 → 원천 품질 검수다.

## 2026-10-01 입구·근처의 해석 중심 답변

- 위치 확인 대기 응답의 첫 화면을 공간 표현 의미 → 실제 후보 관측 → 미확정 조건으로 보완했다. 입구/출구를 항만 전체·중심점으로 대체하지 않고, 근처/주변은 기준 위치와 반경/영역을 분리해 설명한다. 실제 반경 기록이 있으면 보존하고 임의 반경은 추가하지 않는다.
- 이는 표시 계층의 해석 설명이며 지형·좌표·실행 근거를 생성하거나 Qwen에 승인 권한을 주는 변경이 아니다. 검증된 좌표 원천 확보는 기존 P0로 남는다.
- 관련 Node 회귀 5 passed. 실제 웹 부산항 입구로 이동 재요청에서 상단 제목과 답변 본문이 공간 표현 해석, 후보 1개, 좌표 미확정, 미실행으로 표시됨을 확인했다.

## 2026-10-01 추가 확인 대기와 오류 표시 구분

- NEEDS_USER_INPUT을 실행 불가 오류로 표시하던 trace UI를 입력 확인 대기로 수정했다. place_navigation_action은 빠른 지명 해석 경로 선택일 뿐 실행 승인 아님을 명시한다.
- 위치 이름 추출을 좌표 확정처럼 보이게 하는 체크 표시를 제거했다. 빈 KG/RAG 필터·경로는 기록 없음으로 표시하고 검색 0건과 구분한다. 승인 권한이나 resolver 기준은 변경하지 않았다.
- Node 관련 UI 회귀 4 passed 및 inline JS 문법 확인. 실제 브라우저 부산항 입구로 이동 재요청에서 입력 확인 대기·공간쿼리 미실행·추출 위치 이름·KG/RAG 기록 없음 문구를 확인했다. 다음 P0는 아래의 검증된 기준 좌표·복합 출력·원천 연결이며 문구 수정으로 해결됐다고 보지 않는다.

## 2026-10-01 실행 상태 표시와 해석 기반 응답

- 최종 SSE에서 실행 상태 전체를 reset하던 UI와 빠른 지명 조회의 상태 누락을 수정했다. 완료 후 의도 처리, 후보 발견, 후보 확인 대기, 미승인, 미실행, 응답 완료를 유지한다. 응답 완료를 지도·보고서 도구 성공으로 표시하지 않는다.
- 질의 응답 안에 원문/정규화/규칙 순위/Qwen 원문 해석·슬롯/융합 순위/실제 실행 판단을 연결했다. 비교가 늦게 완료돼도 현재 질의만 갱신한다. 모델의 위치 표현이 원문 대상과 다르면 차이를 표시한다. 좌표 없는 외부 후보는 선택 불가와 좌표 보완 필요를 설명한다.
- Node UI 16 passed, 후속 핵심 4 passed. 브라우저에서 부산항 입구로 이동의 기존 reset 증상 재현 후, 수정본의 상태 지속 및 Qwen 완료 시 답변 갱신을 확인했다. Qwen은 부산항으로 슬롯을 축약했지만 실제 원문 부산항 입구를 유지하며 승인하지 않았다.
- 이전 중단된 최종 API 검증도 산출물로 확인: 일반 수로 품질 문서는 Standard RAG 실제 2건, 렌더링 규칙은 PARTIAL/OUTPUT_OBLIGATIONS_UNMET, 창원 정비불량 사고 59건 COMPLETED. 전체 데이터 품질/복합 분석 완성을 뜻하지 않는다.
- 남은 P0와 재현은 [100개 예제 검증](web_presets_processing_20261001.md)을 따른다. 실행 기록이 없는 legacy 전문 단계는 기록 확인 필요로 표시하며 완료를 추정하지 않는다.

## 2026-10-01 질의창 100개 검증과 단계별 응답 연결

- [실제 검증·100개 관측 표·남은 P0](web_presets_processing_20261001.md). 초기 예제 100개 SSE 완료, 수정 후 15개 모두 6단계 설명 확인. 의미 정확도 100%를 뜻하지 않는다.
- 이전 비교 근거 잔류/늦은 응답 혼입, 근거→근처 교정, 사건/예측/신항만예정지역 fast path, 주변 지명 추출, 사고 필터 Gate 안내를 수정했다. 실행 승인 권한은 ExecutionValidator로 유지한다.
- 테스트 배치 68/59/11/27/20/10 passed(중복 포함), Node 13 passed. 기존 비네트워크 graph fixture의 DB 접속 teardown 오류는 미해소이며 전체 테스트 통과를 뜻하지 않는다. 이전 사고 Gate 기대값 실패 2개도 이번 배치에서 해소했다.
- 다음 첫 P0: authoritative 위치 원천 및 복합 요청 양성 검증, 일반 문서/CSV 근거 관련성, AIS 셀 설명/S-101 portrayal의 실제 최종 산출물. 위치/원천 미비를 성공으로 우회하지 않는다. Phase A 전체 완료 및 학습 승격은 보류한다.


## 2026-10-01 사용자 우선순위 — 지명 해석과 실행 응답 연결

- [원인·변경·재현](place_query_linkage_20261001.md). Qwen은 울릉도를 추출했지만 실제 위치 원천에서 기준점을 해소하지 못했다. 해석한 지명·대상·반경을 보존하고 위치 미확인/반경 누락/검색 미실행을 답변에서 구분하도록 보완했다. 반경 누락 시 이미 확인된 위치와 출처도 유지한다.
- 대조 검색에서 DB layer_id=marine_gazetteer_mof와 registry key=marine_gazetteer의 불일치를 발견해 수정했다. 레이어 반경 tool binding도 dwithin으로 정합화했다. ExecutionValidator 권한과 Qwen shadow 정책은 유지한다.
- 관련 회귀 88 passed. 별도 기존 사고 조회 테스트 2개는 기대 오류 코드와 공통 Gate 반환 코드가 달라 실패했으며 이번 변경 대상 밖의 P0로 남긴다. 실제 API 최종 결과는 연결 보고서를 확인한다.
- 다음: 울릉도 자체의 authoritative 기준 geometry 확보 및 사용자 기준점 확인 후 재조회 검증 → 일반 문서 질의의 근거/근처 정규화·오경로 → 사고 Gate 상태 정합성. 원천 확보 전 울릉항이나 모델 좌표로 울릉도를 대체하지 않는다. Phase A 전체 완료와 QLoRA 승격은 보류한다.

## 2026-10-01 Phase A 운영 원천 및 실제 브라우저 검증

- [검증 결과·재현·미비점](phase_a_sources_ui_20261001.md). 운영 Agent 직접 호출 5/5: RAG 문서 2건, 사고 관계 5건, 미준비/fixture/미등록 시계열 차단. HTTP E2E와 구분한다. 시계열 binding에서 파일 존재·루트 경계·fixture 별칭·확장자를 검증하도록 수정했다.
- Python 관련 회귀 117 passed, Node UI 12 passed. backend 재시작 후 실제 API 승인/차단/재개 6/6 통과. 초기 들여쓰기 오류 및 UI 테스트 mock/문구 실패는 수정했으며 검증 문서에 기록했다.
- 실제 브라우저에서 Evidence 메뉴, 분석 아래 비교 영역, 미평가 점수, PARTIAL 안내, 미실행 단계 표시 및 질의창/지도 동일 높이와 내부 스크롤을 확인했다. 이전 browser helper 장애는 이번 세션에서는 해소됐다. 승인이나 human gold 변경은 하지 않았다.
- **다음 첫 P0:** `수로 측량 데이터 품질 관리 관련 근거 문서를 검색해줘`의 `근거`→`근처` 정규화 및 DATA_DISCOVERY 오경로를 조사·수정한다. 사고 데이터 중심 근거 반환을 일반 RAG 정상 답변으로 인정하지 않는다. 직접 RAG 실행 성공과 웹 의도 오류는 별개다.
- 이후 운영 원천 권한/열/Agent/슬롯 변경 검증과 실제 시계열 양성 원천 → Phase A 완료 판단 → B 실제 데이터/adapter → C/D/E/F 순서다. **Phase A 전체 완료는 보류**한다. Qwen/융합 shadow, calibration UNFITTED, QLoRA DEFER 유지.

## 2026-09-30 Phase A 후속 검증 및 일반 질의 재개 계약 보완

- [변경·검증·잔여 범위](phase_a_validation_20260930.md). 사용자 요청으로 Phase A를 재개했다. 일반 질의도 추가 입력 시 이전 계획/QEC/Agent 결과/승인을 폐기하고 revision을 올려 재계획한다. 메모리 checkpoint가 없으면 저장 snapshot을 사용하며, 모두 없으면 재개를 거절한다.
- RAG 사전 원천 검사에 실제 SQL이 사용하는 chunk_id/source_id/source_sha256을 추가했다. 누락 시 실행 전에 차단한다.
- 수정 전 관련 회귀 175 passed. 수정 후 179 passed(77 warnings), 별도 일반 재개·저장 snapshot 복원 route 테스트 2 passed(1 warning). 전체 저장소 테스트 통과나 의미 정확도를 뜻하지 않는다.
- 최신 코드로 backend 재시작 후 실제 API **6/6 통과**: 이동/정의/1km 검색 승인·완료, 반경 누락 추가 입력 요구·미승인, 60km 차단·미승인, 같은 작업에 1km 추가 입력 시 revision 2·새 승인·완료. 정적 UI 자산·검토 이력 API 확인. 원본 `outputs/web-intent-audit/20260930-phase-a-runtime-v1.jsonl`은 커밋 제외.
- 응답 시간은 20.894/40.295/15.802/32.658/41.161/68.390초였다. 계약은 통과했지만 지연 개선/SLO 충족을 뜻하지 않는다. 문법 검사 및 git diff --check 통과.
- **다음 실행 순서:** 일반 RAG·사고 관계·시계열의 실제 운영 원천별 end-to-end 및 권한/원천 변경 검증 → UI 렌더링/지도 문맥 E2E → Phase A 완료 판단 → B 실제 데이터/adapter → C 근거 품질 → D 독립 gold/holdout → E benchmark/CI/SLO → F 학습 판단. Phase A 전체 완료 선언은 보류한다.
- 아래 9월 28일 인계의 '최신 backend 미반영/전체 관련 회귀 미검증'은 이번 범위에서 해소했다. 그 외 미구현 adapter·UI·원천별 검증은 유지한다. 지도 API 연동은 아직 가능성 검토 상태다. 규칙/Qwen/융합 shadow, calibration UNFITTED, QLoRA DEFER.


## 2026-09-29 사용자 우선순위 — parser & Map_viewer 지도 API 연동 검토

- [가능성 판단·근거·연동 순서](map_viewer_api_feasibility_20260929.md): 기술적으로 가능하며 기존 Leaflet에 서버 proxy를 통한 PNG XYZ 레이어 연결을 우선 권장한다. 이번에는 구현하지 않았다.
- 내부 지도 API 3000 health는 DB/projection 정상, FC/PC 2.0.0. 공개 지도 API 3002는 연결 거부, GeoLLM 8000은 전송 오류로 정상 확인 불가. Stage 0~4 로컬 manifest complete=true는 확인했지만 전체 파일/화면/공개 API ready 검증은 아니다. Stage 5/6 완성으로 해석하지 않는다.
- 다음 연동 순서: 서비스 상태/이용권/대표 타일 확인 → 키를 서버에 두는 고정 경로 proxy → Leaflet XYZ 및 줌/좌표 정합성 → 클릭/객체 API·원천 ID/판 매핑. 공개 API는 타일만 제공하므로 객체 근거 연동은 추가 adapter가 필요하다.
- Phase A 전체 회귀와 최신 API 재검증은 여전히 미완료이며 아래 인계에 남는다. 규칙/Qwen/융합은 shadow, calibration UNFITTED, QLoRA DEFER다. 자동 서비스 시작·키 발급·연동 코드 변경은 하지 않았다.


## 2026-09-28 최종 인계 — 사용자 요청으로 Phase A 작업 중단·커밋·푸시

- **다음 세션은 이 절과 문서 전체를 먼저 읽는다. Phase A 완료 선언은 보류한다.** 아래 이전 기록은 당시 검증 범위이며 최신 변경 전체의 통과를 의미하지 않는다.
- 추가 구현: registry 10개 항목에 실행/조사/미지원 계약을 명시하고, 공통 Agent 진입 gate를 dispatch 및 직접 호출에 적용했다. 요청 ID·질의·Agent·권한·operation·원천 binding을 다시 검증한다. QEC 누락/재사용은 차단하고 슬롯 수정은 승인을 무효화한다.
- Standard RAG는 문서 relation/SELECT/필수 열과 embedding profile을 확인한다. Data Discovery는 본문 CSV fetch를 제거한 metadata 전용 조사 계약, Validation은 부모 실행 QEC를 승인하지 않는 별도 조사 계약을 쓴다. AIS/Drone의 미완성 실행 adapter와 미구현 Map Agent는 BLOCKED_CONFIG로 남는다. 이는 기능 완성이 아니다.
- 레거시 DSL 거리 제한을 공통 50km로 맞췄고 최근접 검색 기본 결과 수는 1이다. 화면의 실행 가능 표시는 단순 READY/boolean이 아니라 validator 기록을 확인한다. 사람의 결과 검토 승인 후에는 보고서로 진행하며 실행 승인으로 승격하지 않는다.
- 검증 기록: 최초 진입 gate 회귀 43 passed / 7 failed(변경된 상태명·QEC fixture), 이를 보완했다. 확장 회귀는 170 passed / 2 failed였으며 실행 중 수정 전 사고 Agent fixture를 로드한 결과다. 수정한 사고 Agent 및 신규 계약 테스트의 별도 재검증 결과는 아래 최종 검증 기록을 따른다. 겹치는 수치는 합산하지 않는다.
- 현재 API 5/5 통과 기록(v2)은 **이번 전체 Agent gate 추가 이전 버전**이다. 최신 변경의 컨테이너 재시작과 실제 API 재검증은 중단 요청에 따라 다음 작업으로 남긴다. 현재 실행 중 프로세스와 디스크 소스가 다를 수 있다. UI 브라우저 렌더링도 미검증이다.
- 최종 제한 회귀: `docker exec geollm_backend python -m pytest tests/unit/test_accident_risk_agent.py tests/unit/test_agent_execution_contracts.py -q --disable-warnings --maxfail=2` → **27 passed, 39 warnings (31.37s)**. 사고 Agent의 2개 실패는 수정 후 통과했다. 확장 172개 전체를 최종 소스로 다시 돌린 결과는 아직 없다. `git diff --check` 및 staged 형식 검사는 통과했다.

### 다음 실행 순서 / 재현

1. **P0 / Phase A 마무리**: 변경 파일과 컨테이너 버전 확인 → 최신 회귀 전체 재실행 → backend 재시작 → 정상/부정 실제 API 검증. `docker exec geollm_backend python -m pytest tests/unit/test_agent_execution_contracts.py tests/unit/test_execution_dispatch_gate.py tests/unit/test_execution_validator.py tests/unit/test_spatial_agent.py tests/unit/test_standard_rag.py tests/unit/test_accident_risk_agent.py tests/unit/test_data_discovery.py tests/unit/test_execution_authority.py tests/unit/test_execution_gate_regressions.py tests/unit/test_radius_stream_contract.py tests/unit/test_uport_execution.py -q`. API: `python -m scripts.check_execution_authority_runtime --output outputs/web-intent-audit/<새 파일>.jsonl`(기존 파일 덮어쓰기 금지).
2. 일반 RAG·사고 관계·시계열 직접 호출 및 수정/재개 계약을 실제 서비스에서 추가 검증한다. 원천 권한 변경, Agent 변경, 슬롯 변경 시 실행 전 차단을 확인한다. RAG SQL 전체 필수 열과 검증 열 목록의 일치도 후속 감사한다. 테스트 결과와 실제 실행 결과를 분리한다.
3. 브라우저에서 Evidence 메뉴·분석 아래 비교 근거·지도와 질의창 높이·긴 대화 내부 스크롤을 확인한다. Windows browser sandbox helper 실패로 남은 E2E다.
4. **Phase B**: AIS/V-PASS·수치조류·바다갈라짐·Observation 원천/기간/커버리지 및 실행 adapter. Data Discovery의 기존 예시 catalog 항목을 실제 원천으로 검증/교체한다. metadata 발견을 실제 데이터 검증으로 취급하지 않는다.
5. C KG/인용/lineage/S-101 portrayal → D 사람 승인 3→30→300+ 및 hard negative/대화/복합/실패/holdout → E strict benchmark/CI/CD/SLO/monitoring → F FastPath·retriever 학습 검토. Planner QLoRA는 조건 충족 후 판단한다.
6. **P1 shadow 실험**: 규칙/Qwen/융합은 동일 후보 비교 전용, 실행 권한 없음. calibration UNFITTED, human gold 미승인, QLoRA DEFER. 동점/후보 구분력/추가 확인 오류와 CPU 지연을 독립 gold로 평가한다.

- 공유 작업 보존: 별도 관리자 UI script 및 index의 해당 script 태그/관리자 인계 절, 런타임 피드백 JSONL은 이 커밋에서 제외한다. 자동 생성 출력과 로그도 제외한다. GitHub 푸시 후에도 이 파일들 때문에 작업 트리가 dirty일 수 있다.

## 2026-09-28 실행 권한 단일화 1차 및 Evidence 검토 메뉴

- 사용자 우선순위인 Phase A부터 진행했다. RoutePlanner의 자체 승인을 제거하고 지도 이동·정의·legacy 조회·반경/영역/최근접/레이어·통항·UPort의 승인 부여를 ExecutionValidator로 모았다. 입력/binding hash가 바뀌거나 READY 플래그만 있는 QEC는 승인으로 취급하지 않는다. [변경 범위·검증·A–F 순서](execution_authority_and_review_20260928.md).
- P0 기본 반경 불일치를 수정했다. 위험객체 3km·사고 10km의 암묵 기본값을 제거하고 명시 반경/지도 영역을 요구한다. 반경 상한은 공통 50km다.
- Evidence 검토·승인은 주요 메뉴로 이동했다. 분석 결과 아래의 접이식 비교 근거와 별도로, 검토 화면에서 저장된 최근 30개 요청의 원문→실제 정규화→규칙/Qwen/융합 순위→실행 검증/차단 사유를 확인한다. Evidence 승인과 human gold/실행 권한은 분리한다. 질의창은 지도와 같은 높이, 내역 내부 스크롤, 하단 입력 고정으로 변경했다.
- 단위 검증: 110 passed 및 관련 그래프 회귀 134 passed; 정책 수정 후 최종 반경/통항/승인 회귀 93 passed. 중복 포함이므로 합산하지 않는다. 첫 실제 API 검증에서 30초 관측 타임아웃 3건이 발생했고 원본 v1을 보존했다. 180초 제한 재검증 v2는 **5/5 통과**: 지도 이동·정의·1km 검색은 COMPLETED와 validator 승인 기록, 반경 누락은 NEEDS_CLARIFICATION, 60km는 BLOCKED. UI 자산·검토 이력 API 응답도 확인했다. 원본 `outputs/web-intent-audit/20260928-execution-authority-v2.jsonl`.
- 브라우저 자동화는 Windows sandbox helper 초기화 오류로 시작하지 못했다. 메뉴 클릭·스크롤의 실제 렌더링은 미검증이다. 관리자 메뉴는 별도 공유 작업의 변경을 보존한다.
- 다음 실행 순서: Phase A의 일반 Standard RAG/보조 Agent registry 진입점 전체 QEC 감사와 legacy 재개 계약 → B 실제 원천/커버리지 → C KG/인용/lineage/공식 portrayal → D 사람 승인 자료·hard negative·대화/복합/실패 → E benchmark/CI/SLO/monitoring → F 학습 여부 판단. **모든 Agent QEC 완료로 선언하지 않는다.** Qwen/융합은 shadow, calibration UNFITTED, human gold 미승인, QLoRA DEFER다.

## 2026-09-28 웹 요청의 실제 규칙/Qwen/융합 비교와 지도 이동 허용

- 사용자 지정 우선순위에 따라 웹 SSE 요청(빠른 지명 이동 포함)마다 실제 Qwen 후보 점수 비교를 실행하도록 연결했다. 단일 worker/대기열과 별도 comparison_id를 사용하며, 웹에서 규칙·Qwen·동일 가중치 융합 순위, 원문 슬롯, 모델 해석과 실제 실행 판단을 확인한다. [설계·실패 기록·최종 재현](live_web_intent_comparison_20260928.md).
- 같은 후보를 평가하고 규칙 기준선의 legacy Ollama 호출을 제외했다. prompt/model digest/registry/source hash, 실제 입력·출력·지연, 실행 관측을 SQLite에 기록한다. 모델과 융합은 shadow 전용이며 실행 권한은 없다. gold=null, calibration=UNFITTED, QLoRA DEFER다.
- `해운대구로 이동`은 단일 행정지명 정확 일치·유효 좌표·출처·명시적 이동 조건에서 map_view_only로 허용한다. 분석 권위/registry 승격은 false이며 일반 위치 resolver의 분석 승인 정책은 유지한다. 복합/분석/제외 조건과 모호한 후보는 자동 허용하지 않는다. 지명 마커를 선석으로 오표시하거나 좌표를 임의 이동시키지 않는다.
- 최종 관련 회귀 **114 passed**. 실제 API 비교 **2/2 계약 통과**: 이동 COMPLETED, 주변 위험객체 NEEDS_CLARIFICATION; 둘 다 Qwen 호출과 세 순위 기록 완료. 원본 `outputs/web-intent-audit/20260928-live-comparison-v4/`, 운영 기록 `geollm_results/web_intent_comparison.sqlite3`. 브라우저 도구는 Windows sandbox helper 오류로 시작되지 않아 실제 클릭/렌더링 E2E는 미검증이다.
- P1 제한: Qwen 3.5 4B는 CPU 100% 환경에서 원본/압축 요청 모두 180초 timeout. 웹 기본값을 설치된 Qwen 2.5 1.5B로 조정했다. 1.5B 최초 응답의 문자열 null·후보 중복/누락은 검증에서 거절했고 원문 enum/후보 필수 점수 스키마로 보완했다. 실패 원본은 v1–v3 및 DB에 남겼다.
- 최종 1.5B 비교 지연은 약 63초/59초다. 위험객체 요청에 모든 후보를 1점으로 평가하고 추가 확인 불필요라고 판단한 한계가 남는다. 실제 실행은 이 판단을 따르지 않는다. 웹은 상위 동점을 명시하며, 단순 순위 일치나 구조 검증 통과를 정확도로 취급하지 않는다.
- 다음 실행 순서: 실제 웹 추가 사례를 필수 작업/슬롯/금지 대체 결과 기준으로 human gold 검수 → 후보 구분력·추가 확인 판단 오류 및 4B 지연 분석 → 독립 holdout/calibration. P0의 사건/VTS/예측/신항만예정지역 오해석과 기본 반경 정책 불일치는 아직 미해결이며, 기존 우선순위로 이어간다. 피드백 JSONL과 런타임 출력은 소스 커밋에서 제외한다.

## 2026-09-28 사용자 우선순위: 웹 질의의 의도 오류와 실행 미지원 분리

- 사용자는 한국어 의도/슬롯과 Qwen(Ollama 실행)·규칙 융합 비교 흐름을 우선한다고 재확인했다. 이번에는 모델 비교 이전에 현재 웹 서비스의 해석 오류와 실행 미지원/원천 부족을 분리했다. [검수 보고서와 재현](web_intent_execution_audit_20260928.md).
- 실제 웹 샘플 100개를 같은 SSE API로 순차 실행했다. 완료 이벤트 100/100, 관측 오류 0, COMPLETED 9 / PARTIAL 14 / NEEDS_CLARIFICATION 69 / BLOCKED 8. Browser 도구는 두 차례 Transport closed여서 클릭·지도·렌더링은 미검증이다. 기본 실험은 지도/대화 문맥 없이 수행했으며 상태 분포는 정확도가 아니다.
- 근거 기반 AI 검토에서 37(사건→지명), 51(바다갈라짐 시간→반경), 52(예측→지명), 56(VTS 축약→지명), 72/73(신항만예정지역→항만 기준점)의 의도/작업 해석 오류 6건을 확인했다. 전체 오류가 6건뿐이라는 의미나 human gold가 아니다. 대조 401은 사건을 사고로 바꾸면 실제 59건을 조회했다.
- 선택 객체 API 5/5, 속성/부정/복합 API 10/10 계약 통과. 객체 조회는 실행되지만 공식 portrayal은 PARTIAL, 부정/복합은 명시적 NOT_RUN이다. 31/32는 요청 월 미적재이며 대조 404의 최신 적재 월 AIS는 실제 2023-12 집계 6,847,473건을 반환해 의도 오류/연산 미지원과 구분했다.
- 새 P0: 72/73의 잘못된 COMPLETED와 S-101 위험객체 기본 반경 정책 불일치. 실제 DB geometry만 준 대조 402는 명시 반경 없이 3km/140건, 대조 403은 명시 1km/49건이다. `s101_radius_execution.parse_distance()`의 기본값이며 기존 문서의 근거 없는 반경 제거 완료 주장과 일치하지 않는다. API가 기본값을 고지한다는 점과 정책 정합성 문제를 함께 기록한다. 운영 수정은 이번 평가에 포함하지 않았다.
- 다음: 위 오류/대조쌍을 필수 작업·슬롯·금지 대체 결과 단위로 사람 검수 → fast path 후보 누락과 S3 완료 판정/반경 정책 정리 → 동일 후보 Qwen S4 원문 선택·지연 smoke → 전체 규칙/Qwen/융합 비교 → 독립 gold/calibration. 실행 미지원·원천 부족을 Qwen 의도 오류로 자동 집계하지 않는다. 신규 Qwen 추론/승격은 없고 QLoRA DEFER다.
- 원본은 `outputs/web-intent-audit/20260928-v1/`, `20260928-selected-feature.jsonl`, `20260928-marine-mapping.jsonl`, `20260928-probes.jsonl`에 분리했다. 4개 대조 질의 재현 스크립트는 `scripts/check_web_intent_disambiguation.py`다. 기존 사용자 피드백 JSONL은 소스 커밋에서 제외한다.

## 2026-09-28 다음 단계 점검

- 관련 공통 실행 계약 단위 테스트는 컨테이너에서 62 passed, 경고 1건으로 재확인했다.
- `python scripts/check_web_db_connection.py`는 9/11 통과했다. 웹 페이지·health는 200이나 부산/인천 선석 API가 모두 503이었다. 컨테이너 실행 상태만으로 원천 정상 여부를 판단하지 않는다. 이전 11/11은 과거 검증 결과다.
- 다음 최우선은 위 스크립트로 재현되는 선석 조회 503의 원천 연결/조회 경로 진단과 정상화 확인이다. 이후 사고·통항 경로의 공통 계획/실행/근거 계약 감사 → 공식 portrayal 규칙 trace → 전체 처리 lineage → 복합/부정 조건 실제 실행 순서를 유지한다.
- 이번 점검은 신규 Ollama 추론·calibration을 수행하지 않았다. 독립 human gold/holdout 및 지연 검증 전 shadow 실행 권한 승격과 QLoRA는 보류한다.
- 항행 API 회귀는 최종 7/7 통과했다. 부산 선석 API는 별도 재시도에서 실제 FeatureCollection을 반환했다. 최초 503 원인은 미확정이며 지속 장애로 단정하지 않는다. 전체 웹·DB 재검사와 병행 부하 안정성 검증은 남았다. 전체 저장소 테스트와 브라우저 E2E는 이번 점검 범위가 아니다.

## 2026-09-26 공통 오케스트레이터 계약을 속성 검색으로 확대

- [상세 설계·검증·재현 문서](orchestration_execution_contracts_20260926.md)를 추가했다. 사용자 최우선인 후보/문맥 → 계획 → QEC → 실행 검증 → 근거 연결을 S-101 속성 검색에 확장했다. 일반 semantic router/ContextResolver 전체 개편은 아니다.
- `source_attribute_search` operation을 등록하고 RoutePlanner, typed QueryExecutionContext, SchemaBindingAdapter, execution validator, EvidenceBuilder를 사용한다. 원문에서 다시 해석한 매핑과 Feature/속성 조건/registry·FC hash가 일치해야 실행한다.
- 계획 hash, SQL hash, 결과 hash와 query_execution_id를 남기며 슬롯·실행·공간 근거를 같은 실행으로 연결한다. 검증 준비 상태와 실제 실행 성공/실패를 분리하고 DB 장애를 0건 조회로 대체하지 않는다.
- 관련 단위 **62 passed**, 실제 속성 API **10/10**, 선택 객체 API **5/5**, 웹·DB **11/11** 통과. 원본: `outputs/marine-mapping/orchestration-v1.jsonl`, `outputs/selected-feature/orchestration-v1.jsonl`. 의미 정확도·브라우저 E2E·전체 테스트 통과를 의미하지 않는다.
- 마지막 항행 실제 회귀도 **7/7** 통과했다. 통항 분석 PARTIAL, 위치 부족 clarification, 정의 COMPLETED 상태를 유지한다.
- P1 shadow는 신규 모델 추론/승격 없이 유지하며 QLoRA DEFER다. 다음 P0는 사고·통항 등 다른 실행 경로의 동일 계약 감사 → 실제 portrayal 규칙 근거 → 처리 lineage·복합/부정 작업 실행이다.
- 사용자가 요청한 GitHub push에는 앞선 로컬 커밋 `da09b99`, `f845a96`과 이번 코드·테스트·registry·상세 문서를 함께 포함한다. 사용자 피드백 JSONL 및 outputs 실행 원본은 제외한다.

## 2026-09-26 사용자 우선순위: 공통 오케스트레이터와 선택 객체 근거

- 사용자 지정 최우선 축은 semantic router, context resolver, QueryExecutionContext, route planner, execution validator, Evidence builder의 연결이다. 개별 기능을 추가할 때 후보 해석 → 문맥/슬롯 → 계획 → 입력·원천 검증 → 실제 실행 → 근거 → 완료 판정의 일관성을 먼저 검증한다.
- 선택 객체 요청을 기존 후보/semantic slot 해석 뒤 `selected_feature_lookup` 계획으로 연결했다. RoutePlanner registry, typed QueryExecutionContext, SchemaBindingAdapter의 실제 원천 컬럼·SELECT 권한 확인, 공통 execution validator, EvidenceBuilder를 사용한다. 명시 선택 ID·원천은 request 문맥에서 해소하며 일반 ContextResolver/semantic router 전체를 개편한 것은 아니다.
- 선택 객체의 client 속성 대신 `projection.s101_feature_valid`에서 유일한 ID를 조회한다. 원천·ID 누락/오류, 미존재/중복, 원천 장애는 완료되지 않는다. 계획 hash, 실행 ID, 조회 행 hash와 EvidenceBundle 연결을 기록한다. 행 hash는 조회 시점 결과 식별자이며 원천 파일 전체 lineage가 아니다.
- 기존 Python portrayal 선택은 `CANDIDATE_NOT_VERIFIED`, `official_rule_executed=false`로 구분한다. 공식 PC 규칙 실행 trace가 없어 심볼 연결 요청은 PARTIAL/OUTPUT_OBLIGATIONS_UNMET를 유지한다. portrayal 완료를 위해 필요한 공식 rule/symbol binding은 여전히 P0다.
- 초기 직접 조회 버전은 실제 API 5/5 (`outputs/selected-feature/resume-v1.jsonl`), 초기 모듈 단위 9개 통과. 공통 오케스트레이터 연결 이후 최종 검증은 아래 후속 결과로 구분한다. 첫 관련 테스트 실행은 backend 재시작으로 중단되어 통과 집계에 포함하지 않는다.
- 공통 연결 후 선택 객체/완료 계약 **29 passed**, 선택 객체·execution validator·EvidenceBuilder 최종 회귀 **31 passed**(일부 중복). 실제 API `resume-v2.jsonl` **5/5**로 QEC readiness, 실행 ID와 근거 ID 일치까지 확인했다. 최초 공통 검증 회귀는 20 passed/1 failed였으며 바다갈라짐 미적재 테스트가 운영 executable registry에 의존한 fixture 문제를 수정했다. 운영 바다갈라짐 상태는 변경하지 않았다.
- 선택 객체 처리 flag 초기화까지 포함한 최종 코드 재기동 후 `outputs/selected-feature/resume-v3.jsonl` **5/5** 재확인. 정상 객체·portrayal 부분 완료·선택 없음·잘못된 원천·잘못된 ID를 검사했다. 브라우저 클릭과 전체 서비스 의미 정확도는 미측정이다.
- Qwen은 모델, Ollama는 실행 프로그램이다. 현재 융합 대상은 규칙/슬롯/registry와 모델 후보 평가이며 Qwen·Ollama 두 모델의 앙상블이 아니다. 신규 모델 추론·승격은 이번 작업에 포함하지 않는다.
- 다음: 공통 오케스트레이터의 계획/실행/근거 계약 회귀 확대 → 실제 portrayal 규칙 실행 근거 → 처리 lineage 및 복합 요구. 독립 gold/calibration, 일반 문맥 해소의 정확도·지연 검증과 QLoRA DEFER 조건은 유지한다.

## 2026-09-26 재개: S-101 속성 검색과 입력 계약 검증

- 기존 미커밋 FC 참조 파서·매핑 registry·속성 검색 구현을 이어 검증했다. 잠제/수중방파제는 `ShorelineConstruction`의 `categoryOfShorelineConstruction=1 AND waterLevelEffect=3`으로 제한된 검색이다. 누락 속성은 제외하며 전체 실세계 잠제의 완전한 매핑이나 human gold 승인을 의미하지 않는다. 물양장·예선·선유장의 미해결 매핑은 실행을 차단한다.
- 실제 API 초기 `outputs/marine-mapping/resume-v1.jsonl`은 **7/8**이었다. `잠제를 찾아줘`가 장소 이동 단축 경로로 들어가 지도 기준점 확인만으로 COMPLETED를 반환했다. 등록된 원문 용어의 실행 요청은 정식 매핑/슬롯 검사로 보내도록 수정했고 최종 반경 누락 결과는 `NEEDS_CLARIFICATION/RADIUS_REQUIRED`다.
- 속성 검색 실행 함수에서 지도 `exclusions` 및 불일치/복수 `target_features`를 검사하도록 보강했다. 직접 호출에서도 질의 부정 조건을 검사한다. 부정·복합 실행 지원을 완료한 것은 아니며 미지원 조건은 `NOT_RUN`으로 차단한다.
- 최종 실제 API **10/10** 계약 통과: `outputs/marine-mapping/resume-v2.jsonl`. DB의 실제 잠제 조건 객체에서 평가 기준점을 얻고 조회 행의 두 속성, execution ID, 미해결/부정/복합/반경 누락 응답을 확인했다. 의미 정확도나 F1 측정은 아니다.
- 컨테이너 최종 관련 단위 **102 passed**, shadow 계약·평가 **25 passed**. 앞선 graph 포함 회귀 **98 passed**는 일부 중복이며 최종 fast-path 수정 이전 결과다. 호스트 Python은 `structlog` 부재로 수집 실패했다. 재시작 직후 웹/항행 점검은 연결 거부로 실패했고 준비 완료 후 웹·DB **11/11** 통과했다. 전체 저장소 테스트/브라우저 조작 검증을 의미하지 않는다.
- 준비 완료 후 `check_navigation_runtime.py`도 **7/7** 통과했다. 부산/인천 통항 결과는 PARTIAL을 유지하며 위치 없음·먼 위치·미등록 항만과 정의 질의를 함께 확인했다.
- P1: 기존 원문 선택 schema 및 동일 실험 설정 검사 변경을 보존·회귀 검증했다. 신규 Ollama 추론이나 calibration을 수행하지 않았고 `used_for_execution=false`, QLoRA DEFER를 유지한다.
- 다음 P0: portrayal/선택 객체의 실제 근거 산출물 → 전체 처리 lineage → 복합 작업·부정 조건의 실제 실행 지원. 매핑의 의미 범위와 원문 판/human 검수, API 병행 부하 지연 및 readiness 대기는 남은 제한이다. 사용자 피드백 JSONL과 outputs 원본은 소스 커밋에서 제외한다.

## 2026-09-26 해수부 순화어 런타임 연결과 직접 근거 조회

- [구현·검증 문서](mof_terminology_runtime_20260926.md): 기존 4개 순화어 후보를 원문/hash/페이지를 포함한 보조 registry로 만들고 실제 질의 분석·슬롯 trace·검수 양식에 연결했다. 같은 번호 표 행 안에서만 관계를 추출하도록 다음 행 오연결 문제도 수정했다.
- 원문과 선택적 띄어쓰기를 보존하고 접두부·동음이의어·다중어 제외·인용을 구분한다. 미검수 순화어 관계로 Feature/KG/tool 입력을 자동 확정하지 않는다. 매핑 미해결 및 관련 capability 입력 계약을 trace에 남긴다.
- `잠제의 순화어는?`은 기존 일반 경로에서 30.204초 관측 timeout이 발생했다. 명시적 단일 순화어 질문을 원문 registry 직접 조회로 수정했다. 최종 실제 응답은 `terminology_relation_lookup`, 원문 인용·페이지·hash, LLM 미사용이며 1.012초였다. 일반 정의/복합 실행 질문을 이 경로로 대체하지 않는다.
- 관련 단위 45개와 별도 한국어/평가 회귀 48개, 합계 93개 통과. 실제 API `live-mof-terminology-v3.jsonl` 13/13 계약 통과. 초기 readiness 실패와 v2 12/13 결과를 기록했고 대기 시간 설정 및 readiness 별도 기록을 추가했다. 의미 정확도/F1을 측정한 결과는 아니다.
- 다음: 순화어의 의미 범위와 FC/DCEG 객체·속성 관계 검수 및 사전 확대 → 승인된 매핑의 실제 검색·도구 반영 → 독립 gold → Qwen 원문 선택·지연 개선과 동일 입력 비교. 이번에는 신규 Qwen 추론을 하지 않았고 shadow/QLoRA 승격은 보류한다. P0 portrayal·복합/부정 조건 실제 실행도 남아 있다.

## 2026-09-26 해양 근거 색인·공통 정규화 사전·혼합 평가 연결

- [후속 보고서](reference_linkage_and_mixed_evaluation_20260926.md): MOF 원문 12개 및 S-101 FC/DCEG의 6,090개 근거 단위에 원천·텍스트 hash와 페이지/문단/코드 locator를 부여했다. fonttools 평가용 설치로 PDF 경고 340개 단위를 해소했으며 빈 텍스트 22개·제어문자 4개와 판 보류 50쪽을 구분한다.
- query 원문을 유지하며 Kiwi와 semantic binding의 기존 해양/S-101 사전을 통합했다. 정박지→AnchorageArea→기존 KG seed 누락을 실제 API에서 수정 확인했다. 후보 다중성·제외 조건·미존재 Feature 필터는 유지한다.
- MOF 순화어 4개는 원문 구간과 연결된 AI_REVIEW_REQUIRED 후보다. 새 전체 ontology 구축이나 운영 query 자동 치환 완료가 아니다. 검수 양식 100개 중 18개에 근거 후보를 연결했고 gold 참조의 hash/locator/인용/판/검수 상태를 검사하도록 했다.
- 기존 1.5B/4B 동일 10문항 응답을 규칙/Qwen/혼합으로 재평가했다. 입력·문항·prompt·추론 설정 일치를 강제하며 실패를 제외하지 않는다. 독립 human gold와 calibration이 없어 의미 accuracy/F1은 null, 혼합 슬롯/계획 점수도 아직 null이다. 신규 Qwen 호출은 없었다.
- 최종 근거·혼합·사전 단위 테스트 22개와 별도 Kiwi 활성 테스트 1개가 통과했다. API 최초 readiness 실패 0/8을 보존하고 대기 기능을 추가했다. 준비 완료 뒤 실제 API 최종 9/9 통과(침선 실제 도구 실행 및 부정 사례 포함).
- 다음: 현행 법령/지침 최종본 검증 → MOF 용어·관계 검수와 승인된 정규화 반영 → 독립 gold → Qwen 원문 선택·지연 개선 후 동일 후보 실험 확대. P0 portrayal/복합 작업·부정 조건 실행 및 QLoRA 조건부 보류는 유지한다.

## 2026-09-26 GitHub push 및 해양수산부 공식 원문 확보

- 사용자 요청으로 기존 커밋을 `origin/main`에 push하고 원격 `453b58a`를 확인했다. 후속 자료 수집 코드·목록·문서는 별도 커밋으로 push한다.
- [수집 보고서](maritime_reference_acquisition_20260926.md): 해양수산부 공식 첨부 12개(PDF 4/HML 5/HWPX 3), 출처 페이지 7개를 `Dataset/authoritative_references/mof/20260926-v1/`에 보관했다. 실패 0, 19개 hash 재검증, 기존 S-101·사고자료 12개는 중복 다운로드 없이 목록화했다.
- PDF 페이지/일부 본문 및 HML/HWPX XML 확인 완료. 지침 PDF 표지 `2019-xx`와 동반 제정문 사이의 판 불일치는 GOLD_APPROVAL_BLOCKED로 기록했다. 지정 고시의 제외구역·지적경계 조건도 확인해 좌표만으로 자동 공간 적재하지 않았다.
- 원문은 로컬 Dataset에 보관하며 GitHub에는 재현 스크립트·출처/hash 목록·검수 상태를 보존한다. 기존 사용자 피드백 JSONL은 제외한다.
- 다음 참조 작업: 현행 통합법령·후속 개정 확인 → 불일치 자료 판 검수 → 조항/용어 locator 및 canonical ID 연결 → 독립 human gold. 자료 수집은 완료했으나 원천 전체 망라·RAG/DB 적재·gold 승인은 미완료다. 기존 P0 실제 작업 산출물 및 shadow 지연 개선도 남아 있다.

## 2026-09-26 최종 재검증 및 해양 정답 근거 기준

- `web-samples-v4/`: 실제 API 100/100 완료 이벤트, 도메인 FAILED 0, 관측 오류 0. COMPLETED 9 / PARTIAL 15 / NEEDS_CLARIFICATION 68 / BLOCKED 8. 상태 분포는 의미 정확도가 아니며 추가 질문 68건의 필요성은 독립 검수가 남았다.
- 45번은 빈 graph update 수정 후 SQLAlchemy 2.1의 기본 PostgreSQL 드라이버 변경으로 `No module named 'psycopg'`가 발생했다. 기존 psycopg2와 호환되는 SQLAlchemy `>=2.0.31,<2.1`로 고정하고 lock/image를 재생성했다. 실제 2.0.54·psycopg2 확인 후 v4에서 45번 COMPLETED와 오류 없음 확인. 실패 v2/v3 원본을 보존했다.
- `stage-matrix-v1.json`: 동일 원문·ID 100개를 S0와 대조했다. 상태/오류/route/분석유형/계획 도구 중 변화 사례 5개, 관측 오류 0. 슬롯·KG·입력 계약·실행 ID·근거 수를 함께 기록하며 정답 판정은 아니다.
- 기존 광범위 324개 회귀 통과에 더해 최종 이미지에서 평가 지표 테스트 11개 통과(중복 포함). accuracy, macro/micro-F1, 허용 도구 대안·raw 슬롯·clarification 지표를 구현했다. human gold 부재로 실제 의미 점수는 null이다.
- [해양 정답 근거 기준](maritime_evaluation_reference_standard.md)과 `configs/evaluation/maritime_reference_policy.yaml`을 추가했다. 공식 사전 위키와 일반 위키를 구분하고, FC/PC/DCEG·법령·고시·관측 데이터의 적용 범위와 검수 계약을 정했다. 검수 양식에 출처·최소 주장 필드를 추가했다. 정책은 설계 기준이며 원천 자동 수집·서명/진위 검증·런타임 강제 적용은 미완료다.

다음 실행 순서: P0 실제 portrayal/선택 객체 근거·처리 lineage·복합/부정 조건 실행 보강 → 해양 참조 원천 snapshot/locator와 독립 검수 gold 구축 → shadow 원문 선택·지연 문제 개선 → smoke 통과 후 전체 동일 후보 비교. 9B 및 QLoRA 승격 조건은 여전히 미충족이다. 웹 브라우저 조작은 미검증이며 이번 검증은 실제 SSE API/DB 경로다.

## 2026-09-26 한국어 슬롯·온톨로지/KG·도구 계약 구현

최신 구현과 판단 근거는 [구현·평가 보고서](korean_pipeline_implementation_20260926.md), 검수 방식은 [한국어 shadow 검수 지침](korean_shadow_annotation_guide.md)에 기록했다. 아래 9월 25일의 미설치·계획 상태는 당시 이력이며 현재 상태가 아니다.

- S0: 실제 API 100개 기준선과 모델 입력을 고정했다. 실제 후보 trace 85개, 없는 15개를 구분한다. 과거 기준 시각은 없으므로 생성하지 않았다.
- S1/S2: 원문 구간·출처·거리/기간 검증, Kiwi 0.23.2와 모델 0.23.0 고정, registry 사전·토큰 근거, 부정/문맥/수량 공통 검사를 구현했다. 원문/명시 지도 입력에 근거 없는 반경은 제거한다. 부정/제외는 현재 무시한 실행을 차단하는 단계이며 실행 지원 완료가 아니다.
- 온톨로지/KG/도구 연결: 사전 canonical ID→타입 검증 관계→KG seed→capability 입력/출력 계약을 연결했다. 원문·사전·ontology·KG hash와 unresolved 입력을 기록하고 실제 graph RAG seed와 거리 도구 입력에 반영한다. KG 관계를 사실·실행 권위로 승격하지 않는다.
- S3: 공통 종료 노드에서 필수 산출물을 감사한다. 46/47/48/76/84를 재검증했고 관련 없는 문서나 일반 사건 조회로 완료하지 않는다. portrayal 매핑·선택 객체 근거·전체 처리 lineage 자체의 완성은 남았다.
- 실제 API 100개: `web-samples-v1/`, COMPLETED 9 / PARTIAL 14 / NEEDS_CLARIFICATION 69 / BLOCKED 8. 이후 76의 dispatch 수정은 `p0-followup-v2/`에 별도 보존했다. 상태 분포는 정확도가 아니다. 기존 API 계약 13/13, 신규 계약 7/7. 최종 수정 이후 재검증은 구현 보고서의 후속 기록을 따른다.
- S4: Qwen3.5:4b 설치·동일 후보 runner 구현. CPU 실행 대표 10개 시험에서 구조/인용/슬롯 근거 통과 3, 원문 인용 실패 5, 슬롯 거부 1, 120초 timeout 1. p50 95.835초. 의미 정답률이 아니며 전체 모델 100개 평가 완료가 아니다. 해당 설정은 smoke를 통과하지 못해 전체 확대/운영 채택을 보류한다.
- S5/S6/S7: 독립 human gold·calibration·holdout 미확보. 모델 출력 없는 개발 검수 양식 100개를 만들었다. 9B는 검증된 자원 여유와 무 timeout 조건 미충족으로 보류, QLoRA DEFER. shadow는 계속 `used_for_execution=false`다.
- 효율: 요청 내 참조 검증 16→10회, warm 한국어 분석 p50 1.218ms / p95 2.717ms, binding p50 0.239ms / p95 0.661ms를 관측했다. 단일 개발 환경 측정이며 전체 API 개선율을 주장하지 않는다.
- 배포 재현: Kiwi/model/jsonschema 고정과 poetry.lock 추가, Dockerfile packaging 호환 범위·pip check 보강, runtime 산출물을 이미지 context에서 제외했다. backend 새 이미지 재생성 후 관련 324개 테스트, 실제 API 계약 13/13 및 신규 8/8 통과. 실제 항만 후보 선택 후 1852m Wreck 검색 8건과 근거 8개를 확인했다.
- 후속 실패도 보존: `web-samples-v2/`의 45번 legacy 응답에서 빈 graph update가 SSE 종료를 일으켰다. 상태 update를 보존하도록 수정하고 회귀 테스트를 추가했다. 최종 재실행과 상세 근거는 구현 보고서에 기록한다.

다음 순서: 최종 회귀/런타임 확인 → P0의 실제 산출물·복합 작업·부정 조건 실행 보강 → 원문 span 선택 방식의 shadow adapter 개선과 자원 검증 → smoke 통과 후 전체 동일 후보 비교 → 독립 평가 후 승격/QLoRA 판단. 사용자 피드백 JSONL 및 outputs 원본은 소스 커밋에서 제외한다.

## 2026-09-25 한국어 슬롯·Kiwi·Qwen3.5 상세 작업계획

사용자 지정 후속 계획: [한국어 의도·슬롯 보강 및 Qwen3.5 shadow 평가](korean_intent_slot_shadow_plan.md). **계획 문서 작성 완료이며 신규 구현·모델 실험 완료가 아니다.** 원문 구간/단위/부정/문맥 근거 → Kiwi → 작업별 완료 계약 → 동일 후보 Qwen3.5 4B → 독립 평가와 조건부 9B → QLoRA go/defer 순서다.

- 왜: 무근거 반경·날짜, 부정 표현의 사건 필터 오인, 관련 문서만으로 분석 완료, shadow/API 병행 부하를 각각 해결해야 한다. 단일 intent 일치율로 성공을 판정하지 않는다.
- 어떻게: 기존 registry·KG·PostGIS·도구 실행은 유지하고 원문 근거 슬롯 및 필요한 작업 계약을 추가한다. 모델은 고정 후보의 해석과 점수만 제안하며 shadow 결과는 실행에 반영하지 않는다.
- 이번 재확인: backend 실행 및 `/health` 200, Kiwi 미설치, Qwen3.5 4B/9B 미설치. 기존 Ollama 목록은 qwen2.5:1.5b/bge-m3/gemma2다. 저장된 `live-presets-v5` 100개·오류 0 및 `contracts-v7` 13/13을 재확인했다. 이전 단위 177개는 이번 문서 작업에서 재실행하지 않았다.
- 평가: 계획상 필요 작업 충족과 실제 작업 완료를 분리하고, 슬롯 원문/정규화 정확도·무근거 슬롯·불필요 질문·필요 질문 누락·과잉 실행·p50/p95 지연을 측정한다. 웹 100개는 개발 회귀셋이며 독립 holdout으로 재사용하지 않는다.
- 남은 조건: 하드웨어 계측, Kiwi/모델 설치·버전 고정, 독립 human gold와 calibration, 자원 격리. QLoRA는 DEFER다. 문서의 자원·표본 수 기준은 계획값이며 검증된 성능이 아니다.
- 다음 시작점: 상세 계획 S0(snapshot·자원 기준선) → S1(슬롯 근거 schema·단위 검증) → S2(Kiwi·부정 범위·fast path 공통 검사). 기존 P0 46/47/48/76/84는 S2/S3의 필수 회귀로 유지한다.

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

**최신 사용자 지정 우선순위:** [상세 계획](korean_intent_slot_shadow_plan.md)의 S0–S4 구현·검증 현황은 문서 상단과 [구현 보고서](korean_pipeline_implementation_20260926.md)를 따른다. 남은 실제 작업별 산출물과 shadow 원문/자원 문제를 보완하고 smoke를 통과한 뒤 전체 비교를 확대한다. S5 독립 평가 후 조건부 9B/자원 격리, S7 QLoRA 판단으로 이어간다. 아래 기존 순서는 운영 점검 및 잔여 P0 목록으로 유지한다.

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
