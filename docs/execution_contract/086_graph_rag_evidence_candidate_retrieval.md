# Phase 8.6 Graph-RAG 후보 근거 검색 연결

## 목적

Phase 8.5에서 생성한 KG/RAG/법령 후보 근거를 Graph-RAG 검색 경로에 연결한다. 이 단계의 후보는 실행 권한이나 최종 사실 확정 근거가 아니라, 검색 범위와 응답 근거 묶음을 보강하는 사전 후보이다.

## 입력

- `outputs/evidence/kg_provenance_candidates.jsonl`
- `outputs/evidence/rag_evidence_candidates.jsonl`
- `outputs/evidence/regulatory_evidence_candidates.jsonl`
- 사용자 질의와 `QueryExecutionContext` 또는 `graph_context`
- KG 노드/엣지 파일
  - `outputs/graph/kg_nodes_v2.jsonl`
  - `outputs/graph/kg_edges_v2.jsonl`

## 처리 흐름

1. `GraphRAGRetriever`가 질의 토큰과 context 토큰을 기준으로 Phase 8.5 후보 근거를 점수화한다.
2. 후보의 `feature_code`, `layer_id`, `chunk_id`를 추출한다.
3. `feature_code`와 `layer_id`는 KG 기반 `target_features`, `target_layers`에 병합한다.
4. `chunk_id`는 `rag_filters.candidate_document_ids`에 넣어 pgvector 검색 범위를 좁힌다.
5. Standard RAG Agent는 Graph-RAG 결과의 후보 근거를 구조화 결과에 분리 보존한다.
6. `EvidenceBundle`은 후보 근거를 다음 partition에 나누어 담는다.
   - `kg_provenance`
   - `rag_evidence`
   - `regulatory_evidence`

## 출력

Graph-RAG 결과에는 다음 항목이 추가된다.

- `evidence_candidates.kg_provenance`
- `evidence_candidates.rag_evidence`
- `evidence_candidates.regulatory_evidence`
- `rag_filters.candidate_document_ids`
- `provenance.evidence_candidate_sources`
- `provenance.evidence_candidate_counts`

Standard RAG Agent의 `structured_result`에는 다음 항목이 추가된다.

- `kg_provenance_candidates`
- `rag_evidence_candidates`
- `regulatory_evidence_candidates`
- `evidence_candidate_summary`

## 검증 규칙

- 후보 근거는 `review_required` 값을 보존한다.
- 후보 근거는 KG/RAG/법령 partition을 섞지 않는다.
- `candidate_document_ids`는 실제 vector DB chunk id만 사용한다.
- mock fallback은 테스트 또는 명시 허용 환경에서만 사용한다.
- 공간 실행 여부는 여전히 `QueryExecutionContext -> ExecutionValidator PASS -> Tool 실행 -> EvidenceBundle 반환` 경로를 따라야 한다.

## 다음 보강 지점

- Phase 8.7에서 승인된 후보만 registry/KG에 병합하는 승격 규칙을 추가한다.
- Phase 8.8에서 RAG 검색 결과와 후보 근거 간 충돌을 탐지하고 `NEEDS_REVIEW`로 되돌리는 검증기를 추가한다.
