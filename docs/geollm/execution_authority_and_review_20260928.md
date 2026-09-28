# 실행 검증과 Evidence 검토 UI — 2026-09-28

## 적용 범위

- RoutePlanner는 PLAN_READY 후보만 제안한다. EXECUTION_READY 부여는 ExecutionValidator의 공통 종료 함수로 모았다. 위치 표시, 정의/문서 조회, 사고 조회, 진단, 반경·영역·최근접·레이어 검색, 통항 및 UPort 실행 경로는 실행 전에 검증한다.
- 검증 결과에는 authority, operation, revision, 입력·슬롯·binding hash를 기록한다. 승인 플래그만 있거나 검증 후 슬롯이 변경된 QEC는 승인으로 취급하지 않는다. 이 hash는 변경 감지용이며 보안 인증 토큰이 아니다.
- 실행 성공/실패와 사전 실행 허용은 다른 상태다. SQL 성공 여부로 실행 허용을 사후 부여하지 않는다. 공간/시계열/예측 Agent는 검증 기록을 확인한다.
- 반경은 질의 또는 지도 문맥에서 명시해야 한다. 위험객체 3km와 사고 10km 기본값을 제거했고 최대 50km 정책을 공유한다. 영역 질의는 지도 bounds를 사용할 수 있다.

## UI

- 주요 메뉴의 **Evidence 검토·승인**으로 기존 후보 검토/승인/반려/보류 및 registry 병합 기능을 이동했다. 별도 작업의 관리자 메뉴와 공존한다.
- 질의 결과 아래에는 요청별 규칙/Qwen/동일 가중치 융합 비교를 접어 볼 수 있는 근거로 표시한다. 새 요청이 이전 요청의 비교 폴링을 취소하지 않는다.
- 검토 화면은 SQLite에 보존된 최근 30개 요청의 원문, 실제 정규화, 문맥, 슬롯, 세 순위, 모델 해석, 실행 상태/차단 사유와 버전을 제공한다. 미기록 정규화를 추정해 채우지 않는다.
- Evidence 승인, human gold, 실행 승인은 별도다. 모델은 shadow 후보 평가만 수행하며, 순위 불일치만으로 의도 오류·기능 미지원을 판정하지 않는다.
- 질의창과 지도/결과 패널 높이는 공통 CSS 변수로 맞춘다. 질의 내역만 내부 스크롤하고 입력창은 고정한다. 모바일 높이는 420px이다.

## 검증과 한계

- 실행 validator/기존 gate/Qwen 비교/UPort 110 passed. 그래프 반경/실행 dispatch/속성/정의/통항 134 passed. 추가 회귀에서 변경된 반경 정책 기대값과 신규 이력 fixture를 보완했다. 최종 반경·통항·승인 기록 회귀 93 passed. 서로 중복되므로 수치를 합산하지 않는다.
- 새 검토 이력의 재시작 보존·요청 생성 순서, 실제 정규화 보존, 단순 READY 플래그 거절, 슬롯 변경 후 승인 무효화를 테스트한다.
- 실제 서비스 검증 스크립트: `python -m scripts.check_execution_authority_runtime --output outputs/web-intent-audit/<새 파일>.jsonl`.
- 첫 실제 검증 v1은 30초 SSE 관측 제한으로 정상 경로 3개가 관측 실패했다. 지도 이동은 작업 조회 API에서 COMPLETED 및 validator 승인 기록을 별도로 확인했다. 관측 제한을 180초로 늘린 v2는 **5/5 통과**했다. 정상 3개는 COMPLETED 및 validator 승인, 반경 누락/초과는 각각 NEEDS_CLARIFICATION/BLOCKED다. UI 자산과 검토 이력 API도 확인했다. 타임아웃 원본을 보존하며 지연을 해결했다고 해석하지 않는다.
- 브라우저 도구는 Windows sandbox helper 초기화 실패로 실제 메뉴 클릭, 긴 대화 스크롤, 지도 재표시의 렌더링 E2E를 검증하지 못했다. 정적 JS 문법/API 자산 응답 검사는 렌더링 검증을 대체하지 않는다.

## 다음 실행 순서

최신 중단 지점은 `remaining_work_roadmap.md` 맨 위 인계 절을 우선한다. 이후 registry 전체 공통 진입 gate와 조사용 계약, Standard RAG 원천 검사, 슬롯 변경 승인 무효화, DSL 50km/최근접 기본 1개를 추가했다. 최신 변경의 배포/API 재검증은 사용자 중단 요청으로 다음 세션에 남겼다. 아래 1번의 전체 진입점 연결은 구현했지만 전체 런타임 검증이 끝나지 않아 Phase A 완료로 표시하지 않는다.

1. **Phase A — 진행 중**: 일반 Standard RAG/비실행 보조 Agent까지 포함한 전체 registry 진입점 QEC 감사, legacy 계약의 정리, 실행 전후 상태 및 재개 시 정책 일관성 회귀를 완료한다. 이번 변경만으로 ‘모든 Agent QEC 완료’로 판정하지 않는다.
2. **Phase B**: AIS/V-PASS, 수치조류, 바다갈라짐, Observation의 실제 원천·기간·커버리지·실행 adapter를 검증한다.
3. **Phase C**: KG review, 인용 근거, 처리 lineage, 공식 S-101 portrayal 실행 trace를 완성한다.
4. **Phase D**: 사람 승인 자료 3 → 30 → 300+, hard negative/대화/복합/실패 사례와 독립 holdout을 확보한다.
5. **Phase E**: strict benchmark, CI/CD, 성능 SLO, 관측 및 모니터링을 구성한다. 현재 지연은 SLO 충족 근거가 아니다.
6. **Phase F**: FastPath 및 capability retriever 학습을 평가한다. Planner QLoRA는 gold/holdout/반복 오류/회귀 평가/rollback 조건이 충족된 후 최종 결정한다. 현재 DEFER.
