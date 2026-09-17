# Dataset Evidence Fast Path Error Log

Date: 2026-09-17

## Scope

This note records the Dataset provenance / embedding evidence issues found while testing queries such as:

- `해양경찰청 해상조난사고 데이터셋은 어떤 근거로 적재되고 임베딩됐는지 알려줘`
- `해양지명 gazetteer와 도서지명 gazetteer가 어떤 근거로 적재되었는지 설명해줘`
- `항로표지정보_20250623.csv는 임베딩 되었는지 Dataset 근거를 확인해줘`

## Problems Found

1. Dataset evidence queries could fall into the legal/standard no-evidence path.
   - Symptom: embedded accident datasets were answered as `NO_AUTHORITATIVE_EVIDENCE`.
   - Cause: dataset/provenance intent detection was too narrow and biased toward gazetteer-only terms.
   - Fix: generalized `_looks_like_dataset_evidence_query()` around Dataset, file, embedding, provenance, coverage, and chunk intent signals.

2. Dataset evidence answers were hardcoded.
   - Symptom: accident dataset questions returned marine/island gazetteer prose.
   - Cause: `fast_dataset_evidence_answer_node()` contained fixed gazetteer and accident answer templates.
   - Fix: answer generation now reads live `knowledge.document_chunks` and summarizes matched source files, document types, chunk counts, and null embedding counts.

3. The fast path queried the wrong database first.
   - Symptom: `knowledge.document_chunks` looked empty from the app even though live DB checks showed embedded chunks.
   - Cause: Dataset evidence lookup preferred `POSTGIS_URL=marine_geo`; live embeddings are in `S101_DB_URL=gbhd_s101`.
   - Fix: `_dataset_evidence_db_url()` now prefers `S101_DB_URL` before `POSTGIS_URL`.

4. Normalized query broke exact Dataset/file-name lookup.
   - Symptom: `항로표지정보_20250623.csv` was normalized to `Fairway표지 정보_20250623.csv`, causing false matches.
   - Cause: Dataset evidence node used `normalized_query` before the original query.
   - Fix: Dataset evidence node uses the original query first, preserving file names and source strings.

5. Dataset evidence lookup overmatched law documents.
   - Symptom: law CSV chunks appeared in dataset embedding/provenance answers.
   - Cause: SQL allowed any metadata containing `Dataset/`, including `document_type='law'`.
   - Fix: live lookup now restricts candidates to `dataset_profile`, `accident_data`, and `supplemental_document`.

## Verified Results

### 항로표지정보

Query:

```text
항로표지정보_20250623.csv는 임베딩 되었는지 Dataset 근거를 확인해줘
```

Result:

- route: `dataset_evidence_lookup`
- sources: 1
- embedded chunks: 1
- document types: `dataset_profile 1`
- embedding NULL: 0
- source: `Dataset/해양수산부 부산지방해양수산청_항로표지정보_20250623.csv`

### 해양경찰청 해상조난사고

Query:

```text
해양경찰청 해상조난사고 데이터셋은 어떤 근거로 적재되고 임베딩됐는지 알려줘
```

Result:

- route: `dataset_evidence_lookup`
- sources: 5
- embedded chunks: 19
- document types: `accident_data 13`, `dataset_profile 6`
- embedding NULL: 0
- key sources:
  - `Dataset/해양경찰청_해상조난사고 상세데이터 현황_20251231 (1).csv`
  - `Dataset/해양경찰청_해상조난사고  유형별 사고 척수_20251231.csv`
  - `Dataset/해양경찰청_해상조난사고 해역별 사고 척수_20251231.csv`
  - `Dataset/rag_sources/해양경찰청_해상조난사고 상세데이터 현황_20251231.csv`
  - `Dataset/Ref_Data/해양경찰청_해상조난사고 상세데이터 현황_20251231.csv`

### 해양지명 / 도서지명

Query:

```text
해양지명 gazetteer와 도서지명 gazetteer가 어떤 근거로 적재되었는지 설명해줘
```

Result:

- route: `dataset_evidence_lookup`
- sources: 10
- embedded chunks: 15
- document types: `dataset_profile 12`, `supplemental_document 3`
- embedding NULL: 0
- law/no-evidence route avoided

## Follow-Up

- Quality metrics for dataset evidence are still marked by the generic quality collector as unavailable/low because this route does not yet produce KG similarity scores.
- Next improvement: compute dataset evidence quality from exact source-file match, document type confidence, embedding availability, and source SHA-256 provenance.
