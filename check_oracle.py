from data.database import get_oracle_db
from sqlalchemy import text
db = next(get_oracle_db())
res = db.execute(text("SELECT table_name FROM all_tables WHERE table_name LIKE '%GAZETTEER%'")).fetchall()
print('ORACLE contains gazetteer:', res)
