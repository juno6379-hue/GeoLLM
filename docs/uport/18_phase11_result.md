# Phase 11 — 울산항 선석 제원 소스 연결 경계

## 완료 작업

- 사용자 제공 Drive 폴더의 선석 제원 원본 CSV를 작업 공간 `D:\Hangman\uport-source\berth-specs-20240819.csv`에 내려받아 CP949 인코딩과 실제 구조를 검증했다. 원본 파일은 코드 저장소에 커밋하지 않았다.
- 서버 운영자가 `UPORT_BERTH_SPEC_CSV`로 경로를 지정하면 `GET /api/v1/uport/operations/berth-reference`에서 선석 참고정보, 원본 SHA-256, 품질 표시를 읽을 수 있다. 미설정·잘못된 형식은 503 `DATASET_NOT_AVAILABLE`을 반환한다.
- 대시보드 선석 카드에는 읽힌 제원 행 수와 품질 표시를 보여 준다. 점유 여부나 가용 선석 수로 표시하지 않는다.
- Phase 8 문서의 행 수를 머리글과 마지막 개행을 제외한 실제 데이터 행 수로 정정했다.

## 수정 파일

- `services/orchestrator/main.py`
- `services/orchestrator/static/uport/index.html`
- `docs/uport/15_phase8_result.md`

## 신규 파일

- `services/uport/operations/__init__.py`
- `services/uport/operations/berth_reference.py`
- `services/uport/operations/router.py`
- `services/orchestrator/static/uport/reference.js`
- `tests/unit/test_uport_berth_reference.py`
- `tests/unit/test_uport_reference_ui.js`
- `docs/uport/18_phase11_result.md`

## 재사용 구성과 아키텍처

- 기존 FastAPI `/api/v1` 라우팅, Pydantic 계약, 대시보드 카드 구조를 재사용했다.
- 사용자 제공 원본의 공식 항구·부두·시설 코드를 유지한다. 원본 해시로 읽은 파일 버전을 구별한다.
- 파일 경로는 서버 환경변수에서만 읽고, API 호출자가 경로를 지정할 수 없다. 이 경계는 선석 점유 Provider나 최적화 입력 Provider가 아니다.

## 실제 데이터 확인

- [Drive 선석 제원 CSV](https://drive.google.com/file/d/1msUAFz-HnXdSqOccMCMTFYPy-f5crQm0/view): CP949, 데이터 144행, 파싱 거부 0행, SHA-256 `d4682bffd1e9958bb64c2bb774215155524f688dccdb62a625207ae44af6e485`.
- 원본에서 상한 톤수 0: 22행, 접안 가능 척수 0: 13행, 시작 톤수가 종료 톤수보다 큰 행: 8행. 원본 값을 수정하거나 결측값을 추정하지 않았다.
- [배정 이력](https://drive.google.com/file/d/1zgaJmXKps0HVPJKVwHntusFhG0bxTcdb/view) 33,698행, [사용 신청](https://drive.google.com/file/d/1P1L_6UZ2om4CNMGcrHzbgCT0kAg3dPWZ/view) 17,100행으로 다시 확인했다. 이 두 파일은 시간 단위 점유와 안정적인 선박별 공통 키가 확인되지 않아 운영 스케줄로 연결하지 않았다.

## 실행 및 테스트 결과

- CP949·UTF-8, 부적합 스키마, 품질 표시, 환경변수 미설정·설정 API 테스트 통과.
- 실제 내려받은 원본 파일로 API 호출: HTTP 200, 144행, 위 품질 표시 반환, `operational_status_available=false` 확인.
- U-Port 기존 수용·계획·실행·지도·최적화·예측 회귀 테스트 통과.

## 발견된 문제와 남은 작업

- 선석 제원 파일에는 LOA 한계 길이·수심·실시간 점유가 없어 현재 최적화 계약과 직접 결합할 수 없다.
- 배정·신청 CSV의 날짜는 시간 단위 충돌을 검증하기에 부족하다. 선박 식별자와 운영 스케줄 소스를 확보해야 한다.
- 다음 단계는 배정·신청 자료의 키와 날짜 품질을 정식으로 프로파일링하고, 검증된 운영 데이터 공급자 연결 가능 여부를 판단한다.
