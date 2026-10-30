# 사례별 계획 후보 비교

**모든 모델 답변은 미검증 후보입니다. 정답·승인된 근거·실행 완료를 뜻하지 않습니다.**

이 문서는 모델 출력 검토용이며 GOLD 검수 양식과 분리했습니다. 근거 ID 조회는 식별자 연결 확인일 뿐, 답변과 근거 내용의 의미적 일치나 근거 정답률을 판정하지 않습니다.

## PILOT_Q1_03

질의: What is a wreck in S-101?

| 방법 | 반복 | action | target_features | radius_m | missing_inputs | status |
| --- | --- | --- | --- | --- | --- | --- |
| B0 | 0 | explain | ["wreck"] | 0 | [] | completed |
| B1 | 0 | explain | ["wreck"] | 미측정 | [] | completed |
| B2 | 0 | search | ["wreck"] | 0 | [] | completed |
| B3 | 0 | search | ["wreck"] | 0 | ["location_text", "radius_m"] | completed |
| B4 | 0 | search | ["wreck"] | 0 | [] | completed |
| B1 | 1 | explain | [] | 미측정 | [] | completed |
| B2 | 1 | explain | ["wreck"] | 미측정 | [] | completed |
| B3 | 1 | search | ["wreck"] | 0 | ["location_text"] | completed |
| B4 | 1 | search | ["wreck"] | 미측정 | ["The evidence references do not provide a clear definition of what a wreck is in S-101."] | completed |
| B0 | 1 | explain | ["wrecks"] | 0 | [] | completed |
| B2 | 2 | explain | ["wreck"] | 미측정 | [] | completed |
| B3 | 2 | search | ["wreck"] | 0 | [] | completed |
| B4 | 2 | explain | ["wreck"] | 미측정 | [] | invalid_response |
| B0 | 2 | search | ["wrecks"] | 미측정 | ["S-101"] | completed |
| B1 | 2 | search | ["wreck"] | 0 | [] | completed |

### B0 / 반복 0 — 미검증 후보

후보 답변: A wreck in S-101 is a submerged object, typically a ship, that has sunk to the bottom of the sea. It can be identified on a marine GIS map by its location and depth.

### B1 / 반복 0 — 미검증 후보

후보 답변: A wreck is a ship that has been damaged beyond repair and is often found on the ocean floor. It can be classified into different categories based on its condition, such as Non-Dangerous Wreck, Dangerous Wreck, Distributed Remains of Wreck, Wreck Showing Mast/Masts, and Wreck Showing Any Portion of Hull or Superstructure.

### B2 / 반복 0 — 미검증 후보

후보 답변: A wreck in S-101 is a navigational hazard object that is a wreck. It is included in the S-101 product and has the feature name 'navigation_hazard_object'.
출력 근거 ID: ["line:34", "line:36", "line:38"]
- line:34: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:36: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:38: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87

### B3 / 반복 0 — 미검증 후보

후보 답변: A wreck is a submerged object, usually a ship or other vessel, that has sunk to the bottom of a body of water. In the context of the S-101 map, a wreck could refer to a ship that has sunk to the bottom of the sea, possibly due to an accident or collision. The S-101 map is likely a maritime map, and the wreck would be represented as a feature on the map, with a specific location and radius of influence.

### B4 / 반복 0 — 미검증 후보

후보 답변: In S-101, a wreck is a navigational hazard object that is a wreck.
출력 근거 ID: ["line:34", "line:36", "line:38"]
- line:34: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:36: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:38: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
B4 최초→검토후 변경 필드: ["action", "spatial_relation", "location_text", "radius_m", "crs"]
변경 유무는 개선·수정 성공을 뜻하지 않습니다.

### B1 / 반복 1 — 미검증 후보

후보 답변: A wreck in S-101 refers to a ship that has been damaged or destroyed, resulting in the sinking of the vessel. It is classified into different categories based on its condition and the potential danger it poses. The classification is determined by the depth of the surrounding area and the relationship of the feature's depth to the surrounding depth area.

### B2 / 반복 1 — 미검증 후보

후보 답변: In S-101, a wreck is classified as a 'RestrictedArea' and is part of the regulated area. It is not a navigational hazard and does not require special attention.
출력 근거 ID: ["line:34", "line:36", "line:38"]
- line:34: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:36: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:38: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87

### B3 / 반복 1 — 미검증 후보

후보 답변: A wreck is a submerged object, typically a ship, that has sunk to the bottom of a body of water. In the context of the S-101 map, a wreck could refer to a specific ship that has sunk in the area, or it could be a general term for any submerged object.

### B4 / 반복 1 — 미검증 후보

후보 답변: In S-101, a wreck is a navigational hazard object that is a wreck, as listed in the feature candidates.
출력 근거 ID: ["line:34", "line:36", "line:38"]
- line:34: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:36: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:38: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
B4 최초→검토후 변경 필드: ["missing_inputs"]
변경 유무는 개선·수정 성공을 뜻하지 않습니다.

### B0 / 반복 1 — 미검증 후보

후보 답변: In the context of S-101, a wreck refers to a ship or other maritime vessel that has sunk to the bottom of the sea, often due to collision, grounding, or other accidents. The term 'wreck' is typically used to describe the physical remains of a ship that have been submerged in the ocean, which can be found in the S-101 area.

### B2 / 반복 2 — 미검증 후보

후보 답변: In S-101, a wreck refers to a navigational hazard that is a wreck, which is a type of restricted area. It is a restricted area that poses a risk to navigation and is typically marked on the ENC (Electronic Navigational Chart) for safe passage. Wrecks are often found in areas where ships have sunk, and they can be a significant hazard to ships and other vessels.
출력 근거 ID: ["line:34", "line:36", "line:38"]
- line:34: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:36: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:38: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87

### B3 / 반복 2 — 미검증 후보

후보 답변: A wreck in S-101 is a location on the map where a ship or other vessel has sunk, possibly resulting in the loss of cargo or crew. This information is typically found in maritime databases or maps, where it can be associated with specific locations on the map. The exact location of a wreck can be determined by searching for it using the appropriate tool.

### B4 / 반복 2 — 미검증 후보

후보 답변: In S-101, a wreck refers to a navigational hazard that is a wreck, which is a type of restricted area. It is a restricted area that poses a risk to navigation and is typically marked on the ENC (Electronic Navigational Chart) for safe passage. Wrecks are often found in areas where ships have sunk, and they can be a significant hazard to ships and other vessels.
출력 근거 ID: ["line:34", "line:36", "line:38"]
- line:34: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:36: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:38: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
B4 최초→검토후 변경 필드: []
변경 유무는 개선·수정 성공을 뜻하지 않습니다.

### B0 / 반복 2 — 미검증 후보

후보 답변: A wreck in S-101 refers to the underwater structures or objects that have been intentionally or unintentionally left on the ocean floor, often due to accidents, shipwrecks, or other reasons. These structures can include ships, oil rigs, or other man-made objects. The term 'wreck' in this context is used to describe these submerged structures, and the specific location is S-101.

### B1 / 반복 2 — 미검증 후보

후보 답변: A wreck in S-101 refers to a wrecked or ruined ship that is classified based on its condition. The classification includes Non-Dangerous Wreck, Dangerous Wreck, Distributed Remains of Wreck, Wreck Showing Mast/Masts, and Wreck Showing Any Portion of Hull or Superstructure. These classifications are determined by the depth of the surrounding area and the relationship of the depth of the feature to the range of depth of the surrounding depth area.
## PILOT_Q2_03

질의: Which attributes describe a Wreck in S-101?

| 방법 | 반복 | action | target_features | radius_m | missing_inputs | status |
| --- | --- | --- | --- | --- | --- | --- |
| B1 | 0 | search | ["Wreck"] | 0 | [] | completed |
| B2 | 0 | search | ["Wreck"] | 0 | [] | completed |
| B3 | 0 | search | ["Wreck"] | 0 | [] | completed |
| B4 | 0 | search | ["Wreck"] | 0 | [] | invalid_response |
| B0 | 0 | 미측정 | 미측정 | 미측정 | 미측정 | invalid_response |
| B2 | 1 | search | ["Wreck"] | 미측정 | [] | completed |
| B3 | 1 | search | ["Wreck"] | 0 | [] | completed |
| B4 | 1 | search | ["Wreck"] | 미측정 | [] | invalid_response |
| B0 | 1 | explain | ["Wreck"] | 미측정 | [] | completed |
| B1 | 1 | search | ["Wreck"] | 미측정 | [] | completed |
| B3 | 2 | search | ["Wreck"] | 미측정 | [] | completed |
| B4 | 2 | search | ["Wreck"] | 미측정 | [] | invalid_response |
| B0 | 2 | search | ["Wreck"] | 미측정 | [] | invalid_response |
| B1 | 2 | search | ["Wreck"] | 미측정 | [] | completed |
| B2 | 2 | search | ["Wreck"] | 미측정 | [] | completed |

### B1 / 반복 0 — 미검증 후보

후보 답변: The attributes describing a Wreck in S-101 are as follows: Category of Wreck: 2, Default Clearance Depth: 1, Exposition of Sounding: 1, Height: 10, Interoperability Identifier: CATWRK, Pictorial Representation: CATWRK, Quality of Vertical Measurement: 10, and Radar Conspicuous: true.

### B2 / 반복 0 — 미검증 후보

후보 답변: A Wreck is a feature in the S-101 product, located within the product. It is described as a feature candidate in the product registry.

### B3 / 반복 0 — 미검증 후보

후보 답변: A Wreck located in S-101, which is an active location.

### B4 / 반복 0 — 미검증 후보

후보 답변: In the S-101 product, a Wreck is a navigational hazard that falls under the 'navigational hazard' feature type. It is located within the product and has the label '전자해도 ENC 제품 사양'.
B4 최초→검토후 변경 필드: []
변경 유무는 개선·수정 성공을 뜻하지 않습니다.

### B0 / 반복 0 — 미검증 후보

구조화된 후보 답변 없음. raw 응답은 원시 실행 기록에 보존됩니다.

### B2 / 반복 1 — 미검증 후보

후보 답변: The Wreck feature in S-101 is located within the S-101 product and is classified as a navigational hazard. It is not automatically categorized as a restricted area or protected area.
출력 근거 ID: ["line:34", "line:36", "line:38"]
- line:34: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:36: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:38: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87

### B3 / 반복 1 — 미검증 후보

후보 답변: The attributes that describe a Wreck in S-101 are: name, type, location, date, cause, description, and coordinates.

### B4 / 반복 1 — 미검증 후보

후보 답변: The Wreck feature in S-101 is described by the following attributes: Feature Type: Wreck, Product: S-101, and Provenance: scripts/build_marine_kg.py, data/s100_s101_mapping_registry.yaml.
출력 근거 ID: ["line:34", "line:36", "line:38"]
- line:34: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:36: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:38: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
B4 최초→검토후 변경 필드: []
변경 유무는 개선·수정 성공을 뜻하지 않습니다.

### B0 / 반복 1 — 미검증 후보

후보 답변: The attributes that describe a Wreck in S-101 include its type and its location within the S-101 area.

### B1 / 반복 1 — 미검증 후보

후보 답변: The attributes of a wreck in S-101 are as follows:<br>- Category of Wreck: Dangerous Wreck (2)<br>- Default Clearance Depth: 2<br>- Exposition of Sounding: 2<br>- Height: 10<br>- Interoperability Identifier: CATWRK<br>- Pictorial Representation: CATWRK<br>- Quality of Vertical Measurement: 10<br>- Radar Conspicuous: true

### B3 / 반복 2 — 미검증 후보

후보 답변: The Wreck in S-101 can be described by the attributes 'type' and 'location', where 'type' is 'Wreck' and 'location' is 'S-101'.

### B4 / 반복 2 — 미검증 후보

후보 답변: The Wreck feature in S-101 is a navigation hazard product, specifically a restricted area, which is part of the S-101 product. It is located within the S-101 product and is categorized as a restricted area.
B4 최초→검토후 변경 필드: []
변경 유무는 개선·수정 성공을 뜻하지 않습니다.

### B0 / 반복 2 — 미검증 후보

구조화된 후보 답변 없음. raw 응답은 원시 실행 기록에 보존됩니다.

### B1 / 반복 2 — 미검증 후보

후보 답변: The attributes of a wreck in S-101 are as follows: Category of Wreck: Dangerous Wreck, Default Clearance Depth: Shoaler Than the Range of Depth of the Surrounding Depth Area, Exposition of Sounding: Deeper Than the Range of Depth of the Surrounding Depth Area, Height: 10m, Interoperability Identifier: CATWRK, Pictorial Representation: null, Quality of Vertical Measurement: Maintained Depth, Radar Conspicuous: true.
출력 근거 ID: ["attributes/categoryOfWreck", "attributes/defaultClearanceDepth", "attributes/expositionOfSounding", "attributes/height", "attributes/interoperabilityIdentifier", "attributes/pictorialRepresentation", "attributes/qualityOfVerticalMeasurement", "attributes/radarConspicuous"]
- attributes/categoryOfWreck: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: data/s101_feature_catalogue_v2_parsed.json; SHA-256: 0d26c66d0e1afd8a6ae33629e9bc1bb929c6a3735ccd1d60f637d149a54cad37
- attributes/defaultClearanceDepth: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: data/s101_feature_catalogue_v2_parsed.json; SHA-256: 0d26c66d0e1afd8a6ae33629e9bc1bb929c6a3735ccd1d60f637d149a54cad37
- attributes/expositionOfSounding: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: data/s101_feature_catalogue_v2_parsed.json; SHA-256: 0d26c66d0e1afd8a6ae33629e9bc1bb929c6a3735ccd1d60f637d149a54cad37
- attributes/height: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: data/s101_feature_catalogue_v2_parsed.json; SHA-256: 0d26c66d0e1afd8a6ae33629e9bc1bb929c6a3735ccd1d60f637d149a54cad37
- attributes/interoperabilityIdentifier: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: data/s101_feature_catalogue_v2_parsed.json; SHA-256: 0d26c66d0e1afd8a6ae33629e9bc1bb929c6a3735ccd1d60f637d149a54cad37
- attributes/pictorialRepresentation: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: data/s101_feature_catalogue_v2_parsed.json; SHA-256: 0d26c66d0e1afd8a6ae33629e9bc1bb929c6a3735ccd1d60f637d149a54cad37
- attributes/qualityOfVerticalMeasurement: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: data/s101_feature_catalogue_v2_parsed.json; SHA-256: 0d26c66d0e1afd8a6ae33629e9bc1bb929c6a3735ccd1d60f637d149a54cad37
- attributes/radarConspicuous: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: data/s101_feature_catalogue_v2_parsed.json; SHA-256: 0d26c66d0e1afd8a6ae33629e9bc1bb929c6a3735ccd1d60f637d149a54cad37

### B2 / 반복 2 — 미검증 후보

후보 답변: In the S-101 product, the navigation hazard object is a Wreck. It is categorized as a navigational hazard and has the label '전자해도 ENC 제품 사양'.
## PILOT_Q3_03

질의: Find wrecks intersecting the selected area.

| 방법 | 반복 | action | target_features | radius_m | missing_inputs | status |
| --- | --- | --- | --- | --- | --- | --- |
| B2 | 0 | search | ["wreck"] | 미측정 | [] | completed |
| B3 | 0 | search | ["wrecks"] | 미측정 | [] | completed |
| B4 | 0 | search | ["wreck"] | 미측정 | [] | invalid_response |
| B0 | 0 | search | ["wrecks"] | 미측정 | ["selected area"] | completed |
| B1 | 0 | search | ["wrecks"] | 미측정 | [] | completed |
| B3 | 1 | search | ["wrecks"] | 미측정 | [] | completed |
| B4 | 1 | search | ["wreck"] | 미측정 | [] | invalid_response |
| B0 | 1 | search | ["wrecks"] | 미측정 | ["selected_area"] | completed |
| B1 | 1 | search | ["wrecks"] | 미측정 | [] | completed |
| B2 | 1 | search | ["wreck"] | 미측정 | [] | completed |
| B4 | 2 | search | ["wreck"] | 미측정 | [] | invalid_response |
| B0 | 2 | search | ["wrecks"] | 미측정 | ["selected area"] | completed |
| B1 | 2 | search | ["wrecks"] | 미측정 | [] | completed |
| B2 | 2 | search | ["wreck"] | 미측정 | [] | completed |
| B3 | 2 | search | ["wrecks"] | 미측정 | [] | completed |

### B2 / 반복 0 — 미검증 후보

후보 답변: The search results will show wrecks that intersect with the selected area.
출력 근거 ID: ["line:1235", "line:1236", "line:1237", "line:1240"]
- line:1235: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:1236: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:1237: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:1240: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87

### B3 / 반복 0 — 미검증 후보

후보 답변: The selected area intersects with the wrecks. The wrecks are located in the area.

### B4 / 반복 0 — 미검증 후보

후보 답변: The wrecks intersecting the selected area can be found by searching for 'wreck' on the marine GIS platform.
출력 근거 ID: ["line:1235", "line:1236", "line:1237", "line:1240"]
- line:1235: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:1236: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:1237: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:1240: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
B4 최초→검토후 변경 필드: []
변경 유무는 개선·수정 성공을 뜻하지 않습니다.

### B0 / 반복 0 — 미검증 후보

후보 답변: The search for wrecks intersecting the selected area has been initiated.

### B1 / 반복 0 — 미검증 후보

후보 답변: The search will find wrecks that intersect with the selected area.

### B3 / 반복 1 — 미검증 후보

후보 답변: The search results will include wrecks that intersect with the selected area.

### B4 / 반복 1 — 미검증 후보

후보 답변: The marine GIS plan has been created to find wrecks that intersect with the selected area. The search will be conducted within the specified radius, considering the provided CRS (Coordinate Reference System). The evidence references provided are from the marine knowledge graph and can be used to verify the results.
출력 근거 ID: ["line:1235", "line:1236", "line:1237", "line:1240"]
- line:1235: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:1236: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:1237: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:1240: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
B4 최초→검토후 변경 필드: []
변경 유무는 개선·수정 성공을 뜻하지 않습니다.

### B0 / 반복 1 — 미검증 후보

후보 답변: The search for wrecks intersecting the selected area has been initiated. The selected area is not provided, so the specific wrecks found will depend on the context of the map and the available evidence.

### B1 / 반복 1 — 미검증 후보

후보 답변: The search will find wrecks that intersect with the selected area.

### B2 / 반복 1 — 미검증 후보

후보 답변: The search results will show wrecks that intersect the selected area.
출력 근거 ID: ["line:1235", "line:1236", "line:1237", "line:1240"]
- line:1235: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:1236: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:1237: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:1240: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87

### B4 / 반복 2 — 미검증 후보

후보 답변: The marine GIS plan will search for wrecks that intersect with the selected area on the map.
출력 근거 ID: ["line:1235", "line:1236", "line:1237", "line:1240"]
- line:1235: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:1236: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:1237: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:1240: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
B4 최초→검토후 변경 필드: []
변경 유무는 개선·수정 성공을 뜻하지 않습니다.

### B0 / 반복 2 — 미검증 후보

후보 답변: The search has been initiated to find wrecks that intersect with the selected area.

### B1 / 반복 2 — 미검증 후보

후보 답변: The search will find and return the wrecks that intersect the selected area.

### B2 / 반복 2 — 미검증 후보

후보 답변: The wrecks intersecting the selected area can be found by querying the marine GIS system with the provided evidence references.
출력 근거 ID: ["line:1235", "line:1236", "line:1237", "line:1240"]
- line:1235: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:1236: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:1237: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:1240: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87

### B3 / 반복 2 — 미검증 후보

후보 답변: The search results will provide the locations of wrecks that intersect with the selected area.
## PILOT_Q4_01

질의: 독도 주변 반경 5km의 해양지명을 찾아줘.

| 방법 | 반복 | action | target_features | radius_m | missing_inputs | status |
| --- | --- | --- | --- | --- | --- | --- |
| B3 | 0 | search | ["해양지명"] | 5000 | [] | completed |
| B4 | 0 | search | ["island"] | 5000 | ["radius_m"] | completed |
| B0 | 0 | search | ["island"] | 5000 | ["radius_m"] | completed |
| B1 | 0 | search | ["海域"] | 5000 | [] | completed |
| B2 | 0 | search | ["海域"] | 5000 | [] | completed |
| B4 | 1 | search | ["海域"] | 5000 | ["The evidence reference IDs are not provided"] | completed |
| B0 | 1 | search | ["island"] | 5000 | [] | completed |
| B1 | 1 | search | ["海域"] | 5000 | [] | completed |
| B2 | 1 | search | ["海域"] | 5000 | [] | completed |
| B3 | 1 | search | ["island"] | 5000 | [] | completed |
| B0 | 2 | search | ["Dokdo"] | 5000 | [] | completed |
| B1 | 2 | search | ["island", "peninsula", "island", "peninsula"] | 5000 | [] | completed |
| B2 | 2 | search | ["island", "peninsula", "island", "peninsula"] | 5000 | [] | completed |
| B3 | 2 | search | ["island", "peninsula", "islet"] | 5000 | [] | completed |
| B4 | 2 | search | ["island"] | 5000 | ["target_features"] | completed |

### B3 / 반복 0 — 미검증 후보

후보 답변: 해양지명 '독도' 주변 5km 내의 위치를 찾았습니다.

### B4 / 반복 0 — 미검증 후보

후보 답변: 독도 주변 반경 5km의 해양지명은 '독도'입니다.
B4 최초→검토후 변경 필드: []
변경 유무는 개선·수정 성공을 뜻하지 않습니다.

### B0 / 반복 0 — 미검증 후보

후보 답변: 독도 주변 반경 5km의 해양지명은 '독도'입니다.

### B1 / 반복 0 — 미검증 후보

후보 답변: 独岛（ Dokdo ）位于韩国济州岛以东约100公里处，距离日本九州岛以东约150公里。在距离独岛5公里范围内，有多个海域，包括独岛海域、独岛以东海域、独岛以南海域等。

### B2 / 반복 0 — 미검증 후보

후보 답변: 独岛（ Dokdo ）位于韩国济州岛以东约100公里处，距离日本九州岛以东约150公里。在距离独岛5公里范围内，有多个海域，包括独岛海域、独岛以东海域、独岛以南海域等。

### B4 / 반복 1 — 미검증 후보

후보 답변: 独岛（ Dokdo ）周边5公里范围内海域的名称如下：
B4 최초→검토후 변경 필드: ["missing_inputs"]
변경 유무는 개선·수정 성공을 뜻하지 않습니다.

### B0 / 반복 1 — 미검증 후보

후보 답변: 独岛（ Dokdo ）周边5公里范围内海域的海港、岛屿名称如下：

### B1 / 반복 1 — 미검증 후보

후보 답변: 独岛（ Dokdo ）周边5公里范围内海域的名称如下：

### B2 / 반복 1 — 미검증 후보

후보 답변: 独岛（ Dokdo ）周边5公里范围内海域的名称如下：

### B3 / 반복 1 — 미검증 후보

후보 답변: 独岛位于韩国济州岛附近，距离济州岛约100公里。根据提供的证据，独岛周围5公里范围内没有其他海洋地理特征。

### B0 / 반복 2 — 미검증 후보

후보 답변: The marine geographical names within a 5km radius of Dokdo are: 

### B1 / 반복 2 — 미검증 후보

후보 답변: 独岛（ Dokdo ）周边5公里范围内有以下海洋名称：

### B2 / 반복 2 — 미검증 후보

후보 답변: 独岛（ Dokdo ）周边5公里范围内有以下海洋名称：

### B3 / 반복 2 — 미검증 후보

후보 답변: 独岛位于韩国济州岛附近，周围5公里范围内有多个海洋地理特征，包括岛屿、半岛和小岛。

### B4 / 반복 2 — 미검증 후보

후보 답변: 独岛（ Dokdo ）位于韩国济州岛以东约100公里处，距离日本的竹岛（ Takeshima ）约10公里。根据韩国海洋局的数据，独岛周围5公里范围内有以下海洋地名：
B4 최초→검토후 변경 필드: ["missing_inputs"]
변경 유무는 개선·수정 성공을 뜻하지 않습니다.
## PILOT_Q5_03

질의: Find wrecks within 5 km of Dokdo and explain their S-101 attributes.

| 방법 | 반복 | action | target_features | radius_m | missing_inputs | status |
| --- | --- | --- | --- | --- | --- | --- |
| B4 | 0 | explain | ["wrecks"] | 5000 | [] | invalid_response |
| B0 | 0 | search | ["wrecks"] | 5000 | ["S-101 attribute data for Dokdo wrecks"] | invalid_response |
| B1 | 0 | explain | ["wrecks"] | 5000 | [] | completed |
| B2 | 0 | explain | ["wrecks"] | 5000 | [] | completed |
| B3 | 0 | search | ["wrecks"] | 5000 | [] | completed |
| B0 | 1 | search | ["wrecks"] | 5000 | ["None"] | invalid_response |
| B1 | 1 | explain | ["wrecks"] | 5000 | [] | completed |
| B2 | 1 | explain | ["wrecks"] | 5000 | [] | completed |
| B3 | 1 | search | ["wrecks"] | 5000 | [] | completed |
| B4 | 1 | explain | ["wrecks"] | 5000 | [] | invalid_response |
| B1 | 2 | explain | ["wrecks"] | 5000 | [] | completed |
| B2 | 2 | explain | ["wrecks"] | 5000 | [] | completed |
| B3 | 2 | search | ["wrecks"] | 5000 | [] | completed |
| B4 | 2 | search | ["wrecks"] | 5000 | [] | completed |
| B0 | 2 | search | ["wrecks"] | 5000 | ["wrecks"] | completed |

### B4 / 반복 0 — 미검증 후보

후보 답변: Within 5 km of Dokdo, there are wrecks that have been mapped as S-101 products. These wrecks are not automatically categorized as navigational hazards due to their restricted nature. They are identified as protected areas and restricted areas, which are not automatically classified as navigational hazards. The S-101 product is a standard ENC (Electronic Navigational Chart) version 2.0.0.
출력 근거 ID: ["line:34", "line:36", "line:38"]
- line:34: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:36: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:38: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
B4 최초→검토후 변경 필드: []
변경 유무는 개선·수정 성공을 뜻하지 않습니다.

### B0 / 반복 0 — 미검증 후보

구조화된 후보 답변 없음. raw 응답은 원시 실행 기록에 보존됩니다.

### B1 / 반복 0 — 미검증 후보

후보 답변: The wrecks within 5 km of Dokdo are classified as 'Dangerous Wreck' (value 2), have a default clearance depth of 0, are exposed to the water surface (value 1), and are at a height of 0. They are identified by the Interoperability Identifier 'CATWRK', and their quality of vertical measurement is 'Least Depth Known' (value 6), indicating that the depth is unknown. They are also radar conspicuous, meaning they are visible on radar.

### B2 / 반복 0 — 미검증 후보

후보 답변: Within a 5 km radius of Dokdo, there are wrecks that have been mapped to the S-101 product. These wrecks are part of the navigational chart and are marked as restricted areas. They are not automatically categorized as hazards due to their restricted nature.

### B3 / 반복 0 — 미검증 후보

후보 답변: The wrecks within 5 km of Dokdo are identified and their S-101 attributes are explained.

### B0 / 반복 1 — 미검증 후보

구조화된 후보 답변 없음. raw 응답은 원시 실행 기록에 보존됩니다.

### B1 / 반복 1 — 미검증 후보

후보 답변: The wrecks within 5 km of Dokdo are classified as non-dangerous wrecks with default clearance depth of 1 m, exposition of sounding within the range of the surrounding depth area, a height of 10 m, an interoperability identifier of CATWRK, a pictorial representation of CATWRK, a quality of vertical measurement of 10, and a radar conspicuous feature of false.

### B2 / 반복 1 — 미검증 후보

후보 답변: Within a 5 km radius of Dokdo, there are no known wrecks that have been recorded in the S-101 product. The S-101 product is a standard ENC (Electronic Chart) product that includes various types of hazards, including restricted areas, military practice areas, traffic separation schemes, and protected areas. The S-101 product is not designed to automatically categorize hazards based on their potential for navigation risk, so wrecks may not be included in the product's coverage. The S-101 product is intended for use in electronic charts and navigation systems, not for the purpose of hazard identification or mapping.

### B3 / 반복 1 — 미검증 후보

후보 답변: The search results for wrecks within 5 km of Dokdo include the following features: [List of wrecks with S-101 attributes].

### B4 / 반복 1 — 미검증 후보

후보 답변: Within a 5 km radius of Dokdo, there are wrecks that have been mapped using the S-101 product. These wrecks are identified as 'navigation_hazard_object' in the marine KG and are categorized under the 'navigational_hazard' upper class. The S-101 product is a standard ENC (Electronic Chart) version 2.0.0, which is used for electronic navigational charts.
B4 최초→검토후 변경 필드: []
변경 유무는 개선·수정 성공을 뜻하지 않습니다.

### B1 / 반복 2 — 미검증 후보

후보 답변: The wrecks within 5 km of Dokdo are classified as dangerous wrecks, with a default clearance depth of 1 meter, an exposition of sounding within the range of the surrounding depth area, a height of 10 meters, an interoperability identifier of CATWRK, a pictorial representation of PICREP, a quality of vertical measurement of 10, and a radar conspicuous feature.

### B2 / 반복 2 — 미검증 후보

후보 답변: Within a 5 km radius of Dokdo, there are no wrecks recorded in the S-101 product. The wrecks are not present in the provided evidence references.

### B3 / 반복 2 — 미검증 후보

후보 답변: The search results will provide information on wrecks within 5 km of Dokdo, including their S-101 attributes.

### B4 / 반복 2 — 미검증 후보

후보 답변: Within a 5 km radius of Dokdo, there are no wrecks recorded in the S-101 product. The wrecks are not within the specified radius.
B4 최초→검토후 변경 필드: ["action"]
변경 유무는 개선·수정 성공을 뜻하지 않습니다.

### B0 / 반복 2 — 미검증 후보

후보 답변: Within a 5 km radius of Dokdo, there are several wrecks that can be identified and their S-101 attributes explained. The wrecks are likely to be older, more significant, or of a specific type, as indicated by the S-101 attribute. This information can be used to provide a detailed analysis of the historical and archaeological significance of these wrecks.
## PILOT_Q6_03

질의: What source supports the S-101 definition of AnchorageArea?

| 방법 | 반복 | action | target_features | radius_m | missing_inputs | status |
| --- | --- | --- | --- | --- | --- | --- |
| B0 | 0 | explain | ["S-101"] | 미측정 | ["source"] | completed |
| B1 | 0 | explain | ["AnchorageArea"] | 미측정 | [] | completed |
| B2 | 0 | explain | ["AnchorageArea"] | 미측정 | [] | completed |
| B3 | 0 | explain | ["AnchorageArea"] | 미측정 | ["AnchorageArea definition source"] | completed |
| B4 | 0 | explain | ["AnchorageArea"] | 미측정 | [] | invalid_response |
| B1 | 1 | explain | ["Anchorage Area"] | 미측정 | [] | completed |
| B2 | 1 | explain | ["AnchorageArea"] | 0 | [] | completed |
| B3 | 1 | explain | ["AnchorageArea"] | 미측정 | ["S-101 definition of AnchorageArea"] | completed |
| B4 | 1 | explain | ["AnchorageArea"] | 0 | [] | invalid_response |
| B0 | 1 | explain | ["AnchorageArea"] | 0 | [] | completed |
| B2 | 2 | explain | ["AnchorageArea"] | 미측정 | [] | completed |
| B3 | 2 | search | ["AnchorageArea"] | 미측정 | [] | completed |
| B4 | 2 | explain | ["AnchorageArea"] | 미측정 | [] | completed |
| B0 | 2 | explain | ["AnchorageArea"] | 미측정 | ["S-101 definition of AnchorageArea"] | completed |
| B1 | 2 | explain | ["AnchorageArea"] | 미측정 | [] | completed |

### B0 / 반복 0 — 미검증 후보

후보 답변: The S-101 definition of AnchorageArea is not supported by any specific source. It is a general term used in maritime regulations and does not have a direct reference in a single source. It is defined within the context of maritime law and regulations, but the source of this definition is not explicitly provided in the available evidence.

### B1 / 반복 0 — 미검증 후보

후보 답변: The S-101 definition of AnchorageArea is supported by the following sources: 'AnchorageArea' feature, 'Category of Anchorage' attribute, and 'Scale Minimum' attribute in the S-101 feature catalogue.
출력 근거 ID: ["features/AnchorageArea", "attributes/categoryOfAnchorage", "attributes/scaleMinimum"]
- features/AnchorageArea: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: data/s101_feature_catalogue_v2_parsed.json; SHA-256: 0d26c66d0e1afd8a6ae33629e9bc1bb929c6a3735ccd1d60f637d149a54cad37
- attributes/categoryOfAnchorage: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: data/s101_feature_catalogue_v2_parsed.json; SHA-256: 0d26c66d0e1afd8a6ae33629e9bc1bb929c6a3735ccd1d60f637d149a54cad37
- attributes/scaleMinimum: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: data/s101_feature_catalogue_v2_parsed.json; SHA-256: 0d26c66d0e1afd8a6ae33629e9bc1bb929c6a3735ccd1d60f637d149a54cad37

### B2 / 반복 0 — 미검증 후보

후보 답변: The S-101 definition of AnchorageArea is supported by the following sources: 'navigation_hazard_object' and 'regulated_area' nodes in the marine KG graph. The 'navigation_hazard_object' node maps to the S-101 'restricted_area' product, while the 'regulated_area' node maps to the S-101 'protected_area' product.
출력 근거 ID: ["line:34", "line:36", "line:38"]
- line:34: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:36: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:38: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87

### B3 / 반복 0 — 미검증 후보

후보 답변: The S-101 definition of AnchorageArea is not explicitly supported by any source. This definition is likely based on the International Maritime Organization (IMO) guidelines and may not be widely recognized or documented outside of maritime contexts.

### B4 / 반복 0 — 미검증 후보

후보 답변: The S-101 definition of AnchorageArea is supported by the following sources: line:34, line:36, and line:38.
출력 근거 ID: ["line:34", "line:36", "line:38"]
- line:34: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:36: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:38: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
B4 최초→검토후 변경 필드: []
변경 유무는 개선·수정 성공을 뜻하지 않습니다.

### B1 / 반복 1 — 미검증 후보

후보 답변: The S-101 definition of AnchorageArea is supported by the following sources: 'Anchorage Area' feature in the S-101 feature catalogue, 'Category of Anchorage' attribute, and 'Scale Minimum' attribute. These sources provide the necessary information to understand the specific characteristics and minimum scale requirements for anchorage areas as defined in the S-101 standard.
출력 근거 ID: ["features/AnchorageArea", "attributes/categoryOfAnchorage", "attributes/scaleMinimum"]
- features/AnchorageArea: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: data/s101_feature_catalogue_v2_parsed.json; SHA-256: 0d26c66d0e1afd8a6ae33629e9bc1bb929c6a3735ccd1d60f637d149a54cad37
- attributes/categoryOfAnchorage: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: data/s101_feature_catalogue_v2_parsed.json; SHA-256: 0d26c66d0e1afd8a6ae33629e9bc1bb929c6a3735ccd1d60f637d149a54cad37
- attributes/scaleMinimum: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: data/s101_feature_catalogue_v2_parsed.json; SHA-256: 0d26c66d0e1afd8a6ae33629e9bc1bb929c6a3735ccd1d60f637d149a54cad37

### B2 / 반복 1 — 미검증 후보

후보 답변: The S-101 definition of AnchorageArea is supported by the following sources:<br>- line:34: mapsToProduct with predicate 'mapsToProduct' and subject 'semanticmapping:regulated_area' and object 'product:s-101'<br>- line:36: mapsToProduct with predicate 'mapsToProduct' and subject 'semanticmapping:protected_area' and object 'product:s-101'<br>- line:38: mapsToProduct with predicate 'mapsToProduct' and subject 'semanticmapping:navigation_hazard_object' and object 'product:s-101'
출력 근거 ID: ["line:34", "line:36", "line:38"]
- line:34: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:36: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:38: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87

### B3 / 반복 1 — 미검증 후보

후보 답변: The S-101 definition of AnchorageArea is not supported by any specific source. It is an international standard for maritime areas, but the information provided does not indicate a specific source that supports this definition.

### B4 / 반복 1 — 미검증 후보

후보 답변: The S-101 definition of AnchorageArea is supported by the following sources:<br>- line:34: mapsToProduct with predicate 'mapsToProduct' and subject 'semanticmapping:regulated_area' and object 'product:s-101'<br>- line:36: mapsToProduct with predicate 'mapsToProduct' and subject 'semanticmapping:protected_area' and object 'product:s-101'<br>- line:38: mapsToProduct with predicate 'mapsToProduct' and subject 'semanticmapping:navigation_hazard_object' and object 'product:s-101'
출력 근거 ID: ["line:34", "line:36", "line:38"]
- line:34: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:36: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:38: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
B4 최초→검토후 변경 필드: []
변경 유무는 개선·수정 성공을 뜻하지 않습니다.

### B0 / 반복 1 — 미검증 후보

후보 답변: The S-101 definition of AnchorageArea is not explicitly supported by any source, as it is a specific term used in the International Regulations for Preventing Collisions at Sea (SOLAS) and is not widely documented in general sources.

### B2 / 반복 2 — 미검증 후보

후보 답변: The S-101 definition of AnchorageArea is supported by the following sources:
출력 근거 ID: ["line:34", "line:36", "line:38"]
- line:34: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:36: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:38: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87

### B3 / 반복 2 — 미검증 후보

후보 답변: The S-101 definition of AnchorageArea is supported by the source-backed location candidates provided by the 'places.resolve' tool.

### B4 / 반복 2 — 미검증 후보

후보 답변: The S-101 definition of AnchorageArea is supported by the following sources:
출력 근거 ID: ["line:34", "line:36", "line:38"]
- line:34: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:36: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
- line:38: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: outputs/graph/kg_edges_v2.jsonl; SHA-256: a25b0a7a3a015fa415afb81cc1f099032a88eef437226de8c42d33792a6a9b87
B4 최초→검토후 변경 필드: []
변경 유무는 개선·수정 성공을 뜻하지 않습니다.

### B0 / 반복 2 — 미검증 후보

후보 답변: The S-101 definition of AnchorageArea is not supported by any specific source. It is a standard term used in maritime law and is not explicitly defined in any official maritime document. It is important to consult local maritime regulations or contact a maritime law expert for a precise understanding of the definition.

### B1 / 반복 2 — 미검증 후보

후보 답변: The S-101 definition of AnchorageArea is supported by the following sources: 'Anchorage Area' in the 'AnchorageArea' feature, 'Category of Anchorage' in the 'Category of Anchorage' attribute, and 'Scale Minimum' in the 'Scale Minimum' attribute. These sources provide the necessary information to understand the specific definition and usage of the AnchorageArea feature in the S-101 dataset.
출력 근거 ID: ["features/AnchorageArea", "attributes/categoryOfAnchorage", "attributes/scaleMinimum"]
- features/AnchorageArea: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: data/s101_feature_catalogue_v2_parsed.json; SHA-256: 0d26c66d0e1afd8a6ae33629e9bc1bb929c6a3735ccd1d60f637d149a54cad37
- attributes/categoryOfAnchorage: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: data/s101_feature_catalogue_v2_parsed.json; SHA-256: 0d26c66d0e1afd8a6ae33629e9bc1bb929c6a3735ccd1d60f637d149a54cad37
- attributes/scaleMinimum: 제공 source packet에서 식별자 연결 확인. 의미적 지지 여부 미검증.
  원천 경로: data/s101_feature_catalogue_v2_parsed.json; SHA-256: 0d26c66d0e1afd8a6ae33629e9bc1bb929c6a3735ccd1d60f637d149a54cad37
