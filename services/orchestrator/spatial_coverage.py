"""Server-pinned source coverage checks, independent of benchmark answers.

Object extents are never treated as a coverage boundary. Missing declarations
remain UNKNOWN. A declaration must match both a local immutable asset and the
validated data binding snapshot before it can establish scope.
"""
import hashlib
import json
import math
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
