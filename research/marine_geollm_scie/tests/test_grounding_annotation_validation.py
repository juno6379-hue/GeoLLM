import hashlib
import json
from research.marine_geollm_scie.evaluation.grounding_annotation_validation import PACKAGE, validate_annotation_package


def fixture(root):
    source=root/'source.jsonl'
    source.write_text(json.dumps({'case_id':'a','query':'Find wrecks','feature':'Wreck'})+'\n',encoding='utf-8')
    ref=dict(path='source.jsonl',sha256=hashlib.sha256(source.read_bytes()).hexdigest(),jsonl_line=1)
    query=dict(case_id='a',query='Find wrecks',equivalence_group='wrecks')
    row=dict(**query,query_sha256=hashlib.sha256(query['query'].encode()).hexdigest(),source_contract=ref,task_mapping={'spatial': {'scope':'test spatial task'}},
             atoms=[dict(atom_id='a.feature',kind='feature',task_id='spatial',accepted_values=['Wreck'],
                         derivation='DIRECT_CONTRACT_VALUE',source_refs=[dict(**ref,json_pointer='/feature')])])
    p=root/PACKAGE;p.mkdir(parents=True)
    def write():
        raw=(json.dumps(row)+'\n').encode()
        (p/'gold_atoms.jsonl').write_bytes(raw)
        (p/'manifest.json').write_text(json.dumps(dict(case_count=1,task_ids=['spatial'],sources=[ref],files={'gold_atoms.jsonl':hashlib.sha256(raw).hexdigest()})),encoding='utf-8')
    write()
    return query,row,write


def test_valid_annotation_not_a_model_score_or_human_review(tmp_path):
    q,_,_=fixture(tmp_path)
    r=validate_annotation_package(tmp_path,[q],expected_case_count=1)
    assert r['status']=='VALIDATED_AI_ANNOTATION'
    assert r['validated_cases']==r['atom_count']==1
    assert r['measurement_status']=='NOT_MEASURED'
    assert r['human_approval'] is False


def test_hash_and_direct_value_changes_rejected(tmp_path):
    q,row,write=fixture(tmp_path)
    row['atoms'][0]['accepted_values']=['Lighthouse'];write()
    assert validate_annotation_package(tmp_path,[q],expected_case_count=1)['status']=='INVALID'
    row['atoms'][0]['accepted_values']=['Wreck'];write()
    (tmp_path/'source.jsonl').write_text('{}',encoding='utf-8')
    assert validate_annotation_package(tmp_path,[q],expected_case_count=1)['status']=='INVALID'


def test_cohort_and_duplicate_atoms_rejected(tmp_path):
    q,row,write=fixture(tmp_path)
    assert validate_annotation_package(tmp_path,[q])['status']=='INVALID'
    row['atoms'].append(dict(row['atoms'][0]));write()
    assert validate_annotation_package(tmp_path,[q],expected_case_count=1)['status']=='INVALID'


def test_query_change_and_missing_pointer_rejected(tmp_path):
    q,row,write=fixture(tmp_path)
    q['query']='different'
    assert validate_annotation_package(tmp_path,[q],expected_case_count=1)['status']=='INVALID'
    q['query']='Find wrecks'
    row['atoms'][0]['source_refs'][0]['json_pointer']='/absent';write()
    assert validate_annotation_package(tmp_path,[q],expected_case_count=1)['status']=='INVALID'


def test_holdout_source_rejected_before_read(tmp_path):
    q,row,write=fixture(tmp_path)
    row['atoms'][0]['source_refs'][0]['path']='benchmark/holdout/secret.json';write()
    r=validate_annotation_package(tmp_path,[q],expected_case_count=1)
    assert r['status']=='INVALID'
    assert r['errors'][0]['reason']=='SOURCE_PATH_NOT_ALLOWED'


def test_direct_extra_alternative_and_unknown_derivation_rejected(tmp_path):
    q,row,write=fixture(tmp_path)
    row['atoms'][0]['accepted_values'].append('Lighthouse');write()
    assert validate_annotation_package(tmp_path,[q],expected_case_count=1)['status']=='INVALID'
    row['atoms'][0]['accepted_values']=['Wreck']
    row['atoms'][0]['derivation']='GUESS';write()
    assert validate_annotation_package(tmp_path,[q],expected_case_count=1)['status']=='INVALID'


def test_unknown_task_and_extra_manifest_asset_tamper_rejected(tmp_path):
    q,row,write=fixture(tmp_path)
    row['atoms'][0]['task_id']='other';write()
    assert validate_annotation_package(tmp_path,[q],expected_case_count=1)['status']=='INVALID'
    row['atoms'][0]['task_id']='spatial';write()
    p=tmp_path/PACKAGE
    (p/'schema.json').write_text('{}',encoding='utf-8')
    manifest=json.loads((p/'manifest.json').read_text(encoding='utf-8'))
    manifest['files']['schema.json']='0'*64
    (p/'manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
    assert validate_annotation_package(tmp_path,[q],expected_case_count=1)['status']=='INVALID'


def test_manifest_source_not_used_by_atom_is_still_hash_checked(tmp_path):
    q,row,write=fixture(tmp_path)
    p=tmp_path/PACKAGE
    extra=tmp_path/'approval.json';extra.write_text('{}',encoding='utf-8')
    manifest=json.loads((p/'manifest.json').read_text(encoding='utf-8'))
    manifest['sources'].append(dict(path='approval.json',sha256='0'*64))
    (p/'manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
    r=validate_annotation_package(tmp_path,[q],expected_case_count=1)
    assert r['status']=='INVALID'
    assert r['errors'][0]['reason']=='MANIFEST_SOURCE_HASH_MISMATCH'
