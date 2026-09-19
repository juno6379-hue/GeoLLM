# Phase 7 — ETA 예측 모델 계약 및 평가 경계

## 완료 작업

- AIS 관측 시각·좌표·속도와 ETA 요청/응답을 검증하는 계약을 추가했다. 관측 순서와 시간대, 미래 ETA를 확인한다.
- LSTM, GRU, TFT 모델의 어댑터와 버전형 등록부를 추가했다. 현재 학습된 ETA 모델과 추론 구현이 없어 모두 `unavailable`로 등록했다.
- 실제 도착 시각이 있는 홀드아웃 사례로 MAE, RMSE, P90 절대오차, 편향을 분 단위로 계산한다. 모델 선택은 동일 평가 데이터셋, 버전 일치, 최소 표본 수, 아티팩트 존재를 요구한다.
- `GET /api/v1/uport/predictions/models`는 모델 상태를 공개하고, `POST /api/v1/uport/predictions/eta`는 준비된 모델이 없으면 `MODEL_NOT_AVAILABLE`(503)을 반환한다.

## 수정·추가 파일

- 수정: `services/orchestrator/main.py`
- 추가: `data/uport_prediction_models.yaml`, `services/uport/prediction/`의 계약·어댑터·평가·등록부·Agent·라우터, `tests/unit/test_uport_prediction.py`, 이 문서

## 재사용 구성과 설계

- 기존 FastAPI `/api/v1` 라우팅과 Pydantic 검증을 재사용했다.
- 모델 등록부의 품질 통과 여부와 어댑터의 실제 추론 가능 여부를 모두 확인한다. 현재 어댑터는 학습 가중치를 로드하지 않으며 추정 ETA를 만들지 않는다.
- 일반 시계열 선형 기준선은 선박 ETA 모델로 간주하지 않았다.

## 검증 결과

- U-Port 예측·실행·계획·지도 및 기존 후보 브로커 테스트 27개 통과.
- 계약 검증, 홀드아웃 지표, 모델 선택 차단, API 503 응답을 확인했다.

## 남은 사항과 다음 단계

- AIS 학습/평가 데이터셋, 학습된 모델 아티팩트, 실제 추론 어댑터가 아직 없다. 따라서 실제 선박 ETA 정확도나 운영 데이터 연결은 검증되지 않았다.
- Phase 8에서 선석 최적화의 제약·목적함수·입출력 계약과 실행 가능 데이터 경계를 구현한다.
