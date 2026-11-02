# RQ1 전체 예측 원자 측정 계약 v2

이 계약은 개발 18문항 B1/B2 원문 36개를 **AI 측정용 주석**으로 검토·컴파일하고 동일 규칙으로 새 실행의 원문을 평가하기 위한 것이다. 독립 인간 의미 정확도나 새로운 인간 GOLD 승인으로 표시하지 않는다. 이전 166개 후보/36개 null 초안은 보존하며, 그 부분 추출 결과를 점수로 사용하지 않는다.

## 측정대상과 과업 의미

예측 값은 오직 실제 모델 출력의 구조화 필드와 본문에서 나온다. GOLD는 예측 주석 컴파일이 모두 완료된 뒤 점수 계산 단계에서만 입력한다. 모델에게 제공됐던 prompt/query/검색 context는 예측 witness로 사용할 수 없고 코드에서 거부한다. 질의와 공개 과업명은 task ID를 정렬하는 역할만 하며 거리·owner·feature·출처를 채우는 근거가 아니다.

`task_obligation`은 **명시적인 의미 과업 인식/계획**이다. 실제 실행 성공, 정의 내용의 사실정확도, 답안 완결도를 뜻하지 않는다. 예컨대 `action=explain`, `intent=Wreck`와 Wreck 설명을 쓰는 답변은 설명 과업을 인식한 것으로 주석할 수 있지만, 동어반복이나 잘못된 정의가 정답이라는 뜻은 아니다. 반면 구조물/등화를 구분하지 않은 일반 등대 설명에는 구분 과업을 채우지 않는다. 조건부 실행, 공동 대상, 원천 고정 등 과업 식별자에 포함된 의미도 실제 출력에서 확인해야 한다.

| 개발 과업 | 추출할 의미와 부여 조건 | 보충하면 안 되는 값 |
|---|---|---|
| Q1_01 | 구조물/등화의 구분과 조건별 FC mapping을 실제로 표현할 때 각각의 과업 원자. 명시된 FC 유형은 개별 feature | Lighthouse라는 넓은 명칭을 Landmark/Building/등화 4종으로 자동 확장 |
| Q1_02 | AnchorageArea 설명 계획/본문을 명시하면 설명 과업; 실제 예측 객체 유형을 별도 기록 | Wreck 오답을 AnchorageArea로 교정 |
| Q1_03 | Wreck 설명 계획/본문의 과업과 Wreck 유형을 분리 | 부실 정의를 사실정확성 성공으로 해석 |
| Q2_01 | 구조물/등화 colour 구분, owner별 허용값 설명. 속성은 명시 owner→attribute만 기록 | 일반 ‘등대’ owner를 4종 FC owner로 전개, 실제 색상 주장을 허용 enum 정답으로 대체 |
| Q2_02 | restriction과 area category 구분 및 코드 설명을 실제로 식별했는지 기록 | ‘restricted type’만으로 RestrictedArea owner/정확한 속성코드를 추론 |
| Q2_03 | Wreck 속성 설명 과업, 명시 Wreck→attribute. feature 필드에 넣은 속성 이름은 잘못된 feature 주장으로 별도 유지 | attributes 목록을 FC에서 완성, feature 필드 오류를 조용히 고치기 |
| Q3_01 | nearest, Lighthouse 대상, 기준 위치. 구조물/등화 조건 분해는 실제 명시 때만 추가 | 가장 가까운 실존 등대 ID·거리 및 범위 권위 |
| Q3_02 | 항계 polygon 해석, polygon 검색, covers, 명시 기준 geometry ID/CRS | 단순 1km dwithin을 항계 covers로 변경, 부산항 이름으로 polygon ID 찾기 |
| Q3_03 | Wreck/intersects. AOI 필수 요구와 AOI가 있을 때만 실행한다는 조건은 실제 명시 때만 부여 | selected area 언급을 입력 확인/실행 차단으로 자동 승인 |
| Q4_01 | 아래 Q4 공통규칙. 답변이 객체 목록만 있으면 조건 원자 공집합도 관측된 유효 주석 | 반환 객체명으로 기준점·반경 역추론 |
| Q4_02 | MarinePlaceName, 명시 기준·거리·dwithin. 고정 원천 과업/기준 ID/거리 방식은 실제 표현 때만 | 질의의 기본 반경, 2022 CSV, 동도 ID, WGS84를 답안에 주입 |
| Q4_03 | Q4_02와 동일한 영어/한국어 규칙 | 영어 표현이라는 이유로 추가 정보 승인 |
| Q5_01 | 실제 예측 대상별 공간 task. 공동 조건을 명시한 문장과 root 계획 값만 해당 대상 묶음에 적용. 각 출처는 별도 | anchor_line/naval wreckage를 일반 Wreck로 확대; 누락한 두 번째 작업 생성 |
| Q5_02 | 실제 대상별 공간 task와 별도 comparison task. 양 대상2km 과업·개수/거리/정의/원천 비교 기준은 실제 명시 때만 | 단순 두 대상 나열을 비교 완료로 판정, polygon 면/경계선/centroid 거리 혼합 |
| Q5_03 | 공간 Wreck와 document:Wreck를 분리. 이름·owner가 명시된 속성만 연결. 실제값/표준정의 구분은 명시 때만 | 잘못 attribute라고 부른 Wreck/Obstruction 등을 올바른 feature로 변경 |
| Q6_01 | Wreck 정의 설명 과업과 실제 정의 대상 유형, 표준·출처·edition/locator 명시 여부 | 명시되지 않은 FC hash/locator를 실제 파일에서 찾아서 채움 |
| Q6_02 | 고정 구조물/부유표지 구분과 비교 근거. 별도의 잘못된 유형/추가 비교 기준도 기록 | 높이/관광용 비교를 fixed/floating 모델 구분으로 인정 |
| Q6_03 | AnchorageArea 정의 출처를 제시하는 과업. 실제 쓴 경로/hash/locator와 명시 판본을 기록 | 다른 원천 hash를 FC hash로 수정, 경로만으로 hash/locator를 보충 |

과업 이름의 간단한 token 검사는 필요한 witness의 존재를 확인하는 검사일 뿐이다. 의미를 충분히 표현했는지 판단하는 부분은 명시적인 AI 검토 기록이며, 별도 사람이 재검토할 수 있도록 원문과 판정 이유를 남긴다. 이를 결정론적 자연어 이해 또는 독립 인간 판정으로 표현하지 않는다.

## 14종 원자와 canonical 값

- feature/requested_object/reference: 고정 별칭표만 사용. 넓은 객체명(Lighthouse, MarinePlaceName)과 FC feature를 구분한다. 중국어 锚地/限制区域/港口는 각각 Anch­orageArea/RestrictedArea/Harbour로 AI 번역 주석하고 원문을 보존한다. unknown 값은 그대로 남겨 FP 대상이 사라지지 않게 한다.
- operator: 구조화 within/covers/dwithin은 서로 바꾸지 않는다. `within 5km`/`반경5000m`/`距离…2公里范围`처럼 거리 표현이 명시된 본문은 dwithin이다. 원문 반대 방향이나 polygon 의미가 불명확하면 교정하지 않는다.
- distance_m/reference_crs/reference_geometry_id: 명시 값만. km→정수m 변환은 정확한 경우만 허용하고 반올림·기본값·좌표 변환은 금지한다. reference ID는 모델이 실제 쓴 값만 기록한다.
- attribute_binding: `{owner, attribute}`. owner가 없으면 null을 기록하고 임의로 객체를 선택하지 않는다. 본문에서 feature 코드를 attribute라고 주장하면 잘못된 attribute_binding으로 유지한다.
- standard: `{standard, edition}`. 명시하지 않은 edition은 null이다. 실제 답변의 파일명에 `2.0.0`이 명시된 경우는 그 문자열 witness를 기록할 수 있다.
- source_binding: 모델이 실제 연결한 source_path/source_label/source_sha256/locators만. 빠진 hash는 null, locators는 []로 남긴다. 검증된 올바른 출처로 교체하지 않는다. 부정확한 source claim도 보존한다.
- input_requirement: 선택 영역이 필수라는 명시 요구만 인정. 원래 질의에 selected area라는 단어가 있는 것만으로는 부족하다.
- comparison_criterion: 개수, 최소/최대거리, 서로 다른 FC 정의, 원천범위와 기준 공개의 명시 의미를 정해진 ID로 투영한다. height/structure/layout 등 추가 기준도 실제 값으로 보존한다.
- distance_metric: WGS84 ellipsoid, point-to-point, minimum geometry-to-geometry, polygon area, boundary inclusive 등의 각 구성값마다 명시 witness를 요구한다. centroid/boundary line/sphere와 바꾸지 않는다. JSON에 완전한 값이 직접 있으면 literal witness로도 검증한다.
- task_obligation: 위 18행의 의미 인식 조건에 따라 부여하며 내용·실행 정답성과 분리한다.

## 상충·반복·실패·추가 주장

구조화/본문의 합집합을 평가한다. Q5_02 B2의 구조화 Harbour/AnchorageArea와 본문 AnchorageArea/RestrictedArea는 모두 남긴다. 같은 task·kind·value의 같은 grounding을 재표현한 경우에만 witness들을 한 원자로 병합한다. 별개의 주장인 중복은 `independent_assertion_reason`으로 구분하여 scorer의 FP 대상으로 남긴다. 반복된 실제 객체 결과는 claim sidecar에 따로 보존한다.

schema INVALID_RESPONSE 11개를 제외하지 않는다. 유효 JSON의 명시 필드와 본문은 그대로 검토한다. 절단 JSON은 재구성하지 않고 실제 관측된 접두부의 완전한 field token과 본문 span만 검토한다. 응답이 아예 없는 timeout은 새 검토 양식을 거쳐 관측된 원자 공집합으로 기록할 수 있지만, 관측하지 못한 답안이나 검토하지 않은 답안을 자동 []로 바꾸지 않는다. 각 raw 상태는 분모와 함께 남긴다.

객체 ID/좌표/실제 속성값/정의 문장 자체의 사실 정확도는 기존 RQ1 atom GOLD의 범위 밖이다. 삭제하지 않고 claim sidecar에 원문과 제외 사유를 보존한다. 원문 전체 각 필드를 검토하고 본문 전체 SHA·글자 수·AI 검토 이유를 기록한다. sparse 후보 사전주석만 검토했다고 전체 완료로 표시하지 않는다.

## 실행 및 동결

기존 36개 AI 검토: `outputs/rq1_prediction_complete_20261103_v2/freeze_candidate/ai_reviews.jsonl`. 정규 예측은 같은 폴더 `prediction_atoms.jsonl`, 점수와 조건별 비교는 `measurement/`이다. 상위 폴더의 이전 중간 산출물은 최종 계약이 아니다.

새 Development K1 이후에는 기존 AI 주석을 복사하지 않고 다음 순서로 실행한다.

```powershell
.venv\Scripts\python.exe -m research.marine_geollm_scie.runners.rq1_reviewed_measurement `
  --observations <new_run>/comparison/observations.jsonl `
  --output <new_review_directory>
```

생성된 `reviews_REQUIRED.jsonl`의 36개 전체 원문을 **이 계약으로 AI 검토**하고 raw hash와 case/method/query identity를 유지한다. 새 답안의 새로운 표현에도 같은 규칙을 적용하며 모르는 표현을 정답으로 교정하지 않는다. 필요한 규칙이 계약에 없으면 frozen run을 소급 변경하지 않고 해당 표현/한계를 공개한다. 주석 완료 후:

```powershell
.venv\Scripts\python.exe -m research.marine_geollm_scie.runners.rq1_reviewed_measurement `
  --observations <new_run>/comparison/observations.jsonl `
  --reviews <new_review_directory>/reviews_COMPLETED.jsonl `
  --gold research/marine_geollm_scie/benchmark/grounding_atoms_20261102_v1/gold_atoms.jsonl `
  --output <new_measurement_directory>
```

누락 pair/다른 query/hash/미완성 검토/프롬프트 witness/근거 없는 owner·edition·source 보충은 실패한다. 기존 scorer의 TP/FP/FN을 사용하며 optional GOLD는 exact match한 예측만 별도 중립 처리하고 required 분모는 유지한다. 조건은 기존 multi-label 개발 주석을 그대로 사용하므로 조건별 N을 더하면 전체 N이 되지 않는다. 1개 cluster는 CI null, UNSEEN N=0은 전체 지표 null이다. 2,000회 paired equivalence-group bootstrap, seed=20261103을 고정한다.

최종 freeze 대상은 이 계약, evaluator/runner/test 파일, POLICY JSON/hash, GOLD 원자/schema/manifest hash, case/query/조건 메타데이터 및 source snapshot이다. 원문별 AI annotation은 새 실행 후 만들어지는 측정 산출물이므로 모델 prompt나 실행 입력에 들어가지 않는다. Development K1에서 코드 결함을 고치면 새 소스 freeze로 재실행한다. 홀드아웃은 열거나 개발에 사용하지 않는다.
