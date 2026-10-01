# Phase A 운영 원천 및 UI 검증 — 2026-10-01

## 결과와 범위

Phase A 후속으로 실제 원천별 Agent 호출과 웹 UI/API를 검증했다. Phase A 전체 완료는 보류한다. 운영 파일이 없는 시계열과 테스트 fixture가 실행 가능한 것으로 승인되는 경로를 막았다. 파일 경로는 정규화 후 프로젝트 루트 내부인지 검사하며, fixture 경로 별칭, 없는 파일, 디렉터리, 미지원 확장자는 binding 전에 차단한다. 파일 내용/열/권한 변경의 모든 경우와 파일 교체 race까지 검증한 것은 아니다.

## 실제 운영 원천 직접 호출

`scripts/check_specialist_contract_runtime.py`는 실행 중인 backend 컨테이너에서 registry Agent를 직접 호출한다. HTTP나 브라우저 전체 파이프라인 검증으로 간주하지 않는다.

| 사례 | 관측 | 시간 |
|---|---|---|
| 일반 RAG | COMPLETED, 실제 문서 2건, ExecutionValidator receipt | 21.403초 |
| 사고 관계 | COMPLETED, 실제 feature 702036 연결 관계 5건 | 2.004초 |
| tidal_current_surface | 미준비 원천 BLOCKED, 도구 미실행 | 0.606초 |
| sample_observation_timeseries | fixture BLOCKED, 도구 미실행 | 0.741초 |
| unregistered_observation | 미등록 원천 BLOCKED, 도구 미실행 | 0.680초 |

RAG 검색은 낮은 유사도로 metadata fallback을 사용했다. 조회 성공을 답변 적합도나 정확도로 해석하지 않는다. 최초 RAG v1은 수정 중 들여쓰기 오류로 실패했고 수정 후 v2가 통과했다. 원본은 `outputs/phase-a/20261001-*-v*.json`에 보존한다.

재현: `docker exec geollm_backend python -m scripts.check_specialist_contract_runtime --case rag --output outputs/phase-a/<새 파일>.json`. case는 rag/accident/tidal/fixture/missing이다. 기존 결과 덮어쓰기는 거절한다.

## UI 및 실제 API

- backend 재시작 후 `scripts.check_execution_authority_runtime.py` 실제 HTTP 검증 **6/6 통과**: 이동/정의/1km 조회 승인, 반경 누락 추가 입력, 60km 차단, 동일 작업 1km 추가 입력 시 revision 2와 새 승인. 결과: `outputs/web-intent-audit/20261001-phase-a-runtime-v1.jsonl`.
- 브라우저에서 Evidence 메뉴 전환 및 검토 화면을 확인했다. 승인 버튼은 누르지 않았다. 분석 아래 규칙/Qwen/융합 비교 영역도 확인했다. 이번 UI 관측만으로 Qwen 비교 완료나 calibration을 주장하지 않는다.
- null/빈 평가 점수가 0%가 되던 요약 표시를 `미평가`로 수정했다. 측정된 0은 0.0%로 유지한다.
- 뒤 단계가 끝났다는 이유로 앞의 모든 Agent를 완료 표시하던 로직을 제거했다. 완료 이벤트에서 기존 진행 표시를 정리하며, PARTIAL 응답은 부분 결과라고 안내한다. 전문 Agent별 실행 이벤트 전체 연계는 후속 작업이다.
- 질의창과 지도 패널 실측 높이 모두 529.96px. 내역 높이 417px/내용 5645px로 내부 스크롤을 확인했고 Home 키로 맨 위까지 이동했다. 입력 영역은 패널 하단에 남는다. 이 화면 크기의 확인이며 전체 반응형 검증은 아니다.
- 화면 증거: `outputs/phase-a/20261001-ui.png`, `20261001-panels.png` (커밋 제외).

## 발견된 P0와 다음 순서

1. 웹 질의 `수로 측량 데이터 품질 관리 관련 근거 문서를 검색해줘`가 DATA_DISCOVERY / dataset_evidence_lookup으로 처리되며 사고 데이터 중심 8 source/19 chunks를 반환한다. Semantic Prior에 `근거`→`근처` 변형이 관측됐다. 실제 웹 정규화/후보 점수/라우팅을 단계별로 조사해야 한다. 이 변형이 최종 라우팅의 유일 원인이라고 단정하지 않는다. **의도/근거 적합성 오류이며 RAG 실행 기능 미지원과 구분한다.** 위 질의로 브라우저에서 재현된다.
2. 운영 원천 권한/열/Agent/슬롯 변경 후 재검증 범위와 실제 시계열 양성 원천을 확보한다. fixture를 운영 데이터로 승격하지 않는다.
3. Phase A 완료 판단 후 Phase B의 AIS/V-PASS 기간·커버리지, 수치조류, 바다갈라짐, Observation 실제 adapter로 진행한다. parser & Map_viewer는 기존 가능성 검토 문서의 proxy/좌표/타일 검증 순서를 따른다.

## 회귀 및 제한

- Python 관련 회귀 **117 passed, 34 warnings**: time_series_source_contract, agent_execution_contracts, execution_validator, execution_gate_regressions.
- Node UI **12 passed**: `node --test tests/unit/test_query_summary.js tests/unit/test_radius_ui.js`. 최초 실행에서 기존 DOM mock의 querySelectorAll 누락 및 오래된 기준 위치 문구 기대값이 발견되어 현재 UI 계약에 맞춰 수정했다.
- 규칙/Qwen/융합은 shadow, calibration UNFITTED, human gold 미승인, QLoRA DEFER 유지. 전체 정확도/성능 SLO 통과를 뜻하지 않는다.
- 공유 관리자 UI/로드맵 절, 피드백 JSONL, 실행 출력은 이 작업 소스 커밋과 분리한다.
