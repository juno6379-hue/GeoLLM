import copy
import json
from pathlib import Path
import pytest
from research.marine_geollm_scie.evaluation.grounding_prediction_review_v2 import (
    compile_review,prepare_review_template,sha,CONTRACT_SHA256,check_atom,
)
from research.marine_geollm_scie.evaluation.grounding_atoms_v1 import score_atoms


def complete_fixture():
    raw=json.dumps({'case_id':'case','method':'B1','query':'Q',
        'plan':{'target_features':['height'],'answer':'Wreck attributes: height.'}}).encode()
    review=prepare_review_template(raw,case_id='case',method='B1',query='Q')
    review.update(status='COMPLETE',reviewer_id='AI_fixture',whole_response_review_note='All fields and text reviewed.',
        structured_field_review={'target_features':'Wrong kind is preserved','answer':'Complete text reviewed'},claim_sidecar=[],
        atoms=[{'prediction_id':'p1','kind':'feature','task_id':'query','value':'height','rule':'name',
                'review_note':'Attribute placed in feature list is still a feature claim.',
                'witnesses':[{'pointer':'/plan/target_features/0','literal':'height'}]}])
    return raw,review


def test_wrong_field_is_false_positive_not_repaired_attribute():
    raw,review=complete_fixture();result=compile_review(raw,review)
    scored=score_atoms([{'atom_id':'g','kind':'attribute_binding','task_id':'query',
                        'accepted_values':[{'owner':'Wreck','attribute':'height'}]}],result['prediction_atoms'])
    assert (scored['tp'],scored['fp'],scored['fn'])==(0,1,1)


@pytest.mark.parametrize('mutation',['raw_hash','query','human','incomplete','field','span','prompt','borrow_value','duplicate'])
def test_bad_review_rejected(mutation):
    raw,review=complete_fixture()
    if mutation=='raw_hash':review['raw_sha256']='0'*64
    if mutation=='query':review['query_sha256']='0'*64
    if mutation=='human':review['human_review_complete']=True
    if mutation=='incomplete':review['status']='REVIEW_REQUIRED'
    if mutation=='field':del review['structured_field_review']['target_features']
    if mutation=='span':review['atoms'][0]['witnesses']=[{'pointer':'/plan/answer','span':[1,6],'literal':'Wreck'}]
    if mutation=='prompt':review['atoms'][0]['witnesses']=[{'pointer':'/query','literal':'Q'}]
    if mutation=='borrow_value':review['atoms'][0]['value']='Wreck'
    if mutation=='duplicate':review['atoms'].append(copy.deepcopy(review['atoms'][0]))
    with pytest.raises(ValueError):compile_review(raw,review)


def test_missing_owner_cannot_be_filled_from_topic_or_gold():
    raw,review=complete_fixture();atom=review['atoms'][0]
    atom.update(kind='attribute_binding',value={'owner':'Wreck','attribute':'height'},rule='attribute_owner')
    with pytest.raises(ValueError,match='OWNER_NOT_WITNESSED'):compile_review(raw,review)


def test_source_hash_cannot_be_looked_up_or_replaced():
    raw,review=complete_fixture();atom=review['atoms'][0]
    atom.update(kind='source_binding',value={'source_sha256':'1'*64,'locators':[]},rule='source_claim')
    with pytest.raises(ValueError,match='SOURCE_VALUE_NOT_WITNESSED'):compile_review(raw,review)


def test_edition_cannot_be_inferred_from_catalogue():
    raw={'plan':{'answer':'S-101'}}
    atom={'kind':'standard','task_id':'query','value':{'standard':'S-101','edition':'2.0.0'},
          'rule':'standard','review_note':'fixture','witnesses':[{'pointer':'/plan/answer','literal':'S-101'}]}
    with pytest.raises(ValueError,match='EDITION_NOT_WITNESSED'):check_atom(raw,atom)


def test_composite_wrong_task_not_matched_and_no_scope_broadcast():
    raw,review=complete_fixture();atom=review['atoms'][0]
    atom['task_id']='spatial:anchor_line'
    with pytest.raises(ValueError,match='COMPOSITE_SCOPE_REQUIRED'):compile_review(raw,review)
    atom['task_scope_note']='Explicit wrong target, never remapped to Wreck'
    result=compile_review(raw,review)
    score=score_atoms([{'atom_id':'g','task_id':'spatial:wreck','kind':'feature','accepted_values':['height']}],result['prediction_atoms'])
    assert score['tp']==0 and score['fp']==1


def test_fresh_raw_always_requires_fresh_review():
    raw,review=complete_fixture();new=raw.replace(b'height',b'colour')
    with pytest.raises(ValueError,match='RAW_HASH_MISMATCH'):compile_review(new,review)
    pending=prepare_review_template(new,case_id='case',method='B1',query='Q')
    assert pending['status']=='REVIEW_REQUIRED' and pending['atoms'] is None


def test_no_response_failure_is_explicitly_reviewable_not_silently_dropped():
    raw=json.dumps({'case_id':'x','method':'B2','query':'Q','status':'TIMEOUT','calls':[{'error':'TIMEOUT'}]}).encode()
    review=prepare_review_template(raw,case_id='x',method='B2',query='Q')
    assert review['narrative_review']['pointer'] is None
    with pytest.raises(ValueError,match='FULL_RESPONSE_REVIEW_REQUIRED'):compile_review(raw,review)
    review.update(status='COMPLETE',reviewer_id='AI_fixture',whole_response_review_note='Observed timeout with no model response.',
                  atoms=[],claim_sidecar=[])
    assert compile_review(raw,review)['prediction_atoms']==[]


def test_development_36_reviews_recompile_and_retain_failures():
    root=Path(__file__).resolve().parents[3]
    path=root/'outputs/rq1_prediction_complete_20261103_v2/freeze_candidate/ai_reviews.jsonl'
    if not path.exists():pytest.skip('Optional local raw replay receipt not distributed with source tests')
    reviews=[json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
    rows=[compile_review((root/r['raw_path']).read_bytes(),r) for r in reviews]
    assert len(rows)==36 and len({(r['case_id'],r['method']) for r in rows})==36
    assert sum(r['raw_status']=='INVALID_RESPONSE' for r in rows)==11
    assert all(r['complete_grounding_extraction'] and not r['human_review_complete'] for r in rows)
    b1=next(r for r in rows if r['case_id']=='PILOT_Q5_01' and r['method']=='B1')
    assert any(a['value']=='anchor_line' and a['task_id']=='spatial:anchor_line' for a in b1['prediction_atoms'])
    b2=next(r for r in rows if r['case_id']=='PILOT_Q5_03' and r['method']=='B2')
    assert any(a['kind']=='attribute_binding' and a['value']=={'owner':'Wreck','attribute':'Obstruction'} for a in b2['prediction_atoms'])
    failed=next(r for r in rows if r['case_id']=='PILOT_Q1_01' and r['method']=='B2')
    assert failed['prediction_atoms']  # Truncated prefix was reviewed, not discarded.


def test_distance_metric_components_require_explicit_grounding():
    phrase='WGS84 ellipsoid minimum geometry-to-geometry distance, polygon area, boundary inclusive'
    raw={'plan':{'answer':phrase}}
    atom={'kind':'distance_metric','task_id':'spatial:AnchorageArea','task_scope_note':'explicit group',
          'value':{'surface':'WGS84_ellipsoid','measurement':'minimum_geometry_to_geometry',
                   'reference':'polygon_area','boundary_inclusive':True},
          'rule':'metric_semantics','review_note':'All components stated',
          'witnesses':[{'pointer':'/plan/answer','literal':phrase}]}
    check_atom(raw,atom)
    atom['value']['measurement']='centroid_to_centroid'
    with pytest.raises(ValueError,match='METRIC_COMPONENT_NOT_WITNESSED'):check_atom(raw,atom)


def test_comparison_criterion_is_not_inferred_from_two_target_names():
    raw={'plan':{'answer':'AnchorageArea and RestrictedArea'}}
    atom={'kind':'comparison_criterion','task_id':'comparison','task_scope_note':'comparison task',
          'value':'per_type_object_count','rule':'criterion_semantics','review_note':'fixture',
          'witnesses':[{'pointer':'/plan/answer','literal':raw['plan']['answer']}]}
    with pytest.raises(ValueError,match='CRITERION_NOT_WITNESSED'):check_atom(raw,atom)
