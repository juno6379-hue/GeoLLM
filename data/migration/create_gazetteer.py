import sys
import os
import re
from sqlalchemy import text
from tqdm import tqdm

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from data.database import get_enc_db

def extract_names(attr_str):
    """
    S-100 attr 문자열에서 지명을 추출합니다.
    (126 코드가 등장하면 그로부터 4번째 뒤의 값이 지명 텍스트임)
    """
    if not attr_str:
        return None, None
        
    parts = attr_str.split('|')
    kor_name = None
    eng_name = None
    
    for i in range(len(parts) - 4):
        if parts[i] == '126':
            name = parts[i+4]
            if not name:
                continue
            # 한글이 하나라도 포함되어 있으면 한국어 이름으로 판별
            if any(ord(c) >= 0xAC00 and ord(c) <= 0xD7A3 for c in name):
                kor_name = name
            else:
                eng_name = name
                
    return kor_name, eng_name

def create_and_populate_gazetteer():
    try:
        db = next(get_enc_db())
    except Exception as e:
        print("Database connection failed. Please ensure DB is accessible before running this script.")
        print(f"Error: {e}")
        return

    print("Connected to gbenc database.")
    
    # 1. 테이블 생성
    print("Creating maritime_gazetteer table...")
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS maritime_gazetteer (
            id SERIAL PRIMARY KEY,
            feature_seq BIGINT,
            nftc INTEGER,
            name_kor VARCHAR(255),
            name_eng VARCHAR(255),
            geom GEOMETRY(Geometry, 4326)
        );
    """))
    
    # 인덱스 생성
    db.execute(text("CREATE INDEX IF NOT EXISTS idx_maritime_gazetteer_geom ON maritime_gazetteer USING GIST (geom);"))
    db.execute(text("CREATE INDEX IF NOT EXISTS idx_maritime_gazetteer_name_kor ON maritime_gazetteer (name_kor);"))
    db.execute(text("CREATE INDEX IF NOT EXISTS idx_maritime_gazetteer_name_eng ON maritime_gazetteer (name_eng);"))
    db.commit()
    print("Table and indexes created.")
    
    # 2. 기존 데이터 비우기 (재실행 대비)
    db.execute(text("TRUNCATE TABLE maritime_gazetteer;"))
    db.commit()

    # 3. 데이터 추출 (126 속성 코드를 포함하는 feature만 조회)
    print("Fetching feature records containing names...")
    sql_fetch = text("""
        SELECT seq, nftc, attr, ST_Centroid(geom) as centroid 
        FROM feature 
        WHERE attr LIKE '%|126|%'
    """)
    rows = db.execute(sql_fetch).fetchall()
    
    print(f"Found {len(rows)} features with potential names. Extracting and inserting...")
    
    insert_sql = text("""
        INSERT INTO maritime_gazetteer (feature_seq, nftc, name_kor, name_eng, geom)
        VALUES (:seq, :nftc, :kor, :eng, :geom)
    """)
    
    insert_count = 0
    # tqdm은 없어도 동작하도록 fallback
    for row in rows:
        seq = row[0]
        nftc = row[1]
        attr = row[2]
        geom = row[3]
        
        kor, eng = extract_names(attr)
        
        if kor or eng:
            db.execute(insert_sql, {
                "seq": seq,
                "nftc": nftc,
                "kor": kor,
                "eng": eng,
                "geom": geom
            })
            insert_count += 1
            
            # 1000건마다 커밋
            if insert_count % 1000 == 0:
                db.commit()
                print(f"Inserted {insert_count} records...")
                
    db.commit()
    print(f"Migration completed successfully! Total {insert_count} gazetteer records inserted.")

if __name__ == "__main__":
    create_and_populate_gazetteer()
