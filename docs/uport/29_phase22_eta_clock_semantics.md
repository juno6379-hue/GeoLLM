# 22단계: ETA 원천 시각 의미 검증과 데이터셋 보류

2026-09-20에 울산항만공사 공식 Swagger 원문을 재확인했다.

| API 필드 | 제공기관 설명 | 현재 처리 |
|---|---|---|
| 선박운항 `ptentDt` | 입항일시 | `입항` 이벤트의 도착 시각 **후보** |
| 선박운항 `jobDt` | 작업일시 | `ptentDt`와 일치하는지 검증하는 독립 필드 |
| 선박위치 `updtTm` | 갱신시각 | 위치 레코드 갱신 이력으로만 보관 |

원문: [울산항만공사 선박운항정보](https://www.upa.or.kr/opendata/publicDataDetail.do?id=15156628), [울산항만공사 선박위치정보](https://www.upa.or.kr/opendata/publicDataDetail.do?id=15156631). 두 명세에는 시간대가 명시되지 않았다. `ptentDt`의 설명만으로 실제 입항의 공간적·업무적 기준점이나 확정·정정 규칙도 확인할 수 없다. 공유된 [울산항 Port-MIS 신고 가이드북](https://drive.google.com/file/d/1WaWK-EV-vtQ_tsaPEu9DY2aigCSMp2Oq/view)은 입항정보를 관제 현황을 바탕으로 입력한다고 안내하지만, 이 API 필드의 시간대와 실제 입항 기준점을 정의하지 않는다.

기존 SQLite 볼륨을 백업한 뒤 `positions.observed_at_raw` 열을 `positions.source_updated_at_raw`로 제자리 변경한다. 수집기는 원천 `updtTm` 문자열을 그대로 유지하고, 품질 보고서는 `position_clock_verified=false`를 기본으로 내보낸다. 데이터셋 생성기는 이 값이 진짜 관측시각이라는 제공기관 근거가 확인되기 전에는 학습·보류 파일을 생성하지 않는다. 별도 AIS 원시자료는 `수신시간`의 의미와 시간대를 확인한 뒤 `audit_uport_ais_eta_join.py`로 검사한다.

새 수집 주기 후 운영 DB에는 고유 위치 갱신 이력 930건, 완전한 항차 키 101개, 서로 다른 갱신시각 2개 이상인 항차 82개가 있다. 확인된 `입항` 이벤트보다 앞선 갱신시각이 있는 항차는 0개다. 따라서 현재 **학습 0건·보류 0건**이며, ETA 모델 학습은 시작하지 않는다. 다음 단계는 실제 입항 전 AIS 관측자료와 시간대·이용 조건·입항 이벤트의 기준점 근거를 확보하는 것이다.
