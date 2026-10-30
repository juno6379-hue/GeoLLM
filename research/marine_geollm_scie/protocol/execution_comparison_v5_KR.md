# 전체 18문항 실행 비교 준비 v5

기존 planning90을 재활용하지 않는다. `compare_execution.py`는 원문18개 × B0–B4를 새로 생성하고 명시적인 도구 호출을 실제 실행한다. 방법명은 `B*_EXECUTION_ADAPTER`이며, P의 운영 graph는 별도 실행군이다. 동일 모델·원천을 사용해도 내부 프롬프트·호출예산·검색·답변생성 방식은 다르므로 같은 계산예산 실험으로 표현하지 않는다.

## 실행 범위

- 모든 방법에 같은 제한 도구 목록을 제공하고, 방법별 evidence packet·tool-first 지시·self-review 유무를 구분한다. 이 설계는 기존 B0–B4 planning pilot과 다른 실행 가능한 확장이다.
- FC exact code/name/alias 조회는 검증한 raw XML을 읽어 definition·geometry·owner별 속성 binding·열거값·XPath·판·해시를 반환한다. `catalogue()`/`record()`의 원천 파싱 함수만 호출하며 사례별 정답 선택 함수는 호출하지 않는다.
- 문서검색은 고정 연구 DB에서 literal substring으로 최대5개 chunk를 조회한다. P의 벡터검색과 동일 알고리즘이 아니다.
- 장소 조회는 operational anchor 또는 실제 지명 원천의 exact name을 사용한다. 공간 조회는 dwithin/nearest만 지원하고 명시적 반경·고유기준점·원천별 범위 검증이 필요하다. 미확정 selected AOI/intersects는 미지원 이유를 보존한다.
- 모든 SQL은 정적 allowlist template이고 입력은 base64 JSON 데이터로 분리한다. 고정 `marine-scie-pilot-db/scie_model_v3`에서 READ ONLY·30초 statement timeout을 적용한다. SQL subprocess는45초 제한, 모델 호출은180초 제한이다.
- 실행된 도구 결과를 structured final_result로 보존한다. 초기 model answer는 미검증 후보로 별도 저장하고 도구 실행 후 LLM 합성 호출을 추가하지 않는다. B4는384+384, 나머지는768 token 한도, context8192/temperature0.2이다.
- schema 유효성이나 tool return만으로 전체 execution_success를 만들지 않는다. 부분 성공·환경오류·정책차단을 receipt별로 보존하며 별도 v5 evaluator가 출력 구성요소를 검사한다.

## 고정 profile

`full_pipeline.py::build_profiles`가 쓰는 `baseline_profile.json`을 받는다. 필수키는 `contains_gold_answers:false`, `snapshot_manifest:{path,sha256}`, `catalogue:{path,sha256}`, `model_digest`다. anchors는 operational source_id/name/aliases/Point geometry이며 gold 정답 ID를 넣지 않는다. coverage는 원천별 `scope_verified`, `max_radius_m_by_anchor`로 한정한다. Q4는 동도 anchor·5000m·고정2022지명 원천 범위이며 현실세계 전국완전성을 뜻하지 않는다. s101/navigation_aids의 미확정 coverage는 false를 유지한다.

모델/원천 해시를 시작 전에 검사하고 evidence packet을 고정한다. 끝에 원천 해시를 다시 대조한다. root의 embedding 작업과 동시에 실행하지 않고 supervisor 단계 순서로 실행한다.

## 실행·중단 재개

```powershell
.\.venv\Scripts\python.exe -m research.marine_geollm_scie.runners.compare_execution --profile RUN/baseline_profile.json --output-dir RUN/baselines --repeats 1 --execute
# 중단 시 같은 profile/model/code/packet/schedule에서만 재개
.\.venv\Scripts\python.exe -m research.marine_geollm_scie.runners.compare_execution --profile RUN/baseline_profile.json --output-dir RUN/baselines --repeats 1 --execute --resume
.\.venv\Scripts\python.exe -m research.marine_geollm_scie.runners.execution_report --baselines RUN/baselines --graph RUN/graph --contracts research/marine_geollm_scie/benchmark/frozen_v5/answer_contracts.jsonl --output-dir RUN/report
```

`--execute`가 없으면 준비 manifest만 만든다. K1은90조건/최대108모델호출이다. K5는 별도 새 run에서450조건/최대540모델호출로 선언하며, `--max-new-rows 90`으로 첫90행만 실행하고 나머지는 같은 run의 `--resume`으로 이어갈 수 있다. K1 manifest를 K5로 변경하는 재개는 거부한다. 조건 사이 지연은 `--inter-condition-delay 0..60`초이다. 실패행도 완료된 관측으로 보존하며 자동 재시도로 교체하지 않는다. 중복/깨진 JSONL을 임의 수선하지 않는다.

## 사후 검사 해석

finalizer가 처음으로 frozen_v5 정답 계약을 읽는다. FC 출력의 정의 존재·geometry·binding·판/원천/locator 연결과 Q4의 실제 반환 properties/provenance 기반 원본 ID를 대조한다. 공간 미실행·원천 불일치는 객체정확도 null이다. v5는 사용자 지시 아래 에이전트가 확정한 계약이며 독립 인간 GOLD가 아니다.

P에 명시적 evaluation_output이 없으면 구조 계약은 미측정이다. 이를 오답/0점으로 baseline과 비교하지 않는다. 공통 출력 관측은 양쪽 실제 답안의 FC 문장·feature code 문자 출현과 반환 인용 개수이며, P의 검색된 excerpt/detail_text를 답안으로 옮기지 않는다. 바꿔쓰기는 문자 일치가 아니어도 옳을 수 있고, 인용 존재는 claim support가 아니다. 전체 의미 정확도와 공통 full-task 승률은 아직 null이다. 모든 누락·제약과 실제 상태·비용은 보고서에 남긴다.
