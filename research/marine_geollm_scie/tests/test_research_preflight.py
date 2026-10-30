import json
from pathlib import Path
import pytest
from research.marine_geollm_scie.runners.research_preflight import audit, run, sha256


def write(root, name, value):
    path = root / name
    path.write_text(json.dumps(value), encoding='utf-8')
    return {'path': name, 'sha256': sha256(path)}


def base(tmp_path):
    source = write(tmp_path, 'source.json', {'real': 'test fixture'})
    manifest = write(tmp_path, 'manifest.json', {'status': 'LOADED_VERIFIED', 'captured_at': 'fixture', 'source_transaction': '1',
        'db_identity': {'container': 'marine-scie-pilot-db', 'database': 'scie_binding_v2'},
        'relations': [{'relation': 'marine', 'columns': [['id', 'integer'], ['geometry', 'geometry']], 'rows': 1, 'sha256': source['sha256']}],
        'loaded_verification': [{'relation': 'marine', 'rows': 1, 'roundtrip_sha256': source['sha256'], 'content_match': True}],
        'files': [source], 'bbox_epsg4326': [130, 36, 133, 39]})
    refs = write(tmp_path, 'refs.jsonl', {'case_id': 'Q4', 'human_approval': True, 'annotation_status': 'GOLD',
        'adjudication_status': 'APPROVED', 'review_kind': 'USER_APPROVED_AI_ASSISTED', 'independent_expert_review': False,
        'spatial': {'object_ids': ['real:1'], 'dataset_snapshot_sha256': 'a'*64, 'oracle_sha256': 'b'*64}})
    probe = write(tmp_path, 'probe.json', {'captured': True})
    return {'snapshot_manifest': manifest, 'references': refs, 'required_relations': {'marine': ['id', 'geometry']},
        'expected_db_identity': {'container': 'marine-scie-pilot-db', 'database': 'scie_binding_v2'},
        'environment_observation': {'status': 'AVAILABLE', 'observed_at': 'fixture', 'artifact': probe},
        'profile': {'embedding_required': False, 'embedding_enabled': False},
        'cases': [{'case_id': 'Q4', 'required_components': ['spatial'], 'requires_spatial_input': True,
            'aoi_bbox_epsg4326': [131, 37, 132, 38], 'coverage_verified': True, 'coverage_evidence_sha256': 'c'*64}]}


def check(result, key):
    return next(c for c in result['checks'] if c['key'] == key)


def test_recorded_readiness_is_not_independent_gold_or_score(tmp_path):
    result = audit(base(tmp_path), tmp_path)
    assert result['status'] == 'READY'
    assert check(result, 'Q4')['independent_expert_review'] is False
    assert not result['scientific_scores_generated']
    assert not result['model_errors_inferred']


def test_tamper_and_missing_relation_block(tmp_path):
    config = base(tmp_path)
    (tmp_path/'source.json').write_text('tampered', encoding='utf-8')
    config['required_relations']['marine'].append('missing')
    result = audit(config, tmp_path)
    assert check(result, 'source_file:0')['status'] == 'BLOCKED'
    assert check(result, 'marine')['missing_columns'] == ['missing']


def test_aoi_and_coverage_unknown_never_zero_result(tmp_path):
    config = base(tmp_path)
    config['cases'][0].pop('aoi_bbox_epsg4326')
    config['cases'][0].pop('coverage_verified')
    result = audit(config, tmp_path)
    assert check(result, 'Q4:aoi')['status'] == 'UNKNOWN'
    assert check(result, 'Q4:completeness')['status'] == 'UNKNOWN'
    assert result['status'] == 'NOT_READY'
    assert 'spatial_correct' not in result


def test_v4_draft_does_not_inherit_parent_approval(tmp_path):
    config = base(tmp_path)
    config['references'] = write(tmp_path, 'v4.jsonl', {'case_id': 'Q4', 'source_human_approval': True,
        'human_approval': False, 'annotation_status': 'DRAFT', 'evaluation_enabled': False})
    result = audit(config, tmp_path)
    assert check(result, 'Q4')['status'] == 'BLOCKED'
    assert check(result, 'Q4:spatial')['status'] == 'BLOCKED'
    assert check(result, 'Q4:enabled')['status'] == 'BLOCKED'


def test_environment_failure_and_disabled_embedding_separate(tmp_path):
    config = base(tmp_path)
    config['environment_observation'] = {'status': 'UNAVAILABLE'}
    result = audit(config, tmp_path)
    assert check(result, 'runtime_probe')['category'] == 'ENVIRONMENT'
    assert check(result, 'runtime_probe')['status'] == 'BLOCKED'
    assert check(result, 'embedding')['status'] == 'PASS'


def test_outside_snapshot_is_coverage_block_and_no_overwrite(tmp_path):
    config = base(tmp_path)
    config['cases'][0]['aoi_bbox_epsg4326'] = [129, 37, 132, 38]
    path = tmp_path/'config.json'; path.write_text(json.dumps(config), encoding='utf-8')
    result = run(path, tmp_path/'output', tmp_path)
    assert check(result, 'Q4:bbox')['status'] == 'BLOCKED'
    with pytest.raises(FileExistsError):
        run(path, tmp_path/'output', tmp_path)


def test_loaded_content_flag_does_not_override_mismatched_hash(tmp_path):
    config = base(tmp_path)
    path = tmp_path/'manifest.json'
    manifest = json.loads(path.read_text())
    manifest['loaded_verification'][0]['roundtrip_sha256'] = 'wrong'
    config['snapshot_manifest'] = write(tmp_path, 'manifest.json', manifest)
    result = audit(config, tmp_path)
    load = [c for c in result['checks'] if c['category'] == 'DATABASE_LOAD_OBSERVATION']
    assert load[0]['status'] == 'BLOCKED'


def test_relation_csv_relative_to_manifest_directory(tmp_path):
    config = base(tmp_path)
    folder = tmp_path/'snapshot'; folder.mkdir()
    data = folder/'rows.csv'; data.write_text('id\n1\n', encoding='utf-8')
    manifest = json.loads((tmp_path/'manifest.json').read_text())
    manifest['relations'][0].update(csv_path='rows.csv', sha256=sha256(data))
    manifest['loaded_verification'][0]['roundtrip_sha256'] = sha256(data)
    config['snapshot_manifest'] = write(tmp_path, 'snapshot/manifest.json', manifest)
    result = audit(config, tmp_path)
    assert check(result, 'marine:csv')['status'] == 'PASS'


def test_retrieval_observations_keep_model_profile_unknown(tmp_path):
    config = base(tmp_path)
    rows = write(tmp_path, 'retrieval.jsonl', {'status': 'RETRIEVAL_COMPLETED', 'result_count': 3})
    manifest = write(tmp_path, 'retrieval_manifest.json', {'snapshot_sha256': config['snapshot_manifest']['sha256'],
        'rows_sha256': rows['sha256'], 'rows': 1, 'embedding_calls': 1, 'stored_embedding_model_profile_verified': False})
    config['observations'] = [{'kind': 'RETRIEVAL_COMPONENT', 'manifest': manifest, 'rows': rows}]
    result = audit(config, tmp_path)
    assert check(result, 'RETRIEVAL_COMPONENT:rows')['status'] == 'PASS'
    assert next(c for c in result['checks'] if c['category'] == 'MODEL_PROFILE')['status'] == 'UNKNOWN'
    assert result['observations'][0]['accuracy_inferred'] is False
    assert result['observations'][0]['returned_candidate_counts'] == [3]


def test_observation_from_different_snapshot_is_blocked(tmp_path):
    config = base(tmp_path)
    manifest = write(tmp_path, 'probe_manifest.json', {'snapshot_manifest_sha256': 'not_the_snapshot', 'observations': []})
    config['observations'] = [{'kind': 'DB_PROBE', 'manifest': manifest}]
    result = audit(config, tmp_path)
    assert check(result, 'DB_PROBE')['status'] == 'BLOCKED'
