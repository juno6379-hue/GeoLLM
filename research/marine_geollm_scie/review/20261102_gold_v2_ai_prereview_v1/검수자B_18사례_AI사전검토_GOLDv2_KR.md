# 검수자B — GOLD v2 18사례 AI 사전검토본

**AI 작성 · 사용자 검토 대기 · 독립 인간 검수 미완료**

A/B는 동일 AI의 서로 다른 검토 관점입니다. 두 명의 독립 검수 또는 실제 합의를 수행했다고 주장하지 않습니다. 기존 GOLD를 제안 근거로 노출하므로 이를 읽은 후의 검토는 AI 보조 검수로 기록하십시오.

인간 검수자: ______　검수일: ______　검토 방식(독립 초기 판단/AI 초안 대조): ______

기준: [manifest.json](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/manifest.json>) · [원본근거_사례별대조_KR.md](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261102_gold_v2_ai_prereview_v1/원본근거_사례별대조_KR.md>) · [검토안내_KR.md](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261102_gold_v2_ai_prereview_v1/검토안내_KR.md>)

## PILOT_Q1_01 — 등대의 S-101 객체 유형과 정의를 알려줘.

- **AI 답안 제안:** 등대를 단일 Lighthouse 코드로 단정하지 않고 구조물 Landmark/Building과 등화 LightAllAround/LightSectored의 조건부 모델을 구분한다.
- **B의 비판 검토:** 네 코드를 모두 한 시설의 필수 구성으로 요구해서는 안 된다. 설명을 위한 대안 목록과 실제 객체 매핑을 구분한다.
- 필수 작업: explain_structure_and_light_distinction, explain_conditional_feature_mapping
- 추가 입력: 현재 동결 입력 기준으로 추가 입력을 정답의 필수조건으로 새로 만들지 않음. 원천 범위 부족은 사용자 입력 누락과 구분.
- 평가군: `SOURCE_BOUND_DOCUMENT_OR_EXISTING_Q4` / 동등 표현군: `Q1_01`
- 원본 계약: [answer_contracts.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl>) — JSONL 1행, `PILOT_Q1_01`
- 계약 record SHA256: `81babcf174a26b29cf097cc072e9ff44371aea8bcacd138598efd270ca5af6b8`
- 상세 원문·locator·객체 ID·거리: [PILOT_Q1_01 근거 부록](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261102_gold_v2_ai_prereview_v1/원본근거_사례별대조_KR.md>)의 해당 절
- **AI 잠정 판단:** 기존 기준을 검토용 제안으로 유지. 위 쟁점은 인간 확인 전 확정하지 않음.
- 인간 판단(수용/수정/보류): ______
- 인간 수정 답안·이유·직접 확인한 locator: ______
- AI 초안 열람 전 독립 답안을 작성했는지 및 원본 위치: ______
- 인간 검수자·일시·승인: ______

## PILOT_Q1_02 — S-101에서 정박지는 어떤 객체야?

- **AI 답안 제안:** 정박지는 AnchorageArea로 설명하고 FC 정의·point/surface 허용 geometry와 출처를 연결한다.
- **B의 비판 검토:** 일반 정박 행위와 데이터 객체의 존재를 혼동하지 않는다. 정의 질의에는 공간 실행이 필요하지 않다.
- 필수 작업: explain_anchorage_area_definition
- 추가 입력: 현재 동결 입력 기준으로 추가 입력을 정답의 필수조건으로 새로 만들지 않음. 원천 범위 부족은 사용자 입력 누락과 구분.
- 평가군: `SOURCE_BOUND_DOCUMENT_OR_EXISTING_Q4` / 동등 표현군: `Q1_02`
- 원본 계약: [answer_contracts.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl>) — JSONL 2행, `PILOT_Q1_02`
- 계약 record SHA256: `15705a461a7c4b4669073e5c75afe879e394d921f99b8dc52a8bad4d80547c42`
- 상세 원문·locator·객체 ID·거리: [PILOT_Q1_02 근거 부록](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261102_gold_v2_ai_prereview_v1/원본근거_사례별대조_KR.md>)의 해당 절
- **AI 잠정 판단:** 기존 기준을 검토용 제안으로 유지. 위 쟁점은 인간 확인 전 확정하지 않음.
- 인간 판단(수용/수정/보류): ______
- 인간 수정 답안·이유·직접 확인한 locator: ______
- AI 초안 열람 전 독립 답안을 작성했는지 및 원본 위치: ______
- 인간 검수자·일시·승인: ______

## PILOT_Q1_03 — What is a wreck in S-101?

- **AI 답안 제안:** Wreck의 정의와 point/surface 표현을 FC 근거로 설명한다.
- **B의 비판 검토:** 침선 개념 설명을 실제 침선 위치 검색으로 바꾸지 않는다. 원문과 동등한 의역도 의미 검수 대상이다.
- 필수 작업: explain_wreck_definition
- 추가 입력: 현재 동결 입력 기준으로 추가 입력을 정답의 필수조건으로 새로 만들지 않음. 원천 범위 부족은 사용자 입력 누락과 구분.
- 평가군: `SOURCE_BOUND_DOCUMENT_OR_EXISTING_Q4` / 동등 표현군: `Q1_03`
- 원본 계약: [answer_contracts.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl>) — JSONL 3행, `PILOT_Q1_03`
- 계약 record SHA256: `3f4d5b57299275c6c76fe1a15cf4d10ecf8ea4e1cb02ae9184689d96864fbcfa`
- 상세 원문·locator·객체 ID·거리: [PILOT_Q1_03 근거 부록](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261102_gold_v2_ai_prereview_v1/원본근거_사례별대조_KR.md>)의 해당 절
- **AI 잠정 판단:** 기존 기준을 검토용 제안으로 유지. 위 쟁점은 인간 확인 전 확정하지 않음.
- 인간 판단(수용/수정/보류): ______
- 인간 수정 답안·이유·직접 확인한 locator: ______
- AI 초안 열람 전 독립 답안을 작성했는지 및 원본 위치: ______
- 인간 검수자·일시·승인: ______

## PILOT_Q2_01 — S-101 등대의 색상 속성과 허용 값을 알려줘.

- **AI 답안 제안:** 구조물 colour와 등화 colour를 구분한다. Landmark/Building은 1~13, LightAllAround와 lightSector는 FC에 연결된 1,3,4,5,6,9,10,11을 제시한다.
- **B의 비판 검토:** LightSectored→sectorCharacteristics→lightSector→colour 경로를 확인한다. 전역 colour 코드 목록을 모든 Feature의 허용값으로 복사하지 않는다.
- 필수 작업: distinguish_structure_and_light_colour, explain_feature_bound_permitted_values
- 추가 입력: 현재 동결 입력 기준으로 추가 입력을 정답의 필수조건으로 새로 만들지 않음. 원천 범위 부족은 사용자 입력 누락과 구분.
- 평가군: `SOURCE_BOUND_DOCUMENT_OR_EXISTING_Q4` / 동등 표현군: `Q2_01`
- 원본 계약: [answer_contracts.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl>) — JSONL 4행, `PILOT_Q2_01`
- 계약 record SHA256: `1c605e0e61e3982c9edc8926370751d88f4091dffa37cde56495412345d4138b`
- 상세 원문·locator·객체 ID·거리: [PILOT_Q2_01 근거 부록](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261102_gold_v2_ai_prereview_v1/원본근거_사례별대조_KR.md>)의 해당 절
- **AI 잠정 판단:** 기존 기준을 검토용 제안으로 유지. 위 쟁점은 인간 확인 전 확정하지 않음.
- 인간 판단(수용/수정/보류): ______
- 인간 수정 답안·이유·직접 확인한 locator: ______
- AI 초안 열람 전 독립 답안을 작성했는지 및 원본 위치: ______
- 인간 검수자·일시·승인: ______

## PILOT_Q2_02 — 제한구역의 제한 종류는 어떤 코드로 표현해?

- **AI 답안 제안:** RestrictedArea의 restriction과 categoryOfRestrictedArea를 구분하여 Feature별 연결·다중성·허용 코드를 설명한다.
- **B의 비판 검토:** 구역 종류 코드와 실제 제한 행위 코드는 다른 속성이다. 공개 FC 설명을 실제 구역의 법적 허가 또는 비공개 자료 요청으로 해석하지 않는다.
- 필수 작업: distinguish_restriction_and_area_category, explain_restriction_codes
- 추가 입력: 현재 동결 입력 기준으로 추가 입력을 정답의 필수조건으로 새로 만들지 않음. 원천 범위 부족은 사용자 입력 누락과 구분.
- 평가군: `SOURCE_BOUND_DOCUMENT_OR_EXISTING_Q4` / 동등 표현군: `Q2_02`
- 원본 계약: [answer_contracts.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl>) — JSONL 5행, `PILOT_Q2_02`
- 계약 record SHA256: `66af138ff276d3dc301304e40a23ef64b2eb7ff202d5e78cea9b2db0f1d869a9`
- 상세 원문·locator·객체 ID·거리: [PILOT_Q2_02 근거 부록](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261102_gold_v2_ai_prereview_v1/원본근거_사례별대조_KR.md>)의 해당 절
- **AI 잠정 판단:** 기존 기준을 검토용 제안으로 유지. 위 쟁점은 인간 확인 전 확정하지 않음.
- 인간 판단(수용/수정/보류): ______
- 인간 수정 답안·이유·직접 확인한 locator: ______
- AI 초안 열람 전 독립 답안을 작성했는지 및 원본 위치: ______
- 인간 검수자·일시·승인: ______

## PILOT_Q2_03 — Which attributes describe a Wreck in S-101?

- **AI 답안 제안:** Wreck에 실제 연결된 속성 목록·정의·다중성·허용값을 제시한다. waterLevelEffect와 surroundingDepth의 필수 다중성을 확인한다.
- **B의 비판 검토:** FC 속성 정의와 특정 침선의 실제 속성값은 별개다. 전역에 존재하는 속성을 Wreck에 연결된 것으로 추정하지 않는다.
- 필수 작업: explain_wreck_attribute_bindings
- 추가 입력: 현재 동결 입력 기준으로 추가 입력을 정답의 필수조건으로 새로 만들지 않음. 원천 범위 부족은 사용자 입력 누락과 구분.
- 평가군: `SOURCE_BOUND_DOCUMENT_OR_EXISTING_Q4` / 동등 표현군: `Q2_03`
- 원본 계약: [answer_contracts.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl>) — JSONL 6행, `PILOT_Q2_03`
- 계약 record SHA256: `a5b8ee594911da51c3445af17b68b9836577bafe2f7c3165016b6edb62dd229f`
- 상세 원문·locator·객체 ID·거리: [PILOT_Q2_03 근거 부록](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261102_gold_v2_ai_prereview_v1/원본근거_사례별대조_KR.md>)의 해당 절
- **AI 잠정 판단:** 기존 기준을 검토용 제안으로 유지. 위 쟁점은 인간 확인 전 확정하지 않음.
- 인간 판단(수용/수정/보류): ______
- 인간 수정 답안·이유·직접 확인한 locator: ______
- AI 초안 열람 전 독립 답안을 작성했는지 및 원본 위치: ______
- 인간 검수자·일시·승인: ______

## PILOT_Q3_01 — 독도 부근에서 가장 가까운 등대를 찾아줘.

- **AI 답안 제안:** 현재 부산권 snapshot으로 독도 최근접 등대를 확정할 수 없으므로 DATA_OUT_OF_SCOPE/BLOCKED_DATA와 원천 범위 부족을 설명한다. 공간 객체 GOLD는 없다.
- **B의 비판 검토:** 전국 최근접 계산의 정답이나 실세계 0건으로 만들지 않는다. 단순 UNSUPPORTED_OPERATOR 차단은 올바른 coverage 판단 전체를 충족하지 않는다.
- 필수 작업: resolve_reference, resolve_lighthouse_target_conditions, verify_coverage, find_nearest, report_objects_or_unresolved_reason
- 추가 입력: 현재 동결 입력 기준으로 추가 입력을 정답의 필수조건으로 새로 만들지 않음. 원천 범위 부족은 사용자 입력 누락과 구분.
- 평가군: `OUT_OF_COVERAGE_SAFE_ABSTENTION` / 동등 표현군: `Q3_01`
- 원본 계약: [answer_contracts.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl>) — JSONL 7행, `PILOT_Q3_01`
- 계약 record SHA256: `e5bc6a306d3000b245d85baf34f22c077178e43c936f4b7653969ad724a16e64`
- 상세 원문·locator·객체 ID·거리: [PILOT_Q3_01 근거 부록](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261102_gold_v2_ai_prereview_v1/원본근거_사례별대조_KR.md>)의 해당 절
- **AI 잠정 판단:** 기존 기준을 검토용 제안으로 유지. 위 쟁점은 인간 확인 전 확정하지 않음.
- 인간 판단(수용/수정/보류): ______
- 인간 수정 답안·이유·직접 확인한 locator: ______
- AI 초안 열람 전 독립 답안을 작성했는지 및 원본 위치: ______
- 인간 검수자·일시·승인: ______

## PILOT_Q3_02 — 부산항 영역 안의 정박지를 찾아줘.

- **AI 답안 제안:** 고정 부산항 polygon과 ST_Covers(reference,target)를 사용한 snapshot 내 AnchorageArea 정답은 빈 집합이다. 원천·범위와 검사 조건을 함께 공개한다.
- **B의 비판 검토:** 유효한 빈 Oracle과 미실행/누락은 다르다. 이 polygon은 연구용 고정 경계이며 법적 항계 전체와 동일하다고 단정하지 않는다.
- 필수 작업: resolve_official_port_polygon, verify_coverage, search_within_polygon, report_objects_or_unresolved_reason
- 추가 입력: 현재 동결 입력 기준으로 추가 입력을 정답의 필수조건으로 새로 만들지 않음. 원천 범위 부족은 사용자 입력 누락과 구분.
- 평가군: `IN_SNAPSHOT_SPATIAL` / 동등 표현군: `Q3_02`
- 원본 계약: [answer_contracts.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl>) — JSONL 8행, `PILOT_Q3_02`
- 계약 record SHA256: `ee0c7885bc263af6c93657df474baf2bc46d860444006fdc7b9c2e99baaa78a1`
- 상세 원문·locator·객체 ID·거리: [PILOT_Q3_02 근거 부록](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261102_gold_v2_ai_prereview_v1/원본근거_사례별대조_KR.md>)의 해당 절
- **AI 잠정 판단:** 기존 기준을 검토용 제안으로 유지. 위 쟁점은 인간 확인 전 확정하지 않음.
- 인간 판단(수용/수정/보류): ______
- 인간 수정 답안·이유·직접 확인한 locator: ______
- AI 초안 열람 전 독립 답안을 작성했는지 및 원본 위치: ______
- 인간 검수자·일시·승인: ______

## PILOT_Q3_03 — Find wrecks intersecting the selected area.

- **AI 답안 제안:** 선택 영역이 없으므로 NEEDS_USER_INPUT, MISSING_REFERENCE_GEOMETRY를 반환하고 execution_attempted/started/tool_called/sql_executed=false여야 한다.
- **B의 비판 검토:** 임의 viewport나 기준점으로 대체하지 않는다. 안내 문구만으로 미실행을 인정하지 말고 실행 로그를 확인한다.
- 필수 작업: require_selected_aoi, verify_coverage, search_intersections_if_aoi_available, request_aoi_when_missing
- 추가 입력: 선택 영역이 필요함. 확보 전 GIS 실행 금지.
- 평가군: `MISSING_REQUIRED_INPUT` / 동등 표현군: `Q3_03`
- 원본 계약: [answer_contracts.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl>) — JSONL 9행, `PILOT_Q3_03`
- 계약 record SHA256: `1e22a5d5ebb92f1a9b1a46f55da9b27ed8c3918fb98529d940fddd68a29a3cb2`
- 상세 원문·locator·객체 ID·거리: [PILOT_Q3_03 근거 부록](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261102_gold_v2_ai_prereview_v1/원본근거_사례별대조_KR.md>)의 해당 절
- **AI 잠정 판단:** 기존 기준을 검토용 제안으로 유지. 위 쟁점은 인간 확인 전 확정하지 않음.
- 인간 판단(수용/수정/보류): ______
- 인간 수정 답안·이유·직접 확인한 locator: ______
- AI 초안 열람 전 독립 답안을 작성했는지 및 원본 위치: ______
- 인간 검수자·일시·승인: ______

## PILOT_Q4_01 — 독도 주변 반경 5km의 해양지명을 찾아줘.

- **AI 답안 제안:** 승인 동도 기준점·2022 CSV·WGS84 지오데식 거리 5000m 이하로 고정한다. 원본 ID 44~54의 11개 지명을 반환하고 출처를 연결한다.
- **B의 비판 검토:** 원천 corpus의 정답이며 독도 주변 실세계 지명의 완전목록이 아니다. S-101 ID와 CSV 원본 ID를 혼용하지 않는다.
- 필수 작업: resolve_approved_anchor, search_fixed_gazetteer_5000m, report_source_bound_objects
- 추가 입력: 현재 동결 입력 기준으로 추가 입력을 정답의 필수조건으로 새로 만들지 않음. 원천 범위 부족은 사용자 입력 누락과 구분.
- 평가군: `SOURCE_BOUND_DOCUMENT_OR_EXISTING_Q4` / 동등 표현군: `dokdo_radius_5km`
- 원본 계약: [answer_contracts.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl>) — JSONL 10행, `PILOT_Q4_01`
- 계약 record SHA256: `0cb27baee7c68b4561d814143ed423e143e8efde9d37a6bbab836707286c2efb`
- 상세 원문·locator·객체 ID·거리: [PILOT_Q4_01 근거 부록](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261102_gold_v2_ai_prereview_v1/원본근거_사례별대조_KR.md>)의 해당 절
- **AI 잠정 판단:** 기존 기준을 검토용 제안으로 유지. 위 쟁점은 인간 확인 전 확정하지 않음.
- 인간 판단(수용/수정/보류): ______
- 인간 수정 답안·이유·직접 확인한 locator: ______
- AI 초안 열람 전 독립 답안을 작성했는지 및 원본 위치: ______
- 인간 검수자·일시·승인: ______

## PILOT_Q4_02 — 독도 주변 반경 5000m의 해양지명을 찾아줘.

- **AI 답안 제안:** 5000m를 Q4-01의 5km와 같은 조건으로 해석한다. 동일 기준점과 동일 11개 원본 ID 집합이 정답이다.
- **B의 비판 검토:** 단위 변환은 허용되지만 반경·기준점·원천은 변경하지 않는다. 세 표현을 독립 공간 문제로 합산하지 않는다.
- 필수 작업: resolve_approved_anchor, search_fixed_gazetteer_5000m, report_source_bound_objects
- 추가 입력: 현재 동결 입력 기준으로 추가 입력을 정답의 필수조건으로 새로 만들지 않음. 원천 범위 부족은 사용자 입력 누락과 구분.
- 평가군: `SOURCE_BOUND_DOCUMENT_OR_EXISTING_Q4` / 동등 표현군: `dokdo_radius_5km`
- 원본 계약: [answer_contracts.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl>) — JSONL 11행, `PILOT_Q4_02`
- 계약 record SHA256: `0dcf4dd99e99c1fd3d9e012a6eb3eb94f9d1c6d5364c75e704c0b13775c1bfde`
- 상세 원문·locator·객체 ID·거리: [PILOT_Q4_02 근거 부록](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261102_gold_v2_ai_prereview_v1/원본근거_사례별대조_KR.md>)의 해당 절
- **AI 잠정 판단:** 기존 기준을 검토용 제안으로 유지. 위 쟁점은 인간 확인 전 확정하지 않음.
- 인간 판단(수용/수정/보류): ______
- 인간 수정 답안·이유·직접 확인한 locator: ______
- AI 초안 열람 전 독립 답안을 작성했는지 및 원본 위치: ______
- 인간 검수자·일시·승인: ______

## PILOT_Q4_03 — Find marine place names within 5 km of Dokdo.

- **AI 답안 제안:** 영어 5 km 질의도 Q4-01·02와 같은 기준점·원천·11개 ID를 사용한다.
- **B의 비판 검토:** 언어 차이만으로 공간 의미나 coverage를 바꾸지 않는다. 개발 노출된 동등 표현군이며 독립 holdout이 아니다.
- 필수 작업: resolve_approved_anchor, search_fixed_gazetteer_5000m, report_source_bound_objects
- 추가 입력: 현재 동결 입력 기준으로 추가 입력을 정답의 필수조건으로 새로 만들지 않음. 원천 범위 부족은 사용자 입력 누락과 구분.
- 평가군: `SOURCE_BOUND_DOCUMENT_OR_EXISTING_Q4` / 동등 표현군: `dokdo_radius_5km`
- 원본 계약: [answer_contracts.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl>) — JSONL 12행, `PILOT_Q4_03`
- 계약 record SHA256: `031d4bcfe49d35891520958cdfbf52d72ccf5d0ae888dcb564e0cf386bca10f9`
- 상세 원문·locator·객체 ID·거리: [PILOT_Q4_03 근거 부록](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261102_gold_v2_ai_prereview_v1/원본근거_사례별대조_KR.md>)의 해당 절
- **AI 잠정 판단:** 기존 기준을 검토용 제안으로 유지. 위 쟁점은 인간 확인 전 확정하지 않음.
- 인간 판단(수용/수정/보류): ______
- 인간 수정 답안·이유·직접 확인한 locator: ______
- AI 초안 열람 전 독립 답안을 작성했는지 및 원본 위치: ______
- 인간 검수자·일시·승인: ______

## PILOT_Q5_01 — 독도 주변 5km의 등대와 난파선을 찾아 각각의 근거를 알려줘.

- **AI 답안 제안:** 독도 5km의 Lighthouse와 Wreck 두 공간 하위작업 모두 coverage 부족으로 BLOCKED_DATA다. 표준 정의는 별도 부분응답으로만 허용한다.
- **B의 비판 검토:** 한 대상만 처리하고 전체 완료로 선언하거나 두 빈 집합을 실세계 부재로 제시하면 안 된다. 대상별 상태·근거가 필요하다.
- 필수 작업: resolve_reference, resolve_lighthouse_target_conditions, verify_both_target_coverages, search_both_targets_5000m, provide_per_target_evidence, separate_partial_document_answer
- 추가 입력: 현재 동결 입력 기준으로 추가 입력을 정답의 필수조건으로 새로 만들지 않음. 원천 범위 부족은 사용자 입력 누락과 구분.
- 평가군: `OUT_OF_COVERAGE_SAFE_ABSTENTION` / 동등 표현군: `Q5_01`
- 원본 계약: [answer_contracts.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl>) — JSONL 13행, `PILOT_Q5_01`
- 계약 record SHA256: `38449664101b89df898864ea9e4d914ab28097fccf021af43249cb531ff50d64`
- 상세 원문·locator·객체 ID·거리: [PILOT_Q5_01 근거 부록](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261102_gold_v2_ai_prereview_v1/원본근거_사례별대조_KR.md>)의 해당 절
- **AI 잠정 판단:** 기존 기준을 검토용 제안으로 유지. 위 쟁점은 인간 확인 전 확정하지 않음.
- 인간 판단(수용/수정/보류): ______
- 인간 수정 답안·이유·직접 확인한 locator: ______
- AI 초안 열람 전 독립 답안을 작성했는지 및 원본 위치: ______
- 인간 검수자·일시·승인: ______

## PILOT_Q5_02 — 부산항 주변 2km의 정박지와 제한구역을 찾아 비교해줘.

- **AI 답안 제안:** 고정 부산항 polygon과 geometry 간 최소 지오데식 거리 2000m 이하인 AnchorageArea/RestrictedArea 객체 집합을 각각 반환하고 수·거리·정의·원천 범위를 비교한다.
- **B의 비판 검토:** 표현상 polygon 경계 거리와 ST_DWithin(polygon,target)의 내부거리 0은 다를 수 있다. 동결 계약의 실제 predicate를 우선 보존하고 사람이 의미를 확인한다. ID는 snapshot 기록이며 중복 시설 제거 결과가 아니다.
- 필수 작업: resolve_reference, verify_both_target_coverages, search_both_targets_2000m, compare_target_results, disclose_subset_limitations
- 추가 입력: 현재 동결 입력 기준으로 추가 입력을 정답의 필수조건으로 새로 만들지 않음. 원천 범위 부족은 사용자 입력 누락과 구분.
- 평가군: `IN_SNAPSHOT_SPATIAL` / 동등 표현군: `Q5_02`
- 원본 계약: [answer_contracts.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl>) — JSONL 14행, `PILOT_Q5_02`
- 계약 record SHA256: `96a2767035cae2bdc2c9a1c5530194d676d236e9db86ed30b93434d4280adba2`
- 상세 원문·locator·객체 ID·거리: [PILOT_Q5_02 근거 부록](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261102_gold_v2_ai_prereview_v1/원본근거_사례별대조_KR.md>)의 해당 절
- **AI 잠정 판단:** 기존 기준을 검토용 제안으로 유지. 위 쟁점은 인간 확인 전 확정하지 않음.
- 인간 판단(수용/수정/보류): ______
- 인간 수정 답안·이유·직접 확인한 locator: ______
- AI 초안 열람 전 독립 답안을 작성했는지 및 원본 위치: ______
- 인간 검수자·일시·승인: ______

## PILOT_Q5_03 — Find wrecks within 5 km of Dokdo and explain their S-101 attributes.

- **AI 답안 제안:** 독도 Wreck 공간 부분은 BLOCKED_DATA, 실제 object attribute value는 확정하지 않는다. FC 속성 설명은 별도 문서 부분응답으로 가능하다.
- **B의 비판 검토:** FC 정의만으로 실제 Wreck 객체 속성값을 만들어서는 안 된다. 추후 in-scope 객체 과제는 object value↔FC definition 연결을 따로 평가해야 한다.
- 필수 작업: resolve_reference, verify_coverage, search_wrecks_5000m, explain_s101_attributes, distinguish_object_values_from_standard_attributes, separate_partial_document_answer
- 추가 입력: 현재 동결 입력 기준으로 추가 입력을 정답의 필수조건으로 새로 만들지 않음. 원천 범위 부족은 사용자 입력 누락과 구분.
- 평가군: `OUT_OF_COVERAGE_SAFE_ABSTENTION` / 동등 표현군: `Q5_03`
- 원본 계약: [answer_contracts.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl>) — JSONL 15행, `PILOT_Q5_03`
- 계약 record SHA256: `b2d84688b2c082c4a9b99da6b58ddff4c2d15cac21b98d9a09a41add31d6b242`
- 상세 원문·locator·객체 ID·거리: [PILOT_Q5_03 근거 부록](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261102_gold_v2_ai_prereview_v1/원본근거_사례별대조_KR.md>)의 해당 절
- **AI 잠정 판단:** 기존 기준을 검토용 제안으로 유지. 위 쟁점은 인간 확인 전 확정하지 않음.
- 인간 판단(수용/수정/보류): ______
- 인간 수정 답안·이유·직접 확인한 locator: ______
- AI 초안 열람 전 독립 답안을 작성했는지 및 원본 위치: ______
- 인간 검수자·일시·승인: ______

## PILOT_Q6_01 — S-101 Wreck 정의의 원문과 Feature Catalogue 출처를 알려줘.

- **AI 답안 제안:** Wreck 정의 원문과 FC 2.0.0 판·SHA256·Feature locator를 함께 제시한다.
- **B의 비판 검토:** 원문 인용 정확성과 의미 설명 정확도를 별도로 판단한다. 검색 문서 존재만으로 최종 답변에 인용됐다고 인정하지 않는다.
- 필수 작업: provide_wreck_definition_text, cite_catalogue_edition_and_locator
- 추가 입력: 현재 동결 입력 기준으로 추가 입력을 정답의 필수조건으로 새로 만들지 않음. 원천 범위 부족은 사용자 입력 누락과 구분.
- 평가군: `SOURCE_BOUND_DOCUMENT_OR_EXISTING_Q4` / 동등 표현군: `Q6_01`
- 원본 계약: [answer_contracts.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl>) — JSONL 16행, `PILOT_Q6_01`
- 계약 record SHA256: `0fb641693a52d6303219757898703c7beb5976f1046002dd6a7b094d2875ff2f`
- 상세 원문·locator·객체 ID·거리: [PILOT_Q6_01 근거 부록](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261102_gold_v2_ai_prereview_v1/원본근거_사례별대조_KR.md>)의 해당 절
- **AI 잠정 판단:** 기존 기준을 검토용 제안으로 유지. 위 쟁점은 인간 확인 전 확정하지 않음.
- 인간 판단(수용/수정/보류): ______
- 인간 수정 답안·이유·직접 확인한 locator: ______
- AI 초안 열람 전 독립 답안을 작성했는지 및 원본 위치: ______
- 인간 검수자·일시·승인: ______

## PILOT_Q6_02 — 등대와 부표를 구분하는 S-101 근거를 알려줘.

- **AI 답안 제안:** 조건부 구조물/등화 모델과 대표 부유표지 LateralBuoy를 FC 정의로 비교한다.
- **B의 비판 검토:** LateralBuoy는 부표 전체의 대체가 아닌 한정 대표다. 원질의의 일반 부표 비교를 이 한정 범위로 평가하는 것이 적절한지 사람이 확인해야 한다.
- 필수 작업: compare_fixed_structure_and_floating_aid_models, cite_comparison_evidence
- 추가 입력: 현재 동결 입력 기준으로 추가 입력을 정답의 필수조건으로 새로 만들지 않음. 원천 범위 부족은 사용자 입력 누락과 구분.
- 평가군: `SOURCE_BOUND_DOCUMENT_OR_EXISTING_Q4` / 동등 표현군: `Q6_02`
- 원본 계약: [answer_contracts.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl>) — JSONL 17행, `PILOT_Q6_02`
- 계약 record SHA256: `53a7a1d78ae16fd8cd71f7c070f20e9a0ebb0edb18c2caece06c0c3d4dc72fe5`
- 상세 원문·locator·객체 ID·거리: [PILOT_Q6_02 근거 부록](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261102_gold_v2_ai_prereview_v1/원본근거_사례별대조_KR.md>)의 해당 절
- **AI 잠정 판단:** 기존 기준을 검토용 제안으로 유지. 위 쟁점은 인간 확인 전 확정하지 않음.
- 인간 판단(수용/수정/보류): ______
- 인간 수정 답안·이유·직접 확인한 locator: ______
- AI 초안 열람 전 독립 답안을 작성했는지 및 원본 위치: ______
- 인간 검수자·일시·승인: ______

## PILOT_Q6_03 — What source supports the S-101 definition of AnchorageArea?

- **AI 답안 제안:** AnchorageArea 정의를 뒷받침하는 FC 2.0.0 원문·판·hash·locator를 연결한다.
- **B의 비판 검토:** 원천 제목만 제시하거나 모델의 일반 지식을 인용 근거로 대신하지 않는다. 실제 공간 검색은 요구되지 않는다.
- 필수 작업: provide_anchorage_definition_source, cite_catalogue_edition_and_locator
- 추가 입력: 현재 동결 입력 기준으로 추가 입력을 정답의 필수조건으로 새로 만들지 않음. 원천 범위 부족은 사용자 입력 누락과 구분.
- 평가군: `SOURCE_BOUND_DOCUMENT_OR_EXISTING_Q4` / 동등 표현군: `Q6_03`
- 원본 계약: [answer_contracts.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl>) — JSONL 18행, `PILOT_Q6_03`
- 계약 record SHA256: `092121665e482ded0b260387646eae381cf3d31963d346d3057c601c70cbea74`
- 상세 원문·locator·객체 ID·거리: [PILOT_Q6_03 근거 부록](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261102_gold_v2_ai_prereview_v1/원본근거_사례별대조_KR.md>)의 해당 절
- **AI 잠정 판단:** 기존 기준을 검토용 제안으로 유지. 위 쟁점은 인간 확인 전 확정하지 않음.
- 인간 판단(수용/수정/보류): ______
- 인간 수정 답안·이유·직접 확인한 locator: ______
- AI 초안 열람 전 독립 답안을 작성했는지 및 원본 위치: ______
- 인간 검수자·일시·승인: ______
