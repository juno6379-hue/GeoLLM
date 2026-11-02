# 공간 검색 전 데이터 범위 검증 — 운영 수정

v5의 독도 침선 질의는 `UNKNOWN/required=false` 상태에서 공간 SQL을 실행했다. 일반 반경 검색에서 범위 검증을 선택사항으로 취급한 것이 원인이다. 이번 수정은 운영 실행 정책이며 논문 정답이나 연구 bbox를 운영 승인 원천으로 사용하지 않는다.

## 바뀐 동작

- `SPATIAL_OPERATIONS`는 서버 정책으로 coverage 검사를 필수 적용한다. 요청의 `require_complete_coverage=false`로 해제할 수 없다.
- 범위 밖/부분 포함은 `DATA_OUT_OF_SCOPE`, 범위 선언 미검증은 `DATA_COVERAGE_UNVERIFIED`로 차단한다. 입력 geometry·반경이 부족하거나 무효이면 기존 추가 입력 요청을 유지한다.
- S-101 반경/지도영역 경로는 공간 도구 dispatch 전에 ExecutionValidator를 호출하고 executor transaction 내부에서도 재검증한다.
- preflight 거절에만 대상 공간 작업의 attempted/started/tool_called/sql_executed=false를 기록한다. schema inspection SQL까지 실행되지 않았다는 뜻은 아니다. 일반 예외의 실행 여부는 추정하지 않는다.
- 지도영역 QEC는 중심점 대신 전체 polygon을 전달한다. 원천 범위가 viewport 전체를 포함하는지 검사한다.
- 답변에는 미실행 이유를 한글로 전달하며, 미실행을 검색 결과 0건으로 설명하지 않는다.

## 검증과 원본

수정 담당 회귀 219 passed, 추가 요청 제약·revision 35 passed. 부모의 권한/stream/요청 제약/revision 통합 85 passed. 최종 한글 사유 전달 후 관련 71 passed. 중복 테스트를 합산하지 않는다. 승인 정상 경로는 실제 임시 coverage 파일/hash/snapshot을 사용한 격리 fixture이며 운영 범위 승인 증거가 아니다.

독립 감사는 [감사 기록](coverage_preflight_audit_20261102.md)에 있다. 중간 수정의 CRS/잘못된 좌표 우회를 발견하고 수정했다. 범위 오류를 추가하면서 무효 반경의 NEEDS_USER_INPUT이 BLOCKED_DATA로 바뀌던 문제도 실제 회귀에서 발견해 바로잡았다. 실패를 처음부터 없었던 것으로 처리하지 않는다.

실제 API 첫 검증 원본: `outputs/coverage_preflight_runtime_20261102_v1`. 6개 완료 이벤트에서 반경 3건은 호출 전 차단·네 실행 필드 false·count=null, 영역 누락은 추가 입력, S-101 정의는 완료, 주변 지명은 범위 미검증 차단을 관측했다. 이후 지명 차단 메시지를 보완했으므로 최종 검증은 별도 v3 원본을 따른다. v2는 재시작 준비 전 연결종료 3건이며 성공으로 합산하지 않는다.

재현: `.venv/Scripts/python.exe -m scripts.check_coverage_preflight_runtime --output outputs/<새 경로>`. 이 스크립트는 관측 수집이며 자동으로 의미 정답을 판정하지 않는다.

최종 v3 실제 API 6건을 부모가 원시 SSE와 대조했다. 반경 3건의 preflight 네 false·count=null, 영역 누락 NEEDS_USER_INPUT, 정의 COMPLETED, 주변지명 DATA_COVERAGE_UNVERIFIED/NOT_RUN 및 한글 설명을 확인했다. 수집 전후와 검증 시점의 운영 3파일 hash가 일치한다. `outputs/coverage_preflight_runtime_20261102_v3/verification.json`. 6개 기대 계약 확인은 의미 정확도 100%가 아니며 주변지명 가용성 저하를 포함한다.

## 남은 제한과 연구 분리

운영에 승인된 coverage 선언이 없어 부산 S-101과 주변 해양지명 검색도 UNKNOWN으로 차단된다. 안전 차단 구현과 데이터 범위 구축 완료는 다르다. 단순 객체 bbox 또는 연구 snapshot의 범위를 운영 완전성으로 승격하지 않는다. 향후 원천 판·실제 DB snapshot·geometry·Feature 범위를 검수하고 등록해야 공간 검색 가용성을 복구할 수 있다.

Q5-03의 공간 부분을 막았지만 문서 설명만 별도로 제공하는 부분 응답은 이번에 구현하지 않았다. nearest/canonical polygon/복합 완결성, 사고·통항·별도 overlay 전체의 범위 감사도 미완료다.

논문은 동일 GOLD v2, 모델·예산·평가계약을 유지한 새 v6 전체 144+27 관측으로 비교한다. UNKNOWN 차단으로 정상 통제나 Q4 지명 질문이 차단되는 비용을 숨기지 않는다. 연구 범위 입력과 운영 승인 권위의 차이를 보고하며, 기존 v5 원본을 재채점·덮어쓰기하지 않는다.

Docker 기동 오류는 오래된 runtime socket 접근 실패였다. 런타임 폴더를 `C:\Users\최준오\AppData\Local\Docker\run_preserved_20261102_coverage`로 보존한 후 재기동했다. DB volume 삭제/초기화 명령은 수행하지 않았다. 연구 DB 준비 상태와 운영 health 200을 확인한 뒤 API 검증을 시작했다.
