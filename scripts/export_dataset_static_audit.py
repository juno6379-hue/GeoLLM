from scripts.dataset_spatial_audit_io import output_argument, refuse_existing
import gzip,os
from pathlib import Path
import psycopg2
p=output_argument();refuse_existing(p/'static_geometry_wkb.csv.gz');c=psycopg2.connect(os.environ['S101_DB_URL']);c.set_session(readonly=True)
with c.cursor() as q:
 q.execute("SET LOCAL statement_timeout='180s'")
 with gzip.open(p/'static_geometry_wkb.csv.gz','wt',encoding='utf8',newline='',compresslevel=1) as f:
  q.copy_expert("COPY (SELECT source_id,source_sha256,source_file,source_member,row_index,encode(ST_AsBinary(geom,'NDR'),'hex') AS wkb,geometry_valid FROM serving.dataset_source_records WHERE source_member<>'CSV' ORDER BY source_sha256,source_member,row_index) TO STDOUT WITH CSV HEADER",f)
c.rollback();print('exported')
