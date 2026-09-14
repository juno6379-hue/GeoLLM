# Phase 5.6 용어사전 기반 온톨로지 확장

상태: 구현 완료

## 목적

Phase 5.6은 `Dataset/용어사전.xls`를 단순 참고자료가 아니라 해양 GeoLLM의 한국어 해양 vocabulary 원천으로 승격하는 단계다.

온톨로지는 근거 중심으로 유지한다.

- 한국어 사용자 용어는 용어사전 workbook에서 가져온다.
- S-101 Feature Catalogue와 DCEG는 표준 feature 의미를 제공한다.
- GBENC/PostGIS는 실행 가능한 feature instance 사실을 제공한다.
- 사고 CSV와 relation table은 사고 사실과 사고-객체 관계를 제공한다.
- RAG는 설명과 인용을 제공하지만, 공간적 사실 자체를 대체하지 않는다.

## 원천 자료 역할

| 원천 | 역할 |
|---|---|
| `Dataset/용어사전.xls` | `MarineTerm` 표면어, 정의, alias |
| `data/s101_feature_catalogue_v2_parsed.json` | Feature, 정의, geometry primitive 기준 |
| `outputs/rag/*_chunks.jsonl` | DCEG, 표준, 법령 설명 근거 |
| `serving.accident_s101_relation_current` | 사고-S101 relation 실행 근거 |
| `Dataset/해양경찰청_해상조난사고*.csv` | 사고 event 및 집계 원천 |
| `Dataset/해양수산부_공동활용체계_해양지명_20221231.csv` | 지명 및 해양명 원천 |

## 생성 산출물

- `outputs/dictionaries/marine_term_dictionary.yaml`
- `outputs/dictionaries/marine_term_taxonomy.yaml`
- `outputs/review/kg_needs_review.jsonl`
- `outputs/graph/nodes_marine_terms.jsonl`
- `outputs/graph/nodes_term_taxonomy.jsonl`
- `outputs/graph/edges_term_taxonomy.jsonl`

## Taxonomy

parser는 각 용어를 다음 controlled class 중 하나로 분류한다.

- `hazard_feature_term`
- `accident_term`
- `place_term`
- `traffic_term`
- `bathymetry_environment_term`
- `spatial_layer_term`
- `law_regulation_term`
- `technology_or_english_term`
- `maritime_domain`

이 taxonomy는 보수적으로 적용한다. 모호하거나 mapping되지 않은 용어는 검토 없이 실행 가능한 feature 의미로 승격하지 않는다.

## 사고자료 정책

`해양경찰청_해상조난사고*` 자료는 순수 RAG 자료로만 취급하지 않는다.

- 건수, 거리, 지도, 공간 predicate는 구조화 사고 row와 relation table을 사용한다.
- 데이터셋 설명, field 의미, 서술형 요약, 인용 설명은 RAG를 사용한다.
- graph proximity만으로 사고 원인을 추론하지 않는다.

## 검증 결과

Phase 5.6 build 기준:

- Marine terms: `2222`
- Term-to-Feature edges: `43`
- Term-to-Concept edges: `12`
- Taxonomy classes: `9`
- Review queue records: `289`
- KG ontology validation: `PASS`

## 남은 작업

- `outputs/review/kg_needs_review.jsonl`를 전문가 검토 workflow와 연결한다.
- S-101 FC/DCEG 기반 수동 검수 결과를 `data/marine_term_dictionary.yaml`에 누적한다.
- 한국어 용어와 실행 slot 사이의 불명확한 mapping을 줄인다.
