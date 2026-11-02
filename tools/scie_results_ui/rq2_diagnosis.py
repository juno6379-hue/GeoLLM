"""Read-only, post-hoc target-fault diagnosis of preserved controlled runs.

This does not re-run detectors or credit the common validator observation to B4.
Original receipts must verify before any result is exposed. Mapping old blocker
text to diagnostic codes is an explicitly new descriptive analysis, not a
pre-registered eight-subtype benchmark.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

from research.marine_geollm_scie.runners.report_eight_faults import load_verified_faults

VERSION = 'rq2.target_fault_posthoc.v1'
# This mapping was authored against this exact v6 injected-plan contract. Reusing
# case IDs in a newer experiment does not automatically approve this mapping.
SUPPORTED_CONTRACT_SHA256 = '3802aca3949fda1abff4f12e66a86c5048e82012246f2e2a377c0811707052b1'
EXPECTED = {
    'FAULT_V2_CONTROL': (),
    'FAULT_V2_UNIT_TYPED': ('DISTANCE_VALUE_TYPE_INVALID',),
    'FAULT_V2_MISSING_GEOMETRY': ('MISSING_REFERENCE_GEOMETRY',),
    'FAULT_V2_WRONG_CRS': ('REQUEST_CRS_MISMATCH',),
    'FAULT_V2_UNKNOWN_SOURCE': ('EXPLICIT_SOURCE_REQUIRED',),
    'FAULT_V2_NEGATIVE_RADIUS': ('DISTANCE_NOT_POSITIVE',),
    'FAULT_V2_WRONG_FEATURE': ('REQUEST_TARGET_MISMATCH',),
    'FAULT_V2_SEMANTIC_EXPANSION': ('REQUEST_TARGET_MISMATCH',),
    'FAULT_V2_WRONG_RADIUS': ('REQUEST_DISTANCE_MISMATCH',),
}
BLOCKER_MAPPING = {
    'NEEDS_USER_INPUT: reference geometry is unresolved': 'MISSING_REFERENCE_GEOMETRY',
    'BLOCKED_CONFIG: REQUEST_CRS_MISMATCH': 'REQUEST_CRS_MISMATCH',
    'BLOCKED_CONFIG: explicit research source required': 'EXPLICIT_SOURCE_REQUIRED',
    'NEEDS_USER_INPUT: distance_m must be positive': 'DISTANCE_NOT_POSITIVE',
    'BLOCKED_CONFIG: REQUEST_TARGET_MISMATCH': 'REQUEST_TARGET_MISMATCH',
    'BLOCKED_CONFIG: REQUEST_DISTANCE_MISMATCH': 'REQUEST_DISTANCE_MISMATCH',
    'BLOCKED_DATA: DATA_COVERAGE_UNVERIFIED': 'DATA_COVERAGE_UNVERIFIED',
    'BLOCKED_CONFIG: no validated data binding': 'NO_VALIDATED_DATA_BINDING',
    'BLOCKED_CONFIG: no validated tool binding': 'NO_VALIDATED_TOOL_BINDING',
}
LIMITATIONS = [
    'expected fault code는 기존 fault_contract의 사전 정의 필드가 아니라, 고정 주입 사례와 원문 blocker를 대조한 사후 매핑입니다.',
    'B4 행에 함께 저장된 validator_detection은 공통 비교 계측입니다. LLM Review 검출 성과로 합산하지 않습니다.',
    'B4의 initial_checks/reason/raw verdict를 그대로 공개합니다. 기존 reviewer에 전용 fault-code 출력 계약이 없어 true 판정만으로 정확한 코드 검출을 추정하지 않습니다.',
    'wrong_feature와 semantic_expansion은 같은 REQUEST_TARGET_MISMATCH로 검출됩니다. 두 세부 오류를 독립적으로 정확히 분류했다는 뜻이 아닙니다.',
    '8개 오류 각각 N=1, 정상 CONTROL N=1입니다. 일반화 성능이나 신뢰구간을 만들지 않습니다.',
    'typed unit 1건은 lossless compiler의 형식 거절이며 native Validator 7건과 분리합니다.',
    '기존 v6의 coverage 정상 오차단은 보존합니다. 사후 진단이 운영 수정·새 전체 비교 실행을 대체하지 않습니다.',
]


def _sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def _ratio(values):
    missing = sum(v is None for v in values)
    numerator = sum(v is True for v in values)
    return dict(numerator=numerator, denominator=len(values), measured=len(values)-missing,
                missing=missing, value=numerator/len(values) if values and not missing else None)


def _detector_evidence(row):
    detector = row.get('validator_detection') or {}
    found = []
    for i, trace in enumerate(detector.get('compilation_traces') or []):
        for j, error in enumerate(trace.get('errors') or []):
            found.append(dict(raw=error, code=error if error == 'DISTANCE_VALUE_TYPE_INVALID' else None,
                              stage='LOSSLESS_COMPILER',
                              json_pointer=f'/validator_detection/compilation_traces/{i}/errors/{j}'))
    for i, qec in enumerate(detector.get('qecs') or []):
        for j, blocker in enumerate(qec.get('blockers') or []):
            found.append(dict(raw=blocker, code=BLOCKER_MAPPING.get(blocker), stage='NATIVE_VALIDATOR',
                              json_pointer=f'/validator_detection/qecs/{i}/blockers/{j}'))
    return found


def _score_row(row, review):
    method = row['method']
    expected = list(EXPECTED[row['case_id']])
    verdict = row.get('predicted_invalid')
    if type(verdict) is not bool or type(row.get('expected_invalid')) is not bool:
        raise ValueError('Missing explicit binary fault verdict')
    if bool(expected) != row['expected_invalid']:
        raise ValueError('Post-hoc code mapping differs from injected fault validity')
    rv = review.get('review') or {}
    review_invalid = rv.get('invalid')
    if type(review_invalid) is not bool or row.get('review_invalid') is not review_invalid:
        raise ValueError('Review verdict differs from shared raw receipt')
    detector = row.get('validator_detection') or {}
    if type(detector.get('invalid')) is not bool:
        raise ValueError('Missing detector observation')
    expected_verdict = review_invalid if method == 'B4' else detector['invalid'] if method == 'P0' else (review_invalid or detector['invalid'])
    if verdict is not expected_verdict:
        raise ValueError('Method attribution differs from stored verdict')
    all_evidence = _detector_evidence(row)
    # B4 common-floor validator output is preserved as excluded evidence only.
    admitted = [] if method == 'B4' else all_evidence
    codes = sorted({e['code'] for e in admitted if e['code']})
    code_state = ('NOT_INSTRUMENTED_IN_LLM_REVIEW' if method == 'B4' else
                  'OBSERVED_MAPPED_CODES' if codes else 'NO_MAPPED_CODE_OBSERVED')
    if not expected:
        hit = None
    elif not verdict:
        hit = False  # false initial verdict cannot be a target-fault detection
    elif method == 'B4':
        hit = None  # reason prose / pass/fail dimensions are not an emitted fault code
    else:
        hit = bool(set(expected) & set(codes))
    return dict(case_id=row['case_id'], error_type=row['error_type'], method=method,
                expected_invalid=row['expected_invalid'], predicted_invalid=verdict,
                expected_fault_codes=expected, detected_fault_codes=codes,
                target_code_hit=hit, code_observation_status=code_state,
                binary_detection=verdict if expected else None,
                false_block=verdict if not expected else None,
                compiler_rejected=detector.get('compiler_rejected') if method != 'B4' else None,
                native_validator_called=detector.get('native_validator_called') if method != 'B4' else None,
                attributed_detection_evidence=admitted,
                excluded_common_validator_evidence=all_evidence if method == 'B4' else [],
                review_initial_checks=rv.get('initial_checks'), review_initial_invalid=review_invalid,
                review_reason=rv.get('reason'),
                review_evidence_pointers=['/review/initial_checks', '/review/invalid', '/review/reason', '/call/raw_response'],
                strict_subtype_diagnosis=None,
                strict_subtype_status='NOT_PRE_REGISTERED_OR_SEPARATELY_IDENTIFIABLE',
                mapping_status='POST_HOC_EXACT_LITERAL_MAPPING_NOT_NEW_DETECTOR_OUTPUT')


def build_rq2_diagnosis(root, selected_run_id):
    root = Path(root).resolve()
    base = dict(version=VERSION, status='NOT_MEASURED', selected_run_id=selected_run_id,
                methods=[], rows=[], limitations=LIMITATIONS,
                mapping_status='POST_HOC_DESCRIPTIVE', strict_subtype_recall=None)
    if not isinstance(selected_run_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]+', selected_run_id):
        return {**base, 'status': 'INVALID_RUN_ID'}
    folder = root / 'research/marine_geollm_scie/runs' / selected_run_id / 'faults'
    try:
        if not folder.is_dir(): return {**base, 'status': 'NO_FAULT_OBSERVATIONS'}
        if not folder.resolve().is_relative_to(root): raise ValueError('Source path escapes root')
        # Reject symlinked source members before the existing original-hash gate.
        for p in folder.rglob('*'):
            if not p.resolve().is_relative_to(folder.resolve()): raise ValueError('Fault source path escapes folder')
        rows, manifest = load_verified_faults(folder)
        if manifest.get('fault_contract_sha256') != SUPPORTED_CONTRACT_SHA256:
            return {**base, 'status': 'MAPPING_NOT_DEFINED_FOR_COHORT',
                    'required_fault_contract_sha256': SUPPORTED_CONTRACT_SHA256,
                    'observed_fault_contract_sha256': manifest.get('fault_contract_sha256')}
        if {r['case_id'] for r in rows} != set(EXPECTED):
            return {**base, 'status': 'MAPPING_NOT_DEFINED_FOR_COHORT'}
        outputs=[];receipts={}
        for name in ('manifest.json', 'fault_contract.json', 'independent_oracle.json', 'rows.jsonl'):
            p=folder/name;receipts[p.relative_to(root).as_posix()]=_sha(p)
        for row in rows:
            p=folder/row['case_id'];review_path=p/'review.json'
            review=json.loads(review_path.read_text(encoding='utf-8'))
            result=_score_row(row,review)
            result['raw_path']=(p/(row['method']+'.json')).relative_to(root).as_posix()
            result['raw_sha256']=_sha(p/(row['method']+'.json'))
            result['review_path']=review_path.relative_to(root).as_posix()
            result['review_sha256']=_sha(review_path)
            result['initial_plan_sha256']=row['initial_plan_sha256']
            outputs.append(result)
            for artifact in (p/'initial_plan.json',review_path,p/(row['method']+'.json')):
                receipts[artifact.relative_to(root).as_posix()]=_sha(artifact)
        methods=[]
        for method in ('B4','P0','H'):
            selected=[r for r in outputs if r['method']==method]
            invalid=[r for r in selected if r['expected_invalid']]
            controls=[r for r in selected if not r['expected_invalid']]
            methods.append(dict(method=method,binary_recall=_ratio([r['predicted_invalid'] for r in invalid]),
                                target_code_recall=_ratio([r['target_code_hit'] for r in invalid]),
                                false_block=_ratio([r['false_block'] for r in controls]),
                                compiler_target_hits=sum(r['target_code_hit'] is True and r['compiler_rejected'] is True for r in invalid),
                                native_validator_target_hits=sum(r['target_code_hit'] is True and r['native_validator_called'] is True for r in invalid),
                                strict_subtype_recall=None))
        reread_rows, reread_manifest = load_verified_faults(folder)
        if reread_rows != rows or reread_manifest != manifest or any(
                _sha(root/path) != digest for path,digest in receipts.items()):
            raise ValueError('Fault artifacts changed during diagnosis')
        return {**base,'status':'POST_HOC_VERIFIED_DIAGNOSTIC','methods':methods,'rows':outputs,
                'verified_original_hashes':receipts,'source_manifest':manifest,
                'mapping_contract':{'expected_by_case':EXPECTED,'blocker_literal_mapping':BLOCKER_MAPPING,
                                    'frozen_fault_contract_sha256':SUPPORTED_CONTRACT_SHA256},
                'cases':9,'invalid_cases':8,'control_cases':1,'observations':27,
                'new_model_execution':False,'original_run_modified':False}
    except (ValueError, OSError, KeyError, TypeError, UnicodeError) as exc:
        return {**base,'status':'INTEGRITY_FAILED','error':str(exc)}
