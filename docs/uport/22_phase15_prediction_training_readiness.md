# 15단계: Prediction Agent 학습 준비 상태

검토일: 2026-09-19

## 확인한 자료

| 위치 | 확인 결과 | ETA 학습 가능 여부 |
|---|---|---|
| `Dataset/AIS항로분석.zip` | 월별 격자 Shapefile | 불가: 개별 선박 항적과 입항 시각이 없음 |
| `Dataset/AIS주요통항로분석.zip` | 월별 지도 타일 PNG를 담은 TAR | 불가: 이미지 타일은 선박별 관측 기록이 아님 |
| `Dataset/V-PASS항로분석.zip`, `Dataset/V-PASS주요통항로분석.zip` | 격자·지도 타일 | 불가: ETA 정답 레이블이 없음 |
| `data/fixtures/time_series_observation_sample.csv` | 수위 관측 예시 | 불가: 선박·항만·입항 기록이 없음 |
| 운영 `gbhd_s101` DB | `serving.vessel_traffic_control_area_current`만 관련 테이블명으로 확인 | 불가: 선박별 AIS 관측 및 실제 입항 이력 테이블이 없음 |

현재 확인 범위에서는 `mmsi`, 시각, 위치, 목적항, **실제 입항 시각**을 연결할 수 있는 자료가 없다. 따라서 LSTM·GRU·TFT의 학습, 보류 집합 평가, 최적 모델 선택 및 `ready` 등록을 실행하지 않았다. `data/uport_prediction_models.yaml`의 `unavailable` 상태를 유지한다.

## 구현 후보 및 허가 확인

| 후보 | 확인한 공개 라이선스 | 적용 방안 |
|---|---|---|
| PyTorch | BSD 계열, 저장소의 `LICENSE`와 패키지의 제3자 고지 확인 필요 | LSTM·GRU 계열 모델의 학습 및 추론 기반 후보 |
| PyTorch Forecasting | MIT, 저작권·라이선스 고지 유지 필요 | Temporal Fusion Transformer 구현 후보 |

공식 출처: [PyTorch LICENSE](https://github.com/pytorch/pytorch/blob/main/LICENSE), [PyTorch Forecasting LICENSE](https://github.com/sktime/pytorch-forecasting/blob/main/LICENSE). 두 패키지는 현재 U-Port Prediction Agent에 설치·연동하지 않았다. 공개 소스 코드의 라이선스와 학습 데이터의 이용 권한은 별도로 확인해야 한다.

## 학습 시작 조건

1. 이용 권한과 기간이 확인된 AIS 원시 관측을 선박·시각 순으로 확보한다.
2. 항만별 실제 도착 또는 접안 이벤트를 확보하고, AIS 항적과 선박 식별자·시간으로 결합한다.
3. 예측 시점 이후의 정보를 입력 특성에서 제외하고, 선박 또는 항차 단위로 학습·검증·보류 집합을 분리한다.
4. 단순 ETA 기준 모델과 LSTM·GRU·TFT를 동일한 보류 집합에서 비교한다. MAE, RMSE, 90백분위 오차와 항만별 오차를 기록한다.
5. 선택한 모델의 아티팩트, 입력 스키마, 데이터 계보, 버전, 평가 결과를 검증한 뒤에만 Registry를 `ready`로 변경한다.

혼잡도·대기시간·선석 점유 예측은 각각 항만 교통량, 대기 시작·종료, 선석 점유 시작·종료의 정답 이벤트가 추가로 필요하다. 현재 ETA 전용 계약과 Registry만 있으므로 이를 ETA 모델의 완료 범위로 간주하지 않는다.
