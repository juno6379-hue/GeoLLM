"""Read-only operational spatial audit; never accesses research or holdout data."""
from scripts.dataset_spatial_audit_io import output_argument, refuse_existing
import argparse, json, os, time
from pathlib import Path
from datetime import datetime, timezone

TABLES = {'dataset_source_records':'geom','small_harbour_guide':'geom','marine_gazetteer_current':'geometry','island_gazetteer_current':'geometry','navigation_aid_current':'geometry'}

def audit(output):
    import psycopg2
    from psycopg2.extras import RealDictCursor
    output=Path(output); refuse_existing(output/'db_audit.json')
    result={'observed_at':datetime.now(timezone.utc).isoformat(),'read_only':True,'tables':{},'queries':[],'limitations':['Geometry validity is not source accuracy, currency, completeness, or approved coverage.','Source-file lineage is not a verified semantic place relation.']}
    def save(): (output/'db_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
    conn=psycopg2.connect(os.environ['S101_DB_URL'],connect_timeout=10)
    conn.set_session(readonly=True,autocommit=False)
    def query(label,sql):
        started=time.monotonic()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SET LOCAL statement_timeout='120s'")
            cur.execute(sql); rows=[dict(x) for x in cur.fetchall()]
        result['queries'].append({'label':label,'sql':sql,'elapsed_seconds':round(time.monotonic()-started,3)}); return rows
    for table,g in TABLES.items():
        base=f'serving.{table}'
        result['tables'][table]={'geometry':query(table,f'''SELECT count(*) AS rows,count({g}) AS geometry_present,
        count(*) FILTER(WHERE ST_IsEmpty({g})) AS empty,
        count(*) FILTER(WHERE NOT ST_IsValid({g})) AS invalid,
        count(*) FILTER(WHERE ST_SRID({g})<>4326) AS wrong_srid,
        count(*) FILTER(WHERE NOT ST_CoveredBy(ST_Envelope({g}),ST_MakeEnvelope(-180,-90,180,90,4326))) AS outside_world,
        count(*) FILTER(WHERE NOT ST_CoveredBy(ST_Envelope({g}),ST_MakeEnvelope(120,30,140,45,4326))) AS outside_regional_guard,
        count(*) FILTER(WHERE nullif(provenance->>'source_sha256','') IS NULL) AS missing_source_hash,
        array_agg(DISTINCT ST_SRID({g})) AS srids FROM {base}''')[0]}
        result['tables'][table]['provenance_keys']=query(table+'_keys',f'SELECT key,count(*) FROM {base},jsonb_object_keys(provenance) key GROUP BY 1 ORDER BY 1')
        if table!='dataset_source_records':
            rows=query(table+'_rows',f'SELECT source_id,name,properties,provenance,ST_AsGeoJSON({g},15) AS geojson FROM {base} ORDER BY source_id')
            (output/(table+'.json')).write_text(json.dumps(rows,ensure_ascii=False,default=str),encoding='utf-8')
        else:
            result['tables'][table]['by_source']=query('source_groups',f'''SELECT source_file,source_sha256,source_member,count(*) AS rows,min(row_index) AS min_row,max(row_index) AS max_row,count(DISTINCT row_index) AS distinct_rows,count(geom) AS geometry_present,count(*) FILTER(WHERE geometry_valid) AS marked_valid,count(*) FILTER(WHERE geom IS NOT NULL AND NOT ST_IsValid(geom)) AS invalid,count(*) FILTER(WHERE provenance->>'source_sha256' IS DISTINCT FROM source_sha256) AS hash_mismatch,count(*) FILTER(WHERE coalesce(provenance->>'row_index',provenance->>'row_number') IS NULL) AS missing_locator FROM {base} GROUP BY 1,2,3 ORDER BY 1,3''')
        save(); print(table, result['tables'][table]['geometry'],flush=True)
    result['chunks']=query('chunks',"SELECT document_type,count(*) AS rows,count(*) FILTER(WHERE page_no IS NOT NULL) AS page_locator,count(*) FILTER(WHERE source_sha256 IS NOT NULL) AS source_hash,count(*) FILTER(WHERE metadata ? 'coordinates') AS metadata_coordinates,count(*) FILTER(WHERE metadata ? 'place_id') AS metadata_place_id FROM knowledge.document_chunks GROUP BY 1 ORDER BY 1")
    result['chunk_metadata_keys']=query('chunk_keys','SELECT key,count(*) FROM knowledge.document_chunks,jsonb_object_keys(metadata) key GROUP BY 1 ORDER BY 1')
    result['chunk_examples']=query('chunk_sample',"SELECT chunk_id,document_type,metadata,source_id,source_file,page_no FROM knowledge.document_chunks WHERE document_type IN ('small_harbour_guide','coastal_pilot') ORDER BY chunk_id LIMIT 3")
    save(); conn.rollback(); conn.close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();audit(a.output)
