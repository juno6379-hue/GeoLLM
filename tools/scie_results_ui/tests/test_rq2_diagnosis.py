import hashlib
import json

from research.marine_geollm_scie.runners.matched_branches import plan_hash
from tools.scie_results_ui.rq2_diagnosis import (
    EXPECTED, BLOCKER_MAPPING, _score_row, build_rq2_diagnosis,
)


def _review(invalid=False):
    return {'review': {'invalid': invalid, 'reason': 'literal reason',
                       'initial_checks': {'target': 'pass'}},
            'call': {'raw_response': '{}'}, 'errors': []}


def _row(case='FAULT_V2_WRONG_FEATURE', method='P0', blockers=None):
    expected=bool(EXPECTED[case])
    compiler=case=='FAULT_V2_UNIT_TYPED'
    if blockers is None:
        code=(EXPECTED[case] or ['DATA_COVERAGE_UNVERIFIED'])[0]
        blockers=[next((k for k,v in BLOCKER_MAPPING.items() if v==code),'unmapped')]
    return {'case_id':case,'error_type':case,'method':method,'expected_invalid':expected,
            'predicted_invalid':method!='B4','review_invalid':False,
            'validator_detection':{'invalid':True,'compiler_rejected':compiler,
                'native_validator_called':not compiler,
                'qecs':[] if compiler else [{'blockers':blockers}],
                'compilation_traces':[{'errors':['DISTANCE_VALUE_TYPE_INVALID']}] if compiler else []}}


def test_b4_does_not_inherit_common_validator_target_code():
    result=_score_row(_row(method='B4'),_review())
    assert result['detected_fault_codes']==[]
    assert result['target_code_hit'] is False
    assert result['excluded_common_validator_evidence'][0]['code']=='REQUEST_TARGET_MISMATCH'
    assert result['code_observation_status']=='NOT_INSTRUMENTED_IN_LLM_REVIEW'


def test_unrelated_coverage_block_is_not_target_detection():
    result=_score_row(_row(blockers=['BLOCKED_DATA: DATA_COVERAGE_UNVERIFIED']),_review())
    assert result['binary_detection'] is True
    assert result['target_code_hit'] is False


def test_b4_true_verdict_without_codes_remains_unmeasured():
    row=_row(method='B4');row.update(predicted_invalid=True,review_invalid=True)
    result=_score_row(row,_review(True))
    assert result['target_code_hit'] is None
    assert result['binary_detection'] is True


def test_compiler_is_not_native_validator():
    result=_score_row(_row('FAULT_V2_UNIT_TYPED'),_review())
    assert result['target_code_hit'] is True
    assert result['compiler_rejected'] is True
    assert result['native_validator_called'] is False
    assert result['attributed_detection_evidence'][0]['stage']=='LOSSLESS_COMPILER'


def test_feature_and_expansion_not_separate_subtype_claim():
    for case in ('FAULT_V2_WRONG_FEATURE','FAULT_V2_SEMANTIC_EXPANSION'):
        result=_score_row(_row(case),_review())
        assert result['expected_fault_codes']==['REQUEST_TARGET_MISMATCH']
        assert result['strict_subtype_diagnosis'] is None


def test_control_not_in_target_recall():
    result=_score_row(_row('FAULT_V2_CONTROL'),_review())
    assert result['target_code_hit'] is None
    assert result['false_block'] is True
    assert result['detected_fault_codes']==['DATA_COVERAGE_UNVERIFIED']


def _fixture(root, monkeypatch=None):
    folder=root/'research/marine_geollm_scie/runs/test_run/faults'
    folder.mkdir(parents=True)
    def write(p,obj):
        p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
        return hashlib.sha256(p.read_bytes()).hexdigest()
    cases=[]
    for case in EXPECTED:
        cases.append({'case_id':case,'plan':{},'initial_plan_sha256':plan_hash({}),
                      'expected_invalid':bool(EXPECTED[case])})
    contract_sha=write(folder/'fault_contract.json',{'cases':cases})
    if monkeypatch is not None:
        monkeypatch.setattr('tools.scie_results_ui.rq2_diagnosis.SUPPORTED_CONTRACT_SHA256',contract_sha)
    oracle_sha=write(folder/'independent_oracle.json',{})
    identity={'test':'synthetic_only'}
    rows=[]
    for case in cases:
        p=folder/case['case_id'];p.mkdir()
        write(p/'initial_plan.json',case)
        review_sha=write(p/'review.json',_review())
        for method in ('B4','P0','H'):
            row=_row(case['case_id'],method)
            row.update(initial_plan_sha256=case['initial_plan_sha256'],fault_contract_sha256=contract_sha,
                       independent_oracle_sha256=oracle_sha,benchmark_sha256='a'*64,
                       execution_identity=identity,review_artifact_sha256=review_sha)
            write(p/(method+'.json'),row);rows.append(row)
    (folder/'rows.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows),encoding='utf-8')
    rows_sha=hashlib.sha256((folder/'rows.jsonl').read_bytes()).hexdigest()
    write(folder/'manifest.json',dict(status='COMPLETED_CONTROLLED_DIAGNOSTICS',
          fault_contract_sha256=contract_sha,independent_oracle_sha256=oracle_sha,rows_sha256=rows_sha,
          benchmark_sha256='a'*64,execution_identity=identity))
    return folder


def test_verified_cohort_and_tamper_fail_closed(tmp_path, monkeypatch):
    folder=_fixture(tmp_path, monkeypatch)
    result=build_rq2_diagnosis(tmp_path,'test_run')
    assert result['status']=='POST_HOC_VERIFIED_DIAGNOSTIC'
    methods={m['method']:m for m in result['methods']}
    assert methods['B4']['target_code_recall']['numerator']==0
    assert methods['P0']['target_code_recall']['numerator']==8
    assert methods['P0']['native_validator_target_hits']==7
    assert methods['P0']['compiler_target_hits']==1
    assert methods['H']['false_block']['value']==1
    with (folder/'rows.jsonl').open('a') as f:f.write('\n')
    failed=build_rq2_diagnosis(tmp_path,'test_run')
    assert failed['status']=='INTEGRITY_FAILED' and failed['methods']==[]


def test_raw_branch_tamper_rejected(tmp_path, monkeypatch):
    folder=_fixture(tmp_path, monkeypatch)
    (folder/'FAULT_V2_CONTROL/B4.json').write_text('{}')
    result=build_rq2_diagnosis(tmp_path,'test_run')
    assert result['status']=='INTEGRITY_FAILED'


def test_review_raw_tamper_rejected(tmp_path, monkeypatch):
    folder=_fixture(tmp_path, monkeypatch)
    (folder/'FAULT_V2_CONTROL/review.json').write_text('{}')
    assert build_rq2_diagnosis(tmp_path,'test_run')['status']=='INTEGRITY_FAILED'


def test_invalid_paths_and_absence(tmp_path):
    assert build_rq2_diagnosis(tmp_path,'../../holdout')['status']=='INVALID_RUN_ID'
    assert build_rq2_diagnosis(tmp_path,'test_run')['status']=='NO_FAULT_OBSERVATIONS'


def test_reused_case_ids_in_different_frozen_contract_not_scored(tmp_path):
    _fixture(tmp_path)
    result=build_rq2_diagnosis(tmp_path,'test_run')
    assert result['status']=='MAPPING_NOT_DEFINED_FOR_COHORT'
    assert result['methods']==[] and result['rows']==[]


def test_corrupt_json_is_not_zero_score(tmp_path, monkeypatch):
    folder=_fixture(tmp_path, monkeypatch)
    (folder/'manifest.json').write_text('{')
    result=build_rq2_diagnosis(tmp_path,'test_run')
    assert result['status']=='INTEGRITY_FAILED' and result['methods']==[]
