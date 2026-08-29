import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data.database import get_enc_db
from sqlalchemy import text
import pandas as pd

try:
    db = next(get_enc_db())
    
    # 1. 테이블 목록 조회
    sql_tables = text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    tables = [row[0] for row in db.execute(sql_tables).fetchall()]
    print("=== Tables in gbenc ===")
    print(tables)
    
    # 2. 'feature' 테이블의 컬럼 조회
    if 'feature' in tables:
        print("\n=== Columns in 'feature' table ===")
        sql_cols = text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'feature'
        """)
        cols = db.execute(sql_cols).fetchall()
        for c in cols:
            print(f"- {c[0]}: {c[1]}")
            
    # 3. 객체 이름(지명)과 관련된 속성 탐색
    # feature_name, text, national_name 등이 있는지 확인하기 위해, 
    # feature의 속성이 별도 테이블에 저장되는 구조인지(S-101의 feature_name, information 등)
    if 'feature_name' in tables:
        print("\n=== Columns in 'feature_name' table ===")
        sql_cols2 = text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'feature_name'
        """)
        cols2 = db.execute(sql_cols2).fetchall()
        for c in cols2:
            print(f"- {c[0]}: {c[1]}")
            
except Exception as e:
    import traceback
    traceback.print_exc()
