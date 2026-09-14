# Phase 8.4 S-101/DCEG 매칭 점수화

## 목적

Phase 8.2의 자동 온톨로지 후보와 Phase 8.3의 승인 gate 사이에 S-101 Feature Catalogue 및 DCEG 근거를 추가한다. 이 단계의 결과는 registry 병합이나 실행 권한이 아니라 검토 근거이다.

## 입력

- `outputs/ontology/ontology_binding_proposals.jsonl`
- `outputs/ontology/dataset_profiles.jsonl`
- `data/s101_feature_dictionary_v2.yaml`
- `data/s101_attribute_dictionary_v2.yaml`
- `data/s100_s101_mapping_registry.yaml`
- `outputs/rag/s101_dceg_chunks.jsonl`

## 출력

- `outputs/ontology/s101_dceg_match_scores.jsonl`
- `outputs/ontology/s101_dceg_match_summary.json`
- `outputs/review/s101_dceg_match_needs_review.jsonl`

## 점수 구성

- semantic/layer hint: 기존 `semantic_mapping` 또는 layer type이 제안한 feature 후보와 일치하는지 확인한다.
- lexical score: dataset 이름, source asset, Shapefile 필드, 규칙 키워드와 feature code/name/alias/definition의 토큰 겹침을 계산한다.
- primitive score: Shapefile geometry가 S-101 permitted primitive와 맞는지 확인한다.
- DCEG evidence: DCEG chunk에서 feature 이름, code, alias가 확인되는지 기록한다.
- attribute match: Shapefile 필드명과 S-101 attribute code/alias/name을 비교해 후보 attribute를 제시한다.

## 안전 정책

- `HIGH` confidence도 자동 승인 사유가 아니다.
- S-101 feature와 매칭되어도 DB 물리 테이블, geometry column, SRID, QueryTemplate, ToolBinding 검증 전에는 실행할 수 없다.
- Catalogue에 없는 후보는 `missing_catalogue_hints`로 남기고 검토 큐에 넣는다.
- 예를 들어 `Rock`, `MarineProtectedArea`처럼 상위 의미상 필요하지만 현재 S-101 feature code에 없는 후보는 대체 후보와 함께 사람이 검토해야 한다.

## 다음 단계

Phase 8.5에서는 이 매칭 결과를 KG provenance 및 EvidenceBundle의 KG/RAG 근거 후보로 변환한다. 또한 법령·고시 RAG chunk와 공간 레이어 사이의 `authorizedBy`, `definedBy` 후보를 함께 점수화한다.
