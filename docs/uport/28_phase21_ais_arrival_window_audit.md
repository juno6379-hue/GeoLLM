# 21단계: AIS와 입항 이벤트의 항차별 시간창 감사

`scripts/audit_uport_ais_eta_join.py`는 원시 AIS CSV와 운영 입항 SQLite를 **읽기 전용**으로 비교한다. 동일 MMSI만으로 항차를 확정하지 않는다. 정확한 호출부호·입항연도·항차의 입항 이벤트가 하나이고, 해당 항차의 MMSI가 하나이며, `jobDt`와 `ptentDt`가 일치할 때만 후보 시간창을 만든다. 기본 시간창은 입항 전 72시간이다. 한 AIS 관측이 여러 항차 창에 걸리면 어느 쪽에도 배정하지 않는다. 입항 이후 관측도 제외한다. 서로 다른 관측시각이 두 개 이상인 항차 수를 집계하지만 원시 식별자나 좌표를 출력하지 않는다.

실행 예시는 다음과 같다. 각 시간대는 제공기관 근거를 확인한 뒤 지정해야 하며, 공간 범위도 해당 원시 AIS 계약의 제공 범위에 맞춰야 한다.

```text
python -m scripts.audit_uport_ais_eta_join AIS.csv \
  --arrival-db uport_eta_history.sqlite3 \
  --ais-timezone Asia/Seoul --arrival-timezone Asia/Seoul \
  --bbox WEST SOUTH EAST NORTH
```

보고서의 `eta_training_ready`는 최소 30개 항차의 반복 입항 전 관측, 두 원천의 확인된 시간대, 공간 범위, 실제 입항 이벤트 정의 확인, AIS 자료 이용 조건 확인이 모두 갖춰져야 참이 된다. `--arrival-definition-verified`와 `--source-usage-verified`는 확인 근거가 있을 때만 사용한다. 이 도구는 학습 파일을 생성하지 않는다.

운영 DB에 저장된 항내 위치 702건을 음성 대조 자료로 사용했다. 두 원천의 **상대적 시각 순서만** 비교하기 위해 같은 가상 오프셋을 적용했으며, 입항 전 시간창에 들어온 관측은 0건이었다. 이 점검은 원천 시간대를 UTC라고 확인한 결과가 아니며, AIS 원시자료가 확보됐다는 뜻도 아니다. 현재 `eta_training_ready=false`다.

다음 단계는 2026년 울산항 접근 해역의 승인된 AIS 원시자료와 시각대·이용 조건 근거를 확보한 뒤, 이 감사로 항차별 겹침과 입항 전 관측을 확인하는 것이다. 충분한 항차가 확보되기 전에는 ETA 모델 학습을 시작하지 않는다.
