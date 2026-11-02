# 원본 근거와 사례별 대조

해시는 이번 로컬 파일에서 재계산했다. FC locator는 해당 XML 노드의 유일 존재를 확인했다. 공간 결과는 보존된 SQL/GIS Oracle을 인용하며 이번 작업에서 DB 질의나 거리 계산을 다시 수행하지 않았다. 인간의 의미 판단·원천 범위 승인과는 다르다.

## PILOT_Q1_01

등대의 S-101 객체 유형과 정의를 알려줘.

등대를 단일 Lighthouse 코드로 단정하지 않고 구조물 Landmark/Building과 등화 LightAllAround/LightSectored의 조건부 모델을 구분한다.

**사람이 확인할 점:** 네 코드를 모두 한 시설의 필수 구성으로 요구해서는 안 된다. 설명을 위한 대안 목록과 실제 객체 매핑을 구분한다.

### Landmark
- FC 원문: Any prominent object at a fixed location on land which can be used in determining a location or a direction.
- 허용 geometry: ['point', 'curve', 'surface']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Landmark']]`

### Building
- FC 원문: A free-standing self-supporting construction that is roofed, usually walled, and is intended for human occupancy (for example: a place of work or recreation) and/or habitation.
- 허용 geometry: ['point', 'surface']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Building']]`

### LightAllAround
- FC 원문: An all around light is a light that is visible over the whole horizon of interest to marine navigation and having no change in the characteristics of the light.
- 허용 geometry: ['point']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='LightAllAround']]`

### LightSectored
- FC 원문: A light presenting different appearances (in particular, different colours) over various parts of the horizon of interest to maritime navigation.
- 허용 geometry: ['point']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='LightSectored']]`


### 원본 및 locator 확인
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

- 공간 predicate: `None`; 거리 정책: `None`
- 객체 동일성 정책: `None`

## PILOT_Q1_02

S-101에서 정박지는 어떤 객체야?

정박지는 AnchorageArea로 설명하고 FC 정의·point/surface 허용 geometry와 출처를 연결한다.

**사람이 확인할 점:** 일반 정박 행위와 데이터 객체의 존재를 혼동하지 않는다. 정의 질의에는 공간 실행이 필요하지 않다.

### AnchorageArea
- FC 원문: An area in which vessels or seaplanes anchor or may anchor.
- 허용 geometry: ['point', 'surface']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]`


### 원본 및 locator 확인
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

- 공간 predicate: `None`; 거리 정책: `None`
- 객체 동일성 정책: `None`

## PILOT_Q1_03

What is a wreck in S-101?

Wreck의 정의와 point/surface 표현을 FC 근거로 설명한다.

**사람이 확인할 점:** 침선 개념 설명을 실제 침선 위치 검색으로 바꾸지 않는다. 원문과 동등한 의역도 의미 검수 대상이다.

### Wreck
- FC 원문: The ruined remains of a stranded or sunken vessel which has been rendered useless.
- 허용 geometry: ['point', 'surface']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]`


### 원본 및 locator 확인
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

- 공간 predicate: `None`; 거리 정책: `None`
- 객체 동일성 정책: `None`

## PILOT_Q2_01

S-101 등대의 색상 속성과 허용 값을 알려줘.

구조물 colour와 등화 colour를 구분한다. Landmark/Building은 1~13, LightAllAround와 lightSector는 FC에 연결된 1,3,4,5,6,9,10,11을 제시한다.

**사람이 확인할 점:** LightSectored→sectorCharacteristics→lightSector→colour 경로를 확인한다. 전역 colour 코드 목록을 모든 Feature의 허용값으로 복사하지 않는다.

### Landmark
- FC 원문: Any prominent object at a fixed location on land which can be used in determining a location or a direction.
- 허용 geometry: ['point', 'curve', 'surface']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Landmark']]`

### Building
- FC 원문: A free-standing self-supporting construction that is roofed, usually walled, and is intended for human occupancy (for example: a place of work or recreation) and/or habitation.
- 허용 geometry: ['point', 'surface']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Building']]`

### LightAllAround
- FC 원문: An all around light is a light that is visible over the whole horizon of interest to marine navigation and having no change in the characteristics of the light.
- 허용 geometry: ['point']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='LightAllAround']]`

### LightSectored
- FC 원문: A light presenting different appearances (in particular, different colours) over various parts of the horizon of interest to maritime navigation.
- 허용 geometry: ['point']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='LightSectored']]`

| 소유 객체/속성 | 다중성 | Feature 연결 허용값 |
|---|---|---|
| Landmark → colour | 0..* | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 |
| Building → colour | 0..* | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 |
| LightAllAround → colour | 1..* | 1, 3, 4, 5, 6, 9, 10, 11 |
| LightSectored → sectorCharacteristics | 1..* | 코드 목록 없음/복합 또는 수치 속성 |
| sectorCharacteristics → lightSector | 1..* | 코드 목록 없음/복합 또는 수치 속성 |
| lightSector → colour | 1..* | 1, 3, 4, 5, 6, 9, 10, 11 |

### 원본 및 locator 확인
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

- 공간 predicate: `None`; 거리 정책: `None`
- 객체 동일성 정책: `None`

## PILOT_Q2_02

제한구역의 제한 종류는 어떤 코드로 표현해?

RestrictedArea의 restriction과 categoryOfRestrictedArea를 구분하여 Feature별 연결·다중성·허용 코드를 설명한다.

**사람이 확인할 점:** 구역 종류 코드와 실제 제한 행위 코드는 다른 속성이다. 공개 FC 설명을 실제 구역의 법적 허가 또는 비공개 자료 요청으로 해석하지 않는다.

### RestrictedArea
- FC 원문: A specified area on land or water designated by an appropriate authority within which access or navigation is restricted in accordance with certain specified conditions.
- 허용 geometry: ['surface']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='RestrictedArea']]`

| 소유 객체/속성 | 다중성 | Feature 연결 허용값 |
|---|---|---|
| RestrictedArea → categoryOfRestrictedArea | 0..* | 1, 4, 5, 6, 7, 8, 9, 10, 12, 14, 18, 19, 20, 21, 22, 23, 24, 25, 27, 28, 29, 30, 31, 32 |
| RestrictedArea → restriction | 1..* | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 39, 42 |

### 원본 및 locator 확인
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

- 공간 predicate: `None`; 거리 정책: `None`
- 객체 동일성 정책: `None`

## PILOT_Q2_03

Which attributes describe a Wreck in S-101?

Wreck에 실제 연결된 속성 목록·정의·다중성·허용값을 제시한다. waterLevelEffect와 surroundingDepth의 필수 다중성을 확인한다.

**사람이 확인할 점:** FC 속성 정의와 특정 침선의 실제 속성값은 별개다. 전역에 존재하는 속성을 Wreck에 연결된 것으로 추정하지 않는다.

### Wreck
- FC 원문: The ruined remains of a stranded or sunken vessel which has been rendered useless.
- 허용 geometry: ['point', 'surface']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]`

| 소유 객체/속성 | 다중성 | Feature 연결 허용값 |
|---|---|---|
| Wreck → categoryOfWreck | 0..1 | 1, 2, 3, 4, 5 |
| Wreck → expositionOfSounding | 0..1 | 1, 2, 3 |
| Wreck → featureName | 0..* | 코드 목록 없음/복합 또는 수치 속성 |
| Wreck → height | 0..1 | 코드 목록 없음/복합 또는 수치 속성 |
| Wreck → interoperabilityIdentifier | 0..1 | 코드 목록 없음/복합 또는 수치 속성 |
| Wreck → qualityOfVerticalMeasurement | 0..* | 1, 2, 3, 4, 6, 7, 8, 9 |
| Wreck → radarConspicuous | 0..1 | 코드 목록 없음/복합 또는 수치 속성 |
| Wreck → reportedDate | 0..1 | 코드 목록 없음/복합 또는 수치 속성 |
| Wreck → status | 0..* | 7, 13, 18 |
| Wreck → techniqueOfVerticalMeasurement | 0..* | 1, 2, 3, 4, 5, 8, 9, 10, 11, 12, 13, 15, 16, 17, 18 |
| Wreck → valueOfSounding | 0..1 | 코드 목록 없음/복합 또는 수치 속성 |
| Wreck → visualProminence | 0..1 | 1, 2, 3 |
| Wreck → waterLevelEffect | 1..1 | 1, 2, 3, 4, 5 |
| Wreck → scaleMinimum | 0..1 | 코드 목록 없음/복합 또는 수치 속성 |
| Wreck → information | 0..* | 코드 목록 없음/복합 또는 수치 속성 |
| Wreck → pictorialRepresentation | 0..1 | 코드 목록 없음/복합 또는 수치 속성 |
| Wreck → defaultClearanceDepth | 0..1 | 코드 목록 없음/복합 또는 수치 속성 |
| Wreck → surroundingDepth | 1..1 | 코드 목록 없음/복합 또는 수치 속성 |

### 원본 및 locator 확인
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

- 공간 predicate: `None`; 거리 정책: `None`
- 객체 동일성 정책: `None`

## PILOT_Q3_01

독도 부근에서 가장 가까운 등대를 찾아줘.

현재 부산권 snapshot으로 독도 최근접 등대를 확정할 수 없으므로 DATA_OUT_OF_SCOPE/BLOCKED_DATA와 원천 범위 부족을 설명한다. 공간 객체 GOLD는 없다.

**사람이 확인할 점:** 전국 최근접 계산의 정답이나 실세계 0건으로 만들지 않는다. 단순 UNSUPPORTED_OPERATOR 차단은 올바른 coverage 판단 전체를 충족하지 않는다.


### 기대 공간 행동
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

### 원본 및 locator 확인
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

- 공간 predicate: `None`; 거리 정책: `None`
- 객체 동일성 정책: `None`

## PILOT_Q3_02

부산항 영역 안의 정박지를 찾아줘.

고정 부산항 polygon과 ST_Covers(reference,target)를 사용한 snapshot 내 AnchorageArea 정답은 빈 집합이다. 원천·범위와 검사 조건을 함께 공개한다.

**사람이 확인할 점:** 유효한 빈 Oracle과 미실행/누락은 다르다. 이 polygon은 연구용 고정 경계이며 법적 항계 전체와 동일하다고 단정하지 않는다.


### 공간 GOLD
```json
{
  "AnchorageArea": {
    "object_ids": [],
    "objects": [],
    "source_snapshot_sha256": "1300232a3f03d17ea822eeff55fde99c5458b836f86d26bfd445b9afe8bb7f85",
    "evidence_per_object_required": true
  }
}
```

### 기준 geometry identity(geometry 본문 제외)
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

### 원본 및 locator 확인
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

- 공간 predicate: `ST_Covers(reference,target)`; 거리 정책: `minimum polygon-area to target geometry distance; overlapping/inside=0`
- 객체 동일성 정책: `snapshot feature_instance_id, not inferred physical facilities`

## PILOT_Q3_03

Find wrecks intersecting the selected area.

선택 영역이 없으므로 NEEDS_USER_INPUT, MISSING_REFERENCE_GEOMETRY를 반환하고 execution_attempted/started/tool_called/sql_executed=false여야 한다.

**사람이 확인할 점:** 임의 viewport나 기준점으로 대체하지 않는다. 안내 문구만으로 미실행을 인정하지 말고 실행 로그를 확인한다.


### 원본 및 locator 확인
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

- 공간 predicate: `None`; 거리 정책: `None`
- 객체 동일성 정책: `None`

## PILOT_Q4_01

독도 주변 반경 5km의 해양지명을 찾아줘.

승인 동도 기준점·2022 CSV·WGS84 지오데식 거리 5000m 이하로 고정한다. 원본 ID 44~54의 11개 지명을 반환하고 출처를 연결한다.

**사람이 확인할 점:** 원천 corpus의 정답이며 독도 주변 실세계 지명의 완전목록이 아니다. S-101 ID와 CSV 원본 ID를 혼용하지 않는다.


### 지명 객체·거리·원본 행
```json
{
  "object_ids": [
    "mof_marine_names_20221231:44",
    "mof_marine_names_20221231:45",
    "mof_marine_names_20221231:46",
    "mof_marine_names_20221231:47",
    "mof_marine_names_20221231:48",
    "mof_marine_names_20221231:49",
    "mof_marine_names_20221231:50",
    "mof_marine_names_20221231:51",
    "mof_marine_names_20221231:52",
    "mof_marine_names_20221231:53",
    "mof_marine_names_20221231:54"
  ],
  "objects": [
    {
      "source_id": "44",
      "object_id": "mof_marine_names_20221231:44",
      "name": "북향초",
      "latitude": 37.24944444444444,
      "longitude": 131.8661111111111,
      "csv_line": 47,
      "distance_vincenty_m": 1009.2297312593255,
      "within_5000m": true,
      "coordinate_parse_trace": {
        "latitude": {
          "selected_field": "field1",
          "raw_fields": [
            "37-14-58N",
            "37˚14´58˝N"
          ],
          "parse_warnings": []
        },
        "longitude": {
          "selected_field": "field1",
          "raw_fields": [
            "131-51-58E",
            "131˚51´58˝E"
          ],
          "parse_warnings": []
        }
      },
      "distance_postgis_m": 1009.22973215,
      "independent_distance_difference_m": 8.90674527909141e-07,
      "membership_agrees": true
    },
    {
      "source_id": "45",
      "object_id": "mof_marine_names_20221231:45",
      "name": "가지초",
      "latitude": 37.24916666666667,
      "longitude": 131.86694444444444,
      "csv_line": 48,
      "distance_vincenty_m": 959.4090075635844,
      "within_5000m": true,
      "coordinate_parse_trace": {
        "latitude": {
          "selected_field": "field1",
          "raw_fields": [
            "37-14-57N",
            "37˚14´57˝N"
          ],
          "parse_warnings": []
        },
        "longitude": {
          "selected_field": "field1",
          "raw_fields": [
            "131-52-1E",
            "131˚52´1˝E"
          ],
          "parse_warnings": []
        }
      },
      "distance_postgis_m": 959.4090081,
      "independent_distance_difference_m": 5.364156550058397e-07,
      "membership_agrees": true
    },
    {
      "source_id": "46",
      "object_id": "mof_marine_names_20221231:46",
      "name": "강치초",
      "latitude": 37.2481,
      "longitude": 131.86625555555554,
      "csv_line": 49,
      "distance_vincenty_m": 863.7750788791387,
      "within_5000m": true,
      "coordinate_parse_trace": {
        "latitude": {
          "selected_field": "field1",
          "raw_fields": [
            "37-14-53.16N",
            "37˚14´53.16˝N"
          ],
          "parse_warnings": []
        },
        "longitude": {
          "selected_field": "field1",
          "raw_fields": [
            "131-51-58.52E",
            "131˚51´58.52˝E"
          ],
          "parse_warnings": []
        }
      },
      "distance_postgis_m": 863.77507984,
      "independent_distance_difference_m": 9.608612572264974e-07,
      "membership_agrees": true
    },
    {
      "source_id": "47",
      "object_id": "mof_marine_names_20221231:47",
      "name": "가제초",
      "latitude": 37.246608333333334,
      "longitude": 131.86343333333332,
      "csv_line": 50,
      "distance_vincenty_m": 844.8637232673918,
      "within_5000m": true,
      "coordinate_parse_trace": {
        "latitude": {
          "selected_field": "field1",
          "raw_fields": [
            "37-14-47.79N",
            "37˚14´47.79˝N"
          ],
          "parse_warnings": []
        },
        "longitude": {
          "selected_field": "field1",
          "raw_fields": [
            "131-51-48.36E",
            "131˚51´48.36˝E"
          ],
          "parse_warnings": []
        }
      },
      "distance_postgis_m": 844.86372327,
      "independent_distance_difference_m": 2.608203431009315e-09,
      "membership_agrees": true
    },
    {
      "source_id": "48",
      "object_id": "mof_marine_names_20221231:48",
      "name": "삼봉초",
      "latitude": 37.24608888888889,
      "longitude": 131.86536944444444,
      "csv_line": 51,
      "distance_vincenty_m": 696.700865804542,
      "within_5000m": true,
      "coordinate_parse_trace": {
        "latitude": {
          "selected_field": "field1",
          "raw_fields": [
            "37-14-45.92N",
            "37˚14´45.92˝N"
          ],
          "parse_warnings": []
        },
        "longitude": {
          "selected_field": "field1",
          "raw_fields": [
            "131-51-55.33E",
            "131˚51´55.33˝E"
          ],
          "parse_warnings": []
        }
      },
      "distance_postgis_m": 696.70086772,
      "independent_distance_difference_m": 1.9154580286340206e-06,
      "membership_agrees": true
    },
    {
      "source_id": "49",
      "object_id": "mof_marine_names_20221231:49",
      "name": "괭이초",
      "latitude": 37.245016666666665,
      "longitude": 131.86721666666668,
      "csv_line": 52,
      "distance_vincenty_m": 514.1801960687372,
      "within_5000m": true,
      "coordinate_parse_trace": {
        "latitude": {
          "selected_field": "field1",
          "raw_fields": [
            "37-14-42.06N",
            "37˚14´42.06˝N"
          ],
          "parse_warnings": []
        },
        "longitude": {
          "selected_field": "field1",
          "raw_fields": [
            "131-52-1.98E",
            "131˚52´1.98˝E"
          ],
          "parse_warnings": []
        }
      },
      "distance_postgis_m": 514.18019688,
      "independent_distance_difference_m": 8.112627938317019e-07,
      "membership_agrees": true
    },
    {
      "source_id": "50",
      "object_id": "mof_marine_names_20221231:50",
      "name": "서도초",
      "latitude": 37.244075,
      "longitude": 131.85758888888887,
      "csv_line": 53,
      "distance_vincenty_m": 1123.070571692745,
      "within_5000m": true,
      "coordinate_parse_trace": {
        "latitude": {
          "selected_field": "field1",
          "raw_fields": [
            "37-14-38.67N",
            "37˚14´38.67˝N"
          ],
          "parse_warnings": []
        },
        "longitude": {
          "selected_field": "field1",
          "raw_fields": [
            "131-51-27.32E",
            "131˚51´27.32˝E"
          ],
          "parse_warnings": []
        }
      },
      "distance_postgis_m": 1123.07057171,
      "independent_distance_difference_m": 1.7254933482035995e-08,
      "membership_agrees": true
    },
    {
      "source_id": "51",
      "object_id": "mof_marine_names_20221231:51",
      "name": "군함초",
      "latitude": 37.24373611111111,
      "longitude": 131.86083888888888,
      "csv_line": 54,
      "distance_vincenty_m": 840.2194861787266,
      "within_5000m": true,
      "coordinate_parse_trace": {
        "latitude": {
          "selected_field": "field1",
          "raw_fields": [
            "37-14-37.45N",
            "37˚14´37.45˝N"
          ],
          "parse_warnings": []
        },
        "longitude": {
          "selected_field": "field1",
          "raw_fields": [
            "131-51-39.02E",
            "131˚51´39.02˝E"
          ],
          "parse_warnings": []
        }
      },
      "distance_postgis_m": 840.21948619,
      "independent_distance_difference_m": 1.1273414202150889e-08,
      "membership_agrees": true
    },
    {
      "source_id": "52",
      "object_id": "mof_marine_names_20221231:52",
      "name": "넙덕초",
      "latitude": 37.24256388888889,
      "longitude": 131.8607,
      "csv_line": 55,
      "distance_vincenty_m": 810.3645265974295,
      "within_5000m": true,
      "coordinate_parse_trace": {
        "latitude": {
          "selected_field": "field1",
          "raw_fields": [
            "37-14-33.23N",
            "37˚14´33.23˝N"
          ],
          "parse_warnings": []
        },
        "longitude": {
          "selected_field": "field1",
          "raw_fields": [
            "131-51-38.52E",
            "131˚51´38.52˝E"
          ],
          "parse_warnings": []
        }
      },
      "distance_postgis_m": 810.36452661,
      "independent_distance_difference_m": 1.2570467333716806e-08,
      "membership_agrees": true
    },
    {
      "source_id": "53",
      "object_id": "mof_marine_names_20221231:53",
      "name": "부채초",
      "latitude": 37.23802777777778,
      "longitude": 131.86732222222224,
      "csv_line": 56,
      "distance_vincenty_m": 363.89287903283474,
      "within_5000m": true,
      "coordinate_parse_trace": {
        "latitude": {
          "selected_field": "field1",
          "raw_fields": [
            "37-14-16.9N",
            "37˚14´16.9˝N"
          ],
          "parse_warnings": []
        },
        "longitude": {
          "selected_field": "field1",
          "raw_fields": [
            "131-52-2.36E",
            "131˚52´2.36˝E"
          ],
          "parse_warnings": []
        }
      },
      "distance_postgis_m": 363.89288007,
      "independent_distance_difference_m": 1.0371652479079785e-06,
      "membership_agrees": true
    },
    {
      "source_id": "54",
      "object_id": "mof_marine_names_20221231:54",
      "name": "동도초",
      "latitude": 37.23871388888889,
      "longitude": 131.87139722222224,
      "csv_line": 57,
      "distance_vincenty_m": 281.3718980308276,
      "within_5000m": true,
      "coordinate_parse_trace": {
        "latitude": {
          "selected_field": "field1",
          "raw_fields": [
            "37-14-19.37N",
            "37˚14´19.37˝N"
          ],
          "parse_warnings": []
        },
        "longitude": {
          "selected_field": "field1",
          "raw_fields": [
            "131-52-17.03E",
            "131˚52´17.03˝E"
          ],
          "parse_warnings": []
        }
      },
      "distance_postgis_m": 281.37189895,
      "independent_distance_difference_m": 9.191724075208185e-07,
      "membership_agrees": true
    }
  ],
  "dataset_snapshot_sha256": "bbc3f1c347f6048b0befdf5102959078ffc29c22cdc4412a98586e76cddb0464",
  "oracle_sha256": "cf7e407ec904661093a187e15391b42bc668a6e6ef5f75ead3f96c3f495cb9fb",
  "oracle_path": "D:\\An_GeoLLM\\outputs\\scie_dokdo_reference_20261030_v2\\spatial_reference.json",
  "reference_query_sha256": "1b3764ad439df892151c88eb313b9800b732ccc52559cf4d1320e54c7de39a07",
  "all_distances_sha256": "a26e347dd6405046f9ac96987177a0d03eb03a69e12f55d4b977e6e55466570e",
  "reference_geometry_source": {
    "place_id": "mof:dokdo:east-island",
    "label": "독도",
    "aliases": [
      "Dokdo",
      "독도 동도",
      "독도(동도)"
    ],
    "longitude": 131.86955555555556,
    "latitude": 37.24077777777778,
    "source_url": "https://www.mof.go.kr/doc/ko/selectDoc.do?bbsSeq=27&docSeq=20937&menuSeq=929",
    "source_title": "해양수산부 독도의 주소와 위치",
    "source_coordinates": "동도 북위 37도 14분 26.8초, 동경 131도 52분 10.4초",
    "coordinate_role": "published_east_island_reference_point",
    "note": "독도 부근 검색의 동도 기준점이며 독도 전체 경계 또는 항행 안전 기준점이 아니다."
  },
  "reference_crs": "EPSG:4326",
  "distance_policy": "WGS84 ellipsoidal geodesic, inclusive <=5000m",
  "crs_policy": "Experiment interprets the two explicit geographic DMS fields as WGS84; unlabelled projected WKT is not used.",
  "scope": "2022 CSV records with user-fixed east-island anchor. Not all real-world marine places, not S-101 feature IDs.",
  "independent_expert_review": false,
  "calculation_verified": true
}
```

### 원본 및 locator 확인
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

- 공간 predicate: `None`; 거리 정책: `None`
- 객체 동일성 정책: `None`

## PILOT_Q4_02

독도 주변 반경 5000m의 해양지명을 찾아줘.

5000m를 Q4-01의 5km와 같은 조건으로 해석한다. 동일 기준점과 동일 11개 원본 ID 집합이 정답이다.

**사람이 확인할 점:** 단위 변환은 허용되지만 반경·기준점·원천은 변경하지 않는다. 세 표현을 독립 공간 문제로 합산하지 않는다.


### 지명 객체·거리·원본 행
```json
{
  "object_ids": [
    "mof_marine_names_20221231:44",
    "mof_marine_names_20221231:45",
    "mof_marine_names_20221231:46",
    "mof_marine_names_20221231:47",
    "mof_marine_names_20221231:48",
    "mof_marine_names_20221231:49",
    "mof_marine_names_20221231:50",
    "mof_marine_names_20221231:51",
    "mof_marine_names_20221231:52",
    "mof_marine_names_20221231:53",
    "mof_marine_names_20221231:54"
  ],
  "objects": [
    {
      "source_id": "44",
      "object_id": "mof_marine_names_20221231:44",
      "name": "북향초",
      "latitude": 37.24944444444444,
      "longitude": 131.8661111111111,
      "csv_line": 47,
      "distance_vincenty_m": 1009.2297312593255,
      "within_5000m": true,
      "coordinate_parse_trace": {
        "latitude": {
          "selected_field": "field1",
          "raw_fields": [
            "37-14-58N",
            "37˚14´58˝N"
          ],
          "parse_warnings": []
        },
        "longitude": {
          "selected_field": "field1",
          "raw_fields": [
            "131-51-58E",
            "131˚51´58˝E"
          ],
          "parse_warnings": []
        }
      },
      "distance_postgis_m": 1009.22973215,
      "independent_distance_difference_m": 8.90674527909141e-07,
      "membership_agrees": true
    },
    {
      "source_id": "45",
      "object_id": "mof_marine_names_20221231:45",
      "name": "가지초",
      "latitude": 37.24916666666667,
      "longitude": 131.86694444444444,
      "csv_line": 48,
      "distance_vincenty_m": 959.4090075635844,
      "within_5000m": true,
      "coordinate_parse_trace": {
        "latitude": {
          "selected_field": "field1",
          "raw_fields": [
            "37-14-57N",
            "37˚14´57˝N"
          ],
          "parse_warnings": []
        },
        "longitude": {
          "selected_field": "field1",
          "raw_fields": [
            "131-52-1E",
            "131˚52´1˝E"
          ],
          "parse_warnings": []
        }
      },
      "distance_postgis_m": 959.4090081,
      "independent_distance_difference_m": 5.364156550058397e-07,
      "membership_agrees": true
    },
    {
      "source_id": "46",
      "object_id": "mof_marine_names_20221231:46",
      "name": "강치초",
      "latitude": 37.2481,
      "longitude": 131.86625555555554,
      "csv_line": 49,
      "distance_vincenty_m": 863.7750788791387,
      "within_5000m": true,
      "coordinate_parse_trace": {
        "latitude": {
          "selected_field": "field1",
          "raw_fields": [
            "37-14-53.16N",
            "37˚14´53.16˝N"
          ],
          "parse_warnings": []
        },
        "longitude": {
          "selected_field": "field1",
          "raw_fields": [
            "131-51-58.52E",
            "131˚51´58.52˝E"
          ],
          "parse_warnings": []
        }
      },
      "distance_postgis_m": 863.77507984,
      "independent_distance_difference_m": 9.608612572264974e-07,
      "membership_agrees": true
    },
    {
      "source_id": "47",
      "object_id": "mof_marine_names_20221231:47",
      "name": "가제초",
      "latitude": 37.246608333333334,
      "longitude": 131.86343333333332,
      "csv_line": 50,
      "distance_vincenty_m": 844.8637232673918,
      "within_5000m": true,
      "coordinate_parse_trace": {
        "latitude": {
          "selected_field": "field1",
          "raw_fields": [
            "37-14-47.79N",
            "37˚14´47.79˝N"
          ],
          "parse_warnings": []
        },
        "longitude": {
          "selected_field": "field1",
          "raw_fields": [
            "131-51-48.36E",
            "131˚51´48.36˝E"
          ],
          "parse_warnings": []
        }
      },
      "distance_postgis_m": 844.86372327,
      "independent_distance_difference_m": 2.608203431009315e-09,
      "membership_agrees": true
    },
    {
      "source_id": "48",
      "object_id": "mof_marine_names_20221231:48",
      "name": "삼봉초",
      "latitude": 37.24608888888889,
      "longitude": 131.86536944444444,
      "csv_line": 51,
      "distance_vincenty_m": 696.700865804542,
      "within_5000m": true,
      "coordinate_parse_trace": {
        "latitude": {
          "selected_field": "field1",
          "raw_fields": [
            "37-14-45.92N",
            "37˚14´45.92˝N"
          ],
          "parse_warnings": []
        },
        "longitude": {
          "selected_field": "field1",
          "raw_fields": [
            "131-51-55.33E",
            "131˚51´55.33˝E"
          ],
          "parse_warnings": []
        }
      },
      "distance_postgis_m": 696.70086772,
      "independent_distance_difference_m": 1.9154580286340206e-06,
      "membership_agrees": true
    },
    {
      "source_id": "49",
      "object_id": "mof_marine_names_20221231:49",
      "name": "괭이초",
      "latitude": 37.245016666666665,
      "longitude": 131.86721666666668,
      "csv_line": 52,
      "distance_vincenty_m": 514.1801960687372,
      "within_5000m": true,
      "coordinate_parse_trace": {
        "latitude": {
          "selected_field": "field1",
          "raw_fields": [
            "37-14-42.06N",
            "37˚14´42.06˝N"
          ],
          "parse_warnings": []
        },
        "longitude": {
          "selected_field": "field1",
          "raw_fields": [
            "131-52-1.98E",
            "131˚52´1.98˝E"
          ],
          "parse_warnings": []
        }
      },
      "distance_postgis_m": 514.18019688,
      "independent_distance_difference_m": 8.112627938317019e-07,
      "membership_agrees": true
    },
    {
      "source_id": "50",
      "object_id": "mof_marine_names_20221231:50",
      "name": "서도초",
      "latitude": 37.244075,
      "longitude": 131.85758888888887,
      "csv_line": 53,
      "distance_vincenty_m": 1123.070571692745,
      "within_5000m": true,
      "coordinate_parse_trace": {
        "latitude": {
          "selected_field": "field1",
          "raw_fields": [
            "37-14-38.67N",
            "37˚14´38.67˝N"
          ],
          "parse_warnings": []
        },
        "longitude": {
          "selected_field": "field1",
          "raw_fields": [
            "131-51-27.32E",
            "131˚51´27.32˝E"
          ],
          "parse_warnings": []
        }
      },
      "distance_postgis_m": 1123.07057171,
      "independent_distance_difference_m": 1.7254933482035995e-08,
      "membership_agrees": true
    },
    {
      "source_id": "51",
      "object_id": "mof_marine_names_20221231:51",
      "name": "군함초",
      "latitude": 37.24373611111111,
      "longitude": 131.86083888888888,
      "csv_line": 54,
      "distance_vincenty_m": 840.2194861787266,
      "within_5000m": true,
      "coordinate_parse_trace": {
        "latitude": {
          "selected_field": "field1",
          "raw_fields": [
            "37-14-37.45N",
            "37˚14´37.45˝N"
          ],
          "parse_warnings": []
        },
        "longitude": {
          "selected_field": "field1",
          "raw_fields": [
            "131-51-39.02E",
            "131˚51´39.02˝E"
          ],
          "parse_warnings": []
        }
      },
      "distance_postgis_m": 840.21948619,
      "independent_distance_difference_m": 1.1273414202150889e-08,
      "membership_agrees": true
    },
    {
      "source_id": "52",
      "object_id": "mof_marine_names_20221231:52",
      "name": "넙덕초",
      "latitude": 37.24256388888889,
      "longitude": 131.8607,
      "csv_line": 55,
      "distance_vincenty_m": 810.3645265974295,
      "within_5000m": true,
      "coordinate_parse_trace": {
        "latitude": {
          "selected_field": "field1",
          "raw_fields": [
            "37-14-33.23N",
            "37˚14´33.23˝N"
          ],
          "parse_warnings": []
        },
        "longitude": {
          "selected_field": "field1",
          "raw_fields": [
            "131-51-38.52E",
            "131˚51´38.52˝E"
          ],
          "parse_warnings": []
        }
      },
      "distance_postgis_m": 810.36452661,
      "independent_distance_difference_m": 1.2570467333716806e-08,
      "membership_agrees": true
    },
    {
      "source_id": "53",
      "object_id": "mof_marine_names_20221231:53",
      "name": "부채초",
      "latitude": 37.23802777777778,
      "longitude": 131.86732222222224,
      "csv_line": 56,
      "distance_vincenty_m": 363.89287903283474,
      "within_5000m": true,
      "coordinate_parse_trace": {
        "latitude": {
          "selected_field": "field1",
          "raw_fields": [
            "37-14-16.9N",
            "37˚14´16.9˝N"
          ],
          "parse_warnings": []
        },
        "longitude": {
          "selected_field": "field1",
          "raw_fields": [
            "131-52-2.36E",
            "131˚52´2.36˝E"
          ],
          "parse_warnings": []
        }
      },
      "distance_postgis_m": 363.89288007,
      "independent_distance_difference_m": 1.0371652479079785e-06,
      "membership_agrees": true
    },
    {
      "source_id": "54",
      "object_id": "mof_marine_names_20221231:54",
      "name": "동도초",
      "latitude": 37.23871388888889,
      "longitude": 131.87139722222224,
      "csv_line": 57,
      "distance_vincenty_m": 281.3718980308276,
      "within_5000m": true,
      "coordinate_parse_trace": {
        "latitude": {
          "selected_field": "field1",
          "raw_fields": [
            "37-14-19.37N",
            "37˚14´19.37˝N"
          ],
          "parse_warnings": []
        },
        "longitude": {
          "selected_field": "field1",
          "raw_fields": [
            "131-52-17.03E",
            "131˚52´17.03˝E"
          ],
          "parse_warnings": []
        }
      },
      "distance_postgis_m": 281.37189895,
      "independent_distance_difference_m": 9.191724075208185e-07,
      "membership_agrees": true
    }
  ],
  "dataset_snapshot_sha256": "bbc3f1c347f6048b0befdf5102959078ffc29c22cdc4412a98586e76cddb0464",
  "oracle_sha256": "cf7e407ec904661093a187e15391b42bc668a6e6ef5f75ead3f96c3f495cb9fb",
  "oracle_path": "D:\\An_GeoLLM\\outputs\\scie_dokdo_reference_20261030_v2\\spatial_reference.json",
  "reference_query_sha256": "1b3764ad439df892151c88eb313b9800b732ccc52559cf4d1320e54c7de39a07",
  "all_distances_sha256": "a26e347dd6405046f9ac96987177a0d03eb03a69e12f55d4b977e6e55466570e",
  "reference_geometry_source": {
    "place_id": "mof:dokdo:east-island",
    "label": "독도",
    "aliases": [
      "Dokdo",
      "독도 동도",
      "독도(동도)"
    ],
    "longitude": 131.86955555555556,
    "latitude": 37.24077777777778,
    "source_url": "https://www.mof.go.kr/doc/ko/selectDoc.do?bbsSeq=27&docSeq=20937&menuSeq=929",
    "source_title": "해양수산부 독도의 주소와 위치",
    "source_coordinates": "동도 북위 37도 14분 26.8초, 동경 131도 52분 10.4초",
    "coordinate_role": "published_east_island_reference_point",
    "note": "독도 부근 검색의 동도 기준점이며 독도 전체 경계 또는 항행 안전 기준점이 아니다."
  },
  "reference_crs": "EPSG:4326",
  "distance_policy": "WGS84 ellipsoidal geodesic, inclusive <=5000m",
  "crs_policy": "Experiment interprets the two explicit geographic DMS fields as WGS84; unlabelled projected WKT is not used.",
  "scope": "2022 CSV records with user-fixed east-island anchor. Not all real-world marine places, not S-101 feature IDs.",
  "independent_expert_review": false,
  "calculation_verified": true
}
```

### 원본 및 locator 확인
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

- 공간 predicate: `None`; 거리 정책: `None`
- 객체 동일성 정책: `None`

## PILOT_Q4_03

Find marine place names within 5 km of Dokdo.

영어 5 km 질의도 Q4-01·02와 같은 기준점·원천·11개 ID를 사용한다.

**사람이 확인할 점:** 언어 차이만으로 공간 의미나 coverage를 바꾸지 않는다. 개발 노출된 동등 표현군이며 독립 holdout이 아니다.


### 지명 객체·거리·원본 행
```json
{
  "object_ids": [
    "mof_marine_names_20221231:44",
    "mof_marine_names_20221231:45",
    "mof_marine_names_20221231:46",
    "mof_marine_names_20221231:47",
    "mof_marine_names_20221231:48",
    "mof_marine_names_20221231:49",
    "mof_marine_names_20221231:50",
    "mof_marine_names_20221231:51",
    "mof_marine_names_20221231:52",
    "mof_marine_names_20221231:53",
    "mof_marine_names_20221231:54"
  ],
  "objects": [
    {
      "source_id": "44",
      "object_id": "mof_marine_names_20221231:44",
      "name": "북향초",
      "latitude": 37.24944444444444,
      "longitude": 131.8661111111111,
      "csv_line": 47,
      "distance_vincenty_m": 1009.2297312593255,
      "within_5000m": true,
      "coordinate_parse_trace": {
        "latitude": {
          "selected_field": "field1",
          "raw_fields": [
            "37-14-58N",
            "37˚14´58˝N"
          ],
          "parse_warnings": []
        },
        "longitude": {
          "selected_field": "field1",
          "raw_fields": [
            "131-51-58E",
            "131˚51´58˝E"
          ],
          "parse_warnings": []
        }
      },
      "distance_postgis_m": 1009.22973215,
      "independent_distance_difference_m": 8.90674527909141e-07,
      "membership_agrees": true
    },
    {
      "source_id": "45",
      "object_id": "mof_marine_names_20221231:45",
      "name": "가지초",
      "latitude": 37.24916666666667,
      "longitude": 131.86694444444444,
      "csv_line": 48,
      "distance_vincenty_m": 959.4090075635844,
      "within_5000m": true,
      "coordinate_parse_trace": {
        "latitude": {
          "selected_field": "field1",
          "raw_fields": [
            "37-14-57N",
            "37˚14´57˝N"
          ],
          "parse_warnings": []
        },
        "longitude": {
          "selected_field": "field1",
          "raw_fields": [
            "131-52-1E",
            "131˚52´1˝E"
          ],
          "parse_warnings": []
        }
      },
      "distance_postgis_m": 959.4090081,
      "independent_distance_difference_m": 5.364156550058397e-07,
      "membership_agrees": true
    },
    {
      "source_id": "46",
      "object_id": "mof_marine_names_20221231:46",
      "name": "강치초",
      "latitude": 37.2481,
      "longitude": 131.86625555555554,
      "csv_line": 49,
      "distance_vincenty_m": 863.7750788791387,
      "within_5000m": true,
      "coordinate_parse_trace": {
        "latitude": {
          "selected_field": "field1",
          "raw_fields": [
            "37-14-53.16N",
            "37˚14´53.16˝N"
          ],
          "parse_warnings": []
        },
        "longitude": {
          "selected_field": "field1",
          "raw_fields": [
            "131-51-58.52E",
            "131˚51´58.52˝E"
          ],
          "parse_warnings": []
        }
      },
      "distance_postgis_m": 863.77507984,
      "independent_distance_difference_m": 9.608612572264974e-07,
      "membership_agrees": true
    },
    {
      "source_id": "47",
      "object_id": "mof_marine_names_20221231:47",
      "name": "가제초",
      "latitude": 37.246608333333334,
      "longitude": 131.86343333333332,
      "csv_line": 50,
      "distance_vincenty_m": 844.8637232673918,
      "within_5000m": true,
      "coordinate_parse_trace": {
        "latitude": {
          "selected_field": "field1",
          "raw_fields": [
            "37-14-47.79N",
            "37˚14´47.79˝N"
          ],
          "parse_warnings": []
        },
        "longitude": {
          "selected_field": "field1",
          "raw_fields": [
            "131-51-48.36E",
            "131˚51´48.36˝E"
          ],
          "parse_warnings": []
        }
      },
      "distance_postgis_m": 844.86372327,
      "independent_distance_difference_m": 2.608203431009315e-09,
      "membership_agrees": true
    },
    {
      "source_id": "48",
      "object_id": "mof_marine_names_20221231:48",
      "name": "삼봉초",
      "latitude": 37.24608888888889,
      "longitude": 131.86536944444444,
      "csv_line": 51,
      "distance_vincenty_m": 696.700865804542,
      "within_5000m": true,
      "coordinate_parse_trace": {
        "latitude": {
          "selected_field": "field1",
          "raw_fields": [
            "37-14-45.92N",
            "37˚14´45.92˝N"
          ],
          "parse_warnings": []
        },
        "longitude": {
          "selected_field": "field1",
          "raw_fields": [
            "131-51-55.33E",
            "131˚51´55.33˝E"
          ],
          "parse_warnings": []
        }
      },
      "distance_postgis_m": 696.70086772,
      "independent_distance_difference_m": 1.9154580286340206e-06,
      "membership_agrees": true
    },
    {
      "source_id": "49",
      "object_id": "mof_marine_names_20221231:49",
      "name": "괭이초",
      "latitude": 37.245016666666665,
      "longitude": 131.86721666666668,
      "csv_line": 52,
      "distance_vincenty_m": 514.1801960687372,
      "within_5000m": true,
      "coordinate_parse_trace": {
        "latitude": {
          "selected_field": "field1",
          "raw_fields": [
            "37-14-42.06N",
            "37˚14´42.06˝N"
          ],
          "parse_warnings": []
        },
        "longitude": {
          "selected_field": "field1",
          "raw_fields": [
            "131-52-1.98E",
            "131˚52´1.98˝E"
          ],
          "parse_warnings": []
        }
      },
      "distance_postgis_m": 514.18019688,
      "independent_distance_difference_m": 8.112627938317019e-07,
      "membership_agrees": true
    },
    {
      "source_id": "50",
      "object_id": "mof_marine_names_20221231:50",
      "name": "서도초",
      "latitude": 37.244075,
      "longitude": 131.85758888888887,
      "csv_line": 53,
      "distance_vincenty_m": 1123.070571692745,
      "within_5000m": true,
      "coordinate_parse_trace": {
        "latitude": {
          "selected_field": "field1",
          "raw_fields": [
            "37-14-38.67N",
            "37˚14´38.67˝N"
          ],
          "parse_warnings": []
        },
        "longitude": {
          "selected_field": "field1",
          "raw_fields": [
            "131-51-27.32E",
            "131˚51´27.32˝E"
          ],
          "parse_warnings": []
        }
      },
      "distance_postgis_m": 1123.07057171,
      "independent_distance_difference_m": 1.7254933482035995e-08,
      "membership_agrees": true
    },
    {
      "source_id": "51",
      "object_id": "mof_marine_names_20221231:51",
      "name": "군함초",
      "latitude": 37.24373611111111,
      "longitude": 131.86083888888888,
      "csv_line": 54,
      "distance_vincenty_m": 840.2194861787266,
      "within_5000m": true,
      "coordinate_parse_trace": {
        "latitude": {
          "selected_field": "field1",
          "raw_fields": [
            "37-14-37.45N",
            "37˚14´37.45˝N"
          ],
          "parse_warnings": []
        },
        "longitude": {
          "selected_field": "field1",
          "raw_fields": [
            "131-51-39.02E",
            "131˚51´39.02˝E"
          ],
          "parse_warnings": []
        }
      },
      "distance_postgis_m": 840.21948619,
      "independent_distance_difference_m": 1.1273414202150889e-08,
      "membership_agrees": true
    },
    {
      "source_id": "52",
      "object_id": "mof_marine_names_20221231:52",
      "name": "넙덕초",
      "latitude": 37.24256388888889,
      "longitude": 131.8607,
      "csv_line": 55,
      "distance_vincenty_m": 810.3645265974295,
      "within_5000m": true,
      "coordinate_parse_trace": {
        "latitude": {
          "selected_field": "field1",
          "raw_fields": [
            "37-14-33.23N",
            "37˚14´33.23˝N"
          ],
          "parse_warnings": []
        },
        "longitude": {
          "selected_field": "field1",
          "raw_fields": [
            "131-51-38.52E",
            "131˚51´38.52˝E"
          ],
          "parse_warnings": []
        }
      },
      "distance_postgis_m": 810.36452661,
      "independent_distance_difference_m": 1.2570467333716806e-08,
      "membership_agrees": true
    },
    {
      "source_id": "53",
      "object_id": "mof_marine_names_20221231:53",
      "name": "부채초",
      "latitude": 37.23802777777778,
      "longitude": 131.86732222222224,
      "csv_line": 56,
      "distance_vincenty_m": 363.89287903283474,
      "within_5000m": true,
      "coordinate_parse_trace": {
        "latitude": {
          "selected_field": "field1",
          "raw_fields": [
            "37-14-16.9N",
            "37˚14´16.9˝N"
          ],
          "parse_warnings": []
        },
        "longitude": {
          "selected_field": "field1",
          "raw_fields": [
            "131-52-2.36E",
            "131˚52´2.36˝E"
          ],
          "parse_warnings": []
        }
      },
      "distance_postgis_m": 363.89288007,
      "independent_distance_difference_m": 1.0371652479079785e-06,
      "membership_agrees": true
    },
    {
      "source_id": "54",
      "object_id": "mof_marine_names_20221231:54",
      "name": "동도초",
      "latitude": 37.23871388888889,
      "longitude": 131.87139722222224,
      "csv_line": 57,
      "distance_vincenty_m": 281.3718980308276,
      "within_5000m": true,
      "coordinate_parse_trace": {
        "latitude": {
          "selected_field": "field1",
          "raw_fields": [
            "37-14-19.37N",
            "37˚14´19.37˝N"
          ],
          "parse_warnings": []
        },
        "longitude": {
          "selected_field": "field1",
          "raw_fields": [
            "131-52-17.03E",
            "131˚52´17.03˝E"
          ],
          "parse_warnings": []
        }
      },
      "distance_postgis_m": 281.37189895,
      "independent_distance_difference_m": 9.191724075208185e-07,
      "membership_agrees": true
    }
  ],
  "dataset_snapshot_sha256": "bbc3f1c347f6048b0befdf5102959078ffc29c22cdc4412a98586e76cddb0464",
  "oracle_sha256": "cf7e407ec904661093a187e15391b42bc668a6e6ef5f75ead3f96c3f495cb9fb",
  "oracle_path": "D:\\An_GeoLLM\\outputs\\scie_dokdo_reference_20261030_v2\\spatial_reference.json",
  "reference_query_sha256": "1b3764ad439df892151c88eb313b9800b732ccc52559cf4d1320e54c7de39a07",
  "all_distances_sha256": "a26e347dd6405046f9ac96987177a0d03eb03a69e12f55d4b977e6e55466570e",
  "reference_geometry_source": {
    "place_id": "mof:dokdo:east-island",
    "label": "독도",
    "aliases": [
      "Dokdo",
      "독도 동도",
      "독도(동도)"
    ],
    "longitude": 131.86955555555556,
    "latitude": 37.24077777777778,
    "source_url": "https://www.mof.go.kr/doc/ko/selectDoc.do?bbsSeq=27&docSeq=20937&menuSeq=929",
    "source_title": "해양수산부 독도의 주소와 위치",
    "source_coordinates": "동도 북위 37도 14분 26.8초, 동경 131도 52분 10.4초",
    "coordinate_role": "published_east_island_reference_point",
    "note": "독도 부근 검색의 동도 기준점이며 독도 전체 경계 또는 항행 안전 기준점이 아니다."
  },
  "reference_crs": "EPSG:4326",
  "distance_policy": "WGS84 ellipsoidal geodesic, inclusive <=5000m",
  "crs_policy": "Experiment interprets the two explicit geographic DMS fields as WGS84; unlabelled projected WKT is not used.",
  "scope": "2022 CSV records with user-fixed east-island anchor. Not all real-world marine places, not S-101 feature IDs.",
  "independent_expert_review": false,
  "calculation_verified": true
}
```

### 원본 및 locator 확인
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

- 공간 predicate: `None`; 거리 정책: `None`
- 객체 동일성 정책: `None`

## PILOT_Q5_01

독도 주변 5km의 등대와 난파선을 찾아 각각의 근거를 알려줘.

독도 5km의 Lighthouse와 Wreck 두 공간 하위작업 모두 coverage 부족으로 BLOCKED_DATA다. 표준 정의는 별도 부분응답으로만 허용한다.

**사람이 확인할 점:** 한 대상만 처리하고 전체 완료로 선언하거나 두 빈 집합을 실세계 부재로 제시하면 안 된다. 대상별 상태·근거가 필요하다.

### Landmark
- FC 원문: Any prominent object at a fixed location on land which can be used in determining a location or a direction.
- 허용 geometry: ['point', 'curve', 'surface']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Landmark']]`

### Building
- FC 원문: A free-standing self-supporting construction that is roofed, usually walled, and is intended for human occupancy (for example: a place of work or recreation) and/or habitation.
- 허용 geometry: ['point', 'surface']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Building']]`

### LightAllAround
- FC 원문: An all around light is a light that is visible over the whole horizon of interest to marine navigation and having no change in the characteristics of the light.
- 허용 geometry: ['point']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='LightAllAround']]`

### LightSectored
- FC 원문: A light presenting different appearances (in particular, different colours) over various parts of the horizon of interest to maritime navigation.
- 허용 geometry: ['point']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='LightSectored']]`

### Wreck
- FC 원문: The ruined remains of a stranded or sunken vessel which has been rendered useless.
- 허용 geometry: ['point', 'surface']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]`


### 기대 공간 행동
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

### 원본 및 locator 확인
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

- 공간 predicate: `None`; 거리 정책: `None`
- 객체 동일성 정책: `None`

## PILOT_Q5_02

부산항 주변 2km의 정박지와 제한구역을 찾아 비교해줘.

고정 부산항 polygon과 geometry 간 최소 지오데식 거리 2000m 이하인 AnchorageArea/RestrictedArea 객체 집합을 각각 반환하고 수·거리·정의·원천 범위를 비교한다.

**사람이 확인할 점:** 표현상 polygon 경계 거리와 ST_DWithin(polygon,target)의 내부거리 0은 다를 수 있다. 동결 계약의 실제 predicate를 우선 보존하고 사람이 의미를 확인한다. ID는 snapshot 기록이며 중복 시설 제거 결과가 아니다.

### AnchorageArea
- FC 원문: An area in which vessels or seaplanes anchor or may anchor.
- 허용 geometry: ['point', 'surface']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]`

### RestrictedArea
- FC 원문: A specified area on land or water designated by an appropriate authority within which access or navigation is restricted in accordance with certain specified conditions.
- 허용 geometry: ['surface']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='RestrictedArea']]`


### 공간 GOLD
```json
{
  "AnchorageArea": {
    "object_ids": [
      "1183711",
      "701233",
      "937412"
    ],
    "objects": [
      {
        "id": "1183711",
        "feature": "AnchorageArea",
        "attributes": {
          "name": "N-2 대기정박지",
          "text": "1,000 to 3,000 DWT x 7 Vessels",
          "status": "6",
          "language": "eng",
          "nameUsage": "2",
          "featureName": "",
          "information": "",
          "scaleMinimum": "11999"
        },
        "dataset_name": "101KR00659C81.000",
        "dataset_version_id": 610,
        "harbour_distance_m": 1727.14801424
      },
      {
        "id": "701233",
        "feature": "AnchorageArea",
        "attributes": {
          "name": "N-2 대기정박지",
          "text": "1,000 to 3,000 DWT x 7 Vessels",
          "status": "6",
          "language": "eng",
          "nameUsage": "2",
          "featureName": "",
          "information": "",
          "scaleMinimum": "179999"
        },
        "dataset_name": "101KR004G3B30.000",
        "dataset_version_id": 164,
        "harbour_distance_m": 1727.14801424
      },
      {
        "id": "937412",
        "feature": "AnchorageArea",
        "attributes": {
          "name": "N-2 대기정박지",
          "text": "1,000 to 3,000 DWT x 7 Vessels",
          "status": "6",
          "language": "eng",
          "nameUsage": "2",
          "featureName": "",
          "information": "",
          "scaleMinimum": "44999"
        },
        "dataset_name": "101KR005G3B33.000",
        "dataset_version_id": 292,
        "harbour_distance_m": 1727.14801424
      }
    ],
    "source_snapshot_sha256": "1300232a3f03d17ea822eeff55fde99c5458b836f86d26bfd445b9afe8bb7f85",
    "evidence_per_object_required": true
  },
  "RestrictedArea": {
    "object_ids": [
      "1147946",
      "1147971",
      "1184476",
      "1187997",
      "560530",
      "598356",
      "598377",
      "599612",
      "602472",
      "602618",
      "696657",
      "697312",
      "697320",
      "697371",
      "697374",
      "701758",
      "712477",
      "713031",
      "924030",
      "924204",
      "938200"
    ],
    "objects": [
      {
        "id": "1147946",
        "feature": "RestrictedArea",
        "attributes": {
          "text": "이 구역에서는 속력 7knots 이하로 항해하여야 한다",
          "headline": "속력제한구역",
          "language": "kor",
          "speedLimit": "7",
          "speedUnits": "4",
          "information": "",
          "restriction": "27",
          "scaleMinimum": "17999",
          "vesselSpeedLimit": ""
        },
        "dataset_name": "101KR00658D90.000",
        "dataset_version_id": 557,
        "harbour_distance_m": 186.27078269
      },
      {
        "id": "1147971",
        "feature": "RestrictedArea",
        "attributes": {
          "text": "이 구역에서는 속력 10Knots 이하로 항해하여야 한다",
          "headline": "속력제한구역",
          "language": "kor",
          "speedLimit": "10",
          "speedUnits": "4",
          "information": "",
          "restriction": "27",
          "scaleMinimum": "17999",
          "vesselSpeedLimit": ""
        },
        "dataset_name": "101KR00658D90.000",
        "dataset_version_id": 557,
        "harbour_distance_m": 631.27927436
      },
      {
        "id": "1184476",
        "feature": "RestrictedArea",
        "attributes": {
          "text": "이 구역에서는 속력 10Knots 이하로 항해하여야 한다",
          "headline": "속력제한구역",
          "language": "kor",
          "speedLimit": "10",
          "speedUnits": "4",
          "information": "",
          "restriction": "27",
          "scaleMinimum": "17999",
          "vesselSpeedLimit": ""
        },
        "dataset_name": "101KR00659C81.000",
        "dataset_version_id": 610,
        "harbour_distance_m": 369.50223214
      },
      {
        "id": "1187997",
        "feature": "RestrictedArea",
        "attributes": {
          "text": "이 구역에서는 속력 10Knots 이하로 항해하여야 한다",
          "headline": "속력제한구역",
          "language": "kor",
          "speedLimit": "10",
          "speedUnits": "4",
          "information": "",
          "restriction": "27",
          "scaleMinimum": "17999",
          "vesselSpeedLimit": ""
        },
        "dataset_name": "101KR00659C91.000",
        "dataset_version_id": 614,
        "harbour_distance_m": 210.27604778
      },
      {
        "id": "560530",
        "feature": "RestrictedArea",
        "attributes": {
          "headline": "유조선통항금지해역",
          "language": "kor",
          "information": "",
          "restriction": "8",
          "scaleMinimum": "999999",
          "fileReference": "101KR000020K100.TXT"
        },
        "dataset_name": "101KR002G3000.000",
        "dataset_version_id": 30,
        "harbour_distance_m": 0
      },
      {
        "id": "598356",
        "feature": "RestrictedArea",
        "attributes": {
          "headline": "유조선통항금지해역",
          "language": "kor",
          "information": "",
          "restriction": "8",
          "scaleMinimum": "499999",
          "fileReference": "101KR000020K100.TXT"
        },
        "dataset_name": "101KR003G3A00.000",
        "dataset_version_id": 86,
        "harbour_distance_m": 646.04710292
      },
      {
        "id": "598377",
        "feature": "RestrictedArea",
        "attributes": {
          "headline": "유조선통항금지해역",
          "language": "kor",
          "information": "",
          "restriction": "8",
          "scaleMinimum": "499999",
          "fileReference": "101KR000020K100.TXT"
        },
        "dataset_name": "101KR003G3A00.000",
        "dataset_version_id": 86,
        "harbour_distance_m": 0
      },
      {
        "id": "599612",
        "feature": "RestrictedArea",
        "attributes": {
          "headline": "유조선통항금지해역",
          "language": "kor",
          "information": "",
          "restriction": "8",
          "scaleMinimum": "499999",
          "fileReference": "101KR000020K100.TXT"
        },
        "dataset_name": "101KR003G3B00.000",
        "dataset_version_id": 87,
        "harbour_distance_m": 0
      },
      {
        "id": "602472",
        "feature": "RestrictedArea",
        "attributes": {
          "headline": "유조선통항금지해역",
          "language": "kor",
          "information": "",
          "restriction": "8",
          "scaleMinimum": "499999",
          "fileReference": "101KR000020K100.TXT"
        },
        "dataset_name": "101KR003G3E00.000",
        "dataset_version_id": 89,
        "harbour_distance_m": 909.5024182
      },
      {
        "id": "602618",
        "feature": "RestrictedArea",
        "attributes": {
          "headline": "유조선통항금지해역",
          "language": "kor",
          "information": "",
          "restriction": "8",
          "scaleMinimum": "499999",
          "fileReference": "101KR000020K100.TXT"
        },
        "dataset_name": "101KR003G3F00.000",
        "dataset_version_id": 90,
        "harbour_distance_m": 1955.27191547
      },
      {
        "id": "696657",
        "feature": "RestrictedArea",
        "attributes": {
          "text": "유조선통항금지해역",
          "language": "kor",
          "information": "",
          "restriction": "7",
          "scaleMinimum": "119999",
          "fileReference": "101KR000020K100.TXT"
        },
        "dataset_name": "101KR004G3A40.000",
        "dataset_version_id": 161,
        "harbour_distance_m": 85.03087396
      },
      {
        "id": "697312",
        "feature": "RestrictedArea",
        "attributes": {
          "text": "이 구역에서는 속력 7knots 이하로 항해하여야 한다.",
          "headline": "속력제한구역",
          "language": "kor",
          "speedLimit": "7",
          "speedUnits": "4",
          "information": "",
          "restriction": "27",
          "scaleMinimum": "119999",
          "vesselSpeedLimit": ""
        },
        "dataset_name": "101KR004G3A40.000",
        "dataset_version_id": 161,
        "harbour_distance_m": 186.41500674
      },
      {
        "id": "697320",
        "feature": "RestrictedArea",
        "attributes": {
          "text": "유조선통항금지해역",
          "language": "kor",
          "information": "",
          "restriction": "7",
          "scaleMinimum": "119999",
          "fileReference": "101KR000020K100.TXT"
        },
        "dataset_name": "101KR004G3A40.000",
        "dataset_version_id": 161,
        "harbour_distance_m": 0
      },
      {
        "id": "697371",
        "feature": "RestrictedArea",
        "attributes": {
          "text": "유조선통항금지해역",
          "language": "kor",
          "information": "",
          "restriction": "7",
          "scaleMinimum": "119999",
          "fileReference": "101KR000020K100.TXT"
        },
        "dataset_name": "101KR004G3A40.000",
        "dataset_version_id": 161,
        "harbour_distance_m": 631.38954917
      },
      {
        "id": "697374",
        "feature": "RestrictedArea",
        "attributes": {
          "text": "이 구역에서는 속력 10knots 이하로 항해하여야 한다.",
          "headline": "속력제한구역",
          "language": "kor",
          "speedLimit": "10",
          "speedUnits": "4",
          "information": "",
          "restriction": "27",
          "scaleMinimum": "119999",
          "vesselSpeedLimit": ""
        },
        "dataset_name": "101KR004G3A40.000",
        "dataset_version_id": 161,
        "harbour_distance_m": 631.38954917
      },
      {
        "id": "701758",
        "feature": "RestrictedArea",
        "attributes": {
          "headline": "유조선통항금지해역",
          "language": "kor",
          "information": "",
          "restriction": "8",
          "scaleMinimum": "259999",
          "fileReference": "101KR000020K100.TXT"
        },
        "dataset_name": "101KR004G3B30.000",
        "dataset_version_id": 164,
        "harbour_distance_m": 0
      },
      {
        "id": "712477",
        "feature": "RestrictedArea",
        "attributes": {
          "text": "유조선통항금지해역",
          "language": "kor",
          "information": "",
          "restriction": "7",
          "scaleMinimum": "119999",
          "fileReference": "101KR000020K100.TXT"
        },
        "dataset_name": "101KR004G3E20.000",
        "dataset_version_id": 169,
        "harbour_distance_m": 909.54690844
      },
      {
        "id": "713031",
        "feature": "RestrictedArea",
        "attributes": {
          "headline": "유조선통항금지해역",
          "language": "kor",
          "information": "",
          "restriction": "8",
          "scaleMinimum": "259999",
          "fileReference": "101KR000020K100.TXT"
        },
        "dataset_name": "101KR004G3F10.000",
        "dataset_version_id": 172,
        "harbour_distance_m": 1955.27191547
      },
      {
        "id": "924030",
        "feature": "RestrictedArea",
        "attributes": {
          "text": "이 구역에서는 속력 10knots 이하로 항해하여야 함.",
          "headline": "속력제한구역",
          "language": "kor",
          "speedLimit": "10",
          "speedUnits": "4",
          "information": "",
          "restriction": "27",
          "scaleMinimum": "59999",
          "vesselSpeedLimit": ""
        },
        "dataset_name": "101KR005G3A44.000",
        "dataset_version_id": 286,
        "harbour_distance_m": 631.2351645
      },
      {
        "id": "924204",
        "feature": "RestrictedArea",
        "attributes": {
          "text": "이 구역에서는 속력 7knots 이하로 항해하여야 함.",
          "headline": "속력제한구역",
          "language": "kor",
          "speedLimit": "7",
          "speedUnits": "4",
          "information": "",
          "restriction": "27",
          "scaleMinimum": "59999",
          "vesselSpeedLimit": ""
        },
        "dataset_name": "101KR005G3A44.000",
        "dataset_version_id": 286,
        "harbour_distance_m": 186.37063012
      },
      {
        "id": "938200",
        "feature": "RestrictedArea",
        "attributes": {
          "text": "이 구역에서는 속력 10knots 이하로 항해하여야 함.",
          "headline": "속력제한구역",
          "language": "kor",
          "speedLimit": "10",
          "speedUnits": "4",
          "information": "",
          "restriction": "27",
          "scaleMinimum": "59999",
          "vesselSpeedLimit": ""
        },
        "dataset_name": "101KR005G3B33.000",
        "dataset_version_id": 292,
        "harbour_distance_m": 210.26179189
      }
    ],
    "source_snapshot_sha256": "1300232a3f03d17ea822eeff55fde99c5458b836f86d26bfd445b9afe8bb7f85",
    "evidence_per_object_required": true
  }
}
```

### 기준 geometry identity(geometry 본문 제외)
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

### 원본 및 locator 확인
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

- 공간 predicate: `ST_DWithin(target::geography,reference::geography,2000,true)`; 거리 정책: `minimum polygon-area to target geometry distance; overlapping/inside=0`
- 객체 동일성 정책: `snapshot feature_instance_id, not inferred physical facilities`

## PILOT_Q5_03

Find wrecks within 5 km of Dokdo and explain their S-101 attributes.

독도 Wreck 공간 부분은 BLOCKED_DATA, 실제 object attribute value는 확정하지 않는다. FC 속성 설명은 별도 문서 부분응답으로 가능하다.

**사람이 확인할 점:** FC 정의만으로 실제 Wreck 객체 속성값을 만들어서는 안 된다. 추후 in-scope 객체 과제는 object value↔FC definition 연결을 따로 평가해야 한다.

### Wreck
- FC 원문: The ruined remains of a stranded or sunken vessel which has been rendered useless.
- 허용 geometry: ['point', 'surface']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]`


### 기대 공간 행동
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

### 원본 및 locator 확인
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

- 공간 predicate: `None`; 거리 정책: `None`
- 객체 동일성 정책: `None`

## PILOT_Q6_01

S-101 Wreck 정의의 원문과 Feature Catalogue 출처를 알려줘.

Wreck 정의 원문과 FC 2.0.0 판·SHA256·Feature locator를 함께 제시한다.

**사람이 확인할 점:** 원문 인용 정확성과 의미 설명 정확도를 별도로 판단한다. 검색 문서 존재만으로 최종 답변에 인용됐다고 인정하지 않는다.

### Wreck
- FC 원문: The ruined remains of a stranded or sunken vessel which has been rendered useless.
- 허용 geometry: ['point', 'surface']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]`


### 원본 및 locator 확인
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

- 공간 predicate: `None`; 거리 정책: `None`
- 객체 동일성 정책: `None`

## PILOT_Q6_02

등대와 부표를 구분하는 S-101 근거를 알려줘.

조건부 구조물/등화 모델과 대표 부유표지 LateralBuoy를 FC 정의로 비교한다.

**사람이 확인할 점:** LateralBuoy는 부표 전체의 대체가 아닌 한정 대표다. 원질의의 일반 부표 비교를 이 한정 범위로 평가하는 것이 적절한지 사람이 확인해야 한다.

### Landmark
- FC 원문: Any prominent object at a fixed location on land which can be used in determining a location or a direction.
- 허용 geometry: ['point', 'curve', 'surface']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Landmark']]`

### Building
- FC 원문: A free-standing self-supporting construction that is roofed, usually walled, and is intended for human occupancy (for example: a place of work or recreation) and/or habitation.
- 허용 geometry: ['point', 'surface']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Building']]`

### LightAllAround
- FC 원문: An all around light is a light that is visible over the whole horizon of interest to marine navigation and having no change in the characteristics of the light.
- 허용 geometry: ['point']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='LightAllAround']]`

### LightSectored
- FC 원문: A light presenting different appearances (in particular, different colours) over various parts of the horizon of interest to maritime navigation.
- 허용 geometry: ['point']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='LightSectored']]`

### LateralBuoy
- FC 원문: A lateral buoy is used to indicate the port or starboard hand side of the route to be followed. They are generally used for well-defined channels and are used in conjunction with a conventional direction of buoyage.
- 허용 geometry: ['point']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='LateralBuoy']]`


### 원본 및 locator 확인
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

- 공간 predicate: `None`; 거리 정책: `None`
- 객체 동일성 정책: `None`

## PILOT_Q6_03

What source supports the S-101 definition of AnchorageArea?

AnchorageArea 정의를 뒷받침하는 FC 2.0.0 원문·판·hash·locator를 연결한다.

**사람이 확인할 점:** 원천 제목만 제시하거나 모델의 일반 지식을 인용 근거로 대신하지 않는다. 실제 공간 검색은 요구되지 않는다.

### AnchorageArea
- FC 원문: An area in which vessels or seaplanes anchor or may anchor.
- 허용 geometry: ['point', 'surface']
- locator: `//*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]`


### 원본 및 locator 확인
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

- 공간 predicate: `None`; 거리 정책: `None`
- 객체 동일성 정책: `None`

## 파일 무결성 목록

- [answer_contracts.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/answer_contracts.jsonl>) — `PRESENT_HASH_RECORDED` — SHA256 `550f85c18d902e6895e9affe87b896785a9d150162181153c0d9dd423621bad4`
- [canonical_busan_boundary.json](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/canonical_busan_boundary.json>) — `PRESENT_HASH_RECORDED` — SHA256 `a0f4408850683c987840531e436ff5698af3b9e39bab700098a453727ff5f63b`
- [parent_gold_manifest.json](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/parent_gold_manifest.json>) — `PRESENT_HASH_RECORDED` — SHA256 `2c1ce116f03de8b6ae315ec282a2dc13acb5a1c3f943355f17e11ee7cdd6d013`
- [queries.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/queries.jsonl>) — `PRESENT_HASH_RECORDED` — SHA256 `e0a98769f5bc0375272aa976bba4cb97bdf2a2c8a0e3c43c20910881935023e9`
- [comparison_protocol.json](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/comparison_protocol.json>) — `PRESENT_HASH_RECORDED` — SHA256 `9bfdc4502ac2f841c5039da25b952e2ce5e5e4d19a5b2e31dd5a845d80362af3`
- [oracle_checks.json](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/oracle_checks.json>) — `PRESENT_HASH_RECORDED` — SHA256 `0b7f30e293b2464cebedc2805b9522f95efca178a05e8c0409d59a0f2338fe7c`
- [oracle_query.sql](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/oracle_query.sql>) — `PRESENT_HASH_RECORDED` — SHA256 `91df69a4fe25211ead9f3a905c4ec376d08ec188377c2f0353e2dad2c863b9b4`
- [source_checks.json](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/source_checks.json>) — `PRESENT_HASH_RECORDED` — SHA256 `c21d0e768cef625a64feae95d3371dd37826d6af82f61a40302973581ae46461`
- [manifest.json](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/manifest.json>) — `PRESENT_HASH_RECORDED` — SHA256 `feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c`
- [manifest.sha256](<D:/An_GeoLLM/research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/manifest.sha256>) — `PRESENT_HASH_RECORDED` — SHA256 `27cc24ef45113d1b949a9a43bf07a6ca0ee0db866f50901bb107a664d25ef0ac`
- [questions_and_sources.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261031_independent_gold_v3/questions_and_sources.jsonl>) — `PRESENT_HASH_RECORDED` — SHA256 `10caebfca7cf46fbda4305f4b13c783d2b7f9e841fb13f09a15a67faafc2fc08`
- [AI_reference_candidates_separate.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261031_independent_gold_v3/AI_reference_candidates_separate.jsonl>) — `PRESENT_HASH_RECORDED` — SHA256 `2c9fd0e136bf0349174a400261a1e0ca1e8cb6cc92d245511300a8c283be71e4`
- [reviewer_A_blank.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261031_independent_gold_v3/reviewer_A_blank.jsonl>) — `PRESENT_HASH_RECORDED` — SHA256 `332775fc6ccd842a34451f9af0a140877039d34d76edb165bc4a905e463cd814`
- [검수자A_18문항_독립검수_빈양식_KR.md](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261031_independent_gold_v3/검수자A_18문항_독립검수_빈양식_KR.md>) — `PRESENT_HASH_RECORDED` — SHA256 `7eded9a6fa654894b55f8e321802f01db002d9608d3e58b8077d2769cf4e015e`
- [reviewer_B_blank.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261031_independent_gold_v3/reviewer_B_blank.jsonl>) — `PRESENT_HASH_RECORDED` — SHA256 `4ce833100befc05350ae08122d69c156a394db3411a1444cbbd9ee3333e99c45`
- [검수자B_18문항_독립검수_빈양식_KR.md](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261031_independent_gold_v3/검수자B_18문항_독립검수_빈양식_KR.md>) — `PRESENT_HASH_RECORDED` — SHA256 `e211be747bc18d000c197fc1df4be72c8ffbb69dc8fcf4bbd5c907608da425c0`
- [adjudication_blank.jsonl](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261031_independent_gold_v3/adjudication_blank.jsonl>) — `PRESENT_HASH_RECORDED` — SHA256 `82392e6ebfe980c925b64159cfafbc71cbb8ffe4da83b93d3b7136a6bf43f13b`
- [합의검토_18문항_독립검수_빈양식_KR.md](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261031_independent_gold_v3/합의검토_18문항_독립검수_빈양식_KR.md>) — `PRESENT_HASH_RECORDED` — SHA256 `f99bc07347740c1131ec76e4e89525bff37a3db0683caec52771bd1f79036779`
- [검수안내_KR.md](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261031_independent_gold_v3/검수안내_KR.md>) — `PRESENT_HASH_RECORDED` — SHA256 `03b825707f02275cb2a1eee8f5727f7b20e7ba7b1fa5589e758e6eb07ea172b1`
- [manifest.json](<D:/An_GeoLLM/research/marine_geollm_scie/review/20261031_independent_gold_v3/manifest.json>) — `PRESENT_HASH_RECORDED` — SHA256 `3e5e434ced3e7ebaec0588dee2ae939795e8b807e4a3008c9f1577d05076bd2b`
- [101_Feature_Catalogue_2.0.0.xml](<D:/An_GeoLLM/outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml>) — `HASH_VERIFIED` — SHA256 `2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc`
- [spatial_reference.json](<D:/An_GeoLLM/outputs/scie_dokdo_reference_20261030_v2/spatial_reference.json>) — `HASH_VERIFIED` — SHA256 `cf7e407ec904661093a187e15391b42bc668a6e6ef5f75ead3f96c3f495cb9fb`
- [해양수산부_공동활용체계_해양지명_20221231.csv](<D:/An_GeoLLM/Dataset/해양수산부_공동활용체계_해양지명_20221231.csv>) — `HASH_VERIFIED` — SHA256 `bbc3f1c347f6048b0befdf5102959078ffc29c22cdc4412a98586e76cddb0464`
- [snapshot_manifest.json](<D:/An_GeoLLM/outputs/scie_gold_v2_eight_snapshot_20261102_v6/snapshot_manifest.json>) — `PRESENT_HASH_RECORDED` — SHA256 `ff37cdeb3d3038c915393dbe2da32a2455253e39f5381b58e64873ca6e0629ad`
- [serving__navigation_aid_current.csv](<D:/An_GeoLLM/outputs/scie_gold_v2_eight_snapshot_20261102_v6/serving__navigation_aid_current.csv>) — `HASH_VERIFIED` — SHA256 `f75d5ceb50049e732433d5b36ca6be03e88a0360bc5f8ba67b3fd92e1425cdd7`
- [projection__s101_feature_current.csv](<D:/An_GeoLLM/outputs/scie_gold_v2_eight_snapshot_20261102_v6/projection__s101_feature_current.csv>) — `HASH_VERIFIED` — SHA256 `1300232a3f03d17ea822eeff55fde99c5458b836f86d26bfd445b9afe8bb7f85`