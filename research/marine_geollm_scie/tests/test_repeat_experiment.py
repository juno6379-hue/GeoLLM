import json
from pathlib import Path
import pytest

from research.marine_geollm_scie.runners.repeat_experiment import require_unchanged, sha, validate_stage
from research.marine_geollm_scie.runners.repeat_analysis import summarize
from research.marine_geollm_scie.runners.independent_review_package import build


def test_frozen_source_edit_rejected(tmp_path):
    p = tmp_path/'source.py'; p.write_text('old')
    hashes = {str(p): sha(p)}
    require_unchanged(hashes)
    p.write_text('changed')
    with pytest.raises(ValueError, match='Frozen artifact'):
        require_unchanged(hashes)


def test_baseline_incomplete_manifest_rejected_even_after_exit_zero(tmp_path):
    (tmp_path/'manifest.json').write_text(json.dumps({'status': 'INCOMPLETE_ROW_LIMIT'}))
    with pytest.raises(ValueError, match='completion/integrity'):
        validate_stage(tmp_path, 'baseline')


def test_graph_degraded_warmup_rejected(tmp_path):
    (tmp_path/'model_graph_manifest.json').write_text(json.dumps({'worker_status': 'EXECUTION_OBSERVED',
        'observed_rows': 18, 'source_unchanged_after': True,
        'warmup_verification': {'status': 'DEGRADED_WARMUP'}}))
    with pytest.raises(ValueError, match='warmup'):
        validate_stage(tmp_path, 'graph')


def test_graph_duplicate_case_rejected(tmp_path):
    (tmp_path/'model_graph_manifest.json').write_text(json.dumps({'worker_status': 'EXECUTION_OBSERVED',
        'observed_rows': 18, 'source_unchanged_after': True,
        'warmup_verification': {'status': 'WARMUP_OBSERVED_WITHOUT_PROXY_ERRORS'}}))
    (tmp_path/'production_rows.jsonl').write_text(''.join(json.dumps({'case_id': 'same'})+'\n' for _ in range(18)))
    with pytest.raises(ValueError, match='incomplete'):
        validate_stage(tmp_path, 'graph')


def rows(case, values):
    return [{'case_id': case, 'method': 'P', 'external_repeat': i,
             'all_applicable_checks_pass': v, 'latency_ms': i+1} for i, v in enumerate(values)]


def test_repeat_is_not_independent_sample_and_equivalent_cases_clustered():
    refs = {c: {'equivalence_group': 'same_location'} for c in ('a', 'b', 'c')}
    result = summarize(rows('a', [True]*5)+rows('b', [False]*5)+rows('c', [True]*5), refs)
    method = result['methods'][0]
    assert method['observed_unique_cases'] == 3
    assert method['observed_equivalence_clusters'] == 1
    assert method['component_cluster_macro_measured_only'] == pytest.approx(2/3)
    assert method['full_semantic_accuracy'] is None


def test_missing_observation_not_zero_and_not_dropped_from_denominator():
    result = summarize(rows('a', [True, True, None, False, True]), {'a': {'equivalence_group': 'a'}})
    r = result['case_repeats'][0]
    assert r['unmeasured_repeats'] == 1
    assert r['component_pass_fraction_measured_only'] == .75
    assert r['component_pass_fraction_complete'] is None
    assert result['methods'][0]['unmeasured_clusters'] == 1


def test_absent_repeat_cannot_be_complete():
    result = summarize(rows('a', [True]*4), {'a': {'equivalence_group': 'a'}})
    assert not result['case_repeats'][0]['repeat_schedule_complete']
    assert result['case_repeats'][0]['component_pass_fraction_complete'] is None


def test_duplicate_external_repeat_rejected():
    with pytest.raises(ValueError, match='Duplicate'):
        summarize(rows('a', [True])*2, {'a': {'equivalence_group': 'a'}})


def test_absent_equivalence_cluster_is_reported_missing():
    result = summarize(rows('a', [True]*5), {'a': {'equivalence_group': 'a'}, 'b': {'equivalence_group': 'b'}})
    method = result['methods'][0]
    assert method['observed_equivalence_clusters'] == 1
    assert method['expected_equivalence_clusters'] == 2
    assert method['unmeasured_clusters'] == 1


def test_review_package_is_blank_and_ai_reference_separate(tmp_path):
    source = tmp_path/'contracts.jsonl'
    source.write_text(''.join(json.dumps({'case_id': str(i), 'query': 'question', 'equivalence_group': str(i),
        'human_approval': True, 'machine_checks': [{'expected': 'candidate'}],
        'document_scope': {'evidence_requirements': {'edition': '2.0.0', 'source_path': 'source.xml',
            'source_sha256': 'abc', 'locators': ['AI_selected_feature'], 'claim_source_links_required': True}},
        'spatial_reference': {'object_ids': ['AI_answer'], 'objects': [{'id': 'AI_answer'}], 'reference_crs': 'EPSG:4326'}})+'\n' for i in range(18)))
    output = tmp_path/'review'
    manifest = build(source, output)
    forms = [json.loads(s) for s in (output/'reviewer_A_blank.jsonl').read_text().splitlines()]
    assert manifest['independent_reviews_completed'] == 0
    assert manifest['reviewers_assigned_user_confirmed'] is True
    assert all(r['human_approval'] is False and r['required_tasks'] is None for r in forms)
    assert all('machine_checks' not in r and 'candidate_contract' not in r for r in forms)
    assert all('object_ids' not in r['spatial_source_condition'] and 'objects' not in r['spatial_source_condition'] for r in forms)
    assert all('locators' not in r['source_references'] and 'claim_source_links_required' not in r['source_references'] for r in forms)
    assert all(r['source_references']['source_path'] == 'source.xml' for r in forms)
    assert (output/'검수자A_18문항_독립검수_빈양식_KR.md').is_file()
    with pytest.raises(FileExistsError):
        build(source, output)
