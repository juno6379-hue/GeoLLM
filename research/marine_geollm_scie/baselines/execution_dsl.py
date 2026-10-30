"""Research-only bounded tool executor. Never grants production EXECUTION_READY.

Model plans are untrusted. SQL templates and relations are fixed; values enter via
base64-encoded JSON, not SQL interpolation. Every DB transaction is read-only.
"""
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import time

TOOLS = [
    {'tool_id': 'catalogue.search', 'arguments': {'term': 'exact S-101 feature code/name/alias'},
     'returns': 'source feature definitions and attribute bindings'},
    {'tool_id': 'documents.search', 'arguments': {'term': 'literal text fragment'},
     'returns': 'up to 5 stored document chunks, source locators; lexical retrieval only'},
    {'tool_id': 'places.resolve', 'arguments': {'name': 'exact place name'},
     'returns': 'registered source locations; candidates are not automatically disambiguated'},
    {'tool_id': 'spatial.query', 'arguments': {'relation': 'dwithin|nearest',
        'source': 'marine_places|s101|navigation_aids', 'feature_types': ['exact FC code'],
        'location_text': 'exact registered place name', 'radius_m': 'number >0 <=50000'},
     'returns': 'source IDs, distance, geometry. Requires unique source anchor and declared coverage.'},
]


class ToolBlocked(ValueError):
    pass


class ResearchDatabase:
    def __init__(self, database='scie_model_v3', container='marine-scie-pilot-db', timeout=45):
        if (container, database) != ('marine-scie-pilot-db', 'scie_model_v3'):
            raise ValueError('Only the fixed model-comparison research DB is allowed')
        self.database, self.container, self.timeout = database, container, timeout

    def query(self, body, arguments):
        encoded = base64.b64encode(json.dumps(arguments, ensure_ascii=False).encode()).decode('ascii')
        sql = ("BEGIN READ ONLY; SET LOCAL statement_timeout='30000ms'; "
            "WITH input AS (SELECT convert_from(decode('" + encoded + "','base64'),'UTF8')::jsonb AS args) "
            "SELECT coalesce(jsonb_agg(result),'[]'::jsonb)::text FROM (" + body + ") result; ROLLBACK;")
        command = ['docker', 'exec', self.container, 'psql', '-X', '-qAt', '-v', 'ON_ERROR_STOP=1',
            '-U', 'postgres', '-d', self.database, '-c', sql]
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', timeout=self.timeout)
        if result.returncode:
            # Do not include raw database diagnostics or credentials in model context.
            raise RuntimeError('RESEARCH_DB_QUERY_FAILED')
        return json.loads(result.stdout.strip())


DOCUMENT_SQL = """SELECT d.chunk_id AS source_id, d.title, d.section, d.content,
 d.source_file, d.source_url, d.page_no, d.source_sha256
 FROM knowledge.document_chunks d, input i
 WHERE strpos(lower(coalesce(d.content,'')),lower(i.args->>'term'))>0
 ORDER BY d.chunk_id LIMIT 5"""

PLACE_SQL = """SELECT 'marine:'||p.source_id AS source_id,p.name,ST_AsGeoJSON(p.geometry)::jsonb AS geometry
 FROM serving.marine_gazetteer_current p,input i WHERE lower(p.name)=lower(i.args->>'name')
 UNION ALL SELECT 'island:'||p.source_id,p.name,ST_AsGeoJSON(p.geometry)::jsonb
 FROM serving.island_gazetteer_current p,input i WHERE lower(p.name)=lower(i.args->>'name')"""

SOURCES = {
    'marine_places': ('serving.marine_gazetteer_current', 'source_id', 'name', None),
    'navigation_aids': ('serving.navigation_aid_current', 'source_id', 'name', None),
    's101': ('projection.s101_feature_current', 'feature_instance_id', 'feature_type_name', 'feature_type_name'),
}


def spatial_sql(source, nearest=False):
    relation, identifier, label, filter_column = SOURCES[source]
    filter_sql = (f"AND p.{filter_column} IN (SELECT jsonb_array_elements_text(i.args->'feature_types'))" if filter_column else '')
    lineage = ',p.properties,p.provenance' if source != 's101' else ',p.attributes'
    return f"""SELECT p.{identifier}::text AS source_id,p.{label} AS label,
 ST_AsGeoJSON(p.geometry)::jsonb AS geometry{lineage},
 ST_Distance(p.geometry::geography,ST_SetSRID(ST_GeomFromGeoJSON(i.args->>'anchor'),4326)::geography) AS distance_m
 FROM {relation} p,input i
 WHERE p.geometry IS NOT NULL AND ST_IsValid(p.geometry)
 AND ST_DWithin(p.geometry::geography,ST_SetSRID(ST_GeomFromGeoJSON(i.args->>'anchor'),4326)::geography,(i.args->>'radius_m')::double precision)
 {filter_sql} ORDER BY distance_m,p.{identifier} LIMIT {1 if nearest else 1001}"""


class Executor:
    def __init__(self, db, *, catalogue, catalogue_sha256, anchors, coverage):
        self.db = db
        path = Path(catalogue)
        if hashlib.sha256(path.read_bytes()).hexdigest() != catalogue_sha256:
            raise ValueError('CATALOGUE_HASH_MISMATCH')
        self.catalogue = json.loads(path.read_text(encoding='utf-8'))
        self.catalogue_sha256 = catalogue_sha256
        self.xml_source = None
        if self.catalogue.get('metadata', {}).get('source'):
            # These two helpers only inspect operational FC XML/parsed source.
            # Never call build()/run(), which select reference answers per case.
            from ..runners.extract_fc_reference_candidates import catalogue as read_catalogue
            self.xml_source = read_catalogue(path)
        self.anchors, self.coverage = anchors, coverage

    def call(self, tool_id, args):
        if not isinstance(args, dict):
            raise ToolBlocked('ARGUMENTS_MUST_BE_OBJECT')
        if tool_id == 'catalogue.search':
            term = self._text(args.get('term')).casefold()
            features = [f for f in self.catalogue['features'] if term in
                {str(v).casefold() for v in [f.get('code'), f.get('name'), *f.get('aliases', [])]}]
            document = None
            if self.xml_source:
                from ..runners.extract_fc_reference_candidates import record
                meta, xml_path, xml_hash, nodes, index = self.xml_source
                records = [record(f['code'], *self.xml_source) for f in features]
                bindings = []; queue = list(records); seen = set()
                while queue:
                    owner = queue.pop(0)
                    if owner['code'] in seen: continue
                    seen.add(owner['code'])
                    for binding in owner['bindings']:
                        for ref in binding['references']:
                            if ref['type'] != 'attribute': continue
                            attribute = record(ref['ref'], *self.xml_source)
                            bindings.append({'owner': owner['code'], 'attribute': ref['ref'], 'lower': binding['lower'],
                                'upper': binding['upper'], 'unbounded': binding['unbounded'], 'permitted_values': binding['permitted_values'],
                                'attribute_definition': attribute['definition'], 'global_listed_values': attribute['listed_values'],
                                'owner_locator': owner['locator'], 'attribute_locator': attribute['locator']})
                            queue.append(attribute)
                document = {'features': records, 'attribute_bindings': bindings,
                    'evidence': {'edition': meta['versionNumber'], 'source_sha256': xml_hash,
                        'source_path': meta['source'], 'locators': [r['locator'] for r in records],
                        'claim_source_links': [{'feature_code': r['code'], 'definition_locator': r['locator'], 'source_sha256': xml_hash} for r in records]}}
                if len(records) == 1: document['definition_quote'] = records[0]['definition']
            return {'rows': features, 'document_answer': document, 'source_sha256': self.catalogue_sha256,
                'postcondition': 'SOURCE_RECORDS_RETURNED' if features else 'SOURCE_SEARCH_EMPTY'}
        if tool_id == 'documents.search':
            rows = self.db.query(DOCUMENT_SQL, {'term': self._text(args.get('term'))})
            return {'rows': rows, 'retrieval': 'LEXICAL_SUBSTRING_NOT_VECTOR',
                'postcondition': 'DOCUMENT_CANDIDATES_RETURNED' if rows else 'SOURCE_SEARCH_EMPTY'}
        if tool_id == 'places.resolve':
            name = self._text(args.get('name'))
            rows = self._anchors(name)
            return {'rows': rows, 'postcondition': 'UNIQUE_ANCHOR' if len(rows) == 1 else 'AMBIGUOUS_ANCHOR' if rows else 'ANCHOR_NOT_FOUND'}
        if tool_id != 'spatial.query':
            raise ToolBlocked('UNSUPPORTED_TOOL')
        if args.get('relation') not in {'dwithin', 'nearest'}:
            raise ToolBlocked('UNSUPPORTED_RELATION_REQUIRES_EXPLICIT_AOI')
        source = args.get('source')
        if source not in SOURCES:
            raise ToolBlocked('SOURCE_NOT_ALLOWLISTED')
        radius = args.get('radius_m')
        if type(radius) not in (int, float) or not 0 < radius <= 50000:
            raise ToolBlocked('MISSING_OR_INVALID_RADIUS')
        feature_types = args.get('feature_types', [])
        allowed = {f['code'] for f in self.catalogue['features']}
        if not isinstance(feature_types, list) or any(not isinstance(t, str) or t not in allowed for t in feature_types):
            raise ToolBlocked('FEATURE_CODE_NOT_VERIFIED')
        if source == 's101' and not feature_types:
            raise ToolBlocked('MISSING_FEATURE_TYPES')
        anchors = self._anchors(self._text(args.get('location_text')))
        if len(anchors) != 1:
            raise ToolBlocked('ANCHOR_NOT_UNIQUE')
        anchor = anchors[0]
        coverage = self.coverage.get(source, {})
        # Coverage is explicitly provided by the frozen data profile, not inferred
        # from a nonempty query result or from a model answer.
        if coverage.get('scope_verified') is not True:
            raise ToolBlocked('SOURCE_COVERAGE_UNVERIFIED')
        geometry = anchor.get('geometry')
        if not isinstance(geometry, dict) or geometry.get('type') != 'Point':
            raise ToolBlocked('ANCHOR_POINT_REQUIRED')
        coordinates = geometry.get('coordinates', [])
        if len(coordinates) != 2:
            raise ToolBlocked('ANCHOR_COORDINATES_INVALID')
        bounds = coverage.get('bbox_epsg4326')
        if bounds:
            # Bounds are only a necessary check; radius containment must have been
            # approved in this source profile, never approximated from degrees.
            lon, lat = coordinates
            if not bounds[0] <= lon <= bounds[2] or not bounds[1] <= lat <= bounds[3]:
                raise ToolBlocked('ANCHOR_OUTSIDE_SNAPSHOT')
        max_radius = coverage.get('max_radius_m_by_anchor', {}).get(anchor.get('source_id'))
        if not isinstance(max_radius, (int, float)) or radius > max_radius:
            raise ToolBlocked('SEARCH_EXTENT_COVERAGE_UNVERIFIED')
        rows = self.db.query(spatial_sql(source, args['relation'] == 'nearest'),
            {'anchor': geometry, 'radius_m': radius, 'feature_types': feature_types})
        if len(rows) > 1000:
            raise ToolBlocked('RESULT_LIMIT_EXCEEDED_INCOMPLETE_SET')
        return {'rows': rows, 'source': source, 'anchor': anchor, 'radius_m': radius,
            'postcondition': 'SPATIAL_ROWS_RETURNED' if rows else 'SPATIAL_EMPTY_WITHIN_DECLARED_SOURCE_SCOPE'}

    @staticmethod
    def _text(value):
        if not isinstance(value, str) or not value.strip() or len(value) > 200:
            raise ToolBlocked('INVALID_TEXT_ARGUMENT')
        return value.strip()

    def _anchors(self, name):
        fixed = [a for a in self.anchors if name.casefold() in
            {str(s).casefold() for s in [a.get('name'), *a.get('aliases', [])]}]
        return fixed or self.db.query(PLACE_SQL, {'name': name})

    def execute(self, plan):
        start = time.perf_counter(); receipts = []
        calls = plan.get('tool_calls', []) if isinstance(plan, dict) else []
        if not isinstance(calls, list) or len(calls) > 8:
            return {'status': 'TOOL_POLICY_BLOCKED', 'reason': 'CALL_BUDGET', 'execution_success': None, 'receipts': []}
        if not calls or plan.get('action') in {'clarify', 'unsupported'}:
            return {'status': 'NOT_EXECUTED', 'reason': 'NO_EXECUTABLE_TOOL_CALLS', 'execution_success': None, 'receipts': []}
        for call in calls:
            before = time.perf_counter()
            try:
                result = self.call(call.get('tool_id'), call.get('arguments'))
                receipt = {'tool_id': call.get('tool_id'), 'status': 'TOOL_RETURNED', 'result': result}
            except ToolBlocked as exc:
                receipt = {'tool_id': call.get('tool_id'), 'status': 'TOOL_POLICY_BLOCKED', 'reason': str(exc)}
            except Exception as exc:
                receipt = {'tool_id': call.get('tool_id'), 'status': 'TOOL_ENVIRONMENT_ERROR', 'error_type': type(exc).__name__}
            receipt['latency_ms'] = (time.perf_counter()-before)*1000
            receipts.append(receipt)
        returned = sum(r['status'] == 'TOOL_RETURNED' for r in receipts)
        return {'status': 'TOOLS_RETURNED' if returned == len(receipts) else 'TOOLS_PARTIAL' if returned else 'TOOLS_NOT_COMPLETED',
            'tool_calls_attempted': len(receipts), 'tool_calls_executed': returned, 'receipts': receipts,
            'execution_success': None, 'semantic_correct': None, 'spatial_correct': None, 'evidence_correct': None,
            'task_postconditions': 'NOT_SCORED_PENDING_APPROVED_CONTRACT', 'latency_ms': (time.perf_counter()-start)*1000}
