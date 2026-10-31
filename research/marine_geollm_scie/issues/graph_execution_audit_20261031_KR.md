# 18문항 graph 실행 오류 감사 — 2026-10-31

## 범위와 원본 보존

대상은 `research/marine_geollm_scie/runs/20261030_full_execution_v5/graph/`의 `production_rows.jsonl`, `model_calls.jsonl`, `stdout.log`, `model_graph_manifest.json`이다. 읽기 전용으로 대조했으며 원본 관측을 수정하지 않았다. 이 문서의 오류 분석은 독립 human GOLD 채점이 아니다.

graph 관측 18건은 COMPLETED 10, BLOCKED 4, NEEDS_CLARIFICATION 3, PARTIAL 1이다. GRAPH_RETURNED 및 COMPLETED를 전체 작업 정답률로 해석하지 않는다.

## Qwen 생성 호출의 실제 실패

- proxy 호출 118건 중 RETURNED 107, PROXY_ERROR 11이다. 초기 준비 85건과 문항 실행 33건을 구분한다.
- 초기 준비는 `/api/version` 1회와 `/api/embeddings` 84회다. 문항 실행은 `/api/embed` 22회 성공 및 Qwen `/api/generate` 11회 실패다.
- Qwen 11회 모두 `client_disconnected=true`, `RemoteDisconnected`, 2.53~2.66초이며 성공 생성 응답은 없다. `stdout.log`의 semantic prior timeout 11건과 일치한다.
- 운영 `services/orchestrator/semantic_prior.py`는 `GEOLLM_SEMANTIC_PRIOR_TIMEOUT_SEC` 미지정 시 2.5초를 사용한다. 해당 연구 조건은 운영 기본값을 보존했으며 proxy가 caller 취소 후 upstream 연결을 닫았다. 모델 의미 오답이나 JSON 생성 실패로 분류할 수 없다.
- 따라서 이 run은 **Qwen 호출을 시도했지만 생성 결과를 활용하지 못한 graph**다. 정상 Qwen을 사용한 P와 baseline의 비교, Qwen 추가 효과 또는 모델 우열로 주장할 수 없다. fallback을 포함한 운영 조건 관측으로 보존한다.

## 사례별 원인 구분

| 사례 | 관측 | 분류 및 후속 |
|---|---|---|
| Q1_01·Q1_02·Q2_01 | 정의·속성 요청에 STANDARD_RAG 후보가 있지만 지명 반경 fast path로 들어가 GAZETTEER_UNAVAILABLE. 정의 질문의 일부를 위치로 추출 | 의도→실행 연결 구현 오류와 연구 원천 누락이 겹침. 위치가 불필요한 요청부터 분리해야 함 |
| Q2_02 | 제한구역의 코드 설명을 비공개 보안자료로 차단 | `graph.py::_looks_like_policy_block_query`의 제한구역/restricted 단어 검사에 의한 오차단. 공개 객체 정의와 권한 없는 자료 요청 구분 필요 |
| Q3_03 | selected AOI 없는 intersects 요청이 Wreck 문서 2건 검색으로 COMPLETED | 공간 필수 입력·산출물 의무 누락. AOI 요청이 필요 |
| Q5_01 | 등대+난파선 요청에서 target_features는 Wreck만 남고 0건 COMPLETED | 복합 대상과 각각의 근거 누락. 부산권 subset의 독도 0건을 실제 독도 전체 부재로 해석하면 안 됨 |
| Q3_01 | 가장 가까운 등대 요청을 radius로 처리하며 반경 요구 | nearest/radius 계약 오류 후보. 독도 항로표지 coverage 부족은 별도 문제 |
| Q3_02·Q5_02 | 부산항 다중 후보로 LOCATION_UNCONFIRMED | 확인 요청 자체를 오류로 단정하지 않음. Q3_02의 영역 안 의미가 radius·위치 문자열로 바뀌는 부분은 별도 검증 필요 |
| Q5_03 | Wreck 0건 및 속성 설명 누락을 PARTIAL/OUTPUT_OBLIGATIONS_UNMET로 표시 | 부족한 산출물을 올바르게 노출. 표준 속성 설명 생성과 공간 coverage는 아직 부족 |
| Q6_03 | AnchorageArea를 Anchor재령Area로 정규화하나 원문 대체 경로로 FC 정의 반환 | 정규화 결함. 이 사례 최종 답변 실패와 동일시하지 않음 |

Q1_03/Q2_03/Q3_03/Q6_02는 graph-scoped 유사도 0.6 미만 이후 metadata vector fallback을 수행했다. Q2_03 속성 요청의 요약은 Wreck 정의 발췌, Q6_02 등대·부표 구분 요약은 topmark 도형 목록이다. 검색 성공만으로 답안 범위 충족을 확정하지 않는다.

## 연구 환경의 제한과 정상 관측

- `public.codeinformation` 부재로 NFTC DB 조회가 2회 실패했으나 로컬 S-101 catalogue fallback이 작동했다.
- `public.maritime_gazetteer_khoa`는 연구 snapshot에 없어 unavailable로 기록된다. Q1/Q2의 차단을 순수 원천 장애로만 분류하면 불필요한 공간 경로 진입 오류를 숨기게 된다.
- Q4 세 표현 모두 5,000m·11건을 반환했다. 동일 지리조건의 동등 표현이며 독립 표본 3개가 아니다.
- Q6_01 Wreck·Q6_03 AnchorageArea는 FC 정의와 근거 위치를 답변에 연결했다. 전체 문항 의미 정확도로 일반화하지 않는다.

## 별도 수정 및 재실행 원칙

1. 연구 runner의 명시적 timeout 조건으로 성공 Qwen 호출 가능성을 검증한다. 원본 v5 run과 운영 기본값은 보존한다.
2. 정의/속성의 공간 fast path 오진입과 공개 제한구역 설명 정책 오차단을 별도 수정한다.
3. selected AOI·복합 대상·coverage·최종 산출물 의무를 보강한다.
4. 운영 변경은 단위 테스트 외에 실제 API의 정상·부정 사례로 검증한다. 수정 전후 실험은 새 run ID로 분리한다.

이번 감사에 따른 연구 timeout 조건 구현은 준비됐으며 실제 모델 재실행은 이 문서 작성 시점에 수행하지 않았다. 자세한 사용법은 `protocol/model_graph_timeout_condition_20261031_KR.md`를 따른다.
