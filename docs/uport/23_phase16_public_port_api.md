# 16단계: 공공데이터 항만 API 연결

## 연결한 서비스

| 자료 | 제공된 기본 URL | U-Port 조회 URL |
|---|---|---|
| 선박운항정보 | `https://apis.data.go.kr/B551938/VslNvgtInfoService` | `GET /api/v1/uport/vessel-navigation/records` |
| 수출입 화물정보 | `https://apis.data.go.kr/B551938/IntgCagInfoService` | `GET /api/v1/uport/cargo/records` |
| 선박위치정보 | `https://apis.data.go.kr/B551938/VslPstnInfoService` | `GET /api/v1/uport/vessel-position/records` |

두 조회 API는 서버 측에서만 공공데이터 인증키를 사용한다. 클라이언트에는 키나 상위 서버의 전체 요청 URL을 반환하지 않는다. `page_no`는 1~10,000, `num_of_rows`는 1~100, `response_format`은 `json` 또는 `xml`만 허용한다. 응답은 2 MB로 제한하고, JSON/XML 오류 응답은 실패로 처리한다.

## 운영 설정

```text
UPORT_PORT_DATA_SERVICE_KEY=<공공데이터포털 일반 인증키>
UPORT_VSL_NVGT_OPERATION=getVtsBaseVslNvgtInfo
UPORT_INTG_CAG_OPERATION=getIntgCagInfo
UPORT_VSL_PSTN_OPERATION=getVslPstnInfo
```

키는 저장소에 넣지 않는다. 세 서비스에 같은 키를 사용할 수 있다. 오퍼레이션명은 `get`으로 시작하는 영숫자 경로만 허용한다. 세 경로는 울산항만공사 공식 API 상세 페이지의 Swagger 명세에서 확인했으며, 코드에 검증된 기본값을 설정했다. 형식 선택에는 공식 명세의 `resultType=json|xml`을 사용한다. 선박운항의 `callsgn`, `ptentVtsYr`, 화물의 `prtCd`, `ptentYr`, `vyg`, `callsgn`, `bzentyCd`는 필수 조회 조건이다.

## 검증 및 데이터 의미

JSON·XML 파싱, 반복 XML 항목, 페이지 제한, 필수 조회 조건, 설정 누락, 상위 서버 실패, 키 비노출, 서비스별 경로 분리를 단위 테스트로 검증한다. 선박운항·화물·위치 정보는 각자의 원천 자료로 표시하며, 실제 입항 이벤트 정의와 AIS 관측 결합을 검증하기 전에는 ETA 학습 레이블이나 학습 완료 모델로 취급하지 않는다.

## 실제 수신 검증 (2026-09-19)

| 서비스 | JSON | XML | 첫 페이지 | 조회 시점 총건수 |
|---|---|---|---:|---:|
| 선박운항 | `resultCode=00` | `resultCode=00` | 2건 수신 | 522 |
| 수출입 화물 | `resultCode=00` | `resultCode=00` | 2건 수신 | 28 |
| 선박위치 | `resultCode=00` | `resultCode=00` | 2건 수신 | 528 |

세 서비스 모두 운영 백엔드 `localhost:8000`의 U-Port 경로를 통해 확인했다. 총건수는 제공자 데이터 갱신에 따라 변하며, 선박위치 조회 중 529건에서 528건으로 바뀌었다. 위치 응답에는 `lot`, `lat`, `sog`, `updtTm` 필드가 있다. 확인한 한 예의 `updtTm`은 `20260915233452`였으므로 현재 시각의 실시간 위치라고 단정하지 않는다. 선박운항 응답의 `ptentDt`, `dfptDt`, `jobDt`는 ETA 레이블 후보이나 이벤트 정의 및 품질 검증이 필요하다.

공식 명세: [선박운항](https://www.upa.or.kr/opendata/publicDataDetail.do?id=15156628), [수출입 화물](https://www.upa.or.kr/opendata/publicDataDetail.do?id=15156637), [선박위치](https://www.upa.or.kr/opendata/publicDataDetail.do?id=15156631).
