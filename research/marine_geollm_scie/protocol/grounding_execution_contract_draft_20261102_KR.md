# 명시적 grounding / 실행 신뢰도 계측 계약 초안

상태: **DRAFT / PROPOSED — 합성 테스트용 구현 checkpoint**. 실제 GOLD 원자 주석·실제 답변 원자 추출·동결 run 연결은 아직 수행하지 않았다. 기존 v6 결과, GOLD, 홀드아웃을 변경하거나 새로운 논문 수치를 생성하지 않는다.

## RQ1 입력과 판정

`evaluation/grounding_atoms_v1.py`는 GOLD `{atom_id, kind, task_id, accepted_values}`와 예측 `{prediction_id, kind, task_id, value}`를 명시적으로 받는다. 동일 kind/task 안에서 정확히 일치하는 JSON 값에 한해 최대 일대일 매칭한다. 단위 변환, 새 별칭 추론, feature 보정은 하지 않는다. 허용 동의어는 사전 고정된 accepted_values로만 제공한다. 중복 예측은 FP다.

F1=2TP/(2TP+FP+FN), strict=(FP=0이고 FN=0). 입력 None은 미측정, 빈 배열은 관측된 공집합이다. 양쪽 공집합은 strict=true지만 F1 분모가 0이므로 null이다. 이 점수는 공급된 grounding 원자 범위만 평가하며 전체 작업 의미 정확도나 독립 인간 검수를 뜻하지 않는다.

짝 비교에는 case/repeat/equivalence_group 및 query/GOLD/contract SHA256 일치가 필수다. 반복별 TP/FP/FN을 사례 안에서 평균한 뒤 합산한 micro F1을 계산한다. 동일한 equivalence group 블록을 양 방법에 함께 재표집하여 B−A의 2.5/97.5 백분위 CI를 계산한다. seed와 반복 수를 반환한다. 결측 짝을 버리지 않으며 2개 미만 그룹에서는 CI를 내지 않는다. 0분모 재표집이 있으면 해당 F1 CI는 null이다. 적은 그룹의 CI는 탐색적이며 확증적 결과가 아니다.

## RQ3 입력과 판정

`evaluation/execution_reliability_v1.py`는 실행 대상 eligibility와 실제 관측 E(execution_success), 독립 공간 Oracle 판정 S(spatial_correct)를 받는다. bool과 None을 구분하며 HTTP 성공으로 E를 추정하지 않는다. eligibility 검증과 관측·Oracle 출처는 상위 계층 책임이다.

- ESR=평균 E, raw spatial correctness=평균 S.
- joint SCR=평균(E∧S). E=false이면 S 결측이어도 joint=false다.
- CGE=P(S=true | E=true), SSFR=P(S=false | E=true).
- gap=ESR−joint SCR. CGE와 gap은 서로 다른 지표다.
- 성공 실행이 0이면 CGE/SSFR는 null이다. E 결측은 성공 집단의 소속이 불명확하므로 조건부 비율도 null이다.
- 필요한 관측이 결측이면 전체 해당 비율은 null이며 측정/결측 수와 분모를 함께 반환한다. 비대상 사례는 별도 수로 공개하며 안전 중단 점수로 대체하지 않는다.
- EVQSR의 semantic/plan/claim-evidence 입력이 없으므로 EVQSR를 계산하지 않는다.

기준 문서: `paper_metric_definitions.md`, `../evaluation/rq_metrics.py`, `../../../docs/geollm/rq1_rq3_execution_readiness_20261102.md`. 향후 실제 원자 GOLD/추출 계약 승인, 조건별 cohort/hash 연결, 실제 GIS 로그와 Oracle 연결 및 새 동결 실행이 필요하다. 본 모듈은 자동 모델 실행이나 기존 결과 재채점을 수행하지 않는다.
