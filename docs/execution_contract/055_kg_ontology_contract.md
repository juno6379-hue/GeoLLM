# Phase 5.5 KG 온톨로지 계약

상태: 초안 강제 적용

## 목적

Phase 5.5는 지식그래프가 어떤 의미 단위와 관계를 가질 수 있는지 정의한다. 사고 relation, EvidenceBundle, 결과 provenance를 확장하기 전에, KG가 실행 판단을 대신하지 않도록 의미 계약을 먼저 고정한다.

중요한 구분은 다음과 같다.

- S-101 `Feature`는 표준 카탈로그의 feature class를 뜻한다.
- GBENC `FeatureInstance`는 실제 DB row와 geometry를 가진 객체를 뜻한다.
- `DataLayer`, `Tool`, `QueryTemplate`은 registry/schema 검증을 통과해야 실행 후보가 된다.
- KG path는 의미 설명과 provenance이지, 실행 권한 자체가 아니다.

## 계약 파일

기준 계약 파일은 다음이다.

```text
data/kg_ontology_contract.yaml
```

이 파일은 다음을 정의한다.

- 전자해도 객체, GBENC feature instance, 해양용어, derived concept, 사고자료, 문서, agent, tool, query template, evidence 관련 node type
- subject/object type이 제한된 edge type
- 검증 상태: `VERIFIED`, `CANDIDATE`, `DEFERRED`, `NEEDS_REVIEW`
- 공간, 사고, RAG, KG provenance에 대한 EvidenceBundle mapping

## 의미 계층

1. 전자해도 표준 객체

   `FeatureCatalogue`, `Feature`, `Attribute`, `GeometryType`은 S-101 표준 vocabulary를 나타낸다. 이들은 공간 쿼리 결과 row가 아니다.

2. 실제 GBENC DB 객체

   `FeatureInstance`는 `projection.s101_feature_current` 또는 검증된 serving view에서 나온 실행 가능한 객체를 나타낸다.

3. 해양 용어

   `MarineTerm`은 사용자 표현과 alias를 `Feature` 또는 `DerivedConcept` 후보로 연결한다. 이 mapping은 해석을 돕지만, 단독으로 공간쿼리를 실행 가능하게 만들지는 않는다.

4. 사고 자료

   `AccidentEvent`, `AccidentType`은 위험 개념과 후보 관계를 가질 수 있다. `nearFeature`, `occurredIn`, `overlapsFeature` 같은 공간 관계는 결정론적 geometry 근거가 있을 때만 확정한다.

5. 법령과 문서

   `StandardDocument`, `LawDocument`, `DocumentChunk`는 RAG 답변을 지원한다. 문서 유사도나 graph path만으로 `supportsConcept`를 `VERIFIED`로 승격하지 않는다.

6. Agent와 Tool 계층

   `Agent`, `Tool`, `QueryTemplate`은 사용 가능한 기능을 설명한다. 실제 실행 binding은 `SchemaBindingAdapter`와 `ExecutionValidator`를 통과해야 한다.

7. 실행계약

   `QueryExecutionContext`는 runtime bridge다. KG는 `semantic_resolution`, `kg`, evidence provenance를 보강하지만, 통제된 merge policy 없이 실행 slot을 덮어쓰지 않는다.

8. 결과 근거

   결과는 `EvidenceBundle`에서 `spatial_feature_evidence`, `accident_relation_evidence`, `rag_evidence`, `kg_provenance`를 분리해야 한다.

## Validator

`services.orchestrator.kg_ontology_validator.validate_kg_ontology`는 다음을 검사한다.

- 알 수 없는 node type
- node 또는 edge provenance 누락
- 알 수 없는 edge predicate
- edge subject/object type 위반
- 알 수 없는 verification status
- provenance 없는 `VERIFIED` edge

이 validator는 LLM을 쓰지 않는 결정론적 검사 도구이며, 로컬 검증과 향후 CI에 사용할 수 있다.

## 종료 기준

- 온톨로지 계약 파일이 존재하고 source control 대상이 된다.
- 현재 KG 산출물이 계약에 대해 PASS하거나, 수정 가능한 명시적 오류를 낸다.
- GraphRAG provenance를 stable node/edge ID 기반 `EvidenceItem`으로 변환할 수 있다.
- 사고 및 문서 관계는 결정론적 근거가 생기기 전까지 candidate/deferred 상태를 유지한다.
