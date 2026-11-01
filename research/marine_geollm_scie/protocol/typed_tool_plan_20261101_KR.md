# 연구 최초 계획의 도구 계약 보완

새 개발 조건 `typed_tool_plan_v1`이며 기존 v3 원본·GOLD·보고서는 변경하지 않는다. 모델 실험 개선과 운영 기능 구현은 별개다.

## 원인

v3 B3의 도구 설명은 `source: s101|marine_places|navigation_aids`와 `reference_geometry: explicit input WKT OR geometry_ref...` 같은 의사 코드를 사용했다. 모델은 이를 실제 값으로 복사하여 source를 배열, feature를 설명문, analysis_type을 설명문으로 반환했다. 도구 arguments의 JSON Schema가 자유 object여서 형식 검사 후 실행기로 넘어갔고 `SOURCE_OR_OPERATOR_TYPE_INVALID`로 공간 실행이 막혔다. 이는 P0 차단 능력과 별개인 최초 계획 생성 실패다.

Q5-03의 유일한 INVALID_INITIAL_PLAN은 응답 JSON이 아니라 23.4초 후 Ollama HTTP500으로 raw_response가 없던 경우다. 기존 원본에는 HTTP body가 없어 정확한 서버 내부 원인을 확정할 수 없다. schema 보완으로 이 오류까지 해결했다고 주장하지 않는다.

## 보완 범위

- 새 `baselines/tool_contract.py`가 실제 tool_id와 인자별 type/enum을 정의한다. source는 단일 문자열이며 도구별 arguments는 서로 구분한다.
- B3 최초 생성에만 JSON Schema format과 같은 schema 검사를 적용한다. B0~B2는 기존 생성 조건을 유지한다. 생성된 하나의 계획을 동결하여 B3/B4/P0/H에 동일하게 전달한다.
- 도구 설명을 실행 예제처럼 복사하지 않도록 optional interface임을 명시하고, WKT와 registry key, 연산과 analysis_type의 관계를 구분한다.
- 누락 geometry/CRS를 채우거나 잘못된 feature를 교정하지 않는다. schema는 구문 제약이며 승인 권한이 아니다. missing/null은 Validator가 처리하고 source coverage도 기존 executor에서 검증한다.
- seed/온도/768토큰/180초와 재시도 정책은 유지한다. 변경 소스와 새 계약을 동결한 전체 비교만 후속 결과로 사용한다.

## 검증과 개발 자료

관련 단위·회귀 40개 통과. 모델 호출 결과는 별도 개발 실행 뒤 기록하며 단위 검사만으로 의미 정확도 개선을 주장하지 않는다.

주검증 개발 v2(`outputs/initial_plan_development_20261101_v2`) 2건은 새 schema를 만족했으나 정상 공간 요청에서 clarify+catalogue를 선택하고, 기준영역 없는 요청에 결과처럼 서술하는 의미 오류가 남았다. 두 경우 모두 공간 실행은 하지 않았다. 형식 제약만으로 계획·답변 의미가 해결되지 않았다. 별도 수작업 정상 엔진 통제는 아래 Oracle의3개 feature ID를 실제 SQL로 반환했다. 이는 모델 생성 성공이 아니다. 개발 v1은 Executor 인자 누락으로 원문 저장 전 실패했고 그 호출은 평가에서 제외하며 실패사실을 보존했다.

빈 결과만 검증하던 복구 진단을 보완할 수 있도록 실제 연구DB에서 nonempty 개발 후보를 읽기전용 SQL로 구했다. `outputs/initial_plan_development_20261101_v1/nonempty_oracle.json`에 선택 규칙·원본 ID·SQL·snapshot hash를 기록했다. 고정 내부 bbox 안에서 최소 ID Wreck560495의 점 `POINT(129.1894508 35.0225944)`를 선택하고, 반경500m에서 독립 ST_Distance 조건으로 객체 ID560495/599552/700746을 얻었다. 이는 source feature 단위3건이며 동일 실재 시설3개를 뜻하지 않는다. 실제 feature 중복·축척 정책은 별도 명시해야 한다. 이 개발 후보는 원래18문항 GOLD나 논문 cohort에 합치지 않았다.
