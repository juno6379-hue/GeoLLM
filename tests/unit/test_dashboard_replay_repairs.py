"""Operational regressions found in the 116-query dashboard replay."""
import json
from pathlib import Path
import pytest
from services.orchestrator import dataset_answer, pipeline_diagnostics, traffic_description
from services.orchestrator.execution_validator import validate_lookup_request, validate_place_resolution, is_execution_authorized
from services.orchestrator.request_semantics import requires_execution, requests_map_output, missing_map_scope
from services.orchestrator.s101_radius_execution import _result_target_label, _unnamed_hazard_query
from services.orchestrator.harbour_evidence import harbour_card

QUERY = '통항량 지도 셀을 클릭했을 때 보여줄 AIS/V-PASS 세부정보를 설명해줘'


@pytest.mark.parametrize('query', [QUERY, 'Dataset 폴더 안의 embedding 완료 현황을 요약해줘',
                                 'Ontology/KG validator가 후보를 제거한 이유를 설명해줘'])
def test_operational_diagnostics_never_enter_document_answer(query, monkeypatch):
    monkeypatch.setattr(dataset_answer, 'retrieve', lambda *a, **kw: pytest.fail('diagnostic intercepted as document'))
    assert pipeline_diagnostics.diagnostic_request(query)
    assert not dataset_answer.informational_request(query)
    assert dataset_answer.build_dataset_answer({'task_id':'diagnostic-test','query':query}) is None


def test_description_validated_against_actual_registry_without_spatial_execution():
    assert not requires_execution(QUERY) and not requests_map_output(QUERY)
    assert not missing_map_scope(QUERY,{})
    state={'task_id':'traffic-description-test','query':QUERY}
    qec=validate_lookup_request(state,'traffic_layer_description')
    assert is_execution_authorized(qec)
    assert qec.data_bindings[0].snapshot_version == traffic_description.read_traffic_description()['source_sha256']
    final=pipeline_diagnostics.diagnostic_response(state)
    assert final['status']=='PARTIAL'
    assert len(final['structured_result']['rows'])==4
    evidence=final['evidence_bundle']['diagnostic_evidence'][0]
    assert evidence['snapshot']['live_values_queried'] is False
    assert '실제 클릭한 셀이나 최신 관측값을 조회한 결과는 아닙니다' in final['answer_text']


@pytest.mark.parametrize('query', [QUERY+' 그리고 부산항 주변 실제지도에 표시해줘',
    '부산항 통항량을 실제지도에 표시하고 셀을 클릭했을 때 정보를 설명해줘',
    'AIS 지도 셀을 클릭했을 때 선박별 MMSI 정보를 설명해줘'])
def test_mixed_or_individual_data_requests_are_not_contract_descriptions(query):
    assert not traffic_description.is_hypothetical_traffic_description(query)
    qec=validate_lookup_request({'task_id':'negative','query':query},'traffic_layer_description')
    assert not is_execution_authorized(qec)


@pytest.mark.parametrize('candidates,missing', [([],['reference_geometry']),([{'place_id':'p'}],['location_confirmation'])])
def test_place_clarification_preserves_missing_slots(candidates,missing):
    qec=validate_place_resolution('clarification',{'status':'NEEDS_CLARIFICATION','location_candidates':candidates})
    assert not is_execution_authorized(qec)
    assert qec.slots.unresolved_slots==missing


def test_executor_target_wording_and_unprovided_reference():
    assert _result_target_label(['Wreck'])=='침선'
    assert _result_target_label(['Obstruction'])=='장애물'
    assert _result_target_label(['Wreck','Obstruction'])=='침선·장애물'
    assert _unnamed_hazard_query('근처 위험물',{})
    assert not _unnamed_hazard_query('없는항 침선',{})
    assert not _unnamed_hazard_query('위험객체',{'geometry':'POINT(129 35)'})


def test_harbour_partial_card_preserves_source_prefix_and_labels_missing_tail(tmp_path):
    path=Path(__file__).resolve().parents[2]/'data/source_verification/harbour_prefix_20261103_v1.json'
    receipt=json.loads(path.read_text(encoding='utf-8'))
    e=receipt['entries'][0]
    row={'source_id':e['source_id'],'properties':{e['field']:e['prefix']+'\ufffd'},
         'provenance':{'source_file':e['source_file'],'source_sha256':e['source_sha256'],
                       'component_hashes':{'TB_SAILER.dbf':e['dbf_sha256']},'damaged_fields':[e['field']]}}
    card=harbour_card(row,tmp_path)
    field=card['fields'][0]
    assert field['partial'] and field['missing_text_reconstructed'] is False
    assert field['text'].startswith(e['prefix'])
    assert '\n\n[원문 일부:' in field['text'] and '\\n' not in field['text']
    assert '뒷부분 누락' in field['text'] and '원문 일부' in field['label']
    assert not card['unavailable_fields']
