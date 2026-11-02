# 대시보드 19질의 공동 검증 인계 — 2026-11-03

## 후속 승인에 따른 통합 진행 (2026-11-03)

아래 기존 보류 기록 이후 사용자가 질의창 전반의 오류 수정과 항만 원문·사진 연결을 요청했다. Codex 소유 변경을 적용하고 Python/Node 회귀 검사 및 backend 재시작을 수행했다. Antigravity 관리 메뉴·PDF 작업 등 무관한 변경은 보존했다. A–D 보고서를 현재 편집 파일 목록으로 간주하지 않았다.

- 현재 UI 예시 100개와 기존 19개를 합쳐 중복 제거한 116개를 `scripts/verify_dashboard_requests.py`로 순차 점검 중이다. 결과 원본은 `outputs/dashboard_full_replay_20261103_v1`에 저장한다. 각 응답의 완료·추가 입력·미지원·데이터 한계를 구분하며 논문 성능으로 사용하지 않는다.
- 00–18 실제 API에서 입구 위치 미확정/반경 누락 구분, 독도 5km 지명 11개, 정의 비교 2개 원문, 최근접 항만 미지원 구분을 확인했다. 목포항 DB 잠금은 이번 응답에서 재발하지 않았지만 원인 전체 해결을 주장하지 않는다.
- 인천항의 4개 하위 항만 원천 카드·출처와 후보 선택 지도 반영을 실제 브라우저에서 확인했다. 사진 참조는 있으나 이미지 실체 미확인, 손상 본문은 표시 보류다. 상세는 `harbour_evidence_cards_20261103.md`.
- XLSX 품질 receipt를 `20261103_v4_xlsx_quality`로 게시했다. 본문 셀 미검증 35개를 근거에서 제외했다. 이전 문서의 미게시 상태는 과거 기록이다.
- 실제 판독에서 최종 경로에 shadow 후보 경로가 남는 문제와 특정 파일 질의의 출처 우선순위 오류를 발견했다. 실행 중 backend를 바꾸지 않고 별도 수정안을 준비한다. 원본 점검을 덮지 않고 수정 후 대표·부정 사례를 다시 검증한다.
- 이 점검은 운영 개발 점검이다. UI 파일 보완 및 별도 PDF 데이터 작업이 있어 전체 실행을 불변 데이터의 논문 frozen run으로 취급하지 않는다. 연구/GOLD/홀드아웃은 변경하지 않는다.

## 병행 작업 원칙

사용자가 Antigravity에도 운영 소스 수정을 요청했다. Codex는 추가 소스 편집, 운영 receipt 게시와 backend 재시작을 보류하고 공동 검증을 담당한다. 아래 범위는 Codex의 기존 변경이며 Antigravity의 작업 배정이 확정됐다는 뜻은 아니다. 같은 파일을 고치기 전에 현재 diff와 이 기록을 확인한다. 기존 변경을 reset/checkout으로 지우지 않는다.

검토 입력: `outputs/api_probe_20261102_v1/review_A.md`부터 `review_D.md`. 네 문서는 모두 읽기 전용 판독이라고 명시하며 Antigravity의 현재 수정 파일 목록/완료 선언은 아니다. 원래 raw 응답과 나중에 읽은 소스의 버전이 같다고 가정하지 않는다. 연구 결과, GOLD와 홀드아웃은 수정하지 않는다.

## Codex 기존 수정 범위

| 범위 | 파일 | 현 상태 |
|---|---|---|
| 위치 슬롯/명시 지명과 viewport 우선순위/복합 누락 질문 | services/orchestrator/s101_radius_execution.py | 단위 검증, 최종 API 재검증 대기 |
| 항만 대표점을 입구로 선택하지 못하게 하는 계약 | services/spatial_analysis_agent/place_resolver.py | 초기 후보 태그 후 최종 재검증 필요 |
| 비교 실패·미측정 표시/선택 불가 후보 UI | services/orchestrator/static/intent-comparison.js, execution-view.js, radius-results.js | Node 검증, 실제 브라우저 렌더링 미확인 |
| XLSX 셀 본문 미검증 근거 제외 | services/orchestrator/dataset_verification.py, dataset_answer.py, graph.py, services/standard_rag_agent/vdb.py | 관련 50 tests 통과. 이후 추가 sidecar 검사 최종 수집 확인 필요 |
| 품질 receipt 감사/게시 | scripts/audit_xlsx_receipt_quality.py, scripts/publish_dataset_verification.py | 임시 게시/35개 제외 검증. 운영 게시하지 않음 |

`graph.py`는 Codex의 근거 제외 상태 추가와 Antigravity의 라우팅 수정이 충돌할 가능성이 가장 높다. 파일 전체 교체 대신 각 hunk를 대조해야 한다. 테스트 파일도 기존 변경을 보존한다.

현재 소스 10개 사본과 SHA: `outputs/api_probe_20261102_v1/codex_coordination_20261103/source_snapshot.json`. 이는 실험 freeze나 배포 증명이 아닌 병행 편집 전 비교 기준이다.

## A–D 판독 대조 및 통합 검증 목록

| 사례 | 확인할 내용 | 구분 |
|---|---|---|
| 0–1, 3 | 부산항 입구 텍스트 보존, 좌표 미확정과 반경 누락 함께 표시, 다른 해역 viewport로 대체 금지 | Codex 기존 수정 대상. 배포 후 재검증 필요 |
| 2, 4 | 띄어 쓴 위험 객체/위험물도 공간 대상 의도 유지; clarification_required가 내부 오류문으로 노출되지 않음 | 상류 라우팅/계약 추가 검증, 수정 완료 아님 |
| 5–7, 9, 11 | 동일 라벨 후보의 원천·객체 종류·대표점 역할 구분; 후보 없음과 복수 후보 구분 | 후보 정체 원문/DB 검증 필요. island 접두어만으로 오답 단정 금지 |
| 8 | 목포항 database is locked 실제 stack/경합 원인 및 단독 재현 | 원인 미확정, 지명 부재/사용자 입력 문제로 바꾸지 않음 |
| 10 | 독도 5km 원천 한정 11개 정상 경로 유지, 실행 권한 표시 단계 구분 | SOURCE_DOMAIN_NOT_DECLARED 자체는 source-bound 실행 결함 아님 |
| 12–13 | 모호 질문에서 필요한 위치·대상·범위를 묻고 실행하지 않음 | BLOCKED_DATA/unsupported operation 문구와 분리 |
| 14, 16, 18 | 항로 안전성·최근접·개념 비교를 질의 전체 지명으로 해석하지 않음 | 키워드 하나로 경로 수정하지 않으며 기능 미지원과 슬롯 누락 구분 |
| 15 | 실세계 빠짐없음 요구와 원천 한정 조회를 구분한 이유 설명 | 반경만 추가하면 완전성 보증된다는 안내 금지 |
| 17 | S-101 정의에 검증표 저장 XML 숫자열을 본문 근거로 쓰지 않음 | 기존 receipt 품질 결함 35개 확인. 제외만으로 정의 답변 완성 아님 |

현재 코드에서 `_matches`와 `_has_unbound_qualifier` 중복 정의가 각각 2개인 사실은 직접 확인했다. 뒤 정의가 적용되므로 제거 전에 동작 차이/회귀 테스트를 확인해야 한다. 이 기록에서는 소스를 수정하지 않았다.

review B의 probe `n_features` 딕셔너리 키 수 집계 의심은 서비스 결함과 별도로 원본 FeatureCollection 기준 재계수한다. 리뷰의 지리 상식 기반 좌표 오매칭 추정은 원문/객체 유형 검증 전 확정하지 않는다.

## 검증 순서와 남은 단계

1. Antigravity 수정 파일/완료 시점 확인 → 기존 소스 사본과 diff 대조 → 파일별 작업 소유권 확정.
2. 안정된 소스 hash 전후 동일 여부를 확인하면서 영향 범위 Python/Node 회귀 검사. 실행 중 바뀐 파일의 테스트를 최종 통과로 간주하지 않는다.
3. 양쪽 수정이 준비된 동일 버전으로 backend 한 번 재시작. 기존 PDF 임베딩 worker는 별도 보존한다.
4. 19질의 새 run을 만들어 raw/SSE/최종 응답, source hash와 실제 서비스 상태를 저장한다. 기존 probe 원본은 덮어쓰지 않는다.
5. 정상 독도 조회, 입구 미확정, 지도 문맥 충돌, 범위 밖/완전성 요구, 개념 질의와 무근거 질의 모두 확인한다. API 결과와 UI 표시를 별도 검증한다.
6. 관련 변경만 소유권 확인 후 커밋한다. 현재 연구 전체 재실행/홀드아웃/추가 push는 하지 않는다.

기존 통합 163 tests와 RAG 관련 50 tests는 서로 중복이 있고 검사 도중 추가된 변경도 있어 합산하거나 최종 통합 통과로 표시하지 않는다. 운영 적용 및 19질의 최종 회귀는 아직 미완료다.
