"""Server-pinned source coverage checks, independent of benchmark answers.

Object extents are never treated as a coverage boundary. Missing declarations
remain UNKNOWN. A declaration must match both a local immutable asset and the
validated data binding snapshot before it can establish scope.
"""
import hashlib
import json
import math
import re
from pathlib import Path

from shapely import wkt
from shapely.geometry import box
from shapely.errors import ShapelyError

ROOT = Path(__file__).resolve().parents[2]
SPATIAL_OPERATIONS = {
    'feature_search_by_radius', 'feature_dwithin', 'source_attribute_search',
    'feature_within_area', 'spatial_feature_search', 'feature_search_by_area',
    'nearest_feature', 'nearest_feature_search',
}


def _explicit_finite_inventory_scope(query):
    """Recognize explicit membership in a finite inventory, not vague 'data'.

    This only resolves the request scope. Registry/source/geometry verification
    remains mandatory before any source-bound execution can be authorized.
    """
    return bool(re.search(
        r'(?:\b20\d{2}\s*CSV|원천\s*목록|등록된\s*(?:데이터셋|데이터|목록))\s*'
        r'(?:에\s*(?:수록|등록|포함)된|(?:내|안)의)|'
        r'\b(?:in|from|within)\s+(?:the\s+)?(?:registered|pinned|frozen)\s+'
        r'(?:dataset|source\s+inventory|corpus)\b|'
        r'\b(?:in|from|within)\s+(?:the\s+)?20\d{2}\s+CSV\b', query, re.I))


def _finite_exhaustiveness(query):
    """Every exhaustive clause must bind its own finite source.

    A source phrase in an explanatory clause cannot authorize a different
    unbounded search. Ambiguous coordinated requests remain blocked.
    """
    exhaustive = r'전체|모든|전부|빠짐없이|누락\s*없이|without\s+omission|\b(?:all|every|complete)\b'
    clauses = re.split(r'[;\n!?。]|(?<!\d)\.(?!\d)|그리고|또한|하지만|하고|찾고|보여주고|알려주고|'
                       r'\b(?:and|also|but)\b', query, flags=re.I)
    demanding = [clause for clause in clauses if re.search(exhaustive, clause, re.I)]
    def bound(clause):
        if not _explicit_finite_inventory_scope(clause):
            return False
        # The finite source may qualify a spatially restricted exhaustive set.
        # Only a location/radius modifier may intervene, never another task or
        # object used as evidence for an unrelated exhaustive request.
        if re.search(r'전체|모든|전부|빠짐없이|누락\s*없이', clause):
            matches = re.finditer(
                r'(?:\b20\d{2}\s*CSV|원천\s*목록|등록된\s*(?:데이터셋|데이터|목록))\s*'
                r'(?:에\s*(?:수록|등록|포함)된|(?:내|안)의)\s*(.*?)\s*(?:전체|모든|전부)', clause, re.I)
            for match in matches:
                modifier = match.group(1).strip()
                if re.search(r'참고|설명|조회|알려|보여|찾|기반', modifier):
                    continue
                if re.fullmatch(
                    r'(?:[가-힣A-Za-z0-9_-]{1,30}\s*(?:주변|부근|근처)\s*)?'
                    r'(?:(?:반경\s*)?\d+(?:\.\d+)?\s*(?:km|m|킬로미터|미터)\s*'
                    r'(?:(?:이내|내)(?:의)?)?\s*)?', modifier, re.I):
                    return True
            return False
        # English allows a finite target noun phrase followed by source scope.
        return bool(re.search(
            r'\b(?:all|every|complete)\s+(?:[A-Za-z0-9_-]+\s+){1,8}'
            r'(?:in|from|within)\s+(?:the\s+)?(?:(?:registered|pinned|frozen)\s+'
            r'(?:dataset|source\s+inventory|corpus)|20\d{2}\s+CSV)\b', clause, re.I))
    return bool(demanding) and all(bound(clause) for clause in demanding)


def requests_source_corpus(qec, *, registered_default=False):
    """Determine whether a bounded inventory listing can answer this task.

    An exhaustive finite inventory listing is not real-world completeness.
    Explicit world-completeness/nearest requirements cannot be narrowed by slots.
    """
    operation = qec.route_plan.get('analysis_type') or qec.slots.analysis_type or qec.slots.operation
    if operation in {'nearest_feature', 'nearest_feature_search'}:
        return False
    if qec.slots.filters.get('require_complete_coverage') is True:
        return False
    query = qec.original_query or ''
    if re.search(r'실세계|실제\s*(?:존재|전체|해역|바다)|전\s*해역|전세계|가장\s*가까|최근접|'
                 r'real[- ]world|\b(?:nearest|closest)\b', query, re.I):
        return False
    finite_inventory = _explicit_finite_inventory_scope(query)
    if (re.search(r'전체|모든|전부|빠짐없이|누락\s*없이|without\s+omission|'
                  r'\b(?:all|every|complete)\b', query, re.I) and not _finite_exhaustiveness(query)):
        return False
    if finite_inventory:
        return True
    if (operation in {'feature_dwithin', 'feature_search_by_radius'}
            and set(qec.slots.target_layers) == {'marine_gazetteer'}
            and not qec.slots.target_features):
        return True
    if registered_default and operation in {'feature_dwithin', 'feature_search_by_radius'}:
        # A server registered finite inventory can be the default listing source.
        # The receipt/result must retain SOURCE_CORPUS and never imply absence.
        return True
    return bool(re.search(
        r'(?:자료|데이터|목록|원천|CSV|데이터베이스|DB)\s*(?:에\s*(?:수록|등록|포함)|에서|내에서)|'
        r'(?:수록|등록)된\s*(?:해양)?지명|'
        r'\b(?:in|from|within)\s+(?:the\s+)?(?:registered\s+|source\s+)?(?:dataset|corpus|csv|database)\b',
        query, re.I))


def assess_source_corpus(qec, layer_registry, verifier):
    """Verify a finite source inventory, without certifying geographic absence.

    Called only after geographic coverage is UNKNOWN; an approved boundary's
    OUT_OF_COVERAGE/PARTIAL decision must never be overridden by this path.
    ``verifier`` is server code which checks the live relation against its source.
    """
    layers = (layer_registry or {}).get('layers') or {}
    default_inventory = bool(qec.data_bindings) and all(
        ((layers.get(binding.dataset_id) or {}).get('corpus_contract') or {}).get('kind') in ('s101_exact_inventory_v1', 's101_target_inventory_v2', 'csv_exact_inventory_v1')
        and ((layers.get(binding.dataset_id) or {}).get('corpus_contract') or {}).get('default_inventory_listing') is True
        for binding in qec.data_bindings)
    if not callable(verifier) or not requests_source_corpus(qec, registered_default=default_inventory):
        return None
    operation = qec.route_plan.get('analysis_type') or qec.slots.analysis_type or qec.slots.operation
    try:
        requested = _query_envelope(qec)
        if requested is None or not qec.data_bindings:
            return None
    except (ValueError, TypeError, ShapelyError):
        return None
    sources = []
    domain_relations = []
    for binding in qec.data_bindings:
        layer = (layer_registry.get('layers') or {}).get(binding.dataset_id) or {}
        contract = layer.get('corpus_contract') or {}
        # Only an audited verifier and its exact source layer may be used.
        research_gazetteer = (binding.dataset_id == 'marine_places'
                              and contract.get('dataset_id') == 'marine_places'
                              and (qec.slots.filters or {}).get('source') == 'marine_places'
                              and not qec.slots.target_layers)
        gazetteer = (contract.get('kind') == 'csv_exact_inventory_v1'
                     and (binding.dataset_id == 'marine_gazetteer' or research_gazetteer)
                     and binding.relation == 'serving.marine_gazetteer_current'
                     and not qec.slots.target_features
                     and (set(qec.slots.target_layers) == {'marine_gazetteer'} or research_gazetteer))
        s101 = (contract.get('kind') in ('s101_exact_inventory_v1', 's101_target_inventory_v2')
                and binding.relation == 'projection.s101_feature_current'
                and bool(qec.slots.target_features)
                and set(qec.slots.target_features) <= set(contract.get('target_features') or [])
                and not qec.slots.target_layers)
        if (not (gazetteer or s101)
                or binding.relation != layer.get('physical_table')
                or binding.geometry_column != layer.get('geometry_column')
                or binding.srid != 4326
                or operation not in contract.get('allowed_operations', [])):
            return None
        try:
            observed = verifier(binding, contract)
        except Exception:
            # A source check outage must never turn into execution permission.
            return None
        if (not isinstance(observed, dict) or observed.get('status') != 'VERIFIED'
                or observed.get('dataset_id') != binding.dataset_id
                or observed.get('relation') != binding.relation
                or not re.fullmatch(r'sha256:[0-9a-f]{64}', str(observed.get('snapshot_version', '')))
                or not re.fullmatch(r'[0-9a-f]{64}', str(observed.get('source_sha256', '')))
                or observed.get('source_sha256') != contract.get('source_sha256')
                or observed.get('source_asset') != contract.get('source_asset')
                or type(observed.get('row_count')) is not int
                or observed['row_count'] <= 0):
            return None
        if research_gazetteer and (observed.get('snapshot_version') != contract.get('snapshot_version')
                                   or binding.snapshot_version != contract.get('snapshot_version')):
            return None
        if s101:
            scope = observed.get('source_scope') or {}
            try:
                geometry = wkt.loads(scope['geometry_wkt'])
                if (scope.get('kind') not in {'SOURCE_DECLARED_DATA_COVERAGE', 'RESEARCH_SNAPSHOT_DOMAIN'}
                        or scope.get('crs') != 'EPSG:4326'
                        or not scope.get('source_locator')
                        or scope.get('source_sha256') != contract.get('source_sha256')
                        or geometry.geom_type not in ('Polygon', 'MultiPolygon')
                        or geometry.is_empty or not geometry.is_valid
                        or not all(math.isfinite(value) for value in geometry.bounds)
                        or not (-180 <= geometry.bounds[0] <= geometry.bounds[2] <= 180
                                and -90 <= geometry.bounds[1] <= geometry.bounds[3] <= 90)
                        or not set(qec.slots.target_features) <= set(observed.get('target_features') or [])
                        or observed.get('snapshot_version') != contract.get('snapshot_version')):
                    return None
                domain_relations.append('CONTAINS_QUERY' if geometry.covers(requested) else
                                        'PARTIAL' if geometry.intersects(requested) else 'OUTSIDE')
            except (KeyError, ValueError, TypeError, ShapelyError):
                return None
        sources.append(dict(observed))
    domain = ('OUTSIDE' if 'OUTSIDE' in domain_relations else 'PARTIAL' if 'PARTIAL' in domain_relations
              else 'CONTAINS_QUERY' if domain_relations else 'NOT_DECLARED')
    status = 'OUT_OF_COVERAGE' if domain == 'OUTSIDE' else 'PARTIAL' if domain == 'PARTIAL' else 'CORPUS_VERIFIED'
    research_domain = any((source.get('source_scope') or {}).get('kind') == 'RESEARCH_SNAPSHOT_DOMAIN'
                          for source in sources)
    return {'authority': 'ServerSourceCoverage', 'version': '3',
            'status': status, 'geographic_coverage': 'UNKNOWN',
            'source_corpus_status': 'VERIFIED',
            'geographic_coverage_status': (('RESEARCH_SNAPSHOT_DOMAIN_' if research_domain else 'SOURCE_DECLARED_DOMAIN_')
                                          + domain) if domain != 'NOT_DECLARED' else 'SOURCE_DOMAIN_NOT_DECLARED',
            'real_world_completeness': 'UNKNOWN',
            'query_scope': 'SOURCE_CORPUS', 'required': True,
            'absence_certified': False, 'sources': sources}


def _query_envelope(qec):
    if qec.slots.crs != 'EPSG:4326':
        return None
    raw = qec.slots.reference_geometry or (qec.spatial.get('spatial_context') or {}).get('geometry')
    if not raw:
        return None
    geom = wkt.loads(raw)
    if geom.is_empty or not geom.is_valid:
        return None
    xmin, ymin, xmax, ymax = geom.bounds
    distance = qec.slots.distance_m
    if distance is not None:
        if not math.isfinite(distance) or not 0 < distance <= 50000:
            return None
        # Conservative EPSG:4326 envelope, not a spatial-result distance oracle.
        dy = distance / 110000
        latitude = max(abs(ymin - dy), abs(ymax + dy))
        if latitude >= 89:
            return None
        dx = distance / (110000 * math.cos(math.radians(latitude)))
        xmin, xmax, ymin, ymax = xmin-dx, xmax+dx, ymin-dy, ymax+dy
    if not (-180 <= xmin <= xmax <= 180 and -90 <= ymin <= ymax <= 90):
        return None
    return geom if distance is None else box(xmin, ymin, xmax, ymax)


def assess_coverage(qec, layer_registry, *, root=ROOT):
    """Only server-owned layer metadata is read; QEC supplied VERIFIED is ignored."""
    operation = qec.route_plan.get('analysis_type') or qec.slots.analysis_type or qec.slots.operation
    # Execution scope is a server policy, never an opt-in supplied by the plan.
    required = operation in SPATIAL_OPERATIONS
    receipt = {'authority': 'ServerSourceCoverage', 'version': '2', 'status': 'UNKNOWN',
               'required': required, 'absence_certified': False, 'sources': []}
    try:
        requested = _query_envelope(qec)
    except (ValueError, TypeError, ShapelyError):
        requested = None
    if requested is None or not qec.data_bindings:
        receipt['reason'] = 'REFERENCE_OR_SOURCE_UNRESOLVED'
        return receipt
    layers = layer_registry.get('layers', {}) if isinstance(layer_registry, dict) else {}
    statuses = []
    for binding in qec.data_bindings:
        entry = {'dataset_id': binding.dataset_id, 'relation': binding.relation, 'status': 'UNKNOWN'}
        layer = layers.get(binding.dataset_id) or {}
        declaration = layer.get('coverage_contract') or {}
        try:
            path = (Path(root) / declaration['path']).resolve()
            if not path.is_relative_to(Path(root).resolve()):
                raise ValueError('asset outside approved root')
            raw = path.read_bytes()
            digest = hashlib.sha256(raw).hexdigest()
            if digest != declaration['sha256']:
                raise ValueError('asset digest mismatch')
            contract = json.loads(raw)
            if (contract.get('approval_status') != 'APPROVED'
                    or not contract.get('source_locator')
                    or not binding.snapshot_version
                    or contract.get('snapshot_version') != binding.snapshot_version
                    or contract.get('relation') != binding.relation
                    or contract.get('dataset_id') != binding.dataset_id
                    or layer.get('physical_table') != binding.relation
                    or contract.get('crs') != 'EPSG:4326'
                    or not set(qec.slots.target_features)
                    or not set(qec.slots.target_features) <= set(contract.get('target_features', []))):
                raise ValueError('source identity/snapshot/features unverified')
            coverage = wkt.loads(contract['geometry_wkt'])
            if coverage.geom_type not in ('Polygon', 'MultiPolygon') or coverage.is_empty or not coverage.is_valid:
                raise ValueError('invalid coverage polygon')
            status = 'ADEQUATE' if coverage.covers(requested) else 'PARTIAL' if coverage.intersects(requested) else 'OUT_OF_COVERAGE'
            # A boundary covering the point alone cannot establish global nearest.
            if operation in {'nearest_feature', 'nearest_feature_search'} and contract.get('nearest_domain_complete') is not True:
                status = 'UNKNOWN' if status == 'ADEQUATE' else status
            entry.update(status=status, contract_sha256=digest, snapshot_version=binding.snapshot_version,
                         source_locator=contract['source_locator'])
        except (OSError, KeyError, ValueError, TypeError, ShapelyError):
            entry['reason'] = 'COVERAGE_CONTRACT_UNVERIFIED'
        statuses.append(entry['status'])
        receipt['sources'].append(entry)
    receipt['status'] = next((s for s in ('OUT_OF_COVERAGE', 'PARTIAL', 'UNKNOWN') if s in statuses), 'ADEQUATE')
    return receipt
