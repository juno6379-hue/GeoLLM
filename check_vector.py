import sys
sys.path.append('D:\\An_GeoLLM')
from sqlalchemy import text
from data.database import get_postgis_db, init_engines

init_engines()
db = next(get_postgis_db())
try:
    result = db.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector';")).fetchall()
    print('Extensions:', result)
    
    available = db.execute(text("SELECT name FROM pg_available_extensions WHERE name = 'vector';")).fetchall()
    print('Available:', available)
except Exception as e:
    print('Error:', e)
finally:
    db.close()
