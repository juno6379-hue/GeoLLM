import os
import re
from sqlalchemy import create_engine, text
from shared.observability.logger import get_logger

logger = get_logger("etl_gazetteer")

# 원본 Oracle/Postgres gbenc DB
SRC_DB = os.environ.get("GBENC_SOURCE_DB_URL", "")
# 로컬 GeoLLM PostGIS DB
DEST_DB = "postgresql://postgres:postgres@db:5432/marine_geo"

def etl_process():
    src_engine = create_engine(SRC_DB)
    dest_engine = create_engine(DEST_DB)
    
    # 1. 로컬 DB에 maritime_gazetteer 테이블 (재)생성
    with dest_engine.connect() as dest_conn:
        logger.info("Recreating maritime_gazetteer table in local DB...")
        dest_conn.execute(text("""
            DROP TABLE IF EXISTS maritime_gazetteer;
            CREATE TABLE maritime_gazetteer (
                id SERIAL PRIMARY KEY,
                name_kor VARCHAR(255),
                name_eng VARCHAR(255),
                geom GEOMETRY(Geometry, 4326),
                source VARCHAR(50) DEFAULT 'gbenc'
            );
            CREATE INDEX idx_gazetteer_name_kor ON maritime_gazetteer USING btree (name_kor);
            CREATE INDEX idx_gazetteer_name_eng ON maritime_gazetteer USING btree (name_eng);
            CREATE INDEX idx_gazetteer_geom ON maritime_gazetteer USING gist (geom);
        """))
        dest_conn.commit()
    
    # 2. 원본 DB에서 데이터 가져오기 ('[가-힣]' 포함 데이터만)
    logger.info("Extracting data from gbenc DB...")
    with src_engine.connect() as src_conn:
        result = src_conn.execute(text("""
            SELECT attr, ST_AsText(geom) as wkt 
            FROM feature 
            WHERE attr ~ '[가-힣]'
        """))
        rows = result.fetchall()
        logger.info(f"Fetched {len(rows)} features containing Korean text.")
        
    # 3. 데이터 파싱 및 가공
    insert_data = []
    for row in rows:
        attr = row[0]
        wkt = row[1]
        
        # 파이프(|) 문자열 분석 및 추출
        parts = attr.split('|')
        
        name_kor = None
        name_eng = None
        
        # 간단한 휴리스틱: 한글이 포함된 파트는 한국어 지명, 영어가 포함된 파트는 영어 지명 (일부 오차 허용)
        for part in parts:
            if re.search(r'[가-힣]', part):
                if not name_kor or len(part) > len(name_kor): # 가장 긴 한글 단어
                    name_kor = part.strip()
            elif re.search(r'^[A-Za-z\s]+$', part) and len(part) > 3 and part.lower() not in ['eng', 'true', 'false']:
                if not name_eng or len(part) > len(name_eng):
                    name_eng = part.strip()
                    
        if name_kor:
            insert_data.append({
                "name_kor": name_kor,
                "name_eng": name_eng,
                "wkt": wkt
            })
            
    # 4. 로컬 DB에 적재
    logger.info(f"Loading {len(insert_data)} parsed records into local maritime_gazetteer...")
    with dest_engine.connect() as dest_conn:
        for i, data in enumerate(insert_data):
            dest_conn.execute(text("""
                INSERT INTO maritime_gazetteer (name_kor, name_eng, geom, source) 
                VALUES (:name_kor, :name_eng, ST_Force2D(ST_GeomFromText(:wkt, 4326)), 'gbenc')
            """), data)
            if i % 1000 == 0:
                dest_conn.commit()
        dest_conn.commit()
        
    logger.info("ETL Process Complete! 🚀")

if __name__ == "__main__":
    etl_process()
