# 울산항만공사 항내 위치 응답을 기준으로 한 가상 AIS

기존 백엔드의 `GET /api/v1/uport/vessel-position/records`는 울산항만공사 `VslPstnInfoService/getVslPstnInfo`를 호출한다. 반환 행의 `lat`, `lot`, `sog`, `updtTm`을 가상 궤적의 기준점·표시 속성으로 사용한다.

```powershell
python -m scripts.generate_synthetic_ais geollm_results/synthetic_ais/upa_demo.csv --api-url http://localhost:8000/api/v1/uport/vessel-position/records
```

로컬 API가 실행 중이지 않으면 저장한 프록시 응답을 `--snapshot-json`으로 전달한다. 입력은 `/records` 전체 JSON 응답이어야 한다. 기본적으로 유효한 위치 최대 3건을 골라 각 12개 관측을 만든다. 마지막 가상 좌표는 API 위치에 맞추고 이전 좌표는 일정한 남동 방향 간격으로 만든다. 방향·이동속도·시간 간격은 실제 선박 항적을 재구성한 값이 아니다.

출력에는 기존 감사기용 `MMSI`, `observed_at`, `longitude`, `latitude`와 공급자 형식에 대응하는 `mmsiNo`, `lat`, `lot`, `sog`, `updtTm`이 함께 있다. `MMSI`와 `mmsiNo`는 가상 번호이며 실제 선박 번호를 복사하지 않는다. 모든 행의 `source_type`은 `SYNTHETIC_SIMULATION`이다. `updtTm`은 기준 응답의 **제공기관 갱신시각**을 보존한 것이며, 생성된 `observed_at`은 **가상 관측시각**이다.

이 CSV는 화면·파서·공간 검색 데모에만 쓴다. 실제 AIS 원천, 입항 전 관측, ETA 학습·정확도, 운영 준비 판정에 포함하지 않는다. 원시 위치 응답과 생성 CSV는 저장소에 커밋하지 않는 `geollm_results` 안에 보관한다.
