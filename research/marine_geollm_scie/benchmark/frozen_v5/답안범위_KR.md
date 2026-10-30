# 사용자 지시 아래 확정한 답안 범위 v5

상태: AGENT_FINALIZED_UNDER_USER_DIRECTION. 독립 인간 검수 아님. v3 사용자 승인 원문과 v4 초안은 보존한다. 단일 intent 일치를 정답으로 사용하지 않는다.

| 사례 | 질의 | 문서 범위 | 공간 평가 범위 | 필수 작업 수 |
|---|---|---|---|---|
| PILOT_Q1_01 | 등대의 S-101 객체 유형과 정의를 알려줘. | Landmark, Building, LightAllAround, LightSectored | 비공간 | 2 |
| PILOT_Q1_02 | S-101에서 정박지는 어떤 객체야? | AnchorageArea | 비공간 | 1 |
| PILOT_Q1_03 | What is a wreck in S-101? | Wreck | 비공간 | 1 |
| PILOT_Q2_01 | S-101 등대의 색상 속성과 허용 값을 알려줘. | Landmark, Building, LightAllAround, LightSectored | 비공간 | 2 |
| PILOT_Q2_02 | 제한구역의 제한 종류는 어떤 코드로 표현해? | RestrictedArea | 비공간 | 2 |
| PILOT_Q2_03 | Which attributes describe a Wreck in S-101? | Wreck | 비공간 | 1 |
| PILOT_Q3_01 | 독도 부근에서 가장 가까운 등대를 찾아줘. | 개별 과업 상태와 가용 근거 | REFERENCE_GEOMETRY_OR_COVERAGE_UNVERIFIED | 5 |
| PILOT_Q3_02 | 부산항 영역 안의 정박지를 찾아줘. | 개별 과업 상태와 가용 근거 | REFERENCE_GEOMETRY_OR_COVERAGE_UNVERIFIED | 4 |
| PILOT_Q3_03 | Find wrecks intersecting the selected area. | 개별 과업 상태와 가용 근거 | SELECTED_AOI_NOT_SUPPLIED | 4 |
| PILOT_Q4_01 | 독도 주변 반경 5km의 해양지명을 찾아줘. | 개별 과업 상태와 가용 근거 | FIXED_USER_APPROVED_Q4_REFERENCE | 3 |
| PILOT_Q4_02 | 독도 주변 반경 5000m의 해양지명을 찾아줘. | 개별 과업 상태와 가용 근거 | FIXED_USER_APPROVED_Q4_REFERENCE | 3 |
| PILOT_Q4_03 | Find marine place names within 5 km of Dokdo. | 개별 과업 상태와 가용 근거 | FIXED_USER_APPROVED_Q4_REFERENCE | 3 |
| PILOT_Q5_01 | 독도 주변 5km의 등대와 난파선을 찾아 각각의 근거를 알려줘. | Landmark, Building, LightAllAround, LightSectored, Wreck | REFERENCE_GEOMETRY_OR_COVERAGE_UNVERIFIED | 6 |
| PILOT_Q5_02 | 부산항 주변 2km의 정박지와 제한구역을 찾아 비교해줘. | AnchorageArea, RestrictedArea | REFERENCE_GEOMETRY_OR_COVERAGE_UNVERIFIED | 5 |
| PILOT_Q5_03 | Find wrecks within 5 km of Dokdo and explain their S-101 attributes. | Wreck | REFERENCE_GEOMETRY_OR_COVERAGE_UNVERIFIED | 6 |
| PILOT_Q6_01 | S-101 Wreck 정의의 원문과 Feature Catalogue 출처를 알려줘. | Wreck | 비공간 | 2 |
| PILOT_Q6_02 | 등대와 부표를 구분하는 S-101 근거를 알려줘. | Landmark, Building, LightAllAround, LightSectored, LateralBuoy | 비공간 | 2 |
| PILOT_Q6_03 | What source supports the S-101 definition of AnchorageArea? | AnchorageArea | 비공간 | 2 |

정의: code·정의·허용기하, 속성: FC 직접 binding/명시 경로·다중도·binding 허용값, 인용: edition·원문 hash·locator. 설명의 존재와 의미 정확도를 구분한다. Q4만 실제 ID 정확도, Q3_03은 AOI 확인, 그 외 공간 질의는 미검증 조건 고지·검증 행동을 평가한다.

LateralBuoy는 부표 전체를 대신하는 완전 분류가 아니라 비교용 대표 Feature로 명시했다. 등대 구조/등화 후보의 설명 요구는 모든 유형이 한 시설에 존재해야 한다는 의미가 아니다. Q5는 공간 결과와 설명/비교/근거 과업의 상태를 각각 내야 한다.
