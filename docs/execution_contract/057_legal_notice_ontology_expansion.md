# Phase 5.7 법령·고시 온톨로지 확장

## 목적

해양 공간 레이어는 단순한 도형 데이터가 아니다. 항만 예정지역, 선박교통관제구역, V-PASS, 바다갈라짐, 도서지명, 수치조류도 같은 레이어는 각각 법령, 고시, 행정규칙, 공식 해양조사 산출물에 근거한다.

이 단계의 목적은 공간 레이어를 법적·행정적·공식자료 근거와 연결하여, 결과 응답에서 “어떤 공간 분석을 했는가”뿐 아니라 “그 레이어가 어떤 근거로 정의되었는가”까지 설명할 수 있게 만드는 것이다.

## 추가한 레지스트리

`data/legal_notice_registry.yaml`

이 레지스트리는 다음 항목을 정의한다.

- `Law`: 공간 레이어의 법적 근거가 되는 법률
  - 예: `신항만건설 촉진법`, `토지이용규제 기본법`, `선박교통관제에 관한 법률`, `어선법`
- `LegalNotice`: 고시, 공고, 행정규칙 등 행정 문서
  - 예: `신항만건설 예정지역 지형도면 고시`, `선박교통관제에 관한 규정`, `선박패스(V-Pass) 장치 고시`
- `Authority`: 문서를 발행하거나 자료를 관리하는 기관
  - 예: 해양수산부, 해양경찰청, 국립해양조사원
- `OfficialDataset`: 법령 고시는 아니지만 공식 기관이 제공하는 해양조사·예측·지명 자료
  - 예: 도서지명, 바다갈라짐 예측정보, 수치조류도, 와류, AIS 항로분석

## KG 관계

새로 추가한 온톨로지 관계는 다음과 같다.

```text
DataLayer / DynamicTrafficLayer -> authorizedBy -> LegalNotice / OfficialDataset
DataLayer / DynamicTrafficLayer -> definedBy -> Law
LegalNotice / OfficialDataset -> publishedBy -> Authority
DataLayer / DynamicTrafficLayer -> derivedFrom -> OfficialDataset
```

의미는 다음과 같다.

- `authorizedBy`: 해당 레이어가 어떤 고시, 행정규칙, 공식자료에 의해 권한 또는 근거를 갖는지 나타낸다.
- `definedBy`: 해당 레이어가 어떤 법률 체계에 의해 정의되거나 위임되는지 나타낸다.
- `publishedBy`: 고시, 법령, 공식자료를 발행한 기관을 나타낸다.
- `derivedFrom`: 공간 레이어가 어떤 공식 원천 데이터셋에서 만들어졌는지 나타낸다.

## 보강한 레이어

- `planned_port_area`: 신항만 예정지역
- `vessel_traffic_control_area`: 선박안전교통관제구역
- `vpass_route_analysis`: V-PASS 항로분석
- `vpass_major_route`: V-PASS 주요통항로분석
- `island_gazetteer`: 도서지명
- `sea_parting_prediction`: 바다갈라짐 예측정보
- `tidal_current_surface`: 수치조류도
- `eddy_hazard_area`: 와류
- `ais_route_analysis`: AIS 항로분석
- `ais_major_route`: AIS 주요통항로분석

## 검증 결과

KG 재생성 결과:

```text
kg_generated nodes=8799 edges=9539
```

온톨로지 validator 결과:

```text
status=PASS
errors=0
```

## 응답 근거 모델

`EvidenceBundle`에 다음 partition을 추가했다.

```text
regulatory_evidence
```

최종 응답은 이제 다음 근거를 분리해서 반환할 수 있다.

- `spatial_feature_evidence`: S-101 객체 또는 실제 공간 객체 근거
- `spatial_layer_evidence`: 조류, 와류, 신항만, 도서지명 등 공간 레이어 근거
- `accident_relation_evidence`: 사고와 전자해도 객체의 거리·관계 근거
- `regulatory_evidence`: 법령, 고시, 행정규칙, 공식자료 근거
- `rag_evidence`: 문서/RAG 인용 근거
- `kg_provenance`: KG 경로 및 의미 관계 근거

## 남은 작업

- 법령·고시 원문을 RAG chunk와 더 정밀하게 연결해야 한다.
- `OfficialDataset` 중 `CANDIDATE` 상태인 자료는 원천기관 메타데이터와 고시 여부를 추가 확인해야 한다.
- 최종 답변 생성 단계에서 KG의 `authorizedBy`, `definedBy`, `publishedBy`, `derivedFrom` 경로를 자동으로 `regulatory_evidence`에 채우는 로직이 필요하다.
