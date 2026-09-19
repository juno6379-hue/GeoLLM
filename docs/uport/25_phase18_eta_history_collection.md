# 18단계: ETA 이력 수집과 학습·보류 분할

## 수집 경로

`eta-history-collector`가 6시간마다 기존 U-Port 백엔드 프록시에서 전체 위치 페이지를 가져와 Docker 관리 볼륨 `eta_history_data`의 `/app/eta_history/uport_eta_history.sqlite3`에 저장한다. Windows 호스트 공유 폴더의 SQLite WAL 접근 오류를 피하기 위해 이 볼륨을 사용한다. `mmsiNo`·`callsgn`·`ptentYr`·`vyg`·`updtTm`의 동일 관측은 한 번만 저장한다. 수집 시각은 별도의 UTC 값으로 보관하며, 원천 `updtTm`을 수집 시각으로 대체하지 않는다. 같은 항차의 운항 이벤트도 매 주기 다시 조회해 뒤늦게 게시된 입항 이벤트를 확보한다.

실행 명령은 `docker compose -f docker/docker-compose.yml up -d --no-deps eta-history-collector`이다. 운영 품질 보고서는 `docker exec geollm_eta_history_collector python -m scripts.build_uport_eta_dataset`으로 읽는다. 로컬 단일 주기 검증은 `python -m scripts.collect_uport_eta_history`로 할 수 있다. 두 실행 환경 모두 기존 백엔드 프록시에 접근해야 한다.

## 입항 이벤트와 시각대 판정

울산항만공사 [선박 운항정보](https://www.upa.or.kr/opendata/publicDataDetail.do?id=15156628)는 `입항`을 운항 프로세스 항목으로 열거하고 `입출항일시`와 `작업일시`를 별도 항목으로 설명한다. 공개 설명만으로 `jobDt`가 실제 입항 시각이라고 확정할 수 없다. 따라서 `ioprtVtsNm=입항` 이벤트가 항차에 정확히 하나이고 `jobDt`와 `ptentDt`가 같을 때만 후보 라벨로 삼는다. 값이 일치해도 제공기관이 정한 실제 입항 기준점의 확인은 별도 필요하다.

[위치정보 설명](https://www.upa.or.kr/opendata/publicDataDetail.do?id=15156631)과 운항정보 설명에는 두 원천 시각의 시간대가 명시되지 않는다. 수집기는 원문 시각만 저장한다. `--provider-timezone`은 출처를 통해 검증된 뒤에만 지정한다. 지정 전에는 UTC 변환과 학습·보류 파일 내보내기를 막는다.

## 데이터셋 품질 규칙

`python -m scripts.build_uport_eta_dataset`는 현재 품질 보고서를 출력한다. 항차 결합에는 호출부호·입항연도·항차가 모두 일치해야 한다. 같은 MMSI의 유효 좌표가 입항 전 서로 다른 두 시각 이상 있어야 한다. 입항 이후 위치는 입력에서 제외한다. 최소 30항차, 검증된 시간대(`--provider-timezone`), 제공기관의 실제 입항 기준 확인(`--arrival-definition-verified`)이 모두 있을 때 가장 최근 입항 항차 20%를 보류 집합으로, 이전 항차를 학습 집합으로 내보낸다. 확인 플래그는 근거 확보 후에만 사용한다. 같은 항차의 관측은 양쪽에 나뉘지 않는다. 출력은 Git에서 제외된 `geollm_results/uport_eta_dataset`에 저장한다.

현재 공개 API에서 과거 궤적을 일괄 복원할 수 없고, 첫 수집 주기에는 반복 관측을 확인할 수 없다. 이후 주기의 고유 `updtTm` 증가와 입항 이벤트 게시 여부를 확인해 학습 가능성을 다시 판정해야 한다.
