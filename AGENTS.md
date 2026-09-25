# Repository Agent Instructions

## Session startup

이 저장소에서 작업을 시작할 때 다음 절차를 우선 수행한다.

1. `docs/geollm/remaining_work_roadmap.md`를 처음부터 끝까지 읽는다.
2. 문서의 `P0 미비점`과 `다음 실행 순서`를 확인한다.
3. `P1 Ollama 의도 보조와 QLoRA 보강`의 shadow-mode 후보 점수 결합 실험 상태를 확인한다.
4. 코드, 테스트, 컨테이너 및 실제 서비스 상태를 확인하여 문서 내용이 현재 상태와 일치하는지 검증한다.
5. 사용자의 새 요청이 별도 우선순위를 지정하지 않았다면 첫 번째 미완료 P0 항목부터 작업한다.
6. 문서에 완료됐다고 적혀 있더라도 검증되지 않은 항목은 완료로 간주하지 않는다.

## Work policy

- 질의 라우팅은 표현의 단일 키워드가 아니라 형태·사전 존재 여부·시간/공간/실행 슬롯·대화/지도 문맥·근거 가용성을 결합해 판단한다.
- Ollama는 모호한 의도와 복합 분석 요구를 해석하는 후보 생성기로 사용한다. registry, KG, PostGIS 및 도구 실행 결과를 대신하는 사실 권위로 사용하지 않는다.
- Ollama에는 규칙·슬롯·registry가 만든 동일 후보를 평가하게 한다. 초기에는 shadow mode로만 기록하고 점수 calibration과 오류 분석 없이 실행 결정권을 부여하지 않는다.
- shadow 실험은 규칙/Ollama/혼합 순위, disagreement, 실행 결과, gold label, prompt/model/registry version을 재현 가능하게 보존한다.
- QLoRA는 로드맵에 명시된 gold-label, holdout, 오류 반복성, 평가 및 rollback 조건을 충족한 뒤 적용한다.
- authoritative registry의 exact hit를 답변 정확도 100%로 표현하지 않는다. 의도 적합도, 근거 적합도, 분석 완결도와 gold-label 정확도를 구분한다.
- GeoLLM 공통 의도 해석·분류·평가는 `docs/geollm/`에서 관리한다. UPort 전용 기능과 혼동하지 않는다.
- 단일 intent 라벨 불일치를 오분류로 단정하지 않는다. 필수 작업·허용 capability 조합·입출력 계약·실제 근거를 기준으로 판단하며, AI 검토 의견은 근거와 함께 기록하되 human gold로 취급하지 않는다.
- 실제 서비스 라우팅 변경은 단위 테스트뿐 아니라 실행 중인 API에서 대표 질의와 부정 사례를 함께 검증한다.

## Session handoff

작업을 종료하거나 사용자가 커밋·푸시를 요청하면 다음 절차를 수행한다.

1. `docs/geollm/remaining_work_roadmap.md`에 완료 사항, 실제 검증 결과, 남은 미비점, 다음 실행 순서를 갱신한다.
2. 새로 발견된 제한이나 실패를 숨기지 말고 P0/P1 우선순위와 재현 방법을 기록한다.
3. 런타임 로그나 자동 생성된 임시 파일은 소스 변경과 구분한다.
4. 관련 코드, 테스트, 스키마, 프롬프트 및 문서를 함께 커밋한다.
5. 사용자가 요청한 경우 원격 저장소에 푸시하고 최종 커밋 ID를 보고한다.
