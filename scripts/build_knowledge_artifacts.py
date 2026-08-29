"""Generate v2 dictionaries, registries, RAG manifests and index SQL."""
import csv, hashlib, json, zipfile
from datetime import datetime, timezone
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'; DATASET=ROOT/'Dataset'; OUT=ROOT/'outputs'
def wy(path,value):
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(yaml.safe_dump(value,allow_unicode=True,sort_keys=False),encoding='utf-8')
def build_dictionaries():
    cat=json.loads((DATA/'s101_catalogue.json').read_text(encoding='utf-8'))
    features={x['name']:{k:x.get(k,[]) for k in ('nftc','name_kr','description','primitives','codeinformation','rulefunctions')} for x in cat}
    wy(DATA/'s101_feature_dictionary_v2.yaml',{'version':'2.0','source':'S-101 Feature Catalogue','s101_features':features})
    attrs=[{'feature':x['name'],'name':a,'type':'codeinformation','provenance':'s101_catalogue'} for x in cat for a in x.get('codeinformation',[])]
    wy(DATA/'s101_attribute_dictionary_v2.yaml',{'version':'2.0','attributes':{'common':[{'name':'nftc','type':'integer','required':True},{'name':'geom','type':'geometry','srid':4326,'required':True},{'name':'source_id','type':'string','required':True}],'feature_attributes':attrs}})
    wy(DATA/'gbenc_feature_dictionary_v2.yaml',{'version':'2.0','source':'S100_dev_postgis','table':'public.feature','columns':[{'name':'seq','type':'integer','role':'feature_id'},{'name':'nftc','type':'integer','role':'feature_type_code'},{'name':'geom','type':'geometry','srid':4326}],'catalogue_authority':'s101_feature_dictionary_v2.yaml','provenance_required':True})
    wy(DATA/'marine_term_dictionary.yaml',{'version':'2.0','terms':{'위험객체':{'canonical_id':'navigation_hazard_object','aliases':['hazard'],'context':'navigation_safety'},'침선':{'canonical_id':'Wreck','aliases':['wreck'],'nftc':159},'장애물':{'canonical_id':'Obstruction','aliases':['obstruction'],'nftc':86},'수중암초':{'canonical_id':'UnderwaterAwashRock','aliases':['rock'],'nftc':153}}})
    wy(DATA/'domestic_marine_layer_dictionary.yaml',{'version':'2.0','source_types':['domestic_static_spatial_layer','marine_gazetteer'],'standard':{'crs':'EPSG:4326','required_columns':['source_id','layer_id','geom','dataset_version','provenance'],'geometry_validation':['is_valid','has_srid','non_empty']}})
    wy(DATA/'traffic_data_dictionary.yaml',{'version':'2.0','layer_type':'DynamicTrafficLayer','sources':{'ais':{'classification':'dynamic_traffic_ais','required_columns':['mmsi','observed_at','geom']},'vpass':{'classification':'dynamic_traffic_vpass','required_columns':['vessel_id','observed_at','geom']}},'common_columns':['source_id','observed_at','ingested_at','geom','provenance']})
    wy(DATA/'accident_dictionary.yaml',{'version':'2.0','source_type':'accident_data','required_columns':['source_id','event_id','occurred_at','location','severity','provenance'],'relations':['related_s101_feature','related_dynamic_traffic_layer','risk_profile']})
def build_registries():
    wy(DATA/'s100_product_registry.yaml',{'version':'2.0','products':{p:{'version':v,'source_type':c} for p,v,c in [('S-100','5.2.0','standard_s100'),('S-101','2.0.0','standard_s101'),('S-104','2.0.0','standard_s104'),('S-111','2.0.0','standard_s111'),('S-124','2.0.0','standard_s124'),('S-158','1.x','validation_s158')]}})
    wy(DATA/'derived_concept_registry_v2.yaml',{'version':'2.0','derived_concepts':{'navigation_hazard_object':{'aliases':['위험객체','hazard'],'default_context':'navigation_safety','analysis_type':'feature_search_by_radius','primary_agent':'Spatial Analysis Agent','required_tools':['geocoder.resolve_location','gbenc.s101_feature_search_by_radius','postgis.dwithin'],'required_data':['GBENC_S101_feature','GBENC_codeinformation','s101_feature_dictionary','marine_term_dictionary','location_gazetteer'],'target_features':['Wreck','Obstruction','UnderwaterAwashRock','BuoyIsolatedDanger','BeaconIsolatedDanger']},'dynamic_traffic':{'aliases':['AIS','V-PASS','통항량','항적'],'default_context':'maritime_traffic','primary_agent':'AIS/V-PASS Analysis Agent','required_data':['DynamicTrafficLayer','traffic_data_dictionary']}}})
    wy(DATA/'spatial_layer_registry.yaml',{'version':'2.0','layers':{'GBENC_S101_feature':{'zone':'serving','physical_table':'public.feature','geometry_column':'geom','code_column':'nftc','srid':4326,'database':'S100_dev_postgis'},'marine_gazetteer':{'zone':'serving','physical_table':'public.maritime_gazetteer','geometry_column':'geom','srid':4326}}})
    wy(DATA/'traffic_layer_registry.yaml',{'version':'2.0','layers':{'AIS':{'layer_type':'DynamicTrafficLayer','source_type':'dynamic_traffic_ais','temporal_column':'observed_at','geometry_column':'geom','srid':4326},'V-PASS':{'layer_type':'DynamicTrafficLayer','source_type':'dynamic_traffic_vpass','temporal_column':'observed_at','geometry_column':'geom','srid':4326}}})
    wy(DATA/'data_registry.yaml',{'version':'2.0','datasets':{'GBENC_S101_feature':{'zone':'serving','source':'s100_dev_postgis.public.feature','status':'pending_restore'},'GBENC_codeinformation':{'zone':'serving','source':'s100_dev_postgis.public.codeinformation','status':'pending_restore'},'s101_feature_dictionary':{'zone':'knowledge','path':'data/s101_feature_dictionary_v2.yaml'},'marine_term_dictionary':{'zone':'knowledge','path':'data/marine_term_dictionary.yaml'},'location_gazetteer':{'zone':'serving','source':'public.maritime_gazetteer','status':'pending_restore'},'domestic_marine_layers':{'zone':'standardized','registry':'data/spatial_layer_registry.yaml'},'DynamicTrafficLayer':{'zone':'serving','registry':'data/traffic_layer_registry.yaml'},'accident_data':{'zone':'standardized','dictionary':'data/accident_dictionary.yaml'}}})
    wy(DATA/'tool_registry.yaml',{'version':'2.0','tools':{'geocoder.resolve_location':{'kind':'geocoding','provenance_required':True},'gbenc.s101_feature_search_by_radius':{'kind':'spatial_query','template':'feature_search_by_radius'},'postgis.dwithin':{'kind':'spatial_function','function':'ST_DWithin'},'rag.graph_scoped_retrieve':{'kind':'graph_rag'},'traffic.dynamic_layer_search':{'kind':'temporal_spatial_query'}}})
    wy(DATA/'query_template_registry.yaml',{'version':'2.0','templates':{'feature_search_by_radius':{'allowed_layers':['GBENC_S101_feature'],'required_parameters':['base_geometry','distance_m','nftc_codes'],'executor':'postgis.dwithin'},'traffic_search_by_time_space':{'allowed_layers':['AIS','V-PASS'],'required_parameters':['time_range','geometry'],'executor':'traffic.dynamic_layer_search'},'graph_scoped_rag':{'required_parameters':['entity_ids','query'],'executor':'rag.graph_scoped_retrieve'}}})
    wy(DATA/'validation_rule_registry.yaml',{'version':'2.0','rules':{'source_provenance_required':{'severity':'error','applies_to':['all_outputs']},'spatial_srid_4326':{'severity':'error','applies_to':['spatial_layers']},'no_synthetic_features':{'severity':'error','applies_to':['spatial_query_results']},'rag_evidence_required':{'severity':'error','applies_to':['rag_answers']},'dynamic_observed_at_required':{'severity':'error','applies_to':['DynamicTrafficLayer']}}})
def decode_text_best(path):
    raw=path.read_bytes(); candidates=[]
    for encoding in ('utf-8-sig','cp949','euc-kr','utf-8'):
        try: value=raw.decode(encoding)
        except UnicodeDecodeError: continue
        replacements=value.count('\ufffd')
        hangul=sum(1 for ch in value if 0xAC00 <= ord(ch) <= 0xD7A3)
        candidates.append((hangul-replacements*10000, value))
    return max(candidates, key=lambda item:item[0])[1] if candidates else raw.decode('utf-8',errors='replace')
def preview(path):
    try:
        if path.suffix.lower()=='.csv': return 'text_preview',decode_text_best(path)[:4000]
        if path.suffix.lower()=='.zip':
            with zipfile.ZipFile(path) as z: return 'archive_manifest','Archive members:\n'+'\n'.join(z.namelist()[:100])
    except Exception as e: return 'extraction_failed',str(e)
    return 'metadata_only','Document body extraction pending staging parser.'
def build_rag():
    with (OUT/'inventories/dataset_inventory.csv').open(encoding='utf-8-sig',newline='') as f: sources=list(csv.DictReader(f))
    groups={'s100_product_spec_chunks.jsonl':{'standard_s100'},'s101_dceg_chunks.jsonl':{'standard_s101','feature_catalogue','portrayal_catalogue'},'s104_chunks.jsonl':{'standard_s104'},'s111_chunks.jsonl':{'standard_s111'},'s124_chunks.jsonl':{'standard_s124'},'s158_validation_chunks.jsonl':{'validation_s158'},'law_chunks.jsonl':{'law_rag'},'accident_chunks.jsonl':{'accident_data'}}
    d=OUT/'rag'; d.mkdir(parents=True,exist_ok=True); manifest={'version':'2.0','generated_at':datetime.now(timezone.utc).isoformat(),'embedding_status':'pending','files':{}}
    for filename,kinds in groups.items():
        rows=[]
        for s in sources:
            if s['classification'] not in kinds: continue
            status,text=preview(DATASET/Path(s['relative_path']))
            rows.append({'chunk_id':hashlib.sha256(f"{s['source_id']}:0".encode()).hexdigest()[:24],'text':text,'metadata':{'source_id':s['source_id'],'source_path':s['relative_path'],'source_type':s['classification'],'source_sha256':s['sha256'],'chunk_index':0,'extraction_status':status,'provenance':{'source_path':s['relative_path'],'source_sha256':s['sha256']}}})
        (d/filename).write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows),encoding='utf-8'); manifest['files'][filename]={'chunk_count':len(rows),'embedding_status':'pending','source_types':sorted(kinds)}
    (d/'rag_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def build_indexes():
    p=OUT/'sql/create_indexes.sql'; p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text('''-- An_GeoLLM v2.0 serving indexes. Run after verified DB restore.\nCREATE EXTENSION IF NOT EXISTS postgis;\n-- CREATE EXTENSION IF NOT EXISTS vector; -- requires pgvector image\nCREATE INDEX IF NOT EXISTS idx_feature_geom_gist ON public.feature USING GIST (geom);\nCREATE INDEX IF NOT EXISTS idx_feature_nftc ON public.feature (nftc);\nCREATE INDEX IF NOT EXISTS idx_maritime_gazetteer_geom_gist ON public.maritime_gazetteer USING GIST (geom);\nCREATE SCHEMA IF NOT EXISTS serving;\nCREATE TABLE IF NOT EXISTS serving.dynamic_traffic_layer (source_id text NOT NULL, observed_at timestamptz NOT NULL, ingested_at timestamptz NOT NULL DEFAULT now(), layer_source text NOT NULL, properties jsonb NOT NULL DEFAULT '{}'::jsonb, geom geometry(Geometry,4326) NOT NULL, provenance jsonb NOT NULL);\nCREATE INDEX IF NOT EXISTS idx_dynamic_traffic_geom_gist ON serving.dynamic_traffic_layer USING GIST (geom);\nCREATE INDEX IF NOT EXISTS idx_dynamic_traffic_observed_at ON serving.dynamic_traffic_layer (observed_at);\nCREATE INDEX IF NOT EXISTS idx_dynamic_traffic_source_time ON serving.dynamic_traffic_layer (layer_source, observed_at);\nCREATE SCHEMA IF NOT EXISTS knowledge;\nCREATE TABLE IF NOT EXISTS knowledge.document_chunks (chunk_id text PRIMARY KEY, content text NOT NULL, embedding vector, metadata jsonb NOT NULL, source_id text NOT NULL, source_sha256 text NOT NULL, created_at timestamptz NOT NULL DEFAULT now());\nCREATE INDEX IF NOT EXISTS idx_document_chunks_source ON knowledge.document_chunks (source_id);\nCREATE INDEX IF NOT EXISTS idx_document_chunks_metadata ON knowledge.document_chunks USING GIN (metadata);\n-- CREATE INDEX idx_document_chunks_embedding ON knowledge.document_chunks USING hnsw (embedding vector_cosine_ops);\nCREATE TABLE IF NOT EXISTS knowledge.kg_nodes (node_id text PRIMARY KEY, node_type text NOT NULL, canonical_name text NOT NULL, properties jsonb NOT NULL DEFAULT '{}'::jsonb, provenance jsonb NOT NULL);\nCREATE TABLE IF NOT EXISTS knowledge.kg_edges (edge_id text PRIMARY KEY, subject_id text NOT NULL, predicate text NOT NULL, object_id text NOT NULL, properties jsonb NOT NULL DEFAULT '{}'::jsonb, provenance jsonb NOT NULL);\nCREATE INDEX IF NOT EXISTS idx_kg_nodes_type ON knowledge.kg_nodes (node_type);\nCREATE INDEX IF NOT EXISTS idx_kg_nodes_name ON knowledge.kg_nodes (canonical_name);\nCREATE INDEX IF NOT EXISTS idx_kg_nodes_properties ON knowledge.kg_nodes USING GIN (properties);\nCREATE INDEX IF NOT EXISTS idx_kg_edges_subject ON knowledge.kg_edges (subject_id);\nCREATE INDEX IF NOT EXISTS idx_kg_edges_object ON knowledge.kg_edges (object_id);\nCREATE INDEX IF NOT EXISTS idx_kg_edges_predicate ON knowledge.kg_edges (predicate);\n''',encoding='utf-8')
def build_reports():
    manifest=json.loads((OUT/'rag/rag_manifest.json').read_text(encoding='utf-8'))
    total_chunks=sum(x['chunk_count'] for x in manifest['files'].values())
    (OUT/'rag/embedding_metadata.json').write_text(json.dumps({
        'version':'2.0','status':'pending',
        'reason':'pgvector extension is not installed in the current Docker image',
        'table':'knowledge.document_chunks','column':'embedding','model':None,'dimension':None,
        'index_type':'hnsw','distance':'vector_cosine_ops',
        'source_manifest':'outputs/rag/rag_manifest.json',
        'provenance':{'generator':'scripts/build_knowledge_artifacts.py','generated_at':datetime.now(timezone.utc).isoformat()}
    },ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (OUT/'reports/05_dictionary_registry_report.md').write_text('''# Dictionary / Registry 생성 보고서

## 처리 결과

- S-100/S-101 v2.0 기준 Dictionary 7종과 Registry 8종을 `data/`에 생성했다.
- S-101 Feature/Attribute Dictionary는 `data/s101_catalogue.json`을 기준으로 생성했다.
- `feature_search_by_radius`는 `Spatial Analysis Agent`로 매핑했다.
- `navigation_hazard_object`는 `navigation_safety` context와 공간검색 도구·GBENC/S-101 자료 요구사항을 가진 Derived Concept로 등록했다.
- 등록 항목은 원천 파일 경로 또는 provenance 요구사항을 포함한다.

## 인덱스 산출물

`outputs/sql/create_indexes.sql`에 PostGIS feature/gazetteer GIST, DynamicTrafficLayer 공간·시간 인덱스, pgvector 문서 테이블/메타데이터 인덱스, KG node/edge 인덱스를 정의했다.

현재 Docker 이미지에는 pgvector extension이 없어 vector extension 활성화와 HNSW 인덱스 실행은 대기 상태다. 정상 v2 dump 복원 및 pgvector 지원 이미지 준비 후 SQL을 실행한다.
''',encoding='utf-8')
    (OUT/'reports/06_rag_indexing_report.md').write_text(f'''# RAG / Indexing 생성 보고서

## RAG 결과

- RAG 파일: {len(manifest['files'])}종
- 생성 chunk: {total_chunks}개
- 각 chunk에 `source_id`, `source_path`, `source_type`, `source_sha256`, `chunk_index`, `extraction_status`를 포함했다.
- manifest: `outputs/rag/rag_manifest.json`
- embedding metadata: `outputs/rag/embedding_metadata.json`

현재 PDF/DOCX/XML 및 일부 바이너리 자료는 `metadata_only`, ZIP은 `archive_manifest`로 기록했다. staging parser 완성 후 본문 chunk를 재생성해야 하므로 현재 산출물은 소스 추적 가능한 인덱싱 입력 manifest이며 임베딩 완료본은 아니다.

## DB 인덱스 상태

PostGIS GIST, traffic layer spatial/time, KG node/edge 인덱스 SQL을 생성했다. 정상 `_s100_dev_20260827.dump`가 확보되지 않아 v2 DB에는 아직 restore 및 SQL 실행을 하지 않았다.
''',encoding='utf-8')

def main(): build_dictionaries(); build_registries(); build_rag(); build_indexes(); build_reports(); print('knowledge_artifacts_generated')
if __name__=='__main__': main()
