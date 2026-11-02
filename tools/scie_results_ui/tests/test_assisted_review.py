import copy
import pytest
from tools.scie_results_ui.import_assisted_review import validate,aggregate
from tools.scie_results_ui.prepare_semantic_review import DIMENSIONS

def example():
    item=dict(answer_id='a',answer_sha256='raw',display_sha256='display',gold_manifest_sha256='gold')
    a=dict(item,reviewer='AAA',author_type='HUMAN_VERIFIED_AI_ASSISTED_REVIEW',human_completed=True,ai_assisted_origin=True,independent_review_confirmed=False,reviewed_at='2026-11-02',dimensions=dict.fromkeys(DIMENSIONS,True))
    a.update({k:'human submitted' for k in ('rationale','answer_evidence_quote','gold_evidence_locator','human_label_source','human_reviewer','human_review_attestation')})
    return item,a

def test_assisted_provenance_and_hash_required():
    item,a=example()
    assert validate([a],[item],'AAA')['a']==a
    for k,v in [('independent_review_confirmed',True),('display_sha256','changed'),('human_completed',False)]:
        bad=dict(a,**{k:v})
        with pytest.raises(ValueError):validate([bad],[item],'AAA')
    with pytest.raises(ValueError):validate([a,a],[item],'AAA')

def test_consensus_binding_and_distinct_dimensions():
    _,a=example();b=copy.deepcopy(a);b['dimensions']['meaning_correct']=False
    c=copy.deepcopy(b);c.update(AAA_dimensions=a['dimensions'],BBB_dimensions=b['dimensions'])
    result=aggregate({'a':a},{'a':b},{'a':c},[dict(answer_id='a',method='P1',case_id='q')])
    assert result['dimension_correct']['evidence_supported']==1
    assert result['joint_correct']==0
    assert result['agreement']['meaning_correct']['matches']==0
    c['BBB_dimensions']=a['dimensions']
    with pytest.raises(ValueError):aggregate({'a':a},{'a':b},{'a':c},[])
