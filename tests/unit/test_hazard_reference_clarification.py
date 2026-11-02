"""Missing reference/radius contracts; explicit fixture coordinates, no live DB."""
import copy
import pytest
from services.orchestrator import s101_radius_execution as radius
from services.spatial_analysis_agent import place_resolver


@pytest.fixture
def case(monkeypatch):
    parent = place_resolver._candidate('fixture:busan', '부산항', [], 'POINT(129.1 35.1)', [{'source_ref':'fixture'}])
    monkeypatch.setattr(radius, '_place_entries', lambda: {})
    monkeypatch.setattr(place_resolver, 'load_catalog', lambda **kw: {'candidates':[parent], 'unavailable_sources':[]})
    def forbidden(*args, **kwargs):
        raise AssertionError('No spatial dispatch before complete input')
    monkeypatch.setattr(radius, '_preflight_spatial_scope', forbidden)
    monkeypatch.setattr(radius, '_fetch_result', forbidden)
    monkeypatch.setattr(radius, '_fetch_bounds_result', forbidden)
    return {'task_id':'fixture-entrance', 'query':'부산항입구위험객체',
            'normalized_query':'부산항 입구 navigation_hazard_object', 'spatial_context':{},
            'candidate_trace':{'query':'부산항입구위험객체','deterministic_signals':[
                {'signal_id':'place_name','value':'부산항입구'},
                {'signal_id':'place_name_utf8','value':'부산항입구'}]}}


@pytest.mark.parametrize('bounds', [None, [126.48148,37.36319,126.6128,37.44733]])
def test_named_entrance_not_replaced_with_viewport_and_all_missing_inputs_reported(case, bounds):
    if bounds:
        case['spatial_context']['map_bounds']=bounds
    result=radius.execute_radius_request(case)
    assert result['status']=='NEEDS_CLARIFICATION'
    assert result['error_code']=='LOCATION_UNCONFIRMED'
    qec=result['orchestrator_v2']['query_execution_context']
    assert qec['slots']['location_text']=='부산항 입구'
    assert qec['slots']['location']=='부산항 입구'
    assert qec['slots']['reference_geometry'] is None
    assert set(qec['slots']['unresolved_slots'])=={'reference_geometry','distance_m'}
    assert qec['route_plan']['slots']==qec['slots']
    assert '부산항 입구' in result['summary'] and '반경도' in result['summary']
    assert result['structured_result']['location_text']=='부산항 입구'
    assert all(result['structured_result']['search_execution'][k] is False for k in ['execution_attempted','execution_started','tool_called','sql_executed'])
    assert result['structured_result']['count'] is None
    assert result['clarification_options']
    assert all(c['selection_scope'] == 'PARENT_PLACE_ONLY' and c['qualifier_binding_verified'] is False
               for c in result['clarification_options'])


def test_radius_reply_keeps_missing_entrance_location(case):
    case['spatial_context']['buffer_distance']=1000
    result=radius.execute_radius_request(case)
    assert result['error_code']=='LOCATION_UNCONFIRMED'
    assert result['structured_result']['missing_slots']==['reference_geometry']
    assert result['structured_result']['distance_m']==1000
    assert result['structured_result']['location_text']=='부산항 입구'


def test_explicit_point_and_radius_satisfy_preparation(case):
    case['spatial_context'].update(geometry='POINT(129.075 35.075)',crs='EPSG:4326',buffer_distance=1000)
    qec,*_=radius.prepare_radius_request(case)
    assert qec.slots.location_text=='부산항 입구'
    assert qec.slots.reference_geometry=='POINT (129.075 35.075)'
    assert qec.slots.distance_m==1000
    assert qec.provenance['location_resolution']['status']=='CONFIRMED_INPUT'


def test_confirmed_reference_is_preserved_when_only_radius_missing(case):
    case['spatial_context'].update(geometry='POINT(129.075 35.075)',crs='EPSG:4326')
    result=radius.execute_radius_request(case)
    qec=result['orchestrator_v2']['query_execution_context']
    assert result['error_code']=='DISTANCE_REQUIRED'
    assert result['structured_result']['missing_slots']==['distance_m']
    assert qec['slots']['reference_geometry']=='POINT(129.075 35.075)'
    assert qec['slots']['resolution_status']=='CONFIRMED_INPUT'
    assert result['structured_result']['reference_geometry']==qec['slots']['reference_geometry']
    assert result['structured_result']['result_surface']['reference_geometry']==qec['slots']['reference_geometry']


@pytest.mark.parametrize('value,code', [(-1,'INVALID_RADIUS'),(60000,'RADIUS_LIMIT')])
def test_invalid_or_policy_radius_precedes_lookup(case, monkeypatch, value, code):
    case['spatial_context']['buffer_distance']=value
    monkeypatch.setattr(radius,'resolve_reference',lambda *a: pytest.fail('invalid radius must not resolve'))
    assert radius.execute_radius_request(case)['error_code']==code


def test_direct_bounds_preparation_cannot_bypass_named_reference(case):
    case['spatial_context']['map_bounds']=[126.4,37.3,126.7,37.5]
    with pytest.raises(radius.RadiusProblem, match='기준 위치'):
        radius.prepare_bounds_request(case)


@pytest.mark.parametrize('query', ['위험객체', '현재 지도 위험객체', '여기 주변 위험객체'])
def test_unnamed_map_context_still_prepares_area(case, query):
    case.update(query=query,normalized_query=query,candidate_trace={})
    case['spatial_context']['map_bounds']=[129.0,35.0,129.1,35.1]
    qec,*_=radius.prepare_bounds_request(case)
    assert qec.slots.resolution_status=='MAP_BOUNDS'


def test_unrecognized_named_reference_is_not_implicit_viewport(case):
    case.update(query='Atlantis 위험객체',normalized_query='Atlantis navigation_hazard_object',candidate_trace={})
    case['spatial_context']['map_bounds']=[126.4,37.3,126.7,37.5]
    result=radius.execute_radius_request(case)
    assert result['status']=='NEEDS_CLARIFICATION'
    assert result['structured_result']['reference_geometry'] is None


def test_hint_extraction_does_not_mutate_caller_state(case):
    before=copy.deepcopy(case)
    radius.execute_radius_request(case)
    assert case==before


@pytest.mark.parametrize('trace', ['malformed', {'query':'부산항입구위험객체','deterministic_signals':'malformed'}])
def test_malformed_historical_trace_falls_back_to_grounded_signals(case, trace):
    case['candidate_trace']=trace
    result=radius.execute_radius_request(case)
    assert result['status']=='NEEDS_CLARIFICATION'
    assert result['structured_result']['location_text']=='부산항 입구'


def test_unlocated_radius_reply_retains_distance_in_qec(case):
    case['spatial_context']['buffer_distance']=1000
    result=radius.execute_radius_request(case)
    qec=result['orchestrator_v2']['query_execution_context']
    assert qec['slots']['distance_m']==1000
    assert qec['route_plan']['slots']['distance_m']==1000


def test_parent_harbour_selection_does_not_confirm_entrance(case):
    parent=place_resolver.load_catalog()['candidates'][0]
    case['spatial_context'].update(place_id=parent['place_id'],place_version=parent['place_version'],buffer_distance=1000)
    result=radius.execute_radius_request(case)
    assert result['error_code']=='LOCATION_UNCONFIRMED'
    assert result['structured_result']['missing_slots']==['reference_geometry']
    assert result['orchestrator_v2']['query_execution_context']['slots']['reference_geometry'] is None
    assert result['clarification_options'][0]['selection_scope']=='PARENT_PLACE_ONLY'
    assert '세부 위치' in result['summary']


def test_source_qualified_entrance_selection_is_allowed(case, monkeypatch):
    entrance=place_resolver._candidate('fixture:entrance','부산항 입구',[], 'POINT(129.075 35.075)', [{'source_ref':'fixture'}])
    monkeypatch.setattr(place_resolver,'load_catalog',lambda **kw: {'candidates':[entrance],'unavailable_sources':[]})
    case['spatial_context'].update(place_id=entrance['place_id'],place_version=entrance['place_version'],buffer_distance=1000)
    qec,*_=radius.prepare_radius_request(case)
    assert qec.slots.location_text=='부산항 입구'
    assert qec.provenance['location_resolution']['status']=='CONFIRMED_SELECTION'


def test_whole_harbour_selection_still_allowed(case):
    parent=place_resolver.load_catalog()['candidates'][0]
    case.update(query='부산항 위험객체',normalized_query='부산항 navigation_hazard_object')
    case['spatial_context'].update(place_id=parent['place_id'],place_version=parent['place_version'],buffer_distance=1000)
    qec,*_=radius.prepare_radius_request(case)
    assert qec.slots.location_text=='부산항'
    assert qec.provenance['location_resolution']['status']=='CONFIRMED_SELECTION'


def test_parent_selection_geometry_cannot_silently_bind_entrance(case):
    parent=place_resolver.load_catalog()['candidates'][0]
    case['spatial_context'].update(place_id=parent['place_id'],place_version=parent['place_version'],geometry=parent['geometry'],crs=parent['crs'],buffer_distance=1000)
    result=radius.execute_radius_request(case)
    assert result['error_code']=='LOCATION_UNCONFIRMED'
    assert result['structured_result']['reference_geometry'] is None
