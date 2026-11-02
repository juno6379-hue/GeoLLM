"""Compare a server-pinned S-101 inventory with the live query transaction.

An inventory is not evidence of real-world completeness. No manifest is created
or approved here; absent/changed manifests fail closed. Object extents are not
accepted as a declared dataset scope.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RELATION = 'projection.s101_feature_current'
FIELDS = ('feature_instance_id', 'dataset_id', 'dataset_version_id',
          'feature_type_name', 'attributes', 'geometry_identity')


def inventory_digest(rows):
    return hashlib.sha256(json.dumps(rows, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def verify_s101_corpus(cursor, binding, contract, *, root=ROOT):
    receipt = {'status': 'UNVERIFIED', 'dataset_id': binding.dataset_id,
               'relation': binding.relation, 'absence_certified': False}
    try:
        kind = contract.get('kind')
        targeted = kind == 's101_target_inventory_v2'
        if (kind not in ('s101_exact_inventory_v1', 's101_target_inventory_v2')
                or binding.relation != RELATION or binding.geometry_column != 'geometry'
                or binding.srid != 4326):
            raise ValueError('unsupported source binding')
        base = Path(root).resolve()
        path = (base / contract['source_asset']).resolve()
        if not path.is_relative_to((base / 'data/source_inventory').resolve()):
            raise ValueError('unregistered inventory path')
        raw = path.read_bytes()
        source_hash = hashlib.sha256(raw).hexdigest()
        if source_hash != contract['source_sha256']:
            raise ValueError('changed source inventory')
        source = json.loads(raw)
        scope = source['source_scope']
        expected = source['rows']
        if (source.get('schema_version') != kind
                or source.get('relation') != RELATION
                or source.get('dataset_id') != binding.dataset_id
                or scope.get('kind') != 'SOURCE_DECLARED_DATA_COVERAGE'
                or scope.get('crs') != 'EPSG:4326'
                or not scope.get('source_locator') or not scope.get('geometry_wkt')
                or not isinstance(expected, list) or not expected
                or any(set(row) != set(FIELDS) for row in expected)
                or len({row['feature_instance_id'] for row in expected}) != len(expected)):
            raise ValueError('inventory declaration incomplete')
        expected = sorted(expected, key=lambda row: str(row['feature_instance_id']))
        snapshot = 'sha256:' + inventory_digest(expected)
        if source.get('snapshot_version') != snapshot or contract.get('snapshot_version') != snapshot:
            raise ValueError('inventory snapshot mismatch')
        target_features = set(contract.get('target_features') or [])
        if targeted:
            if not target_features or target_features != set(source.get('target_features') or []):
                raise ValueError('Target inventory contract mismatch')
            if any(row['feature_type_name'] not in target_features for row in expected):
                raise ValueError('Out-of-contract target inventory row')
            from shapely import wkt
            from services.orchestrator.s101_source_coverage import reconstruct_coverage
            proof = source['source_proof']
            raw_path = (base / proof['source_asset']).resolve()
            if not raw_path.is_relative_to((base / 'data/source_inventory').resolve()):
                raise ValueError('Unregistered original source path')
            raw = raw_path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != proof['source_sha256']:
                raise ValueError('Original source cell changed')
            original, decoded = reconstruct_coverage(raw, proof['feature_record_id'])
            if not original.equals(wkt.loads(scope['geometry_wkt'])):
                raise ValueError('Declared scope differs from original DataCoverage')
            cursor.execute('''SELECT d.source_sha256,d.dataset_name,ST_AsText(f.geometry)
                FROM public.s101_dataset d JOIN projection.s101_feature_current f
                  ON f.dataset_id=d.dataset_id
                WHERE d.dataset_id=%s AND f.feature_instance_id=%s
                  AND f.feature_type_name='DataCoverage' ''',
                (proof['dataset_id'], proof['coverage_feature_instance_id']))
            source_rows = cursor.fetchall()
            if len(source_rows) != 1:
                raise ValueError('Live original coverage identity missing')
            row = source_rows[0]
            if isinstance(row, dict):
                row = [row['source_sha256'],row['dataset_name'],row['st_astext']]
            if row[0] != proof['source_sha256'] or row[1] != proof['dataset_name'] or not original.equals(wkt.loads(row[2])):
                raise ValueError('Live original coverage lineage changed')
        sql = '''SELECT feature_instance_id::text, dataset_id::text,
            dataset_version_id::text, feature_type_name, attributes,
            ST_AsEWKB(geometry)::text AS geometry_identity,
            COALESCE(ST_SRID(geometry)=4326 AND ST_IsValid(geometry)
                AND NOT ST_IsEmpty(geometry), false) AS geometry_valid
            FROM projection.s101_feature_current'''
        if targeted:
            sql += ' WHERE feature_type_name=ANY(%s)'
        sql += ' ORDER BY feature_instance_id::text'
        if targeted:
            cursor.execute(sql, (sorted(target_features),))
        else:
            cursor.execute(sql)
        names = [column[0] for column in cursor.description]
        actual = [dict(row) if isinstance(row, dict) else dict(zip(names, row))
                  for row in cursor.fetchall()]
        # Invalid/non-spatial rows must be explicitly represented in the source;
        # do not silently drop rows to manufacture a matching subset.
        projected = [{key: row[key] for key in FIELDS} for row in actual]
        if projected != expected:
            raise ValueError('live source inventory changed')
        if not target_features or any(row['geometry_valid'] is not True for row in actual
                                      if row['feature_type_name'] in target_features):
            raise ValueError('target geometry unavailable')
        if not target_features <= {row['feature_type_name'] for row in actual}:
            raise ValueError('target not in source inventory')
        receipt.update(status='VERIFIED', source_asset=contract['source_asset'],
                       source_sha256=source_hash, row_count=len(actual),
                       snapshot_version=snapshot, target_features=sorted(target_features),
                       source_scope={**scope, 'source_sha256': source_hash},
                       verification='full_target_inventory_and_original_DataCoverage' if targeted else 'full_pinned_inventory_live_membership_attributes_ewkb',
                       inventory_scope='ALL_ROWS_OF_REGISTERED_TARGET_TYPES' if targeted else 'ALL_PROJECTION_ROWS',
                       geographic_completeness=False)
    except Exception as exc:
        receipt.update(reason='SOURCE_IDENTITY_UNVERIFIED', error_type=type(exc).__name__)
    return receipt
