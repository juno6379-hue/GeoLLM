"""Isolated P1 source binding; never installed in the production service.

Only registry source authority is substituted with the same public frozen
research corpus supplied to baselines. Routing, slots and Validator stay intact.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
from shapely.geometry import box
from .reliability_telemetry import VERSION as TELEMETRY_VERSION
from ..baselines.v2_runtime import snapshot_identity_sql

VERSION = 'p1_frozen_research_source_scope_v1'


def install(snapshot, folder):
    if os.environ.get('SCIE_MODEL_GRAPH') != '1' or not Path('/.dockerenv').exists():
        raise RuntimeError('Research worker only')
    if snapshot.get('db_identity') != {'container':'marine-scie-pilot-db','database':'scie_model_v3'}:
        raise ValueError('Fixed research identity required')
    from services.orchestrator.schema_binding_adapter import SchemaBindingAdapter, schema_binding_adapter
    records={r['relation']:r for r in snapshot['relations'] if r['relation'] in {
        'projection.s101_feature_current','serving.marine_gazetteer_current'}}
    catalogue_relative='data/s101_feature_catalogue_v2_parsed.json'
    catalogue_path=Path(__file__).resolve().parents[3]/catalogue_relative
    catalogue_bytes=catalogue_path.read_bytes()
    expected=next((r['sha256'] for r in snapshot['files'] if r['path']==catalogue_relative),None)
    if hashlib.sha256(catalogue_bytes).hexdigest()!=expected:raise ValueError('Frozen FC catalogue required')
    target_features=[feature['code'] for feature in json.loads(catalogue_bytes)['features']]
    folder=Path(folder).resolve()
    for r in records.values():
        p=(folder/r['csv_path']).resolve()
        if not p.is_relative_to(folder) or hashlib.sha256(p.read_bytes()).hexdigest()!=r['sha256']:
            raise ValueError('Frozen corpus missing or changed')
        snapshot_identity_sql(r)
    original_init=SchemaBindingAdapter.__init__
    original_verify=SchemaBindingAdapter.verify_corpus_identity
    original_build=SchemaBindingAdapter.build_bindings

    def configure(adapter):
        adapter.layer_registry=copy.deepcopy(adapter.layer_registry)
        for key, layer in adapter.layer_registry.get('layers',{}).items():
            relation=layer.get('physical_table')
            if relation not in records:continue
            r=records[relation]
            previous=layer.get('corpus_contract') or {}
            kind='s101_exact_inventory_v1' if relation.startswith('projection.') else 'csv_exact_inventory_v1'
            layer['corpus_contract']={**previous,'kind':kind,'dataset_id':key,
                'source_asset':str(folder/r['csv_path']),'source_sha256':r['sha256'],
                'snapshot_version':'sha256:'+r['sha256'],'default_inventory_listing':True,
                'allowed_operations':['feature_dwithin','feature_search_by_radius','feature_within_area','feature_search_by_area'],
                'authority_scope':'RESEARCH_FROZEN_SOURCE_ONLY'}
            if kind.startswith('s101'):
                # Same frozen FC source vocabulary as the baseline adapter.
                # This lists permissible types, never chooses a request target.
                layer['corpus_contract']['target_features']=target_features
            layer.pop('coverage_contract',None)

    def init(adapter,*args,**kwargs):
        original_init(adapter,*args,**kwargs);configure(adapter)

    def build(adapter,*args,**kwargs):
        result=original_build(adapter,*args,**kwargs)
        for binding in result.data_bindings:
            if binding.relation in records:binding.snapshot_version='sha256:'+records[binding.relation]['sha256']
        return result

    def verify(adapter,binding,contract):
        r=records.get(binding.relation)
        if r is None:return original_verify(adapter,binding,contract)
        if contract.get('authority_scope')!='RESEARCH_FROZEN_SOURCE_ONLY' or contract.get('source_sha256')!=r['sha256']:
            return {'status':'UNVERIFIED'}
        def check(connection):
            if connection.get_dsn_parameters().get('dbname')!='scie_model_v3':
                raise ValueError('Database identity mismatch')
            from psycopg2.extensions import cursor as TupleCursor
            with connection.cursor(cursor_factory=TupleCursor) as cursor:
                cursor.execute("SET LOCAL statement_timeout='30000ms'")
                cursor.execute("SELECT current_setting('transaction_read_only'),current_setting('transaction_isolation')")
                if tuple(cursor.fetchone())!=('on','repeatable read'):raise ValueError('Read-only stable snapshot required')
                cursor.execute(snapshot_identity_sql(r));row=cursor.fetchone()
                if tuple(row)!=(r['sha256'],r['rows'],True):return {'status':'UNVERIFIED'}
            receipt={'status':'VERIFIED','dataset_id':binding.dataset_id,'relation':binding.relation,
                'snapshot_version':'sha256:'+r['sha256'],'source_sha256':r['sha256'],
                'source_asset':contract['source_asset'],'row_count':r['rows'],
                'authority_scope':'RESEARCH_FROZEN_SOURCE_ONLY','absence_certified':False,
                'real_world_completeness':'UNKNOWN'}
            if binding.relation.startswith('projection.'):
                scope=r['coverage']
                if scope.get('selection')!='BOUNDED_SUBSET':return {'status':'UNVERIFIED'}
                receipt.update(target_features=contract['target_features'],source_scope={
                    'kind':'RESEARCH_SNAPSHOT_DOMAIN','crs':'EPSG:4326',
                    'source_locator':contract['source_asset']+'#coverage',
                    'source_sha256':r['sha256'],'geometry_wkt':box(*scope['bbox_epsg4326']).wkt})
            return receipt
        try:
            if adapter.connection is not None:return check(adapter.connection)
            import psycopg2
            with psycopg2.connect(os.environ['S101_DB_URL'],connect_timeout=3) as connection:
                connection.set_session(readonly=True,isolation_level='REPEATABLE READ')
                return check(connection)
        except Exception as exc:return {'status':'UNVERIFIED','reason':type(exc).__name__}
    def traced_verify(adapter,binding,contract):
        result=verify(adapter,binding,contract)
        adapter.research_source_checks=getattr(adapter,'research_source_checks',[])+[
            {'relation':binding.relation,'status':result.get('status'),'reason':result.get('reason')}]
        return result
    SchemaBindingAdapter.__init__=init
    SchemaBindingAdapter.build_bindings=build
    SchemaBindingAdapter.verify_corpus_identity=traced_verify
    configure(schema_binding_adapter)
    return {'version':VERSION,'telemetry_version':TELEMETRY_VERSION,
            'relations':{k:v['sha256'] for k,v in records.items()},
            'operational_registry_modified':False,'slots_modified':False,'gold_used':False}
