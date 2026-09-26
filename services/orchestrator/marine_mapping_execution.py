"""Source-qualified S-101 attribute searches using real PostGIS rows and explicit radius."""
import json
import os
import uuid
import psycopg2
from psycopg2.extras import RealDictCursor
from shapely import wkt
from services.orchestrator.marine_s101_mapping import resolve_mappings
from services.orchestrator.s101_radius_execution import RadiusProblem, resolve_reference, parse_distance, conservative_envelope
from services.orchestrator.slot_evidence import radius_quantities
from services.orchestrator.korean_query_analysis import constraints


def attribute_predicates(filters):
    clauses=[]; params=[]
    for key,values in sorted(filters.items()):
        clauses.append("EXISTS (SELECT 1 FROM jsonb_array_elements(CASE jsonb_typeof(attributes -> %s) "
                       "WHEN 'array' THEN attributes -> %s ELSE jsonb_build_array(attributes -> %s) END) v "
                       "WHERE v #>> '{}' = ANY(%s))")
        params.extend([key,key,key,values])
    return ' AND '.join(clauses),params


def applicable(query):
    from services.orchestrator.request_semantics import requires_execution
    return bool(requires_execution(query) and resolve_mappings(query,constraints(query)))


def execute(state):
    query=state['query']; mappings=resolve_mappings(query,constraints(query))
    spatial=state.get('spatial_context') or {}
    if hasattr(spatial,'model_dump'): spatial=spatial.model_dump()
    plan={'intent':'SPATIAL_ANALYSIS','analysis_type':'source_attribute_search',
          'tools':['postgis.dwithin'],'slots':{'source_mappings':mappings},'execution_ready':False}
    qec={'execution_status':'NOT_RUN','tool_bindings':[],'data_bindings':[], 'blockers':[]}
    final={'task_id':state['task_id'],'structured_result':{'analysis_type':'source_attribute_search'},
           'orchestrator_v2':{'route_plan':plan,'query_execution_context':qec}, 'map_layers':[]}
    try:
        if state.get('user_id')=='blocked_user': raise RadiusProblem('BLOCKED','ACCESS_DENIED','이 요청에 대한 접근 권한이 없습니다.')
        if spatial.get('exclusions') or any(
            c['scope_status']=='EXPLICIT_LOCAL_SCOPE' and c['kind'] in {'exclusion','absence_predicate'}
            for c in constraints(query)
        ):
            raise RadiusProblem('BLOCKED','NEGATION_EXECUTION_NOT_SUPPORTED','제외·부재 조건을 적용할 검색 계획이 필요합니다.')
        if len(mappings)!=1: raise RadiusProblem('BLOCKED','COMPOUND_MAPPING_REQUIRED','복수 용어의 속성 조건을 함께 적용할 계획이 필요합니다.')
        mapping=mappings[0]
        requested=spatial.get('target_features')
        if requested is not None and (not isinstance(requested,list) or not requested or
                                      any(f!=mapping['feature'] for f in requested)):
            raise RadiusProblem('BLOCKED','COMPOUND_MAPPING_REQUIRED','지도에서 요청한 객체와 용어의 검색 범위를 함께 확인해야 합니다.')
        other=(state.get('candidate_trace') or {}).get('semantic_slot_binding',{}).get('target_features',[])
        if other and any(f!=mapping['feature'] for f in other):
            raise RadiusProblem('BLOCKED','COMPOUND_MAPPING_REQUIRED','다른 객체와 함께 요청한 복합 검색 계획이 필요합니다.')
        if not mapping['search_enabled']:
            raise RadiusProblem('BLOCKED','TERM_MAPPING_UNRESOLVED',mapping['scope'])
        if not radius_quantities(query) and spatial.get('buffer_distance') is None:
            raise RadiusProblem('NEEDS_USER_INPUT','RADIUS_REQUIRED','검색 반경을 지정해주세요.')
        distance=parse_distance(query,spatial)
        geometry,label,crs,resolution=resolve_reference(query,spatial,{})
        point=wkt.loads(geometry)
        if crs!='EPSG:4326' or point.geom_type!='Point' or point.is_empty or not point.is_valid:
            raise RadiusProblem('NEEDS_USER_INPUT','INVALID_GEOMETRY','EPSG:4326 기준점을 확인해주세요.')
        envelope=conservative_envelope(point,distance)
        conditions,params=attribute_predicates(mapping['filters'])
        statement=("WITH matches AS MATERIALIZED (SELECT feature_instance_id, feature_type_name, attributes, geometry, "
          "ST_Distance(geometry::geography,ST_GeomFromText(%s,4326)::geography) AS distance_m "
          "FROM projection.s101_feature_valid WHERE feature_type_name=%s "
          "AND geometry && ST_MakeEnvelope(%s,%s,%s,%s,4326) "
          "AND ST_DWithin(geometry::geography,ST_GeomFromText(%s,4326)::geography,%s) AND "+conditions+
          ") SELECT (SELECT count(*) FROM matches) AS total_count, COALESCE((SELECT jsonb_agg(t) FROM "
          "(SELECT feature_instance_id,feature_type_name,attributes,distance_m,ST_AsGeoJSON(geometry)::jsonb AS geometry "
          "FROM matches ORDER BY distance_m,feature_instance_id LIMIT 100) t),'[]'::jsonb) AS rows")
        sql_params=[point.wkt,mapping['feature'],*envelope,point.wkt,distance,*params]
        with psycopg2.connect(os.environ['S101_DB_URL']) as connection:
            connection.set_session(readonly=True)
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SET LOCAL statement_timeout='15s'")
                cursor.execute(statement,sql_params); result=cursor.fetchone()
        execution_id=str(uuid.uuid4()); rows=result['rows']; total=result['total_count']
        features=[{'type':'Feature','id':r['feature_instance_id'],'geometry':r['geometry'],
                   'properties':{k:v for k,v in r.items() if k!='geometry'}} for r in rows]
        geojson={'type':'FeatureCollection','features':features}
        evidence=[{'evidence_id':execution_id+':'+str(r['feature_instance_id']), 'evidence_type':'spatial_feature',
                   'source_ref':'projection.s101_feature_valid','data':r} for r in rows]
        qec.update(execution_status='EXECUTED',readiness='EXECUTION_READY',
          tool_bindings=[{'tool_id':'postgis.dwithin','status':'EXECUTED','parameters':{
              'feature':mapping['feature'],'attribute_filters':mapping['filters'],'radius_m':distance,
              'reference_geometry':point.wkt},'query_execution_id':execution_id}],
          data_bindings=[{'source_ref':'projection.s101_feature_valid'}])
        plan.update(execution_ready=True,status='COMPLETED')
        message=(f"{label} 기준 {distance:g}m 이내에서 명시된 S-101 객체·속성 조건에 맞는 {total}건을 조회했습니다. "
                 "속성이 누락된 객체는 포함하지 않았으며 전체 실세계 시설 수를 뜻하지 않습니다.")
        final.update(status='COMPLETED',answer_text=message,summary=message,
          evidence_bundle={'spatial_feature_evidence':evidence,'kg_provenance':[mapping]},
          map_layers=[{'layer_id':execution_id,'source_type':'geojson','inline_geojson':geojson,'feature_count':len(rows)}])
        final['structured_result'].update(total_count=total,returned_count=len(rows),features=rows,geojson=geojson,
          mapping=mapping,distance_m=distance,query_execution_id=execution_id,location_resolution=resolution,
          web_rag_usage={'llm_used':False,'web_used':False,'execution_path':'postgis.dwithin.attributes'})
    except (RadiusProblem,psycopg2.Error) as error:
        status='NEEDS_CLARIFICATION' if isinstance(error,RadiusProblem) and error.status=='NEEDS_USER_INPUT' else 'BLOCKED'
        code=error.code if isinstance(error,RadiusProblem) else 'DB_EXECUTION_FAILED'
        message=str(error) if isinstance(error,RadiusProblem) else '속성 검색 원천 조회에 실패했습니다.'
        final.update(status=status,error_code=code,answer_text=message,summary=message,
                     clarification_options=getattr(error,'candidates',[]))
        qec.update(readiness=status,blockers=[code]); plan.update(status=status)
    return {'final_dict':final,'task_plan':plan,'query_execution_context':qec,
            'candidate_trace':state.get('candidate_trace'),'status':final['status'],'source_mapping_handled':True}
