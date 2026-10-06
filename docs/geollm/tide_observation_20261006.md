# 국립해양조사원 실측·예측 조위 연결

공식 명세: https://www.data.go.kr/data/15142507/openapi.do

- 제공기관: 국립해양조사원. 고정 HTTPS operation: `surveyTideLevel/GetSurveyTideLevelApiService`.
- 필수 `obsCode`, `type=json`, 인증키와 선택 `reqDate`, `min`, `pageNo`, `numOfRows` 사용. 실측은 `bscTdlvHgt`, 예측은 `tdlvHgt`이며 서로 대체하지 않는다. 인증키는 Git 제외 `.env`의 `KHOA_TIDE_SERVICE_KEY`에만 설정하고 Compose backend 환경으로 전달한다.
- `GET /api/v1/observations/tide?station=DT_0001&date=20261006`: 기본 60분 간격/300개, 최대 300개씩 페이지 조회. `has_more`로 미조회 페이지를 알린다. 현재 웹은 60분 간격을 요청하며 자동 polling이나 일 단위 예약 수집은 하지 않는다.
- 웹 지도 아래 조위 패널에서 관측소 코드/날짜 입력 → 조회·저장 → 저장 이력 조회. 인천 DT_0001은 실제 공급자 응답으로 확인했다. 전국 관측소 코드·항만 이름의 자동 매핑은 구현하지 않았다.

## 로컬 저장 위치

- Docker `an_geollm_postgis`의 `gbhd_s101` DB, `serving.khoa_tide_observations`와 `serving.khoa_tide_fetches`.
- 전자는 실측·예측 값, 관측소 코드·이름, 원천 관측시각, 위경도, fetch_id를 저장한다. 후자는 조회시각·출처·요청일 및 정규화 응답 JSON 스냅샷이다. 공급자 원본 HTTP 바이트 보관소는 아니다.
- 각 실제 API 조회마다 새 fetch_id를 저장하여 수정된 예측/실측 이력을 유지한다. 관측시각과 조회시각은 다르다. 30초 메모리 캐시 적중 시에는 중복 저장하지 않는다. 두 테이블 삽입은 같은 transaction이다.
- 물리 데이터는 Compose의 `postgis_data` volume(현재 실제 이름 `docker_postgis_data`, docker inspect 확인)이 컨테이너 `/var/lib/postgresql/data`에 보관한다. `.env`나 Dataset 폴더에 관측 값을 저장하는 구조가 아니다. volume 삭제는 별개이며 백업 정책은 후속 작업이다.
- 이력: `GET /api/v1/observations/tide/history?station=DT_0001&date=20261006` (최신 조회 우선, 기본 300개). 과거 이력을 현재 실시간 값이라고 표시하지 않는다.

```powershell
docker exec geollm_backend python -m scripts.initialize_tide_store
docker exec geollm_backend python -m pytest tests/unit/test_tide_observation.py -q
```

## 검증과 제한

- 제공 키로 공식 API HTTP 200 / NORMAL_SERVICE, 인천 실측·예측 값 수신 확인. 단위 테스트 6 passed: 실측/예측 필드 구분, 0·음수·결측, JSON/XML 인증 오류, 입력 오류, 비밀정보 비노출, 저장/캐시. JS 문법 검사 통과.
- 재배포 실제 API: DT_0001/20261006 60분 간격 24건 HTTP 200 및 storage=STORED, 이력 재조회 24건 HTTP 200. 존재하지 않는 날짜 20260230은 422/TIDE_INVALID_DATE. 원본 관측은 `outputs/tide_runtime_20261006.json`에 보존(커밋 제외).
- 웹에서도 24건 DB 저장 완료, 실측/예측 열 분리 및 향후 시각의 실측 미제공 표시 확인. 두 조회 스냅샷 이력 48건을 확인했다. 화면 `outputs/tide-observation-20261006.png`는 커밋 제외. 이력 건수는 계속 조회하면 증가한다.
- HTTP/API 장애·인증 거절·NO_DATA·DB 저장 실패를 구분한다. DB 실패 시 조회값은 반환하지만 storage=FAILED를 표시한다. 키가 포함된 upstream URL/예외 원문은 반환·로그하지 않으며 redirect하지 않는다.
- OpenAPI 필드 정의에 단위·수직기준면이 명시되어 있지 않아 unit/vertical_datum=null을 유지한다. 별도 활용가이드 검증 전 cm/m 추측이나 UKC·수심 합산을 하지 않는다. 관측시각 문자열은 원천 그대로 보관한다.
- 자연어 질의 라우팅, 관측소 지도 선택, 전체 관측소 registry, 만조/간조·대조기 계산은 아직 연결하지 않았다. 기존 광범위 조석 예보 차단을 해제하지 않는다. 이 API 조회 성공을 공식 항해 분석 또는 ExecutionValidator 승인으로 승격하지 않는다.
