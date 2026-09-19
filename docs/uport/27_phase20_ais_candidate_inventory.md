# 20단계: 입항 전 AIS 후보 자료 조사와 수용 기준

## 조사 결과

- 사용자가 공유한 [울산항 자료 폴더](https://drive.google.com/drive/folders/1kj1wF2Y6-bjXkBgGmhRlApUJUmgKIw9z)에는 선석·정박지·입항예정 CSV가 있지만, 선박별 원시 AIS 궤적 파일은 없다.
- 연결된 Drive 전체 검색의 `ais_cols.txt`에는 2022년 `해양수산부_선박 AIS 동적정보_20220101.csv`의 열 이름 `MMSI`, `수신시간`, `경도`, `위도`가 기록돼 있다. 실제 CSV는 접근 가능한 검색 결과와 현재 운영 경로에서 확인되지 않았다. 설령 확보하더라도 2022년 관측을 2026년 입항 이벤트에 결합할 수 없다.
- Drive의 `해양수산부_AIS 위치정보 통계_20201027.TXT`는 2020년 통계 파일이다. [공공데이터포털의 연안 AIS 통계 API](https://www.data.go.kr/data/15084033/openapi.do)는 1시간 단위 **해역별 선박 척수**를 제공하며 선박별 시각·좌표 기록이 아니다.
- 운영 PostGIS `marine_geo.ocean_data.ais_tracking`은 0행이다. 기존 `services/ais_analysis_agent/tools.py`가 기대하는 `D:\rag_sources\pdfs` 폴더도 현재 환경에 없다.

## 후보 파일 점검

`python -m scripts.audit_uport_ais_candidate <AIS.csv> --arrival-db <uport_eta_history.sqlite3>`는 CSV를 읽기 전용으로 최대 100만 행까지 검사한다. 필수 열은 MMSI, 관측시각, 경도, 위도다. 유효 좌표·시각·MMSI 수, 관측 연도, 입항 이벤트 연도, MMSI 겹침을 집계해 출력한다. 선박 식별자는 출력하지 않는다. 통계 격자처럼 필수 열이 없는 자료는 즉시 거부한다. 운영 입항 DB는 Docker 볼륨 안에 있으므로 파일을 검사할 때는 같은 볼륨에 접근 가능한 실행 환경을 사용한다.

이 점검은 시간대, 항차 결합, 입항 전 위치 여부를 인증하지 않는다. 관측 연도와 MMSI가 겹쳐도 ETA 학습 가능으로 표시하지 않는다. 원천 제공자의 시간대와 이용 허락, 실제 입항 이벤트 기준, 동일 MMSI의 항차 구분이 모두 확인된 뒤에만 후속 결합 절차를 구현한다.

## 다음 단계

2026년 울산항 입항 전 해역을 포함한 원시 AIS 관측 자료 또는 승인된 공급 API가 필요하다. 최소 필드는 MMSI, 원천 관측시각과 시간대, 위경도, 데이터 제공 범위·이용 조건이다. 자료가 확보되면 본 점검을 실행하고 같은 MMSI의 항차별 시간창을 검증한다.
