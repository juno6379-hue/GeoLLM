from scripts.dataset_spatial_audit_io import output_argument, refuse_existing
import gzip,os,json
from pathlib import Path
import psycopg2
p=output_argument();refuse_existing(p/'csv_row_hashes.csv.gz');c=psycopg2.connect(os.environ['S101_DB_URL']);c.set_session(readonly=True)
with c.cursor() as q:
 q.execute("SET LOCAL statement_timeout='180s'")
 with gzip.open(p/'csv_row_hashes.csv.gz','wt',encoding='utf8',newline='',compresslevel=1) as f:
  q.copy_expert("COPY (SELECT source_id,source_sha256,source_file,row_index,md5((properties->'header')::text) AS header_hash,md5((properties->'values')::text) AS values_hash,provenance->>'encoding' AS encoding,provenance->>'row_number' AS row_number,geom IS NULL AS no_geometry FROM serving.dataset_source_records WHERE source_member='CSV' ORDER BY source_sha256,row_index) TO STDOUT WITH CSV HEADER",f)
c.rollback();print('exported CSV hashes')
