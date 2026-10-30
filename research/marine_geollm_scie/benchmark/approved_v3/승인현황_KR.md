# 18개 사용자 승인 참조 현황

**18개 모두 사용자 승인 완료(GOLD·human_approval=true)**입니다. 승인 유형은 **사용자 승인 AI 보조 검토**이며 독립 전문가 2인의 검수나 미노출 holdout은 아닙니다. 문서 승인과 자동 채점에 필요한 정답 데이터의 완성 여부를 아래에서 구분합니다.

전체 합의 서술·원문·미확정 조건은 evaluation_references.jsonl에 그대로 보존했습니다. 의미 후보를 정답집합으로 확장하거나 미관측 공간 ID를 생성하지 않았습니다.

| 사례 ID | 사용자 질의 | 사용자 승인 | 의미 자동평가 | QEC 부분평가에 전사된 값 | 공간 정답 ID와 이유 |
|---|---|---|---|---|---|
| PILOT_Q1_01 | 등대의 S-101 객체 유형과 정의를 알려줘. | 승인 완료 | 미측정: 합의 서술 유지; 필수 완전 label집합 미확정 | 서술형 계약 보존; 확정 scalar 필드 없음 | 대상 아님: 정의·속성·표준근거 설명 질의. |
| PILOT_Q1_02 | S-101에서 정박지는 어떤 객체야? | 승인 완료 | 미측정: 합의 서술 유지; 필수 완전 label집합 미확정 | 서술형 계약 보존; 확정 scalar 필드 없음 | 대상 아님: 정의·속성·표준근거 설명 질의. |
| PILOT_Q1_03 | What is a wreck in S-101? | 승인 완료 | 미측정: 합의 서술 유지; 필수 완전 label집합 미확정 | 서술형 계약 보존; 확정 scalar 필드 없음 | 대상 아님: 정의·속성·표준근거 설명 질의. |
| PILOT_Q2_01 | S-101 등대의 색상 속성과 허용 값을 알려줘. | 승인 완료 | 미측정: 합의 서술 유지; 필수 완전 label집합 미확정 | 서술형 계약 보존; 확정 scalar 필드 없음 | 대상 아님: 정의·속성·표준근거 설명 질의. |
| PILOT_Q2_02 | 제한구역의 제한 종류는 어떤 코드로 표현해? | 승인 완료 | 미측정: 합의 서술 유지; 필수 완전 label집합 미확정 | 서술형 계약 보존; 확정 scalar 필드 없음 | 대상 아님: 정의·속성·표준근거 설명 질의. |
| PILOT_Q2_03 | Which attributes describe a Wreck in S-101? | 승인 완료 | 미측정: 합의 서술 유지; 필수 완전 label집합 미확정 | 서술형 계약 보존; 확정 scalar 필드 없음 | 대상 아님: 정의·속성·표준근거 설명 질의. |
| PILOT_Q3_01 | 독도 부근에서 가장 가까운 등대를 찾아줘. | 승인 완료 | 미측정: 합의 서술 유지; 필수 완전 label집합 미확정 | slots.location_text=독도 | 미확정(null): 등대 대상범위·시설 동일성·자료 coverage 검증 필요. |
| PILOT_Q3_02 | 부산항 영역 안의 정박지를 찾아줘. | 승인 완료 | 미측정: 합의 서술 유지; 필수 완전 label집합 미확정 | slots.location_text=부산항 | 미확정(null): 부산항 영역 geometry와 정박지 source binding 필요. |
| PILOT_Q3_03 | Find wrecks intersecting the selected area. | 승인 완료 | 미측정: 합의 서술 유지; 필수 완전 label집합 미확정 | 서술형 계약 보존; 확정 scalar 필드 없음 | 미확정(null): 선택 영역 없음. 기대 행동 NEEDS_USER_INPUT. |
| PILOT_Q4_01 | 독도 주변 반경 5km의 해양지명을 찾아줘. | 승인 완료 | 미측정: 합의 서술 유지; 필수 완전 label집합 미확정 | slots.location_text=독도; slots.distance_m=5000 | 확보: 동일 원본 ID44–54, 11개. 승인된 동도 기준점·2022 CSV·5km로 검산. |
| PILOT_Q4_02 | 독도 주변 반경 5000m의 해양지명을 찾아줘. | 승인 완료 | 미측정: 합의 서술 유지; 필수 완전 label집합 미확정 | slots.location_text=독도; slots.distance_m=5000 | 확보: 동일 원본 ID44–54, 11개. 승인된 동도 기준점·2022 CSV·5km로 검산. |
| PILOT_Q4_03 | Find marine place names within 5 km of Dokdo. | 승인 완료 | 미측정: 합의 서술 유지; 필수 완전 label집합 미확정 | slots.location_text=독도; slots.distance_m=5000 | 확보: 동일 원본 ID44–54, 11개. 승인된 동도 기준점·2022 CSV·5km로 검산. |
| PILOT_Q5_01 | 독도 주변 5km의 등대와 난파선을 찾아 각각의 근거를 알려줘. | 승인 완료 | 미측정: 합의 서술 유지; 필수 완전 label집합 미확정 | slots.location_text=독도; slots.distance_m=5000 | 미확정(null): 독도 등대/난파선의 검증된 source coverage 및 객체집합 없음. |
| PILOT_Q5_02 | 부산항 주변 2km의 정박지와 제한구역을 찾아 비교해줘. | 승인 완료 | 미측정: 합의 서술 유지; 필수 완전 label집합 미확정 | slots.location_text=부산항; slots.distance_m=2000 | 미확정(null): 항만 거리 기준 geometry와 두 객체 원천 coverage 미확정. |
| PILOT_Q5_03 | Find wrecks within 5 km of Dokdo and explain their S-101 attributes. | 승인 완료 | 미측정: 합의 서술 유지; 필수 완전 label집합 미확정 | slots.location_text=독도; slots.distance_m=5000 | 미확정(null): 독도 등대/난파선의 검증된 source coverage 및 객체집합 없음. |
| PILOT_Q6_01 | S-101 Wreck 정의의 원문과 Feature Catalogue 출처를 알려줘. | 승인 완료 | 미측정: 합의 서술 유지; 필수 완전 label집합 미확정 | 서술형 계약 보존; 확정 scalar 필드 없음 | 대상 아님: 정의·속성·표준근거 설명 질의. |
| PILOT_Q6_02 | 등대와 부표를 구분하는 S-101 근거를 알려줘. | 승인 완료 | 미측정: 합의 서술 유지; 필수 완전 label집합 미확정 | 서술형 계약 보존; 확정 scalar 필드 없음 | 대상 아님: 정의·속성·표준근거 설명 질의. |
| PILOT_Q6_03 | What source supports the S-101 definition of AnchorageArea? | 승인 완료 | 미측정: 합의 서술 유지; 필수 완전 label집합 미확정 | 서술형 계약 보존; 확정 scalar 필드 없음 | 대상 아님: 정의·속성·표준근거 설명 질의. |

## 현재 자동평가 가능한 범위

- 의미: 18건의 설명은 승인됐으나 semantics.labels는 null입니다. 조건부 Feature 후보를 필수 정답집합으로 바꾸지 않아 의미 정확도는 자동 산출하지 않습니다.
- QEC: 8건에 위치·거리의 명시적 scalar 값을 전사했습니다. 부분 슬롯 일치만 평가하며 전체 계획 타당성으로 확대하지 않습니다.
- 공간: Q4 세 표현에 같은 실제 원본 ID11개를 넣었습니다. 같은 source snapshot에서 수행한 실제 실행 결과만 이 정답과 비교할 수 있습니다. 세 표현은 하나의 동등표현 그룹입니다.
- 근거: 원문 근거는 승인·보존됐지만 강제 필수 참조집합(required_refs)은 null입니다. 인용 존재만으로 주장 지지나 evidence correctness를 승인한 것은 아닙니다.
- 공간정답 없이 실행이 끝났다고 정확한 공간결과로 세지 않습니다. 원천·coverage·선택영역 부족은 null을 유지합니다.

Q4 실제 지명·거리·원천 검산: [독도 공간 참조 설명](../../protocol/dokdo_spatial_reference_v3_KR.md). 원본 정답 ID는 S-101 Feature ID가 아니라 2022 해양지명 CSV ID입니다.

## 독립 재확인

18개 승인 상태, 원본 v2 참조 해시, 지정 A/B/합의 XLSX 해시, Q4 oracle 해시, 승인 후 audit의 참조 해시·사례 수를 다시 확인했습니다. 정답 JSONL과 승인 manifest는 변경하지 않았습니다.

생성기 보존 사본은 Windows CRLF 때문에 manifest의 생성 당시 LF 코드 해시와 달랐습니다. 사본만 원래 LF bytes로 복원하여 기존 code_sha256와 일치시켰습니다. 과학적 참조값·승인 내용 변경은 없습니다. 전후 해시와 검증 기록은 independent_verification_v3.json에 있습니다.

참조 JSONL SHA256: `a69cda7558eca74c8d869de6fc80653c51541ab2cc4a7cb628e3fd065b27558c`. 사용자 승인 AI 보조18건, 독립 전문가0건, QEC부분8건, 공간정답3건입니다. 모델 prompt에 정답을 넣거나 신규 XLSX를 만들지 않았습니다.
