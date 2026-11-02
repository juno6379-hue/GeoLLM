# BBB — 독립 인간 답변 채점 144건

실험 방법 라벨과 기계 채점은 별도 분리했다. 원문 내부의 실행 상태·지연·식별자는 보존되어 완전 블라인딩이 아니다. 아래 human-label 블록에 판단을 기록한다.

## ANSWER_144 — S-101 등대의 색상 속성과 허용 값을 알려줘.

답안 hash: `a313c161f3d60626369452f80690ba42b8912cc5ab205f72b69e14b5c747d86d`

### 실제 최종 답안
```json
{
  "answer_text": "등대 색상: 주로 노란색이며, 일부는 검정색이나 흰색입니다. 허용 레이즈: 1000m 이내입니다.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "document_answer": {
    "features": [],
    "attribute_bindings": [],
    "evidence": {
      "edition": "2.0.0",
      "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
      "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
      "locators": [],
      "claim_source_links": []
    }
  },
  "status": "COMPLETED",
  "execution_status": "COMPLETED",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q2_01.json)
```json
{
  "case_id": "PILOT_Q2_01",
  "required_task_obligations": [
    "distinguish_structure_and_light_colour",
    "explain_feature_bound_permitted_values"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "single_Lighthouse_feature_assertion",
    "global_colour_codes_for_feature_binding"
  ],
  "scope_notes": [
    "Landmark/Building describe conditional structure alternatives; LightAllAround/LightSectored describe light alternatives. Listing these for explanation does not assert all must exist in one physical lighthouse."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_144",
  "answer_sha256": "a313c161f3d60626369452f80690ba42b8912cc5ab205f72b69e14b5c747d86d",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "1f6533698bdc721832f3249e84e12c8bf21150f2867bd17eb9a54a74597a14cc",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_143 — Find wrecks intersecting the selected area.

답안 hash: `28e7fb4ed351d54e98407587eba21e698fec5b676233998ed81c569ef178cf4a`

### 실제 최종 답안
```json
{
  "answer_text": "The selected area intersects with the following wrecks:",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q3_03.json)
```json
{
  "case_id": "PILOT_Q3_03",
  "required_task_obligations": [
    "require_selected_aoi",
    "verify_coverage",
    "search_intersections_if_aoi_available",
    "request_aoi_when_missing"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "No selected geometry is provided by this benchmark input; an arbitrary viewport is not a substitute."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_143",
  "answer_sha256": "28e7fb4ed351d54e98407587eba21e698fec5b676233998ed81c569ef178cf4a",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "f39d04bc097b46a1eccab990da2e1885ab58e94bd8e3f80eaf5580abfcc17263",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_142 — 부산항 주변 2km의 정박지와 제한구역을 찾아 비교해줘.

답안 hash: `256d67ffc4c87bc8230b3d0956932799610221d86db773486914d5454adebd32`

### 실제 최종 답안
```json
{
  "answer_text": "The search results for 'port', 'dock', and 'shipyard' within 2km of Busan Port are as follows:",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "document_answers": [
    {
      "features": [],
      "attribute_bindings": [],
      "evidence": {
        "edition": "2.0.0",
        "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
        "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
        "locators": [],
        "claim_source_links": []
      }
    },
    {
      "features": [],
      "attribute_bindings": [],
      "evidence": {
        "edition": "2.0.0",
        "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
        "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
        "locators": [],
        "claim_source_links": []
      }
    },
    {
      "features": [],
      "attribute_bindings": [],
      "evidence": {
        "edition": "2.0.0",
        "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
        "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
        "locators": [],
        "claim_source_links": []
      }
    }
  ],
  "status": "COMPLETED",
  "execution_status": "COMPLETED",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q5_02.json)
```json
{
  "case_id": "PILOT_Q5_02",
  "required_task_obligations": [
    "resolve_reference",
    "verify_both_target_coverages",
    "search_both_targets_2000m",
    "compare_target_results",
    "disclose_subset_limitations"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "Object IDs refer to frozen snapshot records, not deduplicated physical facilities or the whole legal port."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_142",
  "answer_sha256": "256d67ffc4c87bc8230b3d0956932799610221d86db773486914d5454adebd32",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "7f453b95651075baccdcbe45b5ef6b695165123718a44cd141ee64db305d9c23",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_141 — 독도 주변 5km의 등대와 난파선을 찾아 각각의 근거를 알려줘.

답안 hash: `5b2f42ee8ea6a4a0a555c54aac50fb383932f240bac419d3c9cb09c4622497ef`

### 실제 최종 답안
```json
{
  "answer_text": "The lighthouse and anchor line around Dokdo within a 5km radius are as follows:\n\nLighthouse: [Lighthouse name]\n\nAnchor Line: [Anchor line name]",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q5_01.json)
```json
{
  "case_id": "PILOT_Q5_01",
  "required_task_obligations": [
    "resolve_reference",
    "resolve_lighthouse_target_conditions",
    "verify_both_target_coverages",
    "search_both_targets_5000m",
    "provide_per_target_evidence",
    "separate_partial_document_answer"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "User-approved source-bound safe abstention; document explanations are separately evaluated optional partial output."
  ],
  "expected_spatial_behavior": {
    "accepted_states": [
      "BLOCKED_DATA",
      "DATA_OUT_OF_SCOPE"
    ],
    "required_disclosure": "Current connected snapshot cannot determine the answer for the requested spatial extent",
    "per_target": {
      "Lighthouse": {
        "status": "BLOCKED_DATA",
        "object_ids": null
      },
      "Wreck": {
        "status": "BLOCKED_DATA",
        "object_ids": null
      }
    },
    "empty_result_as_answer_forbidden": true,
    "claim_spatial_success_forbidden": true
  }
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_141",
  "answer_sha256": "5b2f42ee8ea6a4a0a555c54aac50fb383932f240bac419d3c9cb09c4622497ef",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "292f7ee0fba582ed04790e9b6140404196646d2505c016b2b49a2986e5297951",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_140 — 등대의 S-101 객체 유형과 정의를 알려줘.

답안 hash: `74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b`

### 실제 최종 답안
```json
null
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q1_01.json)
```json
{
  "case_id": "PILOT_Q1_01",
  "required_task_obligations": [
    "explain_structure_and_light_distinction",
    "explain_conditional_feature_mapping"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "single_Lighthouse_feature_assertion",
    "global_colour_codes_for_feature_binding"
  ],
  "scope_notes": [
    "Landmark/Building describe conditional structure alternatives; LightAllAround/LightSectored describe light alternatives. Listing these for explanation does not assert all must exist in one physical lighthouse."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_140",
  "answer_sha256": "74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_139 — 독도 주변 반경 5km의 해양지명을 찾아줘.

답안 hash: `ce6b426e23589c314e92cc4e2128027b13a3bf19f18ca05fc06481df424961a9`

### 실제 최종 답안
```json
{
  "answer_text": "경상북도 울릉도, 경상북도 울릉이도, 경상북도 울릉이도, 경상북도 울릉이도, 경상북도 울릉이도",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q4_01.json)
```json
{
  "case_id": "PILOT_Q4_01",
  "required_task_obligations": [
    "resolve_approved_anchor",
    "search_fixed_gazetteer_5000m",
    "report_source_bound_objects"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_139",
  "answer_sha256": "ce6b426e23589c314e92cc4e2128027b13a3bf19f18ca05fc06481df424961a9",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "227244882fccc56b25d5011c4e434d0f0066a71445288f79330b78ebec215f72",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_138 — 독도 부근에서 가장 가까운 등대를 찾아줘.

답안 hash: `f6a24e48570bd6e02be40eb03437039815a84db9400a247d0e32c93b992df949`

### 실제 최종 답안
```json
{
  "answer_text": "The nearest lighthouse to Dokdo is located in Busan, Korea.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "validator_blockers": [
    "BLOCKED_CONFIG: explicit research source required",
    "BLOCKED_CONFIG: unsupported operation: None"
  ],
  "status": "BLOCKED_CONFIG",
  "execution_status": "BLOCKED_CONFIG",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q3_01.json)
```json
{
  "case_id": "PILOT_Q3_01",
  "required_task_obligations": [
    "resolve_reference",
    "resolve_lighthouse_target_conditions",
    "verify_coverage",
    "find_nearest",
    "report_objects_or_unresolved_reason"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "User-approved source-bound safe abstention; document explanations are separately evaluated optional partial output."
  ],
  "expected_spatial_behavior": {
    "accepted_states": [
      "BLOCKED_DATA",
      "DATA_OUT_OF_SCOPE"
    ],
    "required_disclosure": "Current connected snapshot cannot determine the answer for the requested spatial extent",
    "per_target": {
      "Lighthouse": {
        "status": "BLOCKED_DATA",
        "object_ids": null
      }
    },
    "empty_result_as_answer_forbidden": true,
    "claim_spatial_success_forbidden": true
  }
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_138",
  "answer_sha256": "f6a24e48570bd6e02be40eb03437039815a84db9400a247d0e32c93b992df949",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "abe20bd58e3d6113867ec15f313e4bec8d600be33d1af6a0b66cbbd87a7d357d",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_137 — 등대와 부표를 구분하는 S-101 근거를 알려줘.

답안 hash: `6fb21b7b7e9a3032ca8bbf3914c86afb4353f17cc041fc526d24cbb4b3d8c23a`

### 실제 최종 답안
```json
{
  "answer_text": "等明灯和浮标在S-101数据库中可以区分。",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "validator_blockers": [
    "BLOCKED_DATA: public catalogue document evidence unavailable",
    "BLOCKED_DATA: public catalogue document evidence unavailable"
  ],
  "status": "BLOCKED_DATA",
  "execution_status": "BLOCKED_DATA",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q6_02.json)
```json
{
  "case_id": "PILOT_Q6_02",
  "required_task_obligations": [
    "compare_fixed_structure_and_floating_aid_models",
    "cite_comparison_evidence"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "single_Lighthouse_feature_assertion",
    "global_colour_codes_for_feature_binding"
  ],
  "scope_notes": [
    "Landmark/Building describe conditional structure alternatives; LightAllAround/LightSectored describe light alternatives. Listing these for explanation does not assert all must exist in one physical lighthouse.",
    "Bounded comparison: LateralBuoy is the explicitly selected representative floating-aid feature; no claim to exhaustively describe every buoy class. Compare with conditional structure/light models."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_137",
  "answer_sha256": "6fb21b7b7e9a3032ca8bbf3914c86afb4353f17cc041fc526d24cbb4b3d8c23a",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "3b34fe2ce027e6bf900d915deb84b5ce242b29624275505ec945364a1a833776",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_136 — What is a wreck in S-101?

답안 hash: `060436314c135e68158c4ef2a55e70bf1fc98e20a3b8c7ae2c967f417f61e819`

### 실제 최종 답안
```json
{
  "answer_text": "A wreck in S-101 refers to a shipwreck or wreckage found within the S-101 area. This area is part of the S-101 research snapshot, which includes the Busan research subset. The wreck is not covered by the Busan regional aids, so it is not included in the coverage.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "status": "NEEDS_USER_INPUT",
  "clarification_request": "A wreck in S-101 refers to a shipwreck or wreckage found within the S-101 area. This area is part of the S-101 research snapshot, which includes the Busan research subset. The wreck is not covered by the Busan regional aids, so it is not included in the coverage.",
  "execution_status": "NEEDS_USER_INPUT",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q1_03.json)
```json
{
  "case_id": "PILOT_Q1_03",
  "required_task_obligations": [
    "explain_wreck_definition"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_136",
  "answer_sha256": "060436314c135e68158c4ef2a55e70bf1fc98e20a3b8c7ae2c967f417f61e819",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "ccde804a2200bf4faaf6a3ec712ff9d4d4a781e4dac3e3c691e2a6472fe076f4",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_135 — S-101 Wreck 정의의 원문과 Feature Catalogue 출처를 알려줘.

답안 hash: `74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b`

### 실제 최종 답안
```json
null
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q6_01.json)
```json
{
  "case_id": "PILOT_Q6_01",
  "required_task_obligations": [
    "provide_wreck_definition_text",
    "cite_catalogue_edition_and_locator"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_135",
  "answer_sha256": "74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_134 — 독도 주변 반경 5km의 해양지명을 찾아줘.

답안 hash: `ce6b426e23589c314e92cc4e2128027b13a3bf19f18ca05fc06481df424961a9`

### 실제 최종 답안
```json
{
  "answer_text": "경상북도 울릉도, 경상북도 울릉이도, 경상북도 울릉이도, 경상북도 울릉이도, 경상북도 울릉이도",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q4_01.json)
```json
{
  "case_id": "PILOT_Q4_01",
  "required_task_obligations": [
    "resolve_approved_anchor",
    "search_fixed_gazetteer_5000m",
    "report_source_bound_objects"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_134",
  "answer_sha256": "ce6b426e23589c314e92cc4e2128027b13a3bf19f18ca05fc06481df424961a9",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "227244882fccc56b25d5011c4e434d0f0066a71445288f79330b78ebec215f72",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_133 — Find wrecks intersecting the selected area.

답안 hash: `f0a7e4b8dc4daf09696216288568fdf17c1294e722078daf19bc5f259f391025`

### 실제 최종 답안
```json
{
  "answer_text": "The selected area does not intersect any wrecks.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "status": "PARTIAL",
  "execution_status": "PARTIAL",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q3_03.json)
```json
{
  "case_id": "PILOT_Q3_03",
  "required_task_obligations": [
    "require_selected_aoi",
    "verify_coverage",
    "search_intersections_if_aoi_available",
    "request_aoi_when_missing"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "No selected geometry is provided by this benchmark input; an arbitrary viewport is not a substitute."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_133",
  "answer_sha256": "f0a7e4b8dc4daf09696216288568fdf17c1294e722078daf19bc5f259f391025",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "a3d30e6ebf18442b800e4b84a9530234080ecd5ce6be7dd584c086bbd0807cd1",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_132 — 부산항 주변 2km의 정박지와 제한구역을 찾아 비교해줘.

답안 hash: `f0633f53f0dcdb2d1a20ddd59e9e0f09835e6bed8e616e0dca86b50d017038f2`

### 실제 최종 답안
```json
{
  "answer_text": "The search results for 'port', 'dock', and 'shipyard' within 2km of Busan Port are as follows:",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "document_answers": [
    {
      "features": [],
      "attribute_bindings": [],
      "evidence": {
        "edition": "2.0.0",
        "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
        "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
        "locators": [],
        "claim_source_links": []
      }
    },
    {
      "features": [],
      "attribute_bindings": [],
      "evidence": {
        "edition": "2.0.0",
        "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
        "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
        "locators": [],
        "claim_source_links": []
      }
    },
    {
      "features": [],
      "attribute_bindings": [],
      "evidence": {
        "edition": "2.0.0",
        "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
        "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
        "locators": [],
        "claim_source_links": []
      }
    }
  ],
  "status": "COMPLETED",
  "execution_status": "COMPLETED",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q5_02.json)
```json
{
  "case_id": "PILOT_Q5_02",
  "required_task_obligations": [
    "resolve_reference",
    "verify_both_target_coverages",
    "search_both_targets_2000m",
    "compare_target_results",
    "disclose_subset_limitations"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "Object IDs refer to frozen snapshot records, not deduplicated physical facilities or the whole legal port."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_132",
  "answer_sha256": "f0633f53f0dcdb2d1a20ddd59e9e0f09835e6bed8e616e0dca86b50d017038f2",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "7f453b95651075baccdcbe45b5ef6b695165123718a44cd141ee64db305d9c23",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_131 — Find marine place names within 5 km of Dokdo.

답안 hash: `e4c3a2cfb61f4bc49b0e1bba2fd444e7737b5a88d22fe8aa76e584b023a2313b`

### 실제 최종 답안
```json
{
  "answer_text": "Marine place names within 5 km of Dokdo: [marine place names]",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "validator_blockers": [
    "BLOCKED_DATA: public catalogue document evidence unavailable"
  ],
  "status": "BLOCKED_DATA",
  "execution_status": "BLOCKED_DATA",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q4_03.json)
```json
{
  "case_id": "PILOT_Q4_03",
  "required_task_obligations": [
    "resolve_approved_anchor",
    "search_fixed_gazetteer_5000m",
    "report_source_bound_objects"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_131",
  "answer_sha256": "e4c3a2cfb61f4bc49b0e1bba2fd444e7737b5a88d22fe8aa76e584b023a2313b",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "231c956d4332c1e270dd656ae94819d035c634810e2a58e8861ec7419580985d",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_130 — 부산항 주변 2km의 정박지와 제한구역을 찾아 비교해줘.

답안 hash: `c9ad70755cc8273fff56ccb98f159a507f106711d3a47ac48ea9f550bf3a6d1a`

### 실제 최종 답안
```json
{
  "answer_text": "The search results for 'port', 'dock', and 'shipyard' within 2km of Busan Port are as follows:",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "validator_blockers": [
    "BLOCKED_DATA: public catalogue document evidence unavailable",
    "BLOCKED_DATA: public catalogue document evidence unavailable",
    "BLOCKED_DATA: public catalogue document evidence unavailable"
  ],
  "status": "BLOCKED_DATA",
  "execution_status": "BLOCKED_DATA",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q5_02.json)
```json
{
  "case_id": "PILOT_Q5_02",
  "required_task_obligations": [
    "resolve_reference",
    "verify_both_target_coverages",
    "search_both_targets_2000m",
    "compare_target_results",
    "disclose_subset_limitations"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "Object IDs refer to frozen snapshot records, not deduplicated physical facilities or the whole legal port."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_130",
  "answer_sha256": "c9ad70755cc8273fff56ccb98f159a507f106711d3a47ac48ea9f550bf3a6d1a",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "f89dce42f51d9d2e1d1cbb5bfe1a9238fbc025d0cc7193da3ca86f55af5660c4",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_129 — S-101 등대의 색상 속성과 허용 값을 알려줘.

답안 hash: `921857b4433276a9a8837c4eb9cbeab23f6a6f583e849c32bbd9b956288626e6`

### 실제 최종 답안
```json
{
  "answer_text": "등대 색상: 주로 노란색이며, 일부는 검정색이나 흰색입니다. 허용 레이즈: 1000m 이내입니다.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "document_answer": {
    "features": [],
    "attribute_bindings": [],
    "evidence": {
      "edition": "2.0.0",
      "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
      "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
      "locators": [],
      "claim_source_links": []
    }
  },
  "status": "COMPLETED",
  "execution_status": "COMPLETED",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q2_01.json)
```json
{
  "case_id": "PILOT_Q2_01",
  "required_task_obligations": [
    "distinguish_structure_and_light_colour",
    "explain_feature_bound_permitted_values"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "single_Lighthouse_feature_assertion",
    "global_colour_codes_for_feature_binding"
  ],
  "scope_notes": [
    "Landmark/Building describe conditional structure alternatives; LightAllAround/LightSectored describe light alternatives. Listing these for explanation does not assert all must exist in one physical lighthouse."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_129",
  "answer_sha256": "921857b4433276a9a8837c4eb9cbeab23f6a6f583e849c32bbd9b956288626e6",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "1f6533698bdc721832f3249e84e12c8bf21150f2867bd17eb9a54a74597a14cc",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_128 — 독도 부근에서 가장 가까운 등대를 찾아줘.

답안 hash: `f6a24e48570bd6e02be40eb03437039815a84db9400a247d0e32c93b992df949`

### 실제 최종 답안
```json
{
  "answer_text": "The nearest lighthouse to Dokdo is located in Busan, Korea.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "validator_blockers": [
    "BLOCKED_CONFIG: explicit research source required",
    "BLOCKED_CONFIG: unsupported operation: None"
  ],
  "status": "BLOCKED_CONFIG",
  "execution_status": "BLOCKED_CONFIG",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q3_01.json)
```json
{
  "case_id": "PILOT_Q3_01",
  "required_task_obligations": [
    "resolve_reference",
    "resolve_lighthouse_target_conditions",
    "verify_coverage",
    "find_nearest",
    "report_objects_or_unresolved_reason"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "User-approved source-bound safe abstention; document explanations are separately evaluated optional partial output."
  ],
  "expected_spatial_behavior": {
    "accepted_states": [
      "BLOCKED_DATA",
      "DATA_OUT_OF_SCOPE"
    ],
    "required_disclosure": "Current connected snapshot cannot determine the answer for the requested spatial extent",
    "per_target": {
      "Lighthouse": {
        "status": "BLOCKED_DATA",
        "object_ids": null
      }
    },
    "empty_result_as_answer_forbidden": true,
    "claim_spatial_success_forbidden": true
  }
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_128",
  "answer_sha256": "f6a24e48570bd6e02be40eb03437039815a84db9400a247d0e32c93b992df949",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "abe20bd58e3d6113867ec15f313e4bec8d600be33d1af6a0b66cbbd87a7d357d",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_127 — Find marine place names within 5 km of Dokdo.

답안 hash: `0ae29b4c5edc5f9a02df50c3e86c1347d971958d95886282415dfabe0f29ba0f`

### 실제 최종 답안
```json
{
  "answer_text": "Marine place names within 5 km of Dokdo: [marine place names]",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "document_answer": {
    "features": [],
    "attribute_bindings": [],
    "evidence": {
      "edition": "2.0.0",
      "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
      "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
      "locators": [],
      "claim_source_links": []
    }
  },
  "status": "COMPLETED",
  "execution_status": "COMPLETED",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q4_03.json)
```json
{
  "case_id": "PILOT_Q4_03",
  "required_task_obligations": [
    "resolve_approved_anchor",
    "search_fixed_gazetteer_5000m",
    "report_source_bound_objects"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_127",
  "answer_sha256": "0ae29b4c5edc5f9a02df50c3e86c1347d971958d95886282415dfabe0f29ba0f",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "9b953ca0c4edf6f26dc622871131b10231f4dd1bafc63e6558ba2c3c4e2bf9e0",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_126 — Find wrecks within 5 km of Dokdo and explain their S-101 attributes.

답안 hash: `33a552d37c04de0547beebc1d936215dbc3b5dcb75d9df13ef6f2dfb215da44c`

### 실제 최종 답안
```json
{
  "answer_text": "The wrecks within 5 km of Dokdo are not found in the S-101 feature catalogue.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "document_answer": {
    "features": [],
    "attribute_bindings": [],
    "evidence": {
      "edition": "2.0.0",
      "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
      "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
      "locators": [],
      "claim_source_links": []
    }
  },
  "status": "COMPLETED",
  "execution_status": "COMPLETED",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q5_03.json)
```json
{
  "case_id": "PILOT_Q5_03",
  "required_task_obligations": [
    "resolve_reference",
    "verify_coverage",
    "search_wrecks_5000m",
    "explain_s101_attributes",
    "distinguish_object_values_from_standard_attributes",
    "separate_partial_document_answer"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "User-approved source-bound safe abstention; document explanations are separately evaluated optional partial output."
  ],
  "expected_spatial_behavior": {
    "accepted_states": [
      "BLOCKED_DATA",
      "DATA_OUT_OF_SCOPE"
    ],
    "required_disclosure": "Current connected snapshot cannot determine the answer for the requested spatial extent",
    "per_target": {
      "Wreck": {
        "status": "BLOCKED_DATA",
        "object_ids": null
      }
    },
    "empty_result_as_answer_forbidden": true,
    "claim_spatial_success_forbidden": true
  }
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_126",
  "answer_sha256": "33a552d37c04de0547beebc1d936215dbc3b5dcb75d9df13ef6f2dfb215da44c",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "7b1799060b9287086b0dc1ccacdfebb777ff6a4c44ce1beabef4dae493815b77",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_125 — Which attributes describe a Wreck in S-101?

답안 hash: `671e8d4c7f67eb528868b4dead4fef5b71e169f3302d732d7255f665b2e5d2d1`

### 실제 최종 답안
```json
{
  "answer_text": "A Wreck in S-101 is located within a 5,000-meter radius of the S-101 boundary, considering the EPSG:4326 coordinate system.",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q2_03.json)
```json
{
  "case_id": "PILOT_Q2_03",
  "required_task_obligations": [
    "explain_wreck_attribute_bindings"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_125",
  "answer_sha256": "671e8d4c7f67eb528868b4dead4fef5b71e169f3302d732d7255f665b2e5d2d1",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "c4c242c66670b18151907f6f1e6430859569b3d1d7b91d19aeffc167ee8da9cf",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_124 — 제한구역의 제한 종류는 어떤 코드로 표현해?

답안 hash: `a2cd26034b74d274b739578aa229e83799a42cd3301ab9c6662cf3dd08c3f079`

### 실제 최종 답안
```json
{
  "answer_text": "제한구역의 제한 종류는 '제한구역'이라는 공식적인 문서 코드로 표현됩니다.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "validator_blockers": [
    "BLOCKED_DATA: public catalogue document evidence unavailable"
  ],
  "status": "BLOCKED_DATA",
  "execution_status": "BLOCKED_DATA",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q2_02.json)
```json
{
  "case_id": "PILOT_Q2_02",
  "required_task_obligations": [
    "distinguish_restriction_and_area_category",
    "explain_restriction_codes"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": [
    "Explain restriction codes separately from categoryOfRestrictedArea. RequiredArea alternatives from another FC edition are not substitutes for FC 2.0.0 RestrictedArea."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_124",
  "answer_sha256": "a2cd26034b74d274b739578aa229e83799a42cd3301ab9c6662cf3dd08c3f079",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "fb3f2b4509ab7587b17a65afe32feeb5af99dd4fff0dd8017577d56d942f9c39",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_123 — 제한구역의 제한 종류는 어떤 코드로 표현해?

답안 hash: `66c82e651dea1ff6909c93e264a49a64f6fd34306fe74d5dd958ae8637cd3f36`

### 실제 최종 답안
```json
{
  "answer_text": "The restricted type is represented by the code 's101'.",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q2_02.json)
```json
{
  "case_id": "PILOT_Q2_02",
  "required_task_obligations": [
    "distinguish_restriction_and_area_category",
    "explain_restriction_codes"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": [
    "Explain restriction codes separately from categoryOfRestrictedArea. RequiredArea alternatives from another FC edition are not substitutes for FC 2.0.0 RestrictedArea."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_123",
  "answer_sha256": "66c82e651dea1ff6909c93e264a49a64f6fd34306fe74d5dd958ae8637cd3f36",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "9200d8e6678e7d9f4dc9c6a5125d2a0084a629d7600df380fbc2ca100b944080",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_122 — 등대의 S-101 객체 유형과 정의를 알려줘.

답안 hash: `b3a62da1b7319f5be0a16d34fff0967fc95cedb5438fc8a4a97c698c0652975c`

### 실제 최종 답안
```json
{
  "answer_text": "등대는 S-101 객체 중 하나입니다. 이 객체는 등대의 정의와 유형을 나타냅니다. S-101는 등대의 공통적인 객체 코드입니다.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "validator_blockers": [
    "BLOCKED_DATA: public catalogue document evidence unavailable"
  ],
  "status": "BLOCKED_DATA",
  "execution_status": "BLOCKED_DATA",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q1_01.json)
```json
{
  "case_id": "PILOT_Q1_01",
  "required_task_obligations": [
    "explain_structure_and_light_distinction",
    "explain_conditional_feature_mapping"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "single_Lighthouse_feature_assertion",
    "global_colour_codes_for_feature_binding"
  ],
  "scope_notes": [
    "Landmark/Building describe conditional structure alternatives; LightAllAround/LightSectored describe light alternatives. Listing these for explanation does not assert all must exist in one physical lighthouse."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_122",
  "answer_sha256": "b3a62da1b7319f5be0a16d34fff0967fc95cedb5438fc8a4a97c698c0652975c",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "7b8cc2c44109400043db40af0794ebb941604c3af532d393dc62359f4e20760a",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_121 — 독도 부근에서 가장 가까운 등대를 찾아줘.

답안 hash: `0a982fe1daa1bb7b56f1e74892a6f1c1c6ce36587f1e67bdfda04f1a6695cd05`

### 실제 최종 답안
```json
{
  "answer_text": "The closest lighthouse to Dokdo is located at the Dokdo Lighthouse.",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q3_01.json)
```json
{
  "case_id": "PILOT_Q3_01",
  "required_task_obligations": [
    "resolve_reference",
    "resolve_lighthouse_target_conditions",
    "verify_coverage",
    "find_nearest",
    "report_objects_or_unresolved_reason"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "User-approved source-bound safe abstention; document explanations are separately evaluated optional partial output."
  ],
  "expected_spatial_behavior": {
    "accepted_states": [
      "BLOCKED_DATA",
      "DATA_OUT_OF_SCOPE"
    ],
    "required_disclosure": "Current connected snapshot cannot determine the answer for the requested spatial extent",
    "per_target": {
      "Lighthouse": {
        "status": "BLOCKED_DATA",
        "object_ids": null
      }
    },
    "empty_result_as_answer_forbidden": true,
    "claim_spatial_success_forbidden": true
  }
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_121",
  "answer_sha256": "0a982fe1daa1bb7b56f1e74892a6f1c1c6ce36587f1e67bdfda04f1a6695cd05",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "db28522bafed7009b9e01e233b90beb2c30e10e0c9a2fdf8be50f0996de0f9a5",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_120 — 부산항 영역 안의 정박지를 찾아줘.

답안 hash: `acbfbbe8bba7382fec810cf38c052ae00ff8bd6e3c421a83b4e8b85f4567dd1a`

### 실제 최종 답안
```json
{
  "answer_text": "在距离'부산항'1公里范围内的泊位。",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q3_02.json)
```json
{
  "case_id": "PILOT_Q3_02",
  "required_task_obligations": [
    "resolve_official_port_polygon",
    "verify_coverage",
    "search_within_polygon",
    "report_objects_or_unresolved_reason"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "Object IDs refer to frozen snapshot records, not deduplicated physical facilities or the whole legal port."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_120",
  "answer_sha256": "acbfbbe8bba7382fec810cf38c052ae00ff8bd6e3c421a83b4e8b85f4567dd1a",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "2a83281c2f3dde9028915926f5f253ccb333f3c35c0c9f7e2f30b6780b517f9a",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_119 — 독도 주변 반경 5km의 해양지명을 찾아줘.

답안 hash: `cf33969e5e0bd569b77d7bcd93b54976b8a7e82c997878db71f2f282571eb50c`

### 실제 최종 답안
```json
{
  "answer_text": "Dokdo 주변 반경 5km의 해양지명은 '독도'입니다.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "validator_blockers": [
    "BLOCKED_DATA: public catalogue document evidence unavailable"
  ],
  "status": "BLOCKED_DATA",
  "execution_status": "BLOCKED_DATA",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q4_01.json)
```json
{
  "case_id": "PILOT_Q4_01",
  "required_task_obligations": [
    "resolve_approved_anchor",
    "search_fixed_gazetteer_5000m",
    "report_source_bound_objects"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_119",
  "answer_sha256": "cf33969e5e0bd569b77d7bcd93b54976b8a7e82c997878db71f2f282571eb50c",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "ed65dafbdfc72a4aac6e2ee1322c0f8cdb7d5812a7792f876a1b5125d4f41b59",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_118 — Find marine place names within 5 km of Dokdo.

답안 hash: `06d005a8bceb7ad53ef6c8645c156769cdd86976be12ce008ef739fe5c3b53da`

### 실제 최종 답안
```json
{
  "answer_text": "Marine place names within 5 km of Dokdo include: ",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q4_03.json)
```json
{
  "case_id": "PILOT_Q4_03",
  "required_task_obligations": [
    "resolve_approved_anchor",
    "search_fixed_gazetteer_5000m",
    "report_source_bound_objects"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_118",
  "answer_sha256": "06d005a8bceb7ad53ef6c8645c156769cdd86976be12ce008ef739fe5c3b53da",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "2e15336412a9dc7da26840f2535629710b97efd684f8204358cd43586850f18b",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_117 — S-101 Wreck 정의의 원문과 Feature Catalogue 출처를 알려줘.

답안 hash: `74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b`

### 실제 최종 답안
```json
null
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q6_01.json)
```json
{
  "case_id": "PILOT_Q6_01",
  "required_task_obligations": [
    "provide_wreck_definition_text",
    "cite_catalogue_edition_and_locator"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_117",
  "answer_sha256": "74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_116 — Find wrecks intersecting the selected area.

답안 hash: `5b6737fce6f9318852fff55fced7f0838d46b084a3ac4b1d7e077c396f04ac26`

### 실제 최종 답안
```json
{
  "answer_text": "The wrecks intersecting the selected area are classified as 'Non-Dangerous Wreck' with a value of 1.",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q3_03.json)
```json
{
  "case_id": "PILOT_Q3_03",
  "required_task_obligations": [
    "require_selected_aoi",
    "verify_coverage",
    "search_intersections_if_aoi_available",
    "request_aoi_when_missing"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "No selected geometry is provided by this benchmark input; an arbitrary viewport is not a substitute."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_116",
  "answer_sha256": "5b6737fce6f9318852fff55fced7f0838d46b084a3ac4b1d7e077c396f04ac26",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "9090122f80ead9630cc3b50e76e65d3fc9a5f3e84b18a929880d64dc849b0707",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_115 — 독도 주변 반경 5000m의 해양지명을 찾아줘.

답안 hash: `6877ef6e5fe6d1048327f22010d3c697a3148ac2b2b42dfbc86d12719189dd3e`

### 실제 최종 답안
```json
{
  "answer_text": "독도 주변 반경 5000m의 해양지명은 다음과 같습니다:\n1. 독도\n2. 독도 남쪽 해안\n3. 독도 서쪽 해안\n4. 독도 동쪽 해안\n5. 독도 북쪽 해안",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q4_02.json)
```json
{
  "case_id": "PILOT_Q4_02",
  "required_task_obligations": [
    "resolve_approved_anchor",
    "search_fixed_gazetteer_5000m",
    "report_source_bound_objects"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_115",
  "answer_sha256": "6877ef6e5fe6d1048327f22010d3c697a3148ac2b2b42dfbc86d12719189dd3e",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "3fee1128039fac1f9b965f054f8981475f3518005c3545fcc48c270b911c61d5",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_114 — 제한구역의 제한 종류는 어떤 코드로 표현해?

답안 hash: `66c82e651dea1ff6909c93e264a49a64f6fd34306fe74d5dd958ae8637cd3f36`

### 실제 최종 답안
```json
{
  "answer_text": "The restricted type is represented by the code 's101'.",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q2_02.json)
```json
{
  "case_id": "PILOT_Q2_02",
  "required_task_obligations": [
    "distinguish_restriction_and_area_category",
    "explain_restriction_codes"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": [
    "Explain restriction codes separately from categoryOfRestrictedArea. RequiredArea alternatives from another FC edition are not substitutes for FC 2.0.0 RestrictedArea."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_114",
  "answer_sha256": "66c82e651dea1ff6909c93e264a49a64f6fd34306fe74d5dd958ae8637cd3f36",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "9200d8e6678e7d9f4dc9c6a5125d2a0084a629d7600df380fbc2ca100b944080",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_113 — 부산항 영역 안의 정박지를 찾아줘.

답안 hash: `cf8e40cfd9b67a334f4dbd3b6f9a525cca5d076876c94b1ea9f404d03f29c192`

### 실제 최종 답안
```json
{
  "answer_text": "The anchorage area within 1000 meters of Busan Port.",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q3_02.json)
```json
{
  "case_id": "PILOT_Q3_02",
  "required_task_obligations": [
    "resolve_official_port_polygon",
    "verify_coverage",
    "search_within_polygon",
    "report_objects_or_unresolved_reason"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "Object IDs refer to frozen snapshot records, not deduplicated physical facilities or the whole legal port."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_113",
  "answer_sha256": "cf8e40cfd9b67a334f4dbd3b6f9a525cca5d076876c94b1ea9f404d03f29c192",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "80b5bc6d111c9cc5ea4cd1525a2569c8f84c20ff3d36b05a8a6933070dfe303c",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_112 — 독도 주변 5km의 등대와 난파선을 찾아 각각의 근거를 알려줘.

답안 hash: `5305a8293a9cb2f117f259f0c53a0c8e2f3282a21adc9ac7dd4cabe48be3112d`

### 실제 최종 답안
```json
{
  "document_answer": {
    "features": [],
    "attribute_bindings": []
  },
  "search_executed": false,
  "execution_status": "BLOCKED",
  "source_coverage": {},
  "per_task_status": {},
  "mapping_provenance": {
    "version": "emitted_output_v1",
    "root": "final_state.final_dict",
    "retrieved_text_used_as_answer": false,
    "reference_used_for_mapping": false,
    "structured_document_answer_present": false
  },
  "status": "BLOCKED",
  "blocker": "UNSUPPORTED_COMPOSITE_TASK",
  "clarification_request": [],
  "answer_text": "요청한 여러 대상의 검색·비교를 모두 수행하는 실행 경로가 아직 지원되지 않습니다. 일부 대상만 조회하지 않았습니다."
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q5_01.json)
```json
{
  "case_id": "PILOT_Q5_01",
  "required_task_obligations": [
    "resolve_reference",
    "resolve_lighthouse_target_conditions",
    "verify_both_target_coverages",
    "search_both_targets_5000m",
    "provide_per_target_evidence",
    "separate_partial_document_answer"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "User-approved source-bound safe abstention; document explanations are separately evaluated optional partial output."
  ],
  "expected_spatial_behavior": {
    "accepted_states": [
      "BLOCKED_DATA",
      "DATA_OUT_OF_SCOPE"
    ],
    "required_disclosure": "Current connected snapshot cannot determine the answer for the requested spatial extent",
    "per_target": {
      "Lighthouse": {
        "status": "BLOCKED_DATA",
        "object_ids": null
      },
      "Wreck": {
        "status": "BLOCKED_DATA",
        "object_ids": null
      }
    },
    "empty_result_as_answer_forbidden": true,
    "claim_spatial_success_forbidden": true
  }
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_112",
  "answer_sha256": "5305a8293a9cb2f117f259f0c53a0c8e2f3282a21adc9ac7dd4cabe48be3112d",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "4f6b48d26d5abfe5b733929c616a6509f95b2cc4cf476f6c1d447626ebbdc0c5",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_111 — S-101 Wreck 정의의 원문과 Feature Catalogue 출처를 알려줘.

답안 hash: `8c1fa20e7c19d703ff4473e9e5705a4468e84d6302ea6dd6f679b5987345f1c6`

### 실제 최종 답안
```json
{
  "answer_text": "The wrecked or ruined ship is classified as 'Non-Dangerous Wreck' based on the provided definition. This classification is determined by the 'Category of Wreck' feature, which is defined in the Feature Catalogue. The classification is based on the 'defaultClearanceDepth' and 'expositionOfSounding' features, which provide depth values and relationships to the surrounding area.",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q6_01.json)
```json
{
  "case_id": "PILOT_Q6_01",
  "required_task_obligations": [
    "provide_wreck_definition_text",
    "cite_catalogue_edition_and_locator"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_111",
  "answer_sha256": "8c1fa20e7c19d703ff4473e9e5705a4468e84d6302ea6dd6f679b5987345f1c6",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "4c2a8c50c015f52f0a690178807a25a3efadd0de4bda951b42b086d3ddfedf5c",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_110 — Find wrecks within 5 km of Dokdo and explain their S-101 attributes.

답안 hash: `5fe54020397d503cedaebeea939966fa27e9381c55704cf282d50eb251aac4ca`

### 실제 최종 답안
```json
{
  "document_answer": {
    "features": [],
    "attribute_bindings": []
  },
  "search_executed": null,
  "execution_status": "BLOCKED",
  "source_coverage": {},
  "per_task_status": {},
  "mapping_provenance": {
    "version": "emitted_output_v1",
    "root": "final_state.final_dict",
    "retrieved_text_used_as_answer": false,
    "reference_used_for_mapping": false,
    "structured_document_answer_present": false
  },
  "status": "BLOCKED",
  "blocker": "DATA_COVERAGE_UNVERIFIED",
  "clarification_request": [],
  "answer_text": "현재 연결된 데이터의 공간 범위가 검증되지 않아 공간 검색을 실행하지 않았습니다."
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q5_03.json)
```json
{
  "case_id": "PILOT_Q5_03",
  "required_task_obligations": [
    "resolve_reference",
    "verify_coverage",
    "search_wrecks_5000m",
    "explain_s101_attributes",
    "distinguish_object_values_from_standard_attributes",
    "separate_partial_document_answer"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "User-approved source-bound safe abstention; document explanations are separately evaluated optional partial output."
  ],
  "expected_spatial_behavior": {
    "accepted_states": [
      "BLOCKED_DATA",
      "DATA_OUT_OF_SCOPE"
    ],
    "required_disclosure": "Current connected snapshot cannot determine the answer for the requested spatial extent",
    "per_target": {
      "Wreck": {
        "status": "BLOCKED_DATA",
        "object_ids": null
      }
    },
    "empty_result_as_answer_forbidden": true,
    "claim_spatial_success_forbidden": true
  }
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_110",
  "answer_sha256": "5fe54020397d503cedaebeea939966fa27e9381c55704cf282d50eb251aac4ca",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "4c895907cba7c8cb81fd5838c23bc2b856cfc5ef1aa45346c48f5ceb79eeca28",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_109 — S-101에서 정박지는 어떤 객체야?

답안 hash: `f2adee5da9a70e87ca1be6bae8ef00049159c784058b94fea5890538c4721862`

### 실제 최종 답안
```json
{
  "answer_text": "정박지는 'Wreck' 이라는 객체입니다.",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q1_02.json)
```json
{
  "case_id": "PILOT_Q1_02",
  "required_task_obligations": [
    "explain_anchorage_area_definition"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_109",
  "answer_sha256": "f2adee5da9a70e87ca1be6bae8ef00049159c784058b94fea5890538c4721862",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "299d286bc830ac15f77558e52d3fbeebb84c0f343632810fdcf45ffd6a08fd87",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_108 — S-101 등대의 색상 속성과 허용 값을 알려줘.

답안 hash: `e52a28ef07079ae5729d43bb78a11571c1b10b7c3d8083467b93076fa8060079`

### 실제 최종 답안
```json
{
  "document_answer": {
    "features": [],
    "attribute_bindings": []
  },
  "search_executed": null,
  "execution_status": "PARTIAL",
  "source_coverage": {},
  "per_task_status": {},
  "mapping_provenance": {
    "version": "emitted_output_v1",
    "root": "final_state.final_dict",
    "retrieved_text_used_as_answer": false,
    "reference_used_for_mapping": false,
    "structured_document_answer_present": false
  },
  "status": "PARTIAL",
  "blocker": "OUTPUT_OBLIGATIONS_UNMET",
  "clarification_request": [],
  "answer_text": "요청한 결과에 필요한 근거가 아직 부족합니다: 요청한 용어·속성과 출처가 연결된 설명 (관련 문서 검색만으로는 미충족)\n질의와 관련된 근거 문서 2건을 찾았습니다. 대표 근거는 S-101_Annex_A_DCEG_Ed_2.0.0 / page_553이며, 내용 요지는 다음과 같습니다: Data Classification and Encoding Guide 533 S-101 Annex A December 2024 Edition 2.0.0 20.12 Safe water beacon IHO Definition: SAFE WATER BEACON. A safe water beacon is used to indicate that there is navigable water around..."
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q2_01.json)
```json
{
  "case_id": "PILOT_Q2_01",
  "required_task_obligations": [
    "distinguish_structure_and_light_colour",
    "explain_feature_bound_permitted_values"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "single_Lighthouse_feature_assertion",
    "global_colour_codes_for_feature_binding"
  ],
  "scope_notes": [
    "Landmark/Building describe conditional structure alternatives; LightAllAround/LightSectored describe light alternatives. Listing these for explanation does not assert all must exist in one physical lighthouse."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_108",
  "answer_sha256": "e52a28ef07079ae5729d43bb78a11571c1b10b7c3d8083467b93076fa8060079",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "0e5459e093905e3387c7c9826f4901d827e2b021ce5bb4fa2d2be61a4cc46006",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_107 — What source supports the S-101 definition of AnchorageArea?

답안 hash: `a6934565eac04a144317a43ac96d43d767f023f6e7a95357195533549c8494f2`

### 실제 최종 답안
```json
{
  "answer_text": "The S-101 definition of AnchorageArea is supported by the source 's101_feature_catalogue_v2'.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "document_answer": {
    "features": [
      {
        "code": "AnchorageArea",
        "xml_type": "S100_FC_FeatureType",
        "definition": "An area in which vessels or seaplanes anchor or may anchor.",
        "permitted_primitives": [
          "point",
          "surface"
        ],
        "bindings": [
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "categoryOfAnchorage"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [
              "1",
              "2",
              "3",
              "5",
              "6",
              "7",
              "9",
              "10",
              "14",
              "15"
            ],
            "xml_child_index": 5
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "categoryOfCargo"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [
              "1",
              "2",
              "3",
              "4",
              "5",
              "6",
              "7",
              "8",
              "9",
              "10",
              "11",
              "12",
              "13",
              "14",
              "15"
            ],
            "xml_child_index": 6
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "featureName"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [],
            "xml_child_index": 7
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "fixedDateRange"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 8
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "interoperabilityIdentifier"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 9
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "periodicDateRange"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [],
            "xml_child_index": 10
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "restriction"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [
              "2",
              "3",
              "4",
              "5",
              "6",
              "8",
              "9",
              "10",
              "11",
              "12",
              "13",
              "15",
              "16",
              "17",
              "18",
              "19",
              "20",
              "21",
              "23",
              "24",
              "27",
              "39"
            ],
            "xml_child_index": 11
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "status"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [
              "1",
              "2",
              "3",
              "5",
              "6",
              "7",
              "8",
              "9",
              "14"
            ],
            "xml_child_index": 12
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "vesselSpeedLimit"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [],
            "xml_child_index": 13
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "scaleMinimum"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 14
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "information"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [],
            "xml_child_index": 15
          },
          {
            "kind": "informationBinding",
            "references": [
              {
                "type": "association",
                "ref": "AdditionalInformation"
              },
              {
                "type": "role",
                "ref": "theInformation"
              },
              {
                "type": "informationType",
                "ref": "ContactDetails"
              },
              {
                "type": "informationType",
                "ref": "NauticalInformation"
              },
              {
                "type": "informationType",
                "ref": "NonStandardWorkingDay"
              },
              {
                "type": "informationType",
                "ref": "ServiceHours"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 16
          },
          {
            "kind": "featureBinding",
            "references": [
              {
                "type": "association",
                "ref": "UpdatedInformation"
              },
              {
                "type": "role",
                "ref": "theUpdate"
              },
              {
                "type": "featureType",
                "ref": "UpdateInformation"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [],
            "xml_child_index": 18
          },
          {
            "kind": "featureBinding",
            "references": [
              {
                "type": "association",
                "ref": "TextAssociation"
              },
              {
                "type": "role",
                "ref": "theCartographicText"
              },
              {
                "type": "featureType",
                "ref": "TextPlacement"
              }
            ],
            "lower": "0",
            "upper": "2",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 19
          }
        ],
        "listed_values": [],
        "version": "2.0.0",
        "source_status": "VERIFIED_XML_EXTRACTION",
        "source_path": "D:\\An_GeoLLM\\outputs\\staging\\s101_feature_catalogue_2_0_0\\S-101\\CATALOGUES\\101_Feature_Catalogue_2.0.0.xml",
        "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "parsed_locator": "/features/126",
        "definition_sha256": "753f012b09c246632a2119c4bbb9faa77ccf966debb2b48d33c26b5c72799a31",
        "xml_element_serialized_sha256": "39334abca32051a75717cd5a450f95388705644972727ac611e4cec8eb1fae9d",
        "element_hash_serialization": "xml.etree.ElementTree serialization; not a raw byte slice"
      }
    ],
    "attribute_bindings": [
      {
        "owner": "AnchorageArea",
        "attribute": "categoryOfAnchorage",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [
          "1",
          "2",
          "3",
          "5",
          "6",
          "7",
          "9",
          "10",
          "14",
          "15"
        ],
        "attribute_definition": "Classification of an area where different use types of vessel can remain static.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Unrestricted Anchorage",
            "definition": "An area in which vessels anchor or may anchor."
          },
          {
            "value": "2",
            "label": "Deep Water Anchorage",
            "definition": "An area in which vessels of deep draught anchor or may anchor."
          },
          {
            "value": "3",
            "label": "Tanker Anchorage",
            "definition": "An area in which tankers anchor or may anchor."
          },
          {
            "value": "5",
            "label": "Quarantine Anchorage",
            "definition": "An area where a vessel anchors when satisfying quarantine regulations."
          },
          {
            "value": "6",
            "label": "Seaplane Anchorage",
            "definition": "An area in which seaplanes anchor or may anchor."
          },
          {
            "value": "7",
            "label": "Small Craft Anchorage",
            "definition": "An area in which yachts and small boats anchor or may anchor."
          },
          {
            "value": "9",
            "label": "Anchorage for Periods Up To 24 Hours",
            "definition": "An area in which vessels anchor or may anchor for periods of up to 24 hours."
          },
          {
            "value": "10",
            "label": "Anchorage for a Limited Period of Time",
            "definition": "An area in which vessels may anchor for a period of time not to exceed a specific limit."
          },
          {
            "value": "14",
            "label": "Waiting Anchorage",
            "definition": "An area in which vessels anchor or may anchor while waiting, for example, for access to a port or berth."
          },
          {
            "value": "15",
            "label": "Reported Anchorage",
            "definition": "A location not defined by a regulatory authority that has been reported to be suitable and safe for anchoring."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='categoryOfAnchorage']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "categoryOfCargo",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [
          "1",
          "2",
          "3",
          "4",
          "5",
          "6",
          "7",
          "8",
          "9",
          "10",
          "11",
          "12",
          "13",
          "14",
          "15"
        ],
        "attribute_definition": "Classification of the different types of cargo that a ship may be carrying.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Bulk",
            "definition": "Unpacked homogenous cargo poured loose in a certain space of a vessel, for example oil or grain."
          },
          {
            "value": "2",
            "label": "Container",
            "definition": "One of a number of standard sized cargo carrying units, secured using standard corner attachments and bar."
          },
          {
            "value": "3",
            "label": "General",
            "definition": "Break bulk cargo normally loaded by crane."
          },
          {
            "value": "4",
            "label": "Liquid",
            "definition": "Any cargo loaded by pipeline."
          },
          {
            "value": "5",
            "label": "Passenger",
            "definition": "A fee paying traveller."
          },
          {
            "value": "6",
            "label": "Livestock",
            "definition": "Live animals carried in bulk."
          },
          {
            "value": "7",
            "label": "Dangerous or Hazardous",
            "definition": "Dangerous or hazardous cargo as described by the IMO International Maritime Dangerous Goods code."
          },
          {
            "value": "8",
            "label": "Heavy Lift",
            "definition": "Indivisible heavy items of weight generally over 100 tons, and width or height greater than 100 metres."
          },
          {
            "value": "9",
            "label": "Ballast",
            "definition": "Material carried by a ship to ensure its stability."
          },
          {
            "value": "10",
            "label": "Dry Bulk Cargo",
            "definition": "Commodity cargo that is transported unpackaged in large quantities. These types of goods usually need to be kept dry during the whole transportation period."
          },
          {
            "value": "11",
            "label": "Liquid Bulk Cargo",
            "definition": "Liquids or gases that are transported in bulk and carried unpackaged."
          },
          {
            "value": "12",
            "label": "Reefer Container Cargo",
            "definition": "Cargo transported in refrigerated containers, generally perishable commodities which require temperature-controlled transportation, such as fruit, meat, fish, vegetables, dairy products and other foods."
          },
          {
            "value": "13",
            "label": "Ro-Ro Cargo",
            "definition": "Wheeled cargo, such as cars, busses, trucks, agricultural vehicles and cranes, that are driven on and off the ship on their own wheels or using a platform vehicle, such as a self-propelled modular transporter."
          },
          {
            "value": "14",
            "label": "Project Cargo",
            "definition": "Project cargo is a term used to broadly describe the national or international transportation of large, heavy, high value, or critical (to the project they are intended for) pieces of equipment. Also commonly referred to as heavy lift, this includes shipments made of various components which need disassembly for shipment and reassembly after delivery."
          },
          {
            "value": "15",
            "label": "Break Bulk Cargo",
            "definition": "Goods that are stowed on board ship in individually counted units, and not in intermodal containers nor in bulk as with oil or grain."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='categoryOfCargo']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "featureName",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [],
        "attribute_definition": "Provides the name of an entity, defines the national language of the name, and provides the option to display the name at various system display settings.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='featureName']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "fixedDateRange",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "An active period of a single fixed event or occurrence, as the date range between discrete start and end dates.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='fixedDateRange']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "interoperabilityIdentifier",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "A common unique identifier for entities which describe a single real-world feature, and which is used to identify instances of the feature in end-user systems where the feature may be included in multiple data product types.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='interoperabilityIdentifier']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "periodicDateRange",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [],
        "attribute_definition": "The active period of a recurring event or occurrence.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='periodicDateRange']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "restriction",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [
          "2",
          "3",
          "4",
          "5",
          "6",
          "8",
          "9",
          "10",
          "11",
          "12",
          "13",
          "15",
          "16",
          "17",
          "18",
          "19",
          "20",
          "21",
          "23",
          "24",
          "27",
          "39"
        ],
        "attribute_definition": "The official legal statute of each kind of restricted area.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Anchoring Prohibited",
            "definition": "An area within which anchoring is not permitted."
          },
          {
            "value": "2",
            "label": "Anchoring Restricted",
            "definition": "A specified area designated by appropriate authority, within which anchoring is restricted in accordance with certain specified conditions."
          },
          {
            "value": "3",
            "label": "Fishing Prohibited",
            "definition": "An area within which fishing is not permitted."
          },
          {
            "value": "4",
            "label": "Fishing Restricted",
            "definition": "A specified area designated by appropriate authority, within which fishing is restricted in accordance with certain specified conditions."
          },
          {
            "value": "5",
            "label": "Trawling Prohibited",
            "definition": "An area within which trawling is not permitted."
          },
          {
            "value": "6",
            "label": "Trawling Restricted",
            "definition": "A specified area designated by appropriate authority, within which trawling is restricted in accordance with certain specified conditions."
          },
          {
            "value": "7",
            "label": "Entry Prohibited",
            "definition": "An area within which navigation and/or anchoring is prohibited."
          },
          {
            "value": "8",
            "label": "Entry Restricted",
            "definition": "A specified area designated by appropriate authority, within which navigation is restricted in accordance with certain specified conditions."
          },
          {
            "value": "9",
            "label": "Dredging Prohibited",
            "definition": "An area within which dredging is not permitted."
          },
          {
            "value": "10",
            "label": "Dredging Restricted",
            "definition": "A specified area designated by appropriate authority, within which dredging is restricted in accordance with certain specified conditions."
          },
          {
            "value": "11",
            "label": "Diving Prohibited",
            "definition": "An area within which diving is not permitted."
          },
          {
            "value": "12",
            "label": "Diving Restricted",
            "definition": "A specified area designated by appropriate authority, within which diving is restricted in accordance with certain specified conditions."
          },
          {
            "value": "13",
            "label": "No Wake",
            "definition": "Mariners must adjust the speed of their vessels to reduce the wave or wash which may cause erosion or disturb moored vessels."
          },
          {
            "value": "14",
            "label": "Area To Be Avoided",
            "definition": "An IMO declared routeing measure comprising an area within defined limits in which either navigation is particularly hazardous or it is exceptionally important to avoid casualties and which should be avoided by all ships, or certain classes of ships."
          },
          {
            "value": "15",
            "label": "Construction Prohibited",
            "definition": "The erection of permanent or temporary fixed structures or artificial islands is prohibited."
          },
          {
            "value": "16",
            "label": "Discharging Prohibited",
            "definition": "An area within which discharging or dumping is prohibited."
          },
          {
            "value": "17",
            "label": "Discharging Restricted",
            "definition": "A specified area designated by an appropriate authority, within which discharging or dumping is restricted in accordance with specified conditions."
          },
          {
            "value": "18",
            "label": "Industrial or Mineral Exploration/Development Prohibited",
            "definition": "An area within which industrial or mineral exploration and development are prohibited."
          },
          {
            "value": "19",
            "label": "Industrial or Mineral Exploration/Development Restricted",
            "definition": "A specified area designated by an appropriate authority, within which industrial or mineral exploration and development is restricted in accordance with certain specified conditions."
          },
          {
            "value": "20",
            "label": "Drilling Prohibited",
            "definition": "An area within which excavating a hole on the seabed with a drill is prohibited."
          },
          {
            "value": "21",
            "label": "Drilling Restricted",
            "definition": "A specified area designated by an appropriate authority, within which excavating a hole on the seabed with a drill is restricted in accordance with certain specified conditions."
          },
          {
            "value": "22",
            "label": "Removal of Historical Artefacts Prohibited",
            "definition": "An area within which the removal of historical artefacts is prohibited."
          },
          {
            "value": "23",
            "label": "Cargo Transhipment (Lightening) Prohibited",
            "definition": "An area in which cargo transhipment (lightening) is prohibited."
          },
          {
            "value": "24",
            "label": "Dragging Prohibited",
            "definition": "An area in which the dragging of anything along the seabed, for example bottom trawling, is prohibited."
          },
          {
            "value": "25",
            "label": "Stopping Prohibited",
            "definition": "An area in which a vessel is prohibited from stopping."
          },
          {
            "value": "26",
            "label": "Landing Prohibited",
            "definition": "An area in which landing is prohibited."
          },
          {
            "value": "27",
            "label": "Speed Restricted",
            "definition": "An area within which speed is restricted."
          },
          {
            "value": "39",
            "label": "Swimming Prohibited",
            "definition": "An area in which swimming is prohibited."
          },
          {
            "value": "42",
            "label": "Power-Driven Vessels Prohibited",
            "definition": "An area within which any vessel propelled by machinery is prohibited."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='restriction']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "status",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [
          "1",
          "2",
          "3",
          "5",
          "6",
          "7",
          "8",
          "9",
          "14"
        ],
        "attribute_definition": "The condition of an object at a given instant in time.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Permanent",
            "definition": "Intended to last or function indefinitely."
          },
          {
            "value": "2",
            "label": "Occasional",
            "definition": "Acting on special occasions; happening irregularly."
          },
          {
            "value": "3",
            "label": "Recommended",
            "definition": "Presented as worthy of confidence, acceptance, use, etc."
          },
          {
            "value": "4",
            "label": "Not in Use",
            "definition": "Use has ceased, but the facility still exists intact; disused."
          },
          {
            "value": "5",
            "label": "Periodic/Intermittent",
            "definition": "Recurring at intervals."
          },
          {
            "value": "6",
            "label": "Reserved",
            "definition": "Set apart for some specific use."
          },
          {
            "value": "7",
            "label": "Temporary",
            "definition": "Meant to last only for a time."
          },
          {
            "value": "8",
            "label": "Private",
            "definition": "Administered by an individual or corporation, rather than a State or a public body."
          },
          {
            "value": "9",
            "label": "Mandatory",
            "definition": "Compulsory; enforced."
          },
          {
            "value": "11",
            "label": "Extinguished",
            "definition": "No longer lit."
          },
          {
            "value": "12",
            "label": "Illuminated",
            "definition": "Lit by flood lights, strip lights, etc."
          },
          {
            "value": "13",
            "label": "Historic",
            "definition": "Famous in history; of historical interest."
          },
          {
            "value": "14",
            "label": "Public",
            "definition": "Belonging to, available to, used or shared by, the community as a whole and not restricted to private use."
          },
          {
            "value": "15",
            "label": "Synchronized",
            "definition": "Occur at a time, coincide in point of time, be contemporary or simultaneous."
          },
          {
            "value": "16",
            "label": "Watched",
            "definition": "Looked at or observed over a period of time especially so as to be aware of any movement or change."
          },
          {
            "value": "17",
            "label": "Unwatched",
            "definition": "Usually automatic in operation, without any permanently-stationed personnel to superintend it."
          },
          {
            "value": "18",
            "label": "Existence Doubtful",
            "definition": "A feature that has been reported but has not been definitely determined to exist."
          },
          {
            "value": "28",
            "label": "Buoyed",
            "definition": "Marked by buoys."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='status']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "vesselSpeedLimit",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [],
        "attribute_definition": "The maximum allowed rate of travel for a vessel in an area in knots.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='vesselSpeedLimit']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "scaleMinimum",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The minimum scale at which the feature may be used for example for ECDIS presentation.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='scaleMinimum']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "information",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [],
        "attribute_definition": "Textual information about the feature. The information may be provided as a string of text or as a file name of a single external text file that contains the text.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]"
      },
      {
        "owner": "featureName",
        "attribute": "language",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The method of human communication, either spoken or written, consisting of the use of words in a structured and conventional way.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='featureName']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='language']]"
      },
      {
        "owner": "featureName",
        "attribute": "name",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The individual name of a feature.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='featureName']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='name']]"
      },
      {
        "owner": "featureName",
        "attribute": "nameUsage",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [
          "1",
          "2"
        ],
        "attribute_definition": "Classification of the type and display level of the name of a feature in an end-user system.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Default Name Display",
            "definition": "The name is intended to be displayed when the end-user system is set to the default name/text display setting."
          },
          {
            "value": "2",
            "label": "Alternate Name Display",
            "definition": "The name is intended to be displayed when the end-user system is set to an alternate name/text display setting, for example an alternate language."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='featureName']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='nameUsage']]"
      },
      {
        "owner": "fixedDateRange",
        "attribute": "dateEnd",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The latest date on which an object (for example a buoy) will be present.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='fixedDateRange']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='dateEnd']]"
      },
      {
        "owner": "fixedDateRange",
        "attribute": "dateStart",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The earliest date on which an object (for example a buoy) will be present.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='fixedDateRange']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='dateStart']]"
      },
      {
        "owner": "periodicDateRange",
        "attribute": "dateEnd",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The latest date on which an object (for example a buoy) will be present.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='periodicDateRange']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='dateEnd']]"
      },
      {
        "owner": "periodicDateRange",
        "attribute": "dateStart",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The earliest date on which an object (for example a buoy) will be present.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='periodicDateRange']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='dateStart']]"
      },
      {
        "owner": "vesselSpeedLimit",
        "attribute": "speedLimit",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The maximum allowed rate of travel in an area.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='vesselSpeedLimit']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='speedLimit']]"
      },
      {
        "owner": "vesselSpeedLimit",
        "attribute": "speedUnits",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [
          "2",
          "3",
          "4"
        ],
        "attribute_definition": "The units for description of speed.",
        "global_listed_values": [
          {
            "value": "2",
            "label": "Kilometres Per Hour",
            "definition": "A unit of speed, expressing the number of kilometres travelled in one hour."
          },
          {
            "value": "3",
            "label": "Miles Per Hour",
            "definition": "An imperial and United States customary unit of speed expressing the number of statute miles covered in one hour."
          },
          {
            "value": "4",
            "label": "Knots",
            "definition": "A nautical unit of speed. One knot is one nautical mile per hour. The name is derived from the knots in the log line."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='vesselSpeedLimit']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='speedUnits']]"
      },
      {
        "owner": "vesselSpeedLimit",
        "attribute": "vesselClass",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The classification of a vessel, normally as defined by length or gross tonnage.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='vesselSpeedLimit']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='vesselClass']]"
      },
      {
        "owner": "information",
        "attribute": "fileLocator",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The location of a fragment of text or other information in a support file.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='fileLocator']]"
      },
      {
        "owner": "information",
        "attribute": "fileReference",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The file name of an externally referenced text file.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='fileReference']]"
      },
      {
        "owner": "information",
        "attribute": "headline",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "Words set at the head of a passage or page to introduce or categorize.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='headline']]"
      },
      {
        "owner": "information",
        "attribute": "language",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The method of human communication, either spoken or written, consisting of the use of words in a structured and conventional way.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='language']]"
      },
      {
        "owner": "information",
        "attribute": "text",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "A non-formatted digital text string.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='text']]"
      }
    ],
    "evidence": {
      "edition": "2.0.0",
      "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
      "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
      "locators": [
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]"
      ],
      "claim_source_links": [
        {
          "feature_code": "AnchorageArea",
          "definition_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
          "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc"
        }
      ]
    },
    "definition_quote": "An area in which vessels or seaplanes anchor or may anchor."
  },
  "status": "COMPLETED",
  "execution_status": "COMPLETED",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q6_03.json)
```json
{
  "case_id": "PILOT_Q6_03",
  "required_task_obligations": [
    "provide_anchorage_definition_source",
    "cite_catalogue_edition_and_locator"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_107",
  "answer_sha256": "a6934565eac04a144317a43ac96d43d767f023f6e7a95357195533549c8494f2",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "020949eb3c39c887d7f25f93595a3eff135e766e70e54dcee96f1ec78f5ecf34",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_106 — Find wrecks intersecting the selected area.

답안 hash: `bb946ad0943b0f5bda34d9be33df1a502f2c81996f86df51ad6ce93c808f80ae`

### 실제 최종 답안
```json
{
  "answer_text": "The selected area does not intersect any wrecks.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "validator_blockers": [
    "BLOCKED_CONFIG: explicit research source required",
    "BLOCKED_CONFIG: unsupported operation: None"
  ],
  "status": "BLOCKED_CONFIG",
  "execution_status": "BLOCKED_CONFIG",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q3_03.json)
```json
{
  "case_id": "PILOT_Q3_03",
  "required_task_obligations": [
    "require_selected_aoi",
    "verify_coverage",
    "search_intersections_if_aoi_available",
    "request_aoi_when_missing"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "No selected geometry is provided by this benchmark input; an arbitrary viewport is not a substitute."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_106",
  "answer_sha256": "bb946ad0943b0f5bda34d9be33df1a502f2c81996f86df51ad6ce93c808f80ae",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "b68ad9b965184ff292cdd3c82261780d1e2ac1ebd3e3b51ea66b9dd7a02b98e1",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_105 — 제한구역의 제한 종류는 어떤 코드로 표현해?

답안 hash: `72b9c35246806afc4f52d51efe7ba284aa8fd6a5d8fcb0a3e0ee939add59aae4`

### 실제 최종 답안
```json
{
  "answer_text": "제한구역의 제한 종류는 '제한구역'이라는 공식적인 문서 코드로 표현됩니다.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "document_answer": {
    "features": [],
    "attribute_bindings": [],
    "evidence": {
      "edition": "2.0.0",
      "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
      "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
      "locators": [],
      "claim_source_links": []
    }
  },
  "status": "COMPLETED",
  "execution_status": "COMPLETED",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q2_02.json)
```json
{
  "case_id": "PILOT_Q2_02",
  "required_task_obligations": [
    "distinguish_restriction_and_area_category",
    "explain_restriction_codes"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": [
    "Explain restriction codes separately from categoryOfRestrictedArea. RequiredArea alternatives from another FC edition are not substitutes for FC 2.0.0 RestrictedArea."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_105",
  "answer_sha256": "72b9c35246806afc4f52d51efe7ba284aa8fd6a5d8fcb0a3e0ee939add59aae4",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "8f3524b1ae27255649fa1657557282c7b9d57c202cdf0555908e2c6c230832c9",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_104 — Find marine place names within 5 km of Dokdo.

답안 hash: `06d005a8bceb7ad53ef6c8645c156769cdd86976be12ce008ef739fe5c3b53da`

### 실제 최종 답안
```json
{
  "answer_text": "Marine place names within 5 km of Dokdo include: ",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q4_03.json)
```json
{
  "case_id": "PILOT_Q4_03",
  "required_task_obligations": [
    "resolve_approved_anchor",
    "search_fixed_gazetteer_5000m",
    "report_source_bound_objects"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_104",
  "answer_sha256": "06d005a8bceb7ad53ef6c8645c156769cdd86976be12ce008ef739fe5c3b53da",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "2e15336412a9dc7da26840f2535629710b97efd684f8204358cd43586850f18b",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_103 — What source supports the S-101 definition of AnchorageArea?

답안 hash: `1cbbbef4d6cb79991d4b46851088fed40681aa1aa64a335add6175b1450d52fd`

### 실제 최종 답안
```json
{
  "answer_text": "The source that supports the S-101 definition of AnchorageArea is the 'marine_places' scope in the 's101' category, with a source SHA256 of '3f931edd30279f561a129afbaa597db33c985bc59d211b9b64bd33942e4e6d7a'.",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q6_03.json)
```json
{
  "case_id": "PILOT_Q6_03",
  "required_task_obligations": [
    "provide_anchorage_definition_source",
    "cite_catalogue_edition_and_locator"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_103",
  "answer_sha256": "1cbbbef4d6cb79991d4b46851088fed40681aa1aa64a335add6175b1450d52fd",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "4573bb98bf93362ae6ed55cf0dd42d491fd35b0ae11ca0f612171926e879e11e",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_102 — S-101에서 정박지는 어떤 객체야?

답안 hash: `03ab65b58c2b5a51e43589059fc2b9b750aca97f75f1e2f73287fe2780c14e6a`

### 실제 최종 답안
```json
{
  "answer_text": "정박지는 Busan 항구에서의 물체입니다.",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q1_02.json)
```json
{
  "case_id": "PILOT_Q1_02",
  "required_task_obligations": [
    "explain_anchorage_area_definition"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_102",
  "answer_sha256": "03ab65b58c2b5a51e43589059fc2b9b750aca97f75f1e2f73287fe2780c14e6a",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "0a928fe01f15e3359eee8eb5aa358b75b3d18bcddccb0c65edb5e405866bd271",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_101 — Find wrecks within 5 km of Dokdo and explain their S-101 attributes.

답안 hash: `67d4c6a0708ce78256fa49d55722aad059ecc041dd90c070e49d300becfeed21`

### 실제 최종 답안
```json
{
  "answer_text": "The wrecks within 5 km of Dokdo are not found in the S-101 feature catalogue.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "validator_blockers": [
    "BLOCKED_DATA: public catalogue document evidence unavailable"
  ],
  "status": "BLOCKED_DATA",
  "execution_status": "BLOCKED_DATA",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q5_03.json)
```json
{
  "case_id": "PILOT_Q5_03",
  "required_task_obligations": [
    "resolve_reference",
    "verify_coverage",
    "search_wrecks_5000m",
    "explain_s101_attributes",
    "distinguish_object_values_from_standard_attributes",
    "separate_partial_document_answer"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "User-approved source-bound safe abstention; document explanations are separately evaluated optional partial output."
  ],
  "expected_spatial_behavior": {
    "accepted_states": [
      "BLOCKED_DATA",
      "DATA_OUT_OF_SCOPE"
    ],
    "required_disclosure": "Current connected snapshot cannot determine the answer for the requested spatial extent",
    "per_target": {
      "Wreck": {
        "status": "BLOCKED_DATA",
        "object_ids": null
      }
    },
    "empty_result_as_answer_forbidden": true,
    "claim_spatial_success_forbidden": true
  }
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_101",
  "answer_sha256": "67d4c6a0708ce78256fa49d55722aad059ecc041dd90c070e49d300becfeed21",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "76cf9aaa21c37bf165622d6b720c7d737fe67b57ad82afeb36733acd86afe57e",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_100 — What source supports the S-101 definition of AnchorageArea?

답안 hash: `4333d3e5b33f1a3ab613d67e79eae09d8eba7a5231f29c278f8b20cc5cd83d96`

### 실제 최종 답안
```json
{
  "answer_text": "The source that supports the S-101 definition of AnchorageArea is the 'outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml' file.",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q6_03.json)
```json
{
  "case_id": "PILOT_Q6_03",
  "required_task_obligations": [
    "provide_anchorage_definition_source",
    "cite_catalogue_edition_and_locator"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_100",
  "answer_sha256": "4333d3e5b33f1a3ab613d67e79eae09d8eba7a5231f29c278f8b20cc5cd83d96",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "82f9aef3d61d1b3bc706544adcb595e239b0f15c77458e26db5537db46bd4a08",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_099 — 제한구역의 제한 종류는 어떤 코드로 표현해?

답안 hash: `a2cd26034b74d274b739578aa229e83799a42cd3301ab9c6662cf3dd08c3f079`

### 실제 최종 답안
```json
{
  "answer_text": "제한구역의 제한 종류는 '제한구역'이라는 공식적인 문서 코드로 표현됩니다.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "validator_blockers": [
    "BLOCKED_DATA: public catalogue document evidence unavailable"
  ],
  "status": "BLOCKED_DATA",
  "execution_status": "BLOCKED_DATA",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q2_02.json)
```json
{
  "case_id": "PILOT_Q2_02",
  "required_task_obligations": [
    "distinguish_restriction_and_area_category",
    "explain_restriction_codes"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": [
    "Explain restriction codes separately from categoryOfRestrictedArea. RequiredArea alternatives from another FC edition are not substitutes for FC 2.0.0 RestrictedArea."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_099",
  "answer_sha256": "a2cd26034b74d274b739578aa229e83799a42cd3301ab9c6662cf3dd08c3f079",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "fb3f2b4509ab7587b17a65afe32feeb5af99dd4fff0dd8017577d56d942f9c39",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_098 — 부산항 영역 안의 정박지를 찾아줘.

답안 hash: `edc85a1b3aa9065db57c85e83173ab6b102aee216c6ee1e823931a38e25fb77f`

### 실제 최종 답안
```json
{
  "answer_text": "The watercraft located within the Busan Port boundary.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "validator_blockers": [
    "BLOCKED_DATA: public catalogue document evidence unavailable"
  ],
  "status": "BLOCKED_DATA",
  "execution_status": "BLOCKED_DATA",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q3_02.json)
```json
{
  "case_id": "PILOT_Q3_02",
  "required_task_obligations": [
    "resolve_official_port_polygon",
    "verify_coverage",
    "search_within_polygon",
    "report_objects_or_unresolved_reason"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "Object IDs refer to frozen snapshot records, not deduplicated physical facilities or the whole legal port."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_098",
  "answer_sha256": "edc85a1b3aa9065db57c85e83173ab6b102aee216c6ee1e823931a38e25fb77f",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "a6bbdc2d5efd3ca88252048c4d3b46db491eeef3535aaa913ffe7ce7eb09428e",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_097 — S-101 Wreck 정의의 원문과 Feature Catalogue 출처를 알려줘.

답안 hash: `74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b`

### 실제 최종 답안
```json
null
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q6_01.json)
```json
{
  "case_id": "PILOT_Q6_01",
  "required_task_obligations": [
    "provide_wreck_definition_text",
    "cite_catalogue_edition_and_locator"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_097",
  "answer_sha256": "74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_096 — Find wrecks intersecting the selected area.

답안 hash: `18b40aad29795c48e096b3aa258993cc72e198f4af5044120cf7d56842f61d89`

### 실제 최종 답안
```json
{
  "answer_text": "The wrecks intersecting the selected area are identified.",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q3_03.json)
```json
{
  "case_id": "PILOT_Q3_03",
  "required_task_obligations": [
    "require_selected_aoi",
    "verify_coverage",
    "search_intersections_if_aoi_available",
    "request_aoi_when_missing"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "No selected geometry is provided by this benchmark input; an arbitrary viewport is not a substitute."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_096",
  "answer_sha256": "18b40aad29795c48e096b3aa258993cc72e198f4af5044120cf7d56842f61d89",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "ed03c731059422f42150874bcaed36516bbc68e7c1ee076c5c99be0226ed1e7c",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_095 — 등대와 부표를 구분하는 S-101 근거를 알려줘.

답안 hash: `5422c25fb0e24d948c0b2d6330c5ceccc8ad017a49f921206718c1c35c0a11c7`

### 실제 최종 답안
```json
{
  "document_answer": {
    "features": [],
    "attribute_bindings": []
  },
  "search_executed": null,
  "execution_status": "COMPLETED",
  "source_coverage": {},
  "per_task_status": {},
  "mapping_provenance": {
    "version": "emitted_output_v1",
    "root": "final_state.final_dict",
    "retrieved_text_used_as_answer": false,
    "reference_used_for_mapping": false,
    "structured_document_answer_present": false
  },
  "status": "COMPLETED",
  "blocker": null,
  "clarification_request": [],
  "answer_text": "질의와 관련된 근거 문서 2건을 찾았습니다. 대표 근거는 S-101_Annex_A_DCEG_Ed_2.0.0 / page_540이며, 내용 요지는 다음과 같습니다: 520 Data Classification and Encoding Guide S-101 Annex A December 2024 Edition 2.0.0 6 : board 7 : x-shaped 8 : upright cross 9 : cube (point up) 10 : 2 cones (point to point) 11 : 2 cones (base to base) 12 : rhombus 13..."
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q6_02.json)
```json
{
  "case_id": "PILOT_Q6_02",
  "required_task_obligations": [
    "compare_fixed_structure_and_floating_aid_models",
    "cite_comparison_evidence"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "single_Lighthouse_feature_assertion",
    "global_colour_codes_for_feature_binding"
  ],
  "scope_notes": [
    "Landmark/Building describe conditional structure alternatives; LightAllAround/LightSectored describe light alternatives. Listing these for explanation does not assert all must exist in one physical lighthouse.",
    "Bounded comparison: LateralBuoy is the explicitly selected representative floating-aid feature; no claim to exhaustively describe every buoy class. Compare with conditional structure/light models."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_095",
  "answer_sha256": "5422c25fb0e24d948c0b2d6330c5ceccc8ad017a49f921206718c1c35c0a11c7",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "8ef488850d58a265ea86178e48d5d64a3d3c694fcb5880ba81a505332813c158",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_094 — Which attributes describe a Wreck in S-101?

답안 hash: `df05a8666f93a777212c762a1af377b2b3b0cc882fee0cbfdb5b798b970b4163`

### 실제 최종 답안
```json
{
  "answer_text": "The Wreck feature is located within the S-101 scope in S-101.",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q2_03.json)
```json
{
  "case_id": "PILOT_Q2_03",
  "required_task_obligations": [
    "explain_wreck_attribute_bindings"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_094",
  "answer_sha256": "df05a8666f93a777212c762a1af377b2b3b0cc882fee0cbfdb5b798b970b4163",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "335ac4b04ad206f3814448ee7fa26ffde41d05989a1fc049c7797917a9f257e4",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_093 — S-101 등대의 색상 속성과 허용 값을 알려줘.

답안 hash: `254751d621ddf61dc526f332fe14b218128255dd14e01dbff192ccc5cba466eb`

### 실제 최종 답안
```json
{
  "answer_text": "등대 색상: 주로 노란색이며, 일부는 검정색이나 흰색입니다. 허용 레이즈: 1000m 이내입니다.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "validator_blockers": [
    "BLOCKED_DATA: public catalogue document evidence unavailable"
  ],
  "status": "BLOCKED_DATA",
  "execution_status": "BLOCKED_DATA",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q2_01.json)
```json
{
  "case_id": "PILOT_Q2_01",
  "required_task_obligations": [
    "distinguish_structure_and_light_colour",
    "explain_feature_bound_permitted_values"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "single_Lighthouse_feature_assertion",
    "global_colour_codes_for_feature_binding"
  ],
  "scope_notes": [
    "Landmark/Building describe conditional structure alternatives; LightAllAround/LightSectored describe light alternatives. Listing these for explanation does not assert all must exist in one physical lighthouse."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_093",
  "answer_sha256": "254751d621ddf61dc526f332fe14b218128255dd14e01dbff192ccc5cba466eb",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "c0ec0bf7ca6b1bbeb618edfd947e7baaf0d6c9452b703ec7887ec38479d02632",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_092 — 독도 주변 반경 5000m의 해양지명을 찾아줘.

답안 hash: `c81bdeb8a334711ad38f10e1f7860ec6dd04cce1c4889f195c9fc29056980c7d`

### 실제 최종 답안
```json
{
  "answer_text": "独岛位于韩国济州道的独岛郡，距离济州岛约10公里。",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "validator_blockers": [
    "BLOCKED_DATA: public catalogue document evidence unavailable"
  ],
  "status": "BLOCKED_DATA",
  "execution_status": "BLOCKED_DATA",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q4_02.json)
```json
{
  "case_id": "PILOT_Q4_02",
  "required_task_obligations": [
    "resolve_approved_anchor",
    "search_fixed_gazetteer_5000m",
    "report_source_bound_objects"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_092",
  "answer_sha256": "c81bdeb8a334711ad38f10e1f7860ec6dd04cce1c4889f195c9fc29056980c7d",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "22dfbb62cfdf949ef450a74449cf7ea264ab5fdf95c0a897e9d13e130aebb6fa",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_091 — What is a wreck in S-101?

답안 hash: `79f387472a63bb5d52813b7d1c0b7195028641ef75f84e44f15b851502d15346`

### 실제 최종 답안
```json
{
  "answer_text": "A wreck is a wreck in S-101.",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q1_03.json)
```json
{
  "case_id": "PILOT_Q1_03",
  "required_task_obligations": [
    "explain_wreck_definition"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_091",
  "answer_sha256": "79f387472a63bb5d52813b7d1c0b7195028641ef75f84e44f15b851502d15346",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "463d05b481bc6945b459f7a66f6d6d036b2adfe12587ef4a3885c7fde3c198fb",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_090 — 부산항 주변 2km의 정박지와 제한구역을 찾아 비교해줘.

답안 hash: `c8920ca6f2cf78eb3d37b2a0d7912531c92fe54c4c11e13416f3f2a2fd76527d`

### 실제 최종 답안
```json
{
  "answer_text": "The search results for '정박지' and '제한구역' within 2km of '부산항' are as follows:",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q5_02.json)
```json
{
  "case_id": "PILOT_Q5_02",
  "required_task_obligations": [
    "resolve_reference",
    "verify_both_target_coverages",
    "search_both_targets_2000m",
    "compare_target_results",
    "disclose_subset_limitations"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "Object IDs refer to frozen snapshot records, not deduplicated physical facilities or the whole legal port."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_090",
  "answer_sha256": "c8920ca6f2cf78eb3d37b2a0d7912531c92fe54c4c11e13416f3f2a2fd76527d",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "d4c07e973a1a1b3592085677e8bfaac7ee59167f1146cd016b8f27b23d6c0575",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_089 — Which attributes describe a Wreck in S-101?

답안 hash: `e5ddbf0f3a7f022e677853f4c230f2172d1635cf3947b057f3e3aadf8a066244`

### 실제 최종 답안
```json
{
  "answer_text": "A wreck is described in S-101, located within the scope of the S-101 feature catalogue.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "document_answer": {
    "features": [
      {
        "code": "Wreck",
        "xml_type": "S100_FC_FeatureType",
        "definition": "The ruined remains of a stranded or sunken vessel which has been rendered useless.",
        "permitted_primitives": [
          "point",
          "surface"
        ],
        "bindings": [
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "categoryOfWreck"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [
              "1",
              "2",
              "3",
              "4",
              "5"
            ],
            "xml_child_index": 5
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "expositionOfSounding"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [
              "1",
              "2",
              "3"
            ],
            "xml_child_index": 6
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "featureName"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [],
            "xml_child_index": 7
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "height"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 8
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "interoperabilityIdentifier"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 9
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "qualityOfVerticalMeasurement"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [
              "1",
              "2",
              "3",
              "4",
              "6",
              "7",
              "8",
              "9"
            ],
            "xml_child_index": 10
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "radarConspicuous"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 11
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "reportedDate"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 12
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "status"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [
              "7",
              "13",
              "18"
            ],
            "xml_child_index": 13
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "techniqueOfVerticalMeasurement"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [
              "1",
              "2",
              "3",
              "4",
              "5",
              "8",
              "9",
              "10",
              "11",
              "12",
              "13",
              "15",
              "16",
              "17",
              "18"
            ],
            "xml_child_index": 14
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "valueOfSounding"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 15
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "visualProminence"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [
              "1",
              "2",
              "3"
            ],
            "xml_child_index": 16
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "waterLevelEffect"
              }
            ],
            "lower": "1",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [
              "1",
              "2",
              "3",
              "4",
              "5"
            ],
            "xml_child_index": 17
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "scaleMinimum"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 18
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "information"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [],
            "xml_child_index": 19
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "pictorialRepresentation"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 20
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "defaultClearanceDepth"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 21
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "surroundingDepth"
              }
            ],
            "lower": "1",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 22
          },
          {
            "kind": "informationBinding",
            "references": [
              {
                "type": "association",
                "ref": "AdditionalInformation"
              },
              {
                "type": "role",
                "ref": "theInformation"
              },
              {
                "type": "informationType",
                "ref": "NauticalInformation"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 23
          },
          {
            "kind": "featureBinding",
            "references": [
              {
                "type": "association",
                "ref": "StructureEquipment"
              },
              {
                "type": "role",
                "ref": "theEquipment"
              },
              {
                "type": "featureType",
                "ref": "Daymark"
              },
              {
                "type": "featureType",
                "ref": "DistanceMark"
              },
              {
                "type": "featureType",
                "ref": "FogSignal"
              },
              {
                "type": "featureType",
                "ref": "LightAllAround"
              },
              {
                "type": "featureType",
                "ref": "LightFogDetector"
              },
              {
                "type": "featureType",
                "ref": "PhysicalAISAidToNavigation"
              },
              {
                "type": "featureType",
                "ref": "RadarTransponderBeacon"
              },
              {
                "type": "featureType",
                "ref": "Retroreflector"
              },
              {
                "type": "featureType",
                "ref": "SignalStationTraffic"
              },
              {
                "type": "featureType",
                "ref": "SignalStationWarning"
              },
              {
                "type": "featureType",
                "ref": "LightSectored"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [],
            "xml_child_index": 25
          },
          {
            "kind": "featureBinding",
            "references": [
              {
                "type": "association",
                "ref": "UpdatedInformation"
              },
              {
                "type": "role",
                "ref": "theUpdate"
              },
              {
                "type": "featureType",
                "ref": "UpdateInformation"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [],
            "xml_child_index": 26
          },
          {
            "kind": "featureBinding",
            "references": [
              {
                "type": "association",
                "ref": "TextAssociation"
              },
              {
                "type": "role",
                "ref": "theCartographicText"
              },
              {
                "type": "featureType",
                "ref": "TextPlacement"
              }
            ],
            "lower": "0",
            "upper": "2",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 27
          }
        ],
        "listed_values": [],
        "version": "2.0.0",
        "source_status": "VERIFIED_XML_EXTRACTION",
        "source_path": "D:\\An_GeoLLM\\outputs\\staging\\s101_feature_catalogue_2_0_0\\S-101\\CATALOGUES\\101_Feature_Catalogue_2.0.0.xml",
        "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "parsed_locator": "/features/86",
        "definition_sha256": "42995f6ea3f18e9e74fd93a554871688cc297d4440b18042e5d894f130eb971a",
        "xml_element_serialized_sha256": "1f207649d80e84625edd620051b6645d926ff8c7553be9fa868b6cf165a54177",
        "element_hash_serialization": "xml.etree.ElementTree serialization; not a raw byte slice"
      }
    ],
    "attribute_bindings": [
      {
        "owner": "Wreck",
        "attribute": "categoryOfWreck",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [
          "1",
          "2",
          "3",
          "4",
          "5"
        ],
        "attribute_definition": "Classification of a wrecked or ruined ship.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Non-Dangerous Wreck",
            "definition": "A wreck which is not considered to be dangerous to surface navigation."
          },
          {
            "value": "2",
            "label": "Dangerous Wreck",
            "definition": "A wreck submerged at such a depth as to be considered dangerous to surface navigation."
          },
          {
            "value": "3",
            "label": "Distributed Remains of Wreck",
            "definition": "A substantively decayed wreck over which it is safe to navigate but which should be avoided for anchoring, taking the ground or ground fishing."
          },
          {
            "value": "4",
            "label": "Wreck Showing Mast/Masts",
            "definition": "Wreck of which only the mast(s) is visible at the sounding datum indicated."
          },
          {
            "value": "5",
            "label": "Wreck Showing Any Portion of Hull or Superstructure",
            "definition": "Wreck of which any portion of the hull or superstructure is visible at the sounding datum indicated."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='categoryOfWreck']]"
      },
      {
        "owner": "Wreck",
        "attribute": "expositionOfSounding",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [
          "1",
          "2",
          "3"
        ],
        "attribute_definition": "Indicates the relationship of the depth of a feature to the range of depth of the surrounding depth area.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Within the Range of Depth of the Surrounding Depth Area",
            "definition": "The depth corresponds to the depth range of the surrounding depth area; that is, the depth is not shoaler than the minimum depth of the surrounding depth area or deeper than the maximum depth of the surrounding depth area."
          },
          {
            "value": "2",
            "label": "Shoaler Than the Range of Depth of the Surrounding Depth Area",
            "definition": "The depth is shoaler than the minimum depth of the surrounding depth area."
          },
          {
            "value": "3",
            "label": "Deeper Than the Range of Depth of the Surrounding Depth Area",
            "definition": "The depth is deeper than the maximum depth of the surrounding depth area."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='expositionOfSounding']]"
      },
      {
        "owner": "Wreck",
        "attribute": "featureName",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [],
        "attribute_definition": "Provides the name of an entity, defines the national language of the name, and provides the option to display the name at various system display settings.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='featureName']]"
      },
      {
        "owner": "Wreck",
        "attribute": "height",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The value of the vertical distance to the highest point of the feature, measured from a specified vertical datum.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='height']]"
      },
      {
        "owner": "Wreck",
        "attribute": "interoperabilityIdentifier",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "A common unique identifier for entities which describe a single real-world feature, and which is used to identify instances of the feature in end-user systems where the feature may be included in multiple data product types.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='interoperabilityIdentifier']]"
      },
      {
        "owner": "Wreck",
        "attribute": "qualityOfVerticalMeasurement",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [
          "1",
          "2",
          "3",
          "4",
          "6",
          "7",
          "8",
          "9"
        ],
        "attribute_definition": "The reliability of the value of a sounding.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Depth Known",
            "definition": "The depth from the chart datum to the seabed (or to the top of a drying feature) is known."
          },
          {
            "value": "2",
            "label": "Depth or Least Depth Unknown",
            "definition": "The depth from chart datum to the seabed, or the shoalest depth of the feature is unknown."
          },
          {
            "value": "3",
            "label": "Doubtful Sounding",
            "definition": "A depth that may be less than indicated."
          },
          {
            "value": "4",
            "label": "Unreliable Sounding",
            "definition": "A depth that is considered to be an unreliable value."
          },
          {
            "value": "6",
            "label": "Least Depth Known",
            "definition": "The shoalest depth over a feature is of known value."
          },
          {
            "value": "7",
            "label": "Least Depth Unknown, Safe Clearance at Value Shown",
            "definition": "The least depth over a feature is unknown, but there is considered to be safe clearance at this depth."
          },
          {
            "value": "8",
            "label": "Value Reported (Not Surveyed)",
            "definition": "Depth value obtained from a report, but not fully surveyed."
          },
          {
            "value": "9",
            "label": "Value Reported (Not Confirmed)",
            "definition": "Depth value obtained from a report, which it has not been possible to confirm."
          },
          {
            "value": "10",
            "label": "Maintained Depth",
            "definition": "The depth at which a channel is kept by human influence, usually by dredging."
          },
          {
            "value": "11",
            "label": "Not Regularly Maintained",
            "definition": "Depths may be altered by human influence, but will not be routinely maintained."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='qualityOfVerticalMeasurement']]"
      },
      {
        "owner": "Wreck",
        "attribute": "radarConspicuous",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "A feature which returns a strong radar echo.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='radarConspicuous']]"
      },
      {
        "owner": "Wreck",
        "attribute": "reportedDate",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The date that the item was observed, done, or investigated.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='reportedDate']]"
      },
      {
        "owner": "Wreck",
        "attribute": "status",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [
          "7",
          "13",
          "18"
        ],
        "attribute_definition": "The condition of an object at a given instant in time.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Permanent",
            "definition": "Intended to last or function indefinitely."
          },
          {
            "value": "2",
            "label": "Occasional",
            "definition": "Acting on special occasions; happening irregularly."
          },
          {
            "value": "3",
            "label": "Recommended",
            "definition": "Presented as worthy of confidence, acceptance, use, etc."
          },
          {
            "value": "4",
            "label": "Not in Use",
            "definition": "Use has ceased, but the facility still exists intact; disused."
          },
          {
            "value": "5",
            "label": "Periodic/Intermittent",
            "definition": "Recurring at intervals."
          },
          {
            "value": "6",
            "label": "Reserved",
            "definition": "Set apart for some specific use."
          },
          {
            "value": "7",
            "label": "Temporary",
            "definition": "Meant to last only for a time."
          },
          {
            "value": "8",
            "label": "Private",
            "definition": "Administered by an individual or corporation, rather than a State or a public body."
          },
          {
            "value": "9",
            "label": "Mandatory",
            "definition": "Compulsory; enforced."
          },
          {
            "value": "11",
            "label": "Extinguished",
            "definition": "No longer lit."
          },
          {
            "value": "12",
            "label": "Illuminated",
            "definition": "Lit by flood lights, strip lights, etc."
          },
          {
            "value": "13",
            "label": "Historic",
            "definition": "Famous in history; of historical interest."
          },
          {
            "value": "14",
            "label": "Public",
            "definition": "Belonging to, available to, used or shared by, the community as a whole and not restricted to private use."
          },
          {
            "value": "15",
            "label": "Synchronized",
            "definition": "Occur at a time, coincide in point of time, be contemporary or simultaneous."
          },
          {
            "value": "16",
            "label": "Watched",
            "definition": "Looked at or observed over a period of time especially so as to be aware of any movement or change."
          },
          {
            "value": "17",
            "label": "Unwatched",
            "definition": "Usually automatic in operation, without any permanently-stationed personnel to superintend it."
          },
          {
            "value": "18",
            "label": "Existence Doubtful",
            "definition": "A feature that has been reported but has not been definitely determined to exist."
          },
          {
            "value": "28",
            "label": "Buoyed",
            "definition": "Marked by buoys."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='status']]"
      },
      {
        "owner": "Wreck",
        "attribute": "techniqueOfVerticalMeasurement",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [
          "1",
          "2",
          "3",
          "4",
          "5",
          "8",
          "9",
          "10",
          "11",
          "12",
          "13",
          "15",
          "16",
          "17",
          "18"
        ],
        "attribute_definition": "Survey method used to obtain depth information.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Found by Echo Sounder",
            "definition": "The depth was measured by using an instrument that determines depth of water by measuring the time interval between emission of a sonic or ultrasonic signal and return of its echo from the bottom."
          },
          {
            "value": "2",
            "label": "Found by Side Scan Sonar",
            "definition": "The depth was computed from a record produced by active sonar in which fixed acoustic beams are directed into the water perpendicularly to the direction of travel to scan the seabed and generate a record of the seabed configuration."
          },
          {
            "value": "3",
            "label": "Found by Multi Beam",
            "definition": "The depth was measured by using a wide swath echo sounder that uses multiple beams to measure depths directly below and transverse to the ship's track."
          },
          {
            "value": "4",
            "label": "Found by Diver",
            "definition": "The depth was determined by a person skilled in the practice of diving."
          },
          {
            "value": "5",
            "label": "Found by Lead Line",
            "definition": "The depth was measured by using a line, graduated with attached marks and fastened to a sounding lead."
          },
          {
            "value": "8",
            "label": "Swept by Vertical Acoustic System",
            "definition": "The given area has been swept using a system comprised of multiple echo sounder transducers attached to booms deployed from the survey vessel."
          },
          {
            "value": "9",
            "label": "Found by Electromagnetic Sensor",
            "definition": "The depth was determined by using an instrument that compares electromagnetic signals."
          },
          {
            "value": "10",
            "label": "Photogrammetry",
            "definition": "The science or art of obtaining reliable measurements from photographs."
          },
          {
            "value": "11",
            "label": "Satellite Imagery",
            "definition": "The depth was determined by using instruments placed aboard an artificial satellite."
          },
          {
            "value": "12",
            "label": "Found by Levelling",
            "definition": "The depth was determined by using levelling techniques to find the elevation of the point relative to a datum."
          },
          {
            "value": "13",
            "label": "Swept by Side Scan Sonar",
            "definition": "The given area was determined to be free from navigational dangers to a certain depth by towing a side scan sonar."
          },
          {
            "value": "15",
            "label": "Found by LIDAR",
            "definition": "The depth was measured by using an instrument that measures distance by emitting timed pulses of laser light and measuring the time between emission and reception of the reflected pulses."
          },
          {
            "value": "16",
            "label": "Synthetic Aperture Radar",
            "definition": "A radar with a synthetic aperture antenna which is composed of a large number of elementary transducing elements. The signals are electronically combined into a resulting signal equivalent to that of a single antenna of a given aperture in a given direction."
          },
          {
            "value": "17",
            "label": "Hyperspectral Imagery",
            "definition": "Term used to describe the imagery derived from subdividing the electromagnetic spectrum into very narrow bandwidths. These narrow bandwidths may be combined with or subtracted from each other in various ways to form images useful in precise terrain or target analysis."
          },
          {
            "value": "18",
            "label": "Mechanically Swept",
            "definition": "The given area was determined to be free from navigational dangers to a certain depth by towing a line or object below the surface at the desired depth; or least depth(s) and position(s) within an area was identified using the same technique."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='techniqueOfVerticalMeasurement']]"
      },
      {
        "owner": "Wreck",
        "attribute": "valueOfSounding",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The value of the measurement of a sounding relative to the chart datum.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='valueOfSounding']]"
      },
      {
        "owner": "Wreck",
        "attribute": "visualProminence",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [
          "1",
          "2",
          "3"
        ],
        "attribute_definition": "The extent to which a feature, either natural or artificial, is visible from seaward.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Visually Conspicuous",
            "definition": "Term applied to an object either natural or artificial which is distinctly and notably visible from seaward."
          },
          {
            "value": "2",
            "label": "Not Visually Conspicuous",
            "definition": "An object that may be visible from seaward, but cannot be used as a fixing mark and is not conspicuous."
          },
          {
            "value": "3",
            "label": "Prominent",
            "definition": "Objects which are easily identifiable, but do not justify being classed as conspicuous."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='visualProminence']]"
      },
      {
        "owner": "Wreck",
        "attribute": "waterLevelEffect",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [
          "1",
          "2",
          "3",
          "4",
          "5"
        ],
        "attribute_definition": "The effect of the surrounding water on an object.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Partly Submerged at High Water",
            "definition": "Partially covered and partially dry at high water."
          },
          {
            "value": "2",
            "label": "Always Dry",
            "definition": "Not covered at high water under average meteorological conditions."
          },
          {
            "value": "3",
            "label": "Always Under Water/Submerged",
            "definition": "Remains covered by water at all times under average meteorological conditions."
          },
          {
            "value": "4",
            "label": "Covers and Uncovers",
            "definition": "Expression intended to indicate an area of a reef or other projection from the bottom of a body of water which periodically extends above and is submerged below the surface. Also referred to as dries or uncovers."
          },
          {
            "value": "5",
            "label": "Awash",
            "definition": "Flush with, or washed by the waves at low water under average meteorological conditions."
          },
          {
            "value": "6",
            "label": "Subject to Inundation or Flooding",
            "definition": "An area periodically covered by flood water, excluding tidal waters."
          },
          {
            "value": "7",
            "label": "Floating",
            "definition": "Resting or moving on the surface of a liquid without sinking."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='waterLevelEffect']]"
      },
      {
        "owner": "Wreck",
        "attribute": "scaleMinimum",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The minimum scale at which the feature may be used for example for ECDIS presentation.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='scaleMinimum']]"
      },
      {
        "owner": "Wreck",
        "attribute": "information",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [],
        "attribute_definition": "Textual information about the feature. The information may be provided as a string of text or as a file name of a single external text file that contains the text.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]"
      },
      {
        "owner": "Wreck",
        "attribute": "pictorialRepresentation",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The file name of an externally referenced picture file.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='pictorialRepresentation']]"
      },
      {
        "owner": "Wreck",
        "attribute": "defaultClearanceDepth",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The depth value determined for an underwater hazard of unknown depth, based on the depth of the surrounding area.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='defaultClearanceDepth']]"
      },
      {
        "owner": "Wreck",
        "attribute": "surroundingDepth",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The depth value determined for seabed around an underwater hazard, based on the depth of the surrounding area.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='surroundingDepth']]"
      },
      {
        "owner": "featureName",
        "attribute": "language",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The method of human communication, either spoken or written, consisting of the use of words in a structured and conventional way.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='featureName']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='language']]"
      },
      {
        "owner": "featureName",
        "attribute": "name",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The individual name of a feature.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='featureName']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='name']]"
      },
      {
        "owner": "featureName",
        "attribute": "nameUsage",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [
          "1",
          "2"
        ],
        "attribute_definition": "Classification of the type and display level of the name of a feature in an end-user system.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Default Name Display",
            "definition": "The name is intended to be displayed when the end-user system is set to the default name/text display setting."
          },
          {
            "value": "2",
            "label": "Alternate Name Display",
            "definition": "The name is intended to be displayed when the end-user system is set to an alternate name/text display setting, for example an alternate language."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='featureName']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='nameUsage']]"
      },
      {
        "owner": "information",
        "attribute": "fileLocator",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The location of a fragment of text or other information in a support file.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='fileLocator']]"
      },
      {
        "owner": "information",
        "attribute": "fileReference",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The file name of an externally referenced text file.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='fileReference']]"
      },
      {
        "owner": "information",
        "attribute": "headline",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "Words set at the head of a passage or page to introduce or categorize.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='headline']]"
      },
      {
        "owner": "information",
        "attribute": "language",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The method of human communication, either spoken or written, consisting of the use of words in a structured and conventional way.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='language']]"
      },
      {
        "owner": "information",
        "attribute": "text",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "A non-formatted digital text string.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='text']]"
      }
    ],
    "evidence": {
      "edition": "2.0.0",
      "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
      "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
      "locators": [
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]"
      ],
      "claim_source_links": [
        {
          "feature_code": "Wreck",
          "definition_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
          "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc"
        }
      ]
    },
    "definition_quote": "The ruined remains of a stranded or sunken vessel which has been rendered useless."
  },
  "status": "COMPLETED",
  "execution_status": "COMPLETED",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q2_03.json)
```json
{
  "case_id": "PILOT_Q2_03",
  "required_task_obligations": [
    "explain_wreck_attribute_bindings"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_089",
  "answer_sha256": "e5ddbf0f3a7f022e677853f4c230f2172d1635cf3947b057f3e3aadf8a066244",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "978150fd3591138d431095b6c17b4b82f2b55255188e6eff224191887bbd5892",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_088 — What is a wreck in S-101?

답안 hash: `d1cda9d525ae319331df9b10bd66e027b25eb9dd5c2f5f6242222f819e5cb476`

### 실제 최종 답안
```json
{
  "answer_text": "A wreck is a damaged or destroyed vehicle or other object, typically on a road or highway, that has been involved in an accident or has been abandoned.",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q1_03.json)
```json
{
  "case_id": "PILOT_Q1_03",
  "required_task_obligations": [
    "explain_wreck_definition"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_088",
  "answer_sha256": "d1cda9d525ae319331df9b10bd66e027b25eb9dd5c2f5f6242222f819e5cb476",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "3b1a5cf4da2b2d114a90cf4c8dc4c197d4642f4eb16bffbe22fd948ae72e776f",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_087 — 등대와 부표를 구분하는 S-101 근거를 알려줘.

답안 hash: `6fb21b7b7e9a3032ca8bbf3914c86afb4353f17cc041fc526d24cbb4b3d8c23a`

### 실제 최종 답안
```json
{
  "answer_text": "等明灯和浮标在S-101数据库中可以区分。",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "validator_blockers": [
    "BLOCKED_DATA: public catalogue document evidence unavailable",
    "BLOCKED_DATA: public catalogue document evidence unavailable"
  ],
  "status": "BLOCKED_DATA",
  "execution_status": "BLOCKED_DATA",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q6_02.json)
```json
{
  "case_id": "PILOT_Q6_02",
  "required_task_obligations": [
    "compare_fixed_structure_and_floating_aid_models",
    "cite_comparison_evidence"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "single_Lighthouse_feature_assertion",
    "global_colour_codes_for_feature_binding"
  ],
  "scope_notes": [
    "Landmark/Building describe conditional structure alternatives; LightAllAround/LightSectored describe light alternatives. Listing these for explanation does not assert all must exist in one physical lighthouse.",
    "Bounded comparison: LateralBuoy is the explicitly selected representative floating-aid feature; no claim to exhaustively describe every buoy class. Compare with conditional structure/light models."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_087",
  "answer_sha256": "6fb21b7b7e9a3032ca8bbf3914c86afb4353f17cc041fc526d24cbb4b3d8c23a",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "3b34fe2ce027e6bf900d915deb84b5ce242b29624275505ec945364a1a833776",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_086 — S-101에서 정박지는 어떤 객체야?

답안 hash: `623503f5cf6bebaf80ce97a7f77570188c9c71cb2e9b617b57ea3029793701d5`

### 실제 최종 답안
```json
{
  "answer_text": "S-101에서 정박지는 'Anchorage Area' 객체입니다.",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q1_02.json)
```json
{
  "case_id": "PILOT_Q1_02",
  "required_task_obligations": [
    "explain_anchorage_area_definition"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_086",
  "answer_sha256": "623503f5cf6bebaf80ce97a7f77570188c9c71cb2e9b617b57ea3029793701d5",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "5f0a43c4924db4a50c65c4f339093b26d2710e97606b287499d5a717395fdb64",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_085 — Find wrecks within 5 km of Dokdo and explain their S-101 attributes.

답안 hash: `05f765711c03c114891a7a9a2deddd6cb058507824a2a47fec36a1be2c0a2c69`

### 실제 최종 답안
```json
{
  "answer_text": "The wrecks within 5 km of Dokdo are classified as 'Non-Dangerous Wreck' and have a default clearance depth of 1.5 meters. They are not distributed remains, showing mast/masts, wreck showing any portion of hull or superstructure, or wreck showing the highest point. The quality of vertical measurement for these wrecks is not reported.",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q5_03.json)
```json
{
  "case_id": "PILOT_Q5_03",
  "required_task_obligations": [
    "resolve_reference",
    "verify_coverage",
    "search_wrecks_5000m",
    "explain_s101_attributes",
    "distinguish_object_values_from_standard_attributes",
    "separate_partial_document_answer"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "User-approved source-bound safe abstention; document explanations are separately evaluated optional partial output."
  ],
  "expected_spatial_behavior": {
    "accepted_states": [
      "BLOCKED_DATA",
      "DATA_OUT_OF_SCOPE"
    ],
    "required_disclosure": "Current connected snapshot cannot determine the answer for the requested spatial extent",
    "per_target": {
      "Wreck": {
        "status": "BLOCKED_DATA",
        "object_ids": null
      }
    },
    "empty_result_as_answer_forbidden": true,
    "claim_spatial_success_forbidden": true
  }
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_085",
  "answer_sha256": "05f765711c03c114891a7a9a2deddd6cb058507824a2a47fec36a1be2c0a2c69",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "75915c01c61af1f9046adb62682863dd24537fc55c837d044faa714efb860a23",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_084 — Which attributes describe a Wreck in S-101?

답안 hash: `27d29009517ec7fef0a32bf4b2cd89f40b8b5e5e02969ecc5b97df6d1bc49258`

### 실제 최종 답안
```json
{
  "document_answer": {
    "features": [
      {
        "code": "Wreck",
        "definition": "The ruined remains of a stranded or sunken vessel which has been rendered useless.",
        "permitted_primitives": [
          "point",
          "surface"
        ]
      }
    ],
    "attribute_bindings": [
      {
        "owner": "Wreck",
        "attribute": "categoryOfWreck",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "categoryOfWreck",
        "permitted_values": [
          "1",
          "2",
          "3",
          "4",
          "5"
        ],
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "definition": "Classification of a wrecked or ruined ship.",
        "attribute_definition": "Classification of a wrecked or ruined ship.",
        "global_listed_values": [
          {
            "label": "Non-Dangerous Wreck",
            "value": "1"
          },
          {
            "label": "Dangerous Wreck",
            "value": "2"
          },
          {
            "label": "Distributed Remains of Wreck",
            "value": "3"
          },
          {
            "label": "Wreck Showing Mast/Masts",
            "value": "4"
          },
          {
            "label": "Wreck Showing Any Portion of Hull or Superstructure",
            "value": "5"
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='categoryOfWreck']]",
        "listed_values": [
          {
            "label": "Non-Dangerous Wreck",
            "value": "1"
          },
          {
            "label": "Dangerous Wreck",
            "value": "2"
          },
          {
            "label": "Distributed Remains of Wreck",
            "value": "3"
          },
          {
            "label": "Wreck Showing Mast/Masts",
            "value": "4"
          },
          {
            "label": "Wreck Showing Any Portion of Hull or Superstructure",
            "value": "5"
          }
        ],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='categoryOfWreck']]"
      },
      {
        "owner": "Wreck",
        "attribute": "expositionOfSounding",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "expositionOfSounding",
        "permitted_values": [
          "1",
          "2",
          "3"
        ],
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "definition": "Indicates the relationship of the depth of a feature to the range of depth of the surrounding depth area.",
        "attribute_definition": "Indicates the relationship of the depth of a feature to the range of depth of the surrounding depth area.",
        "global_listed_values": [
          {
            "label": "Within the Range of Depth of the Surrounding Depth Area",
            "value": "1"
          },
          {
            "label": "Shoaler Than the Range of Depth of the Surrounding Depth Area",
            "value": "2"
          },
          {
            "label": "Deeper Than the Range of Depth of the Surrounding Depth Area",
            "value": "3"
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='expositionOfSounding']]",
        "listed_values": [
          {
            "label": "Within the Range of Depth of the Surrounding Depth Area",
            "value": "1"
          },
          {
            "label": "Shoaler Than the Range of Depth of the Surrounding Depth Area",
            "value": "2"
          },
          {
            "label": "Deeper Than the Range of Depth of the Surrounding Depth Area",
            "value": "3"
          }
        ],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='expositionOfSounding']]"
      },
      {
        "owner": "Wreck",
        "attribute": "featureName",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "featureName",
        "permitted_values": [],
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "definition": "Provides the name of an entity, defines the national language of the name, and provides the option to display the name at various system display settings.",
        "attribute_definition": "Provides the name of an entity, defines the national language of the name, and provides the option to display the name at various system display settings.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='featureName']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='featureName']]"
      },
      {
        "owner": "Wreck",
        "attribute": "height",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "height",
        "permitted_values": [],
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "definition": "The value of the vertical distance to the highest point of the feature, measured from a specified vertical datum.",
        "attribute_definition": "The value of the vertical distance to the highest point of the feature, measured from a specified vertical datum.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='height']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='height']]"
      },
      {
        "owner": "Wreck",
        "attribute": "interoperabilityIdentifier",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "interoperabilityIdentifier",
        "permitted_values": [],
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "definition": "A common unique identifier for entities which describe a single real-world feature, and which is used to identify instances of the feature in end-user systems where the feature may be included in multiple data product types.",
        "attribute_definition": "A common unique identifier for entities which describe a single real-world feature, and which is used to identify instances of the feature in end-user systems where the feature may be included in multiple data product types.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='interoperabilityIdentifier']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='interoperabilityIdentifier']]"
      },
      {
        "owner": "Wreck",
        "attribute": "qualityOfVerticalMeasurement",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "qualityOfVerticalMeasurement",
        "permitted_values": [
          "1",
          "2",
          "3",
          "4",
          "6",
          "7",
          "8",
          "9"
        ],
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "definition": "The reliability of the value of a sounding.",
        "attribute_definition": "The reliability of the value of a sounding.",
        "global_listed_values": [
          {
            "label": "Depth Known",
            "value": "1"
          },
          {
            "label": "Depth or Least Depth Unknown",
            "value": "2"
          },
          {
            "label": "Doubtful Sounding",
            "value": "3"
          },
          {
            "label": "Unreliable Sounding",
            "value": "4"
          },
          {
            "label": "Least Depth Known",
            "value": "6"
          },
          {
            "label": "Least Depth Unknown, Safe Clearance at Value Shown",
            "value": "7"
          },
          {
            "label": "Value Reported (Not Surveyed)",
            "value": "8"
          },
          {
            "label": "Value Reported (Not Confirmed)",
            "value": "9"
          },
          {
            "label": "Maintained Depth",
            "value": "10"
          },
          {
            "label": "Not Regularly Maintained",
            "value": "11"
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='qualityOfVerticalMeasurement']]",
        "listed_values": [
          {
            "label": "Depth Known",
            "value": "1"
          },
          {
            "label": "Depth or Least Depth Unknown",
            "value": "2"
          },
          {
            "label": "Doubtful Sounding",
            "value": "3"
          },
          {
            "label": "Unreliable Sounding",
            "value": "4"
          },
          {
            "label": "Least Depth Known",
            "value": "6"
          },
          {
            "label": "Least Depth Unknown, Safe Clearance at Value Shown",
            "value": "7"
          },
          {
            "label": "Value Reported (Not Surveyed)",
            "value": "8"
          },
          {
            "label": "Value Reported (Not Confirmed)",
            "value": "9"
          },
          {
            "label": "Maintained Depth",
            "value": "10"
          },
          {
            "label": "Not Regularly Maintained",
            "value": "11"
          }
        ],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='qualityOfVerticalMeasurement']]"
      },
      {
        "owner": "Wreck",
        "attribute": "radarConspicuous",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "radarConspicuous",
        "permitted_values": [],
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "definition": "A feature which returns a strong radar echo.",
        "attribute_definition": "A feature which returns a strong radar echo.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='radarConspicuous']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='radarConspicuous']]"
      },
      {
        "owner": "Wreck",
        "attribute": "reportedDate",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "reportedDate",
        "permitted_values": [],
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "definition": "The date that the item was observed, done, or investigated.",
        "attribute_definition": "The date that the item was observed, done, or investigated.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='reportedDate']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='reportedDate']]"
      },
      {
        "owner": "Wreck",
        "attribute": "status",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "status",
        "permitted_values": [
          "7",
          "13",
          "18"
        ],
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "definition": "The condition of an object at a given instant in time.",
        "attribute_definition": "The condition of an object at a given instant in time.",
        "global_listed_values": [
          {
            "label": "Permanent",
            "value": "1"
          },
          {
            "label": "Occasional",
            "value": "2"
          },
          {
            "label": "Recommended",
            "value": "3"
          },
          {
            "label": "Not in Use",
            "value": "4"
          },
          {
            "label": "Periodic/Intermittent",
            "value": "5"
          },
          {
            "label": "Reserved",
            "value": "6"
          },
          {
            "label": "Temporary",
            "value": "7"
          },
          {
            "label": "Private",
            "value": "8"
          },
          {
            "label": "Mandatory",
            "value": "9"
          },
          {
            "label": "Extinguished",
            "value": "11"
          },
          {
            "label": "Illuminated",
            "value": "12"
          },
          {
            "label": "Historic",
            "value": "13"
          },
          {
            "label": "Public",
            "value": "14"
          },
          {
            "label": "Synchronized",
            "value": "15"
          },
          {
            "label": "Watched",
            "value": "16"
          },
          {
            "label": "Unwatched",
            "value": "17"
          },
          {
            "label": "Existence Doubtful",
            "value": "18"
          },
          {
            "label": "Buoyed",
            "value": "28"
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='status']]",
        "listed_values": [
          {
            "label": "Permanent",
            "value": "1"
          },
          {
            "label": "Occasional",
            "value": "2"
          },
          {
            "label": "Recommended",
            "value": "3"
          },
          {
            "label": "Not in Use",
            "value": "4"
          },
          {
            "label": "Periodic/Intermittent",
            "value": "5"
          },
          {
            "label": "Reserved",
            "value": "6"
          },
          {
            "label": "Temporary",
            "value": "7"
          },
          {
            "label": "Private",
            "value": "8"
          },
          {
            "label": "Mandatory",
            "value": "9"
          },
          {
            "label": "Extinguished",
            "value": "11"
          },
          {
            "label": "Illuminated",
            "value": "12"
          },
          {
            "label": "Historic",
            "value": "13"
          },
          {
            "label": "Public",
            "value": "14"
          },
          {
            "label": "Synchronized",
            "value": "15"
          },
          {
            "label": "Watched",
            "value": "16"
          },
          {
            "label": "Unwatched",
            "value": "17"
          },
          {
            "label": "Existence Doubtful",
            "value": "18"
          },
          {
            "label": "Buoyed",
            "value": "28"
          }
        ],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='status']]"
      },
      {
        "owner": "Wreck",
        "attribute": "techniqueOfVerticalMeasurement",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "techniqueOfVerticalMeasurement",
        "permitted_values": [
          "1",
          "2",
          "3",
          "4",
          "5",
          "8",
          "9",
          "10",
          "11",
          "12",
          "13",
          "15",
          "16",
          "17",
          "18"
        ],
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "definition": "Survey method used to obtain depth information.",
        "attribute_definition": "Survey method used to obtain depth information.",
        "global_listed_values": [
          {
            "label": "Found by Echo Sounder",
            "value": "1"
          },
          {
            "label": "Found by Side Scan Sonar",
            "value": "2"
          },
          {
            "label": "Found by Multi Beam",
            "value": "3"
          },
          {
            "label": "Found by Diver",
            "value": "4"
          },
          {
            "label": "Found by Lead Line",
            "value": "5"
          },
          {
            "label": "Swept by Vertical Acoustic System",
            "value": "8"
          },
          {
            "label": "Found by Electromagnetic Sensor",
            "value": "9"
          },
          {
            "label": "Photogrammetry",
            "value": "10"
          },
          {
            "label": "Satellite Imagery",
            "value": "11"
          },
          {
            "label": "Found by Levelling",
            "value": "12"
          },
          {
            "label": "Swept by Side Scan Sonar",
            "value": "13"
          },
          {
            "label": "Found by LIDAR",
            "value": "15"
          },
          {
            "label": "Synthetic Aperture Radar",
            "value": "16"
          },
          {
            "label": "Hyperspectral Imagery",
            "value": "17"
          },
          {
            "label": "Mechanically Swept",
            "value": "18"
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='techniqueOfVerticalMeasurement']]",
        "listed_values": [
          {
            "label": "Found by Echo Sounder",
            "value": "1"
          },
          {
            "label": "Found by Side Scan Sonar",
            "value": "2"
          },
          {
            "label": "Found by Multi Beam",
            "value": "3"
          },
          {
            "label": "Found by Diver",
            "value": "4"
          },
          {
            "label": "Found by Lead Line",
            "value": "5"
          },
          {
            "label": "Swept by Vertical Acoustic System",
            "value": "8"
          },
          {
            "label": "Found by Electromagnetic Sensor",
            "value": "9"
          },
          {
            "label": "Photogrammetry",
            "value": "10"
          },
          {
            "label": "Satellite Imagery",
            "value": "11"
          },
          {
            "label": "Found by Levelling",
            "value": "12"
          },
          {
            "label": "Swept by Side Scan Sonar",
            "value": "13"
          },
          {
            "label": "Found by LIDAR",
            "value": "15"
          },
          {
            "label": "Synthetic Aperture Radar",
            "value": "16"
          },
          {
            "label": "Hyperspectral Imagery",
            "value": "17"
          },
          {
            "label": "Mechanically Swept",
            "value": "18"
          }
        ],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='techniqueOfVerticalMeasurement']]"
      },
      {
        "owner": "Wreck",
        "attribute": "valueOfSounding",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "valueOfSounding",
        "permitted_values": [],
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "definition": "The value of the measurement of a sounding relative to the chart datum.",
        "attribute_definition": "The value of the measurement of a sounding relative to the chart datum.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='valueOfSounding']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='valueOfSounding']]"
      },
      {
        "owner": "Wreck",
        "attribute": "visualProminence",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "visualProminence",
        "permitted_values": [
          "1",
          "2",
          "3"
        ],
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "definition": "The extent to which a feature, either natural or artificial, is visible from seaward.",
        "attribute_definition": "The extent to which a feature, either natural or artificial, is visible from seaward.",
        "global_listed_values": [
          {
            "label": "Visually Conspicuous",
            "value": "1"
          },
          {
            "label": "Not Visually Conspicuous",
            "value": "2"
          },
          {
            "label": "Prominent",
            "value": "3"
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='visualProminence']]",
        "listed_values": [
          {
            "label": "Visually Conspicuous",
            "value": "1"
          },
          {
            "label": "Not Visually Conspicuous",
            "value": "2"
          },
          {
            "label": "Prominent",
            "value": "3"
          }
        ],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='visualProminence']]"
      },
      {
        "owner": "Wreck",
        "attribute": "waterLevelEffect",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "waterLevelEffect",
        "permitted_values": [
          "1",
          "2",
          "3",
          "4",
          "5"
        ],
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "definition": "The effect of the surrounding water on an object.",
        "attribute_definition": "The effect of the surrounding water on an object.",
        "global_listed_values": [
          {
            "label": "Partly Submerged at High Water",
            "value": "1"
          },
          {
            "label": "Always Dry",
            "value": "2"
          },
          {
            "label": "Always Under Water/Submerged",
            "value": "3"
          },
          {
            "label": "Covers and Uncovers",
            "value": "4"
          },
          {
            "label": "Awash",
            "value": "5"
          },
          {
            "label": "Subject to Inundation or Flooding",
            "value": "6"
          },
          {
            "label": "Floating",
            "value": "7"
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='waterLevelEffect']]",
        "listed_values": [
          {
            "label": "Partly Submerged at High Water",
            "value": "1"
          },
          {
            "label": "Always Dry",
            "value": "2"
          },
          {
            "label": "Always Under Water/Submerged",
            "value": "3"
          },
          {
            "label": "Covers and Uncovers",
            "value": "4"
          },
          {
            "label": "Awash",
            "value": "5"
          },
          {
            "label": "Subject to Inundation or Flooding",
            "value": "6"
          },
          {
            "label": "Floating",
            "value": "7"
          }
        ],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='waterLevelEffect']]"
      },
      {
        "owner": "Wreck",
        "attribute": "scaleMinimum",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "scaleMinimum",
        "permitted_values": [],
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "definition": "The minimum scale at which the feature may be used for example for ECDIS presentation.",
        "attribute_definition": "The minimum scale at which the feature may be used for example for ECDIS presentation.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='scaleMinimum']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='scaleMinimum']]"
      },
      {
        "owner": "Wreck",
        "attribute": "information",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "information",
        "permitted_values": [],
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "definition": "Textual information about the feature. The information may be provided as a string of text or as a file name of a single external text file that contains the text.",
        "attribute_definition": "Textual information about the feature. The information may be provided as a string of text or as a file name of a single external text file that contains the text.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='information']]"
      },
      {
        "owner": "Wreck",
        "attribute": "pictorialRepresentation",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "pictorialRepresentation",
        "permitted_values": [],
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "definition": "The file name of an externally referenced picture file.",
        "attribute_definition": "The file name of an externally referenced picture file.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='pictorialRepresentation']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='pictorialRepresentation']]"
      },
      {
        "owner": "Wreck",
        "attribute": "defaultClearanceDepth",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "defaultClearanceDepth",
        "permitted_values": [],
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "definition": "The depth value determined for an underwater hazard of unknown depth, based on the depth of the surrounding area.",
        "attribute_definition": "The depth value determined for an underwater hazard of unknown depth, based on the depth of the surrounding area.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='defaultClearanceDepth']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='defaultClearanceDepth']]"
      },
      {
        "owner": "Wreck",
        "attribute": "surroundingDepth",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "surroundingDepth",
        "permitted_values": [],
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "definition": "The depth value determined for seabed around an underwater hazard, based on the depth of the surrounding area.",
        "attribute_definition": "The depth value determined for seabed around an underwater hazard, based on the depth of the surrounding area.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='surroundingDepth']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='surroundingDepth']]"
      }
    ],
    "definition_quote": "The ruined remains of a stranded or sunken vessel which has been rendered useless.",
    "source_ref": "data/s101_feature_catalogue_v2_parsed.json",
    "source_sha256": "0d26c66d0e1afd8a6ae33629e9bc1bb929c6a3735ccd1d60f637d149a54cad37",
    "evidence": {
      "edition": "2.0.0",
      "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
      "parsed_source_sha256": "0d26c66d0e1afd8a6ae33629e9bc1bb929c6a3735ccd1d60f637d149a54cad37",
      "source_ref": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
      "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
      "locators": [
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='categoryOfWreck']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='expositionOfSounding']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='featureName']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='height']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='interoperabilityIdentifier']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='qualityOfVerticalMeasurement']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='radarConspicuous']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='reportedDate']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='status']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='techniqueOfVerticalMeasurement']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='valueOfSounding']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='visualProminence']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='waterLevelEffect']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='scaleMinimum']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='information']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='pictorialRepresentation']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='defaultClearanceDepth']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='surroundingDepth']]"
      ],
      "claim_source_links": [
        {
          "claim": "The ruined remains of a stranded or sunken vessel which has been rendered useless.",
          "source_ref": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
          "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
          "definition_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='definition']",
          "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='definition']"
        }
      ]
    }
  },
  "search_executed": false,
  "execution_status": "COMPLETED",
  "source_coverage": {},
  "per_task_status": {},
  "mapping_provenance": {
    "version": "emitted_output_v1",
    "root": "final_state.final_dict",
    "retrieved_text_used_as_answer": false,
    "reference_used_for_mapping": false,
    "structured_document_answer_present": true
  },
  "status": "COMPLETED",
  "blocker": null,
  "clarification_request": [],
  "answer_text": "S-101 Feature Catalogue 2.0.0\n\nWreck: The ruined remains of a stranded or sunken vessel which has been rendered useless.\n허용 기하: point, surface\n\n- categoryOfWreck: Classification of a wrecked or ruined ship. (다중도 0..1; 허용 코드 1, 2, 3, 4, 5)\n\n- expositionOfSounding: Indicates the relationship of the depth of a feature to the range of depth of the surrounding depth area. (다중도 0..1; 허용 코드 1, 2, 3)\n\n- featureName: Provides the name of an entity, defines the national language of the name, and provides the option to display the name at various system display settings. (다중도 0..*; 허용 코드 별도 제한 없음)\n\n- height: The value of the vertical distance to the highest point of the feature, measured from a specified vertical datum. (다중도 0..1; 허용 코드 별도 제한 없음)\n\n- interoperabilityIdentifier: A common unique identifier for entities which describe a single real-world feature, and which is used to identify instances of the feature in end-user systems where the feature may be included in multiple data product types. (다중도 0..1; 허용 코드 별도 제한 없음)\n\n- qualityOfVerticalMeasurement: The reliability of the value of a sounding. (다중도 0..*; 허용 코드 1, 2, 3, 4, 6, 7, 8, 9)\n\n- radarConspicuous: A feature which returns a strong radar echo. (다중도 0..1; 허용 코드 별도 제한 없음)\n\n- reportedDate: The date that the item was observed, done, or investigated. (다중도 0..1; 허용 코드 별도 제한 없음)\n\n- status: The condition of an object at a given instant in time. (다중도 0..*; 허용 코드 7, 13, 18)\n\n- techniqueOfVerticalMeasurement: Survey method used to obtain depth information. (다중도 0..*; 허용 코드 1, 2, 3, 4, 5, 8, 9, 10, 11, 12, 13, 15, 16, 17, 18)\n\n- valueOfSounding: The value of the measurement of a sounding relative to the chart datum. (다중도 0..1; 허용 코드 별도 제한 없음)\n\n- visualProminence: The extent to which a feature, either natural or artificial, is visible from seaward. (다중도 0..1; 허용 코드 1, 2, 3)\n\n- waterLevelEffect: The effect of the surrounding water on an object. (다중도 1..1; 허용 코드 1, 2, 3, 4, 5)\n\n- scaleMinimum: The minimum scale at which the feature may be used for example for ECDIS presentation. (다중도 0..1; 허용 코드 별도 제한 없음)\n\n- information: Textual information about the feature. The information may be provided as a string of text or as a file name of a single external text file that contains the text. (다중도 0..*; 허용 코드 별도 제한 없음)\n\n- pictorialRepresentation: The file name of an externally referenced picture file. (다중도 0..1; 허용 코드 별도 제한 없음)\n\n- defaultClearanceDepth: The depth value determined for an underwater hazard of unknown depth, based on the depth of the surrounding area. (다중도 0..1; 허용 코드 별도 제한 없음)\n\n- surroundingDepth: The depth value determined for seabed around an underwater hazard, based on the depth of the surrounding area. (다중도 1..1; 허용 코드 별도 제한 없음)\n\n근거: data/s101_feature_catalogue_v2_parsed.json; //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='categoryOfWreck']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='expositionOfSounding']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='featureName']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='height']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='interoperabilityIdentifier']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='qualityOfVerticalMeasurement']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='radarConspicuous']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='reportedDate']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='status']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='techniqueOfVerticalMeasurement']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='valueOfSounding']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='visualProminence']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='waterLevelEffect']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='scaleMinimum']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='information']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='pictorialRepresentation']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='defaultClearanceDepth']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='surroundingDepth']]"
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q2_03.json)
```json
{
  "case_id": "PILOT_Q2_03",
  "required_task_obligations": [
    "explain_wreck_attribute_bindings"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_084",
  "answer_sha256": "27d29009517ec7fef0a32bf4b2cd89f40b8b5e5e02969ecc5b97df6d1bc49258",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "1bd466645967b4ba4d608cec2cdf002501383196f8f57ec10ce0e4928a302b5c",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_083 — Find wrecks intersecting the selected area.

답안 hash: `5eef97a49274c5876dae03fd7c78f6c523a13d9402614cf26f8aac11eb6b6718`

### 실제 최종 답안
```json
{
  "document_answer": {
    "features": [],
    "attribute_bindings": []
  },
  "search_executed": null,
  "execution_status": "NEEDS_USER_INPUT",
  "source_coverage": {},
  "per_task_status": {},
  "mapping_provenance": {
    "version": "emitted_output_v1",
    "root": "final_state.final_dict",
    "retrieved_text_used_as_answer": false,
    "reference_used_for_mapping": false,
    "structured_document_answer_present": false
  },
  "clarification_request": [
    "교차 검색할 영역의 다각형을 지도에서 선택해주세요. 기준 영역이 없어 공간 검색을 실행하지 않았습니다."
  ],
  "status": "NEEDS_USER_INPUT",
  "blocker": "MISSING_REFERENCE_GEOMETRY",
  "answer_text": "교차 검색할 영역의 다각형을 지도에서 선택해주세요. 기준 영역이 없어 공간 검색을 실행하지 않았습니다."
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q3_03.json)
```json
{
  "case_id": "PILOT_Q3_03",
  "required_task_obligations": [
    "require_selected_aoi",
    "verify_coverage",
    "search_intersections_if_aoi_available",
    "request_aoi_when_missing"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "No selected geometry is provided by this benchmark input; an arbitrary viewport is not a substitute."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_083",
  "answer_sha256": "5eef97a49274c5876dae03fd7c78f6c523a13d9402614cf26f8aac11eb6b6718",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "bf237938049fd36913381e7d95badd87ad7cfb1d75f5ad33bd9e0b330826de55",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_082 — Find marine place names within 5 km of Dokdo.

답안 hash: `e4c3a2cfb61f4bc49b0e1bba2fd444e7737b5a88d22fe8aa76e584b023a2313b`

### 실제 최종 답안
```json
{
  "answer_text": "Marine place names within 5 km of Dokdo: [marine place names]",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "validator_blockers": [
    "BLOCKED_DATA: public catalogue document evidence unavailable"
  ],
  "status": "BLOCKED_DATA",
  "execution_status": "BLOCKED_DATA",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q4_03.json)
```json
{
  "case_id": "PILOT_Q4_03",
  "required_task_obligations": [
    "resolve_approved_anchor",
    "search_fixed_gazetteer_5000m",
    "report_source_bound_objects"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_082",
  "answer_sha256": "e4c3a2cfb61f4bc49b0e1bba2fd444e7737b5a88d22fe8aa76e584b023a2313b",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "231c956d4332c1e270dd656ae94819d035c634810e2a58e8861ec7419580985d",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_081 — 등대의 S-101 객체 유형과 정의를 알려줘.

답안 hash: `1afc5d34b69a70be746b8d2993f1a7db12f521b5033114b926e741f16b1dc59f`

### 실제 최종 답안
```json
{
  "answer_text": "등대의 S-101 객체는 주로 해양 경관을 촬영하는 장비로, 주로 해안 지역에서 사용됩니다. 이 객체는 일반적으로 해양 경관을 촬영하는 데 사용됩니다.",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q1_01.json)
```json
{
  "case_id": "PILOT_Q1_01",
  "required_task_obligations": [
    "explain_structure_and_light_distinction",
    "explain_conditional_feature_mapping"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "single_Lighthouse_feature_assertion",
    "global_colour_codes_for_feature_binding"
  ],
  "scope_notes": [
    "Landmark/Building describe conditional structure alternatives; LightAllAround/LightSectored describe light alternatives. Listing these for explanation does not assert all must exist in one physical lighthouse."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_081",
  "answer_sha256": "1afc5d34b69a70be746b8d2993f1a7db12f521b5033114b926e741f16b1dc59f",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "bec2c43b71d59cc1dc18c281dd6c1bb64c39c9cfb606e6712f93d164b0f7d85d",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_080 — Find marine place names within 5 km of Dokdo.

답안 hash: `ef7a9b7ee52e3f069fd9da9f1da3b07394a8edcda10478bb627c34b2392d1a11`

### 실제 최종 답안
```json
{
  "document_answer": {
    "features": [],
    "attribute_bindings": []
  },
  "search_executed": false,
  "execution_status": "BLOCKED",
  "source_coverage": {},
  "per_task_status": {},
  "mapping_provenance": {
    "version": "emitted_output_v1",
    "root": "final_state.final_dict",
    "retrieved_text_used_as_answer": false,
    "reference_used_for_mapping": false,
    "structured_document_answer_present": false
  },
  "status": "BLOCKED",
  "blocker": "DATA_COVERAGE_UNVERIFIED",
  "clarification_request": [],
  "answer_text": "현재 연결된 데이터의 공간 범위가 검증되지 않아 공간 검색을 실행하지 않았습니다. 검색 결과가 0건이라는 뜻은 아닙니다."
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q4_03.json)
```json
{
  "case_id": "PILOT_Q4_03",
  "required_task_obligations": [
    "resolve_approved_anchor",
    "search_fixed_gazetteer_5000m",
    "report_source_bound_objects"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_080",
  "answer_sha256": "ef7a9b7ee52e3f069fd9da9f1da3b07394a8edcda10478bb627c34b2392d1a11",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "7bb1ec3b6d7659b5c43bf5fe121b42786ab30ce3f0f14c22d7ad99f1f042f4f4",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_079 — 독도 부근에서 가장 가까운 등대를 찾아줘.

답안 hash: `0a982fe1daa1bb7b56f1e74892a6f1c1c6ce36587f1e67bdfda04f1a6695cd05`

### 실제 최종 답안
```json
{
  "answer_text": "The closest lighthouse to Dokdo is located at the Dokdo Lighthouse.",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q3_01.json)
```json
{
  "case_id": "PILOT_Q3_01",
  "required_task_obligations": [
    "resolve_reference",
    "resolve_lighthouse_target_conditions",
    "verify_coverage",
    "find_nearest",
    "report_objects_or_unresolved_reason"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "User-approved source-bound safe abstention; document explanations are separately evaluated optional partial output."
  ],
  "expected_spatial_behavior": {
    "accepted_states": [
      "BLOCKED_DATA",
      "DATA_OUT_OF_SCOPE"
    ],
    "required_disclosure": "Current connected snapshot cannot determine the answer for the requested spatial extent",
    "per_target": {
      "Lighthouse": {
        "status": "BLOCKED_DATA",
        "object_ids": null
      }
    },
    "empty_result_as_answer_forbidden": true,
    "claim_spatial_success_forbidden": true
  }
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_079",
  "answer_sha256": "0a982fe1daa1bb7b56f1e74892a6f1c1c6ce36587f1e67bdfda04f1a6695cd05",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "db28522bafed7009b9e01e233b90beb2c30e10e0c9a2fdf8be50f0996de0f9a5",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_078 — What is a wreck in S-101?

답안 hash: `98b5717bbcdba74e6205e077f6e4d4b5528d9aae66bc7c2a9907b9c03ef05ec6`

### 실제 최종 답안
```json
{
  "answer_text": "A wreck is a wrecked or ruined ship that has been damaged beyond repair and is no longer navigable or useful.",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q1_03.json)
```json
{
  "case_id": "PILOT_Q1_03",
  "required_task_obligations": [
    "explain_wreck_definition"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_078",
  "answer_sha256": "98b5717bbcdba74e6205e077f6e4d4b5528d9aae66bc7c2a9907b9c03ef05ec6",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "0baa1b8a85e207f521cb0c212fa07a7e782da0e52a9de5db8ecea9e7cdcf83e7",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_077 — 등대의 S-101 객체 유형과 정의를 알려줘.

답안 hash: `f5cb414d607407946d6acb2800c7bd84133496079635335d0d3392514568e462`

### 실제 최종 답안
```json
{
  "document_answer": {
    "features": [],
    "attribute_bindings": []
  },
  "search_executed": null,
  "execution_status": "PARTIAL",
  "source_coverage": {},
  "per_task_status": {},
  "mapping_provenance": {
    "version": "emitted_output_v1",
    "root": "final_state.final_dict",
    "retrieved_text_used_as_answer": false,
    "reference_used_for_mapping": false,
    "structured_document_answer_present": false
  },
  "status": "PARTIAL",
  "blocker": "OUTPUT_OBLIGATIONS_UNMET",
  "clarification_request": [],
  "answer_text": "요청한 결과에 필요한 근거가 아직 부족합니다: 요청한 용어·속성과 출처가 연결된 설명 (관련 문서 검색만으로는 미충족)\n질의와 관련된 근거 문서 2건을 찾았습니다. 대표 근거는 S-101_Annex_A_DCEG_Ed_2.0.0 / page_573이며, 내용 요지는 다음과 같습니다: Data Classification and Encoding Guide 553 S-101 Annex A December 2024 Edition 2.0.0 20.16 Light vessel IHO Definition: LIGHT VESSEL. A distinctively marked vessel anchored or moored at a charted point, to serve as an ai..."
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q1_01.json)
```json
{
  "case_id": "PILOT_Q1_01",
  "required_task_obligations": [
    "explain_structure_and_light_distinction",
    "explain_conditional_feature_mapping"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "single_Lighthouse_feature_assertion",
    "global_colour_codes_for_feature_binding"
  ],
  "scope_notes": [
    "Landmark/Building describe conditional structure alternatives; LightAllAround/LightSectored describe light alternatives. Listing these for explanation does not assert all must exist in one physical lighthouse."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_077",
  "answer_sha256": "f5cb414d607407946d6acb2800c7bd84133496079635335d0d3392514568e462",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "767c7c99ba45980231da9ff1bfea195e4f3d730a653661050b11e1bf107e3d76",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_076 — 부산항 영역 안의 정박지를 찾아줘.

답안 hash: `b9c0d13a124c58ab68adbb5f798c7851788450f0489beee532ee8ae8e5de9a39`

### 실제 최종 답안
```json
{
  "answer_text": "The watercraft located within the Busan Port boundary.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "document_answer": {
    "features": [],
    "attribute_bindings": [],
    "evidence": {
      "edition": "2.0.0",
      "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
      "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
      "locators": [],
      "claim_source_links": []
    }
  },
  "status": "COMPLETED",
  "execution_status": "COMPLETED",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q3_02.json)
```json
{
  "case_id": "PILOT_Q3_02",
  "required_task_obligations": [
    "resolve_official_port_polygon",
    "verify_coverage",
    "search_within_polygon",
    "report_objects_or_unresolved_reason"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "Object IDs refer to frozen snapshot records, not deduplicated physical facilities or the whole legal port."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_076",
  "answer_sha256": "b9c0d13a124c58ab68adbb5f798c7851788450f0489beee532ee8ae8e5de9a39",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "55f777bcbc55b58632d3e64ea737b141d4d43edc0b5e0e3d122761768c9e54c3",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_075 — 독도 주변 반경 5000m의 해양지명을 찾아줘.

답안 hash: `6877ef6e5fe6d1048327f22010d3c697a3148ac2b2b42dfbc86d12719189dd3e`

### 실제 최종 답안
```json
{
  "answer_text": "독도 주변 반경 5000m의 해양지명은 다음과 같습니다:\n1. 독도\n2. 독도 남쪽 해안\n3. 독도 서쪽 해안\n4. 독도 동쪽 해안\n5. 독도 북쪽 해안",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q4_02.json)
```json
{
  "case_id": "PILOT_Q4_02",
  "required_task_obligations": [
    "resolve_approved_anchor",
    "search_fixed_gazetteer_5000m",
    "report_source_bound_objects"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_075",
  "answer_sha256": "6877ef6e5fe6d1048327f22010d3c697a3148ac2b2b42dfbc86d12719189dd3e",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "3fee1128039fac1f9b965f054f8981475f3518005c3545fcc48c270b911c61d5",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_074 — 독도 주변 반경 5km의 해양지명을 찾아줘.

답안 hash: `81ab11d732b479081e6e416b5208218e5fba3f1bf5a286f1d8d8ea9be7779d21`

### 실제 최종 답안
```json
{
  "answer_text": "Dokdo 주변 반경 5km의 해양지명은 '독도'입니다.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "document_answer": {
    "features": [],
    "attribute_bindings": [],
    "evidence": {
      "edition": "2.0.0",
      "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
      "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
      "locators": [],
      "claim_source_links": []
    }
  },
  "status": "COMPLETED",
  "execution_status": "COMPLETED",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q4_01.json)
```json
{
  "case_id": "PILOT_Q4_01",
  "required_task_obligations": [
    "resolve_approved_anchor",
    "search_fixed_gazetteer_5000m",
    "report_source_bound_objects"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_074",
  "answer_sha256": "81ab11d732b479081e6e416b5208218e5fba3f1bf5a286f1d8d8ea9be7779d21",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "d1490712c1cc1a1f46b479182fd614564fee2b4857c42f568e313c5ced5ee248",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_073 — 부산항 주변 2km의 정박지와 제한구역을 찾아 비교해줘.

답안 hash: `fdd434879ef448e978bfa5c2c6acb364e58e3b6c3c1971d4bbaa5bd8c2257972`

### 실제 최종 답안
```json
{
  "answer_text": "在距离'부산항'2公里范围内，有以下锚地和限制区域供您参考：",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q5_02.json)
```json
{
  "case_id": "PILOT_Q5_02",
  "required_task_obligations": [
    "resolve_reference",
    "verify_both_target_coverages",
    "search_both_targets_2000m",
    "compare_target_results",
    "disclose_subset_limitations"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "Object IDs refer to frozen snapshot records, not deduplicated physical facilities or the whole legal port."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_073",
  "answer_sha256": "fdd434879ef448e978bfa5c2c6acb364e58e3b6c3c1971d4bbaa5bd8c2257972",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "eba175bdc65a281fc69e164d2e7ba1b683cbc523d5d38c6891ed4a1b3cb868a8",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_072 — What is a wreck in S-101?

답안 hash: `7250e6af51ebdbdca7ba141e3a5d486fffe4db6bb0b143d394344bf3e8dd3f7c`

### 실제 최종 답안
```json
{
  "answer_text": "A wreck in S-101 refers to a shipwreck or wreckage found within the S-101 area. This area is part of the S-101 research snapshot, which includes the Busan research subset. The wreck is not covered by the Busan regional aids, so it is not included in the coverage.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "validator_blockers": [
    "BLOCKED_CONFIG: explicit research source required",
    "BLOCKED_CONFIG: unsupported operation: None"
  ],
  "status": "BLOCKED_CONFIG",
  "execution_status": "BLOCKED_CONFIG",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q1_03.json)
```json
{
  "case_id": "PILOT_Q1_03",
  "required_task_obligations": [
    "explain_wreck_definition"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_072",
  "answer_sha256": "7250e6af51ebdbdca7ba141e3a5d486fffe4db6bb0b143d394344bf3e8dd3f7c",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "02b2a1bc8680e1a2d18889ae1da0b5aef0c20166bfb714473e984c4d7842a2c8",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_071 — What is a wreck in S-101?

답안 hash: `7250e6af51ebdbdca7ba141e3a5d486fffe4db6bb0b143d394344bf3e8dd3f7c`

### 실제 최종 답안
```json
{
  "answer_text": "A wreck in S-101 refers to a shipwreck or wreckage found within the S-101 area. This area is part of the S-101 research snapshot, which includes the Busan research subset. The wreck is not covered by the Busan regional aids, so it is not included in the coverage.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "validator_blockers": [
    "BLOCKED_CONFIG: explicit research source required",
    "BLOCKED_CONFIG: unsupported operation: None"
  ],
  "status": "BLOCKED_CONFIG",
  "execution_status": "BLOCKED_CONFIG",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q1_03.json)
```json
{
  "case_id": "PILOT_Q1_03",
  "required_task_obligations": [
    "explain_wreck_definition"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_071",
  "answer_sha256": "7250e6af51ebdbdca7ba141e3a5d486fffe4db6bb0b143d394344bf3e8dd3f7c",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "02b2a1bc8680e1a2d18889ae1da0b5aef0c20166bfb714473e984c4d7842a2c8",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_070 — S-101에서 정박지는 어떤 객체야?

답안 hash: `e2f8fd4d257d26d1788567e59e6b0b74796b24b67e92dc3e6d33f4027e14aec9`

### 실제 최종 답안
```json
{
  "answer_text": "S-101에서 정박지는 'ship' 객체입니다.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "document_answer": {
    "features": [],
    "attribute_bindings": [],
    "evidence": {
      "edition": "2.0.0",
      "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
      "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
      "locators": [],
      "claim_source_links": []
    }
  },
  "status": "COMPLETED",
  "execution_status": "COMPLETED",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q1_02.json)
```json
{
  "case_id": "PILOT_Q1_02",
  "required_task_obligations": [
    "explain_anchorage_area_definition"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_070",
  "answer_sha256": "e2f8fd4d257d26d1788567e59e6b0b74796b24b67e92dc3e6d33f4027e14aec9",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "ce2444a8a93b02c4c28a87c1ef244e156e28739136a93268b89316088a7e3be8",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_069 — S-101 등대의 색상 속성과 허용 값을 알려줘.

답안 hash: `0686f9b2129c9930f9ed2353c1e6a025168f99b592e008a2c6b6cd9e3e4cfe26`

### 실제 최종 답안
```json
{
  "answer_text": "등대의 색상 속성과 허용 값은 다음과 같습니다:\n- 색상: [색상 정보]\n- 허용 값: [허용 값 정보]",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q2_01.json)
```json
{
  "case_id": "PILOT_Q2_01",
  "required_task_obligations": [
    "distinguish_structure_and_light_colour",
    "explain_feature_bound_permitted_values"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "single_Lighthouse_feature_assertion",
    "global_colour_codes_for_feature_binding"
  ],
  "scope_notes": [
    "Landmark/Building describe conditional structure alternatives; LightAllAround/LightSectored describe light alternatives. Listing these for explanation does not assert all must exist in one physical lighthouse."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_069",
  "answer_sha256": "0686f9b2129c9930f9ed2353c1e6a025168f99b592e008a2c6b6cd9e3e4cfe26",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "ee4811ee99f51fccc8ba9e41cb2e965fb32738b6d9e36aa1850c833b9018d5dc",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_068 — S-101 Wreck 정의의 원문과 Feature Catalogue 출처를 알려줘.

답안 hash: `818439cee0f9d814e15c7829c8c8e94c2470949932c47c293982c3dd43bb100d`

### 실제 최종 답안
```json
{
  "answer_text": "Wreck는 해도 ENC에서 정의된 해상물로, 주로 해상물의 일부를 포함하는 것으로 정의됩니다. 이 정의는 주로 해상물의 일부를 포함하는 해상물에 대한 정의입니다.",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q6_01.json)
```json
{
  "case_id": "PILOT_Q6_01",
  "required_task_obligations": [
    "provide_wreck_definition_text",
    "cite_catalogue_edition_and_locator"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_068",
  "answer_sha256": "818439cee0f9d814e15c7829c8c8e94c2470949932c47c293982c3dd43bb100d",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "1402adc84716b9f8e02a42b4fe549433d88b8e8bc2f395d071445aa631aaaaf0",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_067 — 등대의 S-101 객체 유형과 정의를 알려줘.

답안 hash: `f874ac556e85c8560e0f554651050c31e50091452df0747f76e5fb0c68799487`

### 실제 최종 답안
```json
{
  "answer_text": "등대의 S-101 객체는 주로 해양 경관과 관련된 장비로, 주로 해상 경관을 촬영하거나 해양 생태계를 연구하는 데 사용됩니다. 이 객체는 주로 경상북도의 해안 지역에서 발견되며, 특히 경상북도의 해안 지역에서 가장 많이 사용됩니다. 이 객체는 해양 경관을 촬영하거나 해양 생태계를 연구하는 데 사용되는 장비로, 주로 해양 경관을 촬영하거나 해양 생태계를 연구하는 데 사용됩니다.",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q1_01.json)
```json
{
  "case_id": "PILOT_Q1_01",
  "required_task_obligations": [
    "explain_structure_and_light_distinction",
    "explain_conditional_feature_mapping"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "single_Lighthouse_feature_assertion",
    "global_colour_codes_for_feature_binding"
  ],
  "scope_notes": [
    "Landmark/Building describe conditional structure alternatives; LightAllAround/LightSectored describe light alternatives. Listing these for explanation does not assert all must exist in one physical lighthouse."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_067",
  "answer_sha256": "f874ac556e85c8560e0f554651050c31e50091452df0747f76e5fb0c68799487",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "b76c65749791a0027626d42594d6eff19d062157148e42cace16ca8f08fa457f",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_066 — Which attributes describe a Wreck in S-101?

답안 hash: `06bf2a032b8f95ff00a7eff8b9760dea6896e1563131f1ab9b7550e61d42bc63`

### 실제 최종 답안
```json
{
  "answer_text": "A wreck is described in S-101, located within the scope of the S-101 feature catalogue.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "document_answer": {
    "features": [
      {
        "code": "Wreck",
        "xml_type": "S100_FC_FeatureType",
        "definition": "The ruined remains of a stranded or sunken vessel which has been rendered useless.",
        "permitted_primitives": [
          "point",
          "surface"
        ],
        "bindings": [
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "categoryOfWreck"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [
              "1",
              "2",
              "3",
              "4",
              "5"
            ],
            "xml_child_index": 5
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "expositionOfSounding"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [
              "1",
              "2",
              "3"
            ],
            "xml_child_index": 6
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "featureName"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [],
            "xml_child_index": 7
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "height"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 8
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "interoperabilityIdentifier"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 9
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "qualityOfVerticalMeasurement"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [
              "1",
              "2",
              "3",
              "4",
              "6",
              "7",
              "8",
              "9"
            ],
            "xml_child_index": 10
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "radarConspicuous"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 11
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "reportedDate"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 12
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "status"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [
              "7",
              "13",
              "18"
            ],
            "xml_child_index": 13
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "techniqueOfVerticalMeasurement"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [
              "1",
              "2",
              "3",
              "4",
              "5",
              "8",
              "9",
              "10",
              "11",
              "12",
              "13",
              "15",
              "16",
              "17",
              "18"
            ],
            "xml_child_index": 14
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "valueOfSounding"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 15
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "visualProminence"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [
              "1",
              "2",
              "3"
            ],
            "xml_child_index": 16
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "waterLevelEffect"
              }
            ],
            "lower": "1",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [
              "1",
              "2",
              "3",
              "4",
              "5"
            ],
            "xml_child_index": 17
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "scaleMinimum"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 18
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "information"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [],
            "xml_child_index": 19
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "pictorialRepresentation"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 20
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "defaultClearanceDepth"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 21
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "surroundingDepth"
              }
            ],
            "lower": "1",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 22
          },
          {
            "kind": "informationBinding",
            "references": [
              {
                "type": "association",
                "ref": "AdditionalInformation"
              },
              {
                "type": "role",
                "ref": "theInformation"
              },
              {
                "type": "informationType",
                "ref": "NauticalInformation"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 23
          },
          {
            "kind": "featureBinding",
            "references": [
              {
                "type": "association",
                "ref": "StructureEquipment"
              },
              {
                "type": "role",
                "ref": "theEquipment"
              },
              {
                "type": "featureType",
                "ref": "Daymark"
              },
              {
                "type": "featureType",
                "ref": "DistanceMark"
              },
              {
                "type": "featureType",
                "ref": "FogSignal"
              },
              {
                "type": "featureType",
                "ref": "LightAllAround"
              },
              {
                "type": "featureType",
                "ref": "LightFogDetector"
              },
              {
                "type": "featureType",
                "ref": "PhysicalAISAidToNavigation"
              },
              {
                "type": "featureType",
                "ref": "RadarTransponderBeacon"
              },
              {
                "type": "featureType",
                "ref": "Retroreflector"
              },
              {
                "type": "featureType",
                "ref": "SignalStationTraffic"
              },
              {
                "type": "featureType",
                "ref": "SignalStationWarning"
              },
              {
                "type": "featureType",
                "ref": "LightSectored"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [],
            "xml_child_index": 25
          },
          {
            "kind": "featureBinding",
            "references": [
              {
                "type": "association",
                "ref": "UpdatedInformation"
              },
              {
                "type": "role",
                "ref": "theUpdate"
              },
              {
                "type": "featureType",
                "ref": "UpdateInformation"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [],
            "xml_child_index": 26
          },
          {
            "kind": "featureBinding",
            "references": [
              {
                "type": "association",
                "ref": "TextAssociation"
              },
              {
                "type": "role",
                "ref": "theCartographicText"
              },
              {
                "type": "featureType",
                "ref": "TextPlacement"
              }
            ],
            "lower": "0",
            "upper": "2",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 27
          }
        ],
        "listed_values": [],
        "version": "2.0.0",
        "source_status": "VERIFIED_XML_EXTRACTION",
        "source_path": "D:\\An_GeoLLM\\outputs\\staging\\s101_feature_catalogue_2_0_0\\S-101\\CATALOGUES\\101_Feature_Catalogue_2.0.0.xml",
        "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "parsed_locator": "/features/86",
        "definition_sha256": "42995f6ea3f18e9e74fd93a554871688cc297d4440b18042e5d894f130eb971a",
        "xml_element_serialized_sha256": "1f207649d80e84625edd620051b6645d926ff8c7553be9fa868b6cf165a54177",
        "element_hash_serialization": "xml.etree.ElementTree serialization; not a raw byte slice"
      }
    ],
    "attribute_bindings": [
      {
        "owner": "Wreck",
        "attribute": "categoryOfWreck",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [
          "1",
          "2",
          "3",
          "4",
          "5"
        ],
        "attribute_definition": "Classification of a wrecked or ruined ship.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Non-Dangerous Wreck",
            "definition": "A wreck which is not considered to be dangerous to surface navigation."
          },
          {
            "value": "2",
            "label": "Dangerous Wreck",
            "definition": "A wreck submerged at such a depth as to be considered dangerous to surface navigation."
          },
          {
            "value": "3",
            "label": "Distributed Remains of Wreck",
            "definition": "A substantively decayed wreck over which it is safe to navigate but which should be avoided for anchoring, taking the ground or ground fishing."
          },
          {
            "value": "4",
            "label": "Wreck Showing Mast/Masts",
            "definition": "Wreck of which only the mast(s) is visible at the sounding datum indicated."
          },
          {
            "value": "5",
            "label": "Wreck Showing Any Portion of Hull or Superstructure",
            "definition": "Wreck of which any portion of the hull or superstructure is visible at the sounding datum indicated."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='categoryOfWreck']]"
      },
      {
        "owner": "Wreck",
        "attribute": "expositionOfSounding",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [
          "1",
          "2",
          "3"
        ],
        "attribute_definition": "Indicates the relationship of the depth of a feature to the range of depth of the surrounding depth area.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Within the Range of Depth of the Surrounding Depth Area",
            "definition": "The depth corresponds to the depth range of the surrounding depth area; that is, the depth is not shoaler than the minimum depth of the surrounding depth area or deeper than the maximum depth of the surrounding depth area."
          },
          {
            "value": "2",
            "label": "Shoaler Than the Range of Depth of the Surrounding Depth Area",
            "definition": "The depth is shoaler than the minimum depth of the surrounding depth area."
          },
          {
            "value": "3",
            "label": "Deeper Than the Range of Depth of the Surrounding Depth Area",
            "definition": "The depth is deeper than the maximum depth of the surrounding depth area."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='expositionOfSounding']]"
      },
      {
        "owner": "Wreck",
        "attribute": "featureName",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [],
        "attribute_definition": "Provides the name of an entity, defines the national language of the name, and provides the option to display the name at various system display settings.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='featureName']]"
      },
      {
        "owner": "Wreck",
        "attribute": "height",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The value of the vertical distance to the highest point of the feature, measured from a specified vertical datum.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='height']]"
      },
      {
        "owner": "Wreck",
        "attribute": "interoperabilityIdentifier",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "A common unique identifier for entities which describe a single real-world feature, and which is used to identify instances of the feature in end-user systems where the feature may be included in multiple data product types.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='interoperabilityIdentifier']]"
      },
      {
        "owner": "Wreck",
        "attribute": "qualityOfVerticalMeasurement",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [
          "1",
          "2",
          "3",
          "4",
          "6",
          "7",
          "8",
          "9"
        ],
        "attribute_definition": "The reliability of the value of a sounding.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Depth Known",
            "definition": "The depth from the chart datum to the seabed (or to the top of a drying feature) is known."
          },
          {
            "value": "2",
            "label": "Depth or Least Depth Unknown",
            "definition": "The depth from chart datum to the seabed, or the shoalest depth of the feature is unknown."
          },
          {
            "value": "3",
            "label": "Doubtful Sounding",
            "definition": "A depth that may be less than indicated."
          },
          {
            "value": "4",
            "label": "Unreliable Sounding",
            "definition": "A depth that is considered to be an unreliable value."
          },
          {
            "value": "6",
            "label": "Least Depth Known",
            "definition": "The shoalest depth over a feature is of known value."
          },
          {
            "value": "7",
            "label": "Least Depth Unknown, Safe Clearance at Value Shown",
            "definition": "The least depth over a feature is unknown, but there is considered to be safe clearance at this depth."
          },
          {
            "value": "8",
            "label": "Value Reported (Not Surveyed)",
            "definition": "Depth value obtained from a report, but not fully surveyed."
          },
          {
            "value": "9",
            "label": "Value Reported (Not Confirmed)",
            "definition": "Depth value obtained from a report, which it has not been possible to confirm."
          },
          {
            "value": "10",
            "label": "Maintained Depth",
            "definition": "The depth at which a channel is kept by human influence, usually by dredging."
          },
          {
            "value": "11",
            "label": "Not Regularly Maintained",
            "definition": "Depths may be altered by human influence, but will not be routinely maintained."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='qualityOfVerticalMeasurement']]"
      },
      {
        "owner": "Wreck",
        "attribute": "radarConspicuous",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "A feature which returns a strong radar echo.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='radarConspicuous']]"
      },
      {
        "owner": "Wreck",
        "attribute": "reportedDate",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The date that the item was observed, done, or investigated.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='reportedDate']]"
      },
      {
        "owner": "Wreck",
        "attribute": "status",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [
          "7",
          "13",
          "18"
        ],
        "attribute_definition": "The condition of an object at a given instant in time.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Permanent",
            "definition": "Intended to last or function indefinitely."
          },
          {
            "value": "2",
            "label": "Occasional",
            "definition": "Acting on special occasions; happening irregularly."
          },
          {
            "value": "3",
            "label": "Recommended",
            "definition": "Presented as worthy of confidence, acceptance, use, etc."
          },
          {
            "value": "4",
            "label": "Not in Use",
            "definition": "Use has ceased, but the facility still exists intact; disused."
          },
          {
            "value": "5",
            "label": "Periodic/Intermittent",
            "definition": "Recurring at intervals."
          },
          {
            "value": "6",
            "label": "Reserved",
            "definition": "Set apart for some specific use."
          },
          {
            "value": "7",
            "label": "Temporary",
            "definition": "Meant to last only for a time."
          },
          {
            "value": "8",
            "label": "Private",
            "definition": "Administered by an individual or corporation, rather than a State or a public body."
          },
          {
            "value": "9",
            "label": "Mandatory",
            "definition": "Compulsory; enforced."
          },
          {
            "value": "11",
            "label": "Extinguished",
            "definition": "No longer lit."
          },
          {
            "value": "12",
            "label": "Illuminated",
            "definition": "Lit by flood lights, strip lights, etc."
          },
          {
            "value": "13",
            "label": "Historic",
            "definition": "Famous in history; of historical interest."
          },
          {
            "value": "14",
            "label": "Public",
            "definition": "Belonging to, available to, used or shared by, the community as a whole and not restricted to private use."
          },
          {
            "value": "15",
            "label": "Synchronized",
            "definition": "Occur at a time, coincide in point of time, be contemporary or simultaneous."
          },
          {
            "value": "16",
            "label": "Watched",
            "definition": "Looked at or observed over a period of time especially so as to be aware of any movement or change."
          },
          {
            "value": "17",
            "label": "Unwatched",
            "definition": "Usually automatic in operation, without any permanently-stationed personnel to superintend it."
          },
          {
            "value": "18",
            "label": "Existence Doubtful",
            "definition": "A feature that has been reported but has not been definitely determined to exist."
          },
          {
            "value": "28",
            "label": "Buoyed",
            "definition": "Marked by buoys."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='status']]"
      },
      {
        "owner": "Wreck",
        "attribute": "techniqueOfVerticalMeasurement",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [
          "1",
          "2",
          "3",
          "4",
          "5",
          "8",
          "9",
          "10",
          "11",
          "12",
          "13",
          "15",
          "16",
          "17",
          "18"
        ],
        "attribute_definition": "Survey method used to obtain depth information.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Found by Echo Sounder",
            "definition": "The depth was measured by using an instrument that determines depth of water by measuring the time interval between emission of a sonic or ultrasonic signal and return of its echo from the bottom."
          },
          {
            "value": "2",
            "label": "Found by Side Scan Sonar",
            "definition": "The depth was computed from a record produced by active sonar in which fixed acoustic beams are directed into the water perpendicularly to the direction of travel to scan the seabed and generate a record of the seabed configuration."
          },
          {
            "value": "3",
            "label": "Found by Multi Beam",
            "definition": "The depth was measured by using a wide swath echo sounder that uses multiple beams to measure depths directly below and transverse to the ship's track."
          },
          {
            "value": "4",
            "label": "Found by Diver",
            "definition": "The depth was determined by a person skilled in the practice of diving."
          },
          {
            "value": "5",
            "label": "Found by Lead Line",
            "definition": "The depth was measured by using a line, graduated with attached marks and fastened to a sounding lead."
          },
          {
            "value": "8",
            "label": "Swept by Vertical Acoustic System",
            "definition": "The given area has been swept using a system comprised of multiple echo sounder transducers attached to booms deployed from the survey vessel."
          },
          {
            "value": "9",
            "label": "Found by Electromagnetic Sensor",
            "definition": "The depth was determined by using an instrument that compares electromagnetic signals."
          },
          {
            "value": "10",
            "label": "Photogrammetry",
            "definition": "The science or art of obtaining reliable measurements from photographs."
          },
          {
            "value": "11",
            "label": "Satellite Imagery",
            "definition": "The depth was determined by using instruments placed aboard an artificial satellite."
          },
          {
            "value": "12",
            "label": "Found by Levelling",
            "definition": "The depth was determined by using levelling techniques to find the elevation of the point relative to a datum."
          },
          {
            "value": "13",
            "label": "Swept by Side Scan Sonar",
            "definition": "The given area was determined to be free from navigational dangers to a certain depth by towing a side scan sonar."
          },
          {
            "value": "15",
            "label": "Found by LIDAR",
            "definition": "The depth was measured by using an instrument that measures distance by emitting timed pulses of laser light and measuring the time between emission and reception of the reflected pulses."
          },
          {
            "value": "16",
            "label": "Synthetic Aperture Radar",
            "definition": "A radar with a synthetic aperture antenna which is composed of a large number of elementary transducing elements. The signals are electronically combined into a resulting signal equivalent to that of a single antenna of a given aperture in a given direction."
          },
          {
            "value": "17",
            "label": "Hyperspectral Imagery",
            "definition": "Term used to describe the imagery derived from subdividing the electromagnetic spectrum into very narrow bandwidths. These narrow bandwidths may be combined with or subtracted from each other in various ways to form images useful in precise terrain or target analysis."
          },
          {
            "value": "18",
            "label": "Mechanically Swept",
            "definition": "The given area was determined to be free from navigational dangers to a certain depth by towing a line or object below the surface at the desired depth; or least depth(s) and position(s) within an area was identified using the same technique."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='techniqueOfVerticalMeasurement']]"
      },
      {
        "owner": "Wreck",
        "attribute": "valueOfSounding",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The value of the measurement of a sounding relative to the chart datum.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='valueOfSounding']]"
      },
      {
        "owner": "Wreck",
        "attribute": "visualProminence",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [
          "1",
          "2",
          "3"
        ],
        "attribute_definition": "The extent to which a feature, either natural or artificial, is visible from seaward.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Visually Conspicuous",
            "definition": "Term applied to an object either natural or artificial which is distinctly and notably visible from seaward."
          },
          {
            "value": "2",
            "label": "Not Visually Conspicuous",
            "definition": "An object that may be visible from seaward, but cannot be used as a fixing mark and is not conspicuous."
          },
          {
            "value": "3",
            "label": "Prominent",
            "definition": "Objects which are easily identifiable, but do not justify being classed as conspicuous."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='visualProminence']]"
      },
      {
        "owner": "Wreck",
        "attribute": "waterLevelEffect",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [
          "1",
          "2",
          "3",
          "4",
          "5"
        ],
        "attribute_definition": "The effect of the surrounding water on an object.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Partly Submerged at High Water",
            "definition": "Partially covered and partially dry at high water."
          },
          {
            "value": "2",
            "label": "Always Dry",
            "definition": "Not covered at high water under average meteorological conditions."
          },
          {
            "value": "3",
            "label": "Always Under Water/Submerged",
            "definition": "Remains covered by water at all times under average meteorological conditions."
          },
          {
            "value": "4",
            "label": "Covers and Uncovers",
            "definition": "Expression intended to indicate an area of a reef or other projection from the bottom of a body of water which periodically extends above and is submerged below the surface. Also referred to as dries or uncovers."
          },
          {
            "value": "5",
            "label": "Awash",
            "definition": "Flush with, or washed by the waves at low water under average meteorological conditions."
          },
          {
            "value": "6",
            "label": "Subject to Inundation or Flooding",
            "definition": "An area periodically covered by flood water, excluding tidal waters."
          },
          {
            "value": "7",
            "label": "Floating",
            "definition": "Resting or moving on the surface of a liquid without sinking."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='waterLevelEffect']]"
      },
      {
        "owner": "Wreck",
        "attribute": "scaleMinimum",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The minimum scale at which the feature may be used for example for ECDIS presentation.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='scaleMinimum']]"
      },
      {
        "owner": "Wreck",
        "attribute": "information",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [],
        "attribute_definition": "Textual information about the feature. The information may be provided as a string of text or as a file name of a single external text file that contains the text.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]"
      },
      {
        "owner": "Wreck",
        "attribute": "pictorialRepresentation",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The file name of an externally referenced picture file.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='pictorialRepresentation']]"
      },
      {
        "owner": "Wreck",
        "attribute": "defaultClearanceDepth",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The depth value determined for an underwater hazard of unknown depth, based on the depth of the surrounding area.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='defaultClearanceDepth']]"
      },
      {
        "owner": "Wreck",
        "attribute": "surroundingDepth",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The depth value determined for seabed around an underwater hazard, based on the depth of the surrounding area.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='surroundingDepth']]"
      },
      {
        "owner": "featureName",
        "attribute": "language",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The method of human communication, either spoken or written, consisting of the use of words in a structured and conventional way.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='featureName']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='language']]"
      },
      {
        "owner": "featureName",
        "attribute": "name",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The individual name of a feature.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='featureName']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='name']]"
      },
      {
        "owner": "featureName",
        "attribute": "nameUsage",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [
          "1",
          "2"
        ],
        "attribute_definition": "Classification of the type and display level of the name of a feature in an end-user system.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Default Name Display",
            "definition": "The name is intended to be displayed when the end-user system is set to the default name/text display setting."
          },
          {
            "value": "2",
            "label": "Alternate Name Display",
            "definition": "The name is intended to be displayed when the end-user system is set to an alternate name/text display setting, for example an alternate language."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='featureName']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='nameUsage']]"
      },
      {
        "owner": "information",
        "attribute": "fileLocator",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The location of a fragment of text or other information in a support file.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='fileLocator']]"
      },
      {
        "owner": "information",
        "attribute": "fileReference",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The file name of an externally referenced text file.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='fileReference']]"
      },
      {
        "owner": "information",
        "attribute": "headline",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "Words set at the head of a passage or page to introduce or categorize.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='headline']]"
      },
      {
        "owner": "information",
        "attribute": "language",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The method of human communication, either spoken or written, consisting of the use of words in a structured and conventional way.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='language']]"
      },
      {
        "owner": "information",
        "attribute": "text",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "A non-formatted digital text string.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='text']]"
      }
    ],
    "evidence": {
      "edition": "2.0.0",
      "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
      "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
      "locators": [
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]"
      ],
      "claim_source_links": [
        {
          "feature_code": "Wreck",
          "definition_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
          "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc"
        }
      ]
    },
    "definition_quote": "The ruined remains of a stranded or sunken vessel which has been rendered useless."
  },
  "status": "COMPLETED",
  "execution_status": "COMPLETED",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q2_03.json)
```json
{
  "case_id": "PILOT_Q2_03",
  "required_task_obligations": [
    "explain_wreck_attribute_bindings"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_066",
  "answer_sha256": "06bf2a032b8f95ff00a7eff8b9760dea6896e1563131f1ab9b7550e61d42bc63",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "978150fd3591138d431095b6c17b4b82f2b55255188e6eff224191887bbd5892",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_065 — 독도 주변 반경 5km의 해양지명을 찾아줘.

답안 hash: `8435850bf3e7c6655f952415b941bc24e23029d005fc1735c30bf3ae7adf1b96`

### 실제 최종 답안
```json
{
  "answer_text": "Dokdo 주변 반경 5km의 해양지명은 '독도'입니다.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "document_answer": {
    "features": [],
    "attribute_bindings": [],
    "evidence": {
      "edition": "2.0.0",
      "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
      "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
      "locators": [],
      "claim_source_links": []
    }
  },
  "status": "COMPLETED",
  "execution_status": "COMPLETED",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q4_01.json)
```json
{
  "case_id": "PILOT_Q4_01",
  "required_task_obligations": [
    "resolve_approved_anchor",
    "search_fixed_gazetteer_5000m",
    "report_source_bound_objects"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_065",
  "answer_sha256": "8435850bf3e7c6655f952415b941bc24e23029d005fc1735c30bf3ae7adf1b96",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "d1490712c1cc1a1f46b479182fd614564fee2b4857c42f568e313c5ced5ee248",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_064 — Find marine place names within 5 km of Dokdo.

답안 hash: `06d005a8bceb7ad53ef6c8645c156769cdd86976be12ce008ef739fe5c3b53da`

### 실제 최종 답안
```json
{
  "answer_text": "Marine place names within 5 km of Dokdo include: ",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q4_03.json)
```json
{
  "case_id": "PILOT_Q4_03",
  "required_task_obligations": [
    "resolve_approved_anchor",
    "search_fixed_gazetteer_5000m",
    "report_source_bound_objects"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_064",
  "answer_sha256": "06d005a8bceb7ad53ef6c8645c156769cdd86976be12ce008ef739fe5c3b53da",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "2e15336412a9dc7da26840f2535629710b97efd684f8204358cd43586850f18b",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_063 — 등대의 S-101 객체 유형과 정의를 알려줘.

답안 hash: `b3a62da1b7319f5be0a16d34fff0967fc95cedb5438fc8a4a97c698c0652975c`

### 실제 최종 답안
```json
{
  "answer_text": "등대는 S-101 객체 중 하나입니다. 이 객체는 등대의 정의와 유형을 나타냅니다. S-101는 등대의 공통적인 객체 코드입니다.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "validator_blockers": [
    "BLOCKED_DATA: public catalogue document evidence unavailable"
  ],
  "status": "BLOCKED_DATA",
  "execution_status": "BLOCKED_DATA",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q1_01.json)
```json
{
  "case_id": "PILOT_Q1_01",
  "required_task_obligations": [
    "explain_structure_and_light_distinction",
    "explain_conditional_feature_mapping"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "single_Lighthouse_feature_assertion",
    "global_colour_codes_for_feature_binding"
  ],
  "scope_notes": [
    "Landmark/Building describe conditional structure alternatives; LightAllAround/LightSectored describe light alternatives. Listing these for explanation does not assert all must exist in one physical lighthouse."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_063",
  "answer_sha256": "b3a62da1b7319f5be0a16d34fff0967fc95cedb5438fc8a4a97c698c0652975c",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "7b8cc2c44109400043db40af0794ebb941604c3af532d393dc62359f4e20760a",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_062 — 부산항 영역 안의 정박지를 찾아줘.

답안 hash: `80ced83977bd1c43167889eb1582e7cade00e190049d19c23d94ed2204e7134e`

### 실제 최종 답안
```json
{
  "answer_text": "The watercraft located within the Busan Port boundary.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "document_answer": {
    "features": [],
    "attribute_bindings": [],
    "evidence": {
      "edition": "2.0.0",
      "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
      "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
      "locators": [],
      "claim_source_links": []
    }
  },
  "status": "COMPLETED",
  "execution_status": "COMPLETED",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q3_02.json)
```json
{
  "case_id": "PILOT_Q3_02",
  "required_task_obligations": [
    "resolve_official_port_polygon",
    "verify_coverage",
    "search_within_polygon",
    "report_objects_or_unresolved_reason"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "Object IDs refer to frozen snapshot records, not deduplicated physical facilities or the whole legal port."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_062",
  "answer_sha256": "80ced83977bd1c43167889eb1582e7cade00e190049d19c23d94ed2204e7134e",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "55f777bcbc55b58632d3e64ea737b141d4d43edc0b5e0e3d122761768c9e54c3",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_061 — 등대와 부표를 구분하는 S-101 근거를 알려줘.

답안 hash: `79f63162390f8be63aa3293966a3f87f7417952a5b6a84845d7913a34af26fe7`

### 실제 최종 답안
```json
{
  "answer_text": "등대와 부표는 주로 경상북도 울릉도와 경상남도 울릉군에서 구분됩니다. 이 두 지역은 경상북도와 경상남도의 경계를 이루고 있습니다. 이 지역에서는 등대와 부표의 구분이 주로 이루어져 있습니다. 이 지역에서는 등대는 주로 농업용으로 사용되며, 부표는 주로 해양 경관이나 관광용으로 사용됩니다. 이 지역에서는 등대와 부표는 주로 높이와 구조, 그리고 배치 등에 따라 구분됩니다. 이 지역에서는 등대는 높이가 높고, 부표는 높이가 낮으며, 배치는 등대보다 더 넓습니다. 이 지역에서는 등대와 부표는 주로 높이와 구조, 배치 등에 따라 구분됩니다.",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q6_02.json)
```json
{
  "case_id": "PILOT_Q6_02",
  "required_task_obligations": [
    "compare_fixed_structure_and_floating_aid_models",
    "cite_comparison_evidence"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "single_Lighthouse_feature_assertion",
    "global_colour_codes_for_feature_binding"
  ],
  "scope_notes": [
    "Landmark/Building describe conditional structure alternatives; LightAllAround/LightSectored describe light alternatives. Listing these for explanation does not assert all must exist in one physical lighthouse.",
    "Bounded comparison: LateralBuoy is the explicitly selected representative floating-aid feature; no claim to exhaustively describe every buoy class. Compare with conditional structure/light models."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_061",
  "answer_sha256": "79f63162390f8be63aa3293966a3f87f7417952a5b6a84845d7913a34af26fe7",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "a05857e4360459d5be76998ded541f5d0de2937b2905383a28e725a49d4f4d2f",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_060 — Which attributes describe a Wreck in S-101?

답안 hash: `fa632b89f46ba02925ef5f539d5609fabc2618dcf07b5ed894b48ee39c9cb6ac`

### 실제 최종 답안
```json
{
  "answer_text": "A wreck is described in S-101, located within the scope of the S-101 feature catalogue.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "document_answer": {
    "features": [
      {
        "code": "Wreck",
        "xml_type": "S100_FC_FeatureType",
        "definition": "The ruined remains of a stranded or sunken vessel which has been rendered useless.",
        "permitted_primitives": [
          "point",
          "surface"
        ],
        "bindings": [
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "categoryOfWreck"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [
              "1",
              "2",
              "3",
              "4",
              "5"
            ],
            "xml_child_index": 5
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "expositionOfSounding"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [
              "1",
              "2",
              "3"
            ],
            "xml_child_index": 6
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "featureName"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [],
            "xml_child_index": 7
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "height"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 8
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "interoperabilityIdentifier"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 9
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "qualityOfVerticalMeasurement"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [
              "1",
              "2",
              "3",
              "4",
              "6",
              "7",
              "8",
              "9"
            ],
            "xml_child_index": 10
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "radarConspicuous"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 11
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "reportedDate"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 12
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "status"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [
              "7",
              "13",
              "18"
            ],
            "xml_child_index": 13
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "techniqueOfVerticalMeasurement"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [
              "1",
              "2",
              "3",
              "4",
              "5",
              "8",
              "9",
              "10",
              "11",
              "12",
              "13",
              "15",
              "16",
              "17",
              "18"
            ],
            "xml_child_index": 14
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "valueOfSounding"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 15
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "visualProminence"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [
              "1",
              "2",
              "3"
            ],
            "xml_child_index": 16
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "waterLevelEffect"
              }
            ],
            "lower": "1",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [
              "1",
              "2",
              "3",
              "4",
              "5"
            ],
            "xml_child_index": 17
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "scaleMinimum"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 18
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "information"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [],
            "xml_child_index": 19
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "pictorialRepresentation"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 20
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "defaultClearanceDepth"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 21
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "surroundingDepth"
              }
            ],
            "lower": "1",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 22
          },
          {
            "kind": "informationBinding",
            "references": [
              {
                "type": "association",
                "ref": "AdditionalInformation"
              },
              {
                "type": "role",
                "ref": "theInformation"
              },
              {
                "type": "informationType",
                "ref": "NauticalInformation"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 23
          },
          {
            "kind": "featureBinding",
            "references": [
              {
                "type": "association",
                "ref": "StructureEquipment"
              },
              {
                "type": "role",
                "ref": "theEquipment"
              },
              {
                "type": "featureType",
                "ref": "Daymark"
              },
              {
                "type": "featureType",
                "ref": "DistanceMark"
              },
              {
                "type": "featureType",
                "ref": "FogSignal"
              },
              {
                "type": "featureType",
                "ref": "LightAllAround"
              },
              {
                "type": "featureType",
                "ref": "LightFogDetector"
              },
              {
                "type": "featureType",
                "ref": "PhysicalAISAidToNavigation"
              },
              {
                "type": "featureType",
                "ref": "RadarTransponderBeacon"
              },
              {
                "type": "featureType",
                "ref": "Retroreflector"
              },
              {
                "type": "featureType",
                "ref": "SignalStationTraffic"
              },
              {
                "type": "featureType",
                "ref": "SignalStationWarning"
              },
              {
                "type": "featureType",
                "ref": "LightSectored"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [],
            "xml_child_index": 25
          },
          {
            "kind": "featureBinding",
            "references": [
              {
                "type": "association",
                "ref": "UpdatedInformation"
              },
              {
                "type": "role",
                "ref": "theUpdate"
              },
              {
                "type": "featureType",
                "ref": "UpdateInformation"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [],
            "xml_child_index": 26
          },
          {
            "kind": "featureBinding",
            "references": [
              {
                "type": "association",
                "ref": "TextAssociation"
              },
              {
                "type": "role",
                "ref": "theCartographicText"
              },
              {
                "type": "featureType",
                "ref": "TextPlacement"
              }
            ],
            "lower": "0",
            "upper": "2",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 27
          }
        ],
        "listed_values": [],
        "version": "2.0.0",
        "source_status": "VERIFIED_XML_EXTRACTION",
        "source_path": "D:\\An_GeoLLM\\outputs\\staging\\s101_feature_catalogue_2_0_0\\S-101\\CATALOGUES\\101_Feature_Catalogue_2.0.0.xml",
        "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "parsed_locator": "/features/86",
        "definition_sha256": "42995f6ea3f18e9e74fd93a554871688cc297d4440b18042e5d894f130eb971a",
        "xml_element_serialized_sha256": "1f207649d80e84625edd620051b6645d926ff8c7553be9fa868b6cf165a54177",
        "element_hash_serialization": "xml.etree.ElementTree serialization; not a raw byte slice"
      }
    ],
    "attribute_bindings": [
      {
        "owner": "Wreck",
        "attribute": "categoryOfWreck",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [
          "1",
          "2",
          "3",
          "4",
          "5"
        ],
        "attribute_definition": "Classification of a wrecked or ruined ship.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Non-Dangerous Wreck",
            "definition": "A wreck which is not considered to be dangerous to surface navigation."
          },
          {
            "value": "2",
            "label": "Dangerous Wreck",
            "definition": "A wreck submerged at such a depth as to be considered dangerous to surface navigation."
          },
          {
            "value": "3",
            "label": "Distributed Remains of Wreck",
            "definition": "A substantively decayed wreck over which it is safe to navigate but which should be avoided for anchoring, taking the ground or ground fishing."
          },
          {
            "value": "4",
            "label": "Wreck Showing Mast/Masts",
            "definition": "Wreck of which only the mast(s) is visible at the sounding datum indicated."
          },
          {
            "value": "5",
            "label": "Wreck Showing Any Portion of Hull or Superstructure",
            "definition": "Wreck of which any portion of the hull or superstructure is visible at the sounding datum indicated."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='categoryOfWreck']]"
      },
      {
        "owner": "Wreck",
        "attribute": "expositionOfSounding",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [
          "1",
          "2",
          "3"
        ],
        "attribute_definition": "Indicates the relationship of the depth of a feature to the range of depth of the surrounding depth area.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Within the Range of Depth of the Surrounding Depth Area",
            "definition": "The depth corresponds to the depth range of the surrounding depth area; that is, the depth is not shoaler than the minimum depth of the surrounding depth area or deeper than the maximum depth of the surrounding depth area."
          },
          {
            "value": "2",
            "label": "Shoaler Than the Range of Depth of the Surrounding Depth Area",
            "definition": "The depth is shoaler than the minimum depth of the surrounding depth area."
          },
          {
            "value": "3",
            "label": "Deeper Than the Range of Depth of the Surrounding Depth Area",
            "definition": "The depth is deeper than the maximum depth of the surrounding depth area."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='expositionOfSounding']]"
      },
      {
        "owner": "Wreck",
        "attribute": "featureName",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [],
        "attribute_definition": "Provides the name of an entity, defines the national language of the name, and provides the option to display the name at various system display settings.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='featureName']]"
      },
      {
        "owner": "Wreck",
        "attribute": "height",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The value of the vertical distance to the highest point of the feature, measured from a specified vertical datum.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='height']]"
      },
      {
        "owner": "Wreck",
        "attribute": "interoperabilityIdentifier",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "A common unique identifier for entities which describe a single real-world feature, and which is used to identify instances of the feature in end-user systems where the feature may be included in multiple data product types.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='interoperabilityIdentifier']]"
      },
      {
        "owner": "Wreck",
        "attribute": "qualityOfVerticalMeasurement",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [
          "1",
          "2",
          "3",
          "4",
          "6",
          "7",
          "8",
          "9"
        ],
        "attribute_definition": "The reliability of the value of a sounding.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Depth Known",
            "definition": "The depth from the chart datum to the seabed (or to the top of a drying feature) is known."
          },
          {
            "value": "2",
            "label": "Depth or Least Depth Unknown",
            "definition": "The depth from chart datum to the seabed, or the shoalest depth of the feature is unknown."
          },
          {
            "value": "3",
            "label": "Doubtful Sounding",
            "definition": "A depth that may be less than indicated."
          },
          {
            "value": "4",
            "label": "Unreliable Sounding",
            "definition": "A depth that is considered to be an unreliable value."
          },
          {
            "value": "6",
            "label": "Least Depth Known",
            "definition": "The shoalest depth over a feature is of known value."
          },
          {
            "value": "7",
            "label": "Least Depth Unknown, Safe Clearance at Value Shown",
            "definition": "The least depth over a feature is unknown, but there is considered to be safe clearance at this depth."
          },
          {
            "value": "8",
            "label": "Value Reported (Not Surveyed)",
            "definition": "Depth value obtained from a report, but not fully surveyed."
          },
          {
            "value": "9",
            "label": "Value Reported (Not Confirmed)",
            "definition": "Depth value obtained from a report, which it has not been possible to confirm."
          },
          {
            "value": "10",
            "label": "Maintained Depth",
            "definition": "The depth at which a channel is kept by human influence, usually by dredging."
          },
          {
            "value": "11",
            "label": "Not Regularly Maintained",
            "definition": "Depths may be altered by human influence, but will not be routinely maintained."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='qualityOfVerticalMeasurement']]"
      },
      {
        "owner": "Wreck",
        "attribute": "radarConspicuous",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "A feature which returns a strong radar echo.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='radarConspicuous']]"
      },
      {
        "owner": "Wreck",
        "attribute": "reportedDate",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The date that the item was observed, done, or investigated.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='reportedDate']]"
      },
      {
        "owner": "Wreck",
        "attribute": "status",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [
          "7",
          "13",
          "18"
        ],
        "attribute_definition": "The condition of an object at a given instant in time.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Permanent",
            "definition": "Intended to last or function indefinitely."
          },
          {
            "value": "2",
            "label": "Occasional",
            "definition": "Acting on special occasions; happening irregularly."
          },
          {
            "value": "3",
            "label": "Recommended",
            "definition": "Presented as worthy of confidence, acceptance, use, etc."
          },
          {
            "value": "4",
            "label": "Not in Use",
            "definition": "Use has ceased, but the facility still exists intact; disused."
          },
          {
            "value": "5",
            "label": "Periodic/Intermittent",
            "definition": "Recurring at intervals."
          },
          {
            "value": "6",
            "label": "Reserved",
            "definition": "Set apart for some specific use."
          },
          {
            "value": "7",
            "label": "Temporary",
            "definition": "Meant to last only for a time."
          },
          {
            "value": "8",
            "label": "Private",
            "definition": "Administered by an individual or corporation, rather than a State or a public body."
          },
          {
            "value": "9",
            "label": "Mandatory",
            "definition": "Compulsory; enforced."
          },
          {
            "value": "11",
            "label": "Extinguished",
            "definition": "No longer lit."
          },
          {
            "value": "12",
            "label": "Illuminated",
            "definition": "Lit by flood lights, strip lights, etc."
          },
          {
            "value": "13",
            "label": "Historic",
            "definition": "Famous in history; of historical interest."
          },
          {
            "value": "14",
            "label": "Public",
            "definition": "Belonging to, available to, used or shared by, the community as a whole and not restricted to private use."
          },
          {
            "value": "15",
            "label": "Synchronized",
            "definition": "Occur at a time, coincide in point of time, be contemporary or simultaneous."
          },
          {
            "value": "16",
            "label": "Watched",
            "definition": "Looked at or observed over a period of time especially so as to be aware of any movement or change."
          },
          {
            "value": "17",
            "label": "Unwatched",
            "definition": "Usually automatic in operation, without any permanently-stationed personnel to superintend it."
          },
          {
            "value": "18",
            "label": "Existence Doubtful",
            "definition": "A feature that has been reported but has not been definitely determined to exist."
          },
          {
            "value": "28",
            "label": "Buoyed",
            "definition": "Marked by buoys."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='status']]"
      },
      {
        "owner": "Wreck",
        "attribute": "techniqueOfVerticalMeasurement",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [
          "1",
          "2",
          "3",
          "4",
          "5",
          "8",
          "9",
          "10",
          "11",
          "12",
          "13",
          "15",
          "16",
          "17",
          "18"
        ],
        "attribute_definition": "Survey method used to obtain depth information.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Found by Echo Sounder",
            "definition": "The depth was measured by using an instrument that determines depth of water by measuring the time interval between emission of a sonic or ultrasonic signal and return of its echo from the bottom."
          },
          {
            "value": "2",
            "label": "Found by Side Scan Sonar",
            "definition": "The depth was computed from a record produced by active sonar in which fixed acoustic beams are directed into the water perpendicularly to the direction of travel to scan the seabed and generate a record of the seabed configuration."
          },
          {
            "value": "3",
            "label": "Found by Multi Beam",
            "definition": "The depth was measured by using a wide swath echo sounder that uses multiple beams to measure depths directly below and transverse to the ship's track."
          },
          {
            "value": "4",
            "label": "Found by Diver",
            "definition": "The depth was determined by a person skilled in the practice of diving."
          },
          {
            "value": "5",
            "label": "Found by Lead Line",
            "definition": "The depth was measured by using a line, graduated with attached marks and fastened to a sounding lead."
          },
          {
            "value": "8",
            "label": "Swept by Vertical Acoustic System",
            "definition": "The given area has been swept using a system comprised of multiple echo sounder transducers attached to booms deployed from the survey vessel."
          },
          {
            "value": "9",
            "label": "Found by Electromagnetic Sensor",
            "definition": "The depth was determined by using an instrument that compares electromagnetic signals."
          },
          {
            "value": "10",
            "label": "Photogrammetry",
            "definition": "The science or art of obtaining reliable measurements from photographs."
          },
          {
            "value": "11",
            "label": "Satellite Imagery",
            "definition": "The depth was determined by using instruments placed aboard an artificial satellite."
          },
          {
            "value": "12",
            "label": "Found by Levelling",
            "definition": "The depth was determined by using levelling techniques to find the elevation of the point relative to a datum."
          },
          {
            "value": "13",
            "label": "Swept by Side Scan Sonar",
            "definition": "The given area was determined to be free from navigational dangers to a certain depth by towing a side scan sonar."
          },
          {
            "value": "15",
            "label": "Found by LIDAR",
            "definition": "The depth was measured by using an instrument that measures distance by emitting timed pulses of laser light and measuring the time between emission and reception of the reflected pulses."
          },
          {
            "value": "16",
            "label": "Synthetic Aperture Radar",
            "definition": "A radar with a synthetic aperture antenna which is composed of a large number of elementary transducing elements. The signals are electronically combined into a resulting signal equivalent to that of a single antenna of a given aperture in a given direction."
          },
          {
            "value": "17",
            "label": "Hyperspectral Imagery",
            "definition": "Term used to describe the imagery derived from subdividing the electromagnetic spectrum into very narrow bandwidths. These narrow bandwidths may be combined with or subtracted from each other in various ways to form images useful in precise terrain or target analysis."
          },
          {
            "value": "18",
            "label": "Mechanically Swept",
            "definition": "The given area was determined to be free from navigational dangers to a certain depth by towing a line or object below the surface at the desired depth; or least depth(s) and position(s) within an area was identified using the same technique."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='techniqueOfVerticalMeasurement']]"
      },
      {
        "owner": "Wreck",
        "attribute": "valueOfSounding",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The value of the measurement of a sounding relative to the chart datum.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='valueOfSounding']]"
      },
      {
        "owner": "Wreck",
        "attribute": "visualProminence",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [
          "1",
          "2",
          "3"
        ],
        "attribute_definition": "The extent to which a feature, either natural or artificial, is visible from seaward.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Visually Conspicuous",
            "definition": "Term applied to an object either natural or artificial which is distinctly and notably visible from seaward."
          },
          {
            "value": "2",
            "label": "Not Visually Conspicuous",
            "definition": "An object that may be visible from seaward, but cannot be used as a fixing mark and is not conspicuous."
          },
          {
            "value": "3",
            "label": "Prominent",
            "definition": "Objects which are easily identifiable, but do not justify being classed as conspicuous."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='visualProminence']]"
      },
      {
        "owner": "Wreck",
        "attribute": "waterLevelEffect",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [
          "1",
          "2",
          "3",
          "4",
          "5"
        ],
        "attribute_definition": "The effect of the surrounding water on an object.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Partly Submerged at High Water",
            "definition": "Partially covered and partially dry at high water."
          },
          {
            "value": "2",
            "label": "Always Dry",
            "definition": "Not covered at high water under average meteorological conditions."
          },
          {
            "value": "3",
            "label": "Always Under Water/Submerged",
            "definition": "Remains covered by water at all times under average meteorological conditions."
          },
          {
            "value": "4",
            "label": "Covers and Uncovers",
            "definition": "Expression intended to indicate an area of a reef or other projection from the bottom of a body of water which periodically extends above and is submerged below the surface. Also referred to as dries or uncovers."
          },
          {
            "value": "5",
            "label": "Awash",
            "definition": "Flush with, or washed by the waves at low water under average meteorological conditions."
          },
          {
            "value": "6",
            "label": "Subject to Inundation or Flooding",
            "definition": "An area periodically covered by flood water, excluding tidal waters."
          },
          {
            "value": "7",
            "label": "Floating",
            "definition": "Resting or moving on the surface of a liquid without sinking."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='waterLevelEffect']]"
      },
      {
        "owner": "Wreck",
        "attribute": "scaleMinimum",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The minimum scale at which the feature may be used for example for ECDIS presentation.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='scaleMinimum']]"
      },
      {
        "owner": "Wreck",
        "attribute": "information",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [],
        "attribute_definition": "Textual information about the feature. The information may be provided as a string of text or as a file name of a single external text file that contains the text.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]"
      },
      {
        "owner": "Wreck",
        "attribute": "pictorialRepresentation",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The file name of an externally referenced picture file.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='pictorialRepresentation']]"
      },
      {
        "owner": "Wreck",
        "attribute": "defaultClearanceDepth",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The depth value determined for an underwater hazard of unknown depth, based on the depth of the surrounding area.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='defaultClearanceDepth']]"
      },
      {
        "owner": "Wreck",
        "attribute": "surroundingDepth",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The depth value determined for seabed around an underwater hazard, based on the depth of the surrounding area.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='surroundingDepth']]"
      },
      {
        "owner": "featureName",
        "attribute": "language",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The method of human communication, either spoken or written, consisting of the use of words in a structured and conventional way.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='featureName']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='language']]"
      },
      {
        "owner": "featureName",
        "attribute": "name",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The individual name of a feature.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='featureName']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='name']]"
      },
      {
        "owner": "featureName",
        "attribute": "nameUsage",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [
          "1",
          "2"
        ],
        "attribute_definition": "Classification of the type and display level of the name of a feature in an end-user system.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Default Name Display",
            "definition": "The name is intended to be displayed when the end-user system is set to the default name/text display setting."
          },
          {
            "value": "2",
            "label": "Alternate Name Display",
            "definition": "The name is intended to be displayed when the end-user system is set to an alternate name/text display setting, for example an alternate language."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='featureName']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='nameUsage']]"
      },
      {
        "owner": "information",
        "attribute": "fileLocator",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The location of a fragment of text or other information in a support file.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='fileLocator']]"
      },
      {
        "owner": "information",
        "attribute": "fileReference",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The file name of an externally referenced text file.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='fileReference']]"
      },
      {
        "owner": "information",
        "attribute": "headline",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "Words set at the head of a passage or page to introduce or categorize.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='headline']]"
      },
      {
        "owner": "information",
        "attribute": "language",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The method of human communication, either spoken or written, consisting of the use of words in a structured and conventional way.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='language']]"
      },
      {
        "owner": "information",
        "attribute": "text",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "A non-formatted digital text string.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='text']]"
      }
    ],
    "evidence": {
      "edition": "2.0.0",
      "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
      "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
      "locators": [
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]"
      ],
      "claim_source_links": [
        {
          "feature_code": "Wreck",
          "definition_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
          "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc"
        }
      ]
    },
    "definition_quote": "The ruined remains of a stranded or sunken vessel which has been rendered useless."
  },
  "status": "COMPLETED",
  "execution_status": "COMPLETED",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q2_03.json)
```json
{
  "case_id": "PILOT_Q2_03",
  "required_task_obligations": [
    "explain_wreck_attribute_bindings"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_060",
  "answer_sha256": "fa632b89f46ba02925ef5f539d5609fabc2618dcf07b5ed894b48ee39c9cb6ac",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "978150fd3591138d431095b6c17b4b82f2b55255188e6eff224191887bbd5892",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_059 — S-101 등대의 색상 속성과 허용 값을 알려줘.

답안 hash: `4fd43262ded7a44d9d2c4f0ab7c6ca3c063260f011ae8eec551b28346c665120`

### 실제 최종 답안
```json
{
  "answer_text": "등대의 색상 속성은 일반적으로 노란색이나 검은색이며, 허용 범위는 주변의 해양 장비나 도시 건물의 레이어와 비슷합니다. 그러나 이 정보는 실제 위치에 따라 달라질 수 있으므로, 정확한 정보는 현지 장비 관리자나 관련 기관에 문의하시는 것이 가장 좋습니다.",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q2_01.json)
```json
{
  "case_id": "PILOT_Q2_01",
  "required_task_obligations": [
    "distinguish_structure_and_light_colour",
    "explain_feature_bound_permitted_values"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "single_Lighthouse_feature_assertion",
    "global_colour_codes_for_feature_binding"
  ],
  "scope_notes": [
    "Landmark/Building describe conditional structure alternatives; LightAllAround/LightSectored describe light alternatives. Listing these for explanation does not assert all must exist in one physical lighthouse."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_059",
  "answer_sha256": "4fd43262ded7a44d9d2c4f0ab7c6ca3c063260f011ae8eec551b28346c665120",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "a4175678aa1e5f3176c8bcfcd9de2a2c08d4e34583f488cda32962a77d5f5657",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_058 — Find marine place names within 5 km of Dokdo.

답안 hash: `388fbbe2ac0c8e6491719251d5cbdfc00624bd374847aa7ee8bee06512de3cad`

### 실제 최종 답안
```json
{
  "answer_text": "Marine place names within 5 km of Dokdo: [marine place names]",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "document_answer": {
    "features": [],
    "attribute_bindings": [],
    "evidence": {
      "edition": "2.0.0",
      "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
      "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
      "locators": [],
      "claim_source_links": []
    }
  },
  "status": "COMPLETED",
  "execution_status": "COMPLETED",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q4_03.json)
```json
{
  "case_id": "PILOT_Q4_03",
  "required_task_obligations": [
    "resolve_approved_anchor",
    "search_fixed_gazetteer_5000m",
    "report_source_bound_objects"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_058",
  "answer_sha256": "388fbbe2ac0c8e6491719251d5cbdfc00624bd374847aa7ee8bee06512de3cad",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "9b953ca0c4edf6f26dc622871131b10231f4dd1bafc63e6558ba2c3c4e2bf9e0",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_057 — 제한구역의 제한 종류는 어떤 코드로 표현해?

답안 hash: `f155eb748f5d0d59d76e9245e68c8398e2c281600b8a23ac91fa47d38ab32277`

### 실제 최종 답안
```json
{
  "document_answer": {
    "features": [
      {
        "code": "RestrictedArea",
        "definition": "A specified area on land or water designated by an appropriate authority within which access or navigation is restricted in accordance with certain specified conditions."
      }
    ],
    "attribute_bindings": [
      {
        "owner": "RestrictedArea",
        "attribute": "restriction",
        "lower": "1",
        "upper": null,
        "unbounded": true,
        "permitted_values": [
          "1",
          "2",
          "3",
          "4",
          "5",
          "6",
          "7",
          "8",
          "9",
          "10",
          "11",
          "12",
          "13",
          "14",
          "15",
          "16",
          "17",
          "18",
          "19",
          "20",
          "21",
          "22",
          "23",
          "24",
          "25",
          "26",
          "27",
          "39",
          "42"
        ],
        "attribute_definition": "The official legal statute of each kind of restricted area.",
        "global_listed_values": [
          {
            "label": "Anchoring Prohibited",
            "value": "1"
          },
          {
            "label": "Anchoring Restricted",
            "value": "2"
          },
          {
            "label": "Fishing Prohibited",
            "value": "3"
          },
          {
            "label": "Fishing Restricted",
            "value": "4"
          },
          {
            "label": "Trawling Prohibited",
            "value": "5"
          },
          {
            "label": "Trawling Restricted",
            "value": "6"
          },
          {
            "label": "Entry Prohibited",
            "value": "7"
          },
          {
            "label": "Entry Restricted",
            "value": "8"
          },
          {
            "label": "Dredging Prohibited",
            "value": "9"
          },
          {
            "label": "Dredging Restricted",
            "value": "10"
          },
          {
            "label": "Diving Prohibited",
            "value": "11"
          },
          {
            "label": "Diving Restricted",
            "value": "12"
          },
          {
            "label": "No Wake",
            "value": "13"
          },
          {
            "label": "Area To Be Avoided",
            "value": "14"
          },
          {
            "label": "Construction Prohibited",
            "value": "15"
          },
          {
            "label": "Discharging Prohibited",
            "value": "16"
          },
          {
            "label": "Discharging Restricted",
            "value": "17"
          },
          {
            "label": "Industrial or Mineral Exploration/Development Prohibited",
            "value": "18"
          },
          {
            "label": "Industrial or Mineral Exploration/Development Restricted",
            "value": "19"
          },
          {
            "label": "Drilling Prohibited",
            "value": "20"
          },
          {
            "label": "Drilling Restricted",
            "value": "21"
          },
          {
            "label": "Removal of Historical Artefacts Prohibited",
            "value": "22"
          },
          {
            "label": "Cargo Transhipment (Lightening) Prohibited",
            "value": "23"
          },
          {
            "label": "Dragging Prohibited",
            "value": "24"
          },
          {
            "label": "Stopping Prohibited",
            "value": "25"
          },
          {
            "label": "Landing Prohibited",
            "value": "26"
          },
          {
            "label": "Speed Restricted",
            "value": "27"
          },
          {
            "label": "Swimming Prohibited",
            "value": "39"
          },
          {
            "label": "Power-Driven Vessels Prohibited",
            "value": "42"
          }
        ]
      }
    ]
  },
  "search_executed": false,
  "execution_status": "COMPLETED",
  "source_coverage": {},
  "per_task_status": {},
  "mapping_provenance": {
    "version": "emitted_output_v1",
    "root": "final_state.final_dict",
    "retrieved_text_used_as_answer": false,
    "reference_used_for_mapping": false,
    "structured_document_answer_present": false
  },
  "status": "COMPLETED",
  "blocker": null,
  "clarification_request": [],
  "answer_text": "S-101 Feature Catalogue 2.0.0에서 RestrictedArea의 `restriction`는 다음과 같이 정의됩니다: The official legal statute of each kind of restricted area.\n\nRestrictedArea에 허용된 코드:\n- 1: Anchoring Prohibited\n- 2: Anchoring Restricted\n- 3: Fishing Prohibited\n- 4: Fishing Restricted\n- 5: Trawling Prohibited\n- 6: Trawling Restricted\n- 7: Entry Prohibited\n- 8: Entry Restricted\n- 9: Dredging Prohibited\n- 10: Dredging Restricted\n- 11: Diving Prohibited\n- 12: Diving Restricted\n- 13: No Wake\n- 14: Area To Be Avoided\n- 15: Construction Prohibited\n- 16: Discharging Prohibited\n- 17: Discharging Restricted\n- 18: Industrial or Mineral Exploration/Development Prohibited\n- 19: Industrial or Mineral Exploration/Development Restricted\n- 20: Drilling Prohibited\n- 21: Drilling Restricted\n- 22: Removal of Historical Artefacts Prohibited\n- 23: Cargo Transhipment (Lightening) Prohibited\n- 24: Dragging Prohibited\n- 25: Stopping Prohibited\n- 26: Landing Prohibited\n- 27: Speed Restricted\n- 39: Swimming Prohibited\n- 42: Power-Driven Vessels Prohibited\n\n`restriction`은 금지·제한 행위를 나타냅니다. 구역의 종류를 나타내는 `categoryOfRestrictedArea`와 구분합니다.\n\n근거: data/s101_feature_catalogue_v2_parsed.json (2.0.0), /features/152, /attributes/169, /features/152/bindings/5. 실제 제한구역 위치나 현행 통제 적용 여부를 조회한 결과는 아닙니다."
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q2_02.json)
```json
{
  "case_id": "PILOT_Q2_02",
  "required_task_obligations": [
    "distinguish_restriction_and_area_category",
    "explain_restriction_codes"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": [
    "Explain restriction codes separately from categoryOfRestrictedArea. RequiredArea alternatives from another FC edition are not substitutes for FC 2.0.0 RestrictedArea."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_057",
  "answer_sha256": "f155eb748f5d0d59d76e9245e68c8398e2c281600b8a23ac91fa47d38ab32277",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "fabe1a5c5a8cf78fb0187877e684b7b5a65fc2042042cee3b6ffd31828125ec0",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_056 — S-101에서 정박지는 어떤 객체야?

답안 hash: `dacef4f9a9138ce90db53f80642597c924858cc8ac93ed20a988e5650f3ec304`

### 실제 최종 답안
```json
{
  "answer_text": "S-101에서 정박지는 'ship' 객체입니다.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "document_answer": {
    "features": [],
    "attribute_bindings": [],
    "evidence": {
      "edition": "2.0.0",
      "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
      "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
      "locators": [],
      "claim_source_links": []
    }
  },
  "status": "COMPLETED",
  "execution_status": "COMPLETED",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q1_02.json)
```json
{
  "case_id": "PILOT_Q1_02",
  "required_task_obligations": [
    "explain_anchorage_area_definition"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_056",
  "answer_sha256": "dacef4f9a9138ce90db53f80642597c924858cc8ac93ed20a988e5650f3ec304",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "ce2444a8a93b02c4c28a87c1ef244e156e28739136a93268b89316088a7e3be8",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_055 — What is a wreck in S-101?

답안 hash: `8aaf532c597da2ba721329e6c9316b2f249b4bf4014743e6fc8582d0729ab431`

### 실제 최종 답안
```json
{
  "document_answer": {
    "features": [
      {
        "code": "Wreck",
        "definition": "The ruined remains of a stranded or sunken vessel which has been rendered useless.",
        "permitted_primitives": [
          "point",
          "surface"
        ]
      }
    ],
    "attribute_bindings": [
      {
        "owner": "Wreck",
        "attribute": "categoryOfWreck",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "categoryOfWreck",
        "permitted_values": [
          "1",
          "2",
          "3",
          "4",
          "5"
        ],
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "definition": "Classification of a wrecked or ruined ship.",
        "attribute_definition": "Classification of a wrecked or ruined ship.",
        "global_listed_values": [
          {
            "label": "Non-Dangerous Wreck",
            "value": "1"
          },
          {
            "label": "Dangerous Wreck",
            "value": "2"
          },
          {
            "label": "Distributed Remains of Wreck",
            "value": "3"
          },
          {
            "label": "Wreck Showing Mast/Masts",
            "value": "4"
          },
          {
            "label": "Wreck Showing Any Portion of Hull or Superstructure",
            "value": "5"
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='categoryOfWreck']]",
        "listed_values": [
          {
            "label": "Non-Dangerous Wreck",
            "value": "1"
          },
          {
            "label": "Dangerous Wreck",
            "value": "2"
          },
          {
            "label": "Distributed Remains of Wreck",
            "value": "3"
          },
          {
            "label": "Wreck Showing Mast/Masts",
            "value": "4"
          },
          {
            "label": "Wreck Showing Any Portion of Hull or Superstructure",
            "value": "5"
          }
        ],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='categoryOfWreck']]"
      },
      {
        "owner": "Wreck",
        "attribute": "expositionOfSounding",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "expositionOfSounding",
        "permitted_values": [
          "1",
          "2",
          "3"
        ],
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "definition": "Indicates the relationship of the depth of a feature to the range of depth of the surrounding depth area.",
        "attribute_definition": "Indicates the relationship of the depth of a feature to the range of depth of the surrounding depth area.",
        "global_listed_values": [
          {
            "label": "Within the Range of Depth of the Surrounding Depth Area",
            "value": "1"
          },
          {
            "label": "Shoaler Than the Range of Depth of the Surrounding Depth Area",
            "value": "2"
          },
          {
            "label": "Deeper Than the Range of Depth of the Surrounding Depth Area",
            "value": "3"
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='expositionOfSounding']]",
        "listed_values": [
          {
            "label": "Within the Range of Depth of the Surrounding Depth Area",
            "value": "1"
          },
          {
            "label": "Shoaler Than the Range of Depth of the Surrounding Depth Area",
            "value": "2"
          },
          {
            "label": "Deeper Than the Range of Depth of the Surrounding Depth Area",
            "value": "3"
          }
        ],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='expositionOfSounding']]"
      },
      {
        "owner": "Wreck",
        "attribute": "featureName",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "featureName",
        "permitted_values": [],
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "definition": "Provides the name of an entity, defines the national language of the name, and provides the option to display the name at various system display settings.",
        "attribute_definition": "Provides the name of an entity, defines the national language of the name, and provides the option to display the name at various system display settings.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='featureName']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='featureName']]"
      },
      {
        "owner": "Wreck",
        "attribute": "height",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "height",
        "permitted_values": [],
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "definition": "The value of the vertical distance to the highest point of the feature, measured from a specified vertical datum.",
        "attribute_definition": "The value of the vertical distance to the highest point of the feature, measured from a specified vertical datum.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='height']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='height']]"
      },
      {
        "owner": "Wreck",
        "attribute": "interoperabilityIdentifier",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "interoperabilityIdentifier",
        "permitted_values": [],
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "definition": "A common unique identifier for entities which describe a single real-world feature, and which is used to identify instances of the feature in end-user systems where the feature may be included in multiple data product types.",
        "attribute_definition": "A common unique identifier for entities which describe a single real-world feature, and which is used to identify instances of the feature in end-user systems where the feature may be included in multiple data product types.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='interoperabilityIdentifier']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='interoperabilityIdentifier']]"
      },
      {
        "owner": "Wreck",
        "attribute": "qualityOfVerticalMeasurement",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "qualityOfVerticalMeasurement",
        "permitted_values": [
          "1",
          "2",
          "3",
          "4",
          "6",
          "7",
          "8",
          "9"
        ],
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "definition": "The reliability of the value of a sounding.",
        "attribute_definition": "The reliability of the value of a sounding.",
        "global_listed_values": [
          {
            "label": "Depth Known",
            "value": "1"
          },
          {
            "label": "Depth or Least Depth Unknown",
            "value": "2"
          },
          {
            "label": "Doubtful Sounding",
            "value": "3"
          },
          {
            "label": "Unreliable Sounding",
            "value": "4"
          },
          {
            "label": "Least Depth Known",
            "value": "6"
          },
          {
            "label": "Least Depth Unknown, Safe Clearance at Value Shown",
            "value": "7"
          },
          {
            "label": "Value Reported (Not Surveyed)",
            "value": "8"
          },
          {
            "label": "Value Reported (Not Confirmed)",
            "value": "9"
          },
          {
            "label": "Maintained Depth",
            "value": "10"
          },
          {
            "label": "Not Regularly Maintained",
            "value": "11"
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='qualityOfVerticalMeasurement']]",
        "listed_values": [
          {
            "label": "Depth Known",
            "value": "1"
          },
          {
            "label": "Depth or Least Depth Unknown",
            "value": "2"
          },
          {
            "label": "Doubtful Sounding",
            "value": "3"
          },
          {
            "label": "Unreliable Sounding",
            "value": "4"
          },
          {
            "label": "Least Depth Known",
            "value": "6"
          },
          {
            "label": "Least Depth Unknown, Safe Clearance at Value Shown",
            "value": "7"
          },
          {
            "label": "Value Reported (Not Surveyed)",
            "value": "8"
          },
          {
            "label": "Value Reported (Not Confirmed)",
            "value": "9"
          },
          {
            "label": "Maintained Depth",
            "value": "10"
          },
          {
            "label": "Not Regularly Maintained",
            "value": "11"
          }
        ],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='qualityOfVerticalMeasurement']]"
      },
      {
        "owner": "Wreck",
        "attribute": "radarConspicuous",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "radarConspicuous",
        "permitted_values": [],
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "definition": "A feature which returns a strong radar echo.",
        "attribute_definition": "A feature which returns a strong radar echo.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='radarConspicuous']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='radarConspicuous']]"
      },
      {
        "owner": "Wreck",
        "attribute": "reportedDate",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "reportedDate",
        "permitted_values": [],
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "definition": "The date that the item was observed, done, or investigated.",
        "attribute_definition": "The date that the item was observed, done, or investigated.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='reportedDate']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='reportedDate']]"
      },
      {
        "owner": "Wreck",
        "attribute": "status",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "status",
        "permitted_values": [
          "7",
          "13",
          "18"
        ],
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "definition": "The condition of an object at a given instant in time.",
        "attribute_definition": "The condition of an object at a given instant in time.",
        "global_listed_values": [
          {
            "label": "Permanent",
            "value": "1"
          },
          {
            "label": "Occasional",
            "value": "2"
          },
          {
            "label": "Recommended",
            "value": "3"
          },
          {
            "label": "Not in Use",
            "value": "4"
          },
          {
            "label": "Periodic/Intermittent",
            "value": "5"
          },
          {
            "label": "Reserved",
            "value": "6"
          },
          {
            "label": "Temporary",
            "value": "7"
          },
          {
            "label": "Private",
            "value": "8"
          },
          {
            "label": "Mandatory",
            "value": "9"
          },
          {
            "label": "Extinguished",
            "value": "11"
          },
          {
            "label": "Illuminated",
            "value": "12"
          },
          {
            "label": "Historic",
            "value": "13"
          },
          {
            "label": "Public",
            "value": "14"
          },
          {
            "label": "Synchronized",
            "value": "15"
          },
          {
            "label": "Watched",
            "value": "16"
          },
          {
            "label": "Unwatched",
            "value": "17"
          },
          {
            "label": "Existence Doubtful",
            "value": "18"
          },
          {
            "label": "Buoyed",
            "value": "28"
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='status']]",
        "listed_values": [
          {
            "label": "Permanent",
            "value": "1"
          },
          {
            "label": "Occasional",
            "value": "2"
          },
          {
            "label": "Recommended",
            "value": "3"
          },
          {
            "label": "Not in Use",
            "value": "4"
          },
          {
            "label": "Periodic/Intermittent",
            "value": "5"
          },
          {
            "label": "Reserved",
            "value": "6"
          },
          {
            "label": "Temporary",
            "value": "7"
          },
          {
            "label": "Private",
            "value": "8"
          },
          {
            "label": "Mandatory",
            "value": "9"
          },
          {
            "label": "Extinguished",
            "value": "11"
          },
          {
            "label": "Illuminated",
            "value": "12"
          },
          {
            "label": "Historic",
            "value": "13"
          },
          {
            "label": "Public",
            "value": "14"
          },
          {
            "label": "Synchronized",
            "value": "15"
          },
          {
            "label": "Watched",
            "value": "16"
          },
          {
            "label": "Unwatched",
            "value": "17"
          },
          {
            "label": "Existence Doubtful",
            "value": "18"
          },
          {
            "label": "Buoyed",
            "value": "28"
          }
        ],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='status']]"
      },
      {
        "owner": "Wreck",
        "attribute": "techniqueOfVerticalMeasurement",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "techniqueOfVerticalMeasurement",
        "permitted_values": [
          "1",
          "2",
          "3",
          "4",
          "5",
          "8",
          "9",
          "10",
          "11",
          "12",
          "13",
          "15",
          "16",
          "17",
          "18"
        ],
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "definition": "Survey method used to obtain depth information.",
        "attribute_definition": "Survey method used to obtain depth information.",
        "global_listed_values": [
          {
            "label": "Found by Echo Sounder",
            "value": "1"
          },
          {
            "label": "Found by Side Scan Sonar",
            "value": "2"
          },
          {
            "label": "Found by Multi Beam",
            "value": "3"
          },
          {
            "label": "Found by Diver",
            "value": "4"
          },
          {
            "label": "Found by Lead Line",
            "value": "5"
          },
          {
            "label": "Swept by Vertical Acoustic System",
            "value": "8"
          },
          {
            "label": "Found by Electromagnetic Sensor",
            "value": "9"
          },
          {
            "label": "Photogrammetry",
            "value": "10"
          },
          {
            "label": "Satellite Imagery",
            "value": "11"
          },
          {
            "label": "Found by Levelling",
            "value": "12"
          },
          {
            "label": "Swept by Side Scan Sonar",
            "value": "13"
          },
          {
            "label": "Found by LIDAR",
            "value": "15"
          },
          {
            "label": "Synthetic Aperture Radar",
            "value": "16"
          },
          {
            "label": "Hyperspectral Imagery",
            "value": "17"
          },
          {
            "label": "Mechanically Swept",
            "value": "18"
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='techniqueOfVerticalMeasurement']]",
        "listed_values": [
          {
            "label": "Found by Echo Sounder",
            "value": "1"
          },
          {
            "label": "Found by Side Scan Sonar",
            "value": "2"
          },
          {
            "label": "Found by Multi Beam",
            "value": "3"
          },
          {
            "label": "Found by Diver",
            "value": "4"
          },
          {
            "label": "Found by Lead Line",
            "value": "5"
          },
          {
            "label": "Swept by Vertical Acoustic System",
            "value": "8"
          },
          {
            "label": "Found by Electromagnetic Sensor",
            "value": "9"
          },
          {
            "label": "Photogrammetry",
            "value": "10"
          },
          {
            "label": "Satellite Imagery",
            "value": "11"
          },
          {
            "label": "Found by Levelling",
            "value": "12"
          },
          {
            "label": "Swept by Side Scan Sonar",
            "value": "13"
          },
          {
            "label": "Found by LIDAR",
            "value": "15"
          },
          {
            "label": "Synthetic Aperture Radar",
            "value": "16"
          },
          {
            "label": "Hyperspectral Imagery",
            "value": "17"
          },
          {
            "label": "Mechanically Swept",
            "value": "18"
          }
        ],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='techniqueOfVerticalMeasurement']]"
      },
      {
        "owner": "Wreck",
        "attribute": "valueOfSounding",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "valueOfSounding",
        "permitted_values": [],
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "definition": "The value of the measurement of a sounding relative to the chart datum.",
        "attribute_definition": "The value of the measurement of a sounding relative to the chart datum.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='valueOfSounding']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='valueOfSounding']]"
      },
      {
        "owner": "Wreck",
        "attribute": "visualProminence",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "visualProminence",
        "permitted_values": [
          "1",
          "2",
          "3"
        ],
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "definition": "The extent to which a feature, either natural or artificial, is visible from seaward.",
        "attribute_definition": "The extent to which a feature, either natural or artificial, is visible from seaward.",
        "global_listed_values": [
          {
            "label": "Visually Conspicuous",
            "value": "1"
          },
          {
            "label": "Not Visually Conspicuous",
            "value": "2"
          },
          {
            "label": "Prominent",
            "value": "3"
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='visualProminence']]",
        "listed_values": [
          {
            "label": "Visually Conspicuous",
            "value": "1"
          },
          {
            "label": "Not Visually Conspicuous",
            "value": "2"
          },
          {
            "label": "Prominent",
            "value": "3"
          }
        ],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='visualProminence']]"
      },
      {
        "owner": "Wreck",
        "attribute": "waterLevelEffect",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "waterLevelEffect",
        "permitted_values": [
          "1",
          "2",
          "3",
          "4",
          "5"
        ],
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "definition": "The effect of the surrounding water on an object.",
        "attribute_definition": "The effect of the surrounding water on an object.",
        "global_listed_values": [
          {
            "label": "Partly Submerged at High Water",
            "value": "1"
          },
          {
            "label": "Always Dry",
            "value": "2"
          },
          {
            "label": "Always Under Water/Submerged",
            "value": "3"
          },
          {
            "label": "Covers and Uncovers",
            "value": "4"
          },
          {
            "label": "Awash",
            "value": "5"
          },
          {
            "label": "Subject to Inundation or Flooding",
            "value": "6"
          },
          {
            "label": "Floating",
            "value": "7"
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='waterLevelEffect']]",
        "listed_values": [
          {
            "label": "Partly Submerged at High Water",
            "value": "1"
          },
          {
            "label": "Always Dry",
            "value": "2"
          },
          {
            "label": "Always Under Water/Submerged",
            "value": "3"
          },
          {
            "label": "Covers and Uncovers",
            "value": "4"
          },
          {
            "label": "Awash",
            "value": "5"
          },
          {
            "label": "Subject to Inundation or Flooding",
            "value": "6"
          },
          {
            "label": "Floating",
            "value": "7"
          }
        ],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='waterLevelEffect']]"
      },
      {
        "owner": "Wreck",
        "attribute": "scaleMinimum",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "scaleMinimum",
        "permitted_values": [],
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "definition": "The minimum scale at which the feature may be used for example for ECDIS presentation.",
        "attribute_definition": "The minimum scale at which the feature may be used for example for ECDIS presentation.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='scaleMinimum']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='scaleMinimum']]"
      },
      {
        "owner": "Wreck",
        "attribute": "information",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "information",
        "permitted_values": [],
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "definition": "Textual information about the feature. The information may be provided as a string of text or as a file name of a single external text file that contains the text.",
        "attribute_definition": "Textual information about the feature. The information may be provided as a string of text or as a file name of a single external text file that contains the text.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='information']]"
      },
      {
        "owner": "Wreck",
        "attribute": "pictorialRepresentation",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "pictorialRepresentation",
        "permitted_values": [],
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "definition": "The file name of an externally referenced picture file.",
        "attribute_definition": "The file name of an externally referenced picture file.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='pictorialRepresentation']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='pictorialRepresentation']]"
      },
      {
        "owner": "Wreck",
        "attribute": "defaultClearanceDepth",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "defaultClearanceDepth",
        "permitted_values": [],
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "definition": "The depth value determined for an underwater hazard of unknown depth, based on the depth of the surrounding area.",
        "attribute_definition": "The depth value determined for an underwater hazard of unknown depth, based on the depth of the surrounding area.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='defaultClearanceDepth']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='defaultClearanceDepth']]"
      },
      {
        "owner": "Wreck",
        "attribute": "surroundingDepth",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "surroundingDepth",
        "permitted_values": [],
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "definition": "The depth value determined for seabed around an underwater hazard, based on the depth of the surrounding area.",
        "attribute_definition": "The depth value determined for seabed around an underwater hazard, based on the depth of the surrounding area.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='surroundingDepth']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='surroundingDepth']]"
      }
    ],
    "definition_quote": "The ruined remains of a stranded or sunken vessel which has been rendered useless.",
    "source_ref": "data/s101_feature_catalogue_v2_parsed.json",
    "source_sha256": "0d26c66d0e1afd8a6ae33629e9bc1bb929c6a3735ccd1d60f637d149a54cad37",
    "evidence": {
      "edition": "2.0.0",
      "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
      "parsed_source_sha256": "0d26c66d0e1afd8a6ae33629e9bc1bb929c6a3735ccd1d60f637d149a54cad37",
      "source_ref": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
      "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
      "locators": [
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='categoryOfWreck']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='expositionOfSounding']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='featureName']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='height']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='interoperabilityIdentifier']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='qualityOfVerticalMeasurement']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='radarConspicuous']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='reportedDate']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='status']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='techniqueOfVerticalMeasurement']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='valueOfSounding']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='visualProminence']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='waterLevelEffect']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='scaleMinimum']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='information']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='pictorialRepresentation']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='defaultClearanceDepth']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='surroundingDepth']]"
      ],
      "claim_source_links": [
        {
          "claim": "The ruined remains of a stranded or sunken vessel which has been rendered useless.",
          "source_ref": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
          "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
          "definition_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='definition']",
          "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='definition']"
        }
      ]
    }
  },
  "search_executed": false,
  "execution_status": "COMPLETED",
  "source_coverage": {},
  "per_task_status": {},
  "mapping_provenance": {
    "version": "emitted_output_v1",
    "root": "final_state.final_dict",
    "retrieved_text_used_as_answer": false,
    "reference_used_for_mapping": false,
    "structured_document_answer_present": true
  },
  "status": "COMPLETED",
  "blocker": null,
  "clarification_request": [],
  "answer_text": "S-101 Feature Catalogue 2.0.0\n\nWreck: The ruined remains of a stranded or sunken vessel which has been rendered useless.\n허용 기하: point, surface\n\n근거: data/s101_feature_catalogue_v2_parsed.json; //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='categoryOfWreck']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='expositionOfSounding']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='featureName']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='height']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='interoperabilityIdentifier']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='qualityOfVerticalMeasurement']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='radarConspicuous']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='reportedDate']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='status']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='techniqueOfVerticalMeasurement']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='valueOfSounding']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='visualProminence']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='waterLevelEffect']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='scaleMinimum']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='information']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='pictorialRepresentation']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='defaultClearanceDepth']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='surroundingDepth']]"
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q1_03.json)
```json
{
  "case_id": "PILOT_Q1_03",
  "required_task_obligations": [
    "explain_wreck_definition"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_055",
  "answer_sha256": "8aaf532c597da2ba721329e6c9316b2f249b4bf4014743e6fc8582d0729ab431",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "249042a18409bf6edb87cd18e467a589d6b0c940f8ee73682cabc7c7c4c4aa6f",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_054 — 등대와 부표를 구분하는 S-101 근거를 알려줘.

답안 hash: `c681c0dedac47db665ffe311d5781af2d9b26d8a33fd30f8db1e185bcd7727f0`

### 실제 최종 답안
```json
{
  "answer_text": "等明灯和浮标在S-101数据库中可以区分。",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "status": "NEEDS_USER_INPUT",
  "clarification_request": "等明灯和浮标在S-101数据库中可以区分。",
  "execution_status": "NEEDS_USER_INPUT",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q6_02.json)
```json
{
  "case_id": "PILOT_Q6_02",
  "required_task_obligations": [
    "compare_fixed_structure_and_floating_aid_models",
    "cite_comparison_evidence"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "single_Lighthouse_feature_assertion",
    "global_colour_codes_for_feature_binding"
  ],
  "scope_notes": [
    "Landmark/Building describe conditional structure alternatives; LightAllAround/LightSectored describe light alternatives. Listing these for explanation does not assert all must exist in one physical lighthouse.",
    "Bounded comparison: LateralBuoy is the explicitly selected representative floating-aid feature; no claim to exhaustively describe every buoy class. Compare with conditional structure/light models."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_054",
  "answer_sha256": "c681c0dedac47db665ffe311d5781af2d9b26d8a33fd30f8db1e185bcd7727f0",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "9372997b429c377aee42e67f723319241f9d6fdd0a4c088b8dca52a4154bdcd6",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_053 — What source supports the S-101 definition of AnchorageArea?

답안 hash: `e1b4fc698f5499bbf16ea9fa480a7833ab72c9583c69b9ef156947a706bf2b91`

### 실제 최종 답안
```json
{
  "document_answer": {
    "features": [
      {
        "code": "AnchorageArea",
        "definition": "An area in which vessels or seaplanes anchor or may anchor.",
        "permitted_primitives": [
          "point",
          "surface"
        ]
      }
    ],
    "attribute_bindings": [
      {
        "owner": "AnchorageArea",
        "attribute": "categoryOfAnchorage",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "categoryOfAnchorage",
        "permitted_values": [
          "1",
          "2",
          "3",
          "5",
          "6",
          "7",
          "9",
          "10",
          "14",
          "15"
        ],
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "definition": "Classification of an area where different use types of vessel can remain static.",
        "attribute_definition": "Classification of an area where different use types of vessel can remain static.",
        "global_listed_values": [
          {
            "label": "Unrestricted Anchorage",
            "value": "1"
          },
          {
            "label": "Deep Water Anchorage",
            "value": "2"
          },
          {
            "label": "Tanker Anchorage",
            "value": "3"
          },
          {
            "label": "Quarantine Anchorage",
            "value": "5"
          },
          {
            "label": "Seaplane Anchorage",
            "value": "6"
          },
          {
            "label": "Small Craft Anchorage",
            "value": "7"
          },
          {
            "label": "Anchorage for Periods Up To 24 Hours",
            "value": "9"
          },
          {
            "label": "Anchorage for a Limited Period of Time",
            "value": "10"
          },
          {
            "label": "Waiting Anchorage",
            "value": "14"
          },
          {
            "label": "Reported Anchorage",
            "value": "15"
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='categoryOfAnchorage']]",
        "listed_values": [
          {
            "label": "Unrestricted Anchorage",
            "value": "1"
          },
          {
            "label": "Deep Water Anchorage",
            "value": "2"
          },
          {
            "label": "Tanker Anchorage",
            "value": "3"
          },
          {
            "label": "Quarantine Anchorage",
            "value": "5"
          },
          {
            "label": "Seaplane Anchorage",
            "value": "6"
          },
          {
            "label": "Small Craft Anchorage",
            "value": "7"
          },
          {
            "label": "Anchorage for Periods Up To 24 Hours",
            "value": "9"
          },
          {
            "label": "Anchorage for a Limited Period of Time",
            "value": "10"
          },
          {
            "label": "Waiting Anchorage",
            "value": "14"
          },
          {
            "label": "Reported Anchorage",
            "value": "15"
          }
        ],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='categoryOfAnchorage']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "categoryOfCargo",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "categoryOfCargo",
        "permitted_values": [
          "1",
          "2",
          "3",
          "4",
          "5",
          "6",
          "7",
          "8",
          "9",
          "10",
          "11",
          "12",
          "13",
          "14",
          "15"
        ],
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "definition": "Classification of the different types of cargo that a ship may be carrying.",
        "attribute_definition": "Classification of the different types of cargo that a ship may be carrying.",
        "global_listed_values": [
          {
            "label": "Bulk",
            "value": "1"
          },
          {
            "label": "Container",
            "value": "2"
          },
          {
            "label": "General",
            "value": "3"
          },
          {
            "label": "Liquid",
            "value": "4"
          },
          {
            "label": "Passenger",
            "value": "5"
          },
          {
            "label": "Livestock",
            "value": "6"
          },
          {
            "label": "Dangerous or Hazardous",
            "value": "7"
          },
          {
            "label": "Heavy Lift",
            "value": "8"
          },
          {
            "label": "Ballast",
            "value": "9"
          },
          {
            "label": "Dry Bulk Cargo",
            "value": "10"
          },
          {
            "label": "Liquid Bulk Cargo",
            "value": "11"
          },
          {
            "label": "Reefer Container Cargo",
            "value": "12"
          },
          {
            "label": "Ro-Ro Cargo",
            "value": "13"
          },
          {
            "label": "Project Cargo",
            "value": "14"
          },
          {
            "label": "Break Bulk Cargo",
            "value": "15"
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='categoryOfCargo']]",
        "listed_values": [
          {
            "label": "Bulk",
            "value": "1"
          },
          {
            "label": "Container",
            "value": "2"
          },
          {
            "label": "General",
            "value": "3"
          },
          {
            "label": "Liquid",
            "value": "4"
          },
          {
            "label": "Passenger",
            "value": "5"
          },
          {
            "label": "Livestock",
            "value": "6"
          },
          {
            "label": "Dangerous or Hazardous",
            "value": "7"
          },
          {
            "label": "Heavy Lift",
            "value": "8"
          },
          {
            "label": "Ballast",
            "value": "9"
          },
          {
            "label": "Dry Bulk Cargo",
            "value": "10"
          },
          {
            "label": "Liquid Bulk Cargo",
            "value": "11"
          },
          {
            "label": "Reefer Container Cargo",
            "value": "12"
          },
          {
            "label": "Ro-Ro Cargo",
            "value": "13"
          },
          {
            "label": "Project Cargo",
            "value": "14"
          },
          {
            "label": "Break Bulk Cargo",
            "value": "15"
          }
        ],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='categoryOfCargo']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "featureName",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "featureName",
        "permitted_values": [],
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "definition": "Provides the name of an entity, defines the national language of the name, and provides the option to display the name at various system display settings.",
        "attribute_definition": "Provides the name of an entity, defines the national language of the name, and provides the option to display the name at various system display settings.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='featureName']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='featureName']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "fixedDateRange",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "fixedDateRange",
        "permitted_values": [],
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "definition": "An active period of a single fixed event or occurrence, as the date range between discrete start and end dates.",
        "attribute_definition": "An active period of a single fixed event or occurrence, as the date range between discrete start and end dates.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='fixedDateRange']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='fixedDateRange']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "interoperabilityIdentifier",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "interoperabilityIdentifier",
        "permitted_values": [],
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "definition": "A common unique identifier for entities which describe a single real-world feature, and which is used to identify instances of the feature in end-user systems where the feature may be included in multiple data product types.",
        "attribute_definition": "A common unique identifier for entities which describe a single real-world feature, and which is used to identify instances of the feature in end-user systems where the feature may be included in multiple data product types.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='interoperabilityIdentifier']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='interoperabilityIdentifier']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "periodicDateRange",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "periodicDateRange",
        "permitted_values": [],
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "definition": "The active period of a recurring event or occurrence.",
        "attribute_definition": "The active period of a recurring event or occurrence.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='periodicDateRange']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='periodicDateRange']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "restriction",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "restriction",
        "permitted_values": [
          "2",
          "3",
          "4",
          "5",
          "6",
          "8",
          "9",
          "10",
          "11",
          "12",
          "13",
          "15",
          "16",
          "17",
          "18",
          "19",
          "20",
          "21",
          "23",
          "24",
          "27",
          "39"
        ],
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "definition": "The official legal statute of each kind of restricted area.",
        "attribute_definition": "The official legal statute of each kind of restricted area.",
        "global_listed_values": [
          {
            "label": "Anchoring Prohibited",
            "value": "1"
          },
          {
            "label": "Anchoring Restricted",
            "value": "2"
          },
          {
            "label": "Fishing Prohibited",
            "value": "3"
          },
          {
            "label": "Fishing Restricted",
            "value": "4"
          },
          {
            "label": "Trawling Prohibited",
            "value": "5"
          },
          {
            "label": "Trawling Restricted",
            "value": "6"
          },
          {
            "label": "Entry Prohibited",
            "value": "7"
          },
          {
            "label": "Entry Restricted",
            "value": "8"
          },
          {
            "label": "Dredging Prohibited",
            "value": "9"
          },
          {
            "label": "Dredging Restricted",
            "value": "10"
          },
          {
            "label": "Diving Prohibited",
            "value": "11"
          },
          {
            "label": "Diving Restricted",
            "value": "12"
          },
          {
            "label": "No Wake",
            "value": "13"
          },
          {
            "label": "Area To Be Avoided",
            "value": "14"
          },
          {
            "label": "Construction Prohibited",
            "value": "15"
          },
          {
            "label": "Discharging Prohibited",
            "value": "16"
          },
          {
            "label": "Discharging Restricted",
            "value": "17"
          },
          {
            "label": "Industrial or Mineral Exploration/Development Prohibited",
            "value": "18"
          },
          {
            "label": "Industrial or Mineral Exploration/Development Restricted",
            "value": "19"
          },
          {
            "label": "Drilling Prohibited",
            "value": "20"
          },
          {
            "label": "Drilling Restricted",
            "value": "21"
          },
          {
            "label": "Removal of Historical Artefacts Prohibited",
            "value": "22"
          },
          {
            "label": "Cargo Transhipment (Lightening) Prohibited",
            "value": "23"
          },
          {
            "label": "Dragging Prohibited",
            "value": "24"
          },
          {
            "label": "Stopping Prohibited",
            "value": "25"
          },
          {
            "label": "Landing Prohibited",
            "value": "26"
          },
          {
            "label": "Speed Restricted",
            "value": "27"
          },
          {
            "label": "Swimming Prohibited",
            "value": "39"
          },
          {
            "label": "Power-Driven Vessels Prohibited",
            "value": "42"
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='restriction']]",
        "listed_values": [
          {
            "label": "Anchoring Prohibited",
            "value": "1"
          },
          {
            "label": "Anchoring Restricted",
            "value": "2"
          },
          {
            "label": "Fishing Prohibited",
            "value": "3"
          },
          {
            "label": "Fishing Restricted",
            "value": "4"
          },
          {
            "label": "Trawling Prohibited",
            "value": "5"
          },
          {
            "label": "Trawling Restricted",
            "value": "6"
          },
          {
            "label": "Entry Prohibited",
            "value": "7"
          },
          {
            "label": "Entry Restricted",
            "value": "8"
          },
          {
            "label": "Dredging Prohibited",
            "value": "9"
          },
          {
            "label": "Dredging Restricted",
            "value": "10"
          },
          {
            "label": "Diving Prohibited",
            "value": "11"
          },
          {
            "label": "Diving Restricted",
            "value": "12"
          },
          {
            "label": "No Wake",
            "value": "13"
          },
          {
            "label": "Area To Be Avoided",
            "value": "14"
          },
          {
            "label": "Construction Prohibited",
            "value": "15"
          },
          {
            "label": "Discharging Prohibited",
            "value": "16"
          },
          {
            "label": "Discharging Restricted",
            "value": "17"
          },
          {
            "label": "Industrial or Mineral Exploration/Development Prohibited",
            "value": "18"
          },
          {
            "label": "Industrial or Mineral Exploration/Development Restricted",
            "value": "19"
          },
          {
            "label": "Drilling Prohibited",
            "value": "20"
          },
          {
            "label": "Drilling Restricted",
            "value": "21"
          },
          {
            "label": "Removal of Historical Artefacts Prohibited",
            "value": "22"
          },
          {
            "label": "Cargo Transhipment (Lightening) Prohibited",
            "value": "23"
          },
          {
            "label": "Dragging Prohibited",
            "value": "24"
          },
          {
            "label": "Stopping Prohibited",
            "value": "25"
          },
          {
            "label": "Landing Prohibited",
            "value": "26"
          },
          {
            "label": "Speed Restricted",
            "value": "27"
          },
          {
            "label": "Swimming Prohibited",
            "value": "39"
          },
          {
            "label": "Power-Driven Vessels Prohibited",
            "value": "42"
          }
        ],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='restriction']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "status",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "status",
        "permitted_values": [
          "1",
          "2",
          "3",
          "5",
          "6",
          "7",
          "8",
          "9",
          "14"
        ],
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "definition": "The condition of an object at a given instant in time.",
        "attribute_definition": "The condition of an object at a given instant in time.",
        "global_listed_values": [
          {
            "label": "Permanent",
            "value": "1"
          },
          {
            "label": "Occasional",
            "value": "2"
          },
          {
            "label": "Recommended",
            "value": "3"
          },
          {
            "label": "Not in Use",
            "value": "4"
          },
          {
            "label": "Periodic/Intermittent",
            "value": "5"
          },
          {
            "label": "Reserved",
            "value": "6"
          },
          {
            "label": "Temporary",
            "value": "7"
          },
          {
            "label": "Private",
            "value": "8"
          },
          {
            "label": "Mandatory",
            "value": "9"
          },
          {
            "label": "Extinguished",
            "value": "11"
          },
          {
            "label": "Illuminated",
            "value": "12"
          },
          {
            "label": "Historic",
            "value": "13"
          },
          {
            "label": "Public",
            "value": "14"
          },
          {
            "label": "Synchronized",
            "value": "15"
          },
          {
            "label": "Watched",
            "value": "16"
          },
          {
            "label": "Unwatched",
            "value": "17"
          },
          {
            "label": "Existence Doubtful",
            "value": "18"
          },
          {
            "label": "Buoyed",
            "value": "28"
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='status']]",
        "listed_values": [
          {
            "label": "Permanent",
            "value": "1"
          },
          {
            "label": "Occasional",
            "value": "2"
          },
          {
            "label": "Recommended",
            "value": "3"
          },
          {
            "label": "Not in Use",
            "value": "4"
          },
          {
            "label": "Periodic/Intermittent",
            "value": "5"
          },
          {
            "label": "Reserved",
            "value": "6"
          },
          {
            "label": "Temporary",
            "value": "7"
          },
          {
            "label": "Private",
            "value": "8"
          },
          {
            "label": "Mandatory",
            "value": "9"
          },
          {
            "label": "Extinguished",
            "value": "11"
          },
          {
            "label": "Illuminated",
            "value": "12"
          },
          {
            "label": "Historic",
            "value": "13"
          },
          {
            "label": "Public",
            "value": "14"
          },
          {
            "label": "Synchronized",
            "value": "15"
          },
          {
            "label": "Watched",
            "value": "16"
          },
          {
            "label": "Unwatched",
            "value": "17"
          },
          {
            "label": "Existence Doubtful",
            "value": "18"
          },
          {
            "label": "Buoyed",
            "value": "28"
          }
        ],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='status']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "vesselSpeedLimit",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "vesselSpeedLimit",
        "permitted_values": [],
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "definition": "The maximum allowed rate of travel for a vessel in an area in knots.",
        "attribute_definition": "The maximum allowed rate of travel for a vessel in an area in knots.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='vesselSpeedLimit']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='vesselSpeedLimit']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "scaleMinimum",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "scaleMinimum",
        "permitted_values": [],
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "definition": "The minimum scale at which the feature may be used for example for ECDIS presentation.",
        "attribute_definition": "The minimum scale at which the feature may be used for example for ECDIS presentation.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='scaleMinimum']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='scaleMinimum']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "information",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "information",
        "permitted_values": [],
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "definition": "Textual information about the feature. The information may be provided as a string of text or as a file name of a single external text file that contains the text.",
        "attribute_definition": "Textual information about the feature. The information may be provided as a string of text or as a file name of a single external text file that contains the text.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='information']]"
      }
    ],
    "definition_quote": "An area in which vessels or seaplanes anchor or may anchor.",
    "source_ref": "data/s101_feature_catalogue_v2_parsed.json",
    "source_sha256": "0d26c66d0e1afd8a6ae33629e9bc1bb929c6a3735ccd1d60f637d149a54cad37",
    "evidence": {
      "edition": "2.0.0",
      "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
      "parsed_source_sha256": "0d26c66d0e1afd8a6ae33629e9bc1bb929c6a3735ccd1d60f637d149a54cad37",
      "source_ref": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
      "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
      "locators": [
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='categoryOfAnchorage']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='categoryOfCargo']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='featureName']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='fixedDateRange']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='interoperabilityIdentifier']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='periodicDateRange']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='restriction']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='status']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='vesselSpeedLimit']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='scaleMinimum']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='information']]"
      ],
      "claim_source_links": [
        {
          "claim": "An area in which vessels or seaplanes anchor or may anchor.",
          "source_ref": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
          "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
          "definition_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='definition']",
          "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='definition']"
        }
      ]
    }
  },
  "search_executed": false,
  "execution_status": "COMPLETED",
  "source_coverage": {},
  "per_task_status": {},
  "mapping_provenance": {
    "version": "emitted_output_v1",
    "root": "final_state.final_dict",
    "retrieved_text_used_as_answer": false,
    "reference_used_for_mapping": false,
    "structured_document_answer_present": true
  },
  "status": "COMPLETED",
  "blocker": null,
  "clarification_request": [],
  "answer_text": "S-101 Feature Catalogue 2.0.0\n\nAnchorageArea: An area in which vessels or seaplanes anchor or may anchor.\n허용 기하: point, surface\n\n근거: data/s101_feature_catalogue_v2_parsed.json; //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='categoryOfAnchorage']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='categoryOfCargo']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='featureName']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='fixedDateRange']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='interoperabilityIdentifier']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='periodicDateRange']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='restriction']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='status']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='vesselSpeedLimit']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='scaleMinimum']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='information']]"
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q6_03.json)
```json
{
  "case_id": "PILOT_Q6_03",
  "required_task_obligations": [
    "provide_anchorage_definition_source",
    "cite_catalogue_edition_and_locator"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_053",
  "answer_sha256": "e1b4fc698f5499bbf16ea9fa480a7833ab72c9583c69b9ef156947a706bf2b91",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "f547865c71ea3c32bf5d3e6ba05912bb8eaf345840fce9747022efeebea4a22f",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_052 — 독도 부근에서 가장 가까운 등대를 찾아줘.

답안 hash: `a9e78726a2032b9d26eb8490677d1395de32ca6370918dd90b67325c7f2d347a`

### 실제 최종 답안
```json
{
  "answer_text": "The nearest lighthouse to Dokdo is located at the Dokdo Lighthouse.",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q3_01.json)
```json
{
  "case_id": "PILOT_Q3_01",
  "required_task_obligations": [
    "resolve_reference",
    "resolve_lighthouse_target_conditions",
    "verify_coverage",
    "find_nearest",
    "report_objects_or_unresolved_reason"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "User-approved source-bound safe abstention; document explanations are separately evaluated optional partial output."
  ],
  "expected_spatial_behavior": {
    "accepted_states": [
      "BLOCKED_DATA",
      "DATA_OUT_OF_SCOPE"
    ],
    "required_disclosure": "Current connected snapshot cannot determine the answer for the requested spatial extent",
    "per_target": {
      "Lighthouse": {
        "status": "BLOCKED_DATA",
        "object_ids": null
      }
    },
    "empty_result_as_answer_forbidden": true,
    "claim_spatial_success_forbidden": true
  }
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_052",
  "answer_sha256": "a9e78726a2032b9d26eb8490677d1395de32ca6370918dd90b67325c7f2d347a",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "a7341fabd7bbfca10020df4abfd30150f4fccc4eceb4a0f2364cd117f11ebd95",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_051 — 부산항 영역 안의 정박지를 찾아줘.

답안 hash: `edc85a1b3aa9065db57c85e83173ab6b102aee216c6ee1e823931a38e25fb77f`

### 실제 최종 답안
```json
{
  "answer_text": "The watercraft located within the Busan Port boundary.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "validator_blockers": [
    "BLOCKED_DATA: public catalogue document evidence unavailable"
  ],
  "status": "BLOCKED_DATA",
  "execution_status": "BLOCKED_DATA",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q3_02.json)
```json
{
  "case_id": "PILOT_Q3_02",
  "required_task_obligations": [
    "resolve_official_port_polygon",
    "verify_coverage",
    "search_within_polygon",
    "report_objects_or_unresolved_reason"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "Object IDs refer to frozen snapshot records, not deduplicated physical facilities or the whole legal port."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_051",
  "answer_sha256": "edc85a1b3aa9065db57c85e83173ab6b102aee216c6ee1e823931a38e25fb77f",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "a6bbdc2d5efd3ca88252048c4d3b46db491eeef3535aaa913ffe7ce7eb09428e",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_050 — S-101에서 정박지는 어떤 객체야?

답안 hash: `282672ad5e414ef305455ba07899237f14784ec59062af471cd5b2ceccd8f3c6`

### 실제 최종 답안
```json
{
  "answer_text": "S-101에서 정박지는 'ship' 객체입니다.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "status": "NEEDS_USER_INPUT",
  "clarification_request": "S-101에서 정박지는 'ship' 객체입니다.",
  "execution_status": "NEEDS_USER_INPUT",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q1_02.json)
```json
{
  "case_id": "PILOT_Q1_02",
  "required_task_obligations": [
    "explain_anchorage_area_definition"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_050",
  "answer_sha256": "282672ad5e414ef305455ba07899237f14784ec59062af471cd5b2ceccd8f3c6",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "59e271281f4495e2bfdf6a0d2a465b801012e6a7717381802a197a2b329e0512",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_049 — 제한구역의 제한 종류는 어떤 코드로 표현해?

답안 hash: `ed4b6f25738b0e5bb5ecf9489d066e4ac8785594406cfbd140a34b38454f2b52`

### 실제 최종 답안
```json
{
  "answer_text": "제한구역의 제한 종류는 '제한구역'이라는 공식적인 문서 코드로 표현됩니다.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "status": "NEEDS_USER_INPUT",
  "clarification_request": "제한구역의 제한 종류는 '제한구역'이라는 공식적인 문서 코드로 표현됩니다.",
  "execution_status": "NEEDS_USER_INPUT",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q2_02.json)
```json
{
  "case_id": "PILOT_Q2_02",
  "required_task_obligations": [
    "distinguish_restriction_and_area_category",
    "explain_restriction_codes"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": [
    "Explain restriction codes separately from categoryOfRestrictedArea. RequiredArea alternatives from another FC edition are not substitutes for FC 2.0.0 RestrictedArea."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_049",
  "answer_sha256": "ed4b6f25738b0e5bb5ecf9489d066e4ac8785594406cfbd140a34b38454f2b52",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "23d80240af822fbccf5a98f6f25df387ede31df248a416295088e179142ca83d",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_048 — 등대의 S-101 객체 유형과 정의를 알려줘.

답안 hash: `91d9a78ff8d0452a458793fb65e7c9d2c0f97abeb410f733caa9d590ace4e64b`

### 실제 최종 답안
```json
{
  "answer_text": "등대는 S-101 객체 중 하나입니다. 이 객체는 등대의 정의와 유형을 나타냅니다. S-101는 등대의 공통적인 객체 코드입니다.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "document_answer": {
    "features": [],
    "attribute_bindings": [],
    "evidence": {
      "edition": "2.0.0",
      "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
      "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
      "locators": [],
      "claim_source_links": []
    }
  },
  "status": "COMPLETED",
  "execution_status": "COMPLETED",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q1_01.json)
```json
{
  "case_id": "PILOT_Q1_01",
  "required_task_obligations": [
    "explain_structure_and_light_distinction",
    "explain_conditional_feature_mapping"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "single_Lighthouse_feature_assertion",
    "global_colour_codes_for_feature_binding"
  ],
  "scope_notes": [
    "Landmark/Building describe conditional structure alternatives; LightAllAround/LightSectored describe light alternatives. Listing these for explanation does not assert all must exist in one physical lighthouse."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_048",
  "answer_sha256": "91d9a78ff8d0452a458793fb65e7c9d2c0f97abeb410f733caa9d590ace4e64b",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "bde88339be42b11a715ecec46e7c3cb8626d0db152e74c2a28cd263973b61743",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_047 — 독도 주변 반경 5000m의 해양지명을 찾아줘.

답안 hash: `c81bdeb8a334711ad38f10e1f7860ec6dd04cce1c4889f195c9fc29056980c7d`

### 실제 최종 답안
```json
{
  "answer_text": "独岛位于韩国济州道的独岛郡，距离济州岛约10公里。",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "validator_blockers": [
    "BLOCKED_DATA: public catalogue document evidence unavailable"
  ],
  "status": "BLOCKED_DATA",
  "execution_status": "BLOCKED_DATA",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q4_02.json)
```json
{
  "case_id": "PILOT_Q4_02",
  "required_task_obligations": [
    "resolve_approved_anchor",
    "search_fixed_gazetteer_5000m",
    "report_source_bound_objects"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_047",
  "answer_sha256": "c81bdeb8a334711ad38f10e1f7860ec6dd04cce1c4889f195c9fc29056980c7d",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "22dfbb62cfdf949ef450a74449cf7ea264ab5fdf95c0a897e9d13e130aebb6fa",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_046 — What source supports the S-101 definition of AnchorageArea?

답안 hash: `352c550d1dc17d6e6cc5931c90543f5c3320a18876b011bafab736b742db1c6e`

### 실제 최종 답안
```json
{
  "answer_text": "The S-101 definition of AnchorageArea is supported by the source 's101_feature_catalogue_v2'.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "document_answer": {
    "features": [
      {
        "code": "AnchorageArea",
        "xml_type": "S100_FC_FeatureType",
        "definition": "An area in which vessels or seaplanes anchor or may anchor.",
        "permitted_primitives": [
          "point",
          "surface"
        ],
        "bindings": [
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "categoryOfAnchorage"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [
              "1",
              "2",
              "3",
              "5",
              "6",
              "7",
              "9",
              "10",
              "14",
              "15"
            ],
            "xml_child_index": 5
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "categoryOfCargo"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [
              "1",
              "2",
              "3",
              "4",
              "5",
              "6",
              "7",
              "8",
              "9",
              "10",
              "11",
              "12",
              "13",
              "14",
              "15"
            ],
            "xml_child_index": 6
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "featureName"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [],
            "xml_child_index": 7
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "fixedDateRange"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 8
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "interoperabilityIdentifier"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 9
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "periodicDateRange"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [],
            "xml_child_index": 10
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "restriction"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [
              "2",
              "3",
              "4",
              "5",
              "6",
              "8",
              "9",
              "10",
              "11",
              "12",
              "13",
              "15",
              "16",
              "17",
              "18",
              "19",
              "20",
              "21",
              "23",
              "24",
              "27",
              "39"
            ],
            "xml_child_index": 11
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "status"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [
              "1",
              "2",
              "3",
              "5",
              "6",
              "7",
              "8",
              "9",
              "14"
            ],
            "xml_child_index": 12
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "vesselSpeedLimit"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [],
            "xml_child_index": 13
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "scaleMinimum"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 14
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "information"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [],
            "xml_child_index": 15
          },
          {
            "kind": "informationBinding",
            "references": [
              {
                "type": "association",
                "ref": "AdditionalInformation"
              },
              {
                "type": "role",
                "ref": "theInformation"
              },
              {
                "type": "informationType",
                "ref": "ContactDetails"
              },
              {
                "type": "informationType",
                "ref": "NauticalInformation"
              },
              {
                "type": "informationType",
                "ref": "NonStandardWorkingDay"
              },
              {
                "type": "informationType",
                "ref": "ServiceHours"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 16
          },
          {
            "kind": "featureBinding",
            "references": [
              {
                "type": "association",
                "ref": "UpdatedInformation"
              },
              {
                "type": "role",
                "ref": "theUpdate"
              },
              {
                "type": "featureType",
                "ref": "UpdateInformation"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [],
            "xml_child_index": 18
          },
          {
            "kind": "featureBinding",
            "references": [
              {
                "type": "association",
                "ref": "TextAssociation"
              },
              {
                "type": "role",
                "ref": "theCartographicText"
              },
              {
                "type": "featureType",
                "ref": "TextPlacement"
              }
            ],
            "lower": "0",
            "upper": "2",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 19
          }
        ],
        "listed_values": [],
        "version": "2.0.0",
        "source_status": "VERIFIED_XML_EXTRACTION",
        "source_path": "D:\\An_GeoLLM\\outputs\\staging\\s101_feature_catalogue_2_0_0\\S-101\\CATALOGUES\\101_Feature_Catalogue_2.0.0.xml",
        "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "parsed_locator": "/features/126",
        "definition_sha256": "753f012b09c246632a2119c4bbb9faa77ccf966debb2b48d33c26b5c72799a31",
        "xml_element_serialized_sha256": "39334abca32051a75717cd5a450f95388705644972727ac611e4cec8eb1fae9d",
        "element_hash_serialization": "xml.etree.ElementTree serialization; not a raw byte slice"
      }
    ],
    "attribute_bindings": [
      {
        "owner": "AnchorageArea",
        "attribute": "categoryOfAnchorage",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [
          "1",
          "2",
          "3",
          "5",
          "6",
          "7",
          "9",
          "10",
          "14",
          "15"
        ],
        "attribute_definition": "Classification of an area where different use types of vessel can remain static.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Unrestricted Anchorage",
            "definition": "An area in which vessels anchor or may anchor."
          },
          {
            "value": "2",
            "label": "Deep Water Anchorage",
            "definition": "An area in which vessels of deep draught anchor or may anchor."
          },
          {
            "value": "3",
            "label": "Tanker Anchorage",
            "definition": "An area in which tankers anchor or may anchor."
          },
          {
            "value": "5",
            "label": "Quarantine Anchorage",
            "definition": "An area where a vessel anchors when satisfying quarantine regulations."
          },
          {
            "value": "6",
            "label": "Seaplane Anchorage",
            "definition": "An area in which seaplanes anchor or may anchor."
          },
          {
            "value": "7",
            "label": "Small Craft Anchorage",
            "definition": "An area in which yachts and small boats anchor or may anchor."
          },
          {
            "value": "9",
            "label": "Anchorage for Periods Up To 24 Hours",
            "definition": "An area in which vessels anchor or may anchor for periods of up to 24 hours."
          },
          {
            "value": "10",
            "label": "Anchorage for a Limited Period of Time",
            "definition": "An area in which vessels may anchor for a period of time not to exceed a specific limit."
          },
          {
            "value": "14",
            "label": "Waiting Anchorage",
            "definition": "An area in which vessels anchor or may anchor while waiting, for example, for access to a port or berth."
          },
          {
            "value": "15",
            "label": "Reported Anchorage",
            "definition": "A location not defined by a regulatory authority that has been reported to be suitable and safe for anchoring."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='categoryOfAnchorage']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "categoryOfCargo",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [
          "1",
          "2",
          "3",
          "4",
          "5",
          "6",
          "7",
          "8",
          "9",
          "10",
          "11",
          "12",
          "13",
          "14",
          "15"
        ],
        "attribute_definition": "Classification of the different types of cargo that a ship may be carrying.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Bulk",
            "definition": "Unpacked homogenous cargo poured loose in a certain space of a vessel, for example oil or grain."
          },
          {
            "value": "2",
            "label": "Container",
            "definition": "One of a number of standard sized cargo carrying units, secured using standard corner attachments and bar."
          },
          {
            "value": "3",
            "label": "General",
            "definition": "Break bulk cargo normally loaded by crane."
          },
          {
            "value": "4",
            "label": "Liquid",
            "definition": "Any cargo loaded by pipeline."
          },
          {
            "value": "5",
            "label": "Passenger",
            "definition": "A fee paying traveller."
          },
          {
            "value": "6",
            "label": "Livestock",
            "definition": "Live animals carried in bulk."
          },
          {
            "value": "7",
            "label": "Dangerous or Hazardous",
            "definition": "Dangerous or hazardous cargo as described by the IMO International Maritime Dangerous Goods code."
          },
          {
            "value": "8",
            "label": "Heavy Lift",
            "definition": "Indivisible heavy items of weight generally over 100 tons, and width or height greater than 100 metres."
          },
          {
            "value": "9",
            "label": "Ballast",
            "definition": "Material carried by a ship to ensure its stability."
          },
          {
            "value": "10",
            "label": "Dry Bulk Cargo",
            "definition": "Commodity cargo that is transported unpackaged in large quantities. These types of goods usually need to be kept dry during the whole transportation period."
          },
          {
            "value": "11",
            "label": "Liquid Bulk Cargo",
            "definition": "Liquids or gases that are transported in bulk and carried unpackaged."
          },
          {
            "value": "12",
            "label": "Reefer Container Cargo",
            "definition": "Cargo transported in refrigerated containers, generally perishable commodities which require temperature-controlled transportation, such as fruit, meat, fish, vegetables, dairy products and other foods."
          },
          {
            "value": "13",
            "label": "Ro-Ro Cargo",
            "definition": "Wheeled cargo, such as cars, busses, trucks, agricultural vehicles and cranes, that are driven on and off the ship on their own wheels or using a platform vehicle, such as a self-propelled modular transporter."
          },
          {
            "value": "14",
            "label": "Project Cargo",
            "definition": "Project cargo is a term used to broadly describe the national or international transportation of large, heavy, high value, or critical (to the project they are intended for) pieces of equipment. Also commonly referred to as heavy lift, this includes shipments made of various components which need disassembly for shipment and reassembly after delivery."
          },
          {
            "value": "15",
            "label": "Break Bulk Cargo",
            "definition": "Goods that are stowed on board ship in individually counted units, and not in intermodal containers nor in bulk as with oil or grain."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='categoryOfCargo']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "featureName",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [],
        "attribute_definition": "Provides the name of an entity, defines the national language of the name, and provides the option to display the name at various system display settings.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='featureName']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "fixedDateRange",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "An active period of a single fixed event or occurrence, as the date range between discrete start and end dates.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='fixedDateRange']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "interoperabilityIdentifier",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "A common unique identifier for entities which describe a single real-world feature, and which is used to identify instances of the feature in end-user systems where the feature may be included in multiple data product types.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='interoperabilityIdentifier']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "periodicDateRange",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [],
        "attribute_definition": "The active period of a recurring event or occurrence.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='periodicDateRange']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "restriction",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [
          "2",
          "3",
          "4",
          "5",
          "6",
          "8",
          "9",
          "10",
          "11",
          "12",
          "13",
          "15",
          "16",
          "17",
          "18",
          "19",
          "20",
          "21",
          "23",
          "24",
          "27",
          "39"
        ],
        "attribute_definition": "The official legal statute of each kind of restricted area.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Anchoring Prohibited",
            "definition": "An area within which anchoring is not permitted."
          },
          {
            "value": "2",
            "label": "Anchoring Restricted",
            "definition": "A specified area designated by appropriate authority, within which anchoring is restricted in accordance with certain specified conditions."
          },
          {
            "value": "3",
            "label": "Fishing Prohibited",
            "definition": "An area within which fishing is not permitted."
          },
          {
            "value": "4",
            "label": "Fishing Restricted",
            "definition": "A specified area designated by appropriate authority, within which fishing is restricted in accordance with certain specified conditions."
          },
          {
            "value": "5",
            "label": "Trawling Prohibited",
            "definition": "An area within which trawling is not permitted."
          },
          {
            "value": "6",
            "label": "Trawling Restricted",
            "definition": "A specified area designated by appropriate authority, within which trawling is restricted in accordance with certain specified conditions."
          },
          {
            "value": "7",
            "label": "Entry Prohibited",
            "definition": "An area within which navigation and/or anchoring is prohibited."
          },
          {
            "value": "8",
            "label": "Entry Restricted",
            "definition": "A specified area designated by appropriate authority, within which navigation is restricted in accordance with certain specified conditions."
          },
          {
            "value": "9",
            "label": "Dredging Prohibited",
            "definition": "An area within which dredging is not permitted."
          },
          {
            "value": "10",
            "label": "Dredging Restricted",
            "definition": "A specified area designated by appropriate authority, within which dredging is restricted in accordance with certain specified conditions."
          },
          {
            "value": "11",
            "label": "Diving Prohibited",
            "definition": "An area within which diving is not permitted."
          },
          {
            "value": "12",
            "label": "Diving Restricted",
            "definition": "A specified area designated by appropriate authority, within which diving is restricted in accordance with certain specified conditions."
          },
          {
            "value": "13",
            "label": "No Wake",
            "definition": "Mariners must adjust the speed of their vessels to reduce the wave or wash which may cause erosion or disturb moored vessels."
          },
          {
            "value": "14",
            "label": "Area To Be Avoided",
            "definition": "An IMO declared routeing measure comprising an area within defined limits in which either navigation is particularly hazardous or it is exceptionally important to avoid casualties and which should be avoided by all ships, or certain classes of ships."
          },
          {
            "value": "15",
            "label": "Construction Prohibited",
            "definition": "The erection of permanent or temporary fixed structures or artificial islands is prohibited."
          },
          {
            "value": "16",
            "label": "Discharging Prohibited",
            "definition": "An area within which discharging or dumping is prohibited."
          },
          {
            "value": "17",
            "label": "Discharging Restricted",
            "definition": "A specified area designated by an appropriate authority, within which discharging or dumping is restricted in accordance with specified conditions."
          },
          {
            "value": "18",
            "label": "Industrial or Mineral Exploration/Development Prohibited",
            "definition": "An area within which industrial or mineral exploration and development are prohibited."
          },
          {
            "value": "19",
            "label": "Industrial or Mineral Exploration/Development Restricted",
            "definition": "A specified area designated by an appropriate authority, within which industrial or mineral exploration and development is restricted in accordance with certain specified conditions."
          },
          {
            "value": "20",
            "label": "Drilling Prohibited",
            "definition": "An area within which excavating a hole on the seabed with a drill is prohibited."
          },
          {
            "value": "21",
            "label": "Drilling Restricted",
            "definition": "A specified area designated by an appropriate authority, within which excavating a hole on the seabed with a drill is restricted in accordance with certain specified conditions."
          },
          {
            "value": "22",
            "label": "Removal of Historical Artefacts Prohibited",
            "definition": "An area within which the removal of historical artefacts is prohibited."
          },
          {
            "value": "23",
            "label": "Cargo Transhipment (Lightening) Prohibited",
            "definition": "An area in which cargo transhipment (lightening) is prohibited."
          },
          {
            "value": "24",
            "label": "Dragging Prohibited",
            "definition": "An area in which the dragging of anything along the seabed, for example bottom trawling, is prohibited."
          },
          {
            "value": "25",
            "label": "Stopping Prohibited",
            "definition": "An area in which a vessel is prohibited from stopping."
          },
          {
            "value": "26",
            "label": "Landing Prohibited",
            "definition": "An area in which landing is prohibited."
          },
          {
            "value": "27",
            "label": "Speed Restricted",
            "definition": "An area within which speed is restricted."
          },
          {
            "value": "39",
            "label": "Swimming Prohibited",
            "definition": "An area in which swimming is prohibited."
          },
          {
            "value": "42",
            "label": "Power-Driven Vessels Prohibited",
            "definition": "An area within which any vessel propelled by machinery is prohibited."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='restriction']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "status",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [
          "1",
          "2",
          "3",
          "5",
          "6",
          "7",
          "8",
          "9",
          "14"
        ],
        "attribute_definition": "The condition of an object at a given instant in time.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Permanent",
            "definition": "Intended to last or function indefinitely."
          },
          {
            "value": "2",
            "label": "Occasional",
            "definition": "Acting on special occasions; happening irregularly."
          },
          {
            "value": "3",
            "label": "Recommended",
            "definition": "Presented as worthy of confidence, acceptance, use, etc."
          },
          {
            "value": "4",
            "label": "Not in Use",
            "definition": "Use has ceased, but the facility still exists intact; disused."
          },
          {
            "value": "5",
            "label": "Periodic/Intermittent",
            "definition": "Recurring at intervals."
          },
          {
            "value": "6",
            "label": "Reserved",
            "definition": "Set apart for some specific use."
          },
          {
            "value": "7",
            "label": "Temporary",
            "definition": "Meant to last only for a time."
          },
          {
            "value": "8",
            "label": "Private",
            "definition": "Administered by an individual or corporation, rather than a State or a public body."
          },
          {
            "value": "9",
            "label": "Mandatory",
            "definition": "Compulsory; enforced."
          },
          {
            "value": "11",
            "label": "Extinguished",
            "definition": "No longer lit."
          },
          {
            "value": "12",
            "label": "Illuminated",
            "definition": "Lit by flood lights, strip lights, etc."
          },
          {
            "value": "13",
            "label": "Historic",
            "definition": "Famous in history; of historical interest."
          },
          {
            "value": "14",
            "label": "Public",
            "definition": "Belonging to, available to, used or shared by, the community as a whole and not restricted to private use."
          },
          {
            "value": "15",
            "label": "Synchronized",
            "definition": "Occur at a time, coincide in point of time, be contemporary or simultaneous."
          },
          {
            "value": "16",
            "label": "Watched",
            "definition": "Looked at or observed over a period of time especially so as to be aware of any movement or change."
          },
          {
            "value": "17",
            "label": "Unwatched",
            "definition": "Usually automatic in operation, without any permanently-stationed personnel to superintend it."
          },
          {
            "value": "18",
            "label": "Existence Doubtful",
            "definition": "A feature that has been reported but has not been definitely determined to exist."
          },
          {
            "value": "28",
            "label": "Buoyed",
            "definition": "Marked by buoys."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='status']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "vesselSpeedLimit",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [],
        "attribute_definition": "The maximum allowed rate of travel for a vessel in an area in knots.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='vesselSpeedLimit']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "scaleMinimum",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The minimum scale at which the feature may be used for example for ECDIS presentation.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='scaleMinimum']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "information",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [],
        "attribute_definition": "Textual information about the feature. The information may be provided as a string of text or as a file name of a single external text file that contains the text.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]"
      },
      {
        "owner": "featureName",
        "attribute": "language",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The method of human communication, either spoken or written, consisting of the use of words in a structured and conventional way.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='featureName']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='language']]"
      },
      {
        "owner": "featureName",
        "attribute": "name",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The individual name of a feature.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='featureName']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='name']]"
      },
      {
        "owner": "featureName",
        "attribute": "nameUsage",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [
          "1",
          "2"
        ],
        "attribute_definition": "Classification of the type and display level of the name of a feature in an end-user system.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Default Name Display",
            "definition": "The name is intended to be displayed when the end-user system is set to the default name/text display setting."
          },
          {
            "value": "2",
            "label": "Alternate Name Display",
            "definition": "The name is intended to be displayed when the end-user system is set to an alternate name/text display setting, for example an alternate language."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='featureName']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='nameUsage']]"
      },
      {
        "owner": "fixedDateRange",
        "attribute": "dateEnd",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The latest date on which an object (for example a buoy) will be present.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='fixedDateRange']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='dateEnd']]"
      },
      {
        "owner": "fixedDateRange",
        "attribute": "dateStart",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The earliest date on which an object (for example a buoy) will be present.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='fixedDateRange']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='dateStart']]"
      },
      {
        "owner": "periodicDateRange",
        "attribute": "dateEnd",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The latest date on which an object (for example a buoy) will be present.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='periodicDateRange']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='dateEnd']]"
      },
      {
        "owner": "periodicDateRange",
        "attribute": "dateStart",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The earliest date on which an object (for example a buoy) will be present.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='periodicDateRange']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='dateStart']]"
      },
      {
        "owner": "vesselSpeedLimit",
        "attribute": "speedLimit",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The maximum allowed rate of travel in an area.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='vesselSpeedLimit']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='speedLimit']]"
      },
      {
        "owner": "vesselSpeedLimit",
        "attribute": "speedUnits",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [
          "2",
          "3",
          "4"
        ],
        "attribute_definition": "The units for description of speed.",
        "global_listed_values": [
          {
            "value": "2",
            "label": "Kilometres Per Hour",
            "definition": "A unit of speed, expressing the number of kilometres travelled in one hour."
          },
          {
            "value": "3",
            "label": "Miles Per Hour",
            "definition": "An imperial and United States customary unit of speed expressing the number of statute miles covered in one hour."
          },
          {
            "value": "4",
            "label": "Knots",
            "definition": "A nautical unit of speed. One knot is one nautical mile per hour. The name is derived from the knots in the log line."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='vesselSpeedLimit']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='speedUnits']]"
      },
      {
        "owner": "vesselSpeedLimit",
        "attribute": "vesselClass",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The classification of a vessel, normally as defined by length or gross tonnage.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='vesselSpeedLimit']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='vesselClass']]"
      },
      {
        "owner": "information",
        "attribute": "fileLocator",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The location of a fragment of text or other information in a support file.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='fileLocator']]"
      },
      {
        "owner": "information",
        "attribute": "fileReference",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The file name of an externally referenced text file.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='fileReference']]"
      },
      {
        "owner": "information",
        "attribute": "headline",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "Words set at the head of a passage or page to introduce or categorize.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='headline']]"
      },
      {
        "owner": "information",
        "attribute": "language",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The method of human communication, either spoken or written, consisting of the use of words in a structured and conventional way.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='language']]"
      },
      {
        "owner": "information",
        "attribute": "text",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "A non-formatted digital text string.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='text']]"
      }
    ],
    "evidence": {
      "edition": "2.0.0",
      "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
      "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
      "locators": [
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]"
      ],
      "claim_source_links": [
        {
          "feature_code": "AnchorageArea",
          "definition_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
          "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc"
        }
      ]
    },
    "definition_quote": "An area in which vessels or seaplanes anchor or may anchor."
  },
  "status": "COMPLETED",
  "execution_status": "COMPLETED",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q6_03.json)
```json
{
  "case_id": "PILOT_Q6_03",
  "required_task_obligations": [
    "provide_anchorage_definition_source",
    "cite_catalogue_edition_and_locator"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_046",
  "answer_sha256": "352c550d1dc17d6e6cc5931c90543f5c3320a18876b011bafab736b742db1c6e",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "020949eb3c39c887d7f25f93595a3eff135e766e70e54dcee96f1ec78f5ecf34",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_045 — 독도 주변 5km의 등대와 난파선을 찾아 각각의 근거를 알려줘.

답안 hash: `f960e26b7fe3ffffbb31295d6ada4e65557c1a2caaa44cf6cf383b7189dd4587`

### 실제 최종 답안
```json
{
  "answer_text": "The beacon and anchor line around Dokdo have been found. The beacon is located at 128.9, 34.9, and the anchor line is located at 129.3, 35.3.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "document_answers": [
    {
      "features": [],
      "attribute_bindings": [],
      "evidence": {
        "edition": "2.0.0",
        "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
        "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
        "locators": [],
        "claim_source_links": []
      }
    },
    {
      "features": [],
      "attribute_bindings": [],
      "evidence": {
        "edition": "2.0.0",
        "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
        "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
        "locators": [],
        "claim_source_links": []
      }
    }
  ],
  "status": "COMPLETED",
  "execution_status": "COMPLETED",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q5_01.json)
```json
{
  "case_id": "PILOT_Q5_01",
  "required_task_obligations": [
    "resolve_reference",
    "resolve_lighthouse_target_conditions",
    "verify_both_target_coverages",
    "search_both_targets_5000m",
    "provide_per_target_evidence",
    "separate_partial_document_answer"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "User-approved source-bound safe abstention; document explanations are separately evaluated optional partial output."
  ],
  "expected_spatial_behavior": {
    "accepted_states": [
      "BLOCKED_DATA",
      "DATA_OUT_OF_SCOPE"
    ],
    "required_disclosure": "Current connected snapshot cannot determine the answer for the requested spatial extent",
    "per_target": {
      "Lighthouse": {
        "status": "BLOCKED_DATA",
        "object_ids": null
      },
      "Wreck": {
        "status": "BLOCKED_DATA",
        "object_ids": null
      }
    },
    "empty_result_as_answer_forbidden": true,
    "claim_spatial_success_forbidden": true
  }
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_045",
  "answer_sha256": "f960e26b7fe3ffffbb31295d6ada4e65557c1a2caaa44cf6cf383b7189dd4587",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "a263ccd959d0a5a79e63faf202994388a84053fd232f24ba60bc3b0aa3b6cc37",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_044 — 독도 주변 5km의 등대와 난파선을 찾아 각각의 근거를 알려줘.

답안 hash: `d078607fab92a5636acc78b67c0a8f6b2d25cacc230c7f40f6a72f976d703523`

### 실제 최종 답안
```json
{
  "answer_text": "The beacon and anchor line around Dokdo have been found. The beacon is located at 128.9, 34.9, and the anchor line is located at 129.3, 35.3.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "validator_blockers": [
    "BLOCKED_DATA: public catalogue document evidence unavailable",
    "BLOCKED_DATA: public catalogue document evidence unavailable"
  ],
  "status": "BLOCKED_DATA",
  "execution_status": "BLOCKED_DATA",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q5_01.json)
```json
{
  "case_id": "PILOT_Q5_01",
  "required_task_obligations": [
    "resolve_reference",
    "resolve_lighthouse_target_conditions",
    "verify_both_target_coverages",
    "search_both_targets_5000m",
    "provide_per_target_evidence",
    "separate_partial_document_answer"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "User-approved source-bound safe abstention; document explanations are separately evaluated optional partial output."
  ],
  "expected_spatial_behavior": {
    "accepted_states": [
      "BLOCKED_DATA",
      "DATA_OUT_OF_SCOPE"
    ],
    "required_disclosure": "Current connected snapshot cannot determine the answer for the requested spatial extent",
    "per_target": {
      "Lighthouse": {
        "status": "BLOCKED_DATA",
        "object_ids": null
      },
      "Wreck": {
        "status": "BLOCKED_DATA",
        "object_ids": null
      }
    },
    "empty_result_as_answer_forbidden": true,
    "claim_spatial_success_forbidden": true
  }
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_044",
  "answer_sha256": "d078607fab92a5636acc78b67c0a8f6b2d25cacc230c7f40f6a72f976d703523",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "33249af9f19fdc6dea59395a7c3a9a852356980b5ee1bc19b5f4f5aeeedc0c83",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_043 — What source supports the S-101 definition of AnchorageArea?

답안 hash: `9406fe8c22076c97041c2a5b8ec50d3d39934ebebacf0c4a92af42107a4c250d`

### 실제 최종 답안
```json
{
  "answer_text": "The S-101 definition of AnchorageArea is supported by the source 's101_feature_catalogue_v2'.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "document_answer": {
    "features": [
      {
        "code": "AnchorageArea",
        "xml_type": "S100_FC_FeatureType",
        "definition": "An area in which vessels or seaplanes anchor or may anchor.",
        "permitted_primitives": [
          "point",
          "surface"
        ],
        "bindings": [
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "categoryOfAnchorage"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [
              "1",
              "2",
              "3",
              "5",
              "6",
              "7",
              "9",
              "10",
              "14",
              "15"
            ],
            "xml_child_index": 5
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "categoryOfCargo"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [
              "1",
              "2",
              "3",
              "4",
              "5",
              "6",
              "7",
              "8",
              "9",
              "10",
              "11",
              "12",
              "13",
              "14",
              "15"
            ],
            "xml_child_index": 6
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "featureName"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [],
            "xml_child_index": 7
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "fixedDateRange"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 8
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "interoperabilityIdentifier"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 9
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "periodicDateRange"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [],
            "xml_child_index": 10
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "restriction"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [
              "2",
              "3",
              "4",
              "5",
              "6",
              "8",
              "9",
              "10",
              "11",
              "12",
              "13",
              "15",
              "16",
              "17",
              "18",
              "19",
              "20",
              "21",
              "23",
              "24",
              "27",
              "39"
            ],
            "xml_child_index": 11
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "status"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [
              "1",
              "2",
              "3",
              "5",
              "6",
              "7",
              "8",
              "9",
              "14"
            ],
            "xml_child_index": 12
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "vesselSpeedLimit"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [],
            "xml_child_index": 13
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "scaleMinimum"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 14
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "information"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [],
            "xml_child_index": 15
          },
          {
            "kind": "informationBinding",
            "references": [
              {
                "type": "association",
                "ref": "AdditionalInformation"
              },
              {
                "type": "role",
                "ref": "theInformation"
              },
              {
                "type": "informationType",
                "ref": "ContactDetails"
              },
              {
                "type": "informationType",
                "ref": "NauticalInformation"
              },
              {
                "type": "informationType",
                "ref": "NonStandardWorkingDay"
              },
              {
                "type": "informationType",
                "ref": "ServiceHours"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 16
          },
          {
            "kind": "featureBinding",
            "references": [
              {
                "type": "association",
                "ref": "UpdatedInformation"
              },
              {
                "type": "role",
                "ref": "theUpdate"
              },
              {
                "type": "featureType",
                "ref": "UpdateInformation"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [],
            "xml_child_index": 18
          },
          {
            "kind": "featureBinding",
            "references": [
              {
                "type": "association",
                "ref": "TextAssociation"
              },
              {
                "type": "role",
                "ref": "theCartographicText"
              },
              {
                "type": "featureType",
                "ref": "TextPlacement"
              }
            ],
            "lower": "0",
            "upper": "2",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 19
          }
        ],
        "listed_values": [],
        "version": "2.0.0",
        "source_status": "VERIFIED_XML_EXTRACTION",
        "source_path": "D:\\An_GeoLLM\\outputs\\staging\\s101_feature_catalogue_2_0_0\\S-101\\CATALOGUES\\101_Feature_Catalogue_2.0.0.xml",
        "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "parsed_locator": "/features/126",
        "definition_sha256": "753f012b09c246632a2119c4bbb9faa77ccf966debb2b48d33c26b5c72799a31",
        "xml_element_serialized_sha256": "39334abca32051a75717cd5a450f95388705644972727ac611e4cec8eb1fae9d",
        "element_hash_serialization": "xml.etree.ElementTree serialization; not a raw byte slice"
      }
    ],
    "attribute_bindings": [
      {
        "owner": "AnchorageArea",
        "attribute": "categoryOfAnchorage",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [
          "1",
          "2",
          "3",
          "5",
          "6",
          "7",
          "9",
          "10",
          "14",
          "15"
        ],
        "attribute_definition": "Classification of an area where different use types of vessel can remain static.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Unrestricted Anchorage",
            "definition": "An area in which vessels anchor or may anchor."
          },
          {
            "value": "2",
            "label": "Deep Water Anchorage",
            "definition": "An area in which vessels of deep draught anchor or may anchor."
          },
          {
            "value": "3",
            "label": "Tanker Anchorage",
            "definition": "An area in which tankers anchor or may anchor."
          },
          {
            "value": "5",
            "label": "Quarantine Anchorage",
            "definition": "An area where a vessel anchors when satisfying quarantine regulations."
          },
          {
            "value": "6",
            "label": "Seaplane Anchorage",
            "definition": "An area in which seaplanes anchor or may anchor."
          },
          {
            "value": "7",
            "label": "Small Craft Anchorage",
            "definition": "An area in which yachts and small boats anchor or may anchor."
          },
          {
            "value": "9",
            "label": "Anchorage for Periods Up To 24 Hours",
            "definition": "An area in which vessels anchor or may anchor for periods of up to 24 hours."
          },
          {
            "value": "10",
            "label": "Anchorage for a Limited Period of Time",
            "definition": "An area in which vessels may anchor for a period of time not to exceed a specific limit."
          },
          {
            "value": "14",
            "label": "Waiting Anchorage",
            "definition": "An area in which vessels anchor or may anchor while waiting, for example, for access to a port or berth."
          },
          {
            "value": "15",
            "label": "Reported Anchorage",
            "definition": "A location not defined by a regulatory authority that has been reported to be suitable and safe for anchoring."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='categoryOfAnchorage']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "categoryOfCargo",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [
          "1",
          "2",
          "3",
          "4",
          "5",
          "6",
          "7",
          "8",
          "9",
          "10",
          "11",
          "12",
          "13",
          "14",
          "15"
        ],
        "attribute_definition": "Classification of the different types of cargo that a ship may be carrying.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Bulk",
            "definition": "Unpacked homogenous cargo poured loose in a certain space of a vessel, for example oil or grain."
          },
          {
            "value": "2",
            "label": "Container",
            "definition": "One of a number of standard sized cargo carrying units, secured using standard corner attachments and bar."
          },
          {
            "value": "3",
            "label": "General",
            "definition": "Break bulk cargo normally loaded by crane."
          },
          {
            "value": "4",
            "label": "Liquid",
            "definition": "Any cargo loaded by pipeline."
          },
          {
            "value": "5",
            "label": "Passenger",
            "definition": "A fee paying traveller."
          },
          {
            "value": "6",
            "label": "Livestock",
            "definition": "Live animals carried in bulk."
          },
          {
            "value": "7",
            "label": "Dangerous or Hazardous",
            "definition": "Dangerous or hazardous cargo as described by the IMO International Maritime Dangerous Goods code."
          },
          {
            "value": "8",
            "label": "Heavy Lift",
            "definition": "Indivisible heavy items of weight generally over 100 tons, and width or height greater than 100 metres."
          },
          {
            "value": "9",
            "label": "Ballast",
            "definition": "Material carried by a ship to ensure its stability."
          },
          {
            "value": "10",
            "label": "Dry Bulk Cargo",
            "definition": "Commodity cargo that is transported unpackaged in large quantities. These types of goods usually need to be kept dry during the whole transportation period."
          },
          {
            "value": "11",
            "label": "Liquid Bulk Cargo",
            "definition": "Liquids or gases that are transported in bulk and carried unpackaged."
          },
          {
            "value": "12",
            "label": "Reefer Container Cargo",
            "definition": "Cargo transported in refrigerated containers, generally perishable commodities which require temperature-controlled transportation, such as fruit, meat, fish, vegetables, dairy products and other foods."
          },
          {
            "value": "13",
            "label": "Ro-Ro Cargo",
            "definition": "Wheeled cargo, such as cars, busses, trucks, agricultural vehicles and cranes, that are driven on and off the ship on their own wheels or using a platform vehicle, such as a self-propelled modular transporter."
          },
          {
            "value": "14",
            "label": "Project Cargo",
            "definition": "Project cargo is a term used to broadly describe the national or international transportation of large, heavy, high value, or critical (to the project they are intended for) pieces of equipment. Also commonly referred to as heavy lift, this includes shipments made of various components which need disassembly for shipment and reassembly after delivery."
          },
          {
            "value": "15",
            "label": "Break Bulk Cargo",
            "definition": "Goods that are stowed on board ship in individually counted units, and not in intermodal containers nor in bulk as with oil or grain."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='categoryOfCargo']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "featureName",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [],
        "attribute_definition": "Provides the name of an entity, defines the national language of the name, and provides the option to display the name at various system display settings.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='featureName']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "fixedDateRange",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "An active period of a single fixed event or occurrence, as the date range between discrete start and end dates.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='fixedDateRange']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "interoperabilityIdentifier",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "A common unique identifier for entities which describe a single real-world feature, and which is used to identify instances of the feature in end-user systems where the feature may be included in multiple data product types.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='interoperabilityIdentifier']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "periodicDateRange",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [],
        "attribute_definition": "The active period of a recurring event or occurrence.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='periodicDateRange']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "restriction",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [
          "2",
          "3",
          "4",
          "5",
          "6",
          "8",
          "9",
          "10",
          "11",
          "12",
          "13",
          "15",
          "16",
          "17",
          "18",
          "19",
          "20",
          "21",
          "23",
          "24",
          "27",
          "39"
        ],
        "attribute_definition": "The official legal statute of each kind of restricted area.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Anchoring Prohibited",
            "definition": "An area within which anchoring is not permitted."
          },
          {
            "value": "2",
            "label": "Anchoring Restricted",
            "definition": "A specified area designated by appropriate authority, within which anchoring is restricted in accordance with certain specified conditions."
          },
          {
            "value": "3",
            "label": "Fishing Prohibited",
            "definition": "An area within which fishing is not permitted."
          },
          {
            "value": "4",
            "label": "Fishing Restricted",
            "definition": "A specified area designated by appropriate authority, within which fishing is restricted in accordance with certain specified conditions."
          },
          {
            "value": "5",
            "label": "Trawling Prohibited",
            "definition": "An area within which trawling is not permitted."
          },
          {
            "value": "6",
            "label": "Trawling Restricted",
            "definition": "A specified area designated by appropriate authority, within which trawling is restricted in accordance with certain specified conditions."
          },
          {
            "value": "7",
            "label": "Entry Prohibited",
            "definition": "An area within which navigation and/or anchoring is prohibited."
          },
          {
            "value": "8",
            "label": "Entry Restricted",
            "definition": "A specified area designated by appropriate authority, within which navigation is restricted in accordance with certain specified conditions."
          },
          {
            "value": "9",
            "label": "Dredging Prohibited",
            "definition": "An area within which dredging is not permitted."
          },
          {
            "value": "10",
            "label": "Dredging Restricted",
            "definition": "A specified area designated by appropriate authority, within which dredging is restricted in accordance with certain specified conditions."
          },
          {
            "value": "11",
            "label": "Diving Prohibited",
            "definition": "An area within which diving is not permitted."
          },
          {
            "value": "12",
            "label": "Diving Restricted",
            "definition": "A specified area designated by appropriate authority, within which diving is restricted in accordance with certain specified conditions."
          },
          {
            "value": "13",
            "label": "No Wake",
            "definition": "Mariners must adjust the speed of their vessels to reduce the wave or wash which may cause erosion or disturb moored vessels."
          },
          {
            "value": "14",
            "label": "Area To Be Avoided",
            "definition": "An IMO declared routeing measure comprising an area within defined limits in which either navigation is particularly hazardous or it is exceptionally important to avoid casualties and which should be avoided by all ships, or certain classes of ships."
          },
          {
            "value": "15",
            "label": "Construction Prohibited",
            "definition": "The erection of permanent or temporary fixed structures or artificial islands is prohibited."
          },
          {
            "value": "16",
            "label": "Discharging Prohibited",
            "definition": "An area within which discharging or dumping is prohibited."
          },
          {
            "value": "17",
            "label": "Discharging Restricted",
            "definition": "A specified area designated by an appropriate authority, within which discharging or dumping is restricted in accordance with specified conditions."
          },
          {
            "value": "18",
            "label": "Industrial or Mineral Exploration/Development Prohibited",
            "definition": "An area within which industrial or mineral exploration and development are prohibited."
          },
          {
            "value": "19",
            "label": "Industrial or Mineral Exploration/Development Restricted",
            "definition": "A specified area designated by an appropriate authority, within which industrial or mineral exploration and development is restricted in accordance with certain specified conditions."
          },
          {
            "value": "20",
            "label": "Drilling Prohibited",
            "definition": "An area within which excavating a hole on the seabed with a drill is prohibited."
          },
          {
            "value": "21",
            "label": "Drilling Restricted",
            "definition": "A specified area designated by an appropriate authority, within which excavating a hole on the seabed with a drill is restricted in accordance with certain specified conditions."
          },
          {
            "value": "22",
            "label": "Removal of Historical Artefacts Prohibited",
            "definition": "An area within which the removal of historical artefacts is prohibited."
          },
          {
            "value": "23",
            "label": "Cargo Transhipment (Lightening) Prohibited",
            "definition": "An area in which cargo transhipment (lightening) is prohibited."
          },
          {
            "value": "24",
            "label": "Dragging Prohibited",
            "definition": "An area in which the dragging of anything along the seabed, for example bottom trawling, is prohibited."
          },
          {
            "value": "25",
            "label": "Stopping Prohibited",
            "definition": "An area in which a vessel is prohibited from stopping."
          },
          {
            "value": "26",
            "label": "Landing Prohibited",
            "definition": "An area in which landing is prohibited."
          },
          {
            "value": "27",
            "label": "Speed Restricted",
            "definition": "An area within which speed is restricted."
          },
          {
            "value": "39",
            "label": "Swimming Prohibited",
            "definition": "An area in which swimming is prohibited."
          },
          {
            "value": "42",
            "label": "Power-Driven Vessels Prohibited",
            "definition": "An area within which any vessel propelled by machinery is prohibited."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='restriction']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "status",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [
          "1",
          "2",
          "3",
          "5",
          "6",
          "7",
          "8",
          "9",
          "14"
        ],
        "attribute_definition": "The condition of an object at a given instant in time.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Permanent",
            "definition": "Intended to last or function indefinitely."
          },
          {
            "value": "2",
            "label": "Occasional",
            "definition": "Acting on special occasions; happening irregularly."
          },
          {
            "value": "3",
            "label": "Recommended",
            "definition": "Presented as worthy of confidence, acceptance, use, etc."
          },
          {
            "value": "4",
            "label": "Not in Use",
            "definition": "Use has ceased, but the facility still exists intact; disused."
          },
          {
            "value": "5",
            "label": "Periodic/Intermittent",
            "definition": "Recurring at intervals."
          },
          {
            "value": "6",
            "label": "Reserved",
            "definition": "Set apart for some specific use."
          },
          {
            "value": "7",
            "label": "Temporary",
            "definition": "Meant to last only for a time."
          },
          {
            "value": "8",
            "label": "Private",
            "definition": "Administered by an individual or corporation, rather than a State or a public body."
          },
          {
            "value": "9",
            "label": "Mandatory",
            "definition": "Compulsory; enforced."
          },
          {
            "value": "11",
            "label": "Extinguished",
            "definition": "No longer lit."
          },
          {
            "value": "12",
            "label": "Illuminated",
            "definition": "Lit by flood lights, strip lights, etc."
          },
          {
            "value": "13",
            "label": "Historic",
            "definition": "Famous in history; of historical interest."
          },
          {
            "value": "14",
            "label": "Public",
            "definition": "Belonging to, available to, used or shared by, the community as a whole and not restricted to private use."
          },
          {
            "value": "15",
            "label": "Synchronized",
            "definition": "Occur at a time, coincide in point of time, be contemporary or simultaneous."
          },
          {
            "value": "16",
            "label": "Watched",
            "definition": "Looked at or observed over a period of time especially so as to be aware of any movement or change."
          },
          {
            "value": "17",
            "label": "Unwatched",
            "definition": "Usually automatic in operation, without any permanently-stationed personnel to superintend it."
          },
          {
            "value": "18",
            "label": "Existence Doubtful",
            "definition": "A feature that has been reported but has not been definitely determined to exist."
          },
          {
            "value": "28",
            "label": "Buoyed",
            "definition": "Marked by buoys."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='status']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "vesselSpeedLimit",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [],
        "attribute_definition": "The maximum allowed rate of travel for a vessel in an area in knots.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='vesselSpeedLimit']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "scaleMinimum",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The minimum scale at which the feature may be used for example for ECDIS presentation.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='scaleMinimum']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "information",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [],
        "attribute_definition": "Textual information about the feature. The information may be provided as a string of text or as a file name of a single external text file that contains the text.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]"
      },
      {
        "owner": "featureName",
        "attribute": "language",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The method of human communication, either spoken or written, consisting of the use of words in a structured and conventional way.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='featureName']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='language']]"
      },
      {
        "owner": "featureName",
        "attribute": "name",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The individual name of a feature.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='featureName']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='name']]"
      },
      {
        "owner": "featureName",
        "attribute": "nameUsage",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [
          "1",
          "2"
        ],
        "attribute_definition": "Classification of the type and display level of the name of a feature in an end-user system.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Default Name Display",
            "definition": "The name is intended to be displayed when the end-user system is set to the default name/text display setting."
          },
          {
            "value": "2",
            "label": "Alternate Name Display",
            "definition": "The name is intended to be displayed when the end-user system is set to an alternate name/text display setting, for example an alternate language."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='featureName']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='nameUsage']]"
      },
      {
        "owner": "fixedDateRange",
        "attribute": "dateEnd",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The latest date on which an object (for example a buoy) will be present.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='fixedDateRange']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='dateEnd']]"
      },
      {
        "owner": "fixedDateRange",
        "attribute": "dateStart",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The earliest date on which an object (for example a buoy) will be present.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='fixedDateRange']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='dateStart']]"
      },
      {
        "owner": "periodicDateRange",
        "attribute": "dateEnd",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The latest date on which an object (for example a buoy) will be present.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='periodicDateRange']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='dateEnd']]"
      },
      {
        "owner": "periodicDateRange",
        "attribute": "dateStart",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The earliest date on which an object (for example a buoy) will be present.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='periodicDateRange']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='dateStart']]"
      },
      {
        "owner": "vesselSpeedLimit",
        "attribute": "speedLimit",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The maximum allowed rate of travel in an area.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='vesselSpeedLimit']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='speedLimit']]"
      },
      {
        "owner": "vesselSpeedLimit",
        "attribute": "speedUnits",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [
          "2",
          "3",
          "4"
        ],
        "attribute_definition": "The units for description of speed.",
        "global_listed_values": [
          {
            "value": "2",
            "label": "Kilometres Per Hour",
            "definition": "A unit of speed, expressing the number of kilometres travelled in one hour."
          },
          {
            "value": "3",
            "label": "Miles Per Hour",
            "definition": "An imperial and United States customary unit of speed expressing the number of statute miles covered in one hour."
          },
          {
            "value": "4",
            "label": "Knots",
            "definition": "A nautical unit of speed. One knot is one nautical mile per hour. The name is derived from the knots in the log line."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='vesselSpeedLimit']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='speedUnits']]"
      },
      {
        "owner": "vesselSpeedLimit",
        "attribute": "vesselClass",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The classification of a vessel, normally as defined by length or gross tonnage.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='vesselSpeedLimit']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='vesselClass']]"
      },
      {
        "owner": "information",
        "attribute": "fileLocator",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The location of a fragment of text or other information in a support file.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='fileLocator']]"
      },
      {
        "owner": "information",
        "attribute": "fileReference",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The file name of an externally referenced text file.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='fileReference']]"
      },
      {
        "owner": "information",
        "attribute": "headline",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "Words set at the head of a passage or page to introduce or categorize.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='headline']]"
      },
      {
        "owner": "information",
        "attribute": "language",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The method of human communication, either spoken or written, consisting of the use of words in a structured and conventional way.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='language']]"
      },
      {
        "owner": "information",
        "attribute": "text",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "A non-formatted digital text string.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='text']]"
      }
    ],
    "evidence": {
      "edition": "2.0.0",
      "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
      "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
      "locators": [
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]"
      ],
      "claim_source_links": [
        {
          "feature_code": "AnchorageArea",
          "definition_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
          "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc"
        }
      ]
    },
    "definition_quote": "An area in which vessels or seaplanes anchor or may anchor."
  },
  "status": "COMPLETED",
  "execution_status": "COMPLETED",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q6_03.json)
```json
{
  "case_id": "PILOT_Q6_03",
  "required_task_obligations": [
    "provide_anchorage_definition_source",
    "cite_catalogue_edition_and_locator"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_043",
  "answer_sha256": "9406fe8c22076c97041c2a5b8ec50d3d39934ebebacf0c4a92af42107a4c250d",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "020949eb3c39c887d7f25f93595a3eff135e766e70e54dcee96f1ec78f5ecf34",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_042 — 독도 주변 반경 5km의 해양지명을 찾아줘.

답안 hash: `cf33969e5e0bd569b77d7bcd93b54976b8a7e82c997878db71f2f282571eb50c`

### 실제 최종 답안
```json
{
  "answer_text": "Dokdo 주변 반경 5km의 해양지명은 '독도'입니다.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "validator_blockers": [
    "BLOCKED_DATA: public catalogue document evidence unavailable"
  ],
  "status": "BLOCKED_DATA",
  "execution_status": "BLOCKED_DATA",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q4_01.json)
```json
{
  "case_id": "PILOT_Q4_01",
  "required_task_obligations": [
    "resolve_approved_anchor",
    "search_fixed_gazetteer_5000m",
    "report_source_bound_objects"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_042",
  "answer_sha256": "cf33969e5e0bd569b77d7bcd93b54976b8a7e82c997878db71f2f282571eb50c",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "ed65dafbdfc72a4aac6e2ee1322c0f8cdb7d5812a7792f876a1b5125d4f41b59",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_041 — S-101 Wreck 정의의 원문과 Feature Catalogue 출처를 알려줘.

답안 hash: `a29e548534a5856fbd74562731afeb03dab3599ce7cbb60f38bdf1e0f7e52a2c`

### 실제 최종 답안
```json
{
  "answer_text": "S-101 Wreck은 부산항 연구 기준 항계에 대한 연구 데이터에서 추출된 정보입니다. 이 데이터는 부산항 연구 기준 항계의 범위를 정의하고, 이를 통해 부산항 연구 기준 항계 내의 특정 항목을 설명하는 데 사용됩니다.",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q6_01.json)
```json
{
  "case_id": "PILOT_Q6_01",
  "required_task_obligations": [
    "provide_wreck_definition_text",
    "cite_catalogue_edition_and_locator"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_041",
  "answer_sha256": "a29e548534a5856fbd74562731afeb03dab3599ce7cbb60f38bdf1e0f7e52a2c",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "01f001598f68e0beb8c72fedcd444ecce90685e80b77cbf18b5274275b4df5a0",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_040 — 부산항 영역 안의 정박지를 찾아줘.

답안 hash: `cfe2fb3be6534491be182d7246c3234ec65728b0080c59778e0226036400c9b6`

### 실제 최종 답안
```json
{
  "document_answer": {
    "features": [],
    "attribute_bindings": []
  },
  "search_executed": false,
  "execution_status": "NEEDS_USER_INPUT",
  "source_coverage": {},
  "per_task_status": {},
  "mapping_provenance": {
    "version": "emitted_output_v1",
    "root": "final_state.final_dict",
    "retrieved_text_used_as_answer": false,
    "reference_used_for_mapping": false,
    "structured_document_answer_present": false
  },
  "clarification_request": [
    "여러 위치 또는 기준점 후보가 있습니다. 사용할 위치를 선택해 주세요."
  ],
  "status": "NEEDS_USER_INPUT",
  "blocker": "LOCATION_UNCONFIRMED",
  "answer_text": "여러 위치 또는 기준점 후보가 있습니다. 사용할 위치를 선택해 주세요."
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q3_02.json)
```json
{
  "case_id": "PILOT_Q3_02",
  "required_task_obligations": [
    "resolve_official_port_polygon",
    "verify_coverage",
    "search_within_polygon",
    "report_objects_or_unresolved_reason"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "Object IDs refer to frozen snapshot records, not deduplicated physical facilities or the whole legal port."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_040",
  "answer_sha256": "cfe2fb3be6534491be182d7246c3234ec65728b0080c59778e0226036400c9b6",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "0b06850c85be28ec1855b03883690b793fe9a1655efd0a5e221403c696a903a6",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_039 — 독도 주변 반경 5000m의 해양지명을 찾아줘.

답안 hash: `d8b3cce8c35863a77ab809269c8df19145fc3627306457af58c67ccb8fb6659a`

### 실제 최종 답안
```json
{
  "answer_text": "독도 주변 반경 5000m의 해양지명은 다음과 같습니다:\n1. 독도\n2. 독도 주변의 해양지명들",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q4_02.json)
```json
{
  "case_id": "PILOT_Q4_02",
  "required_task_obligations": [
    "resolve_approved_anchor",
    "search_fixed_gazetteer_5000m",
    "report_source_bound_objects"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_039",
  "answer_sha256": "d8b3cce8c35863a77ab809269c8df19145fc3627306457af58c67ccb8fb6659a",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "012beb5b64d1b21cb91d2ac0c8ebdd5e1750196616b8645e7677ceb4450f7724",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_038 — 독도 주변 반경 5000m의 해양지명을 찾아줘.

답안 hash: `2b89951b2ba03b1c5fb5ed51b1203f0c3999aa060fce9d4cdafa00900c877d2b`

### 실제 최종 답안
```json
{
  "answer_text": "独岛位于韩国济州道的独岛郡，距离济州岛约10公里。",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "document_answer": {
    "features": [],
    "attribute_bindings": [],
    "evidence": {
      "edition": "2.0.0",
      "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
      "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
      "locators": [],
      "claim_source_links": []
    }
  },
  "status": "COMPLETED",
  "execution_status": "COMPLETED",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q4_02.json)
```json
{
  "case_id": "PILOT_Q4_02",
  "required_task_obligations": [
    "resolve_approved_anchor",
    "search_fixed_gazetteer_5000m",
    "report_source_bound_objects"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_038",
  "answer_sha256": "2b89951b2ba03b1c5fb5ed51b1203f0c3999aa060fce9d4cdafa00900c877d2b",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "0ea138088fd41dac4cd15400661d1dd782a7bc64b39aa843fca75534ee622087",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_037 — S-101 Wreck 정의의 원문과 Feature Catalogue 출처를 알려줘.

답안 hash: `8a647e623b2c2e65dd2e94737bece57cc3bbf57e3366fbb99b1d8519f583f22c`

### 실제 최종 답안
```json
{
  "document_answer": {
    "features": [
      {
        "code": "Wreck",
        "definition": "The ruined remains of a stranded or sunken vessel which has been rendered useless.",
        "permitted_primitives": [
          "point",
          "surface"
        ]
      }
    ],
    "attribute_bindings": [
      {
        "owner": "Wreck",
        "attribute": "categoryOfWreck",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "categoryOfWreck",
        "permitted_values": [
          "1",
          "2",
          "3",
          "4",
          "5"
        ],
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "definition": "Classification of a wrecked or ruined ship.",
        "attribute_definition": "Classification of a wrecked or ruined ship.",
        "global_listed_values": [
          {
            "label": "Non-Dangerous Wreck",
            "value": "1"
          },
          {
            "label": "Dangerous Wreck",
            "value": "2"
          },
          {
            "label": "Distributed Remains of Wreck",
            "value": "3"
          },
          {
            "label": "Wreck Showing Mast/Masts",
            "value": "4"
          },
          {
            "label": "Wreck Showing Any Portion of Hull or Superstructure",
            "value": "5"
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='categoryOfWreck']]",
        "listed_values": [
          {
            "label": "Non-Dangerous Wreck",
            "value": "1"
          },
          {
            "label": "Dangerous Wreck",
            "value": "2"
          },
          {
            "label": "Distributed Remains of Wreck",
            "value": "3"
          },
          {
            "label": "Wreck Showing Mast/Masts",
            "value": "4"
          },
          {
            "label": "Wreck Showing Any Portion of Hull or Superstructure",
            "value": "5"
          }
        ],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='categoryOfWreck']]"
      },
      {
        "owner": "Wreck",
        "attribute": "expositionOfSounding",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "expositionOfSounding",
        "permitted_values": [
          "1",
          "2",
          "3"
        ],
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "definition": "Indicates the relationship of the depth of a feature to the range of depth of the surrounding depth area.",
        "attribute_definition": "Indicates the relationship of the depth of a feature to the range of depth of the surrounding depth area.",
        "global_listed_values": [
          {
            "label": "Within the Range of Depth of the Surrounding Depth Area",
            "value": "1"
          },
          {
            "label": "Shoaler Than the Range of Depth of the Surrounding Depth Area",
            "value": "2"
          },
          {
            "label": "Deeper Than the Range of Depth of the Surrounding Depth Area",
            "value": "3"
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='expositionOfSounding']]",
        "listed_values": [
          {
            "label": "Within the Range of Depth of the Surrounding Depth Area",
            "value": "1"
          },
          {
            "label": "Shoaler Than the Range of Depth of the Surrounding Depth Area",
            "value": "2"
          },
          {
            "label": "Deeper Than the Range of Depth of the Surrounding Depth Area",
            "value": "3"
          }
        ],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='expositionOfSounding']]"
      },
      {
        "owner": "Wreck",
        "attribute": "featureName",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "featureName",
        "permitted_values": [],
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "definition": "Provides the name of an entity, defines the national language of the name, and provides the option to display the name at various system display settings.",
        "attribute_definition": "Provides the name of an entity, defines the national language of the name, and provides the option to display the name at various system display settings.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='featureName']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='featureName']]"
      },
      {
        "owner": "Wreck",
        "attribute": "height",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "height",
        "permitted_values": [],
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "definition": "The value of the vertical distance to the highest point of the feature, measured from a specified vertical datum.",
        "attribute_definition": "The value of the vertical distance to the highest point of the feature, measured from a specified vertical datum.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='height']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='height']]"
      },
      {
        "owner": "Wreck",
        "attribute": "interoperabilityIdentifier",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "interoperabilityIdentifier",
        "permitted_values": [],
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "definition": "A common unique identifier for entities which describe a single real-world feature, and which is used to identify instances of the feature in end-user systems where the feature may be included in multiple data product types.",
        "attribute_definition": "A common unique identifier for entities which describe a single real-world feature, and which is used to identify instances of the feature in end-user systems where the feature may be included in multiple data product types.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='interoperabilityIdentifier']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='interoperabilityIdentifier']]"
      },
      {
        "owner": "Wreck",
        "attribute": "qualityOfVerticalMeasurement",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "qualityOfVerticalMeasurement",
        "permitted_values": [
          "1",
          "2",
          "3",
          "4",
          "6",
          "7",
          "8",
          "9"
        ],
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "definition": "The reliability of the value of a sounding.",
        "attribute_definition": "The reliability of the value of a sounding.",
        "global_listed_values": [
          {
            "label": "Depth Known",
            "value": "1"
          },
          {
            "label": "Depth or Least Depth Unknown",
            "value": "2"
          },
          {
            "label": "Doubtful Sounding",
            "value": "3"
          },
          {
            "label": "Unreliable Sounding",
            "value": "4"
          },
          {
            "label": "Least Depth Known",
            "value": "6"
          },
          {
            "label": "Least Depth Unknown, Safe Clearance at Value Shown",
            "value": "7"
          },
          {
            "label": "Value Reported (Not Surveyed)",
            "value": "8"
          },
          {
            "label": "Value Reported (Not Confirmed)",
            "value": "9"
          },
          {
            "label": "Maintained Depth",
            "value": "10"
          },
          {
            "label": "Not Regularly Maintained",
            "value": "11"
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='qualityOfVerticalMeasurement']]",
        "listed_values": [
          {
            "label": "Depth Known",
            "value": "1"
          },
          {
            "label": "Depth or Least Depth Unknown",
            "value": "2"
          },
          {
            "label": "Doubtful Sounding",
            "value": "3"
          },
          {
            "label": "Unreliable Sounding",
            "value": "4"
          },
          {
            "label": "Least Depth Known",
            "value": "6"
          },
          {
            "label": "Least Depth Unknown, Safe Clearance at Value Shown",
            "value": "7"
          },
          {
            "label": "Value Reported (Not Surveyed)",
            "value": "8"
          },
          {
            "label": "Value Reported (Not Confirmed)",
            "value": "9"
          },
          {
            "label": "Maintained Depth",
            "value": "10"
          },
          {
            "label": "Not Regularly Maintained",
            "value": "11"
          }
        ],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='qualityOfVerticalMeasurement']]"
      },
      {
        "owner": "Wreck",
        "attribute": "radarConspicuous",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "radarConspicuous",
        "permitted_values": [],
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "definition": "A feature which returns a strong radar echo.",
        "attribute_definition": "A feature which returns a strong radar echo.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='radarConspicuous']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='radarConspicuous']]"
      },
      {
        "owner": "Wreck",
        "attribute": "reportedDate",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "reportedDate",
        "permitted_values": [],
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "definition": "The date that the item was observed, done, or investigated.",
        "attribute_definition": "The date that the item was observed, done, or investigated.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='reportedDate']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='reportedDate']]"
      },
      {
        "owner": "Wreck",
        "attribute": "status",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "status",
        "permitted_values": [
          "7",
          "13",
          "18"
        ],
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "definition": "The condition of an object at a given instant in time.",
        "attribute_definition": "The condition of an object at a given instant in time.",
        "global_listed_values": [
          {
            "label": "Permanent",
            "value": "1"
          },
          {
            "label": "Occasional",
            "value": "2"
          },
          {
            "label": "Recommended",
            "value": "3"
          },
          {
            "label": "Not in Use",
            "value": "4"
          },
          {
            "label": "Periodic/Intermittent",
            "value": "5"
          },
          {
            "label": "Reserved",
            "value": "6"
          },
          {
            "label": "Temporary",
            "value": "7"
          },
          {
            "label": "Private",
            "value": "8"
          },
          {
            "label": "Mandatory",
            "value": "9"
          },
          {
            "label": "Extinguished",
            "value": "11"
          },
          {
            "label": "Illuminated",
            "value": "12"
          },
          {
            "label": "Historic",
            "value": "13"
          },
          {
            "label": "Public",
            "value": "14"
          },
          {
            "label": "Synchronized",
            "value": "15"
          },
          {
            "label": "Watched",
            "value": "16"
          },
          {
            "label": "Unwatched",
            "value": "17"
          },
          {
            "label": "Existence Doubtful",
            "value": "18"
          },
          {
            "label": "Buoyed",
            "value": "28"
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='status']]",
        "listed_values": [
          {
            "label": "Permanent",
            "value": "1"
          },
          {
            "label": "Occasional",
            "value": "2"
          },
          {
            "label": "Recommended",
            "value": "3"
          },
          {
            "label": "Not in Use",
            "value": "4"
          },
          {
            "label": "Periodic/Intermittent",
            "value": "5"
          },
          {
            "label": "Reserved",
            "value": "6"
          },
          {
            "label": "Temporary",
            "value": "7"
          },
          {
            "label": "Private",
            "value": "8"
          },
          {
            "label": "Mandatory",
            "value": "9"
          },
          {
            "label": "Extinguished",
            "value": "11"
          },
          {
            "label": "Illuminated",
            "value": "12"
          },
          {
            "label": "Historic",
            "value": "13"
          },
          {
            "label": "Public",
            "value": "14"
          },
          {
            "label": "Synchronized",
            "value": "15"
          },
          {
            "label": "Watched",
            "value": "16"
          },
          {
            "label": "Unwatched",
            "value": "17"
          },
          {
            "label": "Existence Doubtful",
            "value": "18"
          },
          {
            "label": "Buoyed",
            "value": "28"
          }
        ],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='status']]"
      },
      {
        "owner": "Wreck",
        "attribute": "techniqueOfVerticalMeasurement",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "techniqueOfVerticalMeasurement",
        "permitted_values": [
          "1",
          "2",
          "3",
          "4",
          "5",
          "8",
          "9",
          "10",
          "11",
          "12",
          "13",
          "15",
          "16",
          "17",
          "18"
        ],
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "definition": "Survey method used to obtain depth information.",
        "attribute_definition": "Survey method used to obtain depth information.",
        "global_listed_values": [
          {
            "label": "Found by Echo Sounder",
            "value": "1"
          },
          {
            "label": "Found by Side Scan Sonar",
            "value": "2"
          },
          {
            "label": "Found by Multi Beam",
            "value": "3"
          },
          {
            "label": "Found by Diver",
            "value": "4"
          },
          {
            "label": "Found by Lead Line",
            "value": "5"
          },
          {
            "label": "Swept by Vertical Acoustic System",
            "value": "8"
          },
          {
            "label": "Found by Electromagnetic Sensor",
            "value": "9"
          },
          {
            "label": "Photogrammetry",
            "value": "10"
          },
          {
            "label": "Satellite Imagery",
            "value": "11"
          },
          {
            "label": "Found by Levelling",
            "value": "12"
          },
          {
            "label": "Swept by Side Scan Sonar",
            "value": "13"
          },
          {
            "label": "Found by LIDAR",
            "value": "15"
          },
          {
            "label": "Synthetic Aperture Radar",
            "value": "16"
          },
          {
            "label": "Hyperspectral Imagery",
            "value": "17"
          },
          {
            "label": "Mechanically Swept",
            "value": "18"
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='techniqueOfVerticalMeasurement']]",
        "listed_values": [
          {
            "label": "Found by Echo Sounder",
            "value": "1"
          },
          {
            "label": "Found by Side Scan Sonar",
            "value": "2"
          },
          {
            "label": "Found by Multi Beam",
            "value": "3"
          },
          {
            "label": "Found by Diver",
            "value": "4"
          },
          {
            "label": "Found by Lead Line",
            "value": "5"
          },
          {
            "label": "Swept by Vertical Acoustic System",
            "value": "8"
          },
          {
            "label": "Found by Electromagnetic Sensor",
            "value": "9"
          },
          {
            "label": "Photogrammetry",
            "value": "10"
          },
          {
            "label": "Satellite Imagery",
            "value": "11"
          },
          {
            "label": "Found by Levelling",
            "value": "12"
          },
          {
            "label": "Swept by Side Scan Sonar",
            "value": "13"
          },
          {
            "label": "Found by LIDAR",
            "value": "15"
          },
          {
            "label": "Synthetic Aperture Radar",
            "value": "16"
          },
          {
            "label": "Hyperspectral Imagery",
            "value": "17"
          },
          {
            "label": "Mechanically Swept",
            "value": "18"
          }
        ],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='techniqueOfVerticalMeasurement']]"
      },
      {
        "owner": "Wreck",
        "attribute": "valueOfSounding",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "valueOfSounding",
        "permitted_values": [],
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "definition": "The value of the measurement of a sounding relative to the chart datum.",
        "attribute_definition": "The value of the measurement of a sounding relative to the chart datum.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='valueOfSounding']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='valueOfSounding']]"
      },
      {
        "owner": "Wreck",
        "attribute": "visualProminence",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "visualProminence",
        "permitted_values": [
          "1",
          "2",
          "3"
        ],
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "definition": "The extent to which a feature, either natural or artificial, is visible from seaward.",
        "attribute_definition": "The extent to which a feature, either natural or artificial, is visible from seaward.",
        "global_listed_values": [
          {
            "label": "Visually Conspicuous",
            "value": "1"
          },
          {
            "label": "Not Visually Conspicuous",
            "value": "2"
          },
          {
            "label": "Prominent",
            "value": "3"
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='visualProminence']]",
        "listed_values": [
          {
            "label": "Visually Conspicuous",
            "value": "1"
          },
          {
            "label": "Not Visually Conspicuous",
            "value": "2"
          },
          {
            "label": "Prominent",
            "value": "3"
          }
        ],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='visualProminence']]"
      },
      {
        "owner": "Wreck",
        "attribute": "waterLevelEffect",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "waterLevelEffect",
        "permitted_values": [
          "1",
          "2",
          "3",
          "4",
          "5"
        ],
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "definition": "The effect of the surrounding water on an object.",
        "attribute_definition": "The effect of the surrounding water on an object.",
        "global_listed_values": [
          {
            "label": "Partly Submerged at High Water",
            "value": "1"
          },
          {
            "label": "Always Dry",
            "value": "2"
          },
          {
            "label": "Always Under Water/Submerged",
            "value": "3"
          },
          {
            "label": "Covers and Uncovers",
            "value": "4"
          },
          {
            "label": "Awash",
            "value": "5"
          },
          {
            "label": "Subject to Inundation or Flooding",
            "value": "6"
          },
          {
            "label": "Floating",
            "value": "7"
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='waterLevelEffect']]",
        "listed_values": [
          {
            "label": "Partly Submerged at High Water",
            "value": "1"
          },
          {
            "label": "Always Dry",
            "value": "2"
          },
          {
            "label": "Always Under Water/Submerged",
            "value": "3"
          },
          {
            "label": "Covers and Uncovers",
            "value": "4"
          },
          {
            "label": "Awash",
            "value": "5"
          },
          {
            "label": "Subject to Inundation or Flooding",
            "value": "6"
          },
          {
            "label": "Floating",
            "value": "7"
          }
        ],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='waterLevelEffect']]"
      },
      {
        "owner": "Wreck",
        "attribute": "scaleMinimum",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "scaleMinimum",
        "permitted_values": [],
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "definition": "The minimum scale at which the feature may be used for example for ECDIS presentation.",
        "attribute_definition": "The minimum scale at which the feature may be used for example for ECDIS presentation.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='scaleMinimum']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='scaleMinimum']]"
      },
      {
        "owner": "Wreck",
        "attribute": "information",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "information",
        "permitted_values": [],
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "definition": "Textual information about the feature. The information may be provided as a string of text or as a file name of a single external text file that contains the text.",
        "attribute_definition": "Textual information about the feature. The information may be provided as a string of text or as a file name of a single external text file that contains the text.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='information']]"
      },
      {
        "owner": "Wreck",
        "attribute": "pictorialRepresentation",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "pictorialRepresentation",
        "permitted_values": [],
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "definition": "The file name of an externally referenced picture file.",
        "attribute_definition": "The file name of an externally referenced picture file.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='pictorialRepresentation']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='pictorialRepresentation']]"
      },
      {
        "owner": "Wreck",
        "attribute": "defaultClearanceDepth",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "defaultClearanceDepth",
        "permitted_values": [],
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "definition": "The depth value determined for an underwater hazard of unknown depth, based on the depth of the surrounding area.",
        "attribute_definition": "The depth value determined for an underwater hazard of unknown depth, based on the depth of the surrounding area.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='defaultClearanceDepth']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='defaultClearanceDepth']]"
      },
      {
        "owner": "Wreck",
        "attribute": "surroundingDepth",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "surroundingDepth",
        "permitted_values": [],
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "definition": "The depth value determined for seabed around an underwater hazard, based on the depth of the surrounding area.",
        "attribute_definition": "The depth value determined for seabed around an underwater hazard, based on the depth of the surrounding area.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='surroundingDepth']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='surroundingDepth']]"
      }
    ],
    "definition_quote": "The ruined remains of a stranded or sunken vessel which has been rendered useless.",
    "source_ref": "data/s101_feature_catalogue_v2_parsed.json",
    "source_sha256": "0d26c66d0e1afd8a6ae33629e9bc1bb929c6a3735ccd1d60f637d149a54cad37",
    "evidence": {
      "edition": "2.0.0",
      "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
      "parsed_source_sha256": "0d26c66d0e1afd8a6ae33629e9bc1bb929c6a3735ccd1d60f637d149a54cad37",
      "source_ref": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
      "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
      "locators": [
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='categoryOfWreck']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='expositionOfSounding']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='featureName']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='height']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='interoperabilityIdentifier']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='qualityOfVerticalMeasurement']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='radarConspicuous']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='reportedDate']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='status']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='techniqueOfVerticalMeasurement']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='valueOfSounding']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='visualProminence']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='waterLevelEffect']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='scaleMinimum']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='information']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='pictorialRepresentation']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='defaultClearanceDepth']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='surroundingDepth']]"
      ],
      "claim_source_links": [
        {
          "claim": "The ruined remains of a stranded or sunken vessel which has been rendered useless.",
          "source_ref": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
          "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
          "definition_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='definition']",
          "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='definition']"
        }
      ]
    }
  },
  "search_executed": false,
  "execution_status": "COMPLETED",
  "source_coverage": {},
  "per_task_status": {},
  "mapping_provenance": {
    "version": "emitted_output_v1",
    "root": "final_state.final_dict",
    "retrieved_text_used_as_answer": false,
    "reference_used_for_mapping": false,
    "structured_document_answer_present": true
  },
  "status": "COMPLETED",
  "blocker": null,
  "clarification_request": [],
  "answer_text": "S-101 Feature Catalogue 2.0.0\n\nWreck: The ruined remains of a stranded or sunken vessel which has been rendered useless.\n허용 기하: point, surface\n\n근거: data/s101_feature_catalogue_v2_parsed.json; //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='categoryOfWreck']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='expositionOfSounding']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='featureName']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='height']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='interoperabilityIdentifier']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='qualityOfVerticalMeasurement']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='radarConspicuous']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='reportedDate']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='status']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='techniqueOfVerticalMeasurement']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='valueOfSounding']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='visualProminence']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='waterLevelEffect']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='scaleMinimum']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='information']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='pictorialRepresentation']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='defaultClearanceDepth']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='surroundingDepth']]"
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q6_01.json)
```json
{
  "case_id": "PILOT_Q6_01",
  "required_task_obligations": [
    "provide_wreck_definition_text",
    "cite_catalogue_edition_and_locator"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_037",
  "answer_sha256": "8a647e623b2c2e65dd2e94737bece57cc3bbf57e3366fbb99b1d8519f583f22c",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "249042a18409bf6edb87cd18e467a589d6b0c940f8ee73682cabc7c7c4c4aa6f",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_036 — Find wrecks within 5 km of Dokdo and explain their S-101 attributes.

답안 hash: `6642c63aac49aea5b2868ccf418b2bb362d208e8cba2c8280d126373812bf2d0`

### 실제 최종 답안
```json
{
  "answer_text": "Within 5 km of Dokdo, there are no wrecks listed in the provided data.",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q5_03.json)
```json
{
  "case_id": "PILOT_Q5_03",
  "required_task_obligations": [
    "resolve_reference",
    "verify_coverage",
    "search_wrecks_5000m",
    "explain_s101_attributes",
    "distinguish_object_values_from_standard_attributes",
    "separate_partial_document_answer"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "User-approved source-bound safe abstention; document explanations are separately evaluated optional partial output."
  ],
  "expected_spatial_behavior": {
    "accepted_states": [
      "BLOCKED_DATA",
      "DATA_OUT_OF_SCOPE"
    ],
    "required_disclosure": "Current connected snapshot cannot determine the answer for the requested spatial extent",
    "per_target": {
      "Wreck": {
        "status": "BLOCKED_DATA",
        "object_ids": null
      }
    },
    "empty_result_as_answer_forbidden": true,
    "claim_spatial_success_forbidden": true
  }
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_036",
  "answer_sha256": "6642c63aac49aea5b2868ccf418b2bb362d208e8cba2c8280d126373812bf2d0",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "6bf1fa81d9340069255690786a9bca6101c354620aa201a1b9eaa7f19a3241a1",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_035 — S-101 등대의 색상 속성과 허용 값을 알려줘.

답안 hash: `254751d621ddf61dc526f332fe14b218128255dd14e01dbff192ccc5cba466eb`

### 실제 최종 답안
```json
{
  "answer_text": "등대 색상: 주로 노란색이며, 일부는 검정색이나 흰색입니다. 허용 레이즈: 1000m 이내입니다.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "validator_blockers": [
    "BLOCKED_DATA: public catalogue document evidence unavailable"
  ],
  "status": "BLOCKED_DATA",
  "execution_status": "BLOCKED_DATA",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q2_01.json)
```json
{
  "case_id": "PILOT_Q2_01",
  "required_task_obligations": [
    "distinguish_structure_and_light_colour",
    "explain_feature_bound_permitted_values"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "single_Lighthouse_feature_assertion",
    "global_colour_codes_for_feature_binding"
  ],
  "scope_notes": [
    "Landmark/Building describe conditional structure alternatives; LightAllAround/LightSectored describe light alternatives. Listing these for explanation does not assert all must exist in one physical lighthouse."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_035",
  "answer_sha256": "254751d621ddf61dc526f332fe14b218128255dd14e01dbff192ccc5cba466eb",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "c0ec0bf7ca6b1bbeb618edfd947e7baaf0d6c9452b703ec7887ec38479d02632",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_034 — What source supports the S-101 definition of AnchorageArea?

답안 hash: `4908016db6bd5539d15c6044a587007bfaf10f128c6d28506f410309cafa0b4b`

### 실제 최종 답안
```json
{
  "answer_text": "The S-101 definition of AnchorageArea is supported by the source with the source_coverage scope verified, BBOX in EPSG:4326, and source_sha256 '1300232a3f03d17ea822eeff55fde99c5458b836f86d26bfd445b9afe8bb7f85'. This source is also used in the reference_geometry_registry for the Busan region.",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q6_03.json)
```json
{
  "case_id": "PILOT_Q6_03",
  "required_task_obligations": [
    "provide_anchorage_definition_source",
    "cite_catalogue_edition_and_locator"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_034",
  "answer_sha256": "4908016db6bd5539d15c6044a587007bfaf10f128c6d28506f410309cafa0b4b",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "ae77867f64e3dcb8325e9479c3b10d29e63bb7c24aad14f269994ee40e12e619",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_033 — 부산항 주변 2km의 정박지와 제한구역을 찾아 비교해줘.

답안 hash: `beb8beb758afcc2e326ddda5701f305a9f2a2aba7e3bc7b100c34c91e7ed4ec9`

### 실제 최종 답안
```json
{
  "answer_text": "검색 결과: 부산항 주변 2km의 정박지와 제한구역은 다음과 같습니다.\n\n1. 정박지: \n   - 부산항 주변 2km 내에 위치한 정박지 정보가 없습니다.\n\n2. 제한구역: \n   - 부산항 주변 2km 내에 위치한 제한구역 정보가 없습니다.",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q5_02.json)
```json
{
  "case_id": "PILOT_Q5_02",
  "required_task_obligations": [
    "resolve_reference",
    "verify_both_target_coverages",
    "search_both_targets_2000m",
    "compare_target_results",
    "disclose_subset_limitations"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "Object IDs refer to frozen snapshot records, not deduplicated physical facilities or the whole legal port."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_033",
  "answer_sha256": "beb8beb758afcc2e326ddda5701f305a9f2a2aba7e3bc7b100c34c91e7ed4ec9",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "78f6a7ab1b93025811a08823ef336b9f4a52274ca25dca1101aa4bf6e5851dad",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_032 — 독도 주변 5km의 등대와 난파선을 찾아 각각의 근거를 알려줘.

답안 hash: `d078607fab92a5636acc78b67c0a8f6b2d25cacc230c7f40f6a72f976d703523`

### 실제 최종 답안
```json
{
  "answer_text": "The beacon and anchor line around Dokdo have been found. The beacon is located at 128.9, 34.9, and the anchor line is located at 129.3, 35.3.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "validator_blockers": [
    "BLOCKED_DATA: public catalogue document evidence unavailable",
    "BLOCKED_DATA: public catalogue document evidence unavailable"
  ],
  "status": "BLOCKED_DATA",
  "execution_status": "BLOCKED_DATA",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q5_01.json)
```json
{
  "case_id": "PILOT_Q5_01",
  "required_task_obligations": [
    "resolve_reference",
    "resolve_lighthouse_target_conditions",
    "verify_both_target_coverages",
    "search_both_targets_5000m",
    "provide_per_target_evidence",
    "separate_partial_document_answer"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "User-approved source-bound safe abstention; document explanations are separately evaluated optional partial output."
  ],
  "expected_spatial_behavior": {
    "accepted_states": [
      "BLOCKED_DATA",
      "DATA_OUT_OF_SCOPE"
    ],
    "required_disclosure": "Current connected snapshot cannot determine the answer for the requested spatial extent",
    "per_target": {
      "Lighthouse": {
        "status": "BLOCKED_DATA",
        "object_ids": null
      },
      "Wreck": {
        "status": "BLOCKED_DATA",
        "object_ids": null
      }
    },
    "empty_result_as_answer_forbidden": true,
    "claim_spatial_success_forbidden": true
  }
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_032",
  "answer_sha256": "d078607fab92a5636acc78b67c0a8f6b2d25cacc230c7f40f6a72f976d703523",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "33249af9f19fdc6dea59395a7c3a9a852356980b5ee1bc19b5f4f5aeeedc0c83",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_031 — Find wrecks intersecting the selected area.

답안 hash: `48dca007030c03e110efec058547a166c2e833f3b84bb84c6b1e45e92cb5a8c4`

### 실제 최종 답안
```json
{
  "answer_text": "The selected area does not intersect any wrecks.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "status": "NEEDS_USER_INPUT",
  "clarification_request": "The selected area does not intersect any wrecks.",
  "execution_status": "NEEDS_USER_INPUT",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q3_03.json)
```json
{
  "case_id": "PILOT_Q3_03",
  "required_task_obligations": [
    "require_selected_aoi",
    "verify_coverage",
    "search_intersections_if_aoi_available",
    "request_aoi_when_missing"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "No selected geometry is provided by this benchmark input; an arbitrary viewport is not a substitute."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_031",
  "answer_sha256": "48dca007030c03e110efec058547a166c2e833f3b84bb84c6b1e45e92cb5a8c4",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "9f45e4ac5d9ba6799b3311b6c20eab8af355d95f7ffe6b767ebb105cf57d9403",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_030 — S-101에서 정박지는 어떤 객체야?

답안 hash: `d93e677e7c78908f06b6b57669d33b927dc1dc8d108c599d86cf90f192e193ea`

### 실제 최종 답안
```json
{
  "document_answer": {
    "features": [
      {
        "code": "AnchorageArea",
        "definition": "An area in which vessels or seaplanes anchor or may anchor.",
        "permitted_primitives": [
          "point",
          "surface"
        ]
      }
    ],
    "attribute_bindings": [
      {
        "owner": "AnchorageArea",
        "attribute": "categoryOfAnchorage",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "categoryOfAnchorage",
        "permitted_values": [
          "1",
          "2",
          "3",
          "5",
          "6",
          "7",
          "9",
          "10",
          "14",
          "15"
        ],
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "definition": "Classification of an area where different use types of vessel can remain static.",
        "attribute_definition": "Classification of an area where different use types of vessel can remain static.",
        "global_listed_values": [
          {
            "label": "Unrestricted Anchorage",
            "value": "1"
          },
          {
            "label": "Deep Water Anchorage",
            "value": "2"
          },
          {
            "label": "Tanker Anchorage",
            "value": "3"
          },
          {
            "label": "Quarantine Anchorage",
            "value": "5"
          },
          {
            "label": "Seaplane Anchorage",
            "value": "6"
          },
          {
            "label": "Small Craft Anchorage",
            "value": "7"
          },
          {
            "label": "Anchorage for Periods Up To 24 Hours",
            "value": "9"
          },
          {
            "label": "Anchorage for a Limited Period of Time",
            "value": "10"
          },
          {
            "label": "Waiting Anchorage",
            "value": "14"
          },
          {
            "label": "Reported Anchorage",
            "value": "15"
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='categoryOfAnchorage']]",
        "listed_values": [
          {
            "label": "Unrestricted Anchorage",
            "value": "1"
          },
          {
            "label": "Deep Water Anchorage",
            "value": "2"
          },
          {
            "label": "Tanker Anchorage",
            "value": "3"
          },
          {
            "label": "Quarantine Anchorage",
            "value": "5"
          },
          {
            "label": "Seaplane Anchorage",
            "value": "6"
          },
          {
            "label": "Small Craft Anchorage",
            "value": "7"
          },
          {
            "label": "Anchorage for Periods Up To 24 Hours",
            "value": "9"
          },
          {
            "label": "Anchorage for a Limited Period of Time",
            "value": "10"
          },
          {
            "label": "Waiting Anchorage",
            "value": "14"
          },
          {
            "label": "Reported Anchorage",
            "value": "15"
          }
        ],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='categoryOfAnchorage']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "categoryOfCargo",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "categoryOfCargo",
        "permitted_values": [
          "1",
          "2",
          "3",
          "4",
          "5",
          "6",
          "7",
          "8",
          "9",
          "10",
          "11",
          "12",
          "13",
          "14",
          "15"
        ],
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "definition": "Classification of the different types of cargo that a ship may be carrying.",
        "attribute_definition": "Classification of the different types of cargo that a ship may be carrying.",
        "global_listed_values": [
          {
            "label": "Bulk",
            "value": "1"
          },
          {
            "label": "Container",
            "value": "2"
          },
          {
            "label": "General",
            "value": "3"
          },
          {
            "label": "Liquid",
            "value": "4"
          },
          {
            "label": "Passenger",
            "value": "5"
          },
          {
            "label": "Livestock",
            "value": "6"
          },
          {
            "label": "Dangerous or Hazardous",
            "value": "7"
          },
          {
            "label": "Heavy Lift",
            "value": "8"
          },
          {
            "label": "Ballast",
            "value": "9"
          },
          {
            "label": "Dry Bulk Cargo",
            "value": "10"
          },
          {
            "label": "Liquid Bulk Cargo",
            "value": "11"
          },
          {
            "label": "Reefer Container Cargo",
            "value": "12"
          },
          {
            "label": "Ro-Ro Cargo",
            "value": "13"
          },
          {
            "label": "Project Cargo",
            "value": "14"
          },
          {
            "label": "Break Bulk Cargo",
            "value": "15"
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='categoryOfCargo']]",
        "listed_values": [
          {
            "label": "Bulk",
            "value": "1"
          },
          {
            "label": "Container",
            "value": "2"
          },
          {
            "label": "General",
            "value": "3"
          },
          {
            "label": "Liquid",
            "value": "4"
          },
          {
            "label": "Passenger",
            "value": "5"
          },
          {
            "label": "Livestock",
            "value": "6"
          },
          {
            "label": "Dangerous or Hazardous",
            "value": "7"
          },
          {
            "label": "Heavy Lift",
            "value": "8"
          },
          {
            "label": "Ballast",
            "value": "9"
          },
          {
            "label": "Dry Bulk Cargo",
            "value": "10"
          },
          {
            "label": "Liquid Bulk Cargo",
            "value": "11"
          },
          {
            "label": "Reefer Container Cargo",
            "value": "12"
          },
          {
            "label": "Ro-Ro Cargo",
            "value": "13"
          },
          {
            "label": "Project Cargo",
            "value": "14"
          },
          {
            "label": "Break Bulk Cargo",
            "value": "15"
          }
        ],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='categoryOfCargo']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "featureName",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "featureName",
        "permitted_values": [],
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "definition": "Provides the name of an entity, defines the national language of the name, and provides the option to display the name at various system display settings.",
        "attribute_definition": "Provides the name of an entity, defines the national language of the name, and provides the option to display the name at various system display settings.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='featureName']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='featureName']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "fixedDateRange",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "fixedDateRange",
        "permitted_values": [],
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "definition": "An active period of a single fixed event or occurrence, as the date range between discrete start and end dates.",
        "attribute_definition": "An active period of a single fixed event or occurrence, as the date range between discrete start and end dates.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='fixedDateRange']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='fixedDateRange']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "interoperabilityIdentifier",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "interoperabilityIdentifier",
        "permitted_values": [],
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "definition": "A common unique identifier for entities which describe a single real-world feature, and which is used to identify instances of the feature in end-user systems where the feature may be included in multiple data product types.",
        "attribute_definition": "A common unique identifier for entities which describe a single real-world feature, and which is used to identify instances of the feature in end-user systems where the feature may be included in multiple data product types.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='interoperabilityIdentifier']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='interoperabilityIdentifier']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "periodicDateRange",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "periodicDateRange",
        "permitted_values": [],
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "definition": "The active period of a recurring event or occurrence.",
        "attribute_definition": "The active period of a recurring event or occurrence.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='periodicDateRange']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='periodicDateRange']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "restriction",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "restriction",
        "permitted_values": [
          "2",
          "3",
          "4",
          "5",
          "6",
          "8",
          "9",
          "10",
          "11",
          "12",
          "13",
          "15",
          "16",
          "17",
          "18",
          "19",
          "20",
          "21",
          "23",
          "24",
          "27",
          "39"
        ],
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "definition": "The official legal statute of each kind of restricted area.",
        "attribute_definition": "The official legal statute of each kind of restricted area.",
        "global_listed_values": [
          {
            "label": "Anchoring Prohibited",
            "value": "1"
          },
          {
            "label": "Anchoring Restricted",
            "value": "2"
          },
          {
            "label": "Fishing Prohibited",
            "value": "3"
          },
          {
            "label": "Fishing Restricted",
            "value": "4"
          },
          {
            "label": "Trawling Prohibited",
            "value": "5"
          },
          {
            "label": "Trawling Restricted",
            "value": "6"
          },
          {
            "label": "Entry Prohibited",
            "value": "7"
          },
          {
            "label": "Entry Restricted",
            "value": "8"
          },
          {
            "label": "Dredging Prohibited",
            "value": "9"
          },
          {
            "label": "Dredging Restricted",
            "value": "10"
          },
          {
            "label": "Diving Prohibited",
            "value": "11"
          },
          {
            "label": "Diving Restricted",
            "value": "12"
          },
          {
            "label": "No Wake",
            "value": "13"
          },
          {
            "label": "Area To Be Avoided",
            "value": "14"
          },
          {
            "label": "Construction Prohibited",
            "value": "15"
          },
          {
            "label": "Discharging Prohibited",
            "value": "16"
          },
          {
            "label": "Discharging Restricted",
            "value": "17"
          },
          {
            "label": "Industrial or Mineral Exploration/Development Prohibited",
            "value": "18"
          },
          {
            "label": "Industrial or Mineral Exploration/Development Restricted",
            "value": "19"
          },
          {
            "label": "Drilling Prohibited",
            "value": "20"
          },
          {
            "label": "Drilling Restricted",
            "value": "21"
          },
          {
            "label": "Removal of Historical Artefacts Prohibited",
            "value": "22"
          },
          {
            "label": "Cargo Transhipment (Lightening) Prohibited",
            "value": "23"
          },
          {
            "label": "Dragging Prohibited",
            "value": "24"
          },
          {
            "label": "Stopping Prohibited",
            "value": "25"
          },
          {
            "label": "Landing Prohibited",
            "value": "26"
          },
          {
            "label": "Speed Restricted",
            "value": "27"
          },
          {
            "label": "Swimming Prohibited",
            "value": "39"
          },
          {
            "label": "Power-Driven Vessels Prohibited",
            "value": "42"
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='restriction']]",
        "listed_values": [
          {
            "label": "Anchoring Prohibited",
            "value": "1"
          },
          {
            "label": "Anchoring Restricted",
            "value": "2"
          },
          {
            "label": "Fishing Prohibited",
            "value": "3"
          },
          {
            "label": "Fishing Restricted",
            "value": "4"
          },
          {
            "label": "Trawling Prohibited",
            "value": "5"
          },
          {
            "label": "Trawling Restricted",
            "value": "6"
          },
          {
            "label": "Entry Prohibited",
            "value": "7"
          },
          {
            "label": "Entry Restricted",
            "value": "8"
          },
          {
            "label": "Dredging Prohibited",
            "value": "9"
          },
          {
            "label": "Dredging Restricted",
            "value": "10"
          },
          {
            "label": "Diving Prohibited",
            "value": "11"
          },
          {
            "label": "Diving Restricted",
            "value": "12"
          },
          {
            "label": "No Wake",
            "value": "13"
          },
          {
            "label": "Area To Be Avoided",
            "value": "14"
          },
          {
            "label": "Construction Prohibited",
            "value": "15"
          },
          {
            "label": "Discharging Prohibited",
            "value": "16"
          },
          {
            "label": "Discharging Restricted",
            "value": "17"
          },
          {
            "label": "Industrial or Mineral Exploration/Development Prohibited",
            "value": "18"
          },
          {
            "label": "Industrial or Mineral Exploration/Development Restricted",
            "value": "19"
          },
          {
            "label": "Drilling Prohibited",
            "value": "20"
          },
          {
            "label": "Drilling Restricted",
            "value": "21"
          },
          {
            "label": "Removal of Historical Artefacts Prohibited",
            "value": "22"
          },
          {
            "label": "Cargo Transhipment (Lightening) Prohibited",
            "value": "23"
          },
          {
            "label": "Dragging Prohibited",
            "value": "24"
          },
          {
            "label": "Stopping Prohibited",
            "value": "25"
          },
          {
            "label": "Landing Prohibited",
            "value": "26"
          },
          {
            "label": "Speed Restricted",
            "value": "27"
          },
          {
            "label": "Swimming Prohibited",
            "value": "39"
          },
          {
            "label": "Power-Driven Vessels Prohibited",
            "value": "42"
          }
        ],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='restriction']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "status",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "status",
        "permitted_values": [
          "1",
          "2",
          "3",
          "5",
          "6",
          "7",
          "8",
          "9",
          "14"
        ],
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "definition": "The condition of an object at a given instant in time.",
        "attribute_definition": "The condition of an object at a given instant in time.",
        "global_listed_values": [
          {
            "label": "Permanent",
            "value": "1"
          },
          {
            "label": "Occasional",
            "value": "2"
          },
          {
            "label": "Recommended",
            "value": "3"
          },
          {
            "label": "Not in Use",
            "value": "4"
          },
          {
            "label": "Periodic/Intermittent",
            "value": "5"
          },
          {
            "label": "Reserved",
            "value": "6"
          },
          {
            "label": "Temporary",
            "value": "7"
          },
          {
            "label": "Private",
            "value": "8"
          },
          {
            "label": "Mandatory",
            "value": "9"
          },
          {
            "label": "Extinguished",
            "value": "11"
          },
          {
            "label": "Illuminated",
            "value": "12"
          },
          {
            "label": "Historic",
            "value": "13"
          },
          {
            "label": "Public",
            "value": "14"
          },
          {
            "label": "Synchronized",
            "value": "15"
          },
          {
            "label": "Watched",
            "value": "16"
          },
          {
            "label": "Unwatched",
            "value": "17"
          },
          {
            "label": "Existence Doubtful",
            "value": "18"
          },
          {
            "label": "Buoyed",
            "value": "28"
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='status']]",
        "listed_values": [
          {
            "label": "Permanent",
            "value": "1"
          },
          {
            "label": "Occasional",
            "value": "2"
          },
          {
            "label": "Recommended",
            "value": "3"
          },
          {
            "label": "Not in Use",
            "value": "4"
          },
          {
            "label": "Periodic/Intermittent",
            "value": "5"
          },
          {
            "label": "Reserved",
            "value": "6"
          },
          {
            "label": "Temporary",
            "value": "7"
          },
          {
            "label": "Private",
            "value": "8"
          },
          {
            "label": "Mandatory",
            "value": "9"
          },
          {
            "label": "Extinguished",
            "value": "11"
          },
          {
            "label": "Illuminated",
            "value": "12"
          },
          {
            "label": "Historic",
            "value": "13"
          },
          {
            "label": "Public",
            "value": "14"
          },
          {
            "label": "Synchronized",
            "value": "15"
          },
          {
            "label": "Watched",
            "value": "16"
          },
          {
            "label": "Unwatched",
            "value": "17"
          },
          {
            "label": "Existence Doubtful",
            "value": "18"
          },
          {
            "label": "Buoyed",
            "value": "28"
          }
        ],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='status']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "vesselSpeedLimit",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "vesselSpeedLimit",
        "permitted_values": [],
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "definition": "The maximum allowed rate of travel for a vessel in an area in knots.",
        "attribute_definition": "The maximum allowed rate of travel for a vessel in an area in knots.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='vesselSpeedLimit']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='vesselSpeedLimit']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "scaleMinimum",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "scaleMinimum",
        "permitted_values": [],
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "definition": "The minimum scale at which the feature may be used for example for ECDIS presentation.",
        "attribute_definition": "The minimum scale at which the feature may be used for example for ECDIS presentation.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='scaleMinimum']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='scaleMinimum']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "information",
        "kind": "attributeBinding",
        "type": "attribute",
        "ref": "information",
        "permitted_values": [],
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "definition": "Textual information about the feature. The information may be provided as a string of text or as a file name of a single external text file that contains the text.",
        "attribute_definition": "Textual information about the feature. The information may be provided as a string of text or as a file name of a single external text file that contains the text.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "listed_values": [],
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='information']]"
      }
    ],
    "definition_quote": "An area in which vessels or seaplanes anchor or may anchor.",
    "source_ref": "data/s101_feature_catalogue_v2_parsed.json",
    "source_sha256": "0d26c66d0e1afd8a6ae33629e9bc1bb929c6a3735ccd1d60f637d149a54cad37",
    "evidence": {
      "edition": "2.0.0",
      "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
      "parsed_source_sha256": "0d26c66d0e1afd8a6ae33629e9bc1bb929c6a3735ccd1d60f637d149a54cad37",
      "source_ref": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
      "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
      "locators": [
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='categoryOfAnchorage']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='categoryOfCargo']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='featureName']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='fixedDateRange']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='interoperabilityIdentifier']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='periodicDateRange']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='restriction']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='status']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='vesselSpeedLimit']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='scaleMinimum']]",
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='information']]"
      ],
      "claim_source_links": [
        {
          "claim": "An area in which vessels or seaplanes anchor or may anchor.",
          "source_ref": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
          "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
          "definition_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='definition']",
          "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='definition']"
        }
      ]
    }
  },
  "search_executed": false,
  "execution_status": "COMPLETED",
  "source_coverage": {},
  "per_task_status": {},
  "mapping_provenance": {
    "version": "emitted_output_v1",
    "root": "final_state.final_dict",
    "retrieved_text_used_as_answer": false,
    "reference_used_for_mapping": false,
    "structured_document_answer_present": true
  },
  "status": "COMPLETED",
  "blocker": null,
  "clarification_request": [],
  "answer_text": "S-101 Feature Catalogue 2.0.0\n\nAnchorageArea: An area in which vessels or seaplanes anchor or may anchor.\n허용 기하: point, surface\n\n근거: data/s101_feature_catalogue_v2_parsed.json; //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='categoryOfAnchorage']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='categoryOfCargo']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='featureName']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='fixedDateRange']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='interoperabilityIdentifier']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='periodicDateRange']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='restriction']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='status']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='vesselSpeedLimit']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='scaleMinimum']], //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]/*[local-name()='attributeBinding'][*[local-name()='attribute' and @ref='information']]"
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q1_02.json)
```json
{
  "case_id": "PILOT_Q1_02",
  "required_task_obligations": [
    "explain_anchorage_area_definition"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_030",
  "answer_sha256": "d93e677e7c78908f06b6b57669d33b927dc1dc8d108c599d86cf90f192e193ea",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "f547865c71ea3c32bf5d3e6ba05912bb8eaf345840fce9747022efeebea4a22f",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_029 — 독도 주변 반경 5000m의 해양지명을 찾아줘.

답안 hash: `60c211687044ae1a438dedd0973fdf6fb3b4c98a5302717b4c70b2f85590faf2`

### 실제 최종 답안
```json
{
  "answer_text": "独岛位于韩国济州道的独岛郡，距离济州岛约10公里。",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "document_answer": {
    "features": [],
    "attribute_bindings": [],
    "evidence": {
      "edition": "2.0.0",
      "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
      "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
      "locators": [],
      "claim_source_links": []
    }
  },
  "status": "COMPLETED",
  "execution_status": "COMPLETED",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q4_02.json)
```json
{
  "case_id": "PILOT_Q4_02",
  "required_task_obligations": [
    "resolve_approved_anchor",
    "search_fixed_gazetteer_5000m",
    "report_source_bound_objects"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_029",
  "answer_sha256": "60c211687044ae1a438dedd0973fdf6fb3b4c98a5302717b4c70b2f85590faf2",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "0ea138088fd41dac4cd15400661d1dd782a7bc64b39aa843fca75534ee622087",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_028 — What is a wreck in S-101?

답안 hash: `6bc05fe6afc8b24bc515e4df30fb86d3e01d93d283cf513af4c6d904d7ec42f0`

### 실제 최종 답안
```json
{
  "answer_text": "A wreck in S-101 refers to a shipwreck or wreckage found within the S-101 area. This area is part of the S-101 research snapshot, which includes the Busan research subset. The wreck is not covered by the Busan regional aids, so it is not included in the coverage.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "status": "PARTIAL",
  "execution_status": "PARTIAL",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q1_03.json)
```json
{
  "case_id": "PILOT_Q1_03",
  "required_task_obligations": [
    "explain_wreck_definition"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_028",
  "answer_sha256": "6bc05fe6afc8b24bc515e4df30fb86d3e01d93d283cf513af4c6d904d7ec42f0",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "5bd97c628fc1d0d2266b05c4fd271fc32cebf24a5defb7b8bdfbe537009b0afd",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_027 — 부산항 주변 2km의 정박지와 제한구역을 찾아 비교해줘.

답안 hash: `dbba72a1a215650eb09b98076e76acbf7eac0129673e2147ed2dae5729c3c699`

### 실제 최종 답안
```json
{
  "document_answer": {
    "features": [],
    "attribute_bindings": []
  },
  "search_executed": false,
  "execution_status": "BLOCKED",
  "source_coverage": {},
  "per_task_status": {},
  "mapping_provenance": {
    "version": "emitted_output_v1",
    "root": "final_state.final_dict",
    "retrieved_text_used_as_answer": false,
    "reference_used_for_mapping": false,
    "structured_document_answer_present": false
  },
  "status": "BLOCKED",
  "blocker": "UNSUPPORTED_COMPOSITE_TASK",
  "clarification_request": [],
  "answer_text": "요청한 여러 대상의 검색·비교를 모두 수행하는 실행 경로가 아직 지원되지 않습니다. 일부 대상만 조회하지 않았습니다."
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q5_02.json)
```json
{
  "case_id": "PILOT_Q5_02",
  "required_task_obligations": [
    "resolve_reference",
    "verify_both_target_coverages",
    "search_both_targets_2000m",
    "compare_target_results",
    "disclose_subset_limitations"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "Object IDs refer to frozen snapshot records, not deduplicated physical facilities or the whole legal port."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_027",
  "answer_sha256": "dbba72a1a215650eb09b98076e76acbf7eac0129673e2147ed2dae5729c3c699",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "4f6b48d26d5abfe5b733929c616a6509f95b2cc4cf476f6c1d447626ebbdc0c5",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_026 — 부산항 영역 안의 정박지를 찾아줘.

답안 hash: `82c87058054e31ca589fafd447e5cbc5cb65f290acd95242b2741d6ba1034a8c`

### 실제 최종 답안
```json
{
  "answer_text": "The anchorage area within 1 kilometer of Busan Port is as follows:",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q3_02.json)
```json
{
  "case_id": "PILOT_Q3_02",
  "required_task_obligations": [
    "resolve_official_port_polygon",
    "verify_coverage",
    "search_within_polygon",
    "report_objects_or_unresolved_reason"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "Object IDs refer to frozen snapshot records, not deduplicated physical facilities or the whole legal port."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_026",
  "answer_sha256": "82c87058054e31ca589fafd447e5cbc5cb65f290acd95242b2741d6ba1034a8c",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "5ba259fa6046492e4853f2a736220d38a054a99d2bb5d155cf3336045caf3978",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_025 — 제한구역의 제한 종류는 어떤 코드로 표현해?

답안 hash: `66c82e651dea1ff6909c93e264a49a64f6fd34306fe74d5dd958ae8637cd3f36`

### 실제 최종 답안
```json
{
  "answer_text": "The restricted type is represented by the code 's101'.",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q2_02.json)
```json
{
  "case_id": "PILOT_Q2_02",
  "required_task_obligations": [
    "distinguish_restriction_and_area_category",
    "explain_restriction_codes"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": [
    "Explain restriction codes separately from categoryOfRestrictedArea. RequiredArea alternatives from another FC edition are not substitutes for FC 2.0.0 RestrictedArea."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_025",
  "answer_sha256": "66c82e651dea1ff6909c93e264a49a64f6fd34306fe74d5dd958ae8637cd3f36",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "9200d8e6678e7d9f4dc9c6a5125d2a0084a629d7600df380fbc2ca100b944080",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_024 — 독도 주변 5km의 등대와 난파선을 찾아 각각의 근거를 알려줘.

답안 hash: `f694eb175c7e2c2adbd30244f7296efde49a6878ea5de81ff2ff6b099dd8cf39`

### 실제 최종 답안
```json
{
  "answer_text": "Dokdo is surrounded by lighthouses and anchor lines within a 5km radius. Lighthouse: Dokdo Lighthouse (129.2357, 35.2353) and Dokdo Lighthouse (129.2357, 35.2353). Anchor line: Dokdo anchor line (129.2357, 35.2353).",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q5_01.json)
```json
{
  "case_id": "PILOT_Q5_01",
  "required_task_obligations": [
    "resolve_reference",
    "resolve_lighthouse_target_conditions",
    "verify_both_target_coverages",
    "search_both_targets_5000m",
    "provide_per_target_evidence",
    "separate_partial_document_answer"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "User-approved source-bound safe abstention; document explanations are separately evaluated optional partial output."
  ],
  "expected_spatial_behavior": {
    "accepted_states": [
      "BLOCKED_DATA",
      "DATA_OUT_OF_SCOPE"
    ],
    "required_disclosure": "Current connected snapshot cannot determine the answer for the requested spatial extent",
    "per_target": {
      "Lighthouse": {
        "status": "BLOCKED_DATA",
        "object_ids": null
      },
      "Wreck": {
        "status": "BLOCKED_DATA",
        "object_ids": null
      }
    },
    "empty_result_as_answer_forbidden": true,
    "claim_spatial_success_forbidden": true
  }
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_024",
  "answer_sha256": "f694eb175c7e2c2adbd30244f7296efde49a6878ea5de81ff2ff6b099dd8cf39",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "e4558943ad847e2dfc4cd01157a237675d53bd5beb03558e8c821772e8d77c70",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_023 — S-101 등대의 색상 속성과 허용 값을 알려줘.

답안 hash: `bd77b317c7bb855ae6a44953062bfd6e8f016f11cde8502fc08fa6120670e448`

### 실제 최종 답안
```json
{
  "answer_text": "등대의 색상 속성은 일반적으로 흰색이며, 허용 값은 100m 이내입니다. 이 정보는 실제 위치에 따라 달라질 수 있으므로, 정확한 정보는 현장에서 확인하시기 바랍니다.",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q2_01.json)
```json
{
  "case_id": "PILOT_Q2_01",
  "required_task_obligations": [
    "distinguish_structure_and_light_colour",
    "explain_feature_bound_permitted_values"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "single_Lighthouse_feature_assertion",
    "global_colour_codes_for_feature_binding"
  ],
  "scope_notes": [
    "Landmark/Building describe conditional structure alternatives; LightAllAround/LightSectored describe light alternatives. Listing these for explanation does not assert all must exist in one physical lighthouse."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_023",
  "answer_sha256": "bd77b317c7bb855ae6a44953062bfd6e8f016f11cde8502fc08fa6120670e448",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "5d13367b1b27b7292dca287d8b0b64a36b7a485405b72cba89dc548b62086b7d",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_022 — 등대와 부표를 구분하는 S-101 근거를 알려줘.

답안 hash: `7733e901a5d50e0b8e8960ebcabf55cd201eff6d82413f5c85ae8dfab236f92f`

### 실제 최종 답안
```json
{
  "answer_text": "等明灯和浮标在S-101数据库中可以区分。",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "document_answers": [
    {
      "features": [],
      "attribute_bindings": [],
      "evidence": {
        "edition": "2.0.0",
        "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
        "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
        "locators": [],
        "claim_source_links": []
      }
    },
    {
      "features": [],
      "attribute_bindings": [],
      "evidence": {
        "edition": "2.0.0",
        "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
        "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
        "locators": [],
        "claim_source_links": []
      }
    }
  ],
  "status": "COMPLETED",
  "execution_status": "COMPLETED",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q6_02.json)
```json
{
  "case_id": "PILOT_Q6_02",
  "required_task_obligations": [
    "compare_fixed_structure_and_floating_aid_models",
    "cite_comparison_evidence"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "single_Lighthouse_feature_assertion",
    "global_colour_codes_for_feature_binding"
  ],
  "scope_notes": [
    "Landmark/Building describe conditional structure alternatives; LightAllAround/LightSectored describe light alternatives. Listing these for explanation does not assert all must exist in one physical lighthouse.",
    "Bounded comparison: LateralBuoy is the explicitly selected representative floating-aid feature; no claim to exhaustively describe every buoy class. Compare with conditional structure/light models."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_022",
  "answer_sha256": "7733e901a5d50e0b8e8960ebcabf55cd201eff6d82413f5c85ae8dfab236f92f",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "a7310246cceeb8e0ccd4429cc68d661aa540eec88aff87db60e8d229ce80cefd",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_021 — 등대와 부표를 구분하는 S-101 근거를 알려줘.

답안 hash: `79f63162390f8be63aa3293966a3f87f7417952a5b6a84845d7913a34af26fe7`

### 실제 최종 답안
```json
{
  "answer_text": "등대와 부표는 주로 경상북도 울릉도와 경상남도 울릉군에서 구분됩니다. 이 두 지역은 경상북도와 경상남도의 경계를 이루고 있습니다. 이 지역에서는 등대와 부표의 구분이 주로 이루어져 있습니다. 이 지역에서는 등대는 주로 농업용으로 사용되며, 부표는 주로 해양 경관이나 관광용으로 사용됩니다. 이 지역에서는 등대와 부표는 주로 높이와 구조, 그리고 배치 등에 따라 구분됩니다. 이 지역에서는 등대는 높이가 높고, 부표는 높이가 낮으며, 배치는 등대보다 더 넓습니다. 이 지역에서는 등대와 부표는 주로 높이와 구조, 배치 등에 따라 구분됩니다.",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q6_02.json)
```json
{
  "case_id": "PILOT_Q6_02",
  "required_task_obligations": [
    "compare_fixed_structure_and_floating_aid_models",
    "cite_comparison_evidence"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "single_Lighthouse_feature_assertion",
    "global_colour_codes_for_feature_binding"
  ],
  "scope_notes": [
    "Landmark/Building describe conditional structure alternatives; LightAllAround/LightSectored describe light alternatives. Listing these for explanation does not assert all must exist in one physical lighthouse.",
    "Bounded comparison: LateralBuoy is the explicitly selected representative floating-aid feature; no claim to exhaustively describe every buoy class. Compare with conditional structure/light models."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_021",
  "answer_sha256": "79f63162390f8be63aa3293966a3f87f7417952a5b6a84845d7913a34af26fe7",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "a05857e4360459d5be76998ded541f5d0de2937b2905383a28e725a49d4f4d2f",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_020 — 독도 부근에서 가장 가까운 등대를 찾아줘.

답안 hash: `31f602f768dd67bece45b5262ce72f3ee4cd3867cf37b49654bae7f236eaf685`

### 실제 최종 답안
```json
{
  "document_answer": {
    "features": [],
    "attribute_bindings": []
  },
  "search_executed": false,
  "execution_status": "BLOCKED",
  "source_coverage": {},
  "per_task_status": {},
  "mapping_provenance": {
    "version": "emitted_output_v1",
    "root": "final_state.final_dict",
    "retrieved_text_used_as_answer": false,
    "reference_used_for_mapping": false,
    "structured_document_answer_present": false
  },
  "status": "BLOCKED",
  "blocker": "UNSUPPORTED_OPERATOR",
  "clarification_request": [],
  "answer_text": "최근접 객체 검색 요청으로 이해했습니다. 현재 선택된 실행 경로는 반경 검색만 지원하므로 실행하지 않았습니다. 최근접 요청을 반경 검색으로 바꾸거나 검색 반경을 요구하지 않습니다."
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q3_01.json)
```json
{
  "case_id": "PILOT_Q3_01",
  "required_task_obligations": [
    "resolve_reference",
    "resolve_lighthouse_target_conditions",
    "verify_coverage",
    "find_nearest",
    "report_objects_or_unresolved_reason"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "User-approved source-bound safe abstention; document explanations are separately evaluated optional partial output."
  ],
  "expected_spatial_behavior": {
    "accepted_states": [
      "BLOCKED_DATA",
      "DATA_OUT_OF_SCOPE"
    ],
    "required_disclosure": "Current connected snapshot cannot determine the answer for the requested spatial extent",
    "per_target": {
      "Lighthouse": {
        "status": "BLOCKED_DATA",
        "object_ids": null
      }
    },
    "empty_result_as_answer_forbidden": true,
    "claim_spatial_success_forbidden": true
  }
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_020",
  "answer_sha256": "31f602f768dd67bece45b5262ce72f3ee4cd3867cf37b49654bae7f236eaf685",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "633e48cb07edf1b812580f7f78d6e11fdca189a0619ed38a4b8112a72ae4fcf9",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_019 — Which attributes describe a Wreck in S-101?

답안 hash: `3ca1c6f0ab68e6a612f8680f13154be520fd4ff66a4a2f771f14222c113b8e51`

### 실제 최종 답안
```json
{
  "answer_text": "The attributes that describe a wreck in S-101 are: height, expositionOfSounding, and qualityOfVerticalMeasurement.",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q2_03.json)
```json
{
  "case_id": "PILOT_Q2_03",
  "required_task_obligations": [
    "explain_wreck_attribute_bindings"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_019",
  "answer_sha256": "3ca1c6f0ab68e6a612f8680f13154be520fd4ff66a4a2f771f14222c113b8e51",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "1ed47b1cf5f3e887a7b87b1de3c6ceb26eeba7c49eb21ea83f08d146989ea44f",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_018 — 부산항 주변 2km의 정박지와 제한구역을 찾아 비교해줘.

답안 hash: `c9ad70755cc8273fff56ccb98f159a507f106711d3a47ac48ea9f550bf3a6d1a`

### 실제 최종 답안
```json
{
  "answer_text": "The search results for 'port', 'dock', and 'shipyard' within 2km of Busan Port are as follows:",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "validator_blockers": [
    "BLOCKED_DATA: public catalogue document evidence unavailable",
    "BLOCKED_DATA: public catalogue document evidence unavailable",
    "BLOCKED_DATA: public catalogue document evidence unavailable"
  ],
  "status": "BLOCKED_DATA",
  "execution_status": "BLOCKED_DATA",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q5_02.json)
```json
{
  "case_id": "PILOT_Q5_02",
  "required_task_obligations": [
    "resolve_reference",
    "verify_both_target_coverages",
    "search_both_targets_2000m",
    "compare_target_results",
    "disclose_subset_limitations"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "Object IDs refer to frozen snapshot records, not deduplicated physical facilities or the whole legal port."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_018",
  "answer_sha256": "c9ad70755cc8273fff56ccb98f159a507f106711d3a47ac48ea9f550bf3a6d1a",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "f89dce42f51d9d2e1d1cbb5bfe1a9238fbc025d0cc7193da3ca86f55af5660c4",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_017 — 독도 주변 5km의 등대와 난파선을 찾아 각각의 근거를 알려줘.

답안 hash: `bbe2c8a285aff6ced66af61bec472381c03738adf10d25017a67c7e81a91014f`

### 실제 최종 답안
```json
{
  "answer_text": "The lighthouse and naval wreckage within 5km of Dokdo are as follows:\n\nLighthouse: Dokdo Lighthouse\n\nNaval Wreckage: Wrecked Submarine Dokdo-1\n\nThese features are within the specified radius and are located near the Dokdo island.",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q5_01.json)
```json
{
  "case_id": "PILOT_Q5_01",
  "required_task_obligations": [
    "resolve_reference",
    "resolve_lighthouse_target_conditions",
    "verify_both_target_coverages",
    "search_both_targets_5000m",
    "provide_per_target_evidence",
    "separate_partial_document_answer"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "User-approved source-bound safe abstention; document explanations are separately evaluated optional partial output."
  ],
  "expected_spatial_behavior": {
    "accepted_states": [
      "BLOCKED_DATA",
      "DATA_OUT_OF_SCOPE"
    ],
    "required_disclosure": "Current connected snapshot cannot determine the answer for the requested spatial extent",
    "per_target": {
      "Lighthouse": {
        "status": "BLOCKED_DATA",
        "object_ids": null
      },
      "Wreck": {
        "status": "BLOCKED_DATA",
        "object_ids": null
      }
    },
    "empty_result_as_answer_forbidden": true,
    "claim_spatial_success_forbidden": true
  }
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_017",
  "answer_sha256": "bbe2c8a285aff6ced66af61bec472381c03738adf10d25017a67c7e81a91014f",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "151447ff8aaf062b3cb7abd04b9faca70af2cb1b9dc4b5169d8447a97529b81e",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_016 — 독도 부근에서 가장 가까운 등대를 찾아줘.

답안 hash: `22266b9326a54875c0dc6b67b95fd5317cd22d2b7afea63f05efe3a65b1d7ba8`

### 실제 최종 답안
```json
{
  "answer_text": "The nearest lighthouse to Dokdo is located in Busan, Korea.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "status": "COMPLETED",
  "execution_status": "COMPLETED",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q3_01.json)
```json
{
  "case_id": "PILOT_Q3_01",
  "required_task_obligations": [
    "resolve_reference",
    "resolve_lighthouse_target_conditions",
    "verify_coverage",
    "find_nearest",
    "report_objects_or_unresolved_reason"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "User-approved source-bound safe abstention; document explanations are separately evaluated optional partial output."
  ],
  "expected_spatial_behavior": {
    "accepted_states": [
      "BLOCKED_DATA",
      "DATA_OUT_OF_SCOPE"
    ],
    "required_disclosure": "Current connected snapshot cannot determine the answer for the requested spatial extent",
    "per_target": {
      "Lighthouse": {
        "status": "BLOCKED_DATA",
        "object_ids": null
      }
    },
    "empty_result_as_answer_forbidden": true,
    "claim_spatial_success_forbidden": true
  }
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_016",
  "answer_sha256": "22266b9326a54875c0dc6b67b95fd5317cd22d2b7afea63f05efe3a65b1d7ba8",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "9b6e0d3395602f252bf55c9ae289c8b97d4dcc7b084de95c5eb8ac02cae5d5d4",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_015 — What source supports the S-101 definition of AnchorageArea?

답안 hash: `6dec9f632954b4aa12a604dc8f007d795eb747e4762fe03ac72fed97ea518dcb`

### 실제 최종 답안
```json
{
  "answer_text": "The S-101 definition of AnchorageArea is supported by the source 's101_feature_catalogue_v2'.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "document_answer": {
    "features": [
      {
        "code": "AnchorageArea",
        "xml_type": "S100_FC_FeatureType",
        "definition": "An area in which vessels or seaplanes anchor or may anchor.",
        "permitted_primitives": [
          "point",
          "surface"
        ],
        "bindings": [
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "categoryOfAnchorage"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [
              "1",
              "2",
              "3",
              "5",
              "6",
              "7",
              "9",
              "10",
              "14",
              "15"
            ],
            "xml_child_index": 5
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "categoryOfCargo"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [
              "1",
              "2",
              "3",
              "4",
              "5",
              "6",
              "7",
              "8",
              "9",
              "10",
              "11",
              "12",
              "13",
              "14",
              "15"
            ],
            "xml_child_index": 6
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "featureName"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [],
            "xml_child_index": 7
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "fixedDateRange"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 8
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "interoperabilityIdentifier"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 9
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "periodicDateRange"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [],
            "xml_child_index": 10
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "restriction"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [
              "2",
              "3",
              "4",
              "5",
              "6",
              "8",
              "9",
              "10",
              "11",
              "12",
              "13",
              "15",
              "16",
              "17",
              "18",
              "19",
              "20",
              "21",
              "23",
              "24",
              "27",
              "39"
            ],
            "xml_child_index": 11
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "status"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [
              "1",
              "2",
              "3",
              "5",
              "6",
              "7",
              "8",
              "9",
              "14"
            ],
            "xml_child_index": 12
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "vesselSpeedLimit"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [],
            "xml_child_index": 13
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "scaleMinimum"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 14
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "information"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [],
            "xml_child_index": 15
          },
          {
            "kind": "informationBinding",
            "references": [
              {
                "type": "association",
                "ref": "AdditionalInformation"
              },
              {
                "type": "role",
                "ref": "theInformation"
              },
              {
                "type": "informationType",
                "ref": "ContactDetails"
              },
              {
                "type": "informationType",
                "ref": "NauticalInformation"
              },
              {
                "type": "informationType",
                "ref": "NonStandardWorkingDay"
              },
              {
                "type": "informationType",
                "ref": "ServiceHours"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 16
          },
          {
            "kind": "featureBinding",
            "references": [
              {
                "type": "association",
                "ref": "UpdatedInformation"
              },
              {
                "type": "role",
                "ref": "theUpdate"
              },
              {
                "type": "featureType",
                "ref": "UpdateInformation"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [],
            "xml_child_index": 18
          },
          {
            "kind": "featureBinding",
            "references": [
              {
                "type": "association",
                "ref": "TextAssociation"
              },
              {
                "type": "role",
                "ref": "theCartographicText"
              },
              {
                "type": "featureType",
                "ref": "TextPlacement"
              }
            ],
            "lower": "0",
            "upper": "2",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 19
          }
        ],
        "listed_values": [],
        "version": "2.0.0",
        "source_status": "VERIFIED_XML_EXTRACTION",
        "source_path": "D:\\An_GeoLLM\\outputs\\staging\\s101_feature_catalogue_2_0_0\\S-101\\CATALOGUES\\101_Feature_Catalogue_2.0.0.xml",
        "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "parsed_locator": "/features/126",
        "definition_sha256": "753f012b09c246632a2119c4bbb9faa77ccf966debb2b48d33c26b5c72799a31",
        "xml_element_serialized_sha256": "39334abca32051a75717cd5a450f95388705644972727ac611e4cec8eb1fae9d",
        "element_hash_serialization": "xml.etree.ElementTree serialization; not a raw byte slice"
      }
    ],
    "attribute_bindings": [
      {
        "owner": "AnchorageArea",
        "attribute": "categoryOfAnchorage",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [
          "1",
          "2",
          "3",
          "5",
          "6",
          "7",
          "9",
          "10",
          "14",
          "15"
        ],
        "attribute_definition": "Classification of an area where different use types of vessel can remain static.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Unrestricted Anchorage",
            "definition": "An area in which vessels anchor or may anchor."
          },
          {
            "value": "2",
            "label": "Deep Water Anchorage",
            "definition": "An area in which vessels of deep draught anchor or may anchor."
          },
          {
            "value": "3",
            "label": "Tanker Anchorage",
            "definition": "An area in which tankers anchor or may anchor."
          },
          {
            "value": "5",
            "label": "Quarantine Anchorage",
            "definition": "An area where a vessel anchors when satisfying quarantine regulations."
          },
          {
            "value": "6",
            "label": "Seaplane Anchorage",
            "definition": "An area in which seaplanes anchor or may anchor."
          },
          {
            "value": "7",
            "label": "Small Craft Anchorage",
            "definition": "An area in which yachts and small boats anchor or may anchor."
          },
          {
            "value": "9",
            "label": "Anchorage for Periods Up To 24 Hours",
            "definition": "An area in which vessels anchor or may anchor for periods of up to 24 hours."
          },
          {
            "value": "10",
            "label": "Anchorage for a Limited Period of Time",
            "definition": "An area in which vessels may anchor for a period of time not to exceed a specific limit."
          },
          {
            "value": "14",
            "label": "Waiting Anchorage",
            "definition": "An area in which vessels anchor or may anchor while waiting, for example, for access to a port or berth."
          },
          {
            "value": "15",
            "label": "Reported Anchorage",
            "definition": "A location not defined by a regulatory authority that has been reported to be suitable and safe for anchoring."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='categoryOfAnchorage']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "categoryOfCargo",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [
          "1",
          "2",
          "3",
          "4",
          "5",
          "6",
          "7",
          "8",
          "9",
          "10",
          "11",
          "12",
          "13",
          "14",
          "15"
        ],
        "attribute_definition": "Classification of the different types of cargo that a ship may be carrying.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Bulk",
            "definition": "Unpacked homogenous cargo poured loose in a certain space of a vessel, for example oil or grain."
          },
          {
            "value": "2",
            "label": "Container",
            "definition": "One of a number of standard sized cargo carrying units, secured using standard corner attachments and bar."
          },
          {
            "value": "3",
            "label": "General",
            "definition": "Break bulk cargo normally loaded by crane."
          },
          {
            "value": "4",
            "label": "Liquid",
            "definition": "Any cargo loaded by pipeline."
          },
          {
            "value": "5",
            "label": "Passenger",
            "definition": "A fee paying traveller."
          },
          {
            "value": "6",
            "label": "Livestock",
            "definition": "Live animals carried in bulk."
          },
          {
            "value": "7",
            "label": "Dangerous or Hazardous",
            "definition": "Dangerous or hazardous cargo as described by the IMO International Maritime Dangerous Goods code."
          },
          {
            "value": "8",
            "label": "Heavy Lift",
            "definition": "Indivisible heavy items of weight generally over 100 tons, and width or height greater than 100 metres."
          },
          {
            "value": "9",
            "label": "Ballast",
            "definition": "Material carried by a ship to ensure its stability."
          },
          {
            "value": "10",
            "label": "Dry Bulk Cargo",
            "definition": "Commodity cargo that is transported unpackaged in large quantities. These types of goods usually need to be kept dry during the whole transportation period."
          },
          {
            "value": "11",
            "label": "Liquid Bulk Cargo",
            "definition": "Liquids or gases that are transported in bulk and carried unpackaged."
          },
          {
            "value": "12",
            "label": "Reefer Container Cargo",
            "definition": "Cargo transported in refrigerated containers, generally perishable commodities which require temperature-controlled transportation, such as fruit, meat, fish, vegetables, dairy products and other foods."
          },
          {
            "value": "13",
            "label": "Ro-Ro Cargo",
            "definition": "Wheeled cargo, such as cars, busses, trucks, agricultural vehicles and cranes, that are driven on and off the ship on their own wheels or using a platform vehicle, such as a self-propelled modular transporter."
          },
          {
            "value": "14",
            "label": "Project Cargo",
            "definition": "Project cargo is a term used to broadly describe the national or international transportation of large, heavy, high value, or critical (to the project they are intended for) pieces of equipment. Also commonly referred to as heavy lift, this includes shipments made of various components which need disassembly for shipment and reassembly after delivery."
          },
          {
            "value": "15",
            "label": "Break Bulk Cargo",
            "definition": "Goods that are stowed on board ship in individually counted units, and not in intermodal containers nor in bulk as with oil or grain."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='categoryOfCargo']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "featureName",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [],
        "attribute_definition": "Provides the name of an entity, defines the national language of the name, and provides the option to display the name at various system display settings.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='featureName']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "fixedDateRange",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "An active period of a single fixed event or occurrence, as the date range between discrete start and end dates.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='fixedDateRange']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "interoperabilityIdentifier",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "A common unique identifier for entities which describe a single real-world feature, and which is used to identify instances of the feature in end-user systems where the feature may be included in multiple data product types.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='interoperabilityIdentifier']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "periodicDateRange",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [],
        "attribute_definition": "The active period of a recurring event or occurrence.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='periodicDateRange']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "restriction",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [
          "2",
          "3",
          "4",
          "5",
          "6",
          "8",
          "9",
          "10",
          "11",
          "12",
          "13",
          "15",
          "16",
          "17",
          "18",
          "19",
          "20",
          "21",
          "23",
          "24",
          "27",
          "39"
        ],
        "attribute_definition": "The official legal statute of each kind of restricted area.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Anchoring Prohibited",
            "definition": "An area within which anchoring is not permitted."
          },
          {
            "value": "2",
            "label": "Anchoring Restricted",
            "definition": "A specified area designated by appropriate authority, within which anchoring is restricted in accordance with certain specified conditions."
          },
          {
            "value": "3",
            "label": "Fishing Prohibited",
            "definition": "An area within which fishing is not permitted."
          },
          {
            "value": "4",
            "label": "Fishing Restricted",
            "definition": "A specified area designated by appropriate authority, within which fishing is restricted in accordance with certain specified conditions."
          },
          {
            "value": "5",
            "label": "Trawling Prohibited",
            "definition": "An area within which trawling is not permitted."
          },
          {
            "value": "6",
            "label": "Trawling Restricted",
            "definition": "A specified area designated by appropriate authority, within which trawling is restricted in accordance with certain specified conditions."
          },
          {
            "value": "7",
            "label": "Entry Prohibited",
            "definition": "An area within which navigation and/or anchoring is prohibited."
          },
          {
            "value": "8",
            "label": "Entry Restricted",
            "definition": "A specified area designated by appropriate authority, within which navigation is restricted in accordance with certain specified conditions."
          },
          {
            "value": "9",
            "label": "Dredging Prohibited",
            "definition": "An area within which dredging is not permitted."
          },
          {
            "value": "10",
            "label": "Dredging Restricted",
            "definition": "A specified area designated by appropriate authority, within which dredging is restricted in accordance with certain specified conditions."
          },
          {
            "value": "11",
            "label": "Diving Prohibited",
            "definition": "An area within which diving is not permitted."
          },
          {
            "value": "12",
            "label": "Diving Restricted",
            "definition": "A specified area designated by appropriate authority, within which diving is restricted in accordance with certain specified conditions."
          },
          {
            "value": "13",
            "label": "No Wake",
            "definition": "Mariners must adjust the speed of their vessels to reduce the wave or wash which may cause erosion or disturb moored vessels."
          },
          {
            "value": "14",
            "label": "Area To Be Avoided",
            "definition": "An IMO declared routeing measure comprising an area within defined limits in which either navigation is particularly hazardous or it is exceptionally important to avoid casualties and which should be avoided by all ships, or certain classes of ships."
          },
          {
            "value": "15",
            "label": "Construction Prohibited",
            "definition": "The erection of permanent or temporary fixed structures or artificial islands is prohibited."
          },
          {
            "value": "16",
            "label": "Discharging Prohibited",
            "definition": "An area within which discharging or dumping is prohibited."
          },
          {
            "value": "17",
            "label": "Discharging Restricted",
            "definition": "A specified area designated by an appropriate authority, within which discharging or dumping is restricted in accordance with specified conditions."
          },
          {
            "value": "18",
            "label": "Industrial or Mineral Exploration/Development Prohibited",
            "definition": "An area within which industrial or mineral exploration and development are prohibited."
          },
          {
            "value": "19",
            "label": "Industrial or Mineral Exploration/Development Restricted",
            "definition": "A specified area designated by an appropriate authority, within which industrial or mineral exploration and development is restricted in accordance with certain specified conditions."
          },
          {
            "value": "20",
            "label": "Drilling Prohibited",
            "definition": "An area within which excavating a hole on the seabed with a drill is prohibited."
          },
          {
            "value": "21",
            "label": "Drilling Restricted",
            "definition": "A specified area designated by an appropriate authority, within which excavating a hole on the seabed with a drill is restricted in accordance with certain specified conditions."
          },
          {
            "value": "22",
            "label": "Removal of Historical Artefacts Prohibited",
            "definition": "An area within which the removal of historical artefacts is prohibited."
          },
          {
            "value": "23",
            "label": "Cargo Transhipment (Lightening) Prohibited",
            "definition": "An area in which cargo transhipment (lightening) is prohibited."
          },
          {
            "value": "24",
            "label": "Dragging Prohibited",
            "definition": "An area in which the dragging of anything along the seabed, for example bottom trawling, is prohibited."
          },
          {
            "value": "25",
            "label": "Stopping Prohibited",
            "definition": "An area in which a vessel is prohibited from stopping."
          },
          {
            "value": "26",
            "label": "Landing Prohibited",
            "definition": "An area in which landing is prohibited."
          },
          {
            "value": "27",
            "label": "Speed Restricted",
            "definition": "An area within which speed is restricted."
          },
          {
            "value": "39",
            "label": "Swimming Prohibited",
            "definition": "An area in which swimming is prohibited."
          },
          {
            "value": "42",
            "label": "Power-Driven Vessels Prohibited",
            "definition": "An area within which any vessel propelled by machinery is prohibited."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='restriction']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "status",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [
          "1",
          "2",
          "3",
          "5",
          "6",
          "7",
          "8",
          "9",
          "14"
        ],
        "attribute_definition": "The condition of an object at a given instant in time.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Permanent",
            "definition": "Intended to last or function indefinitely."
          },
          {
            "value": "2",
            "label": "Occasional",
            "definition": "Acting on special occasions; happening irregularly."
          },
          {
            "value": "3",
            "label": "Recommended",
            "definition": "Presented as worthy of confidence, acceptance, use, etc."
          },
          {
            "value": "4",
            "label": "Not in Use",
            "definition": "Use has ceased, but the facility still exists intact; disused."
          },
          {
            "value": "5",
            "label": "Periodic/Intermittent",
            "definition": "Recurring at intervals."
          },
          {
            "value": "6",
            "label": "Reserved",
            "definition": "Set apart for some specific use."
          },
          {
            "value": "7",
            "label": "Temporary",
            "definition": "Meant to last only for a time."
          },
          {
            "value": "8",
            "label": "Private",
            "definition": "Administered by an individual or corporation, rather than a State or a public body."
          },
          {
            "value": "9",
            "label": "Mandatory",
            "definition": "Compulsory; enforced."
          },
          {
            "value": "11",
            "label": "Extinguished",
            "definition": "No longer lit."
          },
          {
            "value": "12",
            "label": "Illuminated",
            "definition": "Lit by flood lights, strip lights, etc."
          },
          {
            "value": "13",
            "label": "Historic",
            "definition": "Famous in history; of historical interest."
          },
          {
            "value": "14",
            "label": "Public",
            "definition": "Belonging to, available to, used or shared by, the community as a whole and not restricted to private use."
          },
          {
            "value": "15",
            "label": "Synchronized",
            "definition": "Occur at a time, coincide in point of time, be contemporary or simultaneous."
          },
          {
            "value": "16",
            "label": "Watched",
            "definition": "Looked at or observed over a period of time especially so as to be aware of any movement or change."
          },
          {
            "value": "17",
            "label": "Unwatched",
            "definition": "Usually automatic in operation, without any permanently-stationed personnel to superintend it."
          },
          {
            "value": "18",
            "label": "Existence Doubtful",
            "definition": "A feature that has been reported but has not been definitely determined to exist."
          },
          {
            "value": "28",
            "label": "Buoyed",
            "definition": "Marked by buoys."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='status']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "vesselSpeedLimit",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [],
        "attribute_definition": "The maximum allowed rate of travel for a vessel in an area in knots.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='vesselSpeedLimit']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "scaleMinimum",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The minimum scale at which the feature may be used for example for ECDIS presentation.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='scaleMinimum']]"
      },
      {
        "owner": "AnchorageArea",
        "attribute": "information",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [],
        "attribute_definition": "Textual information about the feature. The information may be provided as a string of text or as a file name of a single external text file that contains the text.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]"
      },
      {
        "owner": "featureName",
        "attribute": "language",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The method of human communication, either spoken or written, consisting of the use of words in a structured and conventional way.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='featureName']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='language']]"
      },
      {
        "owner": "featureName",
        "attribute": "name",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The individual name of a feature.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='featureName']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='name']]"
      },
      {
        "owner": "featureName",
        "attribute": "nameUsage",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [
          "1",
          "2"
        ],
        "attribute_definition": "Classification of the type and display level of the name of a feature in an end-user system.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Default Name Display",
            "definition": "The name is intended to be displayed when the end-user system is set to the default name/text display setting."
          },
          {
            "value": "2",
            "label": "Alternate Name Display",
            "definition": "The name is intended to be displayed when the end-user system is set to an alternate name/text display setting, for example an alternate language."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='featureName']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='nameUsage']]"
      },
      {
        "owner": "fixedDateRange",
        "attribute": "dateEnd",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The latest date on which an object (for example a buoy) will be present.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='fixedDateRange']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='dateEnd']]"
      },
      {
        "owner": "fixedDateRange",
        "attribute": "dateStart",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The earliest date on which an object (for example a buoy) will be present.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='fixedDateRange']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='dateStart']]"
      },
      {
        "owner": "periodicDateRange",
        "attribute": "dateEnd",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The latest date on which an object (for example a buoy) will be present.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='periodicDateRange']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='dateEnd']]"
      },
      {
        "owner": "periodicDateRange",
        "attribute": "dateStart",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The earliest date on which an object (for example a buoy) will be present.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='periodicDateRange']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='dateStart']]"
      },
      {
        "owner": "vesselSpeedLimit",
        "attribute": "speedLimit",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The maximum allowed rate of travel in an area.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='vesselSpeedLimit']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='speedLimit']]"
      },
      {
        "owner": "vesselSpeedLimit",
        "attribute": "speedUnits",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [
          "2",
          "3",
          "4"
        ],
        "attribute_definition": "The units for description of speed.",
        "global_listed_values": [
          {
            "value": "2",
            "label": "Kilometres Per Hour",
            "definition": "A unit of speed, expressing the number of kilometres travelled in one hour."
          },
          {
            "value": "3",
            "label": "Miles Per Hour",
            "definition": "An imperial and United States customary unit of speed expressing the number of statute miles covered in one hour."
          },
          {
            "value": "4",
            "label": "Knots",
            "definition": "A nautical unit of speed. One knot is one nautical mile per hour. The name is derived from the knots in the log line."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='vesselSpeedLimit']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='speedUnits']]"
      },
      {
        "owner": "vesselSpeedLimit",
        "attribute": "vesselClass",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The classification of a vessel, normally as defined by length or gross tonnage.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='vesselSpeedLimit']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='vesselClass']]"
      },
      {
        "owner": "information",
        "attribute": "fileLocator",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The location of a fragment of text or other information in a support file.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='fileLocator']]"
      },
      {
        "owner": "information",
        "attribute": "fileReference",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The file name of an externally referenced text file.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='fileReference']]"
      },
      {
        "owner": "information",
        "attribute": "headline",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "Words set at the head of a passage or page to introduce or categorize.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='headline']]"
      },
      {
        "owner": "information",
        "attribute": "language",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The method of human communication, either spoken or written, consisting of the use of words in a structured and conventional way.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='language']]"
      },
      {
        "owner": "information",
        "attribute": "text",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "A non-formatted digital text string.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='text']]"
      }
    ],
    "evidence": {
      "edition": "2.0.0",
      "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
      "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
      "locators": [
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]"
      ],
      "claim_source_links": [
        {
          "feature_code": "AnchorageArea",
          "definition_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
          "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc"
        }
      ]
    },
    "definition_quote": "An area in which vessels or seaplanes anchor or may anchor."
  },
  "status": "COMPLETED",
  "execution_status": "COMPLETED",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q6_03.json)
```json
{
  "case_id": "PILOT_Q6_03",
  "required_task_obligations": [
    "provide_anchorage_definition_source",
    "cite_catalogue_edition_and_locator"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_015",
  "answer_sha256": "6dec9f632954b4aa12a604dc8f007d795eb747e4762fe03ac72fed97ea518dcb",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "020949eb3c39c887d7f25f93595a3eff135e766e70e54dcee96f1ec78f5ecf34",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_014 — Find wrecks within 5 km of Dokdo and explain their S-101 attributes.

답안 hash: `67d4c6a0708ce78256fa49d55722aad059ecc041dd90c070e49d300becfeed21`

### 실제 최종 답안
```json
{
  "answer_text": "The wrecks within 5 km of Dokdo are not found in the S-101 feature catalogue.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "validator_blockers": [
    "BLOCKED_DATA: public catalogue document evidence unavailable"
  ],
  "status": "BLOCKED_DATA",
  "execution_status": "BLOCKED_DATA",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q5_03.json)
```json
{
  "case_id": "PILOT_Q5_03",
  "required_task_obligations": [
    "resolve_reference",
    "verify_coverage",
    "search_wrecks_5000m",
    "explain_s101_attributes",
    "distinguish_object_values_from_standard_attributes",
    "separate_partial_document_answer"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "User-approved source-bound safe abstention; document explanations are separately evaluated optional partial output."
  ],
  "expected_spatial_behavior": {
    "accepted_states": [
      "BLOCKED_DATA",
      "DATA_OUT_OF_SCOPE"
    ],
    "required_disclosure": "Current connected snapshot cannot determine the answer for the requested spatial extent",
    "per_target": {
      "Wreck": {
        "status": "BLOCKED_DATA",
        "object_ids": null
      }
    },
    "empty_result_as_answer_forbidden": true,
    "claim_spatial_success_forbidden": true
  }
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_014",
  "answer_sha256": "67d4c6a0708ce78256fa49d55722aad059ecc041dd90c070e49d300becfeed21",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "76cf9aaa21c37bf165622d6b720c7d737fe67b57ad82afeb36733acd86afe57e",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_013 — 등대의 S-101 객체 유형과 정의를 알려줘.

답안 hash: `a1161ba0fa61d54fd5f784a1ffe098fa815d324473ee658dce5a19112acb4d93`

### 실제 최종 답안
```json
{
  "answer_text": "등대는 S-101 객체 중 하나입니다. 이 객체는 등대의 정의와 유형을 나타냅니다. S-101는 등대의 공통적인 객체 코드입니다.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "document_answer": {
    "features": [],
    "attribute_bindings": [],
    "evidence": {
      "edition": "2.0.0",
      "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
      "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
      "locators": [],
      "claim_source_links": []
    }
  },
  "status": "COMPLETED",
  "execution_status": "COMPLETED",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q1_01.json)
```json
{
  "case_id": "PILOT_Q1_01",
  "required_task_obligations": [
    "explain_structure_and_light_distinction",
    "explain_conditional_feature_mapping"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "single_Lighthouse_feature_assertion",
    "global_colour_codes_for_feature_binding"
  ],
  "scope_notes": [
    "Landmark/Building describe conditional structure alternatives; LightAllAround/LightSectored describe light alternatives. Listing these for explanation does not assert all must exist in one physical lighthouse."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_013",
  "answer_sha256": "a1161ba0fa61d54fd5f784a1ffe098fa815d324473ee658dce5a19112acb4d93",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "bde88339be42b11a715ecec46e7c3cb8626d0db152e74c2a28cd263973b61743",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_012 — Which attributes describe a Wreck in S-101?

답안 hash: `8b8a932925297a0bc10511c42911f6a60a517f18015fc476e50ada070725d41b`

### 실제 최종 답안
```json
{
  "answer_text": "A wreck is described in S-101, located within the scope of the S-101 feature catalogue.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "document_answer": {
    "features": [
      {
        "code": "Wreck",
        "xml_type": "S100_FC_FeatureType",
        "definition": "The ruined remains of a stranded or sunken vessel which has been rendered useless.",
        "permitted_primitives": [
          "point",
          "surface"
        ],
        "bindings": [
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "categoryOfWreck"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [
              "1",
              "2",
              "3",
              "4",
              "5"
            ],
            "xml_child_index": 5
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "expositionOfSounding"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [
              "1",
              "2",
              "3"
            ],
            "xml_child_index": 6
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "featureName"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [],
            "xml_child_index": 7
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "height"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 8
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "interoperabilityIdentifier"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 9
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "qualityOfVerticalMeasurement"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [
              "1",
              "2",
              "3",
              "4",
              "6",
              "7",
              "8",
              "9"
            ],
            "xml_child_index": 10
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "radarConspicuous"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 11
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "reportedDate"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 12
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "status"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [
              "7",
              "13",
              "18"
            ],
            "xml_child_index": 13
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "techniqueOfVerticalMeasurement"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [
              "1",
              "2",
              "3",
              "4",
              "5",
              "8",
              "9",
              "10",
              "11",
              "12",
              "13",
              "15",
              "16",
              "17",
              "18"
            ],
            "xml_child_index": 14
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "valueOfSounding"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 15
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "visualProminence"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [
              "1",
              "2",
              "3"
            ],
            "xml_child_index": 16
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "waterLevelEffect"
              }
            ],
            "lower": "1",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [
              "1",
              "2",
              "3",
              "4",
              "5"
            ],
            "xml_child_index": 17
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "scaleMinimum"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 18
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "information"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [],
            "xml_child_index": 19
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "pictorialRepresentation"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 20
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "defaultClearanceDepth"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 21
          },
          {
            "kind": "attributeBinding",
            "references": [
              {
                "type": "attribute",
                "ref": "surroundingDepth"
              }
            ],
            "lower": "1",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 22
          },
          {
            "kind": "informationBinding",
            "references": [
              {
                "type": "association",
                "ref": "AdditionalInformation"
              },
              {
                "type": "role",
                "ref": "theInformation"
              },
              {
                "type": "informationType",
                "ref": "NauticalInformation"
              }
            ],
            "lower": "0",
            "upper": "1",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 23
          },
          {
            "kind": "featureBinding",
            "references": [
              {
                "type": "association",
                "ref": "StructureEquipment"
              },
              {
                "type": "role",
                "ref": "theEquipment"
              },
              {
                "type": "featureType",
                "ref": "Daymark"
              },
              {
                "type": "featureType",
                "ref": "DistanceMark"
              },
              {
                "type": "featureType",
                "ref": "FogSignal"
              },
              {
                "type": "featureType",
                "ref": "LightAllAround"
              },
              {
                "type": "featureType",
                "ref": "LightFogDetector"
              },
              {
                "type": "featureType",
                "ref": "PhysicalAISAidToNavigation"
              },
              {
                "type": "featureType",
                "ref": "RadarTransponderBeacon"
              },
              {
                "type": "featureType",
                "ref": "Retroreflector"
              },
              {
                "type": "featureType",
                "ref": "SignalStationTraffic"
              },
              {
                "type": "featureType",
                "ref": "SignalStationWarning"
              },
              {
                "type": "featureType",
                "ref": "LightSectored"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [],
            "xml_child_index": 25
          },
          {
            "kind": "featureBinding",
            "references": [
              {
                "type": "association",
                "ref": "UpdatedInformation"
              },
              {
                "type": "role",
                "ref": "theUpdate"
              },
              {
                "type": "featureType",
                "ref": "UpdateInformation"
              }
            ],
            "lower": "0",
            "upper": null,
            "unbounded": true,
            "permitted_values": [],
            "xml_child_index": 26
          },
          {
            "kind": "featureBinding",
            "references": [
              {
                "type": "association",
                "ref": "TextAssociation"
              },
              {
                "type": "role",
                "ref": "theCartographicText"
              },
              {
                "type": "featureType",
                "ref": "TextPlacement"
              }
            ],
            "lower": "0",
            "upper": "2",
            "unbounded": false,
            "permitted_values": [],
            "xml_child_index": 27
          }
        ],
        "listed_values": [],
        "version": "2.0.0",
        "source_status": "VERIFIED_XML_EXTRACTION",
        "source_path": "D:\\An_GeoLLM\\outputs\\staging\\s101_feature_catalogue_2_0_0\\S-101\\CATALOGUES\\101_Feature_Catalogue_2.0.0.xml",
        "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
        "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "parsed_locator": "/features/86",
        "definition_sha256": "42995f6ea3f18e9e74fd93a554871688cc297d4440b18042e5d894f130eb971a",
        "xml_element_serialized_sha256": "1f207649d80e84625edd620051b6645d926ff8c7553be9fa868b6cf165a54177",
        "element_hash_serialization": "xml.etree.ElementTree serialization; not a raw byte slice"
      }
    ],
    "attribute_bindings": [
      {
        "owner": "Wreck",
        "attribute": "categoryOfWreck",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [
          "1",
          "2",
          "3",
          "4",
          "5"
        ],
        "attribute_definition": "Classification of a wrecked or ruined ship.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Non-Dangerous Wreck",
            "definition": "A wreck which is not considered to be dangerous to surface navigation."
          },
          {
            "value": "2",
            "label": "Dangerous Wreck",
            "definition": "A wreck submerged at such a depth as to be considered dangerous to surface navigation."
          },
          {
            "value": "3",
            "label": "Distributed Remains of Wreck",
            "definition": "A substantively decayed wreck over which it is safe to navigate but which should be avoided for anchoring, taking the ground or ground fishing."
          },
          {
            "value": "4",
            "label": "Wreck Showing Mast/Masts",
            "definition": "Wreck of which only the mast(s) is visible at the sounding datum indicated."
          },
          {
            "value": "5",
            "label": "Wreck Showing Any Portion of Hull or Superstructure",
            "definition": "Wreck of which any portion of the hull or superstructure is visible at the sounding datum indicated."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='categoryOfWreck']]"
      },
      {
        "owner": "Wreck",
        "attribute": "expositionOfSounding",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [
          "1",
          "2",
          "3"
        ],
        "attribute_definition": "Indicates the relationship of the depth of a feature to the range of depth of the surrounding depth area.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Within the Range of Depth of the Surrounding Depth Area",
            "definition": "The depth corresponds to the depth range of the surrounding depth area; that is, the depth is not shoaler than the minimum depth of the surrounding depth area or deeper than the maximum depth of the surrounding depth area."
          },
          {
            "value": "2",
            "label": "Shoaler Than the Range of Depth of the Surrounding Depth Area",
            "definition": "The depth is shoaler than the minimum depth of the surrounding depth area."
          },
          {
            "value": "3",
            "label": "Deeper Than the Range of Depth of the Surrounding Depth Area",
            "definition": "The depth is deeper than the maximum depth of the surrounding depth area."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='expositionOfSounding']]"
      },
      {
        "owner": "Wreck",
        "attribute": "featureName",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [],
        "attribute_definition": "Provides the name of an entity, defines the national language of the name, and provides the option to display the name at various system display settings.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='featureName']]"
      },
      {
        "owner": "Wreck",
        "attribute": "height",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The value of the vertical distance to the highest point of the feature, measured from a specified vertical datum.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='height']]"
      },
      {
        "owner": "Wreck",
        "attribute": "interoperabilityIdentifier",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "A common unique identifier for entities which describe a single real-world feature, and which is used to identify instances of the feature in end-user systems where the feature may be included in multiple data product types.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='interoperabilityIdentifier']]"
      },
      {
        "owner": "Wreck",
        "attribute": "qualityOfVerticalMeasurement",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [
          "1",
          "2",
          "3",
          "4",
          "6",
          "7",
          "8",
          "9"
        ],
        "attribute_definition": "The reliability of the value of a sounding.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Depth Known",
            "definition": "The depth from the chart datum to the seabed (or to the top of a drying feature) is known."
          },
          {
            "value": "2",
            "label": "Depth or Least Depth Unknown",
            "definition": "The depth from chart datum to the seabed, or the shoalest depth of the feature is unknown."
          },
          {
            "value": "3",
            "label": "Doubtful Sounding",
            "definition": "A depth that may be less than indicated."
          },
          {
            "value": "4",
            "label": "Unreliable Sounding",
            "definition": "A depth that is considered to be an unreliable value."
          },
          {
            "value": "6",
            "label": "Least Depth Known",
            "definition": "The shoalest depth over a feature is of known value."
          },
          {
            "value": "7",
            "label": "Least Depth Unknown, Safe Clearance at Value Shown",
            "definition": "The least depth over a feature is unknown, but there is considered to be safe clearance at this depth."
          },
          {
            "value": "8",
            "label": "Value Reported (Not Surveyed)",
            "definition": "Depth value obtained from a report, but not fully surveyed."
          },
          {
            "value": "9",
            "label": "Value Reported (Not Confirmed)",
            "definition": "Depth value obtained from a report, which it has not been possible to confirm."
          },
          {
            "value": "10",
            "label": "Maintained Depth",
            "definition": "The depth at which a channel is kept by human influence, usually by dredging."
          },
          {
            "value": "11",
            "label": "Not Regularly Maintained",
            "definition": "Depths may be altered by human influence, but will not be routinely maintained."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='qualityOfVerticalMeasurement']]"
      },
      {
        "owner": "Wreck",
        "attribute": "radarConspicuous",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "A feature which returns a strong radar echo.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='radarConspicuous']]"
      },
      {
        "owner": "Wreck",
        "attribute": "reportedDate",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The date that the item was observed, done, or investigated.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='reportedDate']]"
      },
      {
        "owner": "Wreck",
        "attribute": "status",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [
          "7",
          "13",
          "18"
        ],
        "attribute_definition": "The condition of an object at a given instant in time.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Permanent",
            "definition": "Intended to last or function indefinitely."
          },
          {
            "value": "2",
            "label": "Occasional",
            "definition": "Acting on special occasions; happening irregularly."
          },
          {
            "value": "3",
            "label": "Recommended",
            "definition": "Presented as worthy of confidence, acceptance, use, etc."
          },
          {
            "value": "4",
            "label": "Not in Use",
            "definition": "Use has ceased, but the facility still exists intact; disused."
          },
          {
            "value": "5",
            "label": "Periodic/Intermittent",
            "definition": "Recurring at intervals."
          },
          {
            "value": "6",
            "label": "Reserved",
            "definition": "Set apart for some specific use."
          },
          {
            "value": "7",
            "label": "Temporary",
            "definition": "Meant to last only for a time."
          },
          {
            "value": "8",
            "label": "Private",
            "definition": "Administered by an individual or corporation, rather than a State or a public body."
          },
          {
            "value": "9",
            "label": "Mandatory",
            "definition": "Compulsory; enforced."
          },
          {
            "value": "11",
            "label": "Extinguished",
            "definition": "No longer lit."
          },
          {
            "value": "12",
            "label": "Illuminated",
            "definition": "Lit by flood lights, strip lights, etc."
          },
          {
            "value": "13",
            "label": "Historic",
            "definition": "Famous in history; of historical interest."
          },
          {
            "value": "14",
            "label": "Public",
            "definition": "Belonging to, available to, used or shared by, the community as a whole and not restricted to private use."
          },
          {
            "value": "15",
            "label": "Synchronized",
            "definition": "Occur at a time, coincide in point of time, be contemporary or simultaneous."
          },
          {
            "value": "16",
            "label": "Watched",
            "definition": "Looked at or observed over a period of time especially so as to be aware of any movement or change."
          },
          {
            "value": "17",
            "label": "Unwatched",
            "definition": "Usually automatic in operation, without any permanently-stationed personnel to superintend it."
          },
          {
            "value": "18",
            "label": "Existence Doubtful",
            "definition": "A feature that has been reported but has not been definitely determined to exist."
          },
          {
            "value": "28",
            "label": "Buoyed",
            "definition": "Marked by buoys."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='status']]"
      },
      {
        "owner": "Wreck",
        "attribute": "techniqueOfVerticalMeasurement",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [
          "1",
          "2",
          "3",
          "4",
          "5",
          "8",
          "9",
          "10",
          "11",
          "12",
          "13",
          "15",
          "16",
          "17",
          "18"
        ],
        "attribute_definition": "Survey method used to obtain depth information.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Found by Echo Sounder",
            "definition": "The depth was measured by using an instrument that determines depth of water by measuring the time interval between emission of a sonic or ultrasonic signal and return of its echo from the bottom."
          },
          {
            "value": "2",
            "label": "Found by Side Scan Sonar",
            "definition": "The depth was computed from a record produced by active sonar in which fixed acoustic beams are directed into the water perpendicularly to the direction of travel to scan the seabed and generate a record of the seabed configuration."
          },
          {
            "value": "3",
            "label": "Found by Multi Beam",
            "definition": "The depth was measured by using a wide swath echo sounder that uses multiple beams to measure depths directly below and transverse to the ship's track."
          },
          {
            "value": "4",
            "label": "Found by Diver",
            "definition": "The depth was determined by a person skilled in the practice of diving."
          },
          {
            "value": "5",
            "label": "Found by Lead Line",
            "definition": "The depth was measured by using a line, graduated with attached marks and fastened to a sounding lead."
          },
          {
            "value": "8",
            "label": "Swept by Vertical Acoustic System",
            "definition": "The given area has been swept using a system comprised of multiple echo sounder transducers attached to booms deployed from the survey vessel."
          },
          {
            "value": "9",
            "label": "Found by Electromagnetic Sensor",
            "definition": "The depth was determined by using an instrument that compares electromagnetic signals."
          },
          {
            "value": "10",
            "label": "Photogrammetry",
            "definition": "The science or art of obtaining reliable measurements from photographs."
          },
          {
            "value": "11",
            "label": "Satellite Imagery",
            "definition": "The depth was determined by using instruments placed aboard an artificial satellite."
          },
          {
            "value": "12",
            "label": "Found by Levelling",
            "definition": "The depth was determined by using levelling techniques to find the elevation of the point relative to a datum."
          },
          {
            "value": "13",
            "label": "Swept by Side Scan Sonar",
            "definition": "The given area was determined to be free from navigational dangers to a certain depth by towing a side scan sonar."
          },
          {
            "value": "15",
            "label": "Found by LIDAR",
            "definition": "The depth was measured by using an instrument that measures distance by emitting timed pulses of laser light and measuring the time between emission and reception of the reflected pulses."
          },
          {
            "value": "16",
            "label": "Synthetic Aperture Radar",
            "definition": "A radar with a synthetic aperture antenna which is composed of a large number of elementary transducing elements. The signals are electronically combined into a resulting signal equivalent to that of a single antenna of a given aperture in a given direction."
          },
          {
            "value": "17",
            "label": "Hyperspectral Imagery",
            "definition": "Term used to describe the imagery derived from subdividing the electromagnetic spectrum into very narrow bandwidths. These narrow bandwidths may be combined with or subtracted from each other in various ways to form images useful in precise terrain or target analysis."
          },
          {
            "value": "18",
            "label": "Mechanically Swept",
            "definition": "The given area was determined to be free from navigational dangers to a certain depth by towing a line or object below the surface at the desired depth; or least depth(s) and position(s) within an area was identified using the same technique."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='techniqueOfVerticalMeasurement']]"
      },
      {
        "owner": "Wreck",
        "attribute": "valueOfSounding",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The value of the measurement of a sounding relative to the chart datum.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='valueOfSounding']]"
      },
      {
        "owner": "Wreck",
        "attribute": "visualProminence",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [
          "1",
          "2",
          "3"
        ],
        "attribute_definition": "The extent to which a feature, either natural or artificial, is visible from seaward.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Visually Conspicuous",
            "definition": "Term applied to an object either natural or artificial which is distinctly and notably visible from seaward."
          },
          {
            "value": "2",
            "label": "Not Visually Conspicuous",
            "definition": "An object that may be visible from seaward, but cannot be used as a fixing mark and is not conspicuous."
          },
          {
            "value": "3",
            "label": "Prominent",
            "definition": "Objects which are easily identifiable, but do not justify being classed as conspicuous."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='visualProminence']]"
      },
      {
        "owner": "Wreck",
        "attribute": "waterLevelEffect",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [
          "1",
          "2",
          "3",
          "4",
          "5"
        ],
        "attribute_definition": "The effect of the surrounding water on an object.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Partly Submerged at High Water",
            "definition": "Partially covered and partially dry at high water."
          },
          {
            "value": "2",
            "label": "Always Dry",
            "definition": "Not covered at high water under average meteorological conditions."
          },
          {
            "value": "3",
            "label": "Always Under Water/Submerged",
            "definition": "Remains covered by water at all times under average meteorological conditions."
          },
          {
            "value": "4",
            "label": "Covers and Uncovers",
            "definition": "Expression intended to indicate an area of a reef or other projection from the bottom of a body of water which periodically extends above and is submerged below the surface. Also referred to as dries or uncovers."
          },
          {
            "value": "5",
            "label": "Awash",
            "definition": "Flush with, or washed by the waves at low water under average meteorological conditions."
          },
          {
            "value": "6",
            "label": "Subject to Inundation or Flooding",
            "definition": "An area periodically covered by flood water, excluding tidal waters."
          },
          {
            "value": "7",
            "label": "Floating",
            "definition": "Resting or moving on the surface of a liquid without sinking."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='waterLevelEffect']]"
      },
      {
        "owner": "Wreck",
        "attribute": "scaleMinimum",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The minimum scale at which the feature may be used for example for ECDIS presentation.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='scaleMinimum']]"
      },
      {
        "owner": "Wreck",
        "attribute": "information",
        "lower": "0",
        "upper": null,
        "unbounded": true,
        "permitted_values": [],
        "attribute_definition": "Textual information about the feature. The information may be provided as a string of text or as a file name of a single external text file that contains the text.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]"
      },
      {
        "owner": "Wreck",
        "attribute": "pictorialRepresentation",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The file name of an externally referenced picture file.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='pictorialRepresentation']]"
      },
      {
        "owner": "Wreck",
        "attribute": "defaultClearanceDepth",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The depth value determined for an underwater hazard of unknown depth, based on the depth of the surrounding area.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='defaultClearanceDepth']]"
      },
      {
        "owner": "Wreck",
        "attribute": "surroundingDepth",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The depth value determined for seabed around an underwater hazard, based on the depth of the surrounding area.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='surroundingDepth']]"
      },
      {
        "owner": "featureName",
        "attribute": "language",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The method of human communication, either spoken or written, consisting of the use of words in a structured and conventional way.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='featureName']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='language']]"
      },
      {
        "owner": "featureName",
        "attribute": "name",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The individual name of a feature.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='featureName']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='name']]"
      },
      {
        "owner": "featureName",
        "attribute": "nameUsage",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [
          "1",
          "2"
        ],
        "attribute_definition": "Classification of the type and display level of the name of a feature in an end-user system.",
        "global_listed_values": [
          {
            "value": "1",
            "label": "Default Name Display",
            "definition": "The name is intended to be displayed when the end-user system is set to the default name/text display setting."
          },
          {
            "value": "2",
            "label": "Alternate Name Display",
            "definition": "The name is intended to be displayed when the end-user system is set to an alternate name/text display setting, for example an alternate language."
          }
        ],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='featureName']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='nameUsage']]"
      },
      {
        "owner": "information",
        "attribute": "fileLocator",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The location of a fragment of text or other information in a support file.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='fileLocator']]"
      },
      {
        "owner": "information",
        "attribute": "fileReference",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The file name of an externally referenced text file.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='fileReference']]"
      },
      {
        "owner": "information",
        "attribute": "headline",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "Words set at the head of a passage or page to introduce or categorize.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='headline']]"
      },
      {
        "owner": "information",
        "attribute": "language",
        "lower": "1",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "The method of human communication, either spoken or written, consisting of the use of words in a structured and conventional way.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='language']]"
      },
      {
        "owner": "information",
        "attribute": "text",
        "lower": "0",
        "upper": "1",
        "unbounded": false,
        "permitted_values": [],
        "attribute_definition": "A non-formatted digital text string.",
        "global_listed_values": [],
        "owner_locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
        "attribute_locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='text']]"
      }
    ],
    "evidence": {
      "edition": "2.0.0",
      "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
      "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
      "locators": [
        "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]"
      ],
      "claim_source_links": [
        {
          "feature_code": "Wreck",
          "definition_locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
          "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc"
        }
      ]
    },
    "definition_quote": "The ruined remains of a stranded or sunken vessel which has been rendered useless."
  },
  "status": "COMPLETED",
  "execution_status": "COMPLETED",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q2_03.json)
```json
{
  "case_id": "PILOT_Q2_03",
  "required_task_obligations": [
    "explain_wreck_attribute_bindings"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_012",
  "answer_sha256": "8b8a932925297a0bc10511c42911f6a60a517f18015fc476e50ada070725d41b",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "978150fd3591138d431095b6c17b4b82f2b55255188e6eff224191887bbd5892",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_011 — 독도 부근에서 가장 가까운 등대를 찾아줘.

답안 hash: `f45566c18b85bffd2367b313eb146b958d0b47ffd57deb637f93082608d86892`

### 실제 최종 답안
```json
{
  "answer_text": "The nearest lighthouse to Dokdo is located in Busan, Korea.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "status": "COMPLETED",
  "execution_status": "COMPLETED",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q3_01.json)
```json
{
  "case_id": "PILOT_Q3_01",
  "required_task_obligations": [
    "resolve_reference",
    "resolve_lighthouse_target_conditions",
    "verify_coverage",
    "find_nearest",
    "report_objects_or_unresolved_reason"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "User-approved source-bound safe abstention; document explanations are separately evaluated optional partial output."
  ],
  "expected_spatial_behavior": {
    "accepted_states": [
      "BLOCKED_DATA",
      "DATA_OUT_OF_SCOPE"
    ],
    "required_disclosure": "Current connected snapshot cannot determine the answer for the requested spatial extent",
    "per_target": {
      "Lighthouse": {
        "status": "BLOCKED_DATA",
        "object_ids": null
      }
    },
    "empty_result_as_answer_forbidden": true,
    "claim_spatial_success_forbidden": true
  }
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_011",
  "answer_sha256": "f45566c18b85bffd2367b313eb146b958d0b47ffd57deb637f93082608d86892",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "9b6e0d3395602f252bf55c9ae289c8b97d4dcc7b084de95c5eb8ac02cae5d5d4",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_010 — Find wrecks intersecting the selected area.

답안 hash: `bb946ad0943b0f5bda34d9be33df1a502f2c81996f86df51ad6ce93c808f80ae`

### 실제 최종 답안
```json
{
  "answer_text": "The selected area does not intersect any wrecks.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "validator_blockers": [
    "BLOCKED_CONFIG: explicit research source required",
    "BLOCKED_CONFIG: unsupported operation: None"
  ],
  "status": "BLOCKED_CONFIG",
  "execution_status": "BLOCKED_CONFIG",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q3_03.json)
```json
{
  "case_id": "PILOT_Q3_03",
  "required_task_obligations": [
    "require_selected_aoi",
    "verify_coverage",
    "search_intersections_if_aoi_available",
    "request_aoi_when_missing"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "No selected geometry is provided by this benchmark input; an arbitrary viewport is not a substitute."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_010",
  "answer_sha256": "bb946ad0943b0f5bda34d9be33df1a502f2c81996f86df51ad6ce93c808f80ae",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "b68ad9b965184ff292cdd3c82261780d1e2ac1ebd3e3b51ea66b9dd7a02b98e1",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_009 — 독도 주변 반경 5km의 해양지명을 찾아줘.

답안 hash: `a40910185eb5889a2f28ea235517eedea99a8c5e8a60bca6eb4034c54f13b031`

### 실제 최종 답안
```json
{
  "document_answer": {
    "features": [],
    "attribute_bindings": []
  },
  "search_executed": false,
  "execution_status": "BLOCKED",
  "source_coverage": {},
  "per_task_status": {},
  "mapping_provenance": {
    "version": "emitted_output_v1",
    "root": "final_state.final_dict",
    "retrieved_text_used_as_answer": false,
    "reference_used_for_mapping": false,
    "structured_document_answer_present": false
  },
  "status": "BLOCKED",
  "blocker": "DATA_COVERAGE_UNVERIFIED",
  "clarification_request": [],
  "answer_text": "현재 연결된 데이터의 공간 범위가 검증되지 않아 공간 검색을 실행하지 않았습니다. 검색 결과가 0건이라는 뜻은 아닙니다."
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q4_01.json)
```json
{
  "case_id": "PILOT_Q4_01",
  "required_task_obligations": [
    "resolve_approved_anchor",
    "search_fixed_gazetteer_5000m",
    "report_source_bound_objects"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_009",
  "answer_sha256": "a40910185eb5889a2f28ea235517eedea99a8c5e8a60bca6eb4034c54f13b031",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "7bb1ec3b6d7659b5c43bf5fe121b42786ab30ce3f0f14c22d7ad99f1f042f4f4",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_008 — Find wrecks within 5 km of Dokdo and explain their S-101 attributes.

답안 hash: `7b3bf796e3a51a63b21942ae8f5506f1676cbeefbe9f7cd26e7dcbb1170bfb76`

### 실제 최종 답안
```json
{
  "answer_text": "The wrecks within 5 km of Dokdo are not found in the S-101 feature catalogue.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "document_answer": {
    "features": [],
    "attribute_bindings": [],
    "evidence": {
      "edition": "2.0.0",
      "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
      "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
      "locators": [],
      "claim_source_links": []
    }
  },
  "status": "COMPLETED",
  "execution_status": "COMPLETED",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q5_03.json)
```json
{
  "case_id": "PILOT_Q5_03",
  "required_task_obligations": [
    "resolve_reference",
    "verify_coverage",
    "search_wrecks_5000m",
    "explain_s101_attributes",
    "distinguish_object_values_from_standard_attributes",
    "separate_partial_document_answer"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "User-approved source-bound safe abstention; document explanations are separately evaluated optional partial output."
  ],
  "expected_spatial_behavior": {
    "accepted_states": [
      "BLOCKED_DATA",
      "DATA_OUT_OF_SCOPE"
    ],
    "required_disclosure": "Current connected snapshot cannot determine the answer for the requested spatial extent",
    "per_target": {
      "Wreck": {
        "status": "BLOCKED_DATA",
        "object_ids": null
      }
    },
    "empty_result_as_answer_forbidden": true,
    "claim_spatial_success_forbidden": true
  }
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_008",
  "answer_sha256": "7b3bf796e3a51a63b21942ae8f5506f1676cbeefbe9f7cd26e7dcbb1170bfb76",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "7b1799060b9287086b0dc1ccacdfebb777ff6a4c44ce1beabef4dae493815b77",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_007 — 독도 주변 반경 5km의 해양지명을 찾아줘.

답안 hash: `0e3dd43d7ef3e827b14111d56935f7d321f1507a2cfea7708ba87d41abb5e193`

### 실제 최종 답안
```json
{
  "answer_text": "해양지명: 독도, 대동령, 대동해, 대동해안",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q4_01.json)
```json
{
  "case_id": "PILOT_Q4_01",
  "required_task_obligations": [
    "resolve_approved_anchor",
    "search_fixed_gazetteer_5000m",
    "report_source_bound_objects"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_007",
  "answer_sha256": "0e3dd43d7ef3e827b14111d56935f7d321f1507a2cfea7708ba87d41abb5e193",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "43b81856648bca9ea155219c87756be8fcfdf14dc5f8fc061a09793e9ccdce23",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_006 — 독도 주변 5km의 등대와 난파선을 찾아 각각의 근거를 알려줘.

답안 hash: `ecb690747f1788efd0a8708a595d99ec6f4d5012a4b01500259389e0c4596cb7`

### 실제 최종 답안
```json
{
  "answer_text": "The beacon and anchor line around Dokdo have been found. The beacon is located at 128.9, 34.9, and the anchor line is located at 129.3, 35.3.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "document_answers": [
    {
      "features": [],
      "attribute_bindings": [],
      "evidence": {
        "edition": "2.0.0",
        "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
        "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
        "locators": [],
        "claim_source_links": []
      }
    },
    {
      "features": [],
      "attribute_bindings": [],
      "evidence": {
        "edition": "2.0.0",
        "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
        "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
        "locators": [],
        "claim_source_links": []
      }
    }
  ],
  "status": "COMPLETED",
  "execution_status": "COMPLETED",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q5_01.json)
```json
{
  "case_id": "PILOT_Q5_01",
  "required_task_obligations": [
    "resolve_reference",
    "resolve_lighthouse_target_conditions",
    "verify_both_target_coverages",
    "search_both_targets_5000m",
    "provide_per_target_evidence",
    "separate_partial_document_answer"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "User-approved source-bound safe abstention; document explanations are separately evaluated optional partial output."
  ],
  "expected_spatial_behavior": {
    "accepted_states": [
      "BLOCKED_DATA",
      "DATA_OUT_OF_SCOPE"
    ],
    "required_disclosure": "Current connected snapshot cannot determine the answer for the requested spatial extent",
    "per_target": {
      "Lighthouse": {
        "status": "BLOCKED_DATA",
        "object_ids": null
      },
      "Wreck": {
        "status": "BLOCKED_DATA",
        "object_ids": null
      }
    },
    "empty_result_as_answer_forbidden": true,
    "claim_spatial_success_forbidden": true
  }
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_006",
  "answer_sha256": "ecb690747f1788efd0a8708a595d99ec6f4d5012a4b01500259389e0c4596cb7",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "a263ccd959d0a5a79e63faf202994388a84053fd232f24ba60bc3b0aa3b6cc37",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_005 — S-101에서 정박지는 어떤 객체야?

답안 hash: `282672ad5e414ef305455ba07899237f14784ec59062af471cd5b2ceccd8f3c6`

### 실제 최종 답안
```json
{
  "answer_text": "S-101에서 정박지는 'ship' 객체입니다.",
  "rendering": "DETERMINISTIC_RECEIPT_PROJECTION_V2",
  "spatial_tasks": {},
  "candidate_prose_is_unverified": true,
  "projection_errors": [],
  "status": "NEEDS_USER_INPUT",
  "clarification_request": "S-101에서 정박지는 'ship' 객체입니다.",
  "execution_status": "NEEDS_USER_INPUT",
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q1_02.json)
```json
{
  "case_id": "PILOT_Q1_02",
  "required_task_obligations": [
    "explain_anchorage_area_definition"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_005",
  "answer_sha256": "282672ad5e414ef305455ba07899237f14784ec59062af471cd5b2ceccd8f3c6",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "59e271281f4495e2bfdf6a0d2a465b801012e6a7717381802a197a2b329e0512",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_004 — 등대와 부표를 구분하는 S-101 근거를 알려줘.

답안 hash: `14a335c5aec05ffa41f89bbf5e77ff317417318cd487700280638291e9ff911d`

### 실제 최종 답안
```json
{
  "answer_text": "등대와 부표는 S-101 표준 해도 ENC 제품에서 다음과 같은 요소로 구분됩니다:\n1. **Navigation Hazard Object (등대)**: S-101 표준 해도 ENC 제품에서 등대를 나타내는 요소입니다. 이는 일반적으로 해안에 위치한 등대를 나타냅니다. 이 요소는 주로 해안 지역에서 사용됩니다.\n2. **Regulated Area (보호 지역)**: S-101 표준 해도 ENC 제품에서 보호 지역을 나타내는 요소입니다. 이 요소는 해상 안전을 유지하기 위해 특정 지역을 보호하는 데 사용됩니다. 이 요소는 주로 해상 경로 안전을 보장하기 위해 사용됩니다.\n3. **Protected Area (보호 지역)**: S-101 표준 해도 ENC 제품에서 보호 지역을 나타내는 요소입니다. 이 요소는 해상 안전을 유지하기 위해 특정 지역을 보호하는 데 사용됩니다. 이 요소는 주로 해상 경로 안전을 보장하기 위해 사용됩니다.",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q6_02.json)
```json
{
  "case_id": "PILOT_Q6_02",
  "required_task_obligations": [
    "compare_fixed_structure_and_floating_aid_models",
    "cite_comparison_evidence"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "single_Lighthouse_feature_assertion",
    "global_colour_codes_for_feature_binding"
  ],
  "scope_notes": [
    "Landmark/Building describe conditional structure alternatives; LightAllAround/LightSectored describe light alternatives. Listing these for explanation does not assert all must exist in one physical lighthouse.",
    "Bounded comparison: LateralBuoy is the explicitly selected representative floating-aid feature; no claim to exhaustively describe every buoy class. Compare with conditional structure/light models."
  ]
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_004",
  "answer_sha256": "14a335c5aec05ffa41f89bbf5e77ff317417318cd487700280638291e9ff911d",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "74bd3f2aabaeadeb7a22c4a8eebc22cf8a7e222c7747ac0efa560ae94a7bcce9",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_003 — S-101 Wreck 정의의 원문과 Feature Catalogue 출처를 알려줘.

답안 hash: `74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b`

### 실제 최종 답안
```json
null
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q6_01.json)
```json
{
  "case_id": "PILOT_Q6_01",
  "required_task_obligations": [
    "provide_wreck_definition_text",
    "cite_catalogue_edition_and_locator"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_003",
  "answer_sha256": "74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_002 — 독도 주변 반경 5000m의 해양지명을 찾아줘.

답안 hash: `e7c4f7c98793351cec109bf3c77307bb1d233bb7c50b4768e8d073aee0837ae8`

### 실제 최종 답안
```json
{
  "document_answer": {
    "features": [],
    "attribute_bindings": []
  },
  "search_executed": false,
  "execution_status": "BLOCKED",
  "source_coverage": {},
  "per_task_status": {},
  "mapping_provenance": {
    "version": "emitted_output_v1",
    "root": "final_state.final_dict",
    "retrieved_text_used_as_answer": false,
    "reference_used_for_mapping": false,
    "structured_document_answer_present": false
  },
  "status": "BLOCKED",
  "blocker": "DATA_COVERAGE_UNVERIFIED",
  "clarification_request": [],
  "answer_text": "현재 연결된 데이터의 공간 범위가 검증되지 않아 공간 검색을 실행하지 않았습니다. 검색 결과가 0건이라는 뜻은 아닙니다."
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q4_02.json)
```json
{
  "case_id": "PILOT_Q4_02",
  "required_task_obligations": [
    "resolve_approved_anchor",
    "search_fixed_gazetteer_5000m",
    "report_source_bound_objects"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": []
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_002",
  "answer_sha256": "e7c4f7c98793351cec109bf3c77307bb1d233bb7c50b4768e8d073aee0837ae8",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "7bb1ec3b6d7659b5c43bf5fe121b42786ab30ce3f0f14c22d7ad99f1f042f4f4",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```

## ANSWER_001 — Find wrecks within 5 km of Dokdo and explain their S-101 attributes.

답안 hash: `f3093ad19453be4600f6ba88493505e2ad3e9741469d65dc7c0606c74b2ccb10`

### 실제 최종 답안
```json
{
  "answer_text": "Within 5 km of Dokdo, there are wrecks with the following S-101 attributes: [Wreck, Obstruction, Rock, UnderwaterAwashRock, FoulGround].",
  "status": null,
  "execution_status": null,
  "search_executed": false
}
```

### 승인 GOLD
[해당 사례 전체 GOLD](gold_reference/PILOT_Q5_03.json)
```json
{
  "case_id": "PILOT_Q5_03",
  "required_task_obligations": [
    "resolve_reference",
    "verify_coverage",
    "search_wrecks_5000m",
    "explain_s101_attributes",
    "distinguish_object_values_from_standard_attributes",
    "separate_partial_document_answer"
  ],
  "forbidden_substitutions": [
    "intent_label_for_task_completion",
    "registry_hit_for_factual_authority",
    "plan_json_for_execution_result",
    "unexecuted_search_for_zero_objects",
    "partial_result_for_full_completion",
    "invented_AOI",
    "invented_snapshot_or_object_ID",
    "unsupported_zero_object_claim"
  ],
  "scope_notes": [
    "User-approved source-bound safe abstention; document explanations are separately evaluated optional partial output."
  ],
  "expected_spatial_behavior": {
    "accepted_states": [
      "BLOCKED_DATA",
      "DATA_OUT_OF_SCOPE"
    ],
    "required_disclosure": "Current connected snapshot cannot determine the answer for the requested spatial extent",
    "per_target": {
      "Wreck": {
        "status": "BLOCKED_DATA",
        "object_ids": null
      }
    },
    "empty_result_as_answer_forbidden": true,
    "claim_spatial_success_forbidden": true
  }
}
```

### 입력할 인간 채점 기록
```human-label
{
  "answer_id": "ANSWER_001",
  "answer_sha256": "f3093ad19453be4600f6ba88493505e2ad3e9741469d65dc7c0606c74b2ccb10",
  "gold_manifest_sha256": "feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c",
  "display_sha256": "49a295de24b7ef4eb305ef4c4f772c7fe0a210d7de49d252ce2d56c69017b132",
  "reviewer": "BBB",
  "author_type": "HUMAN",
  "human_completed": false,
  "independent_review_confirmed": false,
  "reviewed_at": null,
  "dimensions": {
    "meaning_correct": null,
    "required_tasks_complete": null,
    "evidence_supported": null,
    "no_unsupported_claims": null
  },
  "rationale": "",
  "answer_evidence_quote": "",
  "gold_evidence_locator": "",
  "human_label_source": ""
}
```
