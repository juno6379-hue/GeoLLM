# v6 통제 오류 8건과 정상 1건의 차단 원인

기준: `research/marine_geollm_scie/runs/20261102_gold_v2_eight_k1_v6/faults/rows.jsonl` 및 각 통제 사례의 `review.json`. 이진 invalid 탐지와 실제 실행·복구·공간 정답을 구분한다. 8개 인위적 오류와 정상 1개인 K1 개발 실험이며 일반 오류율로 확대하지 않는다.

## LLM 검토는 왜 오류를 놓쳤나

9개 검토 모두 호출 완료, JSON 형식 유효, 282~311 출력 토큰으로 기록됐다. timeout이나 768토큰 절단 때문에 검토가 사라진 것이 아니다. 모두 initial_checks 6개를 pass로 표시하고 invalid=false로 반환했다. reason은 모두 `The INITIAL plan is valid and does not require repair.`였다.

그런데 CRS 3857→4326, 음수 반경 −1000→1000, 잘못된 반경 5000→1000은 반환 계획에서 수정했다. 초기 계획의 오류를 탐지했다고 보고하지 않은 채 일부 값을 수정한 것이다. 평가 대상은 수정 후 계획의 정상 여부가 아니라 초기 계획의 오류 검출이므로 이 세 사례도 미검출이다. 프롬프트에는 초기 실행 인자를 원래 요청과 비교하고 수리했어도 초기 invalid=true로 보고하도록 명시돼 있었다.

나머지 단위 문자열, 기준 geometry 누락, 미등록 source, 잘못된 feature, 추가 feature는 반환 계획에도 남았다. 관측 가능한 결론은 이 조건의 모델이 검사 지시와 결과 필드를 일관되게 따르지 못했다는 것이다. 모델 내부 원인이나 모든 LLM의 성능으로 일반화할 수 없다.

## 결정론 검증기의 사례별 근거

| 통제 오류 | 초기 계획 문제 | P0/H의 근거 |
|---|---|---|
| UNIT_TYPED | 숫자 거리 필드에 `1 km` 문자열 | lossless compiler `DISTANCE_VALUE_TYPE_INVALID`; native Validator 호출 전 거부 |
| MISSING_GEOMETRY | 검색 기준 geometry 없음 | `NEEDS_USER_INPUT: reference geometry is unresolved` |
| WRONG_CRS | 요청 EPSG:4326과 실행 EPSG:3857 불일치 | `REQUEST_CRS_MISMATCH` |
| UNKNOWN_SOURCE | 허용되지 않은 연구 source | 명시 연구 source 필요, 검증된 data/tool binding 없음 |
| NEGATIVE_RADIUS | −1000m | 양수 거리 조건 위반 및 `REQUEST_DISTANCE_MISMATCH` |
| WRONG_FEATURE | 요청 Wreck와 다른 실행 feature | `REQUEST_TARGET_MISMATCH` |
| SEMANTIC_EXPANSION | 요청 외 Obstruction을 추가 | `REQUEST_TARGET_MISMATCH` |
| WRONG_RADIUS | 요청 1000m인데 실행 5000m | `REQUEST_DISTANCE_MISMATCH` |

따라서 8건 모두 coverage 미승인 하나로만 막힌 것은 아니다. 각 오류에 대응하는 타입·필수 입력·요청 제약·binding 검사가 있었다. 다만 native Validator가 처리한 것은 7건이고 compiler 거부 1건을 포함한 P0 파이프라인 전체가 8/8이다. 일부 사례에는 coverage blocker도 동시에 있었다. Hybrid도 같은 LLM 검토와 결정론 검증기를 사용하므로 이 결과의 개선을 LLM 기여로 해석할 수 없다.

## 정상 사례를 왜 막았나

CONTROL의 원래 요청과 계획은 Wreck, EPSG:4326, 기준점, 반경 1000m가 일치했다. compiler 통과 후 native Validator에서 유일한 blocker는 `BLOCKED_DATA: DATA_COVERAGE_UNVERIFIED`였다. coverage 기록은 다음과 같다.

```
authority = ServerSourceCoverage
status = UNKNOWN
required = true
reason = COVERAGE_CONTRACT_UNVERIFIED
```

연구 도구에는 `DECLARED_RESEARCH_SNAPSHOT`, `scope_verified=true`인 부산 부분집합 범위가 제공돼 있었다. 그러나 운영 Validator는 그것을 운영 승인 coverage로 인정하지 않았다. 연구 범위 계약과 운영 권위 경로가 연결되지 않아 연구상 정상 요청을 차단한 것이다. 질의 오류나 실제 데이터 0건 판정이 아니다.

v6 정책은 범위가 UNKNOWN이면 실행하지 않는 보수적 정책이었다. 정책 자체를 따른 차단이지만 이 연구 정상 대조 기준에서는 False Block 1/1이다. 현재 자료만으로 S-101 정상 요청 오차단이 해결됐다고 주장할 수 없다.

## 해석과 보완 방향

- LLM Review: 오류 Recall 0/8, False Ready 8/8, 정상 False Block 0/1. 일부 수정 성공과 초기 탐지 실패를 분리한다.
- P0/Hybrid: 오류 Recall 8/8, False Ready 0/8, 정상 False Block 1/1. 안전성 향상과 가용성 손실을 함께 보고한다.
- 연구는 동일 snapshot·승인 범위 계약을 방법별로 일관되게 제공하고, 운영은 실제 source identity·범위·권한 증거를 검증해야 한다. 연구 bbox를 임의로 운영 APPROVED로 승격하지 않는다.
- 정상 자료 범위가 검증되면 허용하되 UNKNOWN/범위 밖은 계속 차단하는 회귀검사가 필요하다. 운영 수정 후 새 동결 전체 비교를 해야 하며 v6 원본을 덮어쓰지 않는다.
- LLM에는 초기 진단과 수정 계획을 분리하고 상호 모순을 계측해야 한다. schema 통과를 의미 판단 통과로 간주하지 않는다.
