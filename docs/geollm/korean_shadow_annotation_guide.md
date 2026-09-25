# 한국어 작업·슬롯 평가 검수 지침

2026-09-26. 모델 출력과 route 이름을 정답으로 사용하지 않는다. 사람이 검수하지 않은 항목은 `UNREVIEWED` 또는 `AI_REVIEW_REQUIRED`로 보존한다.

## 검수 순서와 이유

1. 원문과 실제 제공된 대화·지도 문맥을 먼저 읽는다. 없는 위치, 선택 객체, 날짜 또는 반경을 보충하지 않는다.
2. 사용자가 원하는 산출물별 `required_tasks`를 작성한다. 침선 검색은 위치 해소와 공간 검색을 포함할 수 있다. 사고 원인 분석까지 요청하지 않았다면 사고 분석을 필수 작업으로 추가하지 않는다.
3. 각 작업의 `allowed_capability_sets`에 허용되는 기능 조합을 기록한다. 한 작업을 서로 다른 기능 조합으로 충족할 수 있다. `[[]]`는 금지한다. 등록 기능이 없다면 `[]`와 `candidate_gap`에 이유를 기록한다. 도구 실행과 산출물 완성을 구분한다.
4. 슬롯은 원문 구간과 종류·단위를 함께 검수한다. `12개월`은 기간이며 반경이 아니다. `2.0`은 문맥에 따라 표준 버전일 수 있다. 원문에 존재해도 `target`으로 적합한지는 별도 판단한다. 정박지의 Feature를 묻는 질문에서 S-101만 대상이라고 선택하면 핵심 객체가 빠질 수 있다.
5. 추가 질문이 반드시 필요한지 판단한다. 문맥에 위치가 있으면 위치를 다시 묻는 것을 정답으로 만들지 않는다. 기능 미구현이나 데이터 부족을 사용자가 해결할 수 없는 질문으로 돌리지 않는다.
6. 명시적으로 제외한 대상, 근거 없는 좌표·기간과 과잉 실행을 `forbidden_capabilities` 및 근거 설명에 남긴다. '사고가 없는 구역'은 기간과 coverage까지 필요한 부재 조건이며, 사고 조회 0건만으로 안전을 판정할 수 없다.
7. 가능하면 독립 검수자 2명이 모델 출력을 보기 전에 작성하고 불일치를 조정한다. 검수자 ID, 판단 근거, 원천 참조를 보존한다. 단독 검수와 합의 결과를 구분한다.

## 개발셋과 독립 평가셋

웹 샘플 100개는 이미 수정에 사용한 개발 회귀셋이다. 이름만 바꾸거나 무작위로 나눠 독립 holdout으로 만들지 않는다. 새로운 항만·표현·복합 요구·문맥 사례를 수집하고 동일 대화/템플릿/변형의 lineage가 split을 넘지 않게 나눈다. calibration에서 가중치를 결정한 뒤 locked holdout은 수정 없이 평가한다.

`export_korean_review_pack.py`는 고정 snapshot에서 모델 출력·점수를 제외한 개발 검수 양식을 만든다. 이 양식은 독립 gold 수집을 대신하지 않는다. `reviewer_ids`를 AI 이름이나 자동 생성 문자열로 채워 `HUMAN_VERIFIED`로 승격하지 않는다.

```powershell
docker exec -e PYTHONPATH=/app geollm_backend python scripts/export_korean_review_pack.py --snapshot outputs/korean-intent-shadow/frozen-model-inputs-v1.json --output outputs/korean-intent-shadow/development-review-v1.jsonl
```

## 지표 해석

`evaluate_grounded_shadow.py`는 독립 gold가 없으면 의미 지표를 null로 출력한다. 구조·원문 근거 통과율은 정확도가 아니다. 예를 들어 모델이 '1년간'을 '1 년간'으로 바꾼 경우 원문 구간 계약은 실패하지만 통항 분석 의도까지 오분류했다고 단정하지 않는다.

현재 평가기는 작업의 허용 기능 조합 포함률, raw 슬롯 일치, 추가 질문, 금지 기능 제안률을 계산한다. 검수된 명확한 intent 라벨의 accuracy/macro-F1, 허용 대안 조합을 고려한 tool-plan F1, raw 슬롯 종류·값 F1 및 clarification F1도 지원한다. 모호한 intent는 단일 intent 지표의 분모와 구분한다. 정규화/원문 span 슬롯 F1, 작업 의존관계의 실제 충족, 실제 도구 실행 완료율, bootstrap 신뢰구간과 calibration 학습은 별도 구현·검증 대상이다. 실패 응답을 분모에서 제거하지 않는다. 이 shadow 실험은 도구를 실행하지 않으므로 실행 완료율을 모델 제안으로 대체하지 않는다.

근거 선정은 [해양 정답 기준](maritime_evaluation_reference_standard.md)을 따른다. 검수 양식의 `reference_bindings`에는 출처 ID·판·locator·hash·최소 주장·적용 조건을 기입한다. 공식 위키는 해당 분야 사전 근거로, 일반 위키는 별칭·질문 다양화·원문 탐색에 활용한다. CLI의 `--gold` 평가는 `--reference-index <units.jsonl>`을 필수로 요구하며 색인 hash, 원문 인용, 판, 검수 상태를 검사한다. 이는 출처의 진위나 의미적 적합성에 대한 전문가 검수를 대신하지 않는다. 자동 검색된 `reference_candidates`는 승인된 gold가 아니며, 혼합 평가는 현재 후보 순위만 비교하므로 혼합 슬롯·실행 계획 점수는 null로 남긴다.

QLoRA는 독립 검수 데이터·holdout, 반복 오류, 자원·라이선스·배포·rollback 조건이 모두 충족될 때만 별도 실험한다. 현재 결정은 DEFER다.
