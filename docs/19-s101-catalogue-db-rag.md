# 19. S-101 Catalogue and S100_dev DB RAG Build

## 목적

S-101 v2.0 기반 의미 검색 품질을 높이기 위해 기존 PDF/DOCX 문서 RAG와 별도로 다음 설명 텍스트를 `knowledge.document_chunks`에 추가 적재한다.

- S-101 Feature Catalogue XML의 Feature 정의/설명
- S-101 Feature Catalogue XML의 Attribute 설명 및 listed value
- S100_dev DB의 S-101 feature type별 실제 적재 프로파일
- S100_dev DB의 실제 textual attribute value 샘플

개별 geometry feature instance 전체는 임베딩하지 않는다. geometry와 대량 instance row는 PostGIS 공간 질의 대상으로 유지하고, RAG에는 사람이 해석할 수 있는 정의, 설명, 규칙, 프로파일 텍스트만 넣는다.

## 입력

- XML parse result: `data/s101_feature_catalogue_v2_parsed.json`
- DB: `S101_DB_URL` 우선, 없으면 `POSTGIS_URL`
- 주요 DB 테이블:
  - `projection.s101_feature_current`
  - `canonical.feature_record`
  - `canonical.feature_attribute_value`

## 산출물

기본 산출물은 `.gitignore` 대상인 `outputs/` 아래 생성된다.

- `outputs/rag/s101_catalogue_db_chunks.jsonl`
- `outputs/rag/s101_catalogue_db_embeddings.jsonl`
- `outputs/reports/17_s101_catalogue_db_embedding_report.md`

각 row는 기존 `knowledge.document_chunks`와 호환되도록 `document_id`, `document_type`, `product_id`, `standard_type`, `source_id`, `source_sha256`, `metadata`, `embedding`을 포함한다.

## 실행

백엔드 컨테이너 환경 변수를 그대로 사용한다.

```powershell
docker exec geollm_backend python /app/scripts/build_s101_catalogue_db_rag.py --embed --upsert --replace-source
```

`--replace-source`는 이 스크립트가 관리하는 source만 삭제 후 재삽입한다. 기존 6,252건의 문서 RAG chunk는 삭제하지 않는다.

임베딩 결과는 `outputs/rag/s101_catalogue_db_embeddings.jsonl`에 batch 단위로 append된다. 작업이 중단되면 같은 명령을 다시 실행해 이미 저장된 `chunk_id`는 건너뛰고 남은 chunk만 이어서 임베딩한다.

관리 대상 source id:

- `s101_feature_catalogue_v2_xml`
- `s101_attribute_catalogue_v2_xml`
- `s100_dev_s101_db_feature_profile`
- `s100_dev_s101_db_text_values`

## 적재 정책

Feature Catalogue XML은 feature/attribute 단위로 chunk를 만든다.

S100_dev DB는 다음 단위로 요약 chunk를 만든다.

- `feature_type_code`별 instance count, geometry count, geometry type, observed attribute profile
- `natc`별 textual attribute value 샘플

좌표, geometry, 개별 feature instance row, 단순 numeric code 반복값은 임베딩 대상에서 제외한다. 이 정보는 PostGIS/Registry/KG에서 처리한다.

## 검증 쿼리

```sql
SELECT document_type, COUNT(*)
FROM knowledge.document_chunks
WHERE source_id IN (
  's101_feature_catalogue_v2_xml',
  's101_attribute_catalogue_v2_xml',
  's100_dev_s101_db_feature_profile',
  's100_dev_s101_db_text_values'
)
GROUP BY document_type
ORDER BY document_type;
```

```sql
SELECT COUNT(*) AS total, COUNT(*) FILTER (WHERE embedding IS NULL) AS null_embedding
FROM knowledge.document_chunks;
```

## 검색 연동

현재 `services/standard_rag_agent/vdb.py`는 `S101_DB_URL`이 설정되어 있으면 `knowledge.document_chunks`를 대상으로 pgvector cosine search를 수행한다. 따라서 이 적재가 끝나면 별도 코드 변경 없이 기존 RAG 검색 경로에서 새 S-101 catalogue/DB 설명 chunk가 검색 대상에 포함된다.
