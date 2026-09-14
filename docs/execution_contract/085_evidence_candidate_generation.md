# Phase 8.5 Evidence 후보 생성

## 목적

Phase 8.4의 S-101/DCEG 매칭 점수와 법령·고시 registry를 Evidence 후보로 변환한다. 이 단계의 산출물은 Graph-RAG와 검토 workflow의 입력이며, registry 병합이나 Tool 실행 권한을 부여하지 않는다.

## 입력

- `outputs/ontology/s101_dceg_match_scores.jsonl`
- `outputs/ontology/ontology_binding_proposals.jsonl`
- `data/legal_notice_registry.yaml`
- `outputs/rag/s101_dceg_chunks.jsonl`

## 출력

- `outputs/evidence/kg_provenance_candidates.jsonl`
- `outputs/evidence/rag_evidence_candidates.jsonl`
- `outputs/evidence/regulatory_evidence_candidates.jsonl`
- `outputs/review/evidence_candidate_needs_review.jsonl`
- `outputs/evidence/phase85_evidence_candidate_summary.json`

## Evidence Partition

- `kg_provenance`: 자동 온톨로지 후보와 S-101 feature 간 `supportsFeature`, `mapsToFeature` 후보
- `rag_evidence`: DCEG chunk가 특정 S-101 feature를 뒷받침한다는 후보
- `regulatory_evidence`: 공식 데이터, 법령, 고시가 레이어를 `authorizedBy`, `definedBy`로 뒷받침한다는 후보

## 안전 정책

- 모든 산출물은 `CANDIDATE` 또는 검토 후보이다.
- `VERIFIED` KG edge로 즉시 쓰지 않는다.
- registry를 직접 수정하지 않는다.
- `execution_status: executable` 승격과 무관하다.
- EvidenceBundle에 넣을 때도 출처 partition을 유지한다.

## 다음 단계

Phase 8.6에서는 이 후보들을 Graph-RAG 검색 경로에 연결한다. 질문이 들어오면 KG가 먼저 후보 feature, 법령, 표준 chunk, 데이터 레이어를 좁히고 RAG 검색 범위를 줄이는 방식으로 발전시킨다.
