from scripts.dataset_spatial_audit_io import output_argument, refuse_existing
import os,json,time
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor
p=output_argument();refuse_existing(p/'search_probe.json');out={};c=psycopg2.connect(os.environ['S101_DB_URL']);c.set_session(readonly=True)
with c.cursor(cursor_factory=RealDictCursor) as q:
 q.execute("SET LOCAL statement_timeout='30s'")
 q.execute("SELECT d.chunk_id,d.section,d.content,p.properties->>d.section AS source_text FROM knowledge.document_chunks d JOIN serving.small_harbour_guide p USING(source_id) WHERE d.document_type='small_harbour_guide' AND strpos(d.content,p.properties->>d.section)=0")
 out['literal_failures']=[dict(r) for r in q.fetchall()]
for term in ['양식장','수로']:
 out[term]={}
 for label,sql in [('original',"SELECT source_id FROM serving.dataset_source_records WHERE ((source_member<>'CSV' AND properties::text ILIKE %s) OR source_file ILIKE %s) LIMIT 5"),('filename_first',"SELECT source_id FROM serving.dataset_source_records WHERE source_file ILIKE %s LIMIT 5")]:
  try:
   with c.cursor() as q:
    q.execute("SET LOCAL statement_timeout='3s'");start=time.monotonic();q.execute(sql,('%'+term+'%','%'+term+'%') if label=='original' else ('%'+term+'%',));ids=[r[0] for r in q.fetchall()];out[term][label]={'elapsed_seconds':time.monotonic()-start,'ids':ids}
   c.rollback()
  except psycopg2.Error as e:out[term][label]={'error_code':e.pgcode,'elapsed_seconds':time.monotonic()-start};c.rollback()
(p/'search_probe.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in out.items() if k!='literal_failures'}));print('literal fail count',len(out['literal_failures']))
