# 독립 GOLD 검수 18문항

검수자는 사용자가 선정했다고 확인했습니다. 이 패키지는 빈 양식이며 검수 완료·승인이 아닙니다.
A와 B는 서로의 판단과 모델 출력을 보지 않고 원문 질의와 출처부터 확인합니다. AI 후보는 별도 파일이며 초기 독립 판단을 기록한 뒤 대조하십시오.
초기 판단 양식은 원천 전체의 경로·해시·판만 제공합니다. 특정 객체별 locator와 AI 정답 선택은 별도 후보 파일에만 있습니다. 초기 독립 답안 작성과 기존 AI 후보의 사후 검증을 구분해 기록하십시오.
동등표현 Q4 세 문항은 같은 공간조건 군집입니다. 미확정 공간 범위·AOI·원천 coverage는 임의 정답으로 채우지 말고 미확정 사유를 기록합니다.
A/B JSONL에 검수자·일시·독립성·필수작업·허용답안·근거·clarification 필요성을 작성하고, 합의 파일에 불일치와 해결 근거를 남깁니다.
기존 파일의 human_approval을 자동 True로 바꾸지 않습니다. 제출본은 원본 hash와 함께 새 참조 버전으로 반영하고 이전 AI 참조를 보존합니다.
이 18문항은 이미 개발에 사용했습니다. 독립 검수 후에도 미노출 holdout으로 표시하지 않습니다.

## 질문 목록

1. **PILOT_Q1_01** — 등대의 S-101 객체 유형과 정의를 알려줘.
2. **PILOT_Q1_02** — S-101에서 정박지는 어떤 객체야?
3. **PILOT_Q1_03** — What is a wreck in S-101?
4. **PILOT_Q2_01** — S-101 등대의 색상 속성과 허용 값을 알려줘.
5. **PILOT_Q2_02** — 제한구역의 제한 종류는 어떤 코드로 표현해?
6. **PILOT_Q2_03** — Which attributes describe a Wreck in S-101?
7. **PILOT_Q3_01** — 독도 부근에서 가장 가까운 등대를 찾아줘.
8. **PILOT_Q3_02** — 부산항 영역 안의 정박지를 찾아줘.
9. **PILOT_Q3_03** — Find wrecks intersecting the selected area.
10. **PILOT_Q4_01** — 독도 주변 반경 5km의 해양지명을 찾아줘.
11. **PILOT_Q4_02** — 독도 주변 반경 5000m의 해양지명을 찾아줘.
12. **PILOT_Q4_03** — Find marine place names within 5 km of Dokdo.
13. **PILOT_Q5_01** — 독도 주변 5km의 등대와 난파선을 찾아 각각의 근거를 알려줘.
14. **PILOT_Q5_02** — 부산항 주변 2km의 정박지와 제한구역을 찾아 비교해줘.
15. **PILOT_Q5_03** — Find wrecks within 5 km of Dokdo and explain their S-101 attributes.
16. **PILOT_Q6_01** — S-101 Wreck 정의의 원문과 Feature Catalogue 출처를 알려줘.
17. **PILOT_Q6_02** — 등대와 부표를 구분하는 S-101 근거를 알려줘.
18. **PILOT_Q6_03** — What source supports the S-101 definition of AnchorageArea?
