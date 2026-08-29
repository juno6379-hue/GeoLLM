import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data.database import get_enc_db
from sqlalchemy import text

db = next(get_enc_db())
sql = text("""
    SELECT seq as id, ST_AsGeoJSON(geom) as geojson, 'PUBLIC' as clearance_level 
    FROM feature 
    WHERE ST_DWithin(ST_SetSRID(geom, 4326), ST_SetSRID(ST_GeomFromText('POINT(127.7 34.7)'), 4326), 500.0) 
    AND nftc IN (84)
""")
try:
    res = db.execute(sql).mappings().all()
    print("SUCCESS, count:", len(res))
except Exception as e:
    import traceback
    traceback.print_exc()
    if len(e.args) > 0:
        raw_msg = e.args[0]
        if isinstance(raw_msg, bytes):
            print("Raw bytes:", raw_msg)
        else:
            print("Error message type:", type(raw_msg), repr(raw_msg))
