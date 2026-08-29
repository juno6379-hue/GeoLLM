"""Build a provenance-aware bootstrap Marine Spatial Knowledge Graph."""
import csv, hashlib, json, re
from pathlib import Path
from xml.etree import ElementTree as ET
import yaml

ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'; OUT=ROOT/'outputs/graph'
OUT.mkdir(parents=True,exist_ok=True)
nodes={}; edges=[]

def slug(value): return re.sub(r'[^a-zA-Z0-9_-]+','_',str(value)).strip('_').lower() or 'unknown'
def nid(kind,value): return f'{slug(kind)}:{slug(value)}'
def add_node(node_kind,value,**props):
    key=nid(node_kind,value); nodes.setdefault(key,{'id':key,'node_type':node_kind,'name':str(value),'properties':{},'provenance':{}})
    nodes[key]['properties'].update({k:v for k,v in props.items() if v is not None})
    if props.get('provenance'): nodes[key]['provenance'].update(props['provenance'])
    return key
def add_edge(a,rel,b,**props):
    if not a or not b: return
    edge_id=hashlib.sha256(f'{a}|{rel}|{b}'.encode()).hexdigest()[:24]
    if not any(x['id']==edge_id for x in edges):
        edges.append({'id':edge_id,'subject_id':a,'predicate':rel,'object_id':b,'properties':{k:v for k,v in props.items() if k!='provenance'},'provenance':props.get('provenance',{})})
def load(name):
    return yaml.safe_load((DATA/name).read_text(encoding='utf-8')) or {}
def source(path): return {'source_path':str(path).replace('\\','/'),'generator':'scripts/build_marine_kg.py'}

def build():
    products=load('s100_product_registry.yaml').get('products',{})
    for product,meta in products.items():
        p=add_node('Product',product,version=meta.get('version'),source_type=meta.get('source_type'),provenance=source('data/s100_product_registry.yaml'))
        for catalogue,kind in [('FeatureCatalogue','feature_catalogue'),('PortrayalCatalogue','portrayal_catalogue'),('DCEG','dceg')]:
            files=[x for x in (ROOT/'outputs/inventories/dataset_inventory.csv').read_text(encoding='utf-8-sig').splitlines() if kind in x.lower()]
            for f in files[:20]: add_edge(p,{'FeatureCatalogue':'hasFeatureCatalogue','PortrayalCatalogue':'portrayedBy','DCEG':'hasDCEG'}[catalogue],add_node(catalogue,Path(f.split(',')[1] if ',' in f else f).name,provenance=source('outputs/inventories/dataset_inventory.csv')))

    parsed=json.loads((DATA/'s101_feature_catalogue_v2_parsed.json').read_text(encoding='utf-8'))
    catalogue=[{'name': x.get('code'), 'catalogue_name': x.get('name'),
                'nftc': None, 'description': x.get('definition'),
                'primitives': x.get('permitted_primitives', []),
                'codeinformation': [b.get('ref') for b in x.get('bindings', [])]}
               for x in parsed.get('features', [])]
    catalogue_source='data/s101_feature_catalogue_v2_parsed.json'
    fc=add_node('FeatureCatalogue','S-101 Feature Catalogue v2.0',version='2.0',
                feature_count=len(catalogue), attribute_count=len(parsed.get('attributes', [])),
                provenance=source(catalogue_source))
    for item in catalogue:
        f=add_node('Feature',f"{item.get('name')}:{item.get('nftc') or item.get('name')}",nftc=item.get('nftc'),canonical_name=item.get('name'),catalogue_name=item.get('catalogue_name'),description=item.get('description'),provenance=source(catalogue_source))
        add_edge(fc,'definesFeature',f,provenance=source(catalogue_source))
        for primitive in item.get('primitives',[]):
            g=add_node('GeometryType',primitive,provenance=source(catalogue_source)); add_edge(f,'hasGeometryType',g,provenance=source(catalogue_source))
        for attr in item.get('codeinformation',[]):
            a=add_node('Attribute',attr,feature=item.get('name'),provenance=source(catalogue_source)); add_edge(f,'hasAttribute',a,provenance=source(catalogue_source))

    terms=load('marine_term_dictionary.yaml').get('terms',{})
    for term,meta in terms.items():
        t=add_node('MarineTerm',meta.get('canonical_id',term),aliases=meta.get('aliases'),provenance=source('data/marine_term_dictionary.yaml'))
        if meta.get('canonical_id') in [x.get('name') for x in catalogue]: add_edge(t,'mapsToFeature',nid('Feature',f"{meta['canonical_id']}:{meta['canonical_id']}"),provenance=source('data/marine_term_dictionary.yaml'))
        for alias in meta.get('aliases',[]):
            a=add_node('MarineTerm',alias,alias_of=meta.get('canonical_id'),provenance=source('data/marine_term_dictionary.yaml')); add_edge(a,'aliasOf',t,provenance=source('data/marine_term_dictionary.yaml'))
    concepts=load('derived_concept_registry_v2.yaml').get('derived_concepts',{})
    for name,meta in concepts.items():
        c=add_node('DerivedConcept',name,default_context=meta.get('default_context'),analysis_type=meta.get('analysis_type'),provenance=source('data/derived_concept_registry_v2.yaml'))
        for feature in meta.get('target_features',[]): add_edge(c,'includesFeature',nid('Feature',f'{feature}:{next((x["nftc"] or x["name"] for x in catalogue if x["name"]==feature),feature)}'),provenance=source('data/derived_concept_registry_v2.yaml'))
        for tool in meta.get('required_tools',[]): add_edge(c,'requiresTool',nid('Tool',tool),provenance=source('data/derived_concept_registry_v2.yaml'))
        for data in meta.get('required_data',[]): add_edge(c,'requiresData',nid('DataLayer',data),provenance=source('data/derived_concept_registry_v2.yaml'))
        if meta.get('primary_agent'): add_edge(c,'requiresAgent',nid('Agent',meta['primary_agent']),provenance=source('data/derived_concept_registry_v2.yaml'))

    for name,meta in load('spatial_layer_registry.yaml').get('layers',{}).items():
        l=add_node('DataLayer',name,**meta,provenance=source('data/spatial_layer_registry.yaml')); add_edge(l,'storedIn',add_node('DataLayer',meta.get('physical_table','serving')),provenance=source('data/spatial_layer_registry.yaml'))
    for name,meta in load('traffic_layer_registry.yaml').get('layers',{}).items(): add_node('DynamicTrafficLayer',name,**meta,provenance=source('data/traffic_layer_registry.yaml'))
    for name,meta in load('data_registry.yaml').get('datasets',{}).items(): add_node('DataLayer',name,**meta,provenance=source('data/data_registry.yaml'))
    gbenc=nid('DataLayer','GBENC_S101_feature')
    portrayal=add_node('PortrayalCatalogue','S-101 Portrayal Catalogue v2.0',provenance=source('outputs/inventories/dataset_inventory.csv'))
    for item in catalogue:
        feature=nid('Feature',f"{item.get('name')}:{item.get('nftc') or item.get('name')}"); add_edge(feature,'encodedBy',gbenc,provenance=source('data/spatial_layer_registry.yaml')); add_edge(feature,'portrayedBy',portrayal,provenance=source(catalogue_source))
    hazard=nid('DerivedConcept','navigation_hazard_object')
    add_edge(nid('MarineTerm','navigation_hazard_object'),'mapsToConcept',hazard,provenance=source('data/derived_concept_registry_v2.yaml'))
    add_edge(hazard,'usesLayer',gbenc,provenance=source('data/derived_concept_registry_v2.yaml'))
    traffic=nid('DerivedConcept','dynamic_traffic')
    for layer in load('traffic_layer_registry.yaml').get('layers',{}): add_edge(traffic,'usesDynamicLayer',nid('DynamicTrafficLayer',layer),provenance=source('data/derived_concept_registry_v2.yaml'))
    for name,meta in load('tool_registry.yaml').get('tools',{}).items(): add_node('Tool',name,**meta,provenance=source('data/tool_registry.yaml'))
    for name,meta in load('query_template_registry.yaml').get('templates',{}).items():
        q=add_node('QueryTemplate',name,**meta,provenance=source('data/query_template_registry.yaml'))
        if meta.get('executor'): add_edge(nid('Tool',meta['executor']), 'executesQueryTemplate', q, provenance=source('data/query_template_registry.yaml'))
    for name,meta in load('validation_rule_registry.yaml').get('rules',{}).items(): add_node('ValidationRule',name,**meta,provenance=source('data/validation_rule_registry.yaml'))
    for name in ['search_buffer','hazard_objects']:
        add_node('MapLayerStyle',name,renderer='Map Adapter',provenance=source('data/spatial_layer_registry.yaml'))
    for agent in ['Data Discovery Agent','Spatial Analysis Agent','Standard/RAG Agent','AIS/V-PASS Analysis Agent','Accident/Risk Agent','Validation Agent','Map/Report Agent']:
        add_node('Agent',agent,provenance=source('data/agent_capability_registry.yaml'))
    add_edge(nid('Agent','Spatial Analysis Agent'),'canExecute',nid('QueryTemplate','feature_search_by_radius'),provenance=source('data/agent_capability_registry.yaml'))
    add_edge(nid('Agent','AIS/V-PASS Analysis Agent'),'canExecute',nid('QueryTemplate','traffic_search_by_time_space'),provenance=source('data/agent_capability_registry.yaml'))
    add_edge(nid('Agent','Standard/RAG Agent'),'canExecute',nid('QueryTemplate','graph_scoped_rag'),provenance=source('data/agent_capability_registry.yaml'))

    inv=list(csv.DictReader((OUT.parent/'inventories/dataset_inventory.csv').open(encoding='utf-8-sig',newline='')))
    for row in inv:
        cls=row['classification']; path=row['relative_path']; base=Path(path).name
        if cls in {'standard_s100','standard_s101','standard_s104','standard_s111','standard_s124'}: add_node('StandardDocument',base,classification=cls,provenance=source(path))
        elif cls=='law_rag': add_node('LawDocument',base,classification=cls,provenance=source(path))
        elif cls=='accident_data':
            e=add_node('AccidentEvent',base,classification=cls,provenance=source(path)); add_edge(e,'hasType',add_node('AccidentType','accident_data',provenance=source('data/accident_dictionary.yaml')),provenance=source(path))
        elif cls=='marine_gazetteer': add_node('Place',base,classification=cls,provenance=source(path))
    for filename in json.loads((ROOT/'outputs/rag/rag_manifest.json').read_text(encoding='utf-8'))['files']:
        for line in (ROOT/'outputs/rag'/filename).read_text(encoding='utf-8').splitlines():
            if not line: continue
            row=json.loads(line); m=row['metadata']; ch=add_node('DocumentChunk',row['chunk_id'],source_id=m['source_id'],extraction_status=m['extraction_status'],provenance=m['provenance'])
            parent=add_node('StandardDocument' if m['source_type'].startswith('standard_') else ('LawDocument' if m['source_type']=='law_rag' else 'AccidentEvent' if m['source_type']=='accident_data' else 'DocumentChunk'),m['source_path'],provenance=m['provenance'])
            if parent!=ch: add_edge(parent,'supportsFeature' if m['source_type'].startswith('standard_') else 'relatedToConcept',ch,provenance=m['provenance'])

def write():
    with (OUT/'kg_nodes_v2.jsonl').open('w',encoding='utf-8') as f:
        for x in nodes.values(): f.write(json.dumps(x,ensure_ascii=False)+'\n')
    with (OUT/'kg_edges_v2.jsonl').open('w',encoding='utf-8') as f:
        for x in edges: f.write(json.dumps(x,ensure_ascii=False)+'\n')
    keys=['node_type','name','properties','provenance']; ns='{http://graphml.graphdrawing.org/xmlns}'
    root=ET.Element(ns+'graphml'); ET.SubElement(root,ns+'key',{'id':'node_type','for':'node','attr.name':'node_type','attr.type':'string'}); ET.SubElement(root,ns+'key',{'id':'name','for':'node','attr.name':'name','attr.type':'string'}); ET.SubElement(root,ns+'key',{'id':'properties','for':'node','attr.name':'properties','attr.type':'string'}); ET.SubElement(root,ns+'key',{'id':'provenance','for':'all','attr.name':'provenance','attr.type':'string'}); g=ET.SubElement(root,ns+'graph',id='MarineSpatialKG',edgedefault='directed')
    for x in nodes.values():
        n=ET.SubElement(g,ns+'node',id=x['id']);
        for k,v in [('node_type',x['node_type']),('name',x['name']),('properties',json.dumps(x['properties'],ensure_ascii=False)),('provenance',json.dumps(x['provenance'],ensure_ascii=False))]: ET.SubElement(n,ns+'data',key=k).text=v
    for x in edges: e=ET.SubElement(g,ns+'edge',id=x['id'],source=x['subject_id'],target=x['object_id']); ET.SubElement(e,ns+'data',key='provenance').text=json.dumps({'predicate':x['predicate'],**x['provenance']},ensure_ascii=False)
    ET.ElementTree(root).write(OUT/'kg_v2.graphml',encoding='utf-8',xml_declaration=True)
    with (OUT/'kg_v2_neo4j_nodes.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f); w.writerow(['node_id:ID','name','node_type','properties','provenance',':LABEL']); [w.writerow([x['id'],x['name'],x['node_type'],json.dumps(x['properties'],ensure_ascii=False),json.dumps(x['provenance'],ensure_ascii=False),x['node_type']]) for x in nodes.values()]
    with (OUT/'kg_v2_neo4j_edges.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f); w.writerow(['edge_id:ID',':START_ID','predicate',':END_ID','properties','provenance',':TYPE']); [w.writerow([x['id'],x['subject_id'],x['predicate'],x['object_id'],json.dumps(x['properties'],ensure_ascii=False),json.dumps(x['provenance'],ensure_ascii=False),x['predicate']]) for x in edges]
    (ROOT/'outputs/reports/07_marine_kg_build_report.md').write_text(f'''# Marine Spatial Knowledge Graph 구축 보고서

## 결과

- 노드: {len(nodes)}개
- 엣지: {len(edges)}개
- 산출물: `outputs/graph/kg_nodes_v2.jsonl`, `kg_edges_v2.jsonl`, `kg_v2.graphml`, Neo4j CSV 2종
- 노드 타입 및 엣지 타입은 v2 KG 계약에 따라 생성했다.
- 모든 노드·엣지는 source path 또는 registry provenance를 가진다.
- `nearFeature`, `occurredIn`, `overlapsFeature`, `overlapsLayer`, `supportsConcept`는 실제 공간·사고·본문 근거 확보 전까지 pending 관계로 보류했다.

## 현재 한계 및 이력

- 정상 `_s100_dev_20260827.dump`가 확보되지 않아 실제 v2 공간 Feature 인스턴스와 DB 기반 관계는 bootstrap 메타데이터만 생성했다.
- PDF/DOCX/XML 본문 추출이 아직 없어 DocumentChunk는 metadata_only 또는 archive_manifest 기반이다.
- pgvector 임베딩은 미완료이며 Graph-RAG는 다음 작업에서 본 KG와 본문 임베딩을 연결해야 한다.
''',encoding='utf-8')
def main(): build(); write(); print(f'kg_generated nodes={len(nodes)} edges={len(edges)}')
if __name__=='__main__': main()
