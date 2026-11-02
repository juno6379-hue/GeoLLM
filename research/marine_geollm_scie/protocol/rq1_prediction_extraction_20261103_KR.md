# RQ1 원문 예측 원자 추출 계약 — 구현된 검토 초안

상태: **IMPLEMENTED_EXTRACTION_CONTRACT_REVIEW_DRAFT**. AI 측정용 주석이다. 사람 검수 완료, 36개 완전 예측 주석, Semantic F1 측정 또는 새 benchmark 동결을 뜻하지 않는다. 기존 GOLD 값·v6 원본·홀드아웃은 수정하지 않는다.

## 입력과 동일 조건

개발 18문항의 B1/B2 원문 36개를 모두 포함한다. 원본 상태 completed 25개, INVALID_RESPONSE 11개이고 후자에 JSON 절단 1개가 포함된다. 실패를 제외하거나 잘린 JSON을 복원하지 않는다. JSON이 유효하지만 평가 schema가 잘못된 응답도 실제 명시 필드·본문을 추출 대상으로 유지한다. 전체 응답을 검토하지 않은 실패를 빈 원자 목록 또는 0점으로 바꾸지 않는다.

기존 `grounding_atoms_v1.py`는 변경하지 않는다. 새 준비/검증기는 `evaluation/prediction_contract_v1.py`이며, GOLD 값이나 GOLD 파일을 입력받지 않는다. 예측 값의 유일한 출처는 모델 원문이다. 사용자 질의는 과업 명칭/범위 식별에만 사용할 수 있고 누락된 답안 값을 보충하는 출처가 아니다. 각 원문 SHA, query SHA, contract SHA, JSON pointer와 실제 문자열의 `[start,end)` span을 기록한다. 단위는 Python Unicode 문자열 인덱스다.

## 채널·정규화·FP

1. 구조화 필드와 실제 답변 본문의 합집합을 검토한다. 어느 채널도 무조건 우선하지 않는다. 상충하는 값은 양쪽을 남긴다. 예를 들어 `target_features=[height]`를 올바른 attribute로 고쳐 주지 않는다. feature 종류의 잘못된 추가 주장 후보로 보존한다.
2. feature는 원천 FC code의 대소문자·단어 사이 공백만 정규화한다. 유일한 code에 정확히 일치할 때만 적용하고 원천 파일 SHA를 고정한다. unknown code, `naval wreckage`, `anchor_line` 등을 정답 feature로 번역·교정하지 않는다. 등대와 등화/구조물의 의미적 동일성도 추정하지 않는다.
3. 명시 km/m와 kilometer/metre 표현만 Decimal로 환산한다. 정확한 정수 미터만 허용하고 반올림이나 기본 반경은 없다. 명시 EPSG:4326/4326 표기만 통일한다. 좌표로 CRS를 추론하거나 실제 좌표를 찾아 채우지 않는다.
4. 구조화 `within`, `covers`, `dwithin`은 서로 바꾸지 않는다. 본문의 `within 5km`는 단어 `within`만으로 위상 연산이라고 단정하지 않고 전체 문장/거리 witness의 관계 검토를 요구한다. 관계의 인수 방향과 거리 방식은 보존한다.
5. 같은 단어가 구조화 필드와 본문에서 반복됐다는 이유만으로 FP를 제거하지 않는다. **동일 task·동일 종류·동일 값의 동일 주장임을 명시적으로 검토한 witness만** 하나의 원자로 묶는다. 별개 주장·복합 작업·상충 표현은 별도 원자로 남는다. 기존 scorer는 전달된 별개 중복 원자를 계속 FP로 계산한다.
6. 출처명·경로·hash를 언급한 것과 특정 주장/객체/속성이 해당 출처와 연결됐다는 것은 다르다. source mention만으로 `source_binding`을 만들어 주지 않는다. 잘못된 출처/hash도 원문 주장으로 보존하며 정답 출처로 치환하지 않는다.
7. literal 정의문, 실제 객체명/좌표/속성값 주장은 별도 claim sidecar에 보존한다. RQ1 GOLD의 평가 범위 밖이라는 명시적 판정 없이 삭제하지 않는다. 해당 주장의 실제 사실 정확도는 RQ1 grounding F1과 별도 평가다.

## 과업과 복합 요청

단일 과업은 `query`를 쓸 수 있지만 원문 과업 연결을 먼저 확인한다. 복합 요청은 공간 대상별 task와 설명/비교 task를 분리한다. 부모 질문의 거리·reference를 모든 자식 task에 복제하지 않는다. 원문에 공동 적용이 명시된 문장 또는 구조화 부모-자식 적용 범위를 witness로 제시해야 한다.

잘못된 대상의 과업을 정답 task에 억지로 맞추지 않는다. 모델이 `anchor_line`을 조회했다면 해당 잘못된 대상/과업 주장을 남겨 FP가 사라지지 않게 한다. 요청된 두 공간 작업 중 하나만 있으면 다른 작업을 GOLD에서 보충하지 않는다. 속성의 owner가 없으면 owner를 FC나 GOLD에서 추론하지 않는다.

## 완료 gate

현재 생성물은 `canonical candidate`이며 `prediction_atoms=null`이다. scorer에 넘기려면 다음을 모두 충족해야 한다.

- 36개 코호트와 원문 hash를 유지한다. 실패/절단도 남긴다.
- 모든 구조화 필드·본문 witness 및 전체 원문 추가 주장에 대해 검토한다. sparse 사전주석 목록만 검토한 것으로 전체 답안 검토를 대체하지 않는다.
- 각 witness에 ATOM, 동일 주장 DUPLICATE_WITNESS, OUTSIDE_RQ1_SCOPE, NOT_ASSERTED, NON_SEMANTIC_FIELD 중 하나와 구체적 이유를 기록한다.
- 각 예측 원자는 실제 witness, 종류·값의 허용 정규화, 명시 task binding을 가져야 한다. 현재 구현이 정규화할 수 없는 source binding·attribute owner·task obligation은 임의 수작업 값으로 gate를 우회하지 않는다. 해당 추출 규칙·witness schema를 별도 검증하고 계약 버전을 올린다.
- canonical 후보와 다른 값을 주입하면 검증기가 거부한다. 잘못된 span, pointer, raw hash, 중복 prediction ID, 미처리 witness도 거부한다.
- `full_response_review`는 AI 검토 책임 기록이며 독립 인간 검수 증명이 아니다. 원자 주석의 인간 승인과 기존 GOLD 승인은 별도로 기록한다.

완료 gate 통과 후에만 기존 atom scorer로 F1/Strict Match를 계산한다. B1/B2 짝과 B2−B1 차이 방향·query/GOLD/contract hash·동등군을 고정하고 paired cluster bootstrap을 적용한다. UNSEEN N=0, 적은 cluster, 과거 v6의 사후 개발 분석 한계를 함께 표시한다. 새 운영 코드 효과를 과거 답안 재채점으로 주장하지 않는다.

## 이번 검증 결과와 남은 항목

`outputs/rq1_prediction_contract_20261103_v1`에 36개 원문 대조 결과, 301개 witness, 보수적 canonical 후보 166개, 나머지 135개 개별 처리 검토 대장을 저장했다. 이 135는 오류 건수나 FP 수가 아니며 범위 밖 주장/행동 라벨/관계·출처 해석 등 아직 확정되지 않은 주석 단위의 수다. 166개도 전체 추출 완료가 아니고 과업·상충·중복·추가 FP 검토가 남았다.

전용 테스트 14개 통과. 실제 모델/API/DB 호출은 없었다. 다음은 원문 전체 추가 주장 검토와 36개 개별 task·owner·source·상충/중복 주석을 확정한 뒤 새 추출계약을 동결하는 것이다. 그 이전 RQ1 F1·Strict Match·CI는 null로 유지한다.
