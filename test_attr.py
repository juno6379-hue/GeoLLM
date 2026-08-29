import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data.database import get_enc_db
from sqlalchemy import text
import json

db = next(get_enc_db())
sql = text("SELECT attr FROM feature WHERE attr LIKE '%여수%' OR attr LIKE '%부산%' LIMIT 10")
try:
    rows = db.execute(sql).fetchall()
    print("Found", len(rows), "rows with place names.")
    for r in rows:
        print(r[0])
except Exception as e:
    print(e)
