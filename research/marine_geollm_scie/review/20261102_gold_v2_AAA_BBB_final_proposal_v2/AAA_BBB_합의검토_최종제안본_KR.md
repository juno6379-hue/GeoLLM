# AAA·BBB 합의검토 최종 제안본

**문서 작성 완료 · AI 보조 검토 · 실제 인간 합의/승인 대기**

- 검수자 A 표시명: **AAA** / 검수자 B 표시명: **BBB** (사용자 지정).
- AAA란은 제공된 AI 보조 작성본을 연결한다. BBB란은 기존 AI 반례·근거 검토를 연결한다. BBB가 직접 작성한 별도 검수 기록은 제공되지 않았다.
- 첨부의 “승인/조건부 승인”은 AI 초안의 판단 표현이며 AAA·BBB의 서명·인간 승인으로 승격하지 않는다.
- 최종은 문서 편집본의 상태다. `human_approval=false`, `independent_human_review_complete=false`. 이름 지정만으로 검수 완료를 의미하지 않는다.
- 기존 GOLD v2·실험 결과·평가 점수는 변경하지 않았다. 검토 후 변경은 별도 GOLD 버전으로 관리한다.

첨부 원본: [첨부원본_AI보조검수_A.md](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261102_gold_v2_AAA_BBB_final_proposal_v2/첨부원본_AI보조검수_A.md>) · SHA256 `de75d5208007125f74393a2be559708b370f58541e05bdeaa1ac686b07119d56`
기준 GOLD: [manifest.json](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/manifest.json>) · SHA256 `feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c`
근거 상세: [사례별_원본근거_객체ID_거리_해시_최종_KR.md](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261102_gold_v2_AAA_BBB_final_proposal_v2/사례별_원본근거_객체ID_거리_해시_최종_KR.md>)

## 18사례 제안 요약

| 사례 | AAA 연결 초안 | 최종 제안 상태 |
|---|---|---|
| PILOT_Q1_01 | 조건부 승인(AI) | 조건 유지·사람 확인 대기 |
| PILOT_Q1_02 | 승인(AI) | 기준 유지 제안·사람 확인 대기 |
| PILOT_Q1_03 | 승인(AI) | 기준 유지 제안·사람 확인 대기 |
| PILOT_Q2_01 | 승인(AI) | 기준 유지 제안·사람 확인 대기 |
| PILOT_Q2_02 | 승인(AI) | 기준 유지 제안·사람 확인 대기 |
| PILOT_Q2_03 | 승인(AI) | 기준 유지 제안·사람 확인 대기 |
| PILOT_Q3_01 | 승인(AI) | 기준 유지 제안·사람 확인 대기 |
| PILOT_Q3_02 | 조건부 승인(AI) | 조건 유지·사람 확인 대기 |
| PILOT_Q3_03 | 승인(AI) | 기준 유지 제안·사람 확인 대기 |
| PILOT_Q4_01 | 승인(AI) | 기준 유지 제안·사람 확인 대기 |
| PILOT_Q4_02 | 승인(AI) | 기준 유지 제안·사람 확인 대기 |
| PILOT_Q4_03 | 승인(AI) | 기준 유지 제안·사람 확인 대기 |
| PILOT_Q5_01 | 승인(AI) | 기준 유지 제안·사람 확인 대기 |
| PILOT_Q5_02 | 조건부 승인(AI) | 조건 유지·사람 확인 대기 |
| PILOT_Q5_03 | 승인(AI) | 기준 유지 제안·사람 확인 대기 |
| PILOT_Q6_01 | 승인(AI) | 기준 유지 제안·사람 확인 대기 |
| PILOT_Q6_02 | 조건부 승인(AI) | 조건 유지·사람 확인 대기 |
| PILOT_Q6_03 | 승인(AI) | 기준 유지 제안·사람 확인 대기 |

## PILOT_Q1_01 — 등대의 S-101 객체 유형과 정의를 알려줘.

**AAA 담당란 — 첨부 AI 보조 의견:** 조건부 승인. '등대=Lighthouse 단일 Feature'가 아니라 구조물/등화의 조건부 조합으로 설명하는 현재 기준이 FC 구조와 부합한다.

- 허용 답안: Landmark/Building은 구조물 후보, LightAllAround/LightSectored는 등화 후보로 조건부 설명. 네 Feature가 하나의 실재 등대에 모두 존재한다고 단정하는 답은 불허.
- 필수 근거: S-101 Feature Catalogue 2.0.0의 Landmark, Building, LightAllAround, LightSectored 정의 및 geometry binding.
**BBB 담당란 — AI 대조 검토 제안:** 네 코드를 모두 한 시설의 필수 구성으로 요구해서는 안 된다. 설명을 위한 대안 목록과 실제 객체 매핑을 구분한다.

**합의안 제안:** 등대를 단일 Lighthouse 코드로 단정하지 않고 구조물 Landmark/Building과 등화 LightAllAround/LightSectored의 조건부 모델을 구분한다.
- 제안 상태: 조건 유지·사람 확인 대기. 실제 두 검수자의 일치/불일치는 아직 기록되지 않음.
- 추가 입력: 불필요.
- 공간 정답/미확정: 해당 없음(정의/의미 질의).
- 재현 근거: [PILOT_Q1_01 근거](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261102_gold_v2_AAA_BBB_final_proposal_v2/사례별_원본근거_객체ID_거리_해시_최종_KR.md>) 해당 절. GOLD JSONL 1행.
- AAA 최종 의견·서명·일시: ____________________
- BBB 최종 의견·서명·일시: ____________________
- 합의 판단(수용/수정/보류)·수정 근거·합의일: ____________________

## PILOT_Q1_02 — S-101에서 정박지는 어떤 객체야?

**AAA 담당란 — 첨부 AI 보조 의견:** 승인. 현재 FC 정의와 feature mapping이 직접 일치한다.

- 허용 답안: AnchorageArea. '선박 또는 수상기가 정박하거나 정박할 수 있는 구역'이라는 출처 동등 번역/의역 허용.
- 필수 근거: S-101 FC 2.0.0 AnchorageArea 정의, permitted primitives point/surface.
**BBB 담당란 — AI 대조 검토 제안:** 일반 정박 행위와 데이터 객체의 존재를 혼동하지 않는다. 정의 질의에는 공간 실행이 필요하지 않다.

**합의안 제안:** 정박지는 AnchorageArea로 설명하고 FC 정의·point/surface 허용 geometry와 출처를 연결한다.
- 제안 상태: 기준 유지 제안·사람 확인 대기. 실제 두 검수자의 일치/불일치는 아직 기록되지 않음.
- 추가 입력: 불필요.
- 공간 정답/미확정: 해당 없음.
- 재현 근거: [PILOT_Q1_02 근거](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261102_gold_v2_AAA_BBB_final_proposal_v2/사례별_원본근거_객체ID_거리_해시_최종_KR.md>) 해당 절. GOLD JSONL 2행.
- AAA 최종 의견·서명·일시: ____________________
- BBB 최종 의견·서명·일시: ____________________
- 합의 판단(수용/수정/보류)·수정 근거·합의일: ____________________

## PILOT_Q1_03 — What is a wreck in S-101?

**AAA 담당란 — 첨부 AI 보조 의견:** 승인. FC의 Wreck 정의와 직접 부합한다.

- 허용 답안: Wreck = 좌초 또는 침몰한 선박의 파손 잔해로 사용 불능이 된 것이라는 출처 동등 번역 허용.
- 필수 근거: S-101 FC 2.0.0 Wreck 정의, permitted primitives point/surface.
**BBB 담당란 — AI 대조 검토 제안:** 침선 개념 설명을 실제 침선 위치 검색으로 바꾸지 않는다. 원문과 동등한 의역도 의미 검수 대상이다.

**합의안 제안:** Wreck의 정의와 point/surface 표현을 FC 근거로 설명한다.
- 제안 상태: 기준 유지 제안·사람 확인 대기. 실제 두 검수자의 일치/불일치는 아직 기록되지 않음.
- 추가 입력: 불필요.
- 공간 정답/미확정: 해당 없음.
- 재현 근거: [PILOT_Q1_03 근거](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261102_gold_v2_AAA_BBB_final_proposal_v2/사례별_원본근거_객체ID_거리_해시_최종_KR.md>) 해당 절. GOLD JSONL 3행.
- AAA 최종 의견·서명·일시: ____________________
- BBB 최종 의견·서명·일시: ____________________
- 합의 판단(수용/수정/보류)·수정 근거·합의일: ____________________

## PILOT_Q2_01 — S-101 등대의 색상 속성과 허용 값을 알려줘.

**AAA 담당란 — 첨부 AI 보조 의견:** 승인. 전역 colour 코드와 Feature binding 허용값을 구분하는 현재 기준이 타당하다.

- 허용 답안: Landmark/Building colour=1~13. LightAllAround colour=1,3,4,5,6,9,10,11. LightSectored는 sectorCharacteristics→lightSector→colour 경로에서 1,3,4,5,6,9,10,11. 하나의 통합 색상목록으로 단순화하면 불허.
- 필수 근거: S-101 FC 2.0.0의 각 Feature binding과 colour simple attribute, LightSectored의 sectorCharacteristics/lightSector complex path.
**BBB 담당란 — AI 대조 검토 제안:** LightSectored→sectorCharacteristics→lightSector→colour 경로를 확인한다. 전역 colour 코드 목록을 모든 Feature의 허용값으로 복사하지 않는다.

**합의안 제안:** 구조물 colour와 등화 colour를 구분한다. Landmark/Building은 1~13, LightAllAround와 lightSector는 FC에 연결된 1,3,4,5,6,9,10,11을 제시한다.
- 제안 상태: 기준 유지 제안·사람 확인 대기. 실제 두 검수자의 일치/불일치는 아직 기록되지 않음.
- 추가 입력: 불필요.
- 공간 정답/미확정: 해당 없음.
- 재현 근거: [PILOT_Q2_01 근거](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261102_gold_v2_AAA_BBB_final_proposal_v2/사례별_원본근거_객체ID_거리_해시_최종_KR.md>) 해당 절. GOLD JSONL 4행.
- AAA 최종 의견·서명·일시: ____________________
- BBB 최종 의견·서명·일시: ____________________
- 합의 판단(수용/수정/보류)·수정 근거·합의일: ____________________

## PILOT_Q2_02 — 제한구역의 제한 종류는 어떤 코드로 표현해?

**AAA 담당란 — 첨부 AI 보조 의견:** 승인. 질의의 '제한 종류'는 restriction을 중심으로 답하되 categoryOfRestrictedArea와 혼동하지 않도록 둘을 분리하는 기준이 적절하다.

- 허용 답안: 실제 제한 행위는 restriction(허용 1~27의 지정값 및 39,42), 구역의 종류/법적 성격은 categoryOfRestrictedArea(1,4,5,6,7,8,9,10,12,14,18~25,27~32). 두 code list를 서로 치환하지 않는 설명.
- 필수 근거: S-101 FC 2.0.0 RestrictedArea Feature binding, restriction 및 categoryOfRestrictedArea 정의/허용값.
**BBB 담당란 — AI 대조 검토 제안:** 구역 종류 코드와 실제 제한 행위 코드는 다른 속성이다. 공개 FC 설명을 실제 구역의 법적 허가 또는 비공개 자료 요청으로 해석하지 않는다.

**합의안 제안:** RestrictedArea의 restriction과 categoryOfRestrictedArea를 구분하여 Feature별 연결·다중성·허용 코드를 설명한다.
- 제안 상태: 기준 유지 제안·사람 확인 대기. 실제 두 검수자의 일치/불일치는 아직 기록되지 않음.
- 추가 입력: 불필요.
- 공간 정답/미확정: 해당 없음.
- 재현 근거: [PILOT_Q2_02 근거](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261102_gold_v2_AAA_BBB_final_proposal_v2/사례별_원본근거_객체ID_거리_해시_최종_KR.md>) 해당 절. GOLD JSONL 5행.
- AAA 최종 의견·서명·일시: ____________________
- BBB 최종 의견·서명·일시: ____________________
- 합의 판단(수용/수정/보류)·수정 근거·합의일: ____________________

## PILOT_Q2_03 — Which attributes describe a Wreck in S-101?

**AAA 담당란 — 첨부 AI 보조 의견:** 승인. 현재 frozen_v5의 FC direct binding 목록과 일치한다.

- 허용 답안: Wreck direct attributes: categoryOfWreck, expositionOfSounding, featureName, height, interoperabilityIdentifier, qualityOfVerticalMeasurement, radarConspicuous, reportedDate, status, techniqueOfVerticalMeasurement, valueOfSounding, visualProminence, waterLevelEffect, scaleMinimum, information, pictorialRepresentation, defaultClearanceDepth, surroundingDepth. 복합속성은 구조를 유지해 설명.
- 필수 근거: S-101 FC 2.0.0 Wreck FeatureType 및 각 Simple/ComplexAttribute binding/locator.
**BBB 담당란 — AI 대조 검토 제안:** FC 속성 정의와 특정 침선의 실제 속성값은 별개다. 전역에 존재하는 속성을 Wreck에 연결된 것으로 추정하지 않는다.

**합의안 제안:** Wreck에 실제 연결된 속성 목록·정의·다중성·허용값을 제시한다. waterLevelEffect와 surroundingDepth의 필수 다중성을 확인한다.
- 제안 상태: 기준 유지 제안·사람 확인 대기. 실제 두 검수자의 일치/불일치는 아직 기록되지 않음.
- 추가 입력: 불필요.
- 공간 정답/미확정: 해당 없음.
- 재현 근거: [PILOT_Q2_03 근거](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261102_gold_v2_AAA_BBB_final_proposal_v2/사례별_원본근거_객체ID_거리_해시_최종_KR.md>) 해당 절. GOLD JSONL 6행.
- AAA 최종 의견·서명·일시: ____________________
- BBB 최종 의견·서명·일시: ____________________
- 합의 판단(수용/수정/보류)·수정 근거·합의일: ____________________

## PILOT_Q3_01 — 독도 부근에서 가장 가까운 등대를 찾아줘.

**AAA 담당란 — 첨부 AI 보조 의견:** 승인. nearest를 1km 기본반경으로 바꾸지 않고 coverage 부족을 안전중단으로 처리하는 기준이 타당하다.

- 허용 답안: 현재 snapshot에서는 `DATA_OUT_OF_SCOPE` 또는 `BLOCKED_DATA`. '0건' 또는 부산청 자료에서 계산한 임의 최근접 등대를 실세계 정답으로 제시하는 것은 불허. 향후 in-scope 원천에서는 radius 없이 nearest/top-1 적용.
- 필수 근거: 부산지방해양수산청 항로표지 원천이 전국완전성을 보장하지 않으며 독도 coverage가 검증되지 않았다는 source scope; GOLD v2 comparison protocol.
**BBB 담당란 — AI 대조 검토 제안:** 전국 최근접 계산의 정답이나 실세계 0건으로 만들지 않는다. 단순 UNSUPPORTED_OPERATOR 차단은 올바른 coverage 판단 전체를 충족하지 않는다.

**합의안 제안:** 현재 부산권 snapshot으로 독도 최근접 등대를 확정할 수 없으므로 DATA_OUT_OF_SCOPE/BLOCKED_DATA와 원천 범위 부족을 설명한다. 공간 객체 GOLD는 없다.
- 제안 상태: 기준 유지 제안·사람 확인 대기. 실제 두 검수자의 일치/불일치는 아직 기록되지 않음.
- 추가 입력: 사용자 입력 문제가 아니라 in-scope/권위 있는 등대 원천이 필요함.
- 공간 정답/미확정: 공간 객체 GOLD 없음. 현재 항로표지 source의 독도 coverage가 검증되지 않아 실세계 최근접 등대를 확정할 수 없음.
- 재현 근거: [PILOT_Q3_01 근거](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261102_gold_v2_AAA_BBB_final_proposal_v2/사례별_원본근거_객체ID_거리_해시_최종_KR.md>) 해당 절. GOLD JSONL 7행.
- AAA 최종 의견·서명·일시: ____________________
- BBB 최종 의견·서명·일시: ____________________
- 합의 판단(수용/수정/보류)·수정 근거·합의일: ____________________

## PILOT_Q3_02 — 부산항 영역 안의 정박지를 찾아줘.

**AAA 담당란 — 첨부 AI 보조 의견:** 조건부 승인. 연구 재현성에는 충분하지만 법적 부산항 항계라고 표현하면 안 된다.

- 허용 답안: 현재 연구 기준 객체 1137770(101KR00658D00.000)에 대해 ST_Covers를 적용한 source-bound 결과만 정답으로 사용. 이를 '부산항 전체 실세계 정박지'로 일반화하지 않음.
- 필수 근거: canonical_busan_boundary.json, research snapshot object 1137770, CRS EPSG:4326, GOLD v2 oracle의 ST_Covers 검산.
**BBB 담당란 — AI 대조 검토 제안:** 유효한 빈 Oracle과 미실행/누락은 다르다. 이 polygon은 연구용 고정 경계이며 법적 항계 전체와 동일하다고 단정하지 않는다.

**합의안 제안:** 고정 부산항 polygon과 ST_Covers(reference,target)를 사용한 snapshot 내 AnchorageArea 정답은 빈 집합이다. 원천·범위와 검사 조건을 함께 공개한다.
- 제안 상태: 조건 유지·사람 확인 대기. 실제 두 검수자의 일치/불일치는 아직 기록되지 않음.
- 추가 입력: benchmark에서는 불필요. 실제 프로그램에서는 법적/운영 항계 정책이 별도 필요.
- 공간 정답/미확정: 고정 polygon 1137770에 대한 ST_Covers 기준 결과는 0개. 이는 해당 benchmark polygon 기준 0개일 뿐 부산항 전체에 정박지가 없다는 뜻이 아님.
- 재현 근거: [PILOT_Q3_02 근거](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261102_gold_v2_AAA_BBB_final_proposal_v2/사례별_원본근거_객체ID_거리_해시_최종_KR.md>) 해당 절. GOLD JSONL 8행.
- AAA 최종 의견·서명·일시: ____________________
- BBB 최종 의견·서명·일시: ____________________
- 합의 판단(수용/수정/보류)·수정 근거·합의일: ____________________

## PILOT_Q3_03 — Find wrecks intersecting the selected area.

**AAA 담당란 — 첨부 AI 보조 의견:** 승인. missing input과 공간 0건을 구분하는 기준이 명확하다.

- 허용 답안: `NEEDS_USER_INPUT`, blocker=`MISSING_REFERENCE_GEOMETRY`, execution_attempted=false. 임의 viewport/AOI 생성 불허.
- 필수 근거: GOLD v2 comparison protocol의 semantic_gold(Wreck/intersects), qec_gold(selected_geometry=REQUIRED), execution_gold(execution_attempted=false).
**BBB 담당란 — AI 대조 검토 제안:** 임의 viewport나 기준점으로 대체하지 않는다. 안내 문구만으로 미실행을 인정하지 말고 실행 로그를 확인한다.

**합의안 제안:** 선택 영역이 없으므로 NEEDS_USER_INPUT, MISSING_REFERENCE_GEOMETRY를 반환하고 execution_attempted/started/tool_called/sql_executed=false여야 한다.
- 제안 상태: 기준 유지 제안·사람 확인 대기. 실제 두 검수자의 일치/불일치는 아직 기록되지 않음.
- 추가 입력: 필요. 사용자가 선택한 AOI geometry.
- 공간 정답/미확정: selected area가 제공되지 않아 object set GOLD를 만들지 않음.
- 재현 근거: [PILOT_Q3_03 근거](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261102_gold_v2_AAA_BBB_final_proposal_v2/사례별_원본근거_객체ID_거리_해시_최종_KR.md>) 해당 절. GOLD JSONL 9행.
- AAA 최종 의견·서명·일시: ____________________
- BBB 최종 의견·서명·일시: ____________________
- 합의 판단(수용/수정/보류)·수정 근거·합의일: ____________________

## PILOT_Q4_01 — 독도 주변 반경 5km의 해양지명을 찾아줘.

**AAA 담당란 — 첨부 AI 보조 의견:** 승인. PostGIS/Vincenty membership 검산과 source-bound scope가 명시돼 있다.

- 허용 답안: 정확한 11개 ID 집합: mof_marine_names_20221231:44~54. 이름: 북향초, 가지초, 강치초, 가제초, 삼봉초, 괭이초, 서도초, 군함초, 넙덕초, 부채초, 동도초. 순서는 본질적이지 않음.
- 필수 근거: dataset snapshot SHA256 bbc3f1c347f6048b0befdf5102959078ffc29c22cdc4412a98586e76cddb0464, oracle SHA256 cf7e407ec904661093a187e15391b42bc668a6e6ef5f75ead3f96c3f495cb9fb, 동도 기준점, WGS84 geodesic <=5000m.
**BBB 담당란 — AI 대조 검토 제안:** 원천 corpus의 정답이며 독도 주변 실세계 지명의 완전목록이 아니다. S-101 ID와 CSV 원본 ID를 혼용하지 않는다.

**합의안 제안:** 승인 동도 기준점·2022 CSV·WGS84 지오데식 거리 5000m 이하로 고정한다. 원본 ID 44~54의 11개 지명을 반환하고 출처를 연결한다.
- 제안 상태: 기준 유지 제안·사람 확인 대기. 실제 두 검수자의 일치/불일치는 아직 기록되지 않음.
- 추가 입력: 불필요.
- 공간 정답/미확정: 11개 source-bound set 확정. 실세계 전체 해양지명이나 S-101 Feature ID 집합을 의미하지 않음.
- 재현 근거: [PILOT_Q4_01 근거](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261102_gold_v2_AAA_BBB_final_proposal_v2/사례별_원본근거_객체ID_거리_해시_최종_KR.md>) 해당 절. GOLD JSONL 10행.
- AAA 최종 의견·서명·일시: ____________________
- BBB 최종 의견·서명·일시: ____________________
- 합의 판단(수용/수정/보류)·수정 근거·합의일: ____________________

## PILOT_Q4_02 — 독도 주변 반경 5000m의 해양지명을 찾아줘.

**AAA 담당란 — 첨부 AI 보조 의견:** 승인. 5km와 5000m의 단위 등가성 검증 사례로 적절하다.

- 허용 답안: Q4-01과 동일한 11개 ID(mof_marine_names_20221231:44~54).
- 필수 근거: 동일 dataset snapshot/oracle, distance_m=5000, 동일 동도 anchor.
**BBB 담당란 — AI 대조 검토 제안:** 단위 변환은 허용되지만 반경·기준점·원천은 변경하지 않는다. 세 표현을 독립 공간 문제로 합산하지 않는다.

**합의안 제안:** 5000m를 Q4-01의 5km와 같은 조건으로 해석한다. 동일 기준점과 동일 11개 원본 ID 집합이 정답이다.
- 제안 상태: 기준 유지 제안·사람 확인 대기. 실제 두 검수자의 일치/불일치는 아직 기록되지 않음.
- 추가 입력: 불필요.
- 공간 정답/미확정: 11개 source-bound set 확정. Q4-01과 metamorphic equivalent.
- 재현 근거: [PILOT_Q4_02 근거](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261102_gold_v2_AAA_BBB_final_proposal_v2/사례별_원본근거_객체ID_거리_해시_최종_KR.md>) 해당 절. GOLD JSONL 11행.
- AAA 최종 의견·서명·일시: ____________________
- BBB 최종 의견·서명·일시: ____________________
- 합의 판단(수용/수정/보류)·수정 근거·합의일: ____________________

## PILOT_Q4_03 — Find marine place names within 5 km of Dokdo.

**AAA 담당란 — 첨부 AI 보조 의견:** 승인. 언어 표현 변화에 대한 동등성 검증으로 적절하다.

- 허용 답안: Q4-01/02와 동일한 11개 ID(mof_marine_names_20221231:44~54).
- 필수 근거: 동일 dataset snapshot/oracle, WGS84 geodesic <=5000m, 동일 reference geometry.
**BBB 담당란 — AI 대조 검토 제안:** 언어 차이만으로 공간 의미나 coverage를 바꾸지 않는다. 개발 노출된 동등 표현군이며 독립 holdout이 아니다.

**합의안 제안:** 영어 5 km 질의도 Q4-01·02와 같은 기준점·원천·11개 ID를 사용한다.
- 제안 상태: 기준 유지 제안·사람 확인 대기. 실제 두 검수자의 일치/불일치는 아직 기록되지 않음.
- 추가 입력: 불필요.
- 공간 정답/미확정: 11개 source-bound set 확정. 동일 equivalence group이므로 독립 공간문제 3개로 세지 않음.
- 재현 근거: [PILOT_Q4_03 근거](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261102_gold_v2_AAA_BBB_final_proposal_v2/사례별_원본근거_객체ID_거리_해시_최종_KR.md>) 해당 절. GOLD JSONL 12행.
- AAA 최종 의견·서명·일시: ____________________
- BBB 최종 의견·서명·일시: ____________________
- 합의 판단(수용/수정/보류)·수정 근거·합의일: ____________________

## PILOT_Q5_01 — 독도 주변 5km의 등대와 난파선을 찾아 각각의 근거를 알려줘.

**AAA 담당란 — 첨부 AI 보조 의견:** 승인. 복합질의의 partial/full success와 coverage를 분리하는 기준이 타당하다.

- 허용 답안: 현재 snapshot에서는 Lighthouse와 Wreck 공간 하위작업 모두 `BLOCKED_DATA/DATA_OUT_OF_SCOPE`. S-101 정의/근거 설명은 선택적 PARTIAL_RESPONSE 가능. 한쪽만 답하거나 빈 집합을 정답으로 제시하면 full success 아님.
- 필수 근거: navigation-aid source의 전국완전성 미검증, S-101 Wreck snapshot의 dokdo_coverage=false, GOLD v2 composite completion policy.
**BBB 담당란 — AI 대조 검토 제안:** 한 대상만 처리하고 전체 완료로 선언하거나 두 빈 집합을 실세계 부재로 제시하면 안 된다. 대상별 상태·근거가 필요하다.

**합의안 제안:** 독도 5km의 Lighthouse와 Wreck 두 공간 하위작업 모두 coverage 부족으로 BLOCKED_DATA다. 표준 정의는 별도 부분응답으로만 허용한다.
- 제안 상태: 기준 유지 제안·사람 확인 대기. 실제 두 검수자의 일치/불일치는 아직 기록되지 않음.
- 추가 입력: 사용자 입력보다 전국/독도 coverage가 검증된 원천이 필요.
- 공간 정답/미확정: 두 target 모두 spatial object GOLD=null. 자료 범위 밖이므로 실세계 0건으로 채점하지 않음.
- 재현 근거: [PILOT_Q5_01 근거](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261102_gold_v2_AAA_BBB_final_proposal_v2/사례별_원본근거_객체ID_거리_해시_최종_KR.md>) 해당 절. GOLD JSONL 13행.
- AAA 최종 의견·서명·일시: ____________________
- BBB 최종 의견·서명·일시: ____________________
- 합의 판단(수용/수정/보류)·수정 근거·합의일: ____________________

## PILOT_Q5_02 — 부산항 주변 2km의 정박지와 제한구역을 찾아 비교해줘.

**AAA 담당란 — 첨부 AI 보조 의견:** 조건부 승인. 공간 oracle은 명확하나 검수 양식의 spatial_source_condition=null은 최종 인간 검수 전에 현재 GOLD v2 기준으로 동기화하는 것이 바람직하다.

- 허용 답안: 현재 GOLD v2 oracle 기준 AnchorageArea 3개, RestrictedArea 21개. 비교에는 유형별 count, 최소/최대 거리, FC 정의 근거, source/reference coverage 공개가 포함돼야 함.
- 필수 근거: canonical boundary 1137770 / 101KR00658D00.000, EPSG:4326, ST_DWithin 및 ST_Distance≤2000 독립 대조, S-101 FC AnchorageArea/RestrictedArea 정의.
**BBB 담당란 — AI 대조 검토 제안:** 표현상 polygon 경계 거리와 ST_DWithin(polygon,target)의 내부거리 0은 다를 수 있다. 동결 계약의 실제 predicate를 우선 보존하고 사람이 의미를 확인한다. ID는 snapshot 기록이며 중복 시설 제거 결과가 아니다.

**합의안 제안:** 고정 부산항 polygon과 geometry 간 최소 지오데식 거리 2000m 이하인 AnchorageArea/RestrictedArea 객체 집합을 각각 반환하고 수·거리·정의·원천 범위를 비교한다.
- 제안 상태: 조건 유지·사람 확인 대기. 실제 두 검수자의 일치/불일치는 아직 기록되지 않음.
- 추가 입력: benchmark에서는 불필요. 운영에서는 authoritative harbour boundary policy가 별도 필요.
- 공간 정답/미확정: GOLD v2 oracle에서 2km source-bound 집합이 확정됨(정박지 3, 제한구역 21). 단 canonical polygon은 연구 snapshot 기준이며 법적 부산항 전체 경계로 일반화 금지.
- 재현 근거: [PILOT_Q5_02 근거](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261102_gold_v2_AAA_BBB_final_proposal_v2/사례별_원본근거_객체ID_거리_해시_최종_KR.md>) 해당 절. GOLD JSONL 14행.
- AAA 최종 의견·서명·일시: ____________________
- BBB 최종 의견·서명·일시: ____________________
- 합의 판단(수용/수정/보류)·수정 근거·합의일: ____________________

## PILOT_Q5_03 — Find wrecks within 5 km of Dokdo and explain their S-101 attributes.

**AAA 담당란 — 첨부 AI 보조 의견:** 승인. schema allowed attribute와 instance value를 분리하고 공간 block을 유지하는 기준이 타당하다.

- 허용 답안: 공간 부분은 `BLOCKED_DATA/DATA_OUT_OF_SCOPE`. 문서 부분은 Wreck의 FC attribute binding 설명을 PARTIAL_RESPONSE로 제공 가능. 독도 Wreck object value를 생성/추정하면 불허.
- 필수 근거: Wreck FC binding(categoryOfWreck 등 18개), S-101 FC 2.0.0 edition/hash/locator, S-101 spatial snapshot dokdo_coverage=false.
**BBB 담당란 — AI 대조 검토 제안:** FC 정의만으로 실제 Wreck 객체 속성값을 만들어서는 안 된다. 추후 in-scope 객체 과제는 object value↔FC definition 연결을 따로 평가해야 한다.

**합의안 제안:** 독도 Wreck 공간 부분은 BLOCKED_DATA, 실제 object attribute value는 확정하지 않는다. FC 속성 설명은 별도 문서 부분응답으로 가능하다.
- 제안 상태: 기준 유지 제안·사람 확인 대기. 실제 두 검수자의 일치/불일치는 아직 기록되지 않음.
- 추가 입력: 독도 coverage가 검증된 Wreck 원천 필요.
- 공간 정답/미확정: spatial object GOLD=null. 부산권 Wreck 172개를 독도 실세계 정답으로 사용할 수 없음.
- 재현 근거: [PILOT_Q5_03 근거](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261102_gold_v2_AAA_BBB_final_proposal_v2/사례별_원본근거_객체ID_거리_해시_최종_KR.md>) 해당 절. GOLD JSONL 15행.
- AAA 최종 의견·서명·일시: ____________________
- BBB 최종 의견·서명·일시: ____________________
- 합의 판단(수용/수정/보류)·수정 근거·합의일: ____________________

## PILOT_Q6_01 — S-101 Wreck 정의의 원문과 Feature Catalogue 출처를 알려줘.

**AAA 담당란 — 첨부 AI 보조 의견:** 승인. 원문 인용 요구와 source locator가 명확하다.

- 허용 답안: 원문은 정확히 `The ruined remains of a stranded or sunken vessel which has been rendered useless.` 번역은 보조 설명으로 추가 가능.
- 필수 근거: S-101 FC 2.0.0, source hash 2743d068..., Wreck FeatureType locator.
**BBB 담당란 — AI 대조 검토 제안:** 원문 인용 정확성과 의미 설명 정확도를 별도로 판단한다. 검색 문서 존재만으로 최종 답변에 인용됐다고 인정하지 않는다.

**합의안 제안:** Wreck 정의 원문과 FC 2.0.0 판·SHA256·Feature locator를 함께 제시한다.
- 제안 상태: 기준 유지 제안·사람 확인 대기. 실제 두 검수자의 일치/불일치는 아직 기록되지 않음.
- 추가 입력: 불필요.
- 공간 정답/미확정: 해당 없음.
- 재현 근거: [PILOT_Q6_01 근거](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261102_gold_v2_AAA_BBB_final_proposal_v2/사례별_원본근거_객체ID_거리_해시_최종_KR.md>) 해당 절. GOLD JSONL 16행.
- AAA 최종 의견·서명·일시: ____________________
- BBB 최종 의견·서명·일시: ____________________
- 합의 판단(수용/수정/보류)·수정 근거·합의일: ____________________

## PILOT_Q6_02 — 등대와 부표를 구분하는 S-101 근거를 알려줘.

**AAA 담당란 — 첨부 AI 보조 의견:** 조건부 승인. '부표 전체 분류'가 아니라 LateralBuoy 대표 비교라는 범위를 반드시 공개해야 한다.

- 허용 답안: 등대: Landmark/Building(구조물) + LightAllAround/LightSectored(등화)의 조건부 모델. 부표: LateralBuoy를 대표 floating aid로 비교 가능. LateralBuoy 하나가 모든 부표 종류를 포괄한다고 단정하면 불허.
- 필수 근거: S-101 FC 2.0.0의 Landmark, Building, LightAllAround, LightSectored, LateralBuoy 정의/locator.
**BBB 담당란 — AI 대조 검토 제안:** LateralBuoy는 부표 전체의 대체가 아닌 한정 대표다. 원질의의 일반 부표 비교를 이 한정 범위로 평가하는 것이 적절한지 사람이 확인해야 한다.

**합의안 제안:** 조건부 구조물/등화 모델과 대표 부유표지 LateralBuoy를 FC 정의로 비교한다.
- 제안 상태: 조건 유지·사람 확인 대기. 실제 두 검수자의 일치/불일치는 아직 기록되지 않음.
- 추가 입력: 불필요.
- 공간 정답/미확정: 해당 없음.
- 재현 근거: [PILOT_Q6_02 근거](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261102_gold_v2_AAA_BBB_final_proposal_v2/사례별_원본근거_객체ID_거리_해시_최종_KR.md>) 해당 절. GOLD JSONL 17행.
- AAA 최종 의견·서명·일시: ____________________
- BBB 최종 의견·서명·일시: ____________________
- 합의 판단(수용/수정/보류)·수정 근거·합의일: ____________________

## PILOT_Q6_03 — What source supports the S-101 definition of AnchorageArea?

**AAA 담당란 — 첨부 AI 보조 의견:** 승인. 질문이 요구한 source와 정의가 직접 연결된다.

- 허용 답안: S-101 Feature Catalogue 2.0.0의 AnchorageArea FeatureType이 출처이며, 정의는 `An area in which vessels or seaplanes anchor or may anchor.`
- 필수 근거: S-101 FC 2.0.0, source hash 2743d068..., AnchorageArea locator.
**BBB 담당란 — AI 대조 검토 제안:** 원천 제목만 제시하거나 모델의 일반 지식을 인용 근거로 대신하지 않는다. 실제 공간 검색은 요구되지 않는다.

**합의안 제안:** AnchorageArea 정의를 뒷받침하는 FC 2.0.0 원문·판·hash·locator를 연결한다.
- 제안 상태: 기준 유지 제안·사람 확인 대기. 실제 두 검수자의 일치/불일치는 아직 기록되지 않음.
- 추가 입력: 불필요.
- 공간 정답/미확정: 해당 없음.
- 재현 근거: [PILOT_Q6_03 근거](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261102_gold_v2_AAA_BBB_final_proposal_v2/사례별_원본근거_객체ID_거리_해시_최종_KR.md>) 해당 절. GOLD JSONL 18행.
- AAA 최종 의견·서명·일시: ____________________
- BBB 최종 의견·서명·일시: ____________________
- 합의 판단(수용/수정/보류)·수정 근거·합의일: ____________________
