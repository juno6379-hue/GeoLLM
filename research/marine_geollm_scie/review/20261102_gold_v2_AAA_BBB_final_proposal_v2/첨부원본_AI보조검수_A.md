# 독립 검수자 A — 18문항 빈 양식

> **AI 보조 검수 초안** — ChatGPT가 현재 GOLD v2/frozen_v5/Oracle 근거를 바탕으로 작성했습니다. 독립 인간 검수 결과가 아니며 `independent_human_review_complete=true`의 근거로 사용할 수 없습니다.

검수자 이름: ChatGPT AI 초안 A  검수 일시: 2026-11-02  독립 검수 확인: 아니오(AI 보조 초안, 인간 독립검수 대체 불가)
모델 출력과 상대 검수자 판단을 보지 않고 작성하십시오. 초기 판단용 출처에는 AI가 선택한 객체별 locator를 제공하지 않습니다. AI 후보는 초기 판단을 저장한 뒤 별도 대조합니다.

## PILOT_Q1_01 — 등대의 S-101 객체 유형과 정의를 알려줘.

출처 및 고정 입력 조건:
```json
{
  "source_references": {
    "edition": "2.0.0",
    "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
    "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
    "review_scope": "WHOLE_SOURCE_NO_PRESELECTED_FEATURE_LOCATORS"
  },
  "spatial_source_condition": null
}
```

- 필수 작업: 등대를 단일 S-101 Feature로 단정하지 않고 구조물 표현(Landmark/Building)과 등화 표현(LightAllAround/LightSectored)을 구분해 정의와 허용 geometry를 확인한다.
- 허용 답안과 대안: Landmark/Building은 구조물 후보, LightAllAround/LightSectored는 등화 후보로 조건부 설명. 네 Feature가 하나의 실재 등대에 모두 존재한다고 단정하는 답은 불허.
- 반드시 포함할 근거: S-101 Feature Catalogue 2.0.0의 Landmark, Building, LightAllAround, LightSectored 정의 및 geometry binding.
- 공간 정답 또는 미확정 사유: 해당 없음(정의/의미 질의).
- 추가 입력 필요 여부와 이유: 불필요.
- 실제 확인한 출처·위치(locator): 각 FeatureType locator: code='Landmark', 'Building', 'LightAllAround', 'LightSectored'. 소스 hash 2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc.
- AI 후보를 초기 판단 전에 보았는지: 예. 본 문서는 frozen_v5/GOLD v2/Oracle 근거를 이용한 AI 보조 초안이므로 인간 독립검수 조건을 충족하지 않음.
- 판단 및 근거: 조건부 승인. '등대=Lighthouse 단일 Feature'가 아니라 구조물/등화의 조건부 조합으로 설명하는 현재 기준이 FC 구조와 부합한다.
- 검수자·검수 일시·승인 여부: ChatGPT AI 초안 / 2026-11-02 / 인간 승인 아님 — 실제 검수자가 확인·수정·서명 필요

## PILOT_Q1_02 — S-101에서 정박지는 어떤 객체야?

출처 및 고정 입력 조건:
```json
{
  "source_references": {
    "edition": "2.0.0",
    "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
    "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
    "review_scope": "WHOLE_SOURCE_NO_PRESELECTED_FEATURE_LOCATORS"
  },
  "spatial_source_condition": null
}
```

- 필수 작업: 정박지를 S-101 Feature `AnchorageArea`로 식별하고 정의와 허용 geometry를 확인한다.
- 허용 답안과 대안: AnchorageArea. '선박 또는 수상기가 정박하거나 정박할 수 있는 구역'이라는 출처 동등 번역/의역 허용.
- 반드시 포함할 근거: S-101 FC 2.0.0 AnchorageArea 정의, permitted primitives point/surface.
- 공간 정답 또는 미확정 사유: 해당 없음.
- 추가 입력 필요 여부와 이유: 불필요.
- 실제 확인한 출처·위치(locator): //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]
- AI 후보를 초기 판단 전에 보았는지: 예. 본 문서는 frozen_v5/GOLD v2/Oracle 근거를 이용한 AI 보조 초안이므로 인간 독립검수 조건을 충족하지 않음.
- 판단 및 근거: 승인. 현재 FC 정의와 feature mapping이 직접 일치한다.
- 검수자·검수 일시·승인 여부: ChatGPT AI 초안 / 2026-11-02 / 인간 승인 아님 — 실제 검수자가 확인·수정·서명 필요

## PILOT_Q1_03 — What is a wreck in S-101?

출처 및 고정 입력 조건:
```json
{
  "source_references": {
    "edition": "2.0.0",
    "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
    "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
    "review_scope": "WHOLE_SOURCE_NO_PRESELECTED_FEATURE_LOCATORS"
  },
  "spatial_source_condition": null
}
```

- 필수 작업: S-101의 Wreck Feature 정의와 허용 geometry를 확인한다.
- 허용 답안과 대안: Wreck = 좌초 또는 침몰한 선박의 파손 잔해로 사용 불능이 된 것이라는 출처 동등 번역 허용.
- 반드시 포함할 근거: S-101 FC 2.0.0 Wreck 정의, permitted primitives point/surface.
- 공간 정답 또는 미확정 사유: 해당 없음.
- 추가 입력 필요 여부와 이유: 불필요.
- 실제 확인한 출처·위치(locator): //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]
- AI 후보를 초기 판단 전에 보았는지: 예. 본 문서는 frozen_v5/GOLD v2/Oracle 근거를 이용한 AI 보조 초안이므로 인간 독립검수 조건을 충족하지 않음.
- 판단 및 근거: 승인. FC의 Wreck 정의와 직접 부합한다.
- 검수자·검수 일시·승인 여부: ChatGPT AI 초안 / 2026-11-02 / 인간 승인 아님 — 실제 검수자가 확인·수정·서명 필요

## PILOT_Q2_01 — S-101 등대의 색상 속성과 허용 값을 알려줘.

출처 및 고정 입력 조건:
```json
{
  "source_references": {
    "edition": "2.0.0",
    "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
    "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
    "review_scope": "WHOLE_SOURCE_NO_PRESELECTED_FEATURE_LOCATORS"
  },
  "spatial_source_condition": null
}
```

- 필수 작업: 등대 구조물과 등화의 colour binding을 분리하고 Feature별 허용값을 확인한다. LightSectored는 중첩 complex attribute 경로까지 확인한다.
- 허용 답안과 대안: Landmark/Building colour=1~13. LightAllAround colour=1,3,4,5,6,9,10,11. LightSectored는 sectorCharacteristics→lightSector→colour 경로에서 1,3,4,5,6,9,10,11. 하나의 통합 색상목록으로 단순화하면 불허.
- 반드시 포함할 근거: S-101 FC 2.0.0의 각 Feature binding과 colour simple attribute, LightSectored의 sectorCharacteristics/lightSector complex path.
- 공간 정답 또는 미확정 사유: 해당 없음.
- 추가 입력 필요 여부와 이유: 불필요.
- 실제 확인한 출처·위치(locator): Landmark/Building/LightAllAround FeatureType + colour SimpleAttribute; LightSectored FeatureType → sectorCharacteristics → lightSector → colour.
- AI 후보를 초기 판단 전에 보았는지: 예. 본 문서는 frozen_v5/GOLD v2/Oracle 근거를 이용한 AI 보조 초안이므로 인간 독립검수 조건을 충족하지 않음.
- 판단 및 근거: 승인. 전역 colour 코드와 Feature binding 허용값을 구분하는 현재 기준이 타당하다.
- 검수자·검수 일시·승인 여부: ChatGPT AI 초안 / 2026-11-02 / 인간 승인 아님 — 실제 검수자가 확인·수정·서명 필요

## PILOT_Q2_02 — 제한구역의 제한 종류는 어떤 코드로 표현해?

출처 및 고정 입력 조건:
```json
{
  "source_references": {
    "edition": "2.0.0",
    "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
    "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
    "review_scope": "WHOLE_SOURCE_NO_PRESELECTED_FEATURE_LOCATORS"
  },
  "spatial_source_condition": null
}
```

- 필수 작업: RestrictedArea의 `restriction`과 `categoryOfRestrictedArea`를 별도 속성으로 구분하고 각각의 허용 code set을 확인한다.
- 허용 답안과 대안: 실제 제한 행위는 restriction(허용 1~27의 지정값 및 39,42), 구역의 종류/법적 성격은 categoryOfRestrictedArea(1,4,5,6,7,8,9,10,12,14,18~25,27~32). 두 code list를 서로 치환하지 않는 설명.
- 반드시 포함할 근거: S-101 FC 2.0.0 RestrictedArea Feature binding, restriction 및 categoryOfRestrictedArea 정의/허용값.
- 공간 정답 또는 미확정 사유: 해당 없음.
- 추가 입력 필요 여부와 이유: 불필요.
- 실제 확인한 출처·위치(locator): RestrictedArea FeatureType locator; SimpleAttribute code='restriction' 및 code='categoryOfRestrictedArea' locator.
- AI 후보를 초기 판단 전에 보았는지: 예. 본 문서는 frozen_v5/GOLD v2/Oracle 근거를 이용한 AI 보조 초안이므로 인간 독립검수 조건을 충족하지 않음.
- 판단 및 근거: 승인. 질의의 '제한 종류'는 restriction을 중심으로 답하되 categoryOfRestrictedArea와 혼동하지 않도록 둘을 분리하는 기준이 적절하다.
- 검수자·검수 일시·승인 여부: ChatGPT AI 초안 / 2026-11-02 / 인간 승인 아님 — 실제 검수자가 확인·수정·서명 필요

## PILOT_Q2_03 — Which attributes describe a Wreck in S-101?

출처 및 고정 입력 조건:
```json
{
  "source_references": {
    "edition": "2.0.0",
    "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
    "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
    "review_scope": "WHOLE_SOURCE_NO_PRESELECTED_FEATURE_LOCATORS"
  },
  "spatial_source_condition": null
}
```

- 필수 작업: Wreck에 FC가 직접 binding한 속성을 열거하고 각 다중도/허용값을 구분한다. Feature 속성과 다른 binding 종류를 혼동하지 않는다.
- 허용 답안과 대안: Wreck direct attributes: categoryOfWreck, expositionOfSounding, featureName, height, interoperabilityIdentifier, qualityOfVerticalMeasurement, radarConspicuous, reportedDate, status, techniqueOfVerticalMeasurement, valueOfSounding, visualProminence, waterLevelEffect, scaleMinimum, information, pictorialRepresentation, defaultClearanceDepth, surroundingDepth. 복합속성은 구조를 유지해 설명.
- 반드시 포함할 근거: S-101 FC 2.0.0 Wreck FeatureType 및 각 Simple/ComplexAttribute binding/locator.
- 공간 정답 또는 미확정 사유: 해당 없음.
- 추가 입력 필요 여부와 이유: 불필요.
- 실제 확인한 출처·위치(locator): Wreck FeatureType locator와 각 attribute code locator(총 18개).
- AI 후보를 초기 판단 전에 보았는지: 예. 본 문서는 frozen_v5/GOLD v2/Oracle 근거를 이용한 AI 보조 초안이므로 인간 독립검수 조건을 충족하지 않음.
- 판단 및 근거: 승인. 현재 frozen_v5의 FC direct binding 목록과 일치한다.
- 검수자·검수 일시·승인 여부: ChatGPT AI 초안 / 2026-11-02 / 인간 승인 아님 — 실제 검수자가 확인·수정·서명 필요

## PILOT_Q3_01 — 독도 부근에서 가장 가까운 등대를 찾아줘.

출처 및 고정 입력 조건:
```json
{
  "source_references": null,
  "spatial_source_condition": null
}
```

- 필수 작업: 독도 기준점을 해소하고 '가장 가까운'을 nearest로 유지하며 등대의 시설 단위 의미/중복 정책을 정한 뒤 원천 coverage를 먼저 검증한다.
- 허용 답안과 대안: 현재 snapshot에서는 `DATA_OUT_OF_SCOPE` 또는 `BLOCKED_DATA`. '0건' 또는 부산청 자료에서 계산한 임의 최근접 등대를 실세계 정답으로 제시하는 것은 불허. 향후 in-scope 원천에서는 radius 없이 nearest/top-1 적용.
- 반드시 포함할 근거: 부산지방해양수산청 항로표지 원천이 전국완전성을 보장하지 않으며 독도 coverage가 검증되지 않았다는 source scope; GOLD v2 comparison protocol.
- 공간 정답 또는 미확정 사유: 공간 객체 GOLD 없음. 현재 항로표지 source의 독도 coverage가 검증되지 않아 실세계 최근접 등대를 확정할 수 없음.
- 추가 입력 필요 여부와 이유: 사용자 입력 문제가 아니라 in-scope/권위 있는 등대 원천이 필요함.
- 실제 확인한 출처·위치(locator): Dataset/해양수산부 부산지방해양수산청_항로표지정보_20250623.csv; gold_v2 oracle/source_checks; comparison_protocol PILOT_Q3_01.
- AI 후보를 초기 판단 전에 보았는지: 예. 본 문서는 frozen_v5/GOLD v2/Oracle 근거를 이용한 AI 보조 초안이므로 인간 독립검수 조건을 충족하지 않음.
- 판단 및 근거: 승인. nearest를 1km 기본반경으로 바꾸지 않고 coverage 부족을 안전중단으로 처리하는 기준이 타당하다.
- 검수자·검수 일시·승인 여부: ChatGPT AI 초안 / 2026-11-02 / 인간 승인 아님 — 실제 검수자가 확인·수정·서명 필요

## PILOT_Q3_02 — 부산항 영역 안의 정박지를 찾아줘.

출처 및 고정 입력 조건:
```json
{
  "source_references": null,
  "spatial_source_condition": null
}
```

- 필수 작업: 연구 snapshot에서 고정한 부산항 polygon을 기준기하로 사용하고 '영역 안' predicate를 사전에 고정한 뒤 AnchorageArea 완전 집합을 산출한다.
- 허용 답안과 대안: 현재 연구 기준 객체 1137770(101KR00658D00.000)에 대해 ST_Covers를 적용한 source-bound 결과만 정답으로 사용. 이를 '부산항 전체 실세계 정박지'로 일반화하지 않음.
- 반드시 포함할 근거: canonical_busan_boundary.json, research snapshot object 1137770, CRS EPSG:4326, GOLD v2 oracle의 ST_Covers 검산.
- 공간 정답 또는 미확정 사유: 고정 polygon 1137770에 대한 ST_Covers 기준 결과는 0개. 이는 해당 benchmark polygon 기준 0개일 뿐 부산항 전체에 정박지가 없다는 뜻이 아님.
- 추가 입력 필요 여부와 이유: benchmark에서는 불필요. 실제 프로그램에서는 법적/운영 항계 정책이 별도 필요.
- 실제 확인한 출처·위치(locator): protocol/gold_v2_oracle_and_paired_design_20261101_KR.md; canonical boundary ID 1137770 / dataset 540/540.
- AI 후보를 초기 판단 전에 보았는지: 예. 본 문서는 frozen_v5/GOLD v2/Oracle 근거를 이용한 AI 보조 초안이므로 인간 독립검수 조건을 충족하지 않음.
- 판단 및 근거: 조건부 승인. 연구 재현성에는 충분하지만 법적 부산항 항계라고 표현하면 안 된다.
- 검수자·검수 일시·승인 여부: ChatGPT AI 초안 / 2026-11-02 / 인간 승인 아님 — 실제 검수자가 확인·수정·서명 필요

## PILOT_Q3_03 — Find wrecks intersecting the selected area.

출처 및 고정 입력 조건:
```json
{
  "source_references": null,
  "spatial_source_condition": null
}
```

- 필수 작업: Wreck + intersects 의미를 유지하고 selected AOI의 존재를 확인한다. AOI가 없으면 실행하지 않고 사용자에게 영역을 요청한다.
- 허용 답안과 대안: `NEEDS_USER_INPUT`, blocker=`MISSING_REFERENCE_GEOMETRY`, execution_attempted=false. 임의 viewport/AOI 생성 불허.
- 반드시 포함할 근거: GOLD v2 comparison protocol의 semantic_gold(Wreck/intersects), qec_gold(selected_geometry=REQUIRED), execution_gold(execution_attempted=false).
- 공간 정답 또는 미확정 사유: selected area가 제공되지 않아 object set GOLD를 만들지 않음.
- 추가 입력 필요 여부와 이유: 필요. 사용자가 선택한 AOI geometry.
- 실제 확인한 출처·위치(locator): gold_v2 comparison_protocol.json / PILOT_Q3_03.
- AI 후보를 초기 판단 전에 보았는지: 예. 본 문서는 frozen_v5/GOLD v2/Oracle 근거를 이용한 AI 보조 초안이므로 인간 독립검수 조건을 충족하지 않음.
- 판단 및 근거: 승인. missing input과 공간 0건을 구분하는 기준이 명확하다.
- 검수자·검수 일시·승인 여부: ChatGPT AI 초안 / 2026-11-02 / 인간 승인 아님 — 실제 검수자가 확인·수정·서명 필요

## PILOT_Q4_01 — 독도 주변 반경 5km의 해양지명을 찾아줘.

출처 및 고정 입력 조건:
```json
{
  "source_references": null,
  "spatial_source_condition": {
    "dataset_snapshot_sha256": "bbc3f1c347f6048b0befdf5102959078ffc29c22cdc4412a98586e76cddb0464",
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
    "dataset_source_path": "D:\\An_GeoLLM\\Dataset\\해양수산부_공동활용체계_해양지명_20221231.csv"
  }
}
```

- 필수 작업: 독도 동도 승인 기준점에서 WGS84 지오데식 거리 ≤5000m로 2022 해양지명 CSV를 검색하고 source-bound object set을 반환한다.
- 허용 답안과 대안: 정확한 11개 ID 집합: mof_marine_names_20221231:44~54. 이름: 북향초, 가지초, 강치초, 가제초, 삼봉초, 괭이초, 서도초, 군함초, 넙덕초, 부채초, 동도초. 순서는 본질적이지 않음.
- 반드시 포함할 근거: dataset snapshot SHA256 bbc3f1c347f6048b0befdf5102959078ffc29c22cdc4412a98586e76cddb0464, oracle SHA256 cf7e407ec904661093a187e15391b42bc668a6e6ef5f75ead3f96c3f495cb9fb, 동도 기준점, WGS84 geodesic <=5000m.
- 공간 정답 또는 미확정 사유: 11개 source-bound set 확정. 실세계 전체 해양지명이나 S-101 Feature ID 집합을 의미하지 않음.
- 추가 입력 필요 여부와 이유: 불필요.
- 실제 확인한 출처·위치(locator): frozen_v5 Q4 spatial_reference; outputs/scie_dokdo_reference_20261030_v2/spatial_reference.json.
- AI 후보를 초기 판단 전에 보았는지: 예. 본 문서는 frozen_v5/GOLD v2/Oracle 근거를 이용한 AI 보조 초안이므로 인간 독립검수 조건을 충족하지 않음.
- 판단 및 근거: 승인. PostGIS/Vincenty membership 검산과 source-bound scope가 명시돼 있다.
- 검수자·검수 일시·승인 여부: ChatGPT AI 초안 / 2026-11-02 / 인간 승인 아님 — 실제 검수자가 확인·수정·서명 필요

## PILOT_Q4_02 — 독도 주변 반경 5000m의 해양지명을 찾아줘.

출처 및 고정 입력 조건:
```json
{
  "source_references": null,
  "spatial_source_condition": {
    "dataset_snapshot_sha256": "bbc3f1c347f6048b0befdf5102959078ffc29c22cdc4412a98586e76cddb0464",
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
    "dataset_source_path": "D:\\An_GeoLLM\\Dataset\\해양수산부_공동활용체계_해양지명_20221231.csv"
  }
}
```

- 필수 작업: Q4-01과 동일한 기준점/원천/거리정책을 사용해 5000m 표현이 5km와 동일한 object set을 내는지 확인한다.
- 허용 답안과 대안: Q4-01과 동일한 11개 ID(mof_marine_names_20221231:44~54).
- 반드시 포함할 근거: 동일 dataset snapshot/oracle, distance_m=5000, 동일 동도 anchor.
- 공간 정답 또는 미확정 사유: 11개 source-bound set 확정. Q4-01과 metamorphic equivalent.
- 추가 입력 필요 여부와 이유: 불필요.
- 실제 확인한 출처·위치(locator): frozen_v5 Q4_02 spatial_reference / 동일 oracle SHA256 cf7e407e...
- AI 후보를 초기 판단 전에 보았는지: 예. 본 문서는 frozen_v5/GOLD v2/Oracle 근거를 이용한 AI 보조 초안이므로 인간 독립검수 조건을 충족하지 않음.
- 판단 및 근거: 승인. 5km와 5000m의 단위 등가성 검증 사례로 적절하다.
- 검수자·검수 일시·승인 여부: ChatGPT AI 초안 / 2026-11-02 / 인간 승인 아님 — 실제 검수자가 확인·수정·서명 필요

## PILOT_Q4_03 — Find marine place names within 5 km of Dokdo.

출처 및 고정 입력 조건:
```json
{
  "source_references": null,
  "spatial_source_condition": {
    "dataset_snapshot_sha256": "bbc3f1c347f6048b0befdf5102959078ffc29c22cdc4412a98586e76cddb0464",
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
    "dataset_source_path": "D:\\An_GeoLLM\\Dataset\\해양수산부_공동활용체계_해양지명_20221231.csv"
  }
}
```

- 필수 작업: 영문 질의를 동일 독도 동도 anchor와 5km 지오데식 조건으로 해석해 Q4-01/02와 같은 source-bound 집합을 산출한다.
- 허용 답안과 대안: Q4-01/02와 동일한 11개 ID(mof_marine_names_20221231:44~54).
- 반드시 포함할 근거: 동일 dataset snapshot/oracle, WGS84 geodesic <=5000m, 동일 reference geometry.
- 공간 정답 또는 미확정 사유: 11개 source-bound set 확정. 동일 equivalence group이므로 독립 공간문제 3개로 세지 않음.
- 추가 입력 필요 여부와 이유: 불필요.
- 실제 확인한 출처·위치(locator): frozen_v5 Q4_03 spatial_reference / oracle SHA256 cf7e407e...
- AI 후보를 초기 판단 전에 보았는지: 예. 본 문서는 frozen_v5/GOLD v2/Oracle 근거를 이용한 AI 보조 초안이므로 인간 독립검수 조건을 충족하지 않음.
- 판단 및 근거: 승인. 언어 표현 변화에 대한 동등성 검증으로 적절하다.
- 검수자·검수 일시·승인 여부: ChatGPT AI 초안 / 2026-11-02 / 인간 승인 아님 — 실제 검수자가 확인·수정·서명 필요

## PILOT_Q5_01 — 독도 주변 5km의 등대와 난파선을 찾아 각각의 근거를 알려줘.

출처 및 고정 입력 조건:
```json
{
  "source_references": {
    "edition": "2.0.0",
    "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
    "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
    "review_scope": "WHOLE_SOURCE_NO_PRESELECTED_FEATURE_LOCATORS"
  },
  "spatial_source_condition": null
}
```

- 필수 작업: 독도 기준점과 5km를 해석하고 등대와 Wreck 각각의 coverage를 독립 확인하며 두 공간 하위작업과 근거 의무를 별도 상태로 관리한다.
- 허용 답안과 대안: 현재 snapshot에서는 Lighthouse와 Wreck 공간 하위작업 모두 `BLOCKED_DATA/DATA_OUT_OF_SCOPE`. S-101 정의/근거 설명은 선택적 PARTIAL_RESPONSE 가능. 한쪽만 답하거나 빈 집합을 정답으로 제시하면 full success 아님.
- 반드시 포함할 근거: navigation-aid source의 전국완전성 미검증, S-101 Wreck snapshot의 dokdo_coverage=false, GOLD v2 composite completion policy.
- 공간 정답 또는 미확정 사유: 두 target 모두 spatial object GOLD=null. 자료 범위 밖이므로 실세계 0건으로 채점하지 않음.
- 추가 입력 필요 여부와 이유: 사용자 입력보다 전국/독도 coverage가 검증된 원천이 필요.
- 실제 확인한 출처·위치(locator): gold_v2 comparison_protocol PILOT_Q5_01; oracle_checks/source_checks.
- AI 후보를 초기 판단 전에 보았는지: 예. 본 문서는 frozen_v5/GOLD v2/Oracle 근거를 이용한 AI 보조 초안이므로 인간 독립검수 조건을 충족하지 않음.
- 판단 및 근거: 승인. 복합질의의 partial/full success와 coverage를 분리하는 기준이 타당하다.
- 검수자·검수 일시·승인 여부: ChatGPT AI 초안 / 2026-11-02 / 인간 승인 아님 — 실제 검수자가 확인·수정·서명 필요

## PILOT_Q5_02 — 부산항 주변 2km의 정박지와 제한구역을 찾아 비교해줘.

출처 및 고정 입력 조건:
```json
{
  "source_references": {
    "edition": "2.0.0",
    "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
    "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
    "review_scope": "WHOLE_SOURCE_NO_PRESELECTED_FEATURE_LOCATORS"
  },
  "spatial_source_condition": null
}
```

- 필수 작업: 고정 부산항 polygon 1137770을 기준으로 AnchorageArea와 RestrictedArea를 각각 geometry-to-geometry 최소 지오데식 거리 ≤2000m로 검색하고 두 결과를 비교하며 source scope를 공개한다.
- 허용 답안과 대안: 현재 GOLD v2 oracle 기준 AnchorageArea 3개, RestrictedArea 21개. 비교에는 유형별 count, 최소/최대 거리, FC 정의 근거, source/reference coverage 공개가 포함돼야 함.
- 반드시 포함할 근거: canonical boundary 1137770 / 101KR00658D00.000, EPSG:4326, ST_DWithin 및 ST_Distance≤2000 독립 대조, S-101 FC AnchorageArea/RestrictedArea 정의.
- 공간 정답 또는 미확정 사유: GOLD v2 oracle에서 2km source-bound 집합이 확정됨(정박지 3, 제한구역 21). 단 canonical polygon은 연구 snapshot 기준이며 법적 부산항 전체 경계로 일반화 금지.
- 추가 입력 필요 여부와 이유: benchmark에서는 불필요. 운영에서는 authoritative harbour boundary policy가 별도 필요.
- 실제 확인한 출처·위치(locator): protocol/gold_v2_oracle_and_paired_design_20261101_KR.md; canonical_busan_boundary.json; FC FeatureType AnchorageArea/RestrictedArea.
- AI 후보를 초기 판단 전에 보았는지: 예. 본 문서는 frozen_v5/GOLD v2/Oracle 근거를 이용한 AI 보조 초안이므로 인간 독립검수 조건을 충족하지 않음.
- 판단 및 근거: 조건부 승인. 공간 oracle은 명확하나 검수 양식의 spatial_source_condition=null은 최종 인간 검수 전에 현재 GOLD v2 기준으로 동기화하는 것이 바람직하다.
- 검수자·검수 일시·승인 여부: ChatGPT AI 초안 / 2026-11-02 / 인간 승인 아님 — 실제 검수자가 확인·수정·서명 필요

## PILOT_Q5_03 — Find wrecks within 5 km of Dokdo and explain their S-101 attributes.

출처 및 고정 입력 조건:
```json
{
  "source_references": {
    "edition": "2.0.0",
    "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
    "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
    "review_scope": "WHOLE_SOURCE_NO_PRESELECTED_FEATURE_LOCATORS"
  },
  "spatial_source_condition": null
}
```

- 필수 작업: 독도 기준 5km Wreck 공간검색과 S-101 attribute 설명을 분리하고 coverage를 먼저 검증한다. 실제 object 값과 FC에서 허용되는 attribute를 구분한다.
- 허용 답안과 대안: 공간 부분은 `BLOCKED_DATA/DATA_OUT_OF_SCOPE`. 문서 부분은 Wreck의 FC attribute binding 설명을 PARTIAL_RESPONSE로 제공 가능. 독도 Wreck object value를 생성/추정하면 불허.
- 반드시 포함할 근거: Wreck FC binding(categoryOfWreck 등 18개), S-101 FC 2.0.0 edition/hash/locator, S-101 spatial snapshot dokdo_coverage=false.
- 공간 정답 또는 미확정 사유: spatial object GOLD=null. 부산권 Wreck 172개를 독도 실세계 정답으로 사용할 수 없음.
- 추가 입력 필요 여부와 이유: 독도 coverage가 검증된 Wreck 원천 필요.
- 실제 확인한 출처·위치(locator): gold_v2 comparison_protocol PILOT_Q5_03; Wreck FeatureType 및 18개 attribute locator.
- AI 후보를 초기 판단 전에 보았는지: 예. 본 문서는 frozen_v5/GOLD v2/Oracle 근거를 이용한 AI 보조 초안이므로 인간 독립검수 조건을 충족하지 않음.
- 판단 및 근거: 승인. schema allowed attribute와 instance value를 분리하고 공간 block을 유지하는 기준이 타당하다.
- 검수자·검수 일시·승인 여부: ChatGPT AI 초안 / 2026-11-02 / 인간 승인 아님 — 실제 검수자가 확인·수정·서명 필요

## PILOT_Q6_01 — S-101 Wreck 정의의 원문과 Feature Catalogue 출처를 알려줘.

출처 및 고정 입력 조건:
```json
{
  "source_references": {
    "edition": "2.0.0",
    "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
    "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
    "review_scope": "WHOLE_SOURCE_NO_PRESELECTED_FEATURE_LOCATORS"
  },
  "spatial_source_condition": null
}
```

- 필수 작업: Wreck의 FC 원문 정의를 정확히 제시하고 edition/source hash/Feature locator를 연결한다.
- 허용 답안과 대안: 원문은 정확히 `The ruined remains of a stranded or sunken vessel which has been rendered useless.` 번역은 보조 설명으로 추가 가능.
- 반드시 포함할 근거: S-101 FC 2.0.0, source hash 2743d068..., Wreck FeatureType locator.
- 공간 정답 또는 미확정 사유: 해당 없음.
- 추가 입력 필요 여부와 이유: 불필요.
- 실제 확인한 출처·위치(locator): //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='Wreck']]
- AI 후보를 초기 판단 전에 보았는지: 예. 본 문서는 frozen_v5/GOLD v2/Oracle 근거를 이용한 AI 보조 초안이므로 인간 독립검수 조건을 충족하지 않음.
- 판단 및 근거: 승인. 원문 인용 요구와 source locator가 명확하다.
- 검수자·검수 일시·승인 여부: ChatGPT AI 초안 / 2026-11-02 / 인간 승인 아님 — 실제 검수자가 확인·수정·서명 필요

## PILOT_Q6_02 — 등대와 부표를 구분하는 S-101 근거를 알려줘.

출처 및 고정 입력 조건:
```json
{
  "source_references": {
    "edition": "2.0.0",
    "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
    "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
    "review_scope": "WHOLE_SOURCE_NO_PRESELECTED_FEATURE_LOCATORS"
  },
  "spatial_source_condition": null
}
```

- 필수 작업: 등대의 조건부 구조/등화 Feature와 대표 부표 Feature를 구분해 FC 정의/geometry/근거를 비교한다.
- 허용 답안과 대안: 등대: Landmark/Building(구조물) + LightAllAround/LightSectored(등화)의 조건부 모델. 부표: LateralBuoy를 대표 floating aid로 비교 가능. LateralBuoy 하나가 모든 부표 종류를 포괄한다고 단정하면 불허.
- 반드시 포함할 근거: S-101 FC 2.0.0의 Landmark, Building, LightAllAround, LightSectored, LateralBuoy 정의/locator.
- 공간 정답 또는 미확정 사유: 해당 없음.
- 추가 입력 필요 여부와 이유: 불필요.
- 실제 확인한 출처·위치(locator): 각 FeatureType code locator(Landmark, Building, LightAllAround, LightSectored, LateralBuoy).
- AI 후보를 초기 판단 전에 보았는지: 예. 본 문서는 frozen_v5/GOLD v2/Oracle 근거를 이용한 AI 보조 초안이므로 인간 독립검수 조건을 충족하지 않음.
- 판단 및 근거: 조건부 승인. '부표 전체 분류'가 아니라 LateralBuoy 대표 비교라는 범위를 반드시 공개해야 한다.
- 검수자·검수 일시·승인 여부: ChatGPT AI 초안 / 2026-11-02 / 인간 승인 아님 — 실제 검수자가 확인·수정·서명 필요

## PILOT_Q6_03 — What source supports the S-101 definition of AnchorageArea?

출처 및 고정 입력 조건:
```json
{
  "source_references": {
    "edition": "2.0.0",
    "source_path": "outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml",
    "source_sha256": "2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc",
    "review_scope": "WHOLE_SOURCE_NO_PRESELECTED_FEATURE_LOCATORS"
  },
  "spatial_source_condition": null
}
```

- 필수 작업: AnchorageArea 정의의 공식 FC 출처와 edition/hash/locator를 제시한다.
- 허용 답안과 대안: S-101 Feature Catalogue 2.0.0의 AnchorageArea FeatureType이 출처이며, 정의는 `An area in which vessels or seaplanes anchor or may anchor.`
- 반드시 포함할 근거: S-101 FC 2.0.0, source hash 2743d068..., AnchorageArea locator.
- 공간 정답 또는 미확정 사유: 해당 없음.
- 추가 입력 필요 여부와 이유: 불필요.
- 실제 확인한 출처·위치(locator): //*[local-name()='S100_FC_FeatureType'][*[local-name()='code' and text()='AnchorageArea']]
- AI 후보를 초기 판단 전에 보았는지: 예. 본 문서는 frozen_v5/GOLD v2/Oracle 근거를 이용한 AI 보조 초안이므로 인간 독립검수 조건을 충족하지 않음.
- 판단 및 근거: 승인. 질문이 요구한 source와 정의가 직접 연결된다.
- 검수자·검수 일시·승인 여부: ChatGPT AI 초안 / 2026-11-02 / 인간 승인 아님 — 실제 검수자가 확인·수정·서명 필요
