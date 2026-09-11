# 24. Remaining RAG Development Plan

## 현재 상태

기준일: 2026-09-11

S-101 2.0 RAG는 `s101_core` 범위로 확장되었고, 최종 chunk 목표는 1,869개다.

현재 확인된 상태:

```text
S-101 core chunk target                  | 1,869
outputs/rag/s101_catalogue_db_embeddings | 1,333 rows generated
knowledge.document_chunks                | 605 rows loaded
DB rows with non-null embedding           | 605 rows
```

즉, 파일 기준 embedding 생성은 진행 중이지만, DB에는 아직 이전 605개만 반영되어 있다. `--upsert --replace-source`는 embedding job이 정상 종료된 뒤 실행되므로, 최종 1,869개 적재는 아직 완료 상태가 아니다.

현재 DB에 적재된 source:

```text
gbhd_s101_20_accident_relation_profile | 1
gbhd_s101_20_db_feature_profile        | 125
gbhd_s101_20_db_text_values            | 10
gbhd_s101_20_valid_geometry_profile    | 1
s101_attribute_catalogue_v2_xml        | 278
s101_feature_catalogue_v2_xml          | 190
```

아직 최종 DB 적재가 필요한 source:

```text
s101_product_specification_2_0_pdf
s101_dceg_2_0_pdf
s101_portrayal_catalogue_2_0
s158_101_validation_checks_1_1
```

## 남은 작업 1: 실행 중인 embedding job 상태 확정

먼저 일회성 embedding 컨테이너가 계속 실행 중인지 확인한다.

```powershell
docker ps --filter ancestor=docker-backend --format "table {{.ID}}\t{{.Status}}\t{{.Command}}"
```

부분 embedding 파일 진행률:

```powershell
(Get-Content -Path outputs\rag\s101_catalogue_db_embeddings.jsonl).Count
```

DB 적재 상태:

```powershell
docker exec an_geollm_postgis psql -U postgres -d gbhd_s101 -c "
select count(*) total,
       count(*) filter (where embedding is not null) embedded
from knowledge.document_chunks;
"
```

판단 기준:

- embedding file line count가 1,869면 generation 완료
- DB count가 1,869이고 null embedding이 0이면 upsert 완료
- embedding job이 멈췄고 file line count가 1,869 미만이면 resume 필요

## 남은 작업 2: S-101 core embedding 완료

현재 재개 명령:

```powershell
docker run --rm --network docker_default `
  -v "D:\An_GeoLLM:/app" `
  -w /app `
  -e S101_DB_URL=postgresql://postgres:postgres@an_geollm_postgis:5432/gbhd_s101 `
  -e S101_PRODUCT_SPECIFICATION=INT.IHO.S-101.2.0 `
  -e S101_CATALOGUE_VERSION=2.0.0 `
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 `
  -e OLLAMA_EMBEDDING_URL=http://host.docker.internal:11434/api/embed `
  -e EMBEDDING_MODEL=bge-m3 `
  -e EMBEDDING_BATCH_SIZE=8 `
  -e EMBEDDING_TIMEOUT_SEC=600 `
  docker-backend python -u /app/scripts/build_s101_catalogue_db_rag.py `
    --dataset-root /app/Dataset `
    --embed `
    --upsert `
    --replace-source
```

주의:

- `s101_catalogue_db_embeddings.jsonl`은 checkpoint 역할을 한다.
- 중단되더라도 같은 명령으로 재개 가능하다.
- 기존 `outputs/rag/embeddings_v2.jsonl`의 S-101 Product Spec/DCEG embedding은 재사용하도록 스크립트를 보정했다.

## 남은 작업 3: 최종 적재 검증

embedding job이 끝난 뒤 아래 검증이 통과해야 한다.

```sql
SELECT document_type, source_id, COUNT(*) total,
       COUNT(*) FILTER (WHERE embedding IS NULL) null_embeddings
FROM knowledge.document_chunks
WHERE metadata @> '{"product_id":"S-101","version":"2.0.0","product_specification":"INT.IHO.S-101.2.0"}'::jsonb
GROUP BY document_type, source_id
ORDER BY source_id, document_type;
```

기대 상태:

```text
total S-101 2.0 chunks | 1,869
null_embeddings        | 0
embedding dimension    | 1024
model                  | bge-m3
```

확인해야 할 source:

```text
gbhd_s101_20_accident_relation_profile
gbhd_s101_20_db_feature_profile
gbhd_s101_20_db_text_values
gbhd_s101_20_valid_geometry_profile
s101_attribute_catalogue_v2_xml
s101_dceg_2_0_pdf
s101_feature_catalogue_v2_xml
s101_portrayal_catalogue_2_0
s101_product_specification_2_0_pdf
s158_101_validation_checks_1_1
```

## 남은 작업 4: RAG 검색 smoke test

DB 적재 후 `services/standard_rag_agent/vdb.py` 경로가 S-101 2.0 metadata filter를 적용하는지 확인한다.

필수 질의:

```text
DepthArea definition
Obstruction attribute profile
Wreck portrayal
S-101 validation check
accident relation with S-101 feature
```

검증 포인트:

- 반환 chunk의 `product_id`가 `S-101`
- `version`이 `2.0.0`
- `product_specification`이 `INT.IHO.S-101.2.0`
- source가 S-101 1.0 또는 중복 PDF로 새지 않을 것

## 남은 작업 5: Orchestrator 응답 연결

RAG 검색이 통과하면 GeoLLM 응답에 근거를 붙인다.

필요 작업:

1. 공간 질의 결과에 S-101 catalogue 근거 연결
2. 사고-S101 relation 결과에 relation profile 근거 연결
3. 응답 provenance에 `source_file`, `section`, `source_id`, `document_type` 포함
4. 지도 layer 응답과 텍스트 근거를 같은 task result에 묶기

## 남은 작업 6: 성능 개선

현재 embedding은 느리다. 원인과 개선 방향:

```text
원인
- Portrayal catalogue chunk와 validation chunk가 상대적으로 무겁다.
- Ollama bge-m3 batch 처리 속도가 낮다.
- Docker job stdout/file I/O가 느릴 때 진행률 확인이 지연된다.

개선
- chunk size를 900 words에서 500-700 words로 조정 검토
- source별 embedding을 분리 실행
- product spec / dceg / portrayal / validation / db profile을 별도 output으로 분리
- 완료된 source는 source_id 단위로 lock 파일 생성
```

## 남은 작업 7: 다음 확장 범위

S-101 core가 완료된 뒤 진행한다.

1. `s100_foundation`
   - S-100 5.2.0
   - S-158-100
   - S100BPC
2. `safety_context`
   - SOLAS
   - 선박법령
   - 행정규칙
   - 사고 통계 CSV
   - 용어사전
3. `external_layer_metadata`
   - AIS/V-PASS/수치조류도/제한구역 ZIP의 geometry 원본이 아니라 schema, field, layer metadata만 embedding

## 완료 기준

S-101 RAG 완료는 아래 조건을 모두 만족해야 한다.

```text
knowledge.document_chunks S-101 2.0 rows >= 1,869
null embedding = 0
HNSW/vector index exists
S-101 2.0 metadata filter smoke test pass
GeoLLM answer includes RAG provenance
accident-S101 answer includes relation evidence
```
