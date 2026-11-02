# 사례별 원본 근거·객체 ID·거리·해시 — 최종 편집본

검수자 표시명 AAA·BBB. AI 보조 합의제안의 근거자료이며 독립 인간 검수 완료 문서가 아니다. 공간 Oracle을 다시 실행하지 않고 동결 원본과 기존 검산 산출물을 연결했다. 거리 원값은 아래 표에 보존한다. 시설 단위 중복 제거를 새로 적용하지 않는다.

합의 제안: [AAA_BBB_합의검토_최종제안본_KR.md](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261102_gold_v2_AAA_BBB_final_proposal_v2/AAA_BBB_합의검토_최종제안본_KR.md>) · 첨부: [첨부원본_AI보조검수_A.md](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261102_gold_v2_AAA_BBB_final_proposal_v2/첨부원본_AI보조검수_A.md>) · SHA256 `de75d5208007125f74393a2be559708b370f58541e05bdeaa1ac686b07119d56`

## 해석 및 동기화 규칙

- 첨부의 spatial_source_condition=null을 그대로 정답 부재로 읽지 않는다. Q3-02/Q5-02에는 고정 부산항 polygon·원천 snapshot·객체 집합을 아래에 연결했다.
- Q3-01/Q5-01/Q5-03은 범위 밖: 공간 GOLD null. Q3-03은 영역 누락: 미실행. Q3-02의 빈 집합은 이 고정 snapshot/predicate에 한한 유효 Oracle다.
- Q5-02는 polygon 자체와 대상 geometry의 최소 거리다. polygon 외곽선만의 거리가 아니므로 내부/교차 객체의 0m는 가능하다. 동결 SQL을 변경하지 않는다.
- 정박지 3개는 snapshot 기록 3개이며 독립 실재 시설 3개로 해석하지 않는다. 연구 경계를 법적 부산항 전체 경계로 일반화하지 않는다.
- 원본 Oracle의 상태나 과거 승인 문자열은 원본 생성 당시의 기록이다. 현재 인간 승인 증거로 사용하지 않는다.

## PILOT_Q1_01 — 등대의 S-101 객체 유형과 정의를 알려줘.

- GOLD 계약: [answer_contracts.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl>) JSONL 1행
- 정규화 JSON record SHA256: `81babcf174a26b29cf097cc072e9ff44371aea8bcacd138598efd270ca5af6b8` (UTF-8, sort_keys, compact separators)
- AAA 연결 의견: 조건부 승인. '등대=Lighthouse 단일 Feature'가 아니라 구조물/등화의 조건부 조합으로 설명하는 현재 기준이 FC 구조와 부합한다.
- BBB 검토 쟁점: 네 코드를 모두 한 시설의 필수 구성으로 요구해서는 안 된다. 설명을 위한 대안 목록과 실제 객체 매핑을 구분한다.

### FC Landmark
- 원문: Any prominent object at a fixed location on land which can be used in determining a location or a direction.
- geometry: ['point', 'curve', 'surface']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Landmark']]`

### FC Building
- 원문: A free-standing self-supporting construction that is roofed, usually walled, and is intended for human occupancy (for example: a place of work or recreation) and/or habitation.
- geometry: ['point', 'surface']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Building']]`

### FC LightAllAround
- 원문: An all around light is a light that is visible over the whole horizon of interest to marine navigation and having no change in the characteristics of the light.
- geometry: ['point']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='LightAllAround']]`

### FC LightSectored
- 원문: A light presenting different appearances (in particular, different colours) over various parts of the horizon of interest to maritime navigation.
- geometry: ['point']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='LightSectored']]`


- predicate: `None` / 거리 정책: `None`
### 파일·locator 검증 기록
```json
{
  "contract_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\answer_contracts.jsonl",
  "jsonl_line": 1,
  "contract_record_sha256": "81babcf174a26b29cf097cc072e9ff44371aea8bcacd138598efd270ca5af6b8",
  "FC_source": {
    "path": "D:/An_GeoLLM/outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
    "sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
    "expected_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
    "status": "HASH_VERIFIED"
  },
  "locator_checks": [
    {
      "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Landmark']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    },
    {
      "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Building']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    },
    {
      "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='LightAllAround']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    },
    {
      "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='LightSectored']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    }
  ],
  "spatial_oracle_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\oracle_checks.json",
  "source_checks_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\source_checks.json",
  "Q4_original_csv": null,
  "Q4_calculation": null
}
```

## PILOT_Q1_02 — S-101에서 정박지는 어떤 객체야?

- GOLD 계약: [answer_contracts.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl>) JSONL 2행
- 정규화 JSON record SHA256: `15705a461a7c4b4669073e5c75afe879e394d921f99b8dc52a8bad4d80547c42` (UTF-8, sort_keys, compact separators)
- AAA 연결 의견: 승인. 현재 FC 정의와 feature mapping이 직접 일치한다.
- BBB 검토 쟁점: 일반 정박 행위와 데이터 객체의 존재를 혼동하지 않는다. 정의 질의에는 공간 실행이 필요하지 않다.

### FC AnchorageArea
- 원문: An area in which vessels or seaplanes anchor or may anchor.
- geometry: ['point', 'surface']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]`


- predicate: `None` / 거리 정책: `None`
### 파일·locator 검증 기록
```json
{
  "contract_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\answer_contracts.jsonl",
  "jsonl_line": 2,
  "contract_record_sha256": "15705a461a7c4b4669073e5c75afe879e394d921f99b8dc52a8bad4d80547c42",
  "FC_source": {
    "path": "D:/An_GeoLLM/outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
    "sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
    "expected_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
    "status": "HASH_VERIFIED"
  },
  "locator_checks": [
    {
      "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    }
  ],
  "spatial_oracle_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\oracle_checks.json",
  "source_checks_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\source_checks.json",
  "Q4_original_csv": null,
  "Q4_calculation": null
}
```

## PILOT_Q1_03 — What is a wreck in S-101?

- GOLD 계약: [answer_contracts.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl>) JSONL 3행
- 정규화 JSON record SHA256: `3f4d5b57299275c6c76fe1a15cf4d10ecf8ea4e1cb02ae9184689d96864fbcfa` (UTF-8, sort_keys, compact separators)
- AAA 연결 의견: 승인. FC의 Wreck 정의와 직접 부합한다.
- BBB 검토 쟁점: 침선 개념 설명을 실제 침선 위치 검색으로 바꾸지 않는다. 원문과 동등한 의역도 의미 검수 대상이다.

### FC Wreck
- 원문: The ruined remains of a stranded or sunken vessel which has been rendered useless.
- geometry: ['point', 'surface']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]`


- predicate: `None` / 거리 정책: `None`
### 파일·locator 검증 기록
```json
{
  "contract_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\answer_contracts.jsonl",
  "jsonl_line": 3,
  "contract_record_sha256": "3f4d5b57299275c6c76fe1a15cf4d10ecf8ea4e1cb02ae9184689d96864fbcfa",
  "FC_source": {
    "path": "D:/An_GeoLLM/outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
    "sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
    "expected_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
    "status": "HASH_VERIFIED"
  },
  "locator_checks": [
    {
      "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    }
  ],
  "spatial_oracle_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\oracle_checks.json",
  "source_checks_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\source_checks.json",
  "Q4_original_csv": null,
  "Q4_calculation": null
}
```

## PILOT_Q2_01 — S-101 등대의 색상 속성과 허용 값을 알려줘.

- GOLD 계약: [answer_contracts.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl>) JSONL 4행
- 정규화 JSON record SHA256: `1c605e0e61e3982c9edc8926370751d88f4091dffa37cde56495412345d4138b` (UTF-8, sort_keys, compact separators)
- AAA 연결 의견: 승인. 전역 colour 코드와 Feature binding 허용값을 구분하는 현재 기준이 타당하다.
- BBB 검토 쟁점: LightSectored→sectorCharacteristics→lightSector→colour 경로를 확인한다. 전역 colour 코드 목록을 모든 Feature의 허용값으로 복사하지 않는다.

### FC Landmark
- 원문: Any prominent object at a fixed location on land which can be used in determining a location or a direction.
- geometry: ['point', 'curve', 'surface']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Landmark']]`

### FC Building
- 원문: A free-standing self-supporting construction that is roofed, usually walled, and is intended for human occupancy (for example: a place of work or recreation) and/or habitation.
- geometry: ['point', 'surface']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Building']]`

### FC LightAllAround
- 원문: An all around light is a light that is visible over the whole horizon of interest to marine navigation and having no change in the characteristics of the light.
- geometry: ['point']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='LightAllAround']]`

### FC LightSectored
- 원문: A light presenting different appearances (in particular, different colours) over various parts of the horizon of interest to maritime navigation.
- geometry: ['point']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='LightSectored']]`

| 소유/속성 | 다중성 | 연결된 코드와 명칭 |
|---|---|---|
| Landmark → colour | 0..* | 1: White, 2: Black, 3: Red, 4: Green, 5: Blue, 6: Yellow, 7: Grey, 8: Brown, 9: Amber, 10: Violet, 11: Orange, 12: Magenta, 13: Pink |
| Building → colour | 0..* | 1: White, 2: Black, 3: Red, 4: Green, 5: Blue, 6: Yellow, 7: Grey, 8: Brown, 9: Amber, 10: Violet, 11: Orange, 12: Magenta, 13: Pink |
| LightAllAround → colour | 1..* | 1: White, 3: Red, 4: Green, 5: Blue, 6: Yellow, 9: Amber, 10: Violet, 11: Orange |
| LightSectored → sectorCharacteristics | 1..* | 복합/수치 등, 코드목록 없음 |
| sectorCharacteristics → lightSector | 1..* | 복합/수치 등, 코드목록 없음 |
| lightSector → colour | 1..* | 1: White, 3: Red, 4: Green, 5: Blue, 6: Yellow, 9: Amber, 10: Violet, 11: Orange |

- predicate: `None` / 거리 정책: `None`
### 파일·locator 검증 기록
```json
{
  "contract_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\answer_contracts.jsonl",
  "jsonl_line": 4,
  "contract_record_sha256": "1c605e0e61e3982c9edc8926370751d88f4091dffa37cde56495412345d4138b",
  "FC_source": {
    "path": "D:/An_GeoLLM/outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
    "sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
    "expected_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
    "status": "HASH_VERIFIED"
  },
  "locator_checks": [
    {
      "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Landmark']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    },
    {
      "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Building']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    },
    {
      "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='LightAllAround']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    },
    {
      "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='LightSectored']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    },
    {
      "locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='colour']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    },
    {
      "locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='sectorCharacteristics']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    },
    {
      "locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='lightSector']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    }
  ],
  "spatial_oracle_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\oracle_checks.json",
  "source_checks_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\source_checks.json",
  "Q4_original_csv": null,
  "Q4_calculation": null
}
```

## PILOT_Q2_02 — 제한구역의 제한 종류는 어떤 코드로 표현해?

- GOLD 계약: [answer_contracts.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl>) JSONL 5행
- 정규화 JSON record SHA256: `66af138ff276d3dc301304e40a23ef64b2eb7ff202d5e78cea9b2db0f1d869a9` (UTF-8, sort_keys, compact separators)
- AAA 연결 의견: 승인. 질의의 '제한 종류'는 restriction을 중심으로 답하되 categoryOfRestrictedArea와 혼동하지 않도록 둘을 분리하는 기준이 적절하다.
- BBB 검토 쟁점: 구역 종류 코드와 실제 제한 행위 코드는 다른 속성이다. 공개 FC 설명을 실제 구역의 법적 허가 또는 비공개 자료 요청으로 해석하지 않는다.

### FC RestrictedArea
- 원문: A specified area on land or water designated by an appropriate authority within which access or navigation is restricted in accordance with certain specified conditions.
- geometry: ['surface']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='RestrictedArea']]`

| 소유/속성 | 다중성 | 연결된 코드와 명칭 |
|---|---|---|
| RestrictedArea → categoryOfRestrictedArea | 0..* | 1: Offshore Safety Zone, 4: Nature Reserve, 5: Bird Sanctuary, 6: Game Reserve, 7: Seal Sanctuary, 8: Degaussing Range, 9: Military Area, 10: Historic Wreck Area, 12: Navigational Aid Safety Zone, 14: Minefield, 18: Swimming Area, 19: Waiting Area, 20: Research Area, 21: Dredging Area, 22: Fish Sanctuary, 23: Ecological Reserve, 24: No Wake Area, 25: Swinging Area, 27: Environmentally Sensitive Sea Area, 28: Particularly Sensitive Sea Area, 29: Disengagement Area, 30: Port Security Area, 31: Coral Sanctuary, 32: Recreation Area |
| RestrictedArea → restriction | 1..* | 1: Anchoring Prohibited, 2: Anchoring Restricted, 3: Fishing Prohibited, 4: Fishing Restricted, 5: Trawling Prohibited, 6: Trawling Restricted, 7: Entry Prohibited, 8: Entry Restricted, 9: Dredging Prohibited, 10: Dredging Restricted, 11: Diving Prohibited, 12: Diving Restricted, 13: No Wake, 14: Area To Be Avoided, 15: Construction Prohibited, 16: Discharging Prohibited, 17: Discharging Restricted, 18: Industrial or Mineral Exploration/Development Prohibited, 19: Industrial or Mineral Exploration/Development Restricted, 20: Drilling Prohibited, 21: Drilling Restricted, 22: Removal of Historical Artefacts Prohibited, 23: Cargo Transhipment (Lightening) Prohibited, 24: Dragging Prohibited, 25: Stopping Prohibited, 26: Landing Prohibited, 27: Speed Restricted, 39: Swimming Prohibited, 42: Power-Driven Vessels Prohibited |

- predicate: `None` / 거리 정책: `None`
### 파일·locator 검증 기록
```json
{
  "contract_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\answer_contracts.jsonl",
  "jsonl_line": 5,
  "contract_record_sha256": "66af138ff276d3dc301304e40a23ef64b2eb7ff202d5e78cea9b2db0f1d869a9",
  "FC_source": {
    "path": "D:/An_GeoLLM/outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
    "sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
    "expected_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
    "status": "HASH_VERIFIED"
  },
  "locator_checks": [
    {
      "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='RestrictedArea']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    },
    {
      "locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='categoryOfRestrictedArea']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    },
    {
      "locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='restriction']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    }
  ],
  "spatial_oracle_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\oracle_checks.json",
  "source_checks_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\source_checks.json",
  "Q4_original_csv": null,
  "Q4_calculation": null
}
```

## PILOT_Q2_03 — Which attributes describe a Wreck in S-101?

- GOLD 계약: [answer_contracts.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl>) JSONL 6행
- 정규화 JSON record SHA256: `a5b8ee594911da51c3445af17b68b9836577bafe2f7c3165016b6edb62dd229f` (UTF-8, sort_keys, compact separators)
- AAA 연결 의견: 승인. 현재 frozen_v5의 FC direct binding 목록과 일치한다.
- BBB 검토 쟁점: FC 속성 정의와 특정 침선의 실제 속성값은 별개다. 전역에 존재하는 속성을 Wreck에 연결된 것으로 추정하지 않는다.

### FC Wreck
- 원문: The ruined remains of a stranded or sunken vessel which has been rendered useless.
- geometry: ['point', 'surface']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]`

| 소유/속성 | 다중성 | 연결된 코드와 명칭 |
|---|---|---|
| Wreck → categoryOfWreck | 0..1 | 1: Non-Dangerous Wreck, 2: Dangerous Wreck, 3: Distributed Remains of Wreck, 4: Wreck Showing Mast/Masts, 5: Wreck Showing Any Portion of Hull or Superstructure |
| Wreck → expositionOfSounding | 0..1 | 1: Within the Range of Depth of the Surrounding Depth Area, 2: Shoaler Than the Range of Depth of the Surrounding Depth Area, 3: Deeper Than the Range of Depth of the Surrounding Depth Area |
| Wreck → featureName | 0..* | 복합/수치 등, 코드목록 없음 |
| Wreck → height | 0..1 | 복합/수치 등, 코드목록 없음 |
| Wreck → interoperabilityIdentifier | 0..1 | 복합/수치 등, 코드목록 없음 |
| Wreck → qualityOfVerticalMeasurement | 0..* | 1: Depth Known, 2: Depth or Least Depth Unknown, 3: Doubtful Sounding, 4: Unreliable Sounding, 6: Least Depth Known, 7: Least Depth Unknown, Safe Clearance at Value Shown, 8: Value Reported (Not Surveyed), 9: Value Reported (Not Confirmed) |
| Wreck → radarConspicuous | 0..1 | 복합/수치 등, 코드목록 없음 |
| Wreck → reportedDate | 0..1 | 복합/수치 등, 코드목록 없음 |
| Wreck → status | 0..* | 7: Temporary, 13: Historic, 18: Existence Doubtful |
| Wreck → techniqueOfVerticalMeasurement | 0..* | 1: Found by Echo Sounder, 2: Found by Side Scan Sonar, 3: Found by Multi Beam, 4: Found by Diver, 5: Found by Lead Line, 8: Swept by Vertical Acoustic System, 9: Found by Electromagnetic Sensor, 10: Photogrammetry, 11: Satellite Imagery, 12: Found by Levelling, 13: Swept by Side Scan Sonar, 15: Found by LIDAR, 16: Synthetic Aperture Radar, 17: Hyperspectral Imagery, 18: Mechanically Swept |
| Wreck → valueOfSounding | 0..1 | 복합/수치 등, 코드목록 없음 |
| Wreck → visualProminence | 0..1 | 1: Visually Conspicuous, 2: Not Visually Conspicuous, 3: Prominent |
| Wreck → waterLevelEffect | 1..1 | 1: Partly Submerged at High Water, 2: Always Dry, 3: Always Under Water/Submerged, 4: Covers and Uncovers, 5: Awash |
| Wreck → scaleMinimum | 0..1 | 복합/수치 등, 코드목록 없음 |
| Wreck → information | 0..* | 복합/수치 등, 코드목록 없음 |
| Wreck → pictorialRepresentation | 0..1 | 복합/수치 등, 코드목록 없음 |
| Wreck → defaultClearanceDepth | 0..1 | 복합/수치 등, 코드목록 없음 |
| Wreck → surroundingDepth | 1..1 | 복합/수치 등, 코드목록 없음 |

- predicate: `None` / 거리 정책: `None`
### 파일·locator 검증 기록
```json
{
  "contract_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\answer_contracts.jsonl",
  "jsonl_line": 6,
  "contract_record_sha256": "a5b8ee594911da51c3445af17b68b9836577bafe2f7c3165016b6edb62dd229f",
  "FC_source": {
    "path": "D:/An_GeoLLM/outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
    "sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
    "expected_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
    "status": "HASH_VERIFIED"
  },
  "locator_checks": [
    {
      "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    },
    {
      "locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='categoryOfWreck']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    },
    {
      "locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='expositionOfSounding']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    },
    {
      "locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='featureName']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    },
    {
      "locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='height']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    },
    {
      "locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='interoperabilityIdentifier']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    },
    {
      "locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='qualityOfVerticalMeasurement']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    },
    {
      "locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='radarConspicuous']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    },
    {
      "locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='reportedDate']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    },
    {
      "locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='status']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    },
    {
      "locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='techniqueOfVerticalMeasurement']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    },
    {
      "locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='valueOfSounding']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    },
    {
      "locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='visualProminence']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    },
    {
      "locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='waterLevelEffect']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    },
    {
      "locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='scaleMinimum']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    },
    {
      "locator": "//*[local-name()='S100_FC_ComplexAttribute'][*[local-name()='code' and text()='information']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    },
    {
      "locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='pictorialRepresentation']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    },
    {
      "locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='defaultClearanceDepth']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    },
    {
      "locator": "//*[local-name()='S100_FC_SimpleAttribute'][*[local-name()='code' and text()='surroundingDepth']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    }
  ],
  "spatial_oracle_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\oracle_checks.json",
  "source_checks_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\source_checks.json",
  "Q4_original_csv": null,
  "Q4_calculation": null
}
```

## PILOT_Q3_01 — 독도 부근에서 가장 가까운 등대를 찾아줘.

- GOLD 계약: [answer_contracts.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl>) JSONL 7행
- 정규화 JSON record SHA256: `e5bc6a306d3000b245d85baf34f22c077178e43c936f4b7653969ad724a16e64` (UTF-8, sort_keys, compact separators)
- AAA 연결 의견: 승인. nearest를 1km 기본반경으로 바꾸지 않고 coverage 부족을 안전중단으로 처리하는 기준이 타당하다.
- BBB 검토 쟁점: 전국 최근접 계산의 정답이나 실세계 0건으로 만들지 않는다. 단순 UNSUPPORTED_OPERATOR 차단은 올바른 coverage 판단 전체를 충족하지 않는다.


### 범위 밖 정답 행동
```json
{
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
```

- predicate: `None` / 거리 정책: `None`
### 파일·locator 검증 기록
```json
{
  "contract_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\answer_contracts.jsonl",
  "jsonl_line": 7,
  "contract_record_sha256": "e5bc6a306d3000b245d85baf34f22c077178e43c936f4b7653969ad724a16e64",
  "FC_source": null,
  "locator_checks": [],
  "spatial_oracle_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\oracle_checks.json",
  "source_checks_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\source_checks.json",
  "Q4_original_csv": null,
  "Q4_calculation": null
}
```

## PILOT_Q3_02 — 부산항 영역 안의 정박지를 찾아줘.

- GOLD 계약: [answer_contracts.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl>) JSONL 8행
- 정규화 JSON record SHA256: `ee0c7885bc263af6c93657df474baf2bc46d860444006fdc7b9c2e99baaa78a1` (UTF-8, sort_keys, compact separators)
- AAA 연결 의견: 조건부 승인. 연구 재현성에는 충분하지만 법적 부산항 항계라고 표현하면 안 된다.
- BBB 검토 쟁점: 유효한 빈 Oracle과 미실행/누락은 다르다. 이 polygon은 연구용 고정 경계이며 법적 항계 전체와 동일하다고 단정하지 않는다.


### 고정 기준기하 (첨부 null 보완)
```json
{
  "id": "1137770",
  "dataset_id": 540,
  "dataset_version_id": 540,
  "dataset_name": "101KR00658D00.000",
  "min_scale": 16,
  "max_scale": 18,
  "srid": 4326,
  "product_specification": "INT.IHO.S-101.2.0",
  "geometry_sha256": "af271cb3a14c95cc34cedaade127bfbb87b26bc3c6a96fb1755338e2266a5af0",
  "dataset_snapshot_sha256": "1300232a3f03d17ea822eeff55fde99c5458b836f86d26bfd445b9afe8bb7f85",
  "layer_name": "projection.s101_feature_current/HarbourAreaAdministrative",
  "boundary_source": "snapshot S-101 feature, not independently verified legal full-port boundary",
  "selection_policy": "single exact-name polygon, most detailed min_scale, full 2km extent inside snapshot bbox, largest area then smallest feature ID",
  "coverage_bbox": [
    128.9,
    34.9,
    129.3,
    35.3
  ],
  "coverage_boundary_margin_m": 4561.66668103,
  "selection_status": "FIXED_RESEARCH_REFERENCE_UNDER_USER_SINGLE_POLYGON_POLICY"
}
```

### AnchorageArea: 0개 snapshot 기록
- 원천 snapshot SHA256: `1300232a3f03d17ea822eeff55fde99c5458b836f86d26bfd445b9afe8bb7f85`
- 전체 ID: `[] (유효 빈 집합)`
| 객체 ID | 기준 polygon 최소 거리(m) | dataset / version |
|---|---:|---|
- 거리 최소/최대: 해당 없음 / 해당 없음 m.

- predicate: `ST_Covers(reference,target)` / 거리 정책: `minimum polygon-area to target geometry distance; overlapping/inside=0`
### 파일·locator 검증 기록
```json
{
  "contract_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\answer_contracts.jsonl",
  "jsonl_line": 8,
  "contract_record_sha256": "ee0c7885bc263af6c93657df474baf2bc46d860444006fdc7b9c2e99baaa78a1",
  "FC_source": null,
  "locator_checks": [],
  "spatial_oracle_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\oracle_checks.json",
  "source_checks_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\source_checks.json",
  "Q4_original_csv": null,
  "Q4_calculation": null
}
```

## PILOT_Q3_03 — Find wrecks intersecting the selected area.

- GOLD 계약: [answer_contracts.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl>) JSONL 9행
- 정규화 JSON record SHA256: `1e22a5d5ebb92f1a9b1a46f55da9b27ed8c3918fb98529d940fddd68a29a3cb2` (UTF-8, sort_keys, compact separators)
- AAA 연결 의견: 승인. missing input과 공간 0건을 구분하는 기준이 명확하다.
- BBB 검토 쟁점: 임의 viewport나 기준점으로 대체하지 않는다. 안내 문구만으로 미실행을 인정하지 말고 실행 로그를 확인한다.


- predicate: `None` / 거리 정책: `None`
### 파일·locator 검증 기록
```json
{
  "contract_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\answer_contracts.jsonl",
  "jsonl_line": 9,
  "contract_record_sha256": "1e22a5d5ebb92f1a9b1a46f55da9b27ed8c3918fb98529d940fddd68a29a3cb2",
  "FC_source": null,
  "locator_checks": [],
  "spatial_oracle_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\oracle_checks.json",
  "source_checks_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\source_checks.json",
  "Q4_original_csv": null,
  "Q4_calculation": null
}
```

## PILOT_Q4_01 — 독도 주변 반경 5km의 해양지명을 찾아줘.

- GOLD 계약: [answer_contracts.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl>) JSONL 10행
- 정규화 JSON record SHA256: `0cb27baee7c68b4561d814143ed423e143e8efde9d37a6bbab836707286c2efb` (UTF-8, sort_keys, compact separators)
- AAA 연결 의견: 승인. PostGIS/Vincenty membership 검산과 source-bound scope가 명시돼 있다.
- BBB 검토 쟁점: 원천 corpus의 정답이며 독도 주변 실세계 지명의 완전목록이 아니다. S-101 ID와 CSV 원본 ID를 혼용하지 않는다.


### 동도 기준점·CSV 지명 거리
- 기준점: `{"place_id": "mof:dokdo:east-island", "label": "독도", "aliases": ["Dokdo", "독도 동도", "독도(동도)"], "longitude": 131.86955555555556, "latitude": 37.24077777777778, "source_url": "https://www.mof.go.kr/doc/ko/selectDoc.do?bbsSeq=27&docSeq=20937&menuSeq=929", "source_title": "해양수산부 독도의 주소와 위치", "source_coordinates": "동도 북위 37도 14분 26.8초, 동경 131도 52분 10.4초", "coordinate_role": "published_east_island_reference_point", "note": "독도 부근 검색의 동도 기준점이며 독도 전체 경계 또는 항행 안전 기준점이 아니다."}`
- 정책: WGS84 ellipsoidal geodesic, inclusive <=5000m
- CSV SHA256: `bbc3f1c347f6048b0befdf5102959078ffc29c22cdc4412a98586e76cddb0464`
- Oracle SHA256: `cf7e407ec904661093a187e15391b42bc668a6e6ef5f75ead3f96c3f495cb9fb`
| 원본 객체 ID | 지명 | CSV 행 | PostGIS 거리(m) | Vincenty 거리(m) |
|---|---|---:|---:|---:|
| mof_marine_names_20221231:44 | 북향초 | 47 | 1009.22973215 | 1009.2297312593255 |
| mof_marine_names_20221231:45 | 가지초 | 48 | 959.4090081 | 959.4090075635844 |
| mof_marine_names_20221231:46 | 강치초 | 49 | 863.77507984 | 863.7750788791387 |
| mof_marine_names_20221231:47 | 가제초 | 50 | 844.86372327 | 844.8637232673918 |
| mof_marine_names_20221231:48 | 삼봉초 | 51 | 696.70086772 | 696.700865804542 |
| mof_marine_names_20221231:49 | 괭이초 | 52 | 514.18019688 | 514.1801960687372 |
| mof_marine_names_20221231:50 | 서도초 | 53 | 1123.07057171 | 1123.070571692745 |
| mof_marine_names_20221231:51 | 군함초 | 54 | 840.21948619 | 840.2194861787266 |
| mof_marine_names_20221231:52 | 넙덕초 | 55 | 810.36452661 | 810.3645265974295 |
| mof_marine_names_20221231:53 | 부채초 | 56 | 363.89288007 | 363.89287903283474 |
| mof_marine_names_20221231:54 | 동도초 | 57 | 281.37189895 | 281.3718980308276 |

- predicate: `None` / 거리 정책: `None`
### 파일·locator 검증 기록
```json
{
  "contract_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\answer_contracts.jsonl",
  "jsonl_line": 10,
  "contract_record_sha256": "0cb27baee7c68b4561d814143ed423e143e8efde9d37a6bbab836707286c2efb",
  "FC_source": null,
  "locator_checks": [],
  "spatial_oracle_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\oracle_checks.json",
  "source_checks_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\source_checks.json",
  "Q4_original_csv": {
    "path": "D:/An_GeoLLM/Dataset/해양수산부_공동활용체계_해양지명_20221231.csv",
    "sha256": "bbc3f1c347f6048b0befdf5102959078ffc29c22cdc4412a98586e76cddb0464",
    "expected_sha256": "bbc3f1c347f6048b0befdf5102959078ffc29c22cdc4412a98586e76cddb0464",
    "status": "HASH_VERIFIED"
  },
  "Q4_calculation": {
    "path": "D:/An_GeoLLM/outputs/scie_dokdo_reference_20261030_v2/spatial_reference.json",
    "sha256": "cf7e407ec904661093a187e15391b42bc668a6e6ef5f75ead3f96c3f495cb9fb",
    "expected_sha256": "cf7e407ec904661093a187e15391b42bc668a6e6ef5f75ead3f96c3f495cb9fb",
    "status": "HASH_VERIFIED"
  }
}
```

## PILOT_Q4_02 — 독도 주변 반경 5000m의 해양지명을 찾아줘.

- GOLD 계약: [answer_contracts.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl>) JSONL 11행
- 정규화 JSON record SHA256: `0dcf4dd99e99c1fd3d9e012a6eb3eb94f9d1c6d5364c75e704c0b13775c1bfde` (UTF-8, sort_keys, compact separators)
- AAA 연결 의견: 승인. 5km와 5000m의 단위 등가성 검증 사례로 적절하다.
- BBB 검토 쟁점: 단위 변환은 허용되지만 반경·기준점·원천은 변경하지 않는다. 세 표현을 독립 공간 문제로 합산하지 않는다.


### 동도 기준점·CSV 지명 거리
- 기준점: `{"place_id": "mof:dokdo:east-island", "label": "독도", "aliases": ["Dokdo", "독도 동도", "독도(동도)"], "longitude": 131.86955555555556, "latitude": 37.24077777777778, "source_url": "https://www.mof.go.kr/doc/ko/selectDoc.do?bbsSeq=27&docSeq=20937&menuSeq=929", "source_title": "해양수산부 독도의 주소와 위치", "source_coordinates": "동도 북위 37도 14분 26.8초, 동경 131도 52분 10.4초", "coordinate_role": "published_east_island_reference_point", "note": "독도 부근 검색의 동도 기준점이며 독도 전체 경계 또는 항행 안전 기준점이 아니다."}`
- 정책: WGS84 ellipsoidal geodesic, inclusive <=5000m
- CSV SHA256: `bbc3f1c347f6048b0befdf5102959078ffc29c22cdc4412a98586e76cddb0464`
- Oracle SHA256: `cf7e407ec904661093a187e15391b42bc668a6e6ef5f75ead3f96c3f495cb9fb`
| 원본 객체 ID | 지명 | CSV 행 | PostGIS 거리(m) | Vincenty 거리(m) |
|---|---|---:|---:|---:|
| mof_marine_names_20221231:44 | 북향초 | 47 | 1009.22973215 | 1009.2297312593255 |
| mof_marine_names_20221231:45 | 가지초 | 48 | 959.4090081 | 959.4090075635844 |
| mof_marine_names_20221231:46 | 강치초 | 49 | 863.77507984 | 863.7750788791387 |
| mof_marine_names_20221231:47 | 가제초 | 50 | 844.86372327 | 844.8637232673918 |
| mof_marine_names_20221231:48 | 삼봉초 | 51 | 696.70086772 | 696.700865804542 |
| mof_marine_names_20221231:49 | 괭이초 | 52 | 514.18019688 | 514.1801960687372 |
| mof_marine_names_20221231:50 | 서도초 | 53 | 1123.07057171 | 1123.070571692745 |
| mof_marine_names_20221231:51 | 군함초 | 54 | 840.21948619 | 840.2194861787266 |
| mof_marine_names_20221231:52 | 넙덕초 | 55 | 810.36452661 | 810.3645265974295 |
| mof_marine_names_20221231:53 | 부채초 | 56 | 363.89288007 | 363.89287903283474 |
| mof_marine_names_20221231:54 | 동도초 | 57 | 281.37189895 | 281.3718980308276 |

- predicate: `None` / 거리 정책: `None`
### 파일·locator 검증 기록
```json
{
  "contract_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\answer_contracts.jsonl",
  "jsonl_line": 11,
  "contract_record_sha256": "0dcf4dd99e99c1fd3d9e012a6eb3eb94f9d1c6d5364c75e704c0b13775c1bfde",
  "FC_source": null,
  "locator_checks": [],
  "spatial_oracle_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\oracle_checks.json",
  "source_checks_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\source_checks.json",
  "Q4_original_csv": {
    "path": "D:/An_GeoLLM/Dataset/해양수산부_공동활용체계_해양지명_20221231.csv",
    "sha256": "bbc3f1c347f6048b0befdf5102959078ffc29c22cdc4412a98586e76cddb0464",
    "expected_sha256": "bbc3f1c347f6048b0befdf5102959078ffc29c22cdc4412a98586e76cddb0464",
    "status": "HASH_VERIFIED"
  },
  "Q4_calculation": {
    "path": "D:/An_GeoLLM/outputs/scie_dokdo_reference_20261030_v2/spatial_reference.json",
    "sha256": "cf7e407ec904661093a187e15391b42bc668a6e6ef5f75ead3f96c3f495cb9fb",
    "expected_sha256": "cf7e407ec904661093a187e15391b42bc668a6e6ef5f75ead3f96c3f495cb9fb",
    "status": "HASH_VERIFIED"
  }
}
```

## PILOT_Q4_03 — Find marine place names within 5 km of Dokdo.

- GOLD 계약: [answer_contracts.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl>) JSONL 12행
- 정규화 JSON record SHA256: `031d4bcfe49d35891520958cdfbf52d72ccf5d0ae888dcb564e0cf386bca10f9` (UTF-8, sort_keys, compact separators)
- AAA 연결 의견: 승인. 언어 표현 변화에 대한 동등성 검증으로 적절하다.
- BBB 검토 쟁점: 언어 차이만으로 공간 의미나 coverage를 바꾸지 않는다. 개발 노출된 동등 표현군이며 독립 holdout이 아니다.


### 동도 기준점·CSV 지명 거리
- 기준점: `{"place_id": "mof:dokdo:east-island", "label": "독도", "aliases": ["Dokdo", "독도 동도", "독도(동도)"], "longitude": 131.86955555555556, "latitude": 37.24077777777778, "source_url": "https://www.mof.go.kr/doc/ko/selectDoc.do?bbsSeq=27&docSeq=20937&menuSeq=929", "source_title": "해양수산부 독도의 주소와 위치", "source_coordinates": "동도 북위 37도 14분 26.8초, 동경 131도 52분 10.4초", "coordinate_role": "published_east_island_reference_point", "note": "독도 부근 검색의 동도 기준점이며 독도 전체 경계 또는 항행 안전 기준점이 아니다."}`
- 정책: WGS84 ellipsoidal geodesic, inclusive <=5000m
- CSV SHA256: `bbc3f1c347f6048b0befdf5102959078ffc29c22cdc4412a98586e76cddb0464`
- Oracle SHA256: `cf7e407ec904661093a187e15391b42bc668a6e6ef5f75ead3f96c3f495cb9fb`
| 원본 객체 ID | 지명 | CSV 행 | PostGIS 거리(m) | Vincenty 거리(m) |
|---|---|---:|---:|---:|
| mof_marine_names_20221231:44 | 북향초 | 47 | 1009.22973215 | 1009.2297312593255 |
| mof_marine_names_20221231:45 | 가지초 | 48 | 959.4090081 | 959.4090075635844 |
| mof_marine_names_20221231:46 | 강치초 | 49 | 863.77507984 | 863.7750788791387 |
| mof_marine_names_20221231:47 | 가제초 | 50 | 844.86372327 | 844.8637232673918 |
| mof_marine_names_20221231:48 | 삼봉초 | 51 | 696.70086772 | 696.700865804542 |
| mof_marine_names_20221231:49 | 괭이초 | 52 | 514.18019688 | 514.1801960687372 |
| mof_marine_names_20221231:50 | 서도초 | 53 | 1123.07057171 | 1123.070571692745 |
| mof_marine_names_20221231:51 | 군함초 | 54 | 840.21948619 | 840.2194861787266 |
| mof_marine_names_20221231:52 | 넙덕초 | 55 | 810.36452661 | 810.3645265974295 |
| mof_marine_names_20221231:53 | 부채초 | 56 | 363.89288007 | 363.89287903283474 |
| mof_marine_names_20221231:54 | 동도초 | 57 | 281.37189895 | 281.3718980308276 |

- predicate: `None` / 거리 정책: `None`
### 파일·locator 검증 기록
```json
{
  "contract_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\answer_contracts.jsonl",
  "jsonl_line": 12,
  "contract_record_sha256": "031d4bcfe49d35891520958cdfbf52d72ccf5d0ae888dcb564e0cf386bca10f9",
  "FC_source": null,
  "locator_checks": [],
  "spatial_oracle_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\oracle_checks.json",
  "source_checks_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\source_checks.json",
  "Q4_original_csv": {
    "path": "D:/An_GeoLLM/Dataset/해양수산부_공동활용체계_해양지명_20221231.csv",
    "sha256": "bbc3f1c347f6048b0befdf5102959078ffc29c22cdc4412a98586e76cddb0464",
    "expected_sha256": "bbc3f1c347f6048b0befdf5102959078ffc29c22cdc4412a98586e76cddb0464",
    "status": "HASH_VERIFIED"
  },
  "Q4_calculation": {
    "path": "D:/An_GeoLLM/outputs/scie_dokdo_reference_20261030_v2/spatial_reference.json",
    "sha256": "cf7e407ec904661093a187e15391b42bc668a6e6ef5f75ead3f96c3f495cb9fb",
    "expected_sha256": "cf7e407ec904661093a187e15391b42bc668a6e6ef5f75ead3f96c3f495cb9fb",
    "status": "HASH_VERIFIED"
  }
}
```

## PILOT_Q5_01 — 독도 주변 5km의 등대와 난파선을 찾아 각각의 근거를 알려줘.

- GOLD 계약: [answer_contracts.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl>) JSONL 13행
- 정규화 JSON record SHA256: `38449664101b89df898864ea9e4d914ab28097fccf021af43249cb531ff50d64` (UTF-8, sort_keys, compact separators)
- AAA 연결 의견: 승인. 복합질의의 partial/full success와 coverage를 분리하는 기준이 타당하다.
- BBB 검토 쟁점: 한 대상만 처리하고 전체 완료로 선언하거나 두 빈 집합을 실세계 부재로 제시하면 안 된다. 대상별 상태·근거가 필요하다.

### FC Landmark
- 원문: Any prominent object at a fixed location on land which can be used in determining a location or a direction.
- geometry: ['point', 'curve', 'surface']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Landmark']]`

### FC Building
- 원문: A free-standing self-supporting construction that is roofed, usually walled, and is intended for human occupancy (for example: a place of work or recreation) and/or habitation.
- geometry: ['point', 'surface']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Building']]`

### FC LightAllAround
- 원문: An all around light is a light that is visible over the whole horizon of interest to marine navigation and having no change in the characteristics of the light.
- geometry: ['point']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='LightAllAround']]`

### FC LightSectored
- 원문: A light presenting different appearances (in particular, different colours) over various parts of the horizon of interest to maritime navigation.
- geometry: ['point']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='LightSectored']]`

### FC Wreck
- 원문: The ruined remains of a stranded or sunken vessel which has been rendered useless.
- geometry: ['point', 'surface']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]`


### 범위 밖 정답 행동
```json
{
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
```

- predicate: `None` / 거리 정책: `None`
### 파일·locator 검증 기록
```json
{
  "contract_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\answer_contracts.jsonl",
  "jsonl_line": 13,
  "contract_record_sha256": "38449664101b89df898864ea9e4d914ab28097fccf021af43249cb531ff50d64",
  "FC_source": {
    "path": "D:/An_GeoLLM/outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
    "sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
    "expected_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
    "status": "HASH_VERIFIED"
  },
  "locator_checks": [
    {
      "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Landmark']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    },
    {
      "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Building']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    },
    {
      "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='LightAllAround']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    },
    {
      "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='LightSectored']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    },
    {
      "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    }
  ],
  "spatial_oracle_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\oracle_checks.json",
  "source_checks_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\source_checks.json",
  "Q4_original_csv": null,
  "Q4_calculation": null
}
```

## PILOT_Q5_02 — 부산항 주변 2km의 정박지와 제한구역을 찾아 비교해줘.

- GOLD 계약: [answer_contracts.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl>) JSONL 14행
- 정규화 JSON record SHA256: `96a2767035cae2bdc2c9a1c5530194d676d236e9db86ed30b93434d4280adba2` (UTF-8, sort_keys, compact separators)
- AAA 연결 의견: 조건부 승인. 공간 oracle은 명확하나 검수 양식의 spatial_source_condition=null은 최종 인간 검수 전에 현재 GOLD v2 기준으로 동기화하는 것이 바람직하다.
- BBB 검토 쟁점: 표현상 polygon 경계 거리와 ST_DWithin(polygon,target)의 내부거리 0은 다를 수 있다. 동결 계약의 실제 predicate를 우선 보존하고 사람이 의미를 확인한다. ID는 snapshot 기록이며 중복 시설 제거 결과가 아니다.

### FC AnchorageArea
- 원문: An area in which vessels or seaplanes anchor or may anchor.
- geometry: ['point', 'surface']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]`

### FC RestrictedArea
- 원문: A specified area on land or water designated by an appropriate authority within which access or navigation is restricted in accordance with certain specified conditions.
- geometry: ['surface']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='RestrictedArea']]`


### 고정 기준기하 (첨부 null 보완)
```json
{
  "id": "1137770",
  "dataset_id": 540,
  "dataset_version_id": 540,
  "dataset_name": "101KR00658D00.000",
  "min_scale": 16,
  "max_scale": 18,
  "srid": 4326,
  "product_specification": "INT.IHO.S-101.2.0",
  "geometry_sha256": "af271cb3a14c95cc34cedaade127bfbb87b26bc3c6a96fb1755338e2266a5af0",
  "dataset_snapshot_sha256": "1300232a3f03d17ea822eeff55fde99c5458b836f86d26bfd445b9afe8bb7f85",
  "layer_name": "projection.s101_feature_current/HarbourAreaAdministrative",
  "boundary_source": "snapshot S-101 feature, not independently verified legal full-port boundary",
  "selection_policy": "single exact-name polygon, most detailed min_scale, full 2km extent inside snapshot bbox, largest area then smallest feature ID",
  "coverage_bbox": [
    128.9,
    34.9,
    129.3,
    35.3
  ],
  "coverage_boundary_margin_m": 4561.66668103,
  "selection_status": "FIXED_RESEARCH_REFERENCE_UNDER_USER_SINGLE_POLYGON_POLICY"
}
```

### AnchorageArea: 3개 snapshot 기록
- 원천 snapshot SHA256: `1300232a3f03d17ea822eeff55fde99c5458b836f86d26bfd445b9afe8bb7f85`
- 전체 ID: `1183711, 701233, 937412`
| 객체 ID | 기준 polygon 최소 거리(m) | dataset / version |
|---|---:|---|
| 1183711 | 1727.14801424 | 101KR00659C81.000 / 610 |
| 701233 | 1727.14801424 | 101KR004G3B30.000 / 164 |
| 937412 | 1727.14801424 | 101KR005G3B33.000 / 292 |
- 거리 최소/최대: 1727.14801424 / 1727.14801424 m.

### RestrictedArea: 21개 snapshot 기록
- 원천 snapshot SHA256: `1300232a3f03d17ea822eeff55fde99c5458b836f86d26bfd445b9afe8bb7f85`
- 전체 ID: `1147946, 1147971, 1184476, 1187997, 560530, 598356, 598377, 599612, 602472, 602618, 696657, 697312, 697320, 697371, 697374, 701758, 712477, 713031, 924030, 924204, 938200`
| 객체 ID | 기준 polygon 최소 거리(m) | dataset / version |
|---|---:|---|
| 1147946 | 186.27078269 | 101KR00658D90.000 / 557 |
| 1147971 | 631.27927436 | 101KR00658D90.000 / 557 |
| 1184476 | 369.50223214 | 101KR00659C81.000 / 610 |
| 1187997 | 210.27604778 | 101KR00659C91.000 / 614 |
| 560530 | 0 | 101KR002G3000.000 / 30 |
| 598356 | 646.04710292 | 101KR003G3A00.000 / 86 |
| 598377 | 0 | 101KR003G3A00.000 / 86 |
| 599612 | 0 | 101KR003G3B00.000 / 87 |
| 602472 | 909.5024182 | 101KR003G3E00.000 / 89 |
| 602618 | 1955.27191547 | 101KR003G3F00.000 / 90 |
| 696657 | 85.03087396 | 101KR004G3A40.000 / 161 |
| 697312 | 186.41500674 | 101KR004G3A40.000 / 161 |
| 697320 | 0 | 101KR004G3A40.000 / 161 |
| 697371 | 631.38954917 | 101KR004G3A40.000 / 161 |
| 697374 | 631.38954917 | 101KR004G3A40.000 / 161 |
| 701758 | 0 | 101KR004G3B30.000 / 164 |
| 712477 | 909.54690844 | 101KR004G3E20.000 / 169 |
| 713031 | 1955.27191547 | 101KR004G3F10.000 / 172 |
| 924030 | 631.2351645 | 101KR005G3A44.000 / 286 |
| 924204 | 186.37063012 | 101KR005G3A44.000 / 286 |
| 938200 | 210.26179189 | 101KR005G3B33.000 / 292 |
- 거리 최소/최대: 0 / 1955.27191547 m.

- predicate: `ST_DWithin(target::geography,reference::geography,2000,true)` / 거리 정책: `minimum polygon-area to target geometry distance; overlapping/inside=0`
### 파일·locator 검증 기록
```json
{
  "contract_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\answer_contracts.jsonl",
  "jsonl_line": 14,
  "contract_record_sha256": "96a2767035cae2bdc2c9a1c5530194d676d236e9db86ed30b93434d4280adba2",
  "FC_source": {
    "path": "D:/An_GeoLLM/outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
    "sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
    "expected_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
    "status": "HASH_VERIFIED"
  },
  "locator_checks": [
    {
      "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    },
    {
      "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='RestrictedArea']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    }
  ],
  "spatial_oracle_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\oracle_checks.json",
  "source_checks_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\source_checks.json",
  "Q4_original_csv": null,
  "Q4_calculation": null
}
```

## PILOT_Q5_03 — Find wrecks within 5 km of Dokdo and explain their S-101 attributes.

- GOLD 계약: [answer_contracts.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl>) JSONL 15행
- 정규화 JSON record SHA256: `b2d84688b2c082c4a9b99da6b58ddff4c2d15cac21b98d9a09a41add31d6b242` (UTF-8, sort_keys, compact separators)
- AAA 연결 의견: 승인. schema allowed attribute와 instance value를 분리하고 공간 block을 유지하는 기준이 타당하다.
- BBB 검토 쟁점: FC 정의만으로 실제 Wreck 객체 속성값을 만들어서는 안 된다. 추후 in-scope 객체 과제는 object value↔FC definition 연결을 따로 평가해야 한다.

### FC Wreck
- 원문: The ruined remains of a stranded or sunken vessel which has been rendered useless.
- geometry: ['point', 'surface']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]`


### 범위 밖 정답 행동
```json
{
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
```

- predicate: `None` / 거리 정책: `None`
### 파일·locator 검증 기록
```json
{
  "contract_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\answer_contracts.jsonl",
  "jsonl_line": 15,
  "contract_record_sha256": "b2d84688b2c082c4a9b99da6b58ddff4c2d15cac21b98d9a09a41add31d6b242",
  "FC_source": {
    "path": "D:/An_GeoLLM/outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
    "sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
    "expected_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
    "status": "HASH_VERIFIED"
  },
  "locator_checks": [
    {
      "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    }
  ],
  "spatial_oracle_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\oracle_checks.json",
  "source_checks_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\source_checks.json",
  "Q4_original_csv": null,
  "Q4_calculation": null
}
```

## PILOT_Q6_01 — S-101 Wreck 정의의 원문과 Feature Catalogue 출처를 알려줘.

- GOLD 계약: [answer_contracts.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl>) JSONL 16행
- 정규화 JSON record SHA256: `0fb641693a52d6303219757898703c7beb5976f1046002dd6a7b094d2875ff2f` (UTF-8, sort_keys, compact separators)
- AAA 연결 의견: 승인. 원문 인용 요구와 source locator가 명확하다.
- BBB 검토 쟁점: 원문 인용 정확성과 의미 설명 정확도를 별도로 판단한다. 검색 문서 존재만으로 최종 답변에 인용됐다고 인정하지 않는다.

### FC Wreck
- 원문: The ruined remains of a stranded or sunken vessel which has been rendered useless.
- geometry: ['point', 'surface']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]`


- predicate: `None` / 거리 정책: `None`
### 파일·locator 검증 기록
```json
{
  "contract_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\answer_contracts.jsonl",
  "jsonl_line": 16,
  "contract_record_sha256": "0fb641693a52d6303219757898703c7beb5976f1046002dd6a7b094d2875ff2f",
  "FC_source": {
    "path": "D:/An_GeoLLM/outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
    "sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
    "expected_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
    "status": "HASH_VERIFIED"
  },
  "locator_checks": [
    {
      "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    }
  ],
  "spatial_oracle_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\oracle_checks.json",
  "source_checks_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\source_checks.json",
  "Q4_original_csv": null,
  "Q4_calculation": null
}
```

## PILOT_Q6_02 — 등대와 부표를 구분하는 S-101 근거를 알려줘.

- GOLD 계약: [answer_contracts.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl>) JSONL 17행
- 정규화 JSON record SHA256: `53a7a1d78ae16fd8cd71f7c070f20e9a0ebb0edb18c2caece06c0c3d4dc72fe5` (UTF-8, sort_keys, compact separators)
- AAA 연결 의견: 조건부 승인. '부표 전체 분류'가 아니라 LateralBuoy 대표 비교라는 범위를 반드시 공개해야 한다.
- BBB 검토 쟁점: LateralBuoy는 부표 전체의 대체가 아닌 한정 대표다. 원질의의 일반 부표 비교를 이 한정 범위로 평가하는 것이 적절한지 사람이 확인해야 한다.

### FC Landmark
- 원문: Any prominent object at a fixed location on land which can be used in determining a location or a direction.
- geometry: ['point', 'curve', 'surface']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Landmark']]`

### FC Building
- 원문: A free-standing self-supporting construction that is roofed, usually walled, and is intended for human occupancy (for example: a place of work or recreation) and/or habitation.
- geometry: ['point', 'surface']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Building']]`

### FC LightAllAround
- 원문: An all around light is a light that is visible over the whole horizon of interest to marine navigation and having no change in the characteristics of the light.
- geometry: ['point']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='LightAllAround']]`

### FC LightSectored
- 원문: A light presenting different appearances (in particular, different colours) over various parts of the horizon of interest to maritime navigation.
- geometry: ['point']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='LightSectored']]`

### FC LateralBuoy
- 원문: A lateral buoy is used to indicate the port or starboard hand side of the route to be followed. They are generally used for well-defined channels and are used in conjunction with a conventional direction of buoyage.
- geometry: ['point']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='LateralBuoy']]`


- predicate: `None` / 거리 정책: `None`
### 파일·locator 검증 기록
```json
{
  "contract_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\answer_contracts.jsonl",
  "jsonl_line": 17,
  "contract_record_sha256": "53a7a1d78ae16fd8cd71f7c070f20e9a0ebb0edb18c2caece06c0c3d4dc72fe5",
  "FC_source": {
    "path": "D:/An_GeoLLM/outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
    "sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
    "expected_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
    "status": "HASH_VERIFIED"
  },
  "locator_checks": [
    {
      "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Landmark']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    },
    {
      "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Building']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    },
    {
      "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='LightAllAround']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    },
    {
      "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='LightSectored']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    },
    {
      "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='LateralBuoy']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    }
  ],
  "spatial_oracle_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\oracle_checks.json",
  "source_checks_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\source_checks.json",
  "Q4_original_csv": null,
  "Q4_calculation": null
}
```

## PILOT_Q6_03 — What source supports the S-101 definition of AnchorageArea?

- GOLD 계약: [answer_contracts.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl>) JSONL 18행
- 정규화 JSON record SHA256: `092121665e482ded0b260387646eae381cf3d31963d346d3057c601c70cbea74` (UTF-8, sort_keys, compact separators)
- AAA 연결 의견: 승인. 질문이 요구한 source와 정의가 직접 연결된다.
- BBB 검토 쟁점: 원천 제목만 제시하거나 모델의 일반 지식을 인용 근거로 대신하지 않는다. 실제 공간 검색은 요구되지 않는다.

### FC AnchorageArea
- 원문: An area in which vessels or seaplanes anchor or may anchor.
- geometry: ['point', 'surface']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]`


- predicate: `None` / 거리 정책: `None`
### 파일·locator 검증 기록
```json
{
  "contract_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\answer_contracts.jsonl",
  "jsonl_line": 18,
  "contract_record_sha256": "092121665e482ded0b260387646eae381cf3d31963d346d3057c601c70cbea74",
  "FC_source": {
    "path": "D:/An_GeoLLM/outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
    "sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
    "expected_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
    "status": "HASH_VERIFIED"
  },
  "locator_checks": [
    {
      "locator": "//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]",
      "matched_nodes": 1,
      "status": "MATCHED"
    }
  ],
  "spatial_oracle_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\oracle_checks.json",
  "source_checks_file": "D:\\An_GeoLLM\\research\\marine_geollm_scie\\benchmark\\gold_v2_immutable_20261101_v1\\source_checks.json",
  "Q4_original_csv": null,
  "Q4_calculation": null
}
```

## 이번 편집 시 재확인한 원본 해시

- [answer_contracts.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl>) — `550f85c18d902e6895e9affe87b896785a9d150162181153c0d9dd423621bad4`
- [canonical_busan_boundary.json](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/canonical_busan_boundary.json>) — `a0f4408850683c987840531e436ff5698af3b9e39bab700098a453727ff5f63b`
- [parent_gold_manifest.json](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/parent_gold_manifest.json>) — `2c1ce116f03de8b6ae315ec282a2dc13acb5a1c3f943355f17e11ee7cdd6d013`
- [queries.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/queries.jsonl>) — `e0a98769f5bc0375272aa976bba4cb97bdf2a2c8a0e3c43c20910881935023e9`
- [comparison_protocol.json](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/comparison_protocol.json>) — `9bfdc4502ac2f841c5039da25b952e2ce5e5e4d19a5b2e31dd5a845d80362af3`
- [oracle_checks.json](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/oracle_checks.json>) — `0b7f30e293b2464cebedc2805b9522f95efca178a05e8c0409d59a0f2338fe7c`
- [oracle_query.sql](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/oracle_query.sql>) — `91df69a4fe25211ead9f3a905c4ec376d08ec188377c2f0353e2dad2c863b9b4`
- [source_checks.json](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/source_checks.json>) — `c21d0e768cef625a64feae95d3371dd37826d6af82f61a40302973581ae46461`
- [manifest.json](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/manifest.json>) — `feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c`
- [manifest.sha256](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/manifest.sha256>) — `27cc24ef45113d1b949a9a43bf07a6ca0ee0db866f50901bb107a664d25ef0ac`
- [questions_and_sources.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261031_independent_gold_v3/questions_and_sources.jsonl>) — `10caebfca7cf46fbda4305f4b13c783d2b7f9e841fb13f09a15a67faafc2fc08`
- [AI_reference_candidates_separate.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261031_independent_gold_v3/AI_reference_candidates_separate.jsonl>) — `2c9fd0e136bf0349174a400261a1e0ca1e8cb6cc92d245511300a8c283be71e4`
- [reviewer_A_blank.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261031_independent_gold_v3/reviewer_A_blank.jsonl>) — `332775fc6ccd842a34451f9af0a140877039d34d76edb165bc4a905e463cd814`
- [검수자A_18문항_독립검수_빈양식_KR.md](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261031_independent_gold_v3/검수자A_18문항_독립검수_빈양식_KR.md>) — `7eded9a6fa654894b55f8e321802f01db002d9608d3e58b8077d2769cf4e015e`
- [reviewer_B_blank.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261031_independent_gold_v3/reviewer_B_blank.jsonl>) — `4ce833100befc05350ae08122d69c156a394db3411a1444cbbd9ee3333e99c45`
- [검수자B_18문항_독립검수_빈양식_KR.md](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261031_independent_gold_v3/검수자B_18문항_독립검수_빈양식_KR.md>) — `e211be747bc18d000c197fc1df4be72c8ffbb69dc8fcf4bbd5c907608da425c0`
- [adjudication_blank.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261031_independent_gold_v3/adjudication_blank.jsonl>) — `82392e6ebfe980c925b64159cfafbc71cbb8ffe4da83b93d3b7136a6bf43f13b`
- [합의검토_18문항_독립검수_빈양식_KR.md](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261031_independent_gold_v3/합의검토_18문항_독립검수_빈양식_KR.md>) — `f99bc07347740c1131ec76e4e89525bff37a3db0683caec52771bd1f79036779`
- [검수안내_KR.md](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261031_independent_gold_v3/검수안내_KR.md>) — `03b825707f02275cb2a1eee8f5727f7b20e7ba7b1fa5589e758e6eb07ea172b1`
- [manifest.json](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261031_independent_gold_v3/manifest.json>) — `3e5e434ced3e7ebaec0588dee2ae939795e8b807e4a3008c9f1577d05076bd2b`
- [101_Feature_Catalogue_2.0.0.xml](<D:/An_GeoLLM/outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml>) — `2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc`
- [spatial_reference.json](<D:/An_GeoLLM/outputs/scie_dokdo_reference_20261030_v2/spatial_reference.json>) — `cf7e407ec904661093a187e15391b42bc668a6e6ef5f75ead3f96c3f495cb9fb`
- [해양수산부_공동활용체계_해양지명_20221231.csv](<D:/An_GeoLLM/Dataset/해양수산부_공동활용체계_해양지명_20221231.csv>) — `bbc3f1c347f6048b0befdf5102959078ffc29c22cdc4412a98586e76cddb0464`
- [snapshot_manifest.json](<D:/An_GeoLLM/outputs/scie_gold_v2_eight_snapshot_20261102_v6/snapshot_manifest.json>) — `ff37cdeb3d3038c915393dbe2da32a2455253e39f5381b58e64873ca6e0629ad`
- [serving__navigation_aid_current.csv](<D:/An_GeoLLM/outputs/scie_gold_v2_eight_snapshot_20261102_v6/serving__navigation_aid_current.csv>) — `f75d5ceb50049e732433d5b36ca6be03e88a0360bc5f8ba67b3fd92e1425cdd7`
- [projection__s101_feature_current.csv](<D:/An_GeoLLM/outputs/scie_gold_v2_eight_snapshot_20261102_v6/projection__s101_feature_current.csv>) — `1300232a3f03d17ea822eeff55fde99c5458b836f86d26bfd445b9afe8bb7f85`