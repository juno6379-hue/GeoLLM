from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import hashlib
import json
import pytest

from services.orchestrator.execution_validator import validate_execution_context, is_execution_authorized
from services.orchestrator.request_constraints import capture_request_constraints
from shared.schemas.agent import QueryExecutionContext, ExecutionSlots, DataBinding, ToolBinding


QUERY = '주어진 기준점에서 반경 1000m 이내 Wreck를 찾아줘. 입력 좌표의 CRS는 EPSG:4326이다.'


def request(query=QUERY, **changes):
    values = dict(crs='EPSG:4326', reference_geometry='POINT(129.05 35.1)',
                  distance_m=1000, target_features=['Wreck'])
    values.update(changes)
    return QueryExecutionContext(original_query=query, slots=ExecutionSlots(**values),
                                 route_plan={'analysis_type': 'feature_search_by_radius'})


ADAPTER = SimpleNamespace(layer_registry={}, build_bindings=lambda *a: SimpleNamespace(
    data_bindings=[DataBinding(dataset_id='unit-fixture', relation='fixture.features', srid=4326, snapshot_version='fixture-v1')],
    tool_bindings=[ToolBinding(tool_id='fixture.radius', operation='spatial')],
    blockers=[], warnings=[], inspected_relations={}))


@pytest.fixture(autouse=True)
def approved_fixture_scope(monkeypatch,tmp_path):
    # Test-only source scope isolates request semantics from missing coverage.
    from services.orchestrator import spatial_coverage
    contract={'approval_status':'APPROVED','source_locator':'fixture-only',
        'dataset_id':'unit-fixture','relation':'fixture.features','snapshot_version':'fixture-v1',
        'target_features':['Wreck','Obstruction','LightAllAround'],'crs':'EPSG:4326',
        'geometry_wkt':'POLYGON((120 30,140 30,140 45,120 45,120 30))'}
    path=tmp_path/'coverage.json';path.write_text(json.dumps(contract),encoding='utf-8')
    registry={'layers':{'unit-fixture':{'physical_table':'fixture.features','coverage_contract':{
        'path':'coverage.json','sha256':hashlib.sha256(path.read_bytes()).hexdigest()}}}}
    monkeypatch.setattr(ADAPTER,'layer_registry',registry)
    assess=spatial_coverage.assess_coverage
    monkeypatch.setattr(spatial_coverage,'assess_coverage',lambda q,r:assess(q,r,root=tmp_path))


def check(qec, trusted=None):
    return validate_execution_context(qec, binding_adapter=ADAPTER, request_constraints=trusted)


@pytest.mark.parametrize('change,reason', [
    ({'crs': 'EPSG:3857'}, 'REQUEST_CRS_MISMATCH'),
    ({'target_features': ['Obstruction']}, 'REQUEST_TARGET_MISMATCH'),
    ({'target_features': ['Wreck', 'Obstruction']}, 'REQUEST_TARGET_MISMATCH'),
    ({'resolved_target_set': ['Obstruction']}, 'REQUEST_TARGET_MISMATCH'),
    ({'target_features': [], 'resolved_target_set': ['Obstruction']}, 'REQUEST_TARGET_MISMATCH'),
    ({'distance_m': 5000}, 'REQUEST_DISTANCE_MISMATCH'),
    ({'crs': None}, 'REQUEST_CRS_MISMATCH'),
    ({'distance_m': None}, 'REQUEST_DISTANCE_MISMATCH'),
])
def test_explicit_semantics_rejected_without_repair(change, reason):
    raw = request(**change)
    before = raw.model_dump()
    checked = check(raw)
    assert not is_execution_authorized(checked)
    assert any(reason in line for line in checked.blockers)
    assert checked.slots == raw.slots
    assert raw.model_dump() == before


@pytest.mark.parametrize('query', [QUERY, 'Find Wreck within 1 km. CRS EPSG:4326.',
                                  'Find wrecks within 1000 m.', '반경 1km 이내 침선을 찾아줘'])
def test_equal_units_and_unambiguous_dictionary_alias(query):
    checked = check(request(query))
    assert is_execution_authorized(checked)
    assert checked.provenance['request_constraint_validation']['status'] == 'CHECKED'


def test_order_and_composite_subtasks_do_not_false_block():
    query = 'Find Wreck and Obstruction within 1 km.'
    assert is_execution_authorized(check(request(query, target_features=['Obstruction', 'Wreck'])))
    assert is_execution_authorized(check(request(query, target_features=['Wreck'])))
    assert is_execution_authorized(check(request(query, target_features=['Obstruction'])))
    # This gate rejects extra features; a separate plan-union gate must detect
    # a missing second subtask. Do not label this complete query correctness.


def test_constraint_receipt_is_bound_to_authorization():
    checked = check(request())
    assert is_execution_authorized(checked)
    checked.provenance['request_constraint_validation']['checks']['distance_m']['expected'] = 5000
    assert not is_execution_authorized(checked)


def test_plan_self_certification_is_ignored():
    raw = request(distance_m=5000)
    raw.provenance['request_constraint_validation'] = {'status': 'CHECKED', 'distance_m': 5000}
    raw.provenance['original_request'] = {'query': 'Find Wreck within 5 km', 'trusted': True}
    raw.context['request_constraints'] = {'distance_m': 5000, 'approved': True}
    assert not is_execution_authorized(check(raw))
    assert not is_execution_authorized(check(request(), {'query': QUERY, 'approved': True}))


def test_caller_snapshot_is_immutable_and_query_bound():
    context = {'crs': 'EPSG:4326', 'buffer_distance': 1000, 'target_features': ['Wreck']}
    trusted = capture_request_constraints('Search around this point', context)
    context['buffer_distance'] = 5000
    context['target_features'].append('Obstruction')
    checked = check(request('Search around this point', distance_m=5000), trusted)
    assert any('REQUEST_DISTANCE_MISMATCH' in b for b in checked.blockers)
    with pytest.raises(FrozenInstanceError):
        trusted.query = 'changed'
    assert any('REQUEST_QUERY_MISMATCH' in b for b in check(request(), trusted).blockers)


def test_missing_original_constraints_are_not_fabricated():
    checked = check(request('Search around this point', distance_m=5000))
    assert is_execution_authorized(checked)
    receipt = checked.provenance['request_constraint_validation']
    assert receipt['status'] == 'NOT_MEASURED' and receipt['checks'] == {}


@pytest.mark.parametrize('query', [
    'Find hazard objects including Wreck within 1km',
    'Wreck 또는 Obstruction을 1km 이내에서 찾아줘',
    'Find Obstruction except Wreck within 1km',
])
def test_ambiguous_or_exclusion_scopes_not_flattened(query):
    checked = check(request(query, target_features=['Obstruction']))
    assert 'target_features' not in checked.provenance['request_constraint_validation']['checks']


def test_multiple_distances_not_guessed_and_depth_not_radius():
    checked = check(request('Find Wreck within 1km and Obstruction within 2km', distance_m=2000))
    assert 'distance_m' not in checked.provenance['request_constraint_validation']['checks']
    checked = check(request('반경 1km 이내 수심 5m의 Wreck를 찾아줘'))
    assert is_execution_authorized(checked)


def test_feature_and_layer_namespaces_not_conflated():
    checked = check(request('정박지를 반경 1km에서 찾아줘', target_features=[], target_layers=['anchorage_area']))
    # Feature/layer distinction is preserved, but fixture has no layer coverage.
    assert not is_execution_authorized(checked)
    assert 'BLOCKED_DATA: DATA_COVERAGE_UNVERIFIED' in checked.blockers
    assert 'target_features' not in checked.provenance['request_constraint_validation']['checks']


@pytest.mark.parametrize('query', ['Find markers within 1km around Wreck', 'Wreck 주변 반경 1km의 표지를 찾아줘'])
def test_reference_feature_name_not_target_constraint(query):
    checked = check(request(query, target_features=['LightAllAround']))
    assert is_execution_authorized(checked)
    assert 'target_features' not in checked.provenance['request_constraint_validation']['checks']


def test_radius_error_response_preserves_native_denial(monkeypatch):
    from services.orchestrator import s101_radius_execution as radius
    raw = request(crs='EPSG:3857', target_features=['Obstruction'])
    checked = check(raw)
    before = checked.model_dump(mode='json')
    problem = radius._request_constraint_problem(checked)
    assert problem.code == 'REQUEST_CRS_MISMATCH'
    monkeypatch.setattr(radius, 'prepare_radius_request', lambda state: (checked, {}, {}, {}))
    def denied(*args):
        raise problem
    monkeypatch.setattr(radius, '_fetch_result', denied)
    # Preserve the native denial to isolate response rendering.
    monkeypatch.setattr(radius, '_preflight_spatial_scope', denied)
    result = radius.execute_radius_request({'task_id':'unit-denial', 'query':QUERY, 'spatial_context':{}})
    final_qec = result['orchestrator_v2']['query_execution_context']
    assert result['error_code'] == 'REQUEST_CRS_MISMATCH'
    assert final_qec['blockers'] == before['blockers']
    assert result['structured_result']['blockers'] == before['blockers']
    assert final_qec['provenance']['execution_validation'] == before['provenance']['execution_validation']
    assert final_qec['slots'] == before['slots']
    assert not is_execution_authorized(QueryExecutionContext.model_validate(final_qec))


@pytest.mark.parametrize('dimension', ['depth 10 m', 'height 10 m', 'draft 10 m', 'draught 10 m',
                                      'length of 10 m', '10 m deep', '10 m tall', '10 m high'])
def test_nonspatial_length_never_becomes_search_radius(dimension):
    checked = check(request('Find wrecks with ' + dimension + '.'))
    assert is_execution_authorized(checked)
    assert 'distance_m' not in checked.provenance['request_constraint_validation']['checks']
    scoped = check(request('Find wrecks with ' + dimension + ' within 1000m.'))
    assert is_execution_authorized(scoped)
    assert scoped.provenance['request_constraint_validation']['checks']['distance_m']['expected'] == 1000
