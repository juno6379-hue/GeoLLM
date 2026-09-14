# Phase 6 EvidenceBundle 통합

상태: 구현 완료

## 목적

Phase 6은 흩어져 있던 provenance payload를 typed `EvidenceItem`으로 변환하고, 최종 응답에서 `EvidenceBundle`로 반환하는 단계다.

핵심은 “근거를 섞지 않는 것”이다. 공간 실행 근거, 사고 relation 근거, 문서 인용, KG 경로는 서로 다른 성격이므로 같은 목록에 뭉치지 않는다.

## Evidence partition

- `spatial_feature_evidence`
  - S-101 feature query 또는 실제 공간 객체 row에서 나온 근거
- `spatial_layer_evidence`
  - 수치조류, 와류, 신항만, 도서지명, 바다갈라짐 등 공간 레이어 근거
- `accident_relation_evidence`
  - 사고와 feature instance 사이의 relation row 또는 relation 조회 근거
- `regulatory_evidence`
  - 법령, 고시, 행정규칙, 공식자료 근거
- `rag_evidence`
  - 문서 chunk, citation, source locator 근거
- `kg_provenance`
  - GraphRAG 의미 경로와 KG edge metadata

## 구현 위치

- `services/orchestrator/evidence_builder.py`
- `services/standard_rag_agent/agent.py`
- `services/orchestrator/graph.py`

최종 응답은 nested `evidence_bundle`과 dashboard 호환용 top-level evidence 배열을 함께 노출한다.

## 정책

KG 근거는 의미 선택 경로를 설명한다. 실제 객체가 특정 위치에 존재한다는 사실은 spatial predicate와 DB 결과로 증명해야 한다.

RAG 근거는 문서 인용과 설명을 제공한다. 공간 predicate, 사고 relation table, 법령·고시 registry를 대체하지 않는다.

사고 relation 근거는 거리 기반 근접 관계를 제공한다. 근접 관계만으로 사고 원인이나 책임을 단정하지 않는다.
