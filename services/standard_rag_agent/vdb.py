import os
import json
import urllib.request
from typing import List, Dict, Any
from sqlalchemy import text

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


def _query_embedding(query: str):
    endpoint = os.getenv('OLLAMA_EMBEDDING_URL', ollama_base_url() + '/api/embed')
    body = json.dumps({'model': os.getenv('EMBEDDING_MODEL', 'bge-m3'), 'input': [query]}).encode()
    request = urllib.request.Request(endpoint, data=body, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=int(os.getenv('EMBEDDING_TIMEOUT_SEC', '600'))) as response:
        result = json.load(response)
    return result['embeddings'][0]

# Fallback Mock Data
MOCK_DOCUMENTS = [
    {
        "doc_id": "doc-s101-001",
        "title": "S-101 Electronic Navigational Chart (ENC) Product Specification",
        "version": "1.2.0",
        "content": "위험객체(Hazard) 중 침선(Wreck)은 해상 운항에 중대한 위협이 되므로 수심 20m 미만 지역에서 반드시 표시되어야 한다.",
        "section": "12.3 Wrecks",
        "keywords": ["위험객체", "침선", "s101", "수심"],
        "clearance": "PUBLIC"
    },
    {
        "doc_id": "doc-law-001",
        "title": "해양환경관리법",
        "version": "2025.01",
        "content": "해상풍력 단지 개발 시 보호구역으로 지정된 해양보호구역에서는 최소 2km 이상 이격하여야 한다.",
        "section": "제15조 제2항",
        "keywords": ["해상풍력", "보호구역", "거리", "이격"],
        "clearance": "PUBLIC"
    }
]

def search_vdb(query: str, top_k: int = 2, user_id: str = "system", clearance_level: str = "PUBLIC", rag_filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    사용자 쿼리를 임베딩하여 pgvector의 코사인 유사도 검색(<=>)을 수행합니다.
    로컬 DB 연결 실패 시 기존의 Mock 로직으로 자동 전환됩니다.
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
                # 벡터를 JSON string 변환하여 바인딩
                metadata_filter = {key: value for key, value in rag_filters.items() if key != "candidate_document_ids"}
                params = {"vector": str(query_vector), "top_k": top_k, "metadata_filter": json.dumps(metadata_filter)}
                result = db.execute(sql, params).mappings().all()
                
                if result:
                    return [dict(r) for r in result]
        except Exception as e:
            logger.error("pgvector search failed, falling back to mock", error=str(e))
    
    # Fallback 로직 (보안 필터 적용)
    logger.warning("Falling back to Mock Vector DB Search")
    results = []
    query_lower = query.lower()
    
    clearance_map = {"PUBLIC": 1, "RESTRICTED": 2, "SECRET": 3}
    user_lvl = clearance_map.get(clearance_level.upper(), 1)
    
    filtered_count = 0
    
    candidate_ids = set(rag_filters.get("candidate_document_ids", []))
    for doc in MOCK_DOCUMENTS:
        req_lvl = clearance_map.get(doc.get("clearance", "PUBLIC"), 1)
        if user_lvl >= req_lvl:
            if candidate_ids and doc.get("doc_id") not in candidate_ids:
                continue
            score = sum(1 for kw in doc["keywords"] if kw in query_lower)
            if score > 0:
                results.append({"doc": doc, "score": score})
        else:
            if any(kw in query_lower for kw in doc["keywords"]):
                filtered_count += 1
                
    if filtered_count > 0:
        log_data_access(user_id, "READ", "mock_vector_db", clearance_level, "FILTERED", f"{filtered_count} docs denied")
        logger.warning(f"{filtered_count} RAG documents filtered out due to clearance")
            
    results.sort(key=lambda x: x["score"], reverse=True)
    return [r["doc"] for r in results[:top_k]]
