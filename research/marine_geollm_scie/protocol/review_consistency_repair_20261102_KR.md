# 초기 LLM 판정·수정 계획 불일치 보완

2026-11-02. 연구 전용 변경이며 운영 coverage 변경과 별도로 검증한다. 과거 v6 원본/GOLD/홀드아웃을 바꾸거나 새 모델 호출을 실행하지 않았다.

## 변경과 경계

`structured_review_v3_initial_plan_consistency`는 초기 진단과 수정 계획을 구분한다. invalid=false라면 answer를 제외한 계획 필드를 그대로 반환하도록 프롬프트를 명시한다. 반환 결과는 원래 계획과 비교해 JSON Pointer별 변경 경로와 두 계획/계약 hash를 기록한다. tool arguments뿐 아니라 top-level target, CRS, distance, evidence binding, missing inputs도 비교한다.

모델은 여전히 한 번 호출하며 768토큰·180초·동일 schema·temperature·seed 조건을 유지한다. 단 prompt/code/protocol이 변경되므로 기존 v6와 동일 조건으로 간주하지 않고 새 소스 동결과 전체 실행이 필요하다.

실행 계약은 새 `eight_execution_contract_v5.json`에서 review v3를 참조한다. `prepare_eight_profiles`는 v5와 v3의 실제 bytes가 새 freeze에 모두 포함되고 v3의 version/schema/hash/budget이 실행 코드와 같은지 확인한다. 생성하는 P1·baseline profile에 review protocol path/hash/version을 함께 기록한다. 기존 v4 계약은 해시 `51eae565022dfc1475db1f798c3f994786a56c65e878b402951d4ef7807460a2`를 유지한다. 이렇게 새 run의 설명 계약만 v2에 남는 lineage 불일치를 차단한다.

`invalid=false`이면서 계약 필드가 바뀌면 `REVIEW_UNDECLARED_PLAN_CHANGE`로 반환 검토를 사용 불가 처리한다. B4/H는 같은 실패 receipt를 공유하며 해당 수정 계획을 실행하지 않는다. 원시 응답과 `raw_initial_invalid=false`, `raw_initial_checks`, 변화 경로를 보존한다. 이 상태를 `invalid=true` 또는 LLM 오류 검출 성공으로 변경하지 않는다.

answer 표현 변경과 JSON 숫자 1000/1000.0 차이만 허용한다. 단위/CRS/별칭/문자열 숫자/배열 순서를 의미상 같다고 추정하거나 자동 보완하지 않는다. 검사는 구조적 일관성 검사이며 계획의 의미 정확성 또는 실제 실행 허가를 판단하지 않는다. invalid=true인데 initial_checks가 전부 pass인 반대 방향 판정까지 검출하는 전체 논리 검증기는 아니다.

## 기존 v6 읽기 전용 재현

`outputs/review_consistency_audit_20261102/v6_readonly_replay.json`은 기존 9개 raw review와 initial plan의 SHA를 보존한 계약 재현이다. 새 실험이나 기존 결과 재채점이 아니다.

- 원시 초기 verdict: 정상 대조 포함 9/9 false.
- 무보고 변경 3건: WRONG_CRS, NEGATIVE_RADIUS, WRONG_RADIUS.
- 정상 대조와 나머지 5개 오류: 계획 변화 없음. 따라서 새 구조 검사는 이 다섯 오류를 발견하지 못하며 LLM의 기존 미검출을 해결했다고 주장하지 않는다.
- 다음 새 실험에서는 원시 모델 오류 탐지, review usable/contract failure, 복구 여부를 따로 보고한다. 사용 불가 응답을 분모에서 제외하지 않는다.

## 다음 접속 시 전체 비교

1. 부모 운영 coverage 회귀와 실제 API 검증 완료, 임베딩 worker·소스 변경 종료를 확인한다.
2. 신규 `review_consistency.py`, `structured_review_v3.json`, 변경 runner가 execution freeze에 포함되는지 확인한다.
3. 새 output/snapshot 경로에서 supervisor로 8방법144와 통제27을 전부 실행한다. 기존 raw 재사용, GOLD 또는 예산 조정 없이 실패도 보존한다.
4. B4/H 공유 review SHA, P0 lossless, raw/usable 판정 분리, 실행 callback 미호출, 전체 분모·missing·completion gate를 검증한다.
5. 실제 모델이 개선된 초기 판정을 내리는지는 이 새 실행 후에만 판단한다. 현재 보완 완료 범위는 모순된 계획이 사용되는 코드 경로와 관측 누락 방지다.
