import copy,json
from pathlib import Path
from tools.scie_results_ui.prepare_holdout import OUT,DEV,evaluation_gate,rows,sha

def test_counts_and_reserved_not_evaluated():
    s=json.loads((OUT/'summary.json').read_text(encoding='utf-8'))
    assert (s['main_cases'],s['rq2_fault_cases'],s['rq4_recovery_cases'])==(18,12,8)
    assert not s['evaluation_executed'] and not s['human_review_complete']
    assert not evaluation_gate(OUT)['evaluation_ready']

def test_split_and_sources():
    q=rows(OUT/'queries.jsonl');d=rows(DEV/'queries.jsonl')
    for k in ['case_id','query','equivalence_group']:
        assert not {x[k] for x in q}&{x[k] for x in d}
    m=json.loads((OUT/'source_manifest.json').read_text(encoding='utf-8'))
    assert m['development_files_unchanged'] and m['source_overlap_with_development']

def test_oracles_nonempty_with_geodesic_crosscheck():
    o=json.loads((OUT/'spatial_oracles.json').read_text(encoding='utf-8'))
    assert o['source_rows']==o['parsed_rows']
    assert o['max_distance_difference_m']<.01
    assert len(o['objects'])==6
    for x in o['objects']:
        assert x['object_ids']
        assert not set(x['object_ids'])&{'mof_marine_names_20221231:'+str(i) for i in range(44,55)}
        assert len(x['object_ids'])==len(x['objects'])

def test_fault_controls_and_recovery_invariants():
    f=rows(OUT/'rq2_faults.jsonl');r=rows(OUT/'rq4_recovery.jsonl')
    assert sum(x['expected_invalid'] for x in f)==9
    assert sum(not x['expected_invalid'] for x in f)==3
    for x in f:
        assert (x['request_contract']!=x['frozen_initial_plan'])==x['expected_invalid']
    for x in r:
        if x['recoverable']:
            assert x['spatial_gold']['object_ids']
            assert x['expected_plan']==x['request_contract']
            assert all(x['expected_plan'][k]==x['initial_plan'][k] for k in x['invariants'])
        else:
            assert x['expected_plan'] is None and x['allowed_mutation_paths']==[]

def test_gate_rejects_changed_content(tmp_path):
    import shutil
    p=tmp_path/'holdout';shutil.copytree(OUT,p)
    (p/'gold.jsonl').write_text('{}\n',encoding='utf-8')
    assert 'BENCHMARK_HASH_MISMATCH:gold.jsonl' in evaluation_gate(p)['errors']


def test_hash_strings_without_freeze_artifacts_do_not_unlock():
    receipt=dict(benchmark_manifest_sha256=sha(OUT/'manifest.json'),human_holdout_gold_approved=True,
        reviewer_ids=['test'],approved_at='test',no_holdout_used_for_tuning=True,system_frozen=True,freeze_at='test')
    for k in ('system_source_sha256','model_digest','prompt_sha256','data_snapshot_sha256','evaluation_code_sha256'):receipt[k]='a'*64
    gate=evaluation_gate(OUT,receipt)
    assert not gate['evaluation_ready']
    assert 'VERIFIED_FREEZE_ARTIFACT_REQUIRED:system_source_sha256' in gate['errors']
    assert 'VERIFIED_MODEL_RECEIPT_REQUIRED' in gate['errors']

def test_location_evidence_and_attribute_locator():
    import xml.etree.ElementTree as E
    from tools.scie_results_ui.prepare_holdout import FC
    g=rows(OUT/'gold.jsonl');root=E.parse(FC).getroot()
    for c in g[6:9]:
        a=c['expected'];n=[x for x in root.findall(a['locator'],a['locator_namespaces']) if x.find('f:attribute',a['locator_namespaces']).get('ref')==a['attribute']]
        assert len(n)==1 and a['unique_locator_verified']
    for o in g[14]['expected']['objects']:
        assert o['location_evidence']['column']=='해양지위치정보'
        assert o['location_evidence']['csv_line']==o['csv_line']
        assert o['location_evidence']['source_sha256']==g[14]['expected']['source_sha256']
