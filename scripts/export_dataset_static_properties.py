"""Export static source attributes read-only for independent raw DBF reconciliation."""
import gzip,os
import psycopg2
from scripts.dataset_spatial_audit_io import output_argument,refuse_existing
p=output_argument();target=refuse_existing(p/'static_properties.csv.gz')
c=psycopg2.connect(os.environ['S101_DB_URL']);c.set_session(readonly=True)
with c.cursor() as q:
 q.execute("SET LOCAL statement_timeout='180s'")
 with gzip.open(target,'wt',encoding='utf8',newline='',compresslevel=1) as f:
  q.copy_expert("COPY (SELECT source_id,source_sha256,source_file,source_member,row_index,properties::text AS properties,provenance->>'encoding' AS encoding FROM serving.dataset_source_records WHERE source_member<>'CSV' ORDER BY source_sha256,source_member,row_index) TO STDOUT WITH CSV HEADER",f)
c.rollback();print('exported static attributes')
