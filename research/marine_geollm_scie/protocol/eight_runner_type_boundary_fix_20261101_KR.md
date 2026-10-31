# 8방법 실행기 v1 중단 원인과 새 동결 조건

v1 `20261101_gold_v2_eight_k1_v1`은 baseline10행까지 저장한 뒤 Q1-02 B3의 최종 답변 투영에서 중단됐다. 모델이 `arguments.source`에 문자열 대신 `["s101", "marine_places", "navigation_aids"]`를 반환했고, projector가 이 값을 dict key로 조회하여 `TypeError: unhashable type: 'list'`가 발생했다. 이것은 모델의 잘못된 인자와 이를 격리하지 못한 연구 harness 결함이 함께 발생한 사례다. 기존 run·raw·동결 source는 보존한다.

원본 B3 SHA256 `370c779a821f41e3161f3b518524cbc5addf9a15f293abafeb83bbad44b867e7`을 기록한 회귀 fixture로 이전 source의 동일 예외를 재현했다. 모델 재호출 없이 재현 결과를 `outputs/eight_projection_fix_20261101_v1/reproduction.json`에 저장했다.

수정은 연구 코드에 한정한다.

- source/operator/geometry_ref/feature_types의 잘못된 타입을 인자 오류로 거절한다. 리스트의 첫 source 선택, 객체 문자열화, Feature 교정은 하지 않는다.
- 답변 projector는 잘못된 타입을 `projection_errors`에 기록하고 PARTIAL로 남긴다. 가짜 object set이나 coverage를 만들지 않는다. 이전 모델 plan·실행 receipt는 그대로 보존한다.
- 예상하지 못한 projector 예외는 해당 행의 `ANSWER_PROJECTION_ERROR`, `emitted_answer=null`로 기록하여 후속 관측을 잃지 않는다. 실패를 성공으로 승격하지 않는다.
- Python JSON parser가 허용하는 NaN/Infinity/overflow 수치를 계획 동결 전에 거절한다. raw 문자열은 그대로 남기며 clamp/coercion은 하지 않는다.
- 새 실행기의 공통 출력 schema에 실제 도구 설명이 광고한 `covers`를 명시적으로 추가했다. 기존 `PLAN_SCHEMA`는 변경하지 않고 V2 복사본을 사용한다. `within`을 `covers`로 치환하지 않는다. 모든 새 baseline 생성·검토는 동일 V2 schema를 사용한다.

GOLD v2, 데이터 snapshot 내용, 모델, token/context/timeout 예산은 이 수정으로 바꾸지 않는다. 실행 소스·schema가 달라졌으므로 v1의 결과를 이어 붙이지 않고 새로운 run에서 전체8방법을 다시 실행해야 한다. Q1-01 B2의 768-token length 종료/JSON 절단은 별도 관측 실패이며 예산을 올려 은폐하지 않는다.

관련 테스트49개 통과. 이 검증은 harness 타입 경계·분기 보존의 검증이며 모델 성능이나 운영 시스템 정확도 결과가 아니다.
