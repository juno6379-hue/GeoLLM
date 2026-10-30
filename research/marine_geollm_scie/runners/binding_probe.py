"""Read-only research DB probes; vector identity is not semantic retrieval accuracy."""
import argparse
import json
from pathlib import Path
from research.marine_geollm_scie.runners.binding_snapshot import ROOT, TARGET_DATABASE, digest, psql, verify_files, write


def run(snapshot, output):
    if output.exists(): raise FileExistsError(output)
    manifest=json.loads(snapshot.read_text(encoding='utf-8'))
    if manifest['status']!='LOADED_VERIFIED' or manifest['db_identity']['database']!=TARGET_DATABASE:
        raise ValueError('Verified research snapshot required')
    verify_files(manifest,snapshot.parent)
    output.mkdir(parents=True)
    anchor=json.loads((ROOT/'data/public_place_anchors.json').read_text(encoding='utf-8'))
    # Anchor is the user-fixed public reference, not inferred from expected IDs.
    def walk(x):
        if isinstance(x,dict):
            if x.get('place_id')=='mof:dokdo:east-island' or x.get('id')=='mof:dokdo:east-island': yield x
            for v in x.values(): yield from walk(v)
        elif isinstance(x,list):
            for v in x: yield from walk(v)
    anchors=list(walk(anchor))
    if len(anchors)!=1: raise ValueError('Unique approved anchor required')
    a=anchors[0]
    lon,lat=float(a['longitude']),float(a['latitude'])
    if not (-180<=lon<=180 and -90<=lat<=90):raise ValueError('Invalid source coordinates')
    point=f'POINT({lon} {lat})'
    queries={
      'document_storage': """SELECT json_build_object('rows',count(*),'embedded',count(embedding),'missing_embedding',count(*)-count(embedding),'default_metadata_filter',count(*) FILTER(WHERE metadata @> '{"product_id":"S-101","version":"2.0.0","product_specification":"INT.IHO.S-101.2.0"}'::jsonb)) FROM knowledge.document_chunks""",
      'vector_identity': """WITH q AS (SELECT chunk_id,embedding FROM knowledge.document_chunks WHERE embedding IS NOT NULL ORDER BY chunk_id LIMIT 1) SELECT json_build_object('query_kind','STORED_VECTOR_IDENTITY_NOT_NATURAL_LANGUAGE','anchor_chunk_id',q.chunk_id,'self_cosine_distance',q.embedding <=> q.embedding,'nearest_distance',(SELECT min(d.embedding <=> q.embedding) FROM knowledge.document_chunks d WHERE d.embedding IS NOT NULL)) FROM q""",
      'document_literal_evidence': """SELECT coalesce(json_agg(t),'[]'::json) FROM (SELECT chunk_id,source_id,source_sha256,metadata->>'section' AS section,substring(content,1,500) AS excerpt FROM knowledge.document_chunks WHERE content ILIKE '%Wreck%' AND metadata @> '{"product_id":"S-101","version":"2.0.0"}'::jsonb ORDER BY chunk_id LIMIT 3) t""",
      'q4_source_objects': f"""SELECT coalesce(json_agg(t),'[]'::json) FROM (SELECT source_id,name,properties,provenance,round(ST_Distance(geometry::geography,ST_GeomFromText('{point}',4326)::geography)::numeric,3) AS distance_m FROM serving.marine_gazetteer_current WHERE ST_DWithin(geometry::geography,ST_GeomFromText('{point}',4326)::geography,5000) ORDER BY source_id) t""",
      'spatial_coverage': """SELECT json_build_object('extent',ST_Extent(geometry)::text,'wreck_rows',count(*) FILTER(WHERE feature_type_name='Wreck'),'interpretation','BOUNDED_BUSAN_SUBSET_NOT_DOKDO_COVERAGE') FROM projection.s101_feature_current"""
    }
    observations=[]
    for name,query in queries.items():
        sql="BEGIN TRANSACTION READ ONLY; SET LOCAL statement_timeout='60s';\n"+query+';\nROLLBACK;'
        (output/(name+'.sql')).write_text(sql,encoding='utf-8')
        value=json.loads(psql(sql,TARGET_DATABASE))
        write(output/(name+'.json'),value)
        observations.append({'probe':name,'sql_sha256':digest(output/(name+'.sql')),'result_sha256':digest(output/(name+'.json'))})
    write(output/'manifest.json',{'snapshot_manifest_sha256':digest(snapshot),'observations':observations,
        'database':TARGET_DATABASE,'database_writes':False,'model_calls':0,'semantic_accuracy':None,
        'scope':'REAL_DATA_BINDING_AND_VECTOR_OPERATOR_PROBE_NOT_FULL_PIPELINE'})
    print(json.dumps({'probes':len(observations),'output':str(output)}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--snapshot',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.snapshot,a.output)
