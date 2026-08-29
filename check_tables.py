from data.database import get_enc_db
from sqlalchemy import text
db = next(get_enc_db())
res = db.execute(text("SELECT tablename FROM pg_tables WHERE tablename='maritime_gazetteer'")).fetchall()
print('GBENC contains maritime_gazetteer:', res)
