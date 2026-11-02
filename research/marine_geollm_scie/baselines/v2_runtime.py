"""Read-only research tool adapter; no GOLD imports and no production authority."""
import copy
import base64
import json
import math
import subprocess
import time
import hashlib
import re
from pathlib import Path
from shapely import wkt
from shapely.geometry import mapping, box
from research.marine_geollm_scie.evaluation.execution_semantics import canonical_trace
from .execution_dsl import Executor, ResearchDatabase, SOURCES, ToolBlocked

OPERATIONS = {'dwithin':'feature_search_by_radius', 'nearest':'nearest_feature',
              'within':'feature_within_area', 'covers':'feature_within_area',
              'intersects':'feature_search_by_area'}


def snapshot_identity_sql(record):
    """Reproduce PostgreSQL COPY CSV HEADER bytes, in the frozen key order.

    Only fixed spatial relations/identifiers are interpolated. All cell values
    remain database values. This is inventory identity, never geographic proof.
    """
    relation = record['relation']
    source = next((s for s, spec in SOURCES.items() if spec[0] == relation), None)
    columns = [column[0] for column in record['columns']]
    if source is None or not columns or any(not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', c) for c in columns):
        raise ValueError('RESEARCH_SNAPSHOT_SCHEMA_NOT_ALLOWLISTED')
    cells = []
    for column, specification in zip(columns, record['columns']):
        value = 'p."' + column + '"::text'
        if specification[1] == 'boolean':
            value = '(CASE WHEN p."' + column + '" THEN \'t\' WHEN NOT p."' + column + '" THEN \'f\' ELSE NULL END)'
        cells.append("CASE WHEN " + value + " IS NULL THEN '' WHEN " + value +
                     " = '' OR " + value + " ~ E'[,\\\"\\r\\n]' THEN '\"' || replace(" + value +
                     ", '\"', '\"\"') || '\"' ELSE " + value + " END")
    row = " || ',' || ".join(cells)
    key = SOURCES[source][1]
    header = ','.join(columns)
    schema, table = relation.split('.')
    schema_check = ("(SELECT array_agg(column_name::text ORDER BY ordinal_position) FROM information_schema.columns "
                    "WHERE table_schema='" + schema + "' AND table_name='" + table + "') = ARRAY[" +
                    ','.join("'" + c + "'" for c in columns) + "] AS schema_matches")
    return ("SELECT encode(sha256(convert_to('" + header + "' || E'\\n' || "
            "coalesce(string_agg((" + row + ") || E'\\n', '' ORDER BY p.\"" + key +
            "\"), ''), 'UTF8')), 'hex') AS source_sha256, count(*) AS row_count, " + schema_check + " FROM " + relation + " p")


def _snapshot_guard(record):
    digest = record['sha256']
    if not re.fullmatch(r'[0-9a-f]{64}', digest):
        raise ValueError('RESEARCH_SNAPSHOT_HASH_INVALID')
    return (
            "DO $source_guard$ BEGIN IF NOT EXISTS (SELECT 1 FROM (" + snapshot_identity_sql(record) +
            ") observed WHERE schema_matches IS TRUE AND source_sha256 = '" + digest + "' AND row_count = " + str(int(record['rows'])) +
            ") THEN RAISE EXCEPTION 'RESEARCH_SNAPSHOT_IDENTITY_MISMATCH'; END IF; END $source_guard$; ")


class ObservedDatabase(ResearchDatabase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.events=[]
        self.scope='metadata'
        self.source_guard=None

    def query(self, body, arguments):
        if self.scope == 'spatial' and self.source_guard is None:
            raise ToolBlocked('RESEARCH_ATOMIC_SOURCE_GUARD_REQUIRED')
        event={'scope':self.scope,'sql_submission_attempted':True,'sql_executed':None,'succeeded':None}
        self.events.append(event)
        start=time.perf_counter()
        try:
            encoded=base64.b64encode(json.dumps(arguments,ensure_ascii=False).encode()).decode('ascii')
            guard = _snapshot_guard(self.source_guard) if self.source_guard is not None else ''
            statement=("BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY; SET LOCAL statement_timeout='30000ms'; " + guard + "WITH input AS "
                "(SELECT convert_from(decode('"+encoded+"','base64'),'UTF8')::jsonb AS args) "
                "SELECT coalesce(jsonb_agg(result),'[]'::jsonb)::text FROM ("+body+") result; ROLLBACK;")
            # Geometry may contain >13k vertices. Use stdin, never Windows argv
            # or a shell string, preserving read-only parameter transport.
            command=['docker','exec','-i',self.container,'psql','-X','-qAt','-v','ON_ERROR_STOP=1',
                     '-U','postgres','-d',self.database]
            process=subprocess.run(command,input=statement,capture_output=True,text=True,encoding='utf-8',timeout=self.timeout)
            event['process_returncode']=process.returncode
            if process.returncode:
                if 'RESEARCH_SNAPSHOT_IDENTITY_MISMATCH' in process.stderr:
                    event.update(sql_executed=False,succeeded=False,
                                 source_identity_status='MISMATCH_BEFORE_SPATIAL_SQL')
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
    def __init__(self, db, *, reference_geometries=None, snapshot_manifest=None, **kwargs):
        if isinstance(db, ObservedDatabase) and snapshot_manifest is None:
            raise ToolBlocked('RESEARCH_SNAPSHOT_PIN_REQUIRED')
        super().__init__(db, **kwargs)
        self.reference_geometries=reference_geometries or {}
        self.snapshot_manifest = copy.deepcopy(snapshot_manifest)

    def snapshot_record(self, source):
        """Recheck frozen file identity; never discover a snapshot implicitly."""
        pin = self.snapshot_manifest
        if not isinstance(pin, dict) or not re.fullmatch(r'[0-9a-f]{64}', str(pin.get('sha256', ''))):
            raise ToolBlocked('RESEARCH_SNAPSHOT_PIN_REQUIRED')
        path = Path(pin['path']).resolve()
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != pin['sha256']:
            raise ToolBlocked('RESEARCH_SNAPSHOT_MANIFEST_CHANGED')
        manifest = json.loads(raw)
        identity = {'container': getattr(self.db, 'container', None), 'database': getattr(self.db, 'database', None)}
        if identity != {'container':'marine-scie-pilot-db','database':'scie_model_v3'} or manifest.get('db_identity') != identity or manifest.get('status') != 'LOADED_VERIFIED':
            raise ToolBlocked('RESEARCH_SNAPSHOT_DATABASE_MISMATCH')
        records = [r for r in manifest.get('relations', []) if r['relation'] == SOURCES[source][0]]
        if len(records) != 1:
            raise ToolBlocked('RESEARCH_SNAPSHOT_RELATION_MISSING')
        record = records[0]
        asset = (path.parent / record['csv_path']).resolve()
        if not asset.is_relative_to(path.parent) or hashlib.sha256(asset.read_bytes()).hexdigest() != record['sha256']:
            raise ToolBlocked('RESEARCH_SNAPSHOT_SOURCE_CHANGED')
        if self.coverage.get(source, {}).get('source_sha256') != record['sha256']:
            raise ToolBlocked('RESEARCH_SCOPE_SOURCE_MISMATCH')
        declared = self.coverage.get(source, {})
        frozen_scope = record.get('coverage') or {}
        # Shared executor floor: B3/B4 must not accept a profile that P0/H's
        # adapter rejects. Validate scope before any branch reaches spatial SQL.
        if source == 's101' and (frozen_scope.get('selection') != 'BOUNDED_SUBSET'
                or declared.get('bbox_epsg4326') != frozen_scope.get('bbox_epsg4326')):
            raise ToolBlocked('RESEARCH_SUBSET_SCOPE_MISMATCH')
        if source == 'marine_places' and (frozen_scope.get('selection') != 'ALL_ROWS_IN_SOURCE_RELATION'
                or declared.get('scope_type') != 'FULL_DECLARED_SOURCE'
                or declared.get('bbox_epsg4326') is not None):
            raise ToolBlocked('RESEARCH_CORPUS_SCOPE_MISMATCH')
        snapshot_identity_sql(record)  # Validate identifiers before any SQL.
        return record, asset

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
        record = None
        if isinstance(self.db, ObservedDatabase) and self.snapshot_manifest is None:
            raise ToolBlocked('RESEARCH_SNAPSHOT_PIN_REQUIRED')
        if self.snapshot_manifest is not None:
            record, _ = self.snapshot_record(arguments['source'])
            if not isinstance(self.db, ObservedDatabase):
                raise ToolBlocked('RESEARCH_ATOMIC_SOURCE_GUARD_UNAVAILABLE')
        self.db.scope='coverage_metadata'
        coverage=self.coverage_check(arguments)
        self.db.scope='spatial'
        self.db.source_guard = record
        try:
            rows=self.db.query(spatial_statement(arguments['source'],arguments['relation']),arguments)
        finally:
            self.db.source_guard = None
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
        sql_observed=(True if any(x.get('sql_executed') is True or x.get('succeeded') is True for x in spatial)
                      else False if not spatial or all(x.get('sql_executed') is False for x in spatial)
                      else None)
        result['execution_observation']=canonical_trace({'observation_complete':not spatial or all(type(x.get('succeeded')) is bool for x in spatial),
            'execution_attempted':bool(calls) or bool(spatial),'tool_called':bool(calls),
            'execution_started':sql_observed,'sql_executed':sql_observed,
            'execution_succeeded':all(x.get('succeeded') is True for x in spatial) if spatial and all(type(x.get('succeeded')) is bool for x in spatial) else False if not spatial else None,
            'scope':'SPATIAL_EXECUTION_ONLY; metadata and document SQL separately recorded','db_events':events})
        return result


class ResearchBindingAdapter:
    """Verify only explicit source/tool values using actual research DB metadata."""
    def __init__(self,executor):
        self.executor=executor
        self.tool_registry={'tools':{}}
        self.layer_registry={'layers':{}}

    def verify_corpus_identity(self, binding, contract):
        source = binding.dataset_id
        if source not in SOURCES:
            return {'status':'UNVERIFIED'}
        try:
            record, asset = self.executor.snapshot_record(source)
            if (contract.get('source_sha256') != record['sha256'] or
                    contract.get('source_asset') != str(asset) or binding.relation != record['relation']):
                return {'status':'UNVERIFIED'}
            self.executor.db.scope='source_identity_metadata'
            rows=self.executor.db.query(snapshot_identity_sql(record), {})
            if (len(rows)!=1 or rows[0].get('schema_matches') is not True
                    or rows[0].get('source_sha256')!=record['sha256'] or rows[0].get('row_count')!=record['rows']):
                return {'status':'UNVERIFIED'}
            receipt={'status':'VERIFIED','dataset_id':source,'relation':record['relation'],
                     'snapshot_version':'sha256:'+record['sha256'], 'source_sha256':record['sha256'],
                     'source_asset':str(asset),'row_count':record['rows'],
                     'authority_scope':'RESEARCH_FROZEN_SOURCE_ONLY', 'real_world_completeness':'UNKNOWN',
                     'absence_certified':False}
            if source=='s101':
                bounds=(record.get('coverage') or {}).get('bbox_epsg4326')
                receipt.update(target_features=contract['target_features'], source_scope={
                    'kind':'RESEARCH_SNAPSHOT_DOMAIN','crs':'EPSG:4326',
                    'source_locator':str(asset)+'#manifest.coverage.BOUNDED_SUBSET',
                    'source_sha256':record['sha256'],'geometry_wkt':box(*bounds).wkt})
            return receipt
        except (OSError, ValueError, KeyError, TypeError, RuntimeError):
            return {'status':'UNVERIFIED'}

    def _register_source(self, source):
        record, asset = self.executor.snapshot_record(source)
        declared = self.executor.coverage.get(source, {})
        if declared.get('scope_verified') is not True:
            raise ToolBlocked('SOURCE_COVERAGE_UNVERIFIED')
        kind = (record.get('coverage') or {}).get('selection')
        if source=='s101':
            bounds=(record.get('coverage') or {}).get('bbox_epsg4326')
            if kind!='BOUNDED_SUBSET' or bounds != declared.get('bbox_epsg4326') or not isinstance(bounds,list) or len(bounds)!=4:
                raise ToolBlocked('RESEARCH_SUBSET_SCOPE_MISMATCH')
            if any(type(v) not in (int,float) or not math.isfinite(v) for v in bounds) or not (-180<=bounds[0]<bounds[2]<=180 and -90<=bounds[1]<bounds[3]<=90):
                raise ToolBlocked('RESEARCH_SUBSET_SCOPE_INVALID')
        elif source=='marine_places':
            if kind!='ALL_ROWS_IN_SOURCE_RELATION' or declared.get('scope_type')!='FULL_DECLARED_SOURCE':
                raise ToolBlocked('RESEARCH_CORPUS_SCOPE_MISMATCH')
        else:
            raise ToolBlocked('RESEARCH_SOURCE_SCOPE_UNSUPPORTED')
        contract={'kind':'s101_exact_inventory_v1' if source=='s101' else 'csv_exact_inventory_v1',
                  'dataset_id':source,
                  'source_sha256':record['sha256'],'source_asset':str(asset),
                  'snapshot_version':'sha256:'+record['sha256'],
                  'allowed_operations':[op for op in OPERATIONS.values() if op!='nearest_feature'],
                  'default_inventory_listing':True,
                  'target_features':[f['code'] for f in self.executor.catalogue['features']] if source=='s101' else [],
                  'authority_scope':'RESEARCH_FROZEN_SOURCE_ONLY'}
        self.layer_registry['layers'][source]={'physical_table':record['relation'],
                'geometry_column':'geometry','corpus_contract':contract}
        return record

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
        try:
            record = self._register_source(source)
        except (OSError, ValueError, KeyError, TypeError):
            out.blockers.append('BLOCKED_DATA: research snapshot source identity or scope unverified')
            return out
        out.data_bindings=[DataBinding(dataset_id=source,relation=relation,srid=4326,read_only=True,
                                      geometry_column='geometry',snapshot_version='sha256:'+record['sha256'])]
        out.tool_bindings=[ToolBinding(tool_id='spatial.query',operation=operation)]
        return out


def validator_for(executor, *, query=None, spatial_context=None):
    from services.orchestrator.execution_validator import validate_execution_context
    from services.orchestrator.request_constraints import capture_request_constraints
    # Capture public request input before any candidate/reviewer can change it.
    # This verifies a candidate, never supplies missing fields to its QEC.
    constraints = capture_request_constraints(query, spatial_context) if query is not None else None
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
            return validate_execution_context(qec,binding_adapter=SchemaBindingAdapter(),request_constraints=constraints)
        return validate_execution_context(qec,binding_adapter=ResearchBindingAdapter(executor),request_constraints=constraints)
    return validate
