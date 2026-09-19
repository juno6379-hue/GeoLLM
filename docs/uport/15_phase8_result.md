# Phase 8 — 선석 운영 최적화 결과

## 완료 작업

- 선박·선석·운영 가능 시간·원본 데이터 ID를 포함한 공통 입력 계약을 만들었다. LOA, 폭, 흘수, 선석 길이, 수심, 화물 종류, 안전 거리와 중복 ID를 검증한다.
- FCFS 기준안은 도착 순서에서 접안 가능한 가장 이른 선석을 선택한다.
- NSGA-II는 동일 입력에 대해 총 대기시간과 최대 개별 대기시간의 Pareto 순위, 혼잡도, 교차·변이를 이용한 재현 가능한 탐색을 수행한다.
- MIP는 PuLP로 이진 선석 선택과 선박 간 비중첩 제약을 구성하고 CBC 또는 HiGHS를 선택할 수 있게 했다. 실행 파일이나 패키지가 없으면 사용 불가를 명시한다.
- `POST /api/v1/uport/optimization/compare`는 네 알고리즘을 같은 입력에 적용하고 각각의 계산 결과 또는 오류 코드를 반환한다. 이 API는 호출자가 제공한 운영 스냅샷을 사용하며 실시간 항만 DB 연결을 주장하지 않는다.

## 수정 파일

- `services/orchestrator/main.py`

## 신규 파일

- `services/uport/optimization/__init__.py`
- `services/uport/optimization/contracts.py`
- `services/uport/optimization/common.py`
- `services/uport/optimization/algorithms.py`
- `services/uport/optimization/mip.py`
- `services/uport/optimization/router.py`
- `tests/unit/test_uport_optimization.py`
- `docs/uport/15_phase8_result.md`

## 재사용 구성과 아키텍처

- 기존 FastAPI `/api/v1` 라우팅 및 Pydantic 검증 방식을 재사용했다.
- 예측 모델과 운영 최적화 코드를 별도 패키지로 유지했다. Capability Registry의 `uport.berth.optimize` 상태는 운영 데이터 제공자가 없으므로 `unavailable`을 유지한다.
- 모든 계산 결과에 요청의 `source_dataset_id`를 전달한다. 최적화 알고리즘의 숫자는 LLM 서술에서 생성되지 않는다.

## 데이터 확인

- 사용자가 제공한 Drive 폴더의 CSV 원본 텍스트를 확인했다: 선석 제원 145행, 선석 배정 33,699행, 선석 사용 신청 17,101행.
- 선석 제원 CSV에는 접안 가능 톤수·척수가 있지만 최적화에 필요한 선석 길이·수심은 없다.
- 배정 이력에는 선박 연결용 안정적 ID와 시간 단위 점유 구간이 없다. 신청 파일도 명확한 선박별 공통 키가 없다.
- 따라서 CSV를 운영 가능 시간·수심 등의 값으로 자동 치환하거나 실시간 최적화 입력으로 적재하지 않았다. 원본 한글 인코딩과 결측·이상치 분석은 정식 데이터 어댑터 구축 시 필요하다.

## 실행 및 테스트 결과

- FCFS 비중첩·대기시간 계산, 물리 제약 차단, NSGA-II 재현성, 입력 계약, 솔버 부재 응답을 검증했다.
- U-Port 최적화·예측·실행·계획·지도 테스트를 함께 통과했다.

## 발견된 문제와 남은 작업

- 현재 환경에 PuLP, CBC, HiGHS가 없어 MIP의 실제 최적해 경로는 실행 검증하지 못했다.
- 운영 데이터 제공자와 선석 길이·수심·시간 단위 점유·선박 식별자를 확보해야 실데이터 최적화를 연결할 수 있다.
- Phase 9에서 계산 결과를 지도·Agent 컨텍스트와 양방향으로 연결한다.
