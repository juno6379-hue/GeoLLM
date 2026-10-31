"""Read-only research tool adapter; no GOLD imports and no production authority."""
import copy
import base64
import json
import math
import subprocess
import time
from shapely import wkt
from shapely.geometry import mapping
from .execution_dsl import Executor, ResearchDatabase, SOURCES, ToolBlocked

OPERATIONS = {'dwithin':'feature_search_by_radius', 'nearest':'nearest_feature',
              'within':'feature_within_area', 'covers':'feature_within_area',
              'intersects':'feature_search_by_area'}


class ObservedDatabase(ResearchDatabase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.events=[]
        self.scope='metadata'

    def query(self, body, arguments):
        event={'scope':self.scope,'sql_submission_attempted':True,'sql_executed':None,'succeeded':None}
        self.events.append(event)
        start=time.perf_counter()
        try:
            encoded=base64.b64encode(json.dumps(arguments,ensure_ascii=False).encode()).decode('ascii')
            statement=("BEGIN READ ONLY; SET LOCAL statement_timeout='30000ms'; WITH input AS "
                "(SELECT convert_from(decode('"+encoded+"','base64'),'UTF8')::jsonb AS args) "
                "SELECT coalesce(jsonb_agg(result),'[]'::jsonb)::text FROM ("+body+") result; ROLLBACK;")
            # Geometry may contain >13k vertices. Use stdin, never Windows argv
            # or a shell string, preserving read-only parameter transport.
            command=['docker','exec','-i',self.container,'psql','-X','-qAt','-v','ON_ERROR_STOP=1',
                     '-U','postgres','-d',self.database]
            process=subprocess.run(command,input=statement,capture_output=True,text=True,encoding='utf-8',timeout=self.timeout)
            event['process_returncode']=process.returncode
            if process.returncode:
                raise RuntimeError('RESEARCH_DB_QUERY_FAILED')
            rows=json.loads(process.stdout.strip())
            event.update(sql_executed=True,succeeded=True,row_count=len(rows))
            return rows
        except Exception as exc:
            event['error_type']=type(exc).__name__
            # subprocess/transport failure does not prove server execution.
            raise
        finally:
            event['latency_ms']=(time.perf_counter()-start)*1000


def spatial_statement(source, relation):
    table, identifier, label, filter_column=SOURCES[source]
    predicates={'dwithin':'ST_DWithin(p.geometry::geography,r.geom::geography,(i.args->>\'radius_m\')::float8)',
        'nearest':'TRUE','within':'ST_Within(p.geometry,r.geom)',
        'covers':'ST_Covers(r.geom,p.geometry)','intersects':'ST_Intersects(p.geometry,r.geom)'}
    if relation not in predicates:
        raise ToolBlocked('UNSUPPORTED_SPATIAL_OPERATOR')
    filt=("AND p.feature_type_name IN (SELECT jsonb_array_elements_text(i.args->'feature_types'))"
          if filter_column else '')
    attributes=',p.attributes,p.dataset_id,p.dataset_version_id' if source=='s101' else ',p.properties,p.provenance'
    return f"""SELECT p.{identifier}::text source_id,p.{label} label,
      ST_AsGeoJSON(p.geometry)::jsonb geometry{attributes},
      ST_Distance(p.geometry::geography,r.geom::geography) distance_m
      FROM {table} p,input i CROSS JOIN LATERAL
      (SELECT ST_GeomFromText(i.args->>'reference_geometry',4326) geom) r
      WHERE p.geometry IS NOT NULL AND ST_IsValid(p.geometry) AND {predicates[relation]}
      {filt} ORDER BY distance_m,p.{identifier} LIMIT {1 if relation=='nearest' else 1001}"""


class V2Executor(Executor):
    """Common fixed SQL safety; semantic review/Validator is a separate branch.

    All branches share coverage checks below. Report this common executor floor;
    do not attribute its blocks to the optional deterministic Validator.
    """
    def __init__(self, db, *, reference_geometries=None, **kwargs):
        super().__init__(db, **kwargs)
        self.reference_geometries=reference_geometries or {}

    def reference(self,args):
        explicit=args.get('reference_geometry')
        ref=args.get('geometry_ref')
        if ref is not None and not isinstance(ref,str):
            raise ToolBlocked('INVALID_REFERENCE_GEOMETRY_REF_TYPE')
        if explicit is not None and ref is not None:
            entry=self.reference_geometries.get(ref)
            if not entry or entry.get('geometry_wkt')!=explicit:
                raise ToolBlocked('CONFLICTING_REFERENCE_GEOMETRY')
        if explicit is None and ref is not None:
            entry=self.reference_geometries.get(ref)
            if not entry:
                raise ToolBlocked('UNKNOWN_REFERENCE_GEOMETRY')
            explicit=entry.get('geometry_wkt')
        if not isinstance(explicit,str):
            raise ToolBlocked('MISSING_REFERENCE_GEOMETRY')
        try:
            geometry=wkt.loads(explicit)
            if geometry.is_empty or not geometry.is_valid:
                raise ValueError()
            xmin,ymin,xmax,ymax=geometry.bounds
            if not (-180<=xmin<=xmax<=180 and -90<=ymin<=ymax<=90):
                raise ValueError()
        except Exception as exc:
            raise ToolBlocked('INVALID_REFERENCE_GEOMETRY') from exc
        return explicit

    def spatial_arguments(self,args):
        if args.get('crs')!='EPSG:4326':
            raise ToolBlocked('MISSING_OR_UNSUPPORTED_CRS')
        source=args.get('source')
        relation=args.get('relation')
        if not isinstance(source,str) or not isinstance(relation,str):
            raise ToolBlocked('SOURCE_OR_OPERATOR_TYPE_INVALID')
        if source not in SOURCES or relation not in OPERATIONS:
            raise ToolBlocked('SOURCE_OR_OPERATOR_NOT_ALLOWLISTED')
        radius=args.get('radius_m',args.get('distance_m'))
        if relation=='dwithin' and (type(radius) not in (int,float) or not math.isfinite(radius) or not 0<radius<=50000):
            raise ToolBlocked('MISSING_OR_INVALID_RADIUS')
        # nearest deliberately has no arbitrary maximum search radius.
        if relation=='nearest' and radius is not None:
            raise ToolBlocked('NEAREST_RADIUS_NOT_SUPPORTED_BY_FIXED_CONTRACT')
        features=args.get('feature_types',args.get('target_features'))
        allowed={f['code'] for f in self.catalogue['features']}
        if features is not None and (not isinstance(features,list) or any(not isinstance(x,str) for x in features)):
            raise ToolBlocked('FEATURE_TYPES_INVALID')
        if source=='s101' and (not features or any(x not in allowed for x in features)):
            raise ToolBlocked('FEATURE_CODE_NOT_VERIFIED')
        return {'source':source,'relation':relation,'radius_m':radius,
                'feature_types':features or [],'reference_geometry':self.reference(args)}

    def coverage_check(self, args):
        coverage=self.coverage.get(args['source'],{})
        if coverage.get('scope_verified') is not True:
            raise ToolBlocked('SOURCE_COVERAGE_UNVERIFIED')
        bounds=coverage.get('bbox_epsg4326')
        if bounds:
            # Exact geography margin, not a degrees-to-metres approximation.
            body="""SELECT ST_Covers(b.geom,r.geom) covered,
              ST_Distance(ST_Boundary(b.geom)::geography,r.geom::geography) margin_m
              FROM input i CROSS JOIN LATERAL (SELECT ST_MakeEnvelope(
              (i.args->'bbox'->>0)::float8,(i.args->'bbox'->>1)::float8,
              (i.args->'bbox'->>2)::float8,(i.args->'bbox'->>3)::float8,4326) geom) b
              CROSS JOIN LATERAL (SELECT ST_GeomFromText(i.args->>'reference_geometry',4326) geom) r"""
            rows=self.db.query(body,{'bbox':bounds,'reference_geometry':args['reference_geometry']})
            if not rows or rows[0]['covered'] is not True:
                raise ToolBlocked('DATA_OUT_OF_SCOPE')
            if args['relation']=='dwithin' and rows[0]['margin_m']<args['radius_m']:
                raise ToolBlocked('SEARCH_EXTENT_COVERAGE_UNVERIFIED')
        elif coverage.get('scope_type')!='FULL_DECLARED_SOURCE':
            raise ToolBlocked('SEARCH_EXTENT_COVERAGE_UNVERIFIED')
        return coverage

    def call(self,tool_id,args):
        if tool_id!='spatial.query':
            self.db.scope='document' if tool_id=='documents.search' else 'metadata'
            return super().call(tool_id,args)
        if not isinstance(args,dict):
            raise ToolBlocked('ARGUMENTS_MUST_BE_OBJECT')
        arguments=self.spatial_arguments(args)
        self.db.scope='coverage_metadata'
        coverage=self.coverage_check(arguments)
        self.db.scope='spatial'
        rows=self.db.query(spatial_statement(arguments['source'],arguments['relation']),arguments)
        if len(rows)>1000:
            raise ToolBlocked('RESULT_LIMIT_EXCEEDED_INCOMPLETE_SET')
        return {'rows':rows,'source':arguments['source'],'source_scope':coverage,
                'relation':arguments['relation'],'radius_m':arguments['radius_m'],
                'source_sha256':coverage.get('source_sha256'),
                'postcondition':'SPATIAL_ROWS_RETURNED' if rows else 'SPATIAL_EMPTY_WITHIN_DECLARED_SOURCE_SCOPE'}

    def execute(self,plan):
        start=len(self.db.events)
        result=super().execute(plan)
        events=copy.deepcopy(self.db.events[start:])
        spatial=[x for x in events if x['scope']=='spatial']
        calls=[x for x in result.get('receipts',[]) if x['tool_id']=='spatial.query']
        sql_observed=True if any(x.get('sql_executed') is True or x.get('succeeded') is True for x in spatial) else None if spatial else False
        result['execution_observation']={'observation_complete':True,
            'execution_attempted':bool(calls) or bool(spatial),'tool_called':bool(calls),
            'execution_started':sql_observed,'sql_executed':sql_observed,
            'execution_succeeded':True if spatial and all(x.get('succeeded') is True for x in spatial) else None,
            'scope':'SPATIAL_EXECUTION_ONLY; metadata and document SQL separately recorded','db_events':events}
        return result


class ResearchBindingAdapter:
    """Verify only explicit source/tool values using actual research DB metadata."""
    def __init__(self,executor):
        self.executor=executor
        self.tool_registry={'tools':{}}

    def build_bindings(self,route,slots):
        from services.orchestrator.schema_binding_adapter import BindingResult
        from shared.schemas.agent import DataBinding,ToolBinding
        out=BindingResult()
        source=(slots.get('filters') or {}).get('source')
        if not isinstance(source,str) or source not in SOURCES:
            out.blockers.append('BLOCKED_CONFIG: explicit research source required')
            return out
        relation=SOURCES[source][0]
        sql="""SELECT to_regclass(i.args->>'relation') IS NOT NULL present,
          has_table_privilege(current_user,i.args->>'relation','SELECT') selectable,
          (SELECT jsonb_agg(column_name) FROM information_schema.columns
           WHERE table_schema=split_part(i.args->>'relation','.',1)
             AND table_name=split_part(i.args->>'relation','.',2)) columns FROM input i"""
        self.executor.db.scope='binding_metadata'
        records=self.executor.db.query(sql,{'relation':relation})
        info=records[0] if records else {}
        out.inspected_relations[relation]=info
        if info.get('present') is not True or info.get('selectable') is not True or 'geometry' not in (info.get('columns') or []):
            out.blockers.append('BLOCKED_DATA: research source metadata verification failed')
            return out
        if slots.get('tool')!='spatial.query':
            out.blockers.append('BLOCKED_CONFIG: unsupported explicit tool binding')
            return out
        operation=route.get('analysis_type')
        if operation not in OPERATIONS.values():
            out.blockers.append('BLOCKED_CONFIG: explicit analysis_type required')
            return out
        out.data_bindings=[DataBinding(dataset_id=source,relation=relation,srid=4326,read_only=True)]
        out.tool_bindings=[ToolBinding(tool_id='spatial.query',operation=operation)]
        return out


def validator_for(executor):
    from services.orchestrator.execution_validator import validate_execution_context
    def validate(qec):
        # Explicit symbol dereference is binding verification, never selection.
        if qec.slots.geometry_ref and not qec.slots.reference_geometry:
            ref=executor.reference_geometries.get(qec.slots.geometry_ref)
            if ref and qec.slots.crs==ref.get('crs'):
                qec.spatial['spatial_context']={'geometry':ref['geometry_wkt']}
                qec.provenance['explicit_reference_binding']={'geometry_ref':qec.slots.geometry_ref,
                    'source_sha256':ref.get('source_sha256'),'selection_performed':False}
        if qec.route_plan.get('analysis_type')=='public_catalogue_document_lookup':
            from services.orchestrator.schema_binding_adapter import SchemaBindingAdapter
            return validate_execution_context(qec,binding_adapter=SchemaBindingAdapter())
        return validate_execution_context(qec,binding_adapter=ResearchBindingAdapter(executor))
    return validate
