# 16단계: 공공데이터 항만 API 연결

## 연결한 서비스

| 자료 | 제공된 기본 URL | U-Port 조회 URL |
|---|---|---|
| 선박운항정보 | `https://apis.data.go.kr/B551938/VslNvgtInfoService` | `GET /api/v1/uport/vessel-navigation/records` |
| 수출입 화물정보 | `https://apis.data.go.kr/B551938/IntgCagInfoService` | `GET /api/v1/uport/cargo/records` |

두 조회 API는 서버 측에서만 공공데이터 인증키를 사용한다. 클라이언트에는 키나 상위 서버의 전체 요청 URL을 반환하지 않는다. `page_no`는 1~10,000, `num_of_rows`는 1~100, `response_format`은 `json` 또는 `xml`만 허용한다. 응답은 2 MB로 제한하고, JSON/XML 오류 응답은 실패로 처리한다.

## 운영 설정

```text
UPORT_PORT_DATA_SERVICE_KEY=<공공데이터포털 일반 인증키>
UPORT_VSL_NVGT_OPERATION=<선박운항정보 문서의 GET 오퍼레이션명>
UPORT_INTG_CAG_OPERATION=<수출입 화물정보 문서의 GET 오퍼레이션명>
```

키는 저장소에 넣지 않는다. 두 서비스에 같은 키를 사용할 수 있다. 오퍼레이션명은 `get`으로 시작하는 영숫자 경로만 허용하며, **공식 문서의 실제 이름**을 설정해야 한다. 기본 URL만 호출하면 제공자가 `NO_OPENAPI_SERVICE_ERROR`를 반환했다. 따라서 오퍼레이션명을 추측해서 운영 호출하지 않는다.

## 검증 및 데이터 의미

JSON·XML 파싱, 반복 XML 항목, 페이지 제한, 설정 누락, 상위 서버 실패, 키 비노출, 서비스별 경로 분리를 단위 테스트 5개로 검증했다. 실제 데이터 조회는 오퍼레이션명이 확인된 뒤 수행해야 한다. 선박운항정보와 화물정보는 각자의 원천 자료로 표시하며, 실제 입항 시각과 선박별 AIS 관측을 확인하기 전에는 ETA 학습 레이블이나 학습 완료 모델로 취급하지 않는다.
