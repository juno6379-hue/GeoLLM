from services.orchestrator import graph
from services.spatial_analysis_agent import place_resolver


def test_explicit_radius_overrides_map_and_preserves_invalid_values():
    state = {'spatial_context': {'buffer_distance': 3000}}
    assert graph._requested_layer_distance_m('독도 1km 지명', state) == 1000
    assert graph._requested_layer_distance_m('독도 -1km 지명', state) == -1000
    assert graph._requested_layer_distance_m('독도 0m 지명', state) == 0


def test_typo_requires_known_place_and_gazetteer_task(monkeypatch):
    monkeypatch.setattr(place_resolver, 'load_catalog', lambda: {'candidates': [{'label': '독도'}]})
    targets = [graph.REQUESTED_SPATIAL_LAYER_TARGETS['marine_gazetteer']]
    assert graph._requested_layer_anchor_query('독도구근해저지명', targets) == '독도'
    assert graph._requested_layer_anchor_query('없는섬구근해저지명', targets) == '없는섬구근'
    assert graph._requested_layer_anchor_query('독도 부근 해양지명을 찾아줘', targets) == '독도'
