# 후속 우선순위 수정과 검증

운영 수정과 연구 개발을 분리한다. 기존 v3 144+27 관측은 보존하며 새 개발 호출을 기존 논문 점수에 합치지 않는다.

## 운영 실행 버전

place resolution과 일부 lookup/graph/mapping/traffic/선택 객체 경로가 새 QEC를 만들 때 revision을 생략해 기본1로 돌아갔다. 요청의 execution_revision 또는 부모 QEC revision을 전달하도록 수정했다. 실행 권한은 기존 ExecutionValidator만 부여한다.

관련 운영·연구 회귀 통합102개 통과. 기존 사용자 변경이 있던 place graph 테스트는 수정하지 않고 실행했으며 revision3 보존 사례도 통과했다. 실제 API `outputs/priority_runtime_20261101_v1`에서 영역 누락→NEEDS_CLARIFICATION, 동일 task 추가 입력→COMPLETED 및 최종 orchestrator_v2 QEC revision2, 정상 공간 검색18건을 확인했다.

## Shadow 표시용 순위

기존 모델의 scores와 selected 이중 생성은 모순될 수 있었다. 새 응답은 scores와 명시 abstain만 생성하고 유일 최고점일 때만 표시 후보를 파생한다. 동점은 유보한다. legacy 응답 검사는 유지하며 원본 selected를 사후 수정하지 않는다. 파생 근거와 used_for_execution=false, calibration UNFITTED를 기록한다.

첫 실제 API 개발검증에서 점수2 등 0~1 범위를 벗어난 출력이 거절됐다. 이를 클램핑하지 않고 원본 실패를 보존했다. 후속 v3 표시 계약은 JSON Schema enum으로 0~1의0.1 간격 점수만 생성하도록 제한한다. 이는 확률이 아니라 양자화된 순위 점수이며 기존 연속 점수와 calibration 결과를 혼합하지 않는다. 후속 단위41개 통과. `outputs/priority_runtime_20261101_v2`의 실제 정상 공간검색18건과 후속 shadow COMPLETED/accepted를 확인했다. 이는 대표1건의 구조·근거 검사 통과이며 전체 의도 정확도 검증이 아니다.

## 연구 개발의 실패도 보존

- LLM 검토 v2의 명시 initial_checks 추가는 개발4건 모두 형식 통과했지만 정상 외 오류3건도 모두 pass/invalid=false로 판단했다. 의미 오류 해결로 인정하지 않는다. `outputs/review_priority_development_20261101_v1`.
- B3 최초 계획의 source 배열/설명문 복사 문제는 typed tool schema로 제약했다. 새 개발2건은 형식 통과했으나 정상 공간 질의에 clarify+catalogue 도구, geometry 없는 질의에 실행한 듯한 답변을 생성했다. 둘 다 공간 실행은 하지 않았다. 도구 선택·답변 의미 오류는 남는다. `outputs/initial_plan_development_20261101_v2`.
- 최초 개발 harness의 Executor 초기화 인자 누락으로 한 호출 뒤 중단됐다. 이 호출의 원문 응답은 보존하지 못했으므로 점수에 사용하지 않는다. 실패 기록을 남기고 v2는 모델 원문을 실행 전에 저장하도록 변경했다. 연구 benchmark 실패가 아닌 개발 도구 오류다.
- 읽기전용 실제DB의 개발 기준점에서 독립 ST_Distance Oracle 객체560495/599552/700746을 확보했다. 수작업 정상 계획의 엔진 대조는 실제 공간 SQL로 이 세 feature를 반환했다. 모델이 만든 성공 계획 또는 서로 다른 실재 시설3개의 성공으로 표현하지 않는다.

운영 coverage의 승인된 원천 범위와 연구용 부산 bbox는 별개다. 연구 기준 polygon이나 object extent를 운영 authoritative coverage로 승격하지 않았다. canonical polygon·nearest·복합 완결성, 독립 인간 GOLD와 반복 평가를 전체 완료로 주장하지 않는다.
