from scripts.dataset_spatial_audit_io import output_argument, refuse_existing
"""Read-only validation of re-parsed raw place geometry and chunk links."""
import json,os,time
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor,execute_values
OUT=output_argument();refuse_existing(OUT/'geometry_reconciliation.json')
c=psycopg2.connect(os.environ['S101_DB_URL']);c.set_session(readonly=True)
result={'read_only':True,'transform_comparisons':{},'queries':[]}
def query(label,sql):
    with c.cursor(cursor_factory=RealDictCursor) as q:
        q.execute("SET LOCAL statement_timeout='120s'");q.execute(sql);r=[dict(x) for x in q.fetchall()]
    result['queries'].append({'label':label,'sql':sql});return r
expected=json.loads((OUT/'expected_geometry.json').read_text(encoding='utf8'))
for table,col in [('small_harbour_guide','geom'),('marine_gazetteer_current','geometry'),('navigation_aid_current','geometry'),('island_gazetteer_current','geometry')]:
    rows=[x for x in expected if x['table']==table];comparisons=[]
    with c.cursor(cursor_factory=RealDictCursor) as q:
        q.execute("SET LOCAL statement_timeout='120s'")
        for start in range(0,len(rows),300):
            batch=rows[start:start+300]; values=[(r['source_id'],r['geometry'] if isinstance(r['geometry'],str) else json.dumps(r['geometry']),r['srid']) for r in batch]
            constructor='ST_GeomFromText(v.raw)' if table=='marine_gazetteer_current' else 'ST_GeomFromGeoJSON(v.raw)'
            sql=f'''WITH v(source_id,raw,srid) AS (VALUES %s), e AS (SELECT source_id,ST_Force2D(ST_Transform(ST_SetSRID({constructor},srid),4326)) AS expected FROM v)
            SELECT e.source_id,ST_Equals(e.expected,t.{col}) AS topology_equal,ST_HausdorffDistance(e.expected,t.{col}) AS max_delta_degrees FROM e JOIN serving.{table} t USING(source_id)'''
            execute_values(q,sql,values,page_size=300);comparisons.extend(dict(x) for x in q.fetchall())
    result['transform_comparisons'][table]={'expected':len(rows),'compared':len(comparisons),'topology_equal':sum(r['topology_equal'] for r in comparisons),'max_delta_degrees':max(r['max_delta_degrees'] for r in comparisons),'mismatches':[r for r in comparisons if not r['topology_equal']]}
result['quarantine']=query('quarantine', '''SELECT count(*) FILTER(WHERE geometry_valid) AS marked_valid,count(*) FILTER(WHERE geometry_valid AND (geom IS NULL OR ST_IsEmpty(geom) OR NOT ST_IsValid(geom) OR ST_SRID(geom)<>4326 OR NOT ST_CoveredBy(geom,ST_MakeEnvelope(120,30,140,45,4326)))) AS unsafe_marked_valid,count(*) FILTER(WHERE NOT geometry_valid AND source_member<>'CSV') AS excluded_static,count(*) FILTER(WHERE NOT geometry_valid AND NOT ST_IsValid(geom)) AS excluded_invalid,count(*) FILTER(WHERE NOT geometry_valid AND NOT ST_CoveredBy(ST_Envelope(geom),ST_MakeEnvelope(-180,-90,180,90,4326))) AS excluded_outside_world FROM serving.dataset_source_records''')
result['island_outside_regional']=query('islands',"SELECT source_id,name,properties,ST_AsGeoJSON(geometry)::json AS geometry FROM serving.island_gazetteer_current WHERE NOT ST_CoveredBy(geometry,ST_MakeEnvelope(120,30,140,45,4326))")
result['harbour_chunk_links']=query('harbour_links',"SELECT count(*) AS chunks,count(*) FILTER(WHERE p.source_id IS NOT NULL) AS linked,count(*) FILTER(WHERE d.source_sha256=p.provenance->>'source_sha256') AS source_hash_match,count(*) FILTER(WHERE d.section IS NOT NULL AND p.properties ? d.section) AS source_field_exists FROM knowledge.document_chunks d LEFT JOIN serving.small_harbour_guide p USING(source_id) WHERE d.document_type='small_harbour_guide'")
result['harbour_link_candidates']=query('harbour_candidates',"SELECT d.chunk_id,d.source_id AS object_id,d.source_sha256,d.section AS source_field,(d.metadata->>'row_index')::integer AS source_row_index,'describesHarbourRecord' AS predicate,'source_field_verified_retrieval_only' AS authority,'harbour_reference_point_not_entrance' AS geometry_role FROM knowledge.document_chunks d JOIN serving.small_harbour_guide p USING(source_id) WHERE d.document_type='small_harbour_guide' AND d.source_sha256=p.provenance->>'source_sha256' AND p.properties ? d.section AND strpos(d.content,p.properties->>d.section)>0")
result['indexes']=query('indexes',"SELECT indexname,indexdef FROM pg_indexes WHERE schemaname='serving' AND tablename='dataset_source_records'")
for term in ['양식장','수로']:
    with c.cursor(cursor_factory=RealDictCursor) as q:
        q.execute("SET LOCAL statement_timeout='10s'")
        sql="EXPLAIN (FORMAT JSON) SELECT source_id,source_sha256,source_file,source_member,row_index,properties,geometry_valid FROM serving.dataset_source_records WHERE ((source_member<>'CSV' AND properties::text ILIKE %s) OR source_file ILIKE %s) LIMIT 5"
        q.execute(sql,('%'+term+'%','%'+term+'%'));result['plan_'+term]=q.fetchone()
(OUT/'geometry_reconciliation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str),encoding='utf8')
c.rollback();print(json.dumps({'geometry':result['transform_comparisons'],'quarantine':result['quarantine'],'harbour':result['harbour_chunk_links'],'candidates':len(result['harbour_link_candidates'])}))
