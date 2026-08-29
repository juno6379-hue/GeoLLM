# -*- coding: utf-8 -*-
import sys
import os

sys.path.append('/app/services')
from data.database import get_enc_db
from sqlalchemy import text
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.documents import Document

def build_index():
    db_gen = get_enc_db()
    db = next(db_gen)
    
    sql_prim = text('''
        SELECT "객체_명_KR", "FEATURE NAME_EN", "정의"
        FROM primitives 
        WHERE "객체_명_KR" IS NOT NULL
    ''')
    
    result_prim = db.execute(sql_prim).fetchall()
    
    docs = []
    print(f"Loaded {len(result_prim)} primitive features.")
    
    for row in result_prim:
        kr_name = row[0]
        en_name = row[1]
        definition = row[2] or ""
        
        if not en_name:
            continue
            
        en_name_clean = en_name.replace(" ", "").lower()
        
        sql_code = text('''
            SELECT code 
            FROM codeinformation 
            WHERE type = 0 AND LOWER(name) = :n
        ''')
        result_code = db.execute(sql_code, {"n": en_name_clean}).fetchall()
        nftc_codes = [r[0] for r in result_code]
        
        if not nftc_codes:
            continue
            
        content = f"객체명(한글): {kr_name}\n객체명(영문): {en_name}\n정의: {definition}"
        doc = Document(
            page_content=content,
            metadata={
                "feature_name": en_name_clean,
                "nftc_codes": nftc_codes,
                "kr_name": kr_name
            }
        )
        docs.append(doc)
        
    print(f"Building FAISS index for {len(docs)} documents...")
    
    # Use native Ollama Embeddings to bypass OpenAI SDK array issues
    embeddings = OllamaEmbeddings(
        model="bge-m3", 
        base_url="http://host.docker.internal:11434"
    )
    vectorstore = FAISS.from_documents(docs, embeddings)
    
    out_path = "/app/services/registry/rag_index"
    os.makedirs(out_path, exist_ok=True)
    vectorstore.save_local(out_path)
    
    print(f"Successfully saved FAISS index to {out_path}")

if __name__ == "__main__":
    build_index()
