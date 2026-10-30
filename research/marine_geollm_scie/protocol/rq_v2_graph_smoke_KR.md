# RQ v2 실제 오케스트레이터 격리 실행

2026-10-30, `runs/20261030_rq_v2_graph_smoke/`에 기존 운영 graph의 실제 실행을 새 run으로 기록했다. 연구 snapshot DB만 접근 가능한 Docker internal network, 읽기 전용 DB transaction, 빈 `.env` 마스크, 별도 feedback tmpfs를 사용했다. 운영 DB·서비스를 중단하거나 수정하지 않았다.

## 실행 조건

- 방법 이름: `P_current_production_no_llm`. 모델 호출과 pgvector capability 검색을 비활성화했다. B0–B4와 동일 모델 조건인 P0/P1이라고 주장하지 않는다.
- 운영 `orchestrator_graph.ainvoke`를 호출한다. node/validator를 mock으로 대체하지 않는다.
- 사례 6개, 각 1회. graph singleton warm cache를 공유하되 요청마다 UUID·초기 state를 분리한다.
- 초기 graph import 실측: 13,762.6ms. 이전 run의 import timeout 원인은 여전히 미확정이며 이번 성공으로 과거 실패를 삭제하지 않는다.
- launcher exit code 0. 실제 6개 graph 응답을 보존했다. manifest에 기록된 graph/adapter/benchmark 3개 소스 해시는 실행 후에도 일치했다. 모든 의존 파일의 불변성을 검증했다는 뜻은 아니다.

## 관측

| 사례 | graph 상태 | 질의 처리시간(ms) | 관측 |
|---|---|---:|---|
| PILOT_Q1_03 | BLOCKED | 20837.8 | 문서 source/schema/SELECT binding 미확보 |
| PILOT_Q2_03 | BLOCKED | 343.7 | 문서 source/schema/SELECT binding 미확보 |
| PILOT_Q3_03 | BLOCKED | 270.5 | Standard RAG 경로 및 문서 binding 차단; AOI 부재 판단과 구분 필요 |
| PILOT_Q4_01 | BLOCKED | 2073.2 | serving.marine_gazetteer_current 미적재 |
| PILOT_Q5_03 | COMPLETED | 1342.6 | Wreck 반경 5000m, SUCCESS_EMPTY, 속성 설명 누락 의심 |
| PILOT_Q6_03 | BLOCKED | 435.7 | 문서 source/schema/SELECT binding 미확보 |

`GRAPH_RETURNED`는 도구 실행 성공이 아니다. 차단 5건을 일반 오답 또는 안전 정답으로 자동 판정하지 않았다. 연구 DB는 원본의 25,300행 부분집합이며 전체 자료가 아니다. Q5의 0건만으로 잘못된 공간 결과라고 단정하지 않는다. 독도 동도 기준점은 운영 원천 후보이며 독립 Spatial GOLD 승인은 아니다.

Q5는 원문에서 `explain their S-101 attributes`도 요청하지만 최종 응답에는 반경 조회 요약만 있고 RAG/KG 근거 수는 0이다. 원문 산출물 계약의 누락 후보로 별도 시스템 수정 에이전트에게 실제 API 재현을 요청했다. GOLD를 보고 runtime 정답을 고정하거나 이 관측을 논문 SSFR/EVQSR로 바꾸지 않는다. 후속 수정과 재측정은 별도 run에 남긴다.

## 재현 및 남은 조건

```powershell
.venv/Scripts/python.exe -m research.marine_geollm_scie.runners.launch_production --session --repeats 1 --output-dir D:/An_GeoLLM/research/marine_geollm_scie/runs/<새이름>
```

본실험은 공통 데이터/문서 snapshot, 비교가능한 모델 및 retrieval 조건, 실제 실행 baseline, post-validation/recovery 측정, 승인된 독립 GOLD/holdout이 더 필요하다. 이번 scope를 component 결과와 합쳐 Full P 성능으로 집계하지 않는다.
