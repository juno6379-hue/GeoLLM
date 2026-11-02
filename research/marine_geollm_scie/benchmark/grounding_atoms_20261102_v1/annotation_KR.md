# RQ1 개발 18문항 GOLD grounding atom 주석

**작성: 18/18 완료. 실제 RQ1 Semantic F1·Strict Match·CI: 미측정.** 기존 승인 GOLD에서 파생한 AI 원자 주석이다. 새 원자 표현·정규화에 대한 인간 검수 완료를 생성하지 않는다. 포인터·해시의 기계 검증은 의미의 독립 검수가 아니다. 모델 답변·홀드아웃은 읽지 않았다.

## 평가 경계

- 원자 값은 covers/dwithin/nearest/intersects, 정수 미터, EPSG:4326로 정규화한다. 명시 5000.0과 5000은 동일 의미다. schema.json의 무손실 변환만 예측 추출에 허용하며 누락 슬롯을 추론하지 않는다.
- 의미 과업, 대상 Feature, 속성 소유 연결, 연산, 기준 위치·거리·입력 문맥을 평가한다. 원문 정의의 문자열 일치를 의미 정확도로 쓰지 않는다.
- 단일 과업은 `query`, Q5는 대상별 `spatial:*`와 `comparison`/`document:Wreck`로 분리한다. 거리·기준·연산은 각 공간 하위과업에 귀속한다. 공개 task_mapping은 모델 자체 subtask 이름과 무관하다.
- 실행 여부·결과 객체집합·안전중단·공간 정답성은 기존 GOLD 별도 계약이다. 범위 밖 독도 요청도 질문 의미 원자는 유지한다.
- `Lighthouse`는 requested_object이며 S-101 단일 Feature를 신설하지 않는다. 구조물/등화의 조건부 설명은 기존 GOLD를 따른다.
- 조건 라벨은 기존 사후 metadata를 그대로 연결했다. UNSEEN_SYNONYM을 새로 만들지 않았다. Q4 영문 일반표현의 용어축 미분류도 유지한다.

총 원자 **172개**. 종류별: attribute_binding=44, comparison_criterion=4, distance_m=8, distance_metric=5, feature=26, input_requirement=1, operator=11, reference=10, reference_crs=6, reference_geometry_id=6, requested_object=5, source_binding=3, standard=11, task_obligation=32

## 사례별 근거와 원자

### PILOT_Q1_01 — 등대의 S-101 객체 유형과 정의를 알려줘.

조건: DOMAIN_KOREAN / 동등군: `Q1_01` / 원자 7개

근거: `research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl` line 1 · SHA256 `550f85c18d902e6895e9affe87b896785a9d150162181153c0d9dd423621bad4`

| 원자 | 종류 | 정답 허용값 | 파생 | 원본 JSON pointer |
|---|---|---|---|---|
| a001 (query) | task_obligation | `"explain_structure_and_light_distinction"` | DIRECT_CONTRACT_VALUE | `/required_task_obligations/0` |
| a002 (query) | task_obligation | `"explain_conditional_feature_mapping"` | DIRECT_CONTRACT_VALUE | `/required_task_obligations/1` |
| a003 (query) | feature | `"Landmark"` | DIRECT_CONTRACT_VALUE | `/document_scope/selected_feature_codes/0` |
| a004 (query) | feature | `"Building"` | DIRECT_CONTRACT_VALUE | `/document_scope/selected_feature_codes/1` |
| a005 (query) | feature | `"LightAllAround"` | DIRECT_CONTRACT_VALUE | `/document_scope/selected_feature_codes/2` |
| a006 (query) | feature | `"LightSectored"` | DIRECT_CONTRACT_VALUE | `/document_scope/selected_feature_codes/3` |
| a007 (query) | standard | `{"standard": "S-101", "edition": "2.0.0"}` | CONTRACT_PROJECTION | `/document_scope/evidence_requirements/edition`<br>`/document_scope/evidence_requirements/source_path` |

해석 범위: Landmark/Building describe conditional structure alternatives; LightAllAround/LightSectored describe light alternatives. Listing these for explanation does not assert all must exist in one physical lighthouse.

### PILOT_Q1_02 — S-101에서 정박지는 어떤 객체야?

조건: DOMAIN_KOREAN, COLLOQUIAL / 동등군: `Q1_02` / 원자 3개

근거: `research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl` line 2 · SHA256 `550f85c18d902e6895e9affe87b896785a9d150162181153c0d9dd423621bad4`

| 원자 | 종류 | 정답 허용값 | 파생 | 원본 JSON pointer |
|---|---|---|---|---|
| a001 (query) | task_obligation | `"explain_anchorage_area_definition"` | DIRECT_CONTRACT_VALUE | `/required_task_obligations/0` |
| a002 (query) | feature | `"AnchorageArea"` | DIRECT_CONTRACT_VALUE | `/document_scope/selected_feature_codes/0` |
| a003 (query) | standard | `{"standard": "S-101", "edition": "2.0.0"}` | CONTRACT_PROJECTION | `/document_scope/evidence_requirements/edition`<br>`/document_scope/evidence_requirements/source_path` |

해석 범위: 기존 GOLD 범위 유지.

### PILOT_Q1_03 — What is a wreck in S-101?

조건: OFFICIAL_TERM / 동등군: `Q1_03` / 원자 3개

근거: `research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl` line 3 · SHA256 `550f85c18d902e6895e9affe87b896785a9d150162181153c0d9dd423621bad4`

| 원자 | 종류 | 정답 허용값 | 파생 | 원본 JSON pointer |
|---|---|---|---|---|
| a001 (query) | task_obligation | `"explain_wreck_definition"` | DIRECT_CONTRACT_VALUE | `/required_task_obligations/0` |
| a002 (query) | feature | `"Wreck"` | DIRECT_CONTRACT_VALUE | `/document_scope/selected_feature_codes/0` |
| a003 (query) | standard | `{"standard": "S-101", "edition": "2.0.0"}` | CONTRACT_PROJECTION | `/document_scope/evidence_requirements/edition`<br>`/document_scope/evidence_requirements/source_path` |

해석 범위: 기존 GOLD 범위 유지.

### PILOT_Q2_01 — S-101 등대의 색상 속성과 허용 값을 알려줘.

조건: DOMAIN_KOREAN / 동등군: `Q2_01` / 원자 13개

근거: `research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl` line 4 · SHA256 `550f85c18d902e6895e9affe87b896785a9d150162181153c0d9dd423621bad4`

| 원자 | 종류 | 정답 허용값 | 파생 | 원본 JSON pointer |
|---|---|---|---|---|
| a001 (query) | task_obligation | `"distinguish_structure_and_light_colour"` | DIRECT_CONTRACT_VALUE | `/required_task_obligations/0` |
| a002 (query) | task_obligation | `"explain_feature_bound_permitted_values"` | DIRECT_CONTRACT_VALUE | `/required_task_obligations/1` |
| a003 (query) | feature | `"Landmark"` | DIRECT_CONTRACT_VALUE | `/document_scope/selected_feature_codes/0` |
| a004 (query) | feature | `"Building"` | DIRECT_CONTRACT_VALUE | `/document_scope/selected_feature_codes/1` |
| a005 (query) | feature | `"LightAllAround"` | DIRECT_CONTRACT_VALUE | `/document_scope/selected_feature_codes/2` |
| a006 (query) | feature | `"LightSectored"` | DIRECT_CONTRACT_VALUE | `/document_scope/selected_feature_codes/3` |
| a007 (query) | attribute_binding | `{"owner": "Landmark", "attribute": "colour"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/0/owner`<br>`/document_scope/attribute_scope/bindings/0/attribute` |
| a008 (query) | attribute_binding | `{"owner": "Building", "attribute": "colour"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/1/owner`<br>`/document_scope/attribute_scope/bindings/1/attribute` |
| a009 (query) | attribute_binding | `{"owner": "LightAllAround", "attribute": "colour"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/2/owner`<br>`/document_scope/attribute_scope/bindings/2/attribute` |
| a010 (query) | attribute_binding | `{"owner": "LightSectored", "attribute": "sectorCharacteristics"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/3/owner`<br>`/document_scope/attribute_scope/bindings/3/attribute` |
| a011 (query) | attribute_binding | `{"owner": "sectorCharacteristics", "attribute": "lightSector"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/4/owner`<br>`/document_scope/attribute_scope/bindings/4/attribute` |
| a012 (query) | attribute_binding | `{"owner": "lightSector", "attribute": "colour"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/5/owner`<br>`/document_scope/attribute_scope/bindings/5/attribute` |
| a013 (query) | standard | `{"standard": "S-101", "edition": "2.0.0"}` | CONTRACT_PROJECTION | `/document_scope/evidence_requirements/edition`<br>`/document_scope/evidence_requirements/source_path` |

해석 범위: Landmark/Building describe conditional structure alternatives; LightAllAround/LightSectored describe light alternatives. Listing these for explanation does not assert all must exist in one physical lighthouse.

### PILOT_Q2_02 — 제한구역의 제한 종류는 어떤 코드로 표현해?

조건: DOMAIN_KOREAN, COLLOQUIAL / 동등군: `Q2_02` / 원자 6개

근거: `research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl` line 5 · SHA256 `550f85c18d902e6895e9affe87b896785a9d150162181153c0d9dd423621bad4`

| 원자 | 종류 | 정답 허용값 | 파생 | 원본 JSON pointer |
|---|---|---|---|---|
| a001 (query) | task_obligation | `"distinguish_restriction_and_area_category"` | DIRECT_CONTRACT_VALUE | `/required_task_obligations/0` |
| a002 (query) | task_obligation | `"explain_restriction_codes"` | DIRECT_CONTRACT_VALUE | `/required_task_obligations/1` |
| a003 (query) | feature | `"RestrictedArea"` | DIRECT_CONTRACT_VALUE | `/document_scope/selected_feature_codes/0` |
| a004 (query) | attribute_binding | `{"owner": "RestrictedArea", "attribute": "categoryOfRestrictedArea"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/0/owner`<br>`/document_scope/attribute_scope/bindings/0/attribute` |
| a005 (query) | attribute_binding | `{"owner": "RestrictedArea", "attribute": "restriction"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/1/owner`<br>`/document_scope/attribute_scope/bindings/1/attribute` |
| a006 (query) | standard | `{"standard": "S-101", "edition": "2.0.0"}` | CONTRACT_PROJECTION | `/document_scope/evidence_requirements/edition`<br>`/document_scope/evidence_requirements/source_path` |

해석 범위: Explain restriction codes separately from categoryOfRestrictedArea. RequiredArea alternatives from another FC edition are not substitutes for FC 2.0.0 RestrictedArea.

### PILOT_Q2_03 — Which attributes describe a Wreck in S-101?

조건: OFFICIAL_TERM / 동등군: `Q2_03` / 원자 21개

근거: `research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl` line 6 · SHA256 `550f85c18d902e6895e9affe87b896785a9d150162181153c0d9dd423621bad4`

| 원자 | 종류 | 정답 허용값 | 파생 | 원본 JSON pointer |
|---|---|---|---|---|
| a001 (query) | task_obligation | `"explain_wreck_attribute_bindings"` | DIRECT_CONTRACT_VALUE | `/required_task_obligations/0` |
| a002 (query) | feature | `"Wreck"` | DIRECT_CONTRACT_VALUE | `/document_scope/selected_feature_codes/0` |
| a003 (query) | attribute_binding | `{"owner": "Wreck", "attribute": "categoryOfWreck"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/0/owner`<br>`/document_scope/attribute_scope/bindings/0/attribute` |
| a004 (query) | attribute_binding | `{"owner": "Wreck", "attribute": "expositionOfSounding"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/1/owner`<br>`/document_scope/attribute_scope/bindings/1/attribute` |
| a005 (query) | attribute_binding | `{"owner": "Wreck", "attribute": "featureName"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/2/owner`<br>`/document_scope/attribute_scope/bindings/2/attribute` |
| a006 (query) | attribute_binding | `{"owner": "Wreck", "attribute": "height"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/3/owner`<br>`/document_scope/attribute_scope/bindings/3/attribute` |
| a007 (query) | attribute_binding | `{"owner": "Wreck", "attribute": "interoperabilityIdentifier"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/4/owner`<br>`/document_scope/attribute_scope/bindings/4/attribute` |
| a008 (query) | attribute_binding | `{"owner": "Wreck", "attribute": "qualityOfVerticalMeasurement"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/5/owner`<br>`/document_scope/attribute_scope/bindings/5/attribute` |
| a009 (query) | attribute_binding | `{"owner": "Wreck", "attribute": "radarConspicuous"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/6/owner`<br>`/document_scope/attribute_scope/bindings/6/attribute` |
| a010 (query) | attribute_binding | `{"owner": "Wreck", "attribute": "reportedDate"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/7/owner`<br>`/document_scope/attribute_scope/bindings/7/attribute` |
| a011 (query) | attribute_binding | `{"owner": "Wreck", "attribute": "status"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/8/owner`<br>`/document_scope/attribute_scope/bindings/8/attribute` |
| a012 (query) | attribute_binding | `{"owner": "Wreck", "attribute": "techniqueOfVerticalMeasurement"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/9/owner`<br>`/document_scope/attribute_scope/bindings/9/attribute` |
| a013 (query) | attribute_binding | `{"owner": "Wreck", "attribute": "valueOfSounding"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/10/owner`<br>`/document_scope/attribute_scope/bindings/10/attribute` |
| a014 (query) | attribute_binding | `{"owner": "Wreck", "attribute": "visualProminence"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/11/owner`<br>`/document_scope/attribute_scope/bindings/11/attribute` |
| a015 (query) | attribute_binding | `{"owner": "Wreck", "attribute": "waterLevelEffect"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/12/owner`<br>`/document_scope/attribute_scope/bindings/12/attribute` |
| a016 (query) | attribute_binding | `{"owner": "Wreck", "attribute": "scaleMinimum"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/13/owner`<br>`/document_scope/attribute_scope/bindings/13/attribute` |
| a017 (query) | attribute_binding | `{"owner": "Wreck", "attribute": "information"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/14/owner`<br>`/document_scope/attribute_scope/bindings/14/attribute` |
| a018 (query) | attribute_binding | `{"owner": "Wreck", "attribute": "pictorialRepresentation"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/15/owner`<br>`/document_scope/attribute_scope/bindings/15/attribute` |
| a019 (query) | attribute_binding | `{"owner": "Wreck", "attribute": "defaultClearanceDepth"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/16/owner`<br>`/document_scope/attribute_scope/bindings/16/attribute` |
| a020 (query) | attribute_binding | `{"owner": "Wreck", "attribute": "surroundingDepth"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/17/owner`<br>`/document_scope/attribute_scope/bindings/17/attribute` |
| a021 (query) | standard | `{"standard": "S-101", "edition": "2.0.0"}` | CONTRACT_PROJECTION | `/document_scope/evidence_requirements/edition`<br>`/document_scope/evidence_requirements/source_path` |

해석 범위: 기존 GOLD 범위 유지.

### PILOT_Q3_01 — 독도 부근에서 가장 가까운 등대를 찾아줘.

조건: DOMAIN_KOREAN / 동등군: `Q3_01` / 원자 5개

근거: `research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl` line 7 · SHA256 `550f85c18d902e6895e9affe87b896785a9d150162181153c0d9dd423621bad4`

| 원자 | 종류 | 정답 허용값 | 파생 | 원본 JSON pointer |
|---|---|---|---|---|
| a001 (query) | task_obligation | `"resolve_lighthouse_target_conditions"` | DIRECT_CONTRACT_VALUE | `/required_task_obligations/1` |
| a002 (query) | task_obligation | `"find_nearest"` | DIRECT_CONTRACT_VALUE | `/required_task_obligations/3` |
| a003 (query) | reference | `"독도"` | DIRECT_CONTRACT_VALUE | `/required_qec_fields/slots.location_text` |
| a004 (query) | requested_object | `"Lighthouse"` | AI_CANONICALIZATION_PROPOSAL | `/expected_spatial_behavior/per_target/Lighthouse` |
| a005 (query) | operator | `"nearest"` | AI_CANONICALIZATION_PROPOSAL | `/required_task_obligations/3` |

해석 범위: User-approved source-bound safe abstention; document explanations are separately evaluated optional partial output.

### PILOT_Q3_02 — 부산항 영역 안의 정박지를 찾아줘.

조건: DOMAIN_KOREAN / 동등군: `Q3_02` / 원자 7개

근거: `research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl` line 8 · SHA256 `550f85c18d902e6895e9affe87b896785a9d150162181153c0d9dd423621bad4`

| 원자 | 종류 | 정답 허용값 | 파생 | 원본 JSON pointer |
|---|---|---|---|---|
| a001 (query) | task_obligation | `"resolve_official_port_polygon"` | DIRECT_CONTRACT_VALUE | `/required_task_obligations/0` |
| a002 (query) | task_obligation | `"search_within_polygon"` | DIRECT_CONTRACT_VALUE | `/required_task_obligations/2` |
| a003 (query) | reference | `"부산항"` | DIRECT_CONTRACT_VALUE | `/required_qec_fields/slots.location_text` |
| a004 (query) | operator | `"covers"` | CONTRACT_PROJECTION | `/spatial_predicate` |
| a005 (query) | reference_geometry_id | `"1137770"` | DIRECT_CONTRACT_VALUE | `/reference_geometry/id` |
| a006 (query) | reference_crs | `"EPSG:4326"` | CONTRACT_PROJECTION | `/reference_geometry/srid` |
| a007 (query) | feature | `"AnchorageArea"` | CONTRACT_PROJECTION | `/spatial_gold/AnchorageArea` |

해석 범위: Object IDs refer to frozen snapshot records, not deduplicated physical facilities or the whole legal port.

### PILOT_Q3_03 — Find wrecks intersecting the selected area.

조건: OFFICIAL_TERM / 동등군: `Q3_03` / 원자 4개

근거: `research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl` line 9 · SHA256 `550f85c18d902e6895e9affe87b896785a9d150162181153c0d9dd423621bad4`

| 원자 | 종류 | 정답 허용값 | 파생 | 원본 JSON pointer |
|---|---|---|---|---|
| a001 (query) | task_obligation | `"search_intersections_if_aoi_available"` | DIRECT_CONTRACT_VALUE | `/required_task_obligations/2` |
| a002 (query) | feature | `"Wreck"` | DIRECT_CONTRACT_VALUE | `/semantic_gold/feature` |
| a003 (query) | operator | `"intersects"` | DIRECT_CONTRACT_VALUE | `/semantic_gold/operator` |
| a004 (query) | input_requirement | `{"field": "selected_geometry", "requirement": "REQUIRED"}` | CONTRACT_PROJECTION | `/qec_gold/selected_geometry` |

해석 범위: No selected geometry is provided by this benchmark input; an arbitrary viewport is not a substitute.

### PILOT_Q4_01 — 독도 주변 반경 5km의 해양지명을 찾아줘.

조건: DOMAIN_KOREAN / 동등군: `dokdo_radius_5km` / 원자 8개

근거: `research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl` line 10 · SHA256 `550f85c18d902e6895e9affe87b896785a9d150162181153c0d9dd423621bad4`

| 원자 | 종류 | 정답 허용값 | 파생 | 원본 JSON pointer |
|---|---|---|---|---|
| a001 (query) | task_obligation | `"search_fixed_gazetteer_5000m"` | DIRECT_CONTRACT_VALUE | `/required_task_obligations/1` |
| a002 (query) | reference | `"독도"` | DIRECT_CONTRACT_VALUE | `/required_qec_fields/slots.location_text` |
| a003 (query) | distance_m | `5000` | CONTRACT_PROJECTION | `/required_qec_fields/slots.distance_m` |
| a004 (query) | requested_object | `"MarinePlaceName"` | AI_CANONICALIZATION_PROPOSAL | `/required_task_obligations/1` |
| a005 (query) | operator | `"dwithin"` | AI_CANONICALIZATION_PROPOSAL | `/spatial_reference/distance_policy` |
| a006 (query) | reference_geometry_id | `"mof:dokdo:east-island"` | DIRECT_CONTRACT_VALUE | `/spatial_reference/reference_geometry_source/place_id` |
| a007 (query) | reference_crs | `"EPSG:4326"` | DIRECT_CONTRACT_VALUE | `/spatial_reference/reference_crs` |
| a008 (query) | distance_metric | `{"surface": "WGS84_ellipsoid", "measurement": "point_to_point", "boundary_inclusive": true}` | CONTRACT_PROJECTION | `/spatial_reference/distance_policy`<br>`/spatial_reference/reference_geometry_source/coordinate_role` |

해석 범위: 기존 GOLD 범위 유지.

### PILOT_Q4_02 — 독도 주변 반경 5000m의 해양지명을 찾아줘.

조건: DOMAIN_KOREAN / 동등군: `dokdo_radius_5km` / 원자 8개

근거: `research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl` line 11 · SHA256 `550f85c18d902e6895e9affe87b896785a9d150162181153c0d9dd423621bad4`

| 원자 | 종류 | 정답 허용값 | 파생 | 원본 JSON pointer |
|---|---|---|---|---|
| a001 (query) | task_obligation | `"search_fixed_gazetteer_5000m"` | DIRECT_CONTRACT_VALUE | `/required_task_obligations/1` |
| a002 (query) | reference | `"독도"` | DIRECT_CONTRACT_VALUE | `/required_qec_fields/slots.location_text` |
| a003 (query) | distance_m | `5000` | CONTRACT_PROJECTION | `/required_qec_fields/slots.distance_m` |
| a004 (query) | requested_object | `"MarinePlaceName"` | AI_CANONICALIZATION_PROPOSAL | `/required_task_obligations/1` |
| a005 (query) | operator | `"dwithin"` | AI_CANONICALIZATION_PROPOSAL | `/spatial_reference/distance_policy` |
| a006 (query) | reference_geometry_id | `"mof:dokdo:east-island"` | DIRECT_CONTRACT_VALUE | `/spatial_reference/reference_geometry_source/place_id` |
| a007 (query) | reference_crs | `"EPSG:4326"` | DIRECT_CONTRACT_VALUE | `/spatial_reference/reference_crs` |
| a008 (query) | distance_metric | `{"surface": "WGS84_ellipsoid", "measurement": "point_to_point", "boundary_inclusive": true}` | CONTRACT_PROJECTION | `/spatial_reference/distance_policy`<br>`/spatial_reference/reference_geometry_source/coordinate_role` |

해석 범위: 기존 GOLD 범위 유지.

### PILOT_Q4_03 — Find marine place names within 5 km of Dokdo.

조건: 용어축 미분류 / 동등군: `dokdo_radius_5km` / 원자 8개

근거: `research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl` line 12 · SHA256 `550f85c18d902e6895e9affe87b896785a9d150162181153c0d9dd423621bad4`

| 원자 | 종류 | 정답 허용값 | 파생 | 원본 JSON pointer |
|---|---|---|---|---|
| a001 (query) | task_obligation | `"search_fixed_gazetteer_5000m"` | DIRECT_CONTRACT_VALUE | `/required_task_obligations/1` |
| a002 (query) | reference | `"독도"` | DIRECT_CONTRACT_VALUE | `/required_qec_fields/slots.location_text` |
| a003 (query) | distance_m | `5000` | CONTRACT_PROJECTION | `/required_qec_fields/slots.distance_m` |
| a004 (query) | requested_object | `"MarinePlaceName"` | AI_CANONICALIZATION_PROPOSAL | `/required_task_obligations/1` |
| a005 (query) | operator | `"dwithin"` | AI_CANONICALIZATION_PROPOSAL | `/spatial_reference/distance_policy` |
| a006 (query) | reference_geometry_id | `"mof:dokdo:east-island"` | DIRECT_CONTRACT_VALUE | `/spatial_reference/reference_geometry_source/place_id` |
| a007 (query) | reference_crs | `"EPSG:4326"` | DIRECT_CONTRACT_VALUE | `/spatial_reference/reference_crs` |
| a008 (query) | distance_metric | `{"surface": "WGS84_ellipsoid", "measurement": "point_to_point", "boundary_inclusive": true}` | CONTRACT_PROJECTION | `/spatial_reference/distance_policy`<br>`/spatial_reference/reference_geometry_source/coordinate_role` |

해석 범위: 기존 GOLD 범위 유지.

### PILOT_Q5_01 — 독도 주변 5km의 등대와 난파선을 찾아 각각의 근거를 알려줘.

조건: DOMAIN_KOREAN / 동등군: `Q5_01` / 원자 12개

근거: `research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl` line 13 · SHA256 `550f85c18d902e6895e9affe87b896785a9d150162181153c0d9dd423621bad4`

| 원자 | 종류 | 정답 허용값 | 파생 | 원본 JSON pointer |
|---|---|---|---|---|
| a001 (spatial:lighthouse) | task_obligation | `"resolve_lighthouse_target_conditions"` | DIRECT_CONTRACT_VALUE | `/required_task_obligations/1` |
| a002 (query) | task_obligation | `"search_both_targets_5000m"` | DIRECT_CONTRACT_VALUE | `/required_task_obligations/3` |
| a003 (spatial:lighthouse) | task_obligation | `"provide_per_target_evidence"` | DIRECT_CONTRACT_VALUE | `/required_task_obligations/4` |
| a004 (spatial:wreck) | task_obligation | `"provide_per_target_evidence"` | DIRECT_CONTRACT_VALUE | `/required_task_obligations/4` |
| a005 (spatial:wreck) | feature | `"Wreck"` | DIRECT_CONTRACT_VALUE | `/document_scope/selected_feature_codes/4` |
| a006 (spatial:lighthouse) | reference | `"독도"` | DIRECT_CONTRACT_VALUE | `/required_qec_fields/slots.location_text` |
| a007 (spatial:wreck) | reference | `"독도"` | DIRECT_CONTRACT_VALUE | `/required_qec_fields/slots.location_text` |
| a008 (spatial:lighthouse) | distance_m | `5000` | CONTRACT_PROJECTION | `/required_qec_fields/slots.distance_m` |
| a009 (spatial:wreck) | distance_m | `5000` | CONTRACT_PROJECTION | `/required_qec_fields/slots.distance_m` |
| a010 (spatial:lighthouse) | requested_object | `"Lighthouse"` | AI_CANONICALIZATION_PROPOSAL | `/expected_spatial_behavior/per_target/Lighthouse` |
| a011 (spatial:lighthouse) | operator | `"dwithin"` | AI_CANONICALIZATION_PROPOSAL | `/required_task_obligations/3`<br>`/required_qec_fields/slots.distance_m` |
| a012 (spatial:wreck) | operator | `"dwithin"` | AI_CANONICALIZATION_PROPOSAL | `/required_task_obligations/3`<br>`/required_qec_fields/slots.distance_m` |

선택적 보충 원자(주 RQ1 분모 제외): feature:"Landmark", feature:"Building", feature:"LightAllAround", feature:"LightSectored", standard:{"standard": "S-101", "edition": "2.0.0"}

해석 범위: User-approved source-bound safe abstention; document explanations are separately evaluated optional partial output.

### PILOT_Q5_02 — 부산항 주변 2km의 정박지와 제한구역을 찾아 비교해줘.

조건: DOMAIN_KOREAN / 동등군: `Q5_02` / 원자 21개

근거: `research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl` line 14 · SHA256 `550f85c18d902e6895e9affe87b896785a9d150162181153c0d9dd423621bad4`

| 원자 | 종류 | 정답 허용값 | 파생 | 원본 JSON pointer |
|---|---|---|---|---|
| a001 (query) | task_obligation | `"search_both_targets_2000m"` | DIRECT_CONTRACT_VALUE | `/required_task_obligations/2` |
| a002 (comparison) | task_obligation | `"compare_target_results"` | DIRECT_CONTRACT_VALUE | `/required_task_obligations/3` |
| a003 (spatial:AnchorageArea) | feature | `"AnchorageArea"` | DIRECT_CONTRACT_VALUE | `/document_scope/selected_feature_codes/0` |
| a004 (spatial:RestrictedArea) | feature | `"RestrictedArea"` | DIRECT_CONTRACT_VALUE | `/document_scope/selected_feature_codes/1` |
| a005 (comparison) | standard | `{"standard": "S-101", "edition": "2.0.0"}` | CONTRACT_PROJECTION | `/document_scope/evidence_requirements/edition`<br>`/document_scope/evidence_requirements/source_path` |
| a006 (spatial:AnchorageArea) | reference | `"부산항"` | DIRECT_CONTRACT_VALUE | `/required_qec_fields/slots.location_text` |
| a007 (spatial:RestrictedArea) | reference | `"부산항"` | DIRECT_CONTRACT_VALUE | `/required_qec_fields/slots.location_text` |
| a008 (spatial:AnchorageArea) | distance_m | `2000` | CONTRACT_PROJECTION | `/required_qec_fields/slots.distance_m` |
| a009 (spatial:RestrictedArea) | distance_m | `2000` | CONTRACT_PROJECTION | `/required_qec_fields/slots.distance_m` |
| a010 (spatial:AnchorageArea) | operator | `"dwithin"` | CONTRACT_PROJECTION | `/spatial_predicate` |
| a011 (spatial:RestrictedArea) | operator | `"dwithin"` | CONTRACT_PROJECTION | `/spatial_predicate` |
| a012 (spatial:AnchorageArea) | distance_metric | `{"surface": "WGS84_ellipsoid", "measurement": "minimum_geometry_to_geometry", "reference": "polygon_area", "boundary_inclusive": true}` | CONTRACT_PROJECTION | `/spatial_predicate`<br>`/distance_mode` |
| a013 (spatial:RestrictedArea) | distance_metric | `{"surface": "WGS84_ellipsoid", "measurement": "minimum_geometry_to_geometry", "reference": "polygon_area", "boundary_inclusive": true}` | CONTRACT_PROJECTION | `/spatial_predicate`<br>`/distance_mode` |
| a014 (spatial:AnchorageArea) | reference_geometry_id | `"1137770"` | DIRECT_CONTRACT_VALUE | `/reference_geometry/id` |
| a015 (spatial:RestrictedArea) | reference_geometry_id | `"1137770"` | DIRECT_CONTRACT_VALUE | `/reference_geometry/id` |
| a016 (spatial:AnchorageArea) | reference_crs | `"EPSG:4326"` | CONTRACT_PROJECTION | `/reference_geometry/srid` |
| a017 (spatial:RestrictedArea) | reference_crs | `"EPSG:4326"` | CONTRACT_PROJECTION | `/reference_geometry/srid` |
| a018 (comparison) | comparison_criterion | `"per_type_object_count"` | DIRECT_CONTRACT_VALUE | `/comparison_gold/criteria/0` |
| a019 (comparison) | comparison_criterion | `"per_type_minimum_and_maximum_distance_m"` | DIRECT_CONTRACT_VALUE | `/comparison_gold/criteria/1` |
| a020 (comparison) | comparison_criterion | `"distinct_FC_feature_definitions"` | DIRECT_CONTRACT_VALUE | `/comparison_gold/criteria/2` |
| a021 (comparison) | comparison_criterion | `"source_scope_and_reference_disclosure"` | DIRECT_CONTRACT_VALUE | `/comparison_gold/criteria/3` |

해석 범위: Object IDs refer to frozen snapshot records, not deduplicated physical facilities or the whole legal port.

### PILOT_Q5_03 — Find wrecks within 5 km of Dokdo and explain their S-101 attributes.

조건: OFFICIAL_TERM / 동등군: `Q5_03` / 원자 27개

근거: `research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl` line 15 · SHA256 `550f85c18d902e6895e9affe87b896785a9d150162181153c0d9dd423621bad4`

| 원자 | 종류 | 정답 허용값 | 파생 | 원본 JSON pointer |
|---|---|---|---|---|
| a001 (spatial:wreck) | task_obligation | `"search_wrecks_5000m"` | DIRECT_CONTRACT_VALUE | `/required_task_obligations/2` |
| a002 (document:Wreck) | task_obligation | `"explain_s101_attributes"` | DIRECT_CONTRACT_VALUE | `/required_task_obligations/3` |
| a003 (document:Wreck) | task_obligation | `"distinguish_object_values_from_standard_attributes"` | DIRECT_CONTRACT_VALUE | `/required_task_obligations/4` |
| a004 (document:Wreck) | feature | `"Wreck"` | DIRECT_CONTRACT_VALUE | `/document_scope/selected_feature_codes/0` |
| a005 (spatial:wreck) | feature | `"Wreck"` | DIRECT_CONTRACT_VALUE | `/document_scope/selected_feature_codes/0` |
| a006 (document:Wreck) | attribute_binding | `{"owner": "Wreck", "attribute": "categoryOfWreck"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/0/owner`<br>`/document_scope/attribute_scope/bindings/0/attribute` |
| a007 (document:Wreck) | attribute_binding | `{"owner": "Wreck", "attribute": "expositionOfSounding"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/1/owner`<br>`/document_scope/attribute_scope/bindings/1/attribute` |
| a008 (document:Wreck) | attribute_binding | `{"owner": "Wreck", "attribute": "featureName"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/2/owner`<br>`/document_scope/attribute_scope/bindings/2/attribute` |
| a009 (document:Wreck) | attribute_binding | `{"owner": "Wreck", "attribute": "height"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/3/owner`<br>`/document_scope/attribute_scope/bindings/3/attribute` |
| a010 (document:Wreck) | attribute_binding | `{"owner": "Wreck", "attribute": "interoperabilityIdentifier"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/4/owner`<br>`/document_scope/attribute_scope/bindings/4/attribute` |
| a011 (document:Wreck) | attribute_binding | `{"owner": "Wreck", "attribute": "qualityOfVerticalMeasurement"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/5/owner`<br>`/document_scope/attribute_scope/bindings/5/attribute` |
| a012 (document:Wreck) | attribute_binding | `{"owner": "Wreck", "attribute": "radarConspicuous"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/6/owner`<br>`/document_scope/attribute_scope/bindings/6/attribute` |
| a013 (document:Wreck) | attribute_binding | `{"owner": "Wreck", "attribute": "reportedDate"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/7/owner`<br>`/document_scope/attribute_scope/bindings/7/attribute` |
| a014 (document:Wreck) | attribute_binding | `{"owner": "Wreck", "attribute": "status"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/8/owner`<br>`/document_scope/attribute_scope/bindings/8/attribute` |
| a015 (document:Wreck) | attribute_binding | `{"owner": "Wreck", "attribute": "techniqueOfVerticalMeasurement"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/9/owner`<br>`/document_scope/attribute_scope/bindings/9/attribute` |
| a016 (document:Wreck) | attribute_binding | `{"owner": "Wreck", "attribute": "valueOfSounding"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/10/owner`<br>`/document_scope/attribute_scope/bindings/10/attribute` |
| a017 (document:Wreck) | attribute_binding | `{"owner": "Wreck", "attribute": "visualProminence"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/11/owner`<br>`/document_scope/attribute_scope/bindings/11/attribute` |
| a018 (document:Wreck) | attribute_binding | `{"owner": "Wreck", "attribute": "waterLevelEffect"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/12/owner`<br>`/document_scope/attribute_scope/bindings/12/attribute` |
| a019 (document:Wreck) | attribute_binding | `{"owner": "Wreck", "attribute": "scaleMinimum"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/13/owner`<br>`/document_scope/attribute_scope/bindings/13/attribute` |
| a020 (document:Wreck) | attribute_binding | `{"owner": "Wreck", "attribute": "information"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/14/owner`<br>`/document_scope/attribute_scope/bindings/14/attribute` |
| a021 (document:Wreck) | attribute_binding | `{"owner": "Wreck", "attribute": "pictorialRepresentation"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/15/owner`<br>`/document_scope/attribute_scope/bindings/15/attribute` |
| a022 (document:Wreck) | attribute_binding | `{"owner": "Wreck", "attribute": "defaultClearanceDepth"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/16/owner`<br>`/document_scope/attribute_scope/bindings/16/attribute` |
| a023 (document:Wreck) | attribute_binding | `{"owner": "Wreck", "attribute": "surroundingDepth"}` | CONTRACT_PROJECTION | `/document_scope/attribute_scope/bindings/17/owner`<br>`/document_scope/attribute_scope/bindings/17/attribute` |
| a024 (document:Wreck) | standard | `{"standard": "S-101", "edition": "2.0.0"}` | CONTRACT_PROJECTION | `/document_scope/evidence_requirements/edition`<br>`/document_scope/evidence_requirements/source_path` |
| a025 (spatial:wreck) | reference | `"독도"` | DIRECT_CONTRACT_VALUE | `/required_qec_fields/slots.location_text` |
| a026 (spatial:wreck) | distance_m | `5000` | CONTRACT_PROJECTION | `/required_qec_fields/slots.distance_m` |
| a027 (spatial:wreck) | operator | `"dwithin"` | AI_CANONICALIZATION_PROPOSAL | `/required_task_obligations/2`<br>`/required_qec_fields/slots.distance_m` |

해석 범위: User-approved source-bound safe abstention; document explanations are separately evaluated optional partial output.

### PILOT_Q6_01 — S-101 Wreck 정의의 원문과 Feature Catalogue 출처를 알려줘.

조건: OFFICIAL_TERM, MIXED_KO_EN / 동등군: `Q6_01` / 원자 5개

근거: `research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl` line 16 · SHA256 `550f85c18d902e6895e9affe87b896785a9d150162181153c0d9dd423621bad4`

| 원자 | 종류 | 정답 허용값 | 파생 | 원본 JSON pointer |
|---|---|---|---|---|
| a001 (query) | task_obligation | `"provide_wreck_definition_text"` | DIRECT_CONTRACT_VALUE | `/required_task_obligations/0` |
| a002 (query) | task_obligation | `"cite_catalogue_edition_and_locator"` | DIRECT_CONTRACT_VALUE | `/required_task_obligations/1` |
| a003 (query) | feature | `"Wreck"` | DIRECT_CONTRACT_VALUE | `/document_scope/selected_feature_codes/0` |
| a004 (query) | standard | `{"standard": "S-101", "edition": "2.0.0"}` | CONTRACT_PROJECTION | `/document_scope/evidence_requirements/edition`<br>`/document_scope/evidence_requirements/source_path` |
| a005 (query) | source_binding | `{"source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc", "locators": ["//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]"]}` | CONTRACT_PROJECTION | `/document_scope/evidence_requirements/source_sha256`<br>`/document_scope/evidence_requirements/locators` |

해석 범위: 기존 GOLD 범위 유지.

### PILOT_Q6_02 — 등대와 부표를 구분하는 S-101 근거를 알려줘.

조건: DOMAIN_KOREAN / 동등군: `Q6_02` / 원자 9개

근거: `research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl` line 17 · SHA256 `550f85c18d902e6895e9affe87b896785a9d150162181153c0d9dd423621bad4`

| 원자 | 종류 | 정답 허용값 | 파생 | 원본 JSON pointer |
|---|---|---|---|---|
| a001 (query) | task_obligation | `"compare_fixed_structure_and_floating_aid_models"` | DIRECT_CONTRACT_VALUE | `/required_task_obligations/0` |
| a002 (query) | task_obligation | `"cite_comparison_evidence"` | DIRECT_CONTRACT_VALUE | `/required_task_obligations/1` |
| a003 (query) | feature | `"Landmark"` | DIRECT_CONTRACT_VALUE | `/document_scope/selected_feature_codes/0` |
| a004 (query) | feature | `"Building"` | DIRECT_CONTRACT_VALUE | `/document_scope/selected_feature_codes/1` |
| a005 (query) | feature | `"LightAllAround"` | DIRECT_CONTRACT_VALUE | `/document_scope/selected_feature_codes/2` |
| a006 (query) | feature | `"LightSectored"` | DIRECT_CONTRACT_VALUE | `/document_scope/selected_feature_codes/3` |
| a007 (query) | feature | `"LateralBuoy"` | DIRECT_CONTRACT_VALUE | `/document_scope/selected_feature_codes/4` |
| a008 (query) | standard | `{"standard": "S-101", "edition": "2.0.0"}` | CONTRACT_PROJECTION | `/document_scope/evidence_requirements/edition`<br>`/document_scope/evidence_requirements/source_path` |
| a009 (query) | source_binding | `{"source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc", "locators": ["//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Landmark']]", "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Building']]", "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='LightAllAround']]", "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='LightSectored']]", "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='LateralBuoy']]"]}` | CONTRACT_PROJECTION | `/document_scope/evidence_requirements/source_sha256`<br>`/document_scope/evidence_requirements/locators` |

해석 범위: Landmark/Building describe conditional structure alternatives; LightAllAround/LightSectored describe light alternatives. Listing these for explanation does not assert all must exist in one physical lighthouse.; Bounded comparison: LateralBuoy is the explicitly selected representative floating-aid feature; no claim to exhaustively describe every buoy class. Compare with conditional structure/light models.

### PILOT_Q6_03 — What source supports the S-101 definition of AnchorageArea?

조건: OFFICIAL_TERM / 동등군: `Q6_03` / 원자 5개

근거: `research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl` line 18 · SHA256 `550f85c18d902e6895e9affe87b896785a9d150162181153c0d9dd423621bad4`

| 원자 | 종류 | 정답 허용값 | 파생 | 원본 JSON pointer |
|---|---|---|---|---|
| a001 (query) | task_obligation | `"provide_anchorage_definition_source"` | DIRECT_CONTRACT_VALUE | `/required_task_obligations/0` |
| a002 (query) | task_obligation | `"cite_catalogue_edition_and_locator"` | DIRECT_CONTRACT_VALUE | `/required_task_obligations/1` |
| a003 (query) | feature | `"AnchorageArea"` | DIRECT_CONTRACT_VALUE | `/document_scope/selected_feature_codes/0` |
| a004 (query) | standard | `{"standard": "S-101", "edition": "2.0.0"}` | CONTRACT_PROJECTION | `/document_scope/evidence_requirements/edition`<br>`/document_scope/evidence_requirements/source_path` |
| a005 (query) | source_binding | `{"source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc", "locators": ["//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]"]}` | CONTRACT_PROJECTION | `/document_scope/evidence_requirements/source_sha256`<br>`/document_scope/evidence_requirements/locators` |

해석 범위: 기존 GOLD 범위 유지.

## 다음 평가 연결

1. 새 원자 표현과 예측 추출 규칙을 독립 검토한다.
2. B1/B2의 실제 원본 답변에서 같은 schema의 예측 원자를 별도 주석화하고 원문 span/hash를 고정한다. GOLD에서 누락값을 채우지 않는다.
3. 조건별 F1·Strict Match와 동등군 paired CI를 계산한다. 18개는 개발셋이고 사후 조건 라벨이므로 탐색적 결과로 표시한다.
4. 운영 코드 변경 후의 방법 비교는 새 동결 전체 실행으로 수행한다. 기존 v6 재주석은 기존 원본 분석일 뿐 새 시스템 성능이 아니다.
