# 실제 production graph adapter와 격리 실행 조건

`baselines/production_adapter.py`는 `services.orchestrator.graph.orchestrator_graph.ainvoke`를 직접 호출한다. production graph/node/validator를 대체하지 않는다. 웹 router 자체는 import하지 않아 운영 task store 및 웹 비교 queue를 생성하지 않는다. 초기 state는 운영 `run_langgraph_workflow`와 같은 필드이며 benchmark의 원문과 spatial_context를 사용한다. 요청마다 새 UUID thread_id를 부여한다.

현재 방법명은 **P_current_production_no_llm**이다. Full P·모델동등 비교·실제 웹 API 실험으로 표기하지 않는다. 제한조건은 다음과 같다.

- 운영 소스 전체 read-only mount. feedback 기록은 별도 tmpfs. 결과만 별도 /out에 저장.
- 운영 envfile 사용 안 함. Docker internal 전용망에 연구 snapshot DB만 연결. 기존 DB network 연결은 유지.
- S101_DB_URL/POSTGIS_URL은 marine-scie-pilot-db/scie_pilot만 허용. PGOPTIONS로 read-only transaction 및 statement timeout 적용.
- DISABLE_LLM_API=1. Ollama/OpenAI 호환 주소는 연결 불가능한 localhost:9. capability pgvector off. 따라서 LLM baseline과 모델/embedding/외부의존성 조건이 다르다.
- 실제 운영 fallback은 ChatOpenAI 및 LLM_MODEL/OPENAI_BASE_URL을 읽고, embedding은 Ollama와 EMBEDDING_MODEL(bge-m3 기본값)을 사용한다. 향후 local Ollama 호환 API로 연결할 수 있지만 호출예산·tokenlimit·embedding접근까지 동일하다고 검증한 것은 아니다.

## 관측 기록

20261030 첫 독립 child 방식은 graph import를 각 요청마다 반복했다. 첫90초 timeout을 `runs/20261030_comparison_v2/production/production_rows.jsonl`에 보존했다. 다음 요청 중 자원경합 의심으로 연구 container만 중단했다. 이 결과로 production의 논리 오류나 질의의 공간정답을 판정하지 않는다.

후속 `production_session.py`는 singleton graph를 한 번 초기화하고 `warmup.json`에 import 시간을 분리한다. 각 요청 state는 새로 만들며 MemorySaver thread UUID도 분리한다. 공유 component cache가 유지되는 조건임을 명시한다. 초기 smoke는6개×1회이고 통과 확인 후 새 결과 디렉터리에서6개×3회 실행한다. 각 case는 Linux alarm60초, container launcher는 outer2000초 제한을 갖는다. C 확장 내부 지연에는 signal 처리가 늦어질 수 있어 외부 제한도 필요하다.

root 모델실험과 동시 실행 중 host/docker 도구 조회까지 지연되어 smoke worker도 중단 요청했다. 이는 자원경합 가설이지 측정으로 확정된 원인이 아니다. root 모델실험 완료 후 단독 재개한다. 어떤 중단 run도 성공결과로 교체하지 않는다.

## 캡처와 판정

각 행에 benchmark source_case 원문, initial_state, 최종 graph state, 모든 발견 QEC, evidence bundle, validator receipt를 보존한다. private thinking/chain_of_thought와 credential 필드는 제외한다. graph 반환을 실행성공으로 변환하지 않으며 execution_success/spatial_correct는 독립 증거 없으면 null이다. clarification과 BLOCKED는 실패로그와 구분해 원래 graph_status로 남긴다. GOLD는0이다.

source image ID와 graph/adapter/benchmark hash는 adapter_manifest.json에 남긴다. 원본20261029 pilot은 변경하지 않는다. graph code 수정 없음.

## 재현

연구 internal network `marine-scie-graph-isolated`와 snapshot DB가 연결돼 있어야 한다. 최초 생성/연결은 수행했으며 생산서비스는 중단하지 않는다.

```powershell
.\.venv\Scripts\python.exe -m pytest research/marine_geollm_scie/tests/test_production_adapter.py -q
.\.venv\Scripts\python.exe -m research.marine_geollm_scie.runners.launch_production --session --repeats 1 --output-dir D:\An_GeoLLM\research\marine_geollm_scie\runs\20261030_comparison_v2\production_session_smoke_retry1
```

동일 output directory에 raw가 있으면 재실행은 거부된다. 기존파일 삭제·덮어쓰기 대신 새 run path를 사용한다. smoke 관측을 확인한 후 `--repeats 3` 및 별도 경로로 확장한다.

## 다음 재개 시 import 지연 관측

`production_session.py`는 actual graph import 전에45초 단발 faulthandler를 등록하여 `/out/import_stack.log`에 thread stack만 기록한다. 환경변수·local 변수·비밀값을 출력하지 않는다. import가 끝나거나 예외로 종료되면 예약을 취소한다. `--import-stack-after 0`으로 비활성화할 수 있다. 파일은 신규 생성 모드라 과거 관측을 덮어쓰지 않는다.

연구 launcher는 `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`을 명시한다. 캐시에 없는 Hugging Face 모델이 필요하면 자동 다운로드를 시도하는 대신 해당 제한이 실패로 드러나야 한다. 이 조건은 manifest에 기록되며 모델 baseline과 같은 조건이라고 주장하지 않는다. 기존90초 timeout의 원인이 Hugging Face 대기 또는 자원경합이었다고 아직 확정하지 않는다. 현재 변경은 재개 준비이며 graph를 실행하지 않았다.
