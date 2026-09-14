# Phase 8.1 해양수산부 범용 Upper Ontology 1차

## 목적

1차 목표는 개별 데이터셋을 바로 `위험`, `사고`, `공간분석` 같은 실행 범주에 넣지 않고, 먼저 상위 온톨로지와 해양수산 업무 도메인을 통과하게 만드는 것이다.

이 구조가 필요한 이유는 `보호수역` 사례에서 분명하다. 보호수역은 항행 위험 자체가 아니라 보호·보전 목적의 공간 제약 레이어다. 따라서 위험해역이 아니라 `protected_area`로 분류하고, 필요하면 법령·공식자료 근거와 함께 의사결정 지원 근거로 반환해야 한다.

## 1차 구조

```text
KG Inventory
-> Upper Ontology
-> 해양수산 업무 Domain
-> S-100/S-101 Mapping
```

## 추가 Registry

- `data/kg_inventory_registry.yaml`
  - 현재 KG가 보유한 표준, 용어, 데이터, 법령, 실행계약, evidence 자산의 inventory를 정의한다.
- `data/upper_ontology_registry.yaml`
  - `navigational_hazard`, `regulated_area`, `protected_area`, `hydrographic_observation`, `traffic_activity`, `accident_risk`, `legal_authority` 같은 상위 분류를 정의한다.
- `data/mof_domain_registry.yaml`
  - 해양정책, 수산정책, 해운물류, 해사안전, 항만, 해양환경, 수로조사·해양정보 도메인을 정의한다.
- `data/s100_s101_mapping_registry.yaml`
  - GeoLLM 파생개념, 상위 분류, S-100/S-101/S-104/S-111/S-124 제품 의미를 연결한다.

## 해양수산 업무 도메인

해양수산부 용어사전 발간 자료는 해양수산 정책 용어를 해양정책, 수산정책, 해운물류, 해사안전, 항만 등 분야로 나누어 제공한다. 1차 registry는 여기에 해양환경과 수로조사·해양정보 축을 추가해 GeoLLM 실행 구조에 맞춘다.

## S-100/S-101 Mapping

S-101은 전자해도 기반의 항행 객체와 구역을 담당한다. 다만 모든 해양수산 데이터가 S-101 feature는 아니다.

- 위험객체: S-101 `Wreck`, `Obstruction`, `Rock`, `UnderwaterAwashRock`, `FoulGround`
- 규제·제한 해역: S-101 `RestrictedArea`, `TrafficSeparationScheme`, `MilitaryPracticeArea`
- 보호·보전 해역: S-101 `MarineProtectedArea`, 필요 시 `RestrictedArea`
- 선박교통 활동: S-101 `Fairway`, `RecommendedTrack`, `TrafficSeparationSchemeLanePart`, `VesselTrafficServiceArea`
- 수치조류도: S-111 성격이며 현재는 metadata_only
- 바다갈라짐/조석 예측: S-104 성격의 시간·수위 정보와 연결 가능

## 실행 원칙

- KG는 의미 후보를 제안한다.
- registry/schema adapter와 ExecutionValidator가 실행 가능 여부를 결정한다.
- 보호·보전, 규제·제한, 항행 위험은 서로 다른 상위 분류로 유지한다.
- EvidenceBundle은 공간, KG, RAG, 법령, 사고 근거를 섞지 않고 partition으로 반환한다.

## 1차 산출

- KG node type 추가: `KGInventory`, `UpperClass`, `DomainArea`, `SemanticMapping`
- KG edge type 추가: `belongsToUpperClass`, `belongsToDomain`, `mapsToProduct`, `mapsToSemanticMapping`, `domainUsesUpperClass`, `specializes`
- `protected_sea_area`는 `protected_area`로 분류한다.
- `hazard_area_lookup`과 `protected_area_lookup`을 분리한다.
