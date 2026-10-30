# 18사례 평가계약 초안 v4

기존 v3 사용자 승인은 보존한다. 아래 작업 분해·capability 조합은 새 해석이므로 DRAFT이며 자동 채점에 사용하지 않는다.

| 사례 | 질의 | 작업 제안 | 승인 QEC 전사 | 공간 참조 | 미확정 원문 |
|---|---|---|---|---|---|
| PILOT_Q1_01 | 등대의 S-101 객체 유형과 정의를 알려줘. | explain_structure_and_light_distinction, explain_conditional_feature_mapping | 0개 필드 | 비공간 과업 | 최종 GOLD에서 ‘등대 구조물’과 ‘등화’를 별도 정답 범위로 명시하고, function/category binding은 FC 2.0.0로 최종 확인. |
| PILOT_Q1_02 | S-101에서 정박지는 어떤 객체야? | explain_anchorage_area_definition | 0개 필드 | 비공간 과업 | GOLD 승인 시 이 질의의 ‘정박지’가 일반 정박구역을 뜻한다는 범위를 명시. |
| PILOT_Q1_03 | What is a wreck in S-101? | explain_wreck_definition | 0개 필드 | 비공간 과업 | 추가 쟁점 없음. 표준 정의·feature code·기하를 최종 확인. |
| PILOT_Q2_01 | S-101 등대의 색상 속성과 허용 값을 알려줘. | distinguish_structure_and_light_colour, explain_feature_bound_permitted_values | 0개 필드 | 비공간 과업 | 이 항목은 기존 합의안의 실질 수정사항. 최종 GOLD에서 Feature별 permitted_values를 FC binding 기준으로 확정. |
| PILOT_Q2_02 | 제한구역의 제한 종류는 어떤 코드로 표현해? | distinguish_restriction_and_area_category, explain_restriction_codes | 0개 필드 | 비공간 과업 | 최종 답안은 질의의 ‘제한 종류’가 두 의미 중 무엇인지 짧게 구분 설명하는 것이 적절. |
| PILOT_Q2_03 | Which attributes describe a Wreck in S-101? | explain_wreck_attribute_bindings | 0개 필드 | 비공간 과업 | 최종 GOLD에는 필수/선택, 다중도, permitted_values까지 필요한 수준을 결정하고 DB projection 컬럼과 표준 attribute를 구분. |
| PILOT_Q3_01 | 독도 부근에서 가장 가까운 등대를 찾아줘. | resolve_reference, resolve_lighthouse_target_conditions, verify_coverage, find_nearest, report_objects_or_unresolved_reason | 1개 필드 | 공간정답 미확정 | Spatial GOLD 조건: 독도 anchor 승인 + 전국 AtoN/S-101 snapshot + 시설 중복정책 + 독립 nearest SQL/object ID. |
| PILOT_Q3_02 | 부산항 영역 안의 정박지를 찾아줘. | resolve_official_port_polygon, verify_coverage, search_within_polygon, report_objects_or_unresolved_reason | 1개 필드 | 공간정답 미확정 | 부산항 권위 polygon 확보 후 경계 포함규칙을 고정하고 object ID를 독립 검증. |
| PILOT_Q3_03 | Find wrecks intersecting the selected area. | require_selected_aoi, verify_coverage, search_intersections_if_aoi_available, request_aoi_when_missing | 0개 필드 | 공간정답 미확정 | QEC GOLD에 geometry_required=true, no_default_AOI=true 및 Wreck geometry support를 명시. |
| PILOT_Q4_01 | 독도 주변 반경 5km의 해양지명을 찾아줘. | resolve_approved_anchor, search_fixed_gazetteer_5000m, report_source_bound_objects | 2개 필드 | 기존 Q4 11개 ID | 기준점·CSV·거리·ID는 v3에서 해소. 새 작업분해 승인 및 응답 완결성 기준 미확정. |
| PILOT_Q4_02 | 독도 주변 반경 5000m의 해양지명을 찾아줘. | resolve_approved_anchor, search_fixed_gazetteer_5000m, report_source_bound_objects | 2개 필드 | 기존 Q4 11개 ID | 기준점·CSV·거리·ID는 v3에서 해소. 새 작업분해 승인 및 응답 완결성 기준 미확정. |
| PILOT_Q4_03 | Find marine place names within 5 km of Dokdo. | resolve_approved_anchor, search_fixed_gazetteer_5000m, report_source_bound_objects | 2개 필드 | 기존 Q4 11개 ID | 기준점·CSV·거리·ID는 v3에서 해소. 새 작업분해 승인 및 응답 완결성 기준 미확정. |
| PILOT_Q5_01 | 독도 주변 5km의 등대와 난파선을 찾아 각각의 근거를 알려줘. | resolve_reference, resolve_lighthouse_target_conditions, verify_both_target_coverages, search_both_targets_5000m, provide_per_target_evidence, separate_partial_document_answer | 2개 필드 | 공간정답 미확정 | B의 Q5_01 feature 후보에서 Building 누락을 최종 전문가가 확인. 독도 anchor·등대 coverage·Wreck snapshot·dedup 정책 확보 후 Spatial GOLD. |
| PILOT_Q5_02 | 부산항 주변 2km의 정박지와 제한구역을 찾아 비교해줘. | resolve_reference, verify_both_target_coverages, search_both_targets_2000m, compare_target_results, disclose_subset_limitations | 2개 필드 | 공간정답 미확정 | 부산항 기준 geometry와 거리정책을 먼저 승인. 전체 S-101 RestrictedArea benchmark와 DS09 subset benchmark를 분리하는 것이 바람직. |
| PILOT_Q5_03 | Find wrecks within 5 km of Dokdo and explain their S-101 attributes. | resolve_reference, verify_coverage, search_wrecks_5000m, explain_s101_attributes, distinguish_object_values_from_standard_attributes, separate_partial_document_answer | 2개 필드 | 공간정답 미확정 | 독도 anchor + S-101 Wreck snapshot + 독립 radius oracle 필요. Evidence GOLD는 FC 허용속성과 object actual value를 분리. |
| PILOT_Q6_01 | S-101 Wreck 정의의 원문과 Feature Catalogue 출처를 알려줘. | provide_wreck_definition_text, cite_catalogue_edition_and_locator | 0개 필드 | 비공간 과업 | Evidence GOLD에는 edition, feature code, source file, locator/section을 필수 저장. |
| PILOT_Q6_02 | 등대와 부표를 구분하는 S-101 근거를 알려줘. | compare_fixed_structure_and_floating_aid_models, cite_comparison_evidence | 0개 필드 | 비공간 과업 | 최종 GOLD에서 비교 기준을 ‘고정 구조물 vs 부유 표지의 Feature 모델링 및 equipment composition’으로 명시. |
| PILOT_Q6_03 | What source supports the S-101 definition of AnchorageArea? | provide_anchorage_definition_source, cite_catalogue_edition_and_locator | 0개 필드 | 비공간 과업 | Evidence GOLD에 source file/version/locator와 Feature code를 저장. |
