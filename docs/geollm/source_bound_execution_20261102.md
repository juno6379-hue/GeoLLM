# 원천 조회 실행성과 실세계 완전성 분리

2026-11-02 KST. 운영 coverage 보완과 실제 LLM 개발 검증을 별도 에이전트에 배정하고 독립 감사를 수행했다. 과거 v5/v6 논문 결과를 수정하지 않는다.

## 세 가지 판단 축

| 축 | 확인하는 내용 | 확인하지 못하는 내용 |
|---|---|---|
| Source corpus identity | 원천/목록 파일 bytes, snapshot, 현재 DB의 대상 전체 membership·속성·geometry 일치 | 모든 객체의 실세계 정확성 |
| Dataset geographic coverage | 원천에 선언된 DataCoverage와 요청 영역의 관계 | 실세계 모든 객체가 수록됐다는 보장 |
| Real-world completeness | 별도 독립 근거가 있어야 하는 실제 세계 전체성 | 파일 존재나 검색 성공에서 추론할 수 없음 |

ExecutionValidator가 나머지 입력·도구·권한·원천 검사를 모두 통과한 경우에만 `execution_scope_validation.status=SOURCE_BOUND_EXECUTABLE`을 기록한다. `source_corpus_status`, `geographic_coverage_status`, `real_world_completeness`는 별도 필드다. 이 추가 기록이 기존 `EXECUTION_READY` 권한 검사를 대신하지 않는다. 실세계 완전성은 UNKNOWN이고 부재 보증은 false다.

원천이 검증됐어도 범위 밖이면 `source_corpus_status=VERIFIED`를 유지하고 별도로 공간 범위 밖/부분 겹침을 기록해 차단한다. 원천 검증에 성공했다는 이유로 잘못된 반경·CRS·geometry를 허용하지 않는다. 이전 결정/클라이언트가 전달한 source-bound 표시는 새 권한을 만들지 못한다.

명시적으로 원천 목록에 수록된 **모든** 객체를 요청하는 것은 실세계의 **모든** 객체 요구와 다르다. 원천 한정이 해당 전수 조회 절·대상에 직접 적용되는 경우만 finite inventory 조회로 처리한다. 다른 절에서 CSV를 설명하라는 요청이 있다고 별도 공간 과업을 원천 조회로 축소하지 않는다. 모호한 요청이나 실세계/최근접 요구는 이 예외로 허용하지 않는다.

## 실제 운영 원천

Q4는 해양지명 2022 CSV 전체 1,146행과 현재 DB를 대조한다. 실세계 전체 지명의 완전한 목록으로 취급하지 않는다. S-101은 부산 원본 cell 1개의 DataCoverage를 binary topology에서 복원해 현재 DB와 비교하고, 등록 대상 Wreck 전체 4,339행 snapshot을 현재 DB와 대조한다. 전국 coverage나 각 Wreck 원문 geometry 전수 검증을 뜻하지 않는다. 상세 근거는 [부산 원천 등록](s101_busan_source_inventory_20261102.md)에 있다.

초기 실제 Q4 검증에서 한글 5km·영문 5km·한글 5000m 세 표현은 각각 11건을 반환했다. 실세계 전체 지명을 빠짐없이 찾으라는 요청은 차단했다. 이 세 표현은 같은 공간 과업의 변형이며 세 개 독립 공간 문제로 집계하지 않는다.

초기 S-101 API v2에서 부산 기준점 1km 요청은 원천 내 0건으로 완료됐다. 답변은 원천 목록 한정과 실제 침선 부재 미보증을 명시했다. 범위 밖/전체성 요청은 count=null로 차단, 영역 미지정은 추가 입력을 요청했다. 첫 v1은 backend 재기동 준비 중 RemoteDisconnected 4건이며 원본을 보존했다.

최종 API 검증은 코드 hash를 고정한 `outputs/coverage_review_live_20261102_s101_v4/`에 별도로 저장했다. 7건 모두 최종 응답을 받았고 실행 중 코드 hash는 동일했다. 정상 0건·4건, Q4 및 명시 CSV 전체검색 각각 11건으로 완료했다. 범위 밖/실세계 전체성 요구는 BLOCKED, 영역 누락은 NEEDS_CLARIFICATION이며 세 경우 네 실행 flags=false, 결과 건수=null이다. 후보 planning_status=ready와 최종 실행 허가를 분리했다. 이전 v3의 finite-all 오차단 원본도 보존했다. 정상·비어 있지 않은 결과·범위 밖·누락 영역·Q4·명시 finite-all을 확인한다. 공간 SELECT의 SQL 응답 수신 후에만 execution_started/sql_executed를 true로 기록하며, metadata 조회는 공간 실행으로 세지 않는다. 연결 오류에서는 서버 실행 여부를 unknown으로 남긴다.

## 실제 LLM 검증

새 개발 입력 4건과 고정 Qwen2.5 1.5B digest/seed/기존 예산으로 호출했다. 정상 1건은 초기 false·수정 없음으로 사용 가능했다. CRS·반경 오류는 초기 false인데 계획을 수정해 새 모순 guard가 사용을 차단했다. geometry 누락은 여전히 초기 false로 미검출됐다.

따라서 초기 오류 Recall은 **0/3**이고 모순 수정안 차단은 **2/4**다. timeout/출력 절단이 아니라 completed/stop 응답이었다. 모순 거부를 LLM 검출 true로 바꾸지 않았다. 이 결과는 개발 probe이며 논문 8방법 결과나 인간 의미 정확도가 아니다. 원문은 `outputs/review_live_development_20261102_v1/`, 독립 재계산은 `outputs/coverage_review_live_20261102_independent/`에 보존한다.

## 연구 재실행 경계

v6 False Block과 P1 0/5는 당시 조건의 결과로 보존한다. 현재 운영 Q4 복구를 과거 결과에 소급 적용하지 않는다. 신규 freeze에는 registry YAML뿐 아니라 inventory JSON, 원본 cell, source-verification pointer/manifest/receipt까지 bytes hash로 포함한다. 누락·변조·경로 이탈을 거부한다.

운영 DB와 연구 부산 subset은 서로 다르다. 연구 `ResearchBindingAdapter`의 선언된 snapshot 범위와 실제 연구 DB identity를 별도 검증하는 접점이 아직 필요하다. 운영 원천 계약을 연구 APPROVED로 복사하지 않는다. 이 연결과 진행 중 Dataset revision 정리를 마친 후 새 동결 8방법 전체 비교를 수행한다. 이번 작업에서는 전체 비교·홀드아웃을 실행하지 않았다.

## 최종 회귀 검증

운영 관련 최종 194 tests, 전체 연구 457 tests 통과. 독립/부분 검사는 중복합산하지 않는다. 실제 API 검증은 SSE 관측이며 브라우저 조작 검증이나 독립 인간 정확도 측정은 아니다.
