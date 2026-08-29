import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import dotenv
dotenv.load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from sqlalchemy import text
from data.database import get_enc_db
from shared.observability.logger import get_logger

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

logger = get_logger("scripts.build_rag_index")

def build_index():
    db_gen = get_enc_db()
    db = next(db_gen)
    
    if not db:
        logger.error("Failed to connect to GBENC DB.")
        return
        
    logger.info("Fetching primitives, codeinformation, rulefunctions...")
    
    # 조인 쿼리: primitives (객체_명_KR, FEATURE NAME_EN) -> codeinformation (type=0, name) -> rulefunctions (featurename)
    query = text('''
        SELECT 
            p."객체_명_KR" as term_ko,
            p."FEATURE NAME_EN" as feature_name_raw,
            p."정의" as description,
            c.code as nftc_code,
            c.name as feature_name_clean,
            r.functionname as rendering_rule
        FROM primitives p
        LEFT JOIN codeinformation c 
          ON LOWER(REPLACE(p."FEATURE NAME_EN", ' ', '')) = LOWER(c.name) AND c.type = 0
        LEFT JOIN rulefunctions r
          ON LOWER(c.name) = LOWER(r.featurename)
    ''')
    
    results = db.execute(query).fetchall()
    
    docs = []
    # 중복 nftc 코드를 모아두기 위한 dict
    feature_map = {}
    
    for row in results:
        term_ko = row.term_ko or ""
        feature_name = row.feature_name_clean or row.feature_name_raw or ""
        description = row.description or ""
        nftc = row.nftc_code
        rule = row.rendering_rule or ""
        
        if not feature_name:
            continue
            
        key = feature_name.lower()
        if key not in feature_map:
            feature_map[key] = {
                "term_ko": term_ko,
                "feature_name": feature_name,
                "description": description,
                "nftc_codes": set(),
                "rendering_rule": rule
            }
            
        if nftc is not None:
            feature_map[key]["nftc_codes"].add(nftc)
            
    # Document 객체 생성
    for key, data in feature_map.items():
        # 검색 대상 텍스트(page_content)는 한글명, 영문명, 설명 등을 합침
        page_content = f"명칭: {data['term_ko']}, {data['feature_name']}\n설명: {data['description']}"
        
        metadata = {
            "term_ko": data["term_ko"],
            "feature_name": data["feature_name"],
            "nftc_codes": list(data["nftc_codes"]),
            "rendering_rule": data["rendering_rule"]
        }
        
        docs.append(Document(page_content=page_content, metadata=metadata))
        
    logger.info(f"Generated {len(docs)} documents for RAG indexing.")
    
    if not docs:
        logger.error("No documents found. Aborting.")
        return
        
    if "OPENAI_API_KEY" not in os.environ:
        logger.error("OPENAI_API_KEY is missing in .env")
        return
        
    logger.info("Initializing OpenAI Embeddings & building FAISS index...")
    embed_model_name = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
    embeddings = OpenAIEmbeddings(model=embed_model_name)
    vectorstore = FAISS.from_documents(docs, embeddings)
    
    # 저장 경로
    save_dir = os.path.join(os.path.dirname(__file__), "..", "services", "registry", "rag_index")
    os.makedirs(save_dir, exist_ok=True)
    
    vectorstore.save_local(save_dir)
    logger.info(f"RAG Index saved locally to {save_dir}")

if __name__ == "__main__":
    build_index()
