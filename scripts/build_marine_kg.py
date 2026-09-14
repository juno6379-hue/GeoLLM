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
def chunk_source_type(metadata):
    source_type=metadata.get('source_type')
    if source_type: return source_type
    document_type=str(metadata.get('document_type') or '').lower()
    standard_type=str(metadata.get('standard_type') or '').lower()
    if document_type in {'law','law_rag','notice','regulation'}: return 'law_rag'
    if standard_type in {'s-100','s100'}: return 'standard_s100'
    if standard_type in {'s-101','s101'}: return 'standard_s101'
    if standard_type in {'s-104','s104'}: return 'standard_s104'
    if standard_type in {'s-111','s111'}: return 'standard_s111'
    if standard_type in {'s-124','s124'}: return 'standard_s124'
    if 'accident' in document_type: return 'accident_data'
    return 'document_chunk'
def chunk_source_path(metadata):
    return metadata.get('source_path') or metadata.get('source_file') or metadata.get('source_id') or 'unknown_document'
def load_yaml_path(path):
    if not path.exists(): return {}
    return yaml.safe_load(path.read_text(encoding='utf-8')) or {}
def term_dict_sources():
    sources=[]
    data_terms=load('marine_term_dictionary.yaml').get('terms',{})
    if data_terms: sources.append(('data/marine_term_dictionary.yaml', data_terms))
    generated=load_yaml_path(ROOT/'outputs/dictionaries/marine_term_dictionary.yaml').get('terms',{})
    if generated: sources.append(('outputs/dictionaries/marine_term_dictionary.yaml', generated))
    return sources
def feature_node_for(feature,catalogue):
    catalogue_code=next((x["nftc"] or x["name"] for x in catalogue if x["name"]==feature),feature)
    return add_node('Feature',f'{feature}:{catalogue_code}',canonical_name=feature,provenance=source('data/s101_feature_catalogue_v2_parsed.json'))
def layer_node_id(layer_name):
    if layer_name in load('traffic_layer_registry.yaml').get('layers',{}):
        return nid('DynamicTrafficLayer',layer_name)
    return nid('DataLayer',layer_name)
def evidence_ref_node(ref, predicate=None, legal_registry=None, catalogue=None):
    value=str(ref)
    if value.startswith('ontology_binding:'):
        return add_node('OntologyBindingProposal',value,provenance=source('outputs/ontology/ontology_binding_proposals.jsonl'))
    if predicate in {'supportsFeature','mapsToFeature','includesFeature'}:
        return feature_node_for(value,catalogue or [])
    if predicate in {'authorizedBy','publishedBy'}:
        legal_registry=legal_registry or {}
        if value in legal_registry.get('legal_notices',{}):
            return nid('LegalNotice',value)
        if value in legal_registry.get('official_datasets',{}):
            return nid('OfficialDataset',value)
        if value in legal_registry.get('authorities',{}):
            return nid('Authority',value)
    if predicate == 'definedBy':
        return nid('Law',value)
    if value in load('traffic_layer_registry.yaml').get('layers',{}):
        return nid('DynamicTrafficLayer',value)
    return layer_node_id(value)

def build():
    inventory=load('kg_inventory_registry.yaml')
    inventory_root=add_node('KGInventory',inventory.get('inventory_id','geollm.kg.inventory'),version=inventory.get('version'),source_note=inventory.get('source_note'),provenance=source('data/kg_inventory_registry.yaml'))
    for group,meta in inventory.get('inventory_groups',{}).items():
        group_node=add_node('KGInventory',group,**meta,provenance=source('data/kg_inventory_registry.yaml'))
        add_edge(inventory_root,'hasInventoryGroup',group_node,provenance=source('data/kg_inventory_registry.yaml'))

    upper=load('upper_ontology_registry.yaml')
    for name,meta in upper.get('classes',{}).items():
        cls=add_node('UpperClass',name,**meta,provenance=source('data/upper_ontology_registry.yaml'))
        if meta.get('parent'):
            add_edge(cls,'specializes',nid('UpperClass',meta['parent']),provenance=source('data/upper_ontology_registry.yaml'))

    mof_domains=load('mof_domain_registry.yaml')
    for name,meta in mof_domains.get('domains',{}).items():
        domain=add_node('DomainArea',name,**meta,provenance=source('data/mof_domain_registry.yaml'))
        for upper_class in meta.get('upper_classes') or []:
            add_edge(domain,'domainUsesUpperClass',nid('UpperClass',upper_class),provenance=source('data/mof_domain_registry.yaml'))

    semantic_mapping=load('s100_s101_mapping_registry.yaml')
    for product,meta in semantic_mapping.get('products',{}).items():
        add_node('Product',product,**meta,provenance=source('data/s100_s101_mapping_registry.yaml'))
    for name,meta in semantic_mapping.get('semantic_mappings',{}).items():
        mapping=add_node('SemanticMapping',name,**meta,provenance=source('data/s100_s101_mapping_registry.yaml'))
        if meta.get('upper_class'):
            add_edge(mapping,'belongsToUpperClass',nid('UpperClass',meta['upper_class']),provenance=source('data/s100_s101_mapping_registry.yaml'))
        if meta.get('product'):
            add_edge(mapping,'mapsToProduct',nid('Product',meta['product']),provenance=source('data/s100_s101_mapping_registry.yaml'))

    products=load('s100_product_registry.yaml').get('products',{})
    for product,meta in products.items():
        p=add_node('Product',product,version=meta.get('version'),source_type=meta.get('source_type'),provenance=source('data/s100_product_registry.yaml'))
        for catalogue,kind in [('FeatureCatalogue','feature_catalogue'),('PortrayalCatalogue','portrayal_catalogue'),('DCEG','dceg')]:
            files=[x for x in (ROOT/'outputs/inventories/dataset_inventory.csv').read_text(encoding='utf-8-sig').splitlines() if kind in x.lower()]
            for f in files[:20]:
                provenance=source('outputs/inventories/dataset_inventory.csv')
                target=add_node(catalogue,Path(f.split(',')[1] if ',' in f else f).name,provenance=provenance)
                add_edge(p,{'FeatureCatalogue':'hasFeatureCatalogue','PortrayalCatalogue':'portrayedBy','DCEG':'hasDCEG'}[catalogue],target,provenance=provenance)

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

    for source_path,terms in term_dict_sources():
      for term,meta in terms.items():
        canonical=meta.get('canonical_id') or meta.get('canonical_term') or term
        aliases=list(dict.fromkeys([term]+(meta.get('aliases') or [])))
        provenance=meta.get('provenance') if isinstance(meta.get('provenance'),dict) else source(source_path)
        t=add_node('MarineTerm',canonical,surface_terms=[term],aliases=aliases,replace_in_query=meta.get('replace_in_query'),source_evidence=meta.get('source_evidence'),s101_feature_catalogue=meta.get('s101_feature_catalogue'),dceg_evidence=meta.get('dceg_evidence'),disambiguation_attributes=meta.get('disambiguation_attributes'),taxonomy_class=meta.get('taxonomy_class'),verification_status=meta.get('verification_status'),definitions=meta.get('definitions'),provenance=provenance)
        taxonomy=meta.get('taxonomy_class')
        if taxonomy:
            cls=add_node('TaxonomyClass',taxonomy,provenance=source('scripts/parse_marine_terms_gazetteer.py'))
            add_edge(cls,'classifiesTerm',t,provenance=provenance)
        feature_targets=list(dict.fromkeys((meta.get('maps_to_features') or []) + ([canonical] if canonical in [x.get('name') for x in catalogue] else [])))
        for feature in feature_targets:
            add_edge(t,'mapsToFeature',feature_node_for(feature,catalogue),verification_status=meta.get('verification_status') or 'CANDIDATE',provenance=provenance)
        for concept in meta.get('maps_to_concepts') or []:
            concept_node=add_node('DerivedConcept',concept,provenance=source('data/derived_concept_registry_v2.yaml'))
            add_edge(t,'mapsToConcept',concept_node,verification_status=meta.get('verification_status') or 'CANDIDATE',provenance=provenance)
        for alias in aliases:
            a=add_node('MarineTerm',alias,alias_of=canonical,provenance=provenance); add_edge(a,'aliasOf',t,provenance=provenance)
    concepts=load('derived_concept_registry_v2.yaml').get('derived_concepts',{})
    for name,meta in concepts.items():
        c=add_node('DerivedConcept',name,default_context=meta.get('default_context'),analysis_type=meta.get('analysis_type'),provenance=source('data/derived_concept_registry_v2.yaml'))
        if name in semantic_mapping.get('semantic_mappings',{}):
            add_edge(c,'mapsToSemanticMapping',nid('SemanticMapping',name),provenance=source('data/s100_s101_mapping_registry.yaml'))
        for feature in meta.get('target_features',[]):
            catalogue_code=next((x["nftc"] or x["name"] for x in catalogue if x["name"]==feature),feature)
            feature_node=add_node('Feature',f'{feature}:{catalogue_code}',canonical_name=feature,provenance=source('data/derived_concept_registry_v2.yaml'))
            add_edge(c,'includesFeature',feature_node,provenance=source('data/derived_concept_registry_v2.yaml'))
        for tool in meta.get('required_tools',[]): add_edge(c,'requiresTool',nid('Tool',tool),provenance=source('data/derived_concept_registry_v2.yaml'))
        for data in meta.get('required_data',[]):
            data_node=add_node('DataLayer',data,provenance=source('data/derived_concept_registry_v2.yaml'))
            add_edge(c,'requiresData',data_node,provenance=source('data/derived_concept_registry_v2.yaml'))
        if meta.get('primary_agent'): add_edge(c,'requiresAgent',nid('Agent',meta['primary_agent']),provenance=source('data/derived_concept_registry_v2.yaml'))

    for name,meta in load('spatial_layer_registry.yaml').get('layers',{}).items():
        provenance=source('data/spatial_layer_registry.yaml')
        l=add_node('DataLayer',name,**meta,provenance=provenance); add_edge(l,'storedIn',add_node('DataLayer',meta.get('physical_table','serving'),provenance=provenance),provenance=provenance)
        upper_class=upper.get('layer_classification_rules',{}).get(name)
        if upper_class:
            add_edge(l,'belongsToUpperClass',nid('UpperClass',upper_class),provenance=source('data/upper_ontology_registry.yaml'))
        for domain in mof_domains.get('layer_domain_map',{}).get(name) or []:
            add_edge(l,'belongsToDomain',nid('DomainArea',domain),provenance=source('data/mof_domain_registry.yaml'))
        product=semantic_mapping.get('layer_product_map',{}).get(name)
        if product:
            add_edge(l,'mapsToProduct',nid('Product',product),provenance=source('data/s100_s101_mapping_registry.yaml'))
        for mapping_name,mapping_meta in semantic_mapping.get('semantic_mappings',{}).items():
            if mapping_meta.get('upper_class') == upper_class:
                add_edge(l,'mapsToSemanticMapping',nid('SemanticMapping',mapping_name),provenance=source('data/s100_s101_mapping_registry.yaml'))
    for name,meta in load('traffic_layer_registry.yaml').get('layers',{}).items(): add_node('DynamicTrafficLayer',name,**meta,provenance=source('data/traffic_layer_registry.yaml'))
    for name,meta in load('data_registry.yaml').get('datasets',{}).items(): add_node('DataLayer',name,**meta,provenance=source('data/data_registry.yaml'))
    legal_registry=load('legal_notice_registry.yaml').get('registries',{})
    legal_prov=source('data/legal_notice_registry.yaml')
    for authority_id,meta in legal_registry.get('authorities',{}).items():
        add_node('Authority',authority_id,**meta,provenance=legal_prov)
    for law_id,meta in legal_registry.get('laws',{}).items():
        law=add_node('Law',law_id,**meta,provenance=legal_prov)
        if meta.get('authority_id'):
            add_edge(law,'publishedBy',nid('Authority',meta['authority_id']),verification_status=meta.get('verification_status','CANDIDATE'),provenance=legal_prov)
    for notice_id,meta in legal_registry.get('legal_notices',{}).items():
        notice=add_node('LegalNotice',notice_id,**meta,provenance=legal_prov)
        if meta.get('authority_id'):
            add_edge(notice,'publishedBy',nid('Authority',meta['authority_id']),verification_status=meta.get('verification_status','CANDIDATE'),provenance=legal_prov)
        for law_id in meta.get('basis_laws') or []:
            add_edge(notice,'definedBy',nid('Law',law_id),verification_status=meta.get('verification_status','CANDIDATE'),provenance=legal_prov)
        for layer in meta.get('governs_layers') or []:
            add_edge(layer_node_id(layer),'authorizedBy',notice,verification_status=meta.get('verification_status','CANDIDATE'),provenance=legal_prov)
            for law_id in meta.get('basis_laws') or []:
                add_edge(layer_node_id(layer),'definedBy',nid('Law',law_id),verification_status=meta.get('verification_status','CANDIDATE'),provenance=legal_prov)
    for dataset_id,meta in legal_registry.get('official_datasets',{}).items():
        dataset=add_node('OfficialDataset',dataset_id,**meta,provenance=legal_prov)
        if meta.get('authority_id'):
            add_edge(dataset,'publishedBy',nid('Authority',meta['authority_id']),verification_status=meta.get('verification_status','CANDIDATE'),provenance=legal_prov)
        for law_id in meta.get('basis_laws') or []:
            add_edge(dataset,'definedBy',nid('Law',law_id),verification_status=meta.get('verification_status','CANDIDATE'),provenance=legal_prov)
        for layer in meta.get('governs_layers') or []:
            add_edge(layer_node_id(layer),'derivedFrom',dataset,verification_status=meta.get('verification_status','CANDIDATE'),provenance=legal_prov)
            add_edge(layer_node_id(layer),'authorizedBy',dataset,verification_status=meta.get('verification_status','CANDIDATE'),provenance=legal_prov)
    evidence_registry=load_yaml_path(DATA/'evidence_registry.yaml')
    evidence_prov=source('data/evidence_registry.yaml')
    for evidence_id,item in (evidence_registry.get('evidence_items') or {}).items():
        evidence_node=add_node('EvidenceItem',evidence_id,partition=item.get('partition'),evidence_type=item.get('evidence_type'),summary=item.get('summary'),source_ref=item.get('source_ref'),verification_status=item.get('verification_status'),review_status=item.get('review_status'),provenance=item.get('provenance') or evidence_prov)
        for edge in (evidence_registry.get('kg_edge_promotions') or {}).get(evidence_id) or []:
            predicate=edge.get('predicate')
            subject=evidence_ref_node(edge.get('subject'),predicate,legal_registry,catalogue)
            obj=evidence_ref_node(edge.get('object'),predicate,legal_registry,catalogue)
            add_edge(subject,predicate,obj,verification_status=edge.get('verification_status') or item.get('verification_status'),evidence_id=evidence_id,review_status=item.get('review_status'),provenance={**evidence_prov,'evidence_id':evidence_id,'source_ref':item.get('source_ref')})
            add_edge(evidence_node,'supportsSubject',subject,provenance=evidence_prov)
            add_edge(evidence_node,'supportsObject',obj,provenance=evidence_prov)
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
            row=json.loads(line); m=row['metadata']; source_type=chunk_source_type(m); source_path=chunk_source_path(m); provenance=m.get('provenance') or source(source_path)
            ch=add_node('DocumentChunk',row['chunk_id'],source_id=m.get('source_id'),extraction_status=m.get('extraction_status'),provenance=provenance)
            parent=add_node('StandardDocument' if source_type.startswith('standard_') else ('LawDocument' if source_type=='law_rag' else 'AccidentEvent' if source_type=='accident_data' else 'DocumentChunk'),source_path,provenance=provenance)
            if parent!=ch: add_edge(parent,'hasChunk',ch,provenance=provenance)

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
