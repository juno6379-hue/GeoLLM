"""Apply/run only after the proposed catalogue and shared-obligation patch."""
from copy import deepcopy
import hashlib
import pytest
from services.orchestrator import catalogue_document as catalogue
from services.orchestrator import request_obligations as obligations


@pytest.mark.parametrize('phrase', ['DCEG 근거', 'DCEG의 근거', 'DCEG근거'])
def test_dceg_required_with_korean_particle(phrase):
    assert 'dceg_source_evidence' in obligations.required_outputs('Obstruction 정의와 '+phrase+'를 알려줘')


def test_fc_definition_alone_does_not_fulfill_dceg_request():
    query='S-101 2.0 Obstruction 정의와 DCEG 근거를 알려줘'
    result=catalogue.build_catalogue_document_response({'task_id':'fc-dceg-fixture','query':query,'user_id':'fixture'})
    assert result
    final=result['final_dict']
    assert final['status']=='PARTIAL'
    assert 'dceg_source_evidence' in final['structured_result']['unmet_outputs']
    assert 'DCEG 원문' in final['answer_text']
    assert any(row['output']=='grounded_term_explanation' and row['status']=='EVIDENCE_PRESENT_REVIEW_REQUIRED'
               for row in final['orchestrator_v2']['output_obligations'])
    original=final['structured_result']['document_answer']['evidence']
    assert final['rag_evidence'][0]['data']==original
    assert final['evidence_bundle']['rag_evidence'][0]['data']==original
    assert final['rag_evidence'][0]['source_ref']==original['source_ref']
    assert final['rag_evidence'][0]['source_sha256']==original['source_sha256']


def test_fc_only_request_stays_complete():
    final=catalogue.build_catalogue_document_response({'task_id':'fc-only-fixture','query':'Wreck 정의와 S-101 근거를 알려줘','user_id':'fixture'})['final_dict']
    assert final['status']=='COMPLETED'
    assert 'dceg_source_evidence' not in obligations.required_outputs('Wreck 정의와 S-101 근거를 알려줘')


def test_false_dceg_label_missing_locator_and_hash_tampering_fail_closed(tmp_path,monkeypatch):
    monkeypatch.setattr(obligations,'SOURCE_ROOT',tmp_path)
    raw=b'DCEG fixture source (test only)'
    (tmp_path/'DCEG-fixture.txt').write_bytes(raw)
    entry={'source_kind':'S101_DCEG','source_ref':'DCEG-fixture.txt','source_sha256':hashlib.sha256(raw).hexdigest(),
           'locators':['line:1'],'quote':raw.decode()}
    final={'structured_result':{'dceg_evidence':entry}}
    assert obligations._has_dceg_source_evidence(final)
    for patch in [{'source_kind':'S101_FEATURE_CATALOGUE'},{'source_ref':'catalogue.xml'},
                  {'source_sha256':'0'*64},{'locators':[]},{'quote':''},{'quote':'invented quote with real source hash'},
                  {'locators':['line:2']},{'locators':['page:1']},{'source_ref':'../DCEG-escape.txt'}]:
        modified=deepcopy(final)
        modified['structured_result']['dceg_evidence'].update(patch)
        assert not obligations._has_dceg_source_evidence(modified)
    assert 'dceg_source_evidence' not in obligations.required_outputs('Obstruction 정의, DCEG 제외')
