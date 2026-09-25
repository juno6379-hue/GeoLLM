import os
import json
import urllib.request
from typing import List, Dict, Any
from sqlalchemy import bindparam, text

import data.database as db_module
from shared.observability.logger import get_logger
from shared.observability.audit_logger import log_data_access
from services.llm_config import llm_api_enabled, ollama_base_url

logger = get_logger("standard_rag_agent.vdb")

DEFAULT_S101_METADATA_FILTER = {
    "product_id": "S-101",
    "version": os.getenv("S101_CATALOGUE_VERSION", "2.0.0"),
    "product_specification": os.getenv("S101_PRODUCT_SPECIFICATION", "INT.IHO.S-101.2.0"),
}
METADATA_FILTER_KEYS = {"product_id", "version", "product_specification", "document_type", "source_id", "source_file", "source_path"}


def _default_metadata_filter() -> Dict[str, Any]:
    raw_filter = os.getenv("S101_RAG_METADATA_FILTER")
    if raw_filter:
        try:
            parsed = json.loads(raw_filter)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            logger.warning("Ignoring invalid S101_RAG_METADATA_FILTER")
    return DEFAULT_S101_METADATA_FILTER.copy()


def _normalize_metadata_filter(rag_filters: Dict[str, Any]) -> Dict[str, Any]:
    normalized = {}
    for key, value in rag_filters.items():
        if key not in METADATA_FILTER_KEYS:
            continue
        if value in (None, "", []):
            continue
        if isinstance(value, list):
            if len(value) != 1:
                continue
            value = value[0]
        normalized[key] = value
    return normalized


def _query_embedding(query: str):
    endpoint = os.getenv('OLLAMA_EMBEDDING_URL', ollama_base_url() + '/api/embed')
    body = json.dumps({'model': os.getenv('EMBEDDING_MODEL', 'bge-m3'), 'input': [query]}).encode()
    request = urllib.request.Request(endpoint, data=body, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=int(os.getenv('EMBEDDING_TIMEOUT_SEC', '600'))) as response:
        result = json.load(response)
    return result['embeddings'][0]

class RetrievalUnavailable(RuntimeError):
    """A source failure must not be represented as a successful empty search."""


def search_vdb(query: str, top_k: int = 2, user_id: str = "system", clearance_level: str = "PUBLIC", rag_filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    사용자 쿼리를 임베딩하여 pgvector의 코사인 유사도 검색(<=>)을 수행합니다.
    검색 실패 시 가짜 문서로 대체하지 않습니다.
    """
    
    # DB 연결 확인
    db_module.init_engines()
    session_factory = db_module.PostgisSessionLocal
    if os.getenv('S101_DB_URL'):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        session_factory = sessionmaker(bind=create_engine(os.getenv('S101_DB_URL'), pool_pre_ping=True))
    db_available = False
    if session_factory:
        try:
            with session_factory() as db:
                db.execute(text("SELECT 1"))
            db_available = True
        except Exception:
            db_available = False
            
    rag_filters = {**_default_metadata_filter(), **(rag_filters or {})}
    if db_available and llm_api_enabled():
        try:
            logger.info("Executing real pgvector similarity search")
            query_vector = _query_embedding(query)

            with session_factory() as db:
                # <=> 는 코사인 거리 연산자 (pgvector)
                candidate_ids = [str(item) for item in (rag_filters.get("candidate_document_ids") or []) if item]
                candidate_filter_sql = "AND chunk_id IN :candidate_document_ids" if candidate_ids else ""
                sql = text(f"""
                    SELECT chunk_id AS doc_id,
                           COALESCE(metadata->>'title', metadata->>'source_path', source_id) AS title,
                           COALESCE(metadata->>'version', 'v2') AS version,
                           content,
                           COALESCE(metadata->>'section', '') AS section,
                           source_id,
                           source_sha256,
                           metadata,
                           1 - (embedding <=> CAST(:vector AS vector)) AS similarity
                    FROM knowledge.document_chunks
                    WHERE embedding IS NOT NULL
                      AND (:metadata_filter = '{{}}' OR metadata @> CAST(:metadata_filter AS jsonb))
                      {candidate_filter_sql}
                    ORDER BY embedding <=> :vector 
                    LIMIT :top_k
                """)
                if candidate_ids:
                    sql = sql.bindparams(bindparam("candidate_document_ids", expanding=True))
                # 벡터를 JSON string 변환하여 바인딩
                metadata_filter = _normalize_metadata_filter(rag_filters)
                params = {"vector": str(query_vector), "top_k": top_k, "metadata_filter": json.dumps(metadata_filter)}
                if candidate_ids:
                    params["candidate_document_ids"] = candidate_ids
                result = db.execute(sql, params).mappings().all()

                if result:
                    rows = [dict(r) for r in result]
                    best_similarity = max(float(row.get("similarity") or 0.0) for row in rows)
                    min_graph_similarity = float(os.getenv("RAG_GRAPH_MIN_SIMILARITY", "0.60"))
                    if not candidate_ids or best_similarity >= min_graph_similarity:
                        return rows
                    logger.warning(
                        "Graph-scoped candidate filter returned low-similarity rows; retrying metadata-scoped vector search",
                        best_similarity=best_similarity,
                        threshold=min_graph_similarity,
                    )
                if candidate_ids:
                    logger.warning("Graph-scoped candidate filter returned no usable rows; retrying metadata-scoped vector search")
                    sql = text("""
                        SELECT chunk_id AS doc_id,
                               COALESCE(metadata->>'title', metadata->>'source_path', source_id) AS title,
                               COALESCE(metadata->>'version', 'v2') AS version,
                               content,
                               COALESCE(metadata->>'section', '') AS section,
                               source_id,
                               source_sha256,
                               metadata,
                               1 - (embedding <=> CAST(:vector AS vector)) AS similarity
                        FROM knowledge.document_chunks
                        WHERE embedding IS NOT NULL
                          AND (:metadata_filter = '{}' OR metadata @> CAST(:metadata_filter AS jsonb))
                        ORDER BY embedding <=> :vector
                        LIMIT :top_k
                    """)
                    params = {"vector": str(query_vector), "top_k": top_k, "metadata_filter": json.dumps(metadata_filter)}
                    result = db.execute(sql, params).mappings().all()
                    if result:
                        return [dict(r) for r in result]
        except Exception as e:
            logger.error("pgvector search failed; no evidence returned", error=str(e))
            raise RetrievalUnavailable("문서 검색 DB 또는 임베딩 엔진을 사용할 수 없습니다.") from e
    
    if not db_available or not llm_api_enabled():
        raise RetrievalUnavailable("문서 검색 DB 또는 임베딩 엔진이 준비되지 않았습니다.")
    return []
