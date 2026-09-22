# 가상 AIS 시계열 v2

작성일: 2026-09-22

## 목적과 경계

`scripts/generate_synthetic_ais_v2.py`는 ETA 전처리, 시퀀스 학습, 모델
저장·로딩, API와 지도 연동을 기술적으로 시험하기 위한 재현 가능한
다항차 데이터 생성기다. 모든 행은 `SYNTHETIC_SIMULATION`으로 표시하며
운영 ETA 정확도, 실데이터 준비도, 모델 Registry 승격에는 사용하지 않는다.

## 보강 내용

- 선박별 복수 항차와 항차별 고유 ID
- UTC 관측·수신·입항 시각과 `minutes_to_arrival` 정답
- SOG, COG, heading, 항해상태, 선종
- 정상 접근, 감속, 묘박 대기, 관측 공백, 위치 잡음 시나리오
- 품질 플래그와 dataset ID
- seed 기반 재현성과 JSON manifest
- 기존 감사기 호환 컬럼 유지

## 생성 명령과 현재 결과

```powershell
python -m scripts.generate_synthetic_ais_v2 geollm_results/synthetic_ais/eta_training_demo_v2.csv --vessels 60 --voyages-per-vessel 3 --observations 72 --seed 20260922
```

현재 생성 결과는 60척, 180항차, 12,960관측이다. 다섯 시나리오는 각각
36항차이며 manifest의 `operational_use_allowed`는 `false`다. 출력 CSV와
manifest는 의도적으로 Git 추적 대상이 아닌 `geollm_results`에 둔다.

## 검증 기준

- 정확히 12,960행과 180개 고유 항차
- 모든 시나리오 존재
- 모든 관측의 source가 `SYNTHETIC_SIMULATION`
- 모든 관측에 양수인 도착 잔여시간 정답 존재
- manifest에 운영 사용 금지 표시
- 같은 파라미터와 seed로 byte-identical CSV 생성

단위 테스트는 `tests/unit/test_generate_synthetic_ais_v2.py`에 있다. 백엔드
이미지에 pytest가 없는 환경에서도 표준 Python 불변조건 검사를 실행해
행·항차·시나리오·정답·합성 데이터 보호 조건이 통과함을 확인했다.
