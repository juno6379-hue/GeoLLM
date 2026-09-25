import copy
import pytest
from services.orchestrator.reference_evaluation import make_unit, validate_reference_gold
from scripts.index_maritime_references import units_for
from scripts.evaluate_grounded_shadow import ranking_comparison


def fixture():
    unit=make_unit({'artifact_id':'fixture','sha256':'a'*64,'edition':'1'},
                   {'kind':'pdf_page','page_1based':2},'A wreck is a vessel remnant.')
    binding={k:unit[k] for k in ('unit_id','source_id','source_sha256','edition','text_sha256','locator')}
    binding.update(quote='vessel remnant',claim='fixture claim',applicability='fixture edition',
                   reviewer_ids=['test-fixture-only'],review_status='HUMAN_VERIFIED')
    return unit,{'reference_review_status':'HUMAN_VERIFIED','reference_bindings':[binding]}


def test_exact_reference_contract():
    unit,gold=fixture()
    assert validate_reference_gold([gold],[unit])['bindings']==1


@pytest.mark.parametrize('change,error',[
    ({'source_review_status':'GOLD_APPROVAL_BLOCKED'},'blocked'),
    ({'extraction_flags':['CONTROL_CHARACTERS']},'extraction'),
    ({'text':'changed'},'hash mismatch')])
def test_unusable_source_cannot_be_gold(change,error):
    unit,gold=fixture(); unit.update(change)
    with pytest.raises(ValueError,match=error): validate_reference_gold([gold],[unit])


def test_old_notice_cannot_be_asserted_as_current_law():
    unit,gold=fixture(); gold['reference_bindings'][0]['use_as_current_law']=True
    with pytest.raises(ValueError,match='Current legal'): validate_reference_gold([gold],[unit])


def test_invented_quote_and_wrong_edition_rejected():
    unit,gold=fixture()
    for field,value,error in [('quote','made up','quote'),('edition','2','match frozen')]:
        bad=copy.deepcopy(gold); bad['reference_bindings'][0][field]=value
        with pytest.raises(ValueError,match=error): validate_reference_gold([bad],[unit])


def test_hml_paragraphs_preserve_text_and_ordinals():
    raw=b'<HWPML><BODY><P><TEXT><CHAR>alpha</CHAR><CHAR> beta</CHAR></TEXT></P><P><TEXT><CHAR>gamma</CHAR></TEXT></P></BODY></HWPML>'
    rows=list(units_for(raw,'hml'))
    assert rows[0][1]=='alpha beta'
    assert rows[1][0]['paragraph_1based']==2


def test_rankings_do_not_hide_model_rejection_with_rule_fallback():
    rows=[{'sample':1,'accepted':False,'rankings':{'rule':{'ranking':['A']},'ollama':{'ranking':['A']}}}]
    result=ranking_comparison(rows,[{'sample':1,'intent':'A'}])
    assert result['methods']['rule']['semantic_metrics']['exact_match_accuracy']==1
    assert result['methods']['ollama']['semantic_metrics']['exact_match_accuracy']==0
    assert result['methods']['ollama']['abstained_failed_or_unavailable']==1
    assert result['mixed_slot_and_task_metrics'] is None


def test_existing_anchorage_registry_reaches_feature_binding():
    from services.orchestrator.semantic_slot_binding import bind_semantic_slots
    result=bind_semantic_slots('정박지는 S-101에서 어떤 Feature야?',{'constraints':[],'slots':[]},[])
    assert result['target_features']==['AnchorageArea']
    term=next(t for t in result['term_bindings'] if t['raw_text']=='정박지')
    assert term['registry_ref'].endswith('s101_features/정박지')
    assert term['span']==[0,3]


def test_shared_lexicon_does_not_invent_missing_fc_codes():
    from services.orchestrator.marine_lexicon import load_terms
    terms,_=load_terms()
    assert 'Light' not in terms.get('등화',{}).get('maps_to_features',[])
    assert terms['선석']['canonical_id'] is None
    assert len(terms['선석']['maps_to_features'])>1


def test_new_anchorage_binding_preserves_exclusion():
    from services.orchestrator.semantic_slot_binding import bind_semantic_slots
    from services.orchestrator.korean_query_analysis import constraints
    query='정박지 말고 침선을 찾아줘'
    result=bind_semantic_slots(query,{'constraints':constraints(query),'slots':[]},[])
    assert 'AnchorageArea' not in result['target_features']
    assert 'Wreck' in result['target_features']
