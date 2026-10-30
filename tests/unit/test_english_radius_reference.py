import pytest
from services.orchestrator.semantic_router import DynamicSlotExtractor
from services.spatial_analysis_agent.place_resolver import resolve_location, PlaceResolutionProblem, _candidate


@pytest.mark.parametrize('query, expected', [
    ('Find marine place names within 5 km of Dokdo.', 'Dokdo'),
    ('Find marine place names within 5000m of Dokdo.', 'Dokdo'),
    ('Find marine place names within 2 km of 부산항.', '부산항'),
    ('List place names within 500 m of Busan Port.', 'Busan Port'),
    ('Find wrecks within 3 km of Ulleungdo and explain their attributes.', 'Ulleungdo'),
    # Preserve the existing Korean extractor output; later normalization handles 주변.
    ('독도 주변 반경 5km의 해양지명을 찾아줘.', '독도 주변'),
])
def test_reference_follows_english_radius_without_changing_korean(query, expected):
    assert DynamicSlotExtractor().extract_location_before_distance(query) == expected


@pytest.mark.parametrize('query', [
    'Find marine place names within 5 km of.',
    'Find marine place names within 5 km.',
    'Find place names within 5 km of Dokdo and within 2 km of Busan.',
])
def test_missing_or_multiple_radius_references_do_not_become_command_prefix(query):
    assert DynamicSlotExtractor().extract_location_before_distance(query) is None


def test_multiple_place_names_are_not_silently_reduced_to_first():
    query = 'Find marine place names within 5 km of Alpha and Beta.'
    extracted = DynamicSlotExtractor().extract_location_before_distance(query)
    assert extracted == 'Alpha and Beta'
    # Synthetic catalogue fixtures exercise source matching, not real coordinates.
    catalog = {'candidates': [_candidate(str(i), label, [label], f'POINT({i} 1)',
        [{'source_ref':'fixture:catalogue', 'source_id':str(i)}]) for i,label in enumerate(['Alpha','Beta'],1)],
        'unavailable_sources': []}
    with pytest.raises(PlaceResolutionProblem):
        resolve_location(query, {'location_text':extracted}, catalog=catalog)


def test_english_extraction_does_not_grant_unknown_place_authority():
    query = 'Find place names within 2 km of UnregisteredReference.'
    location = DynamicSlotExtractor().extract_location_before_distance(query)
    with pytest.raises(PlaceResolutionProblem):
        resolve_location(query, {'location_text':location}, catalog={'candidates':[], 'unavailable_sources':[]})


@pytest.mark.parametrize('query, expected', [
    ('Find marine place names within 5 km of Dokdo.', 'Dokdo'),
    ('Find marine place names within 2 km of 부산항.', '부산항'),
    ('Find marine place names within 5 km of Dokdo and Ulleungdo.', 'Dokdo and Ulleungdo'),
    ('Find marine place names within 5 km of.', ''),
    ('Find marine place names within 5 km.', ''),
    ('Find places within 5 km of Alpha and within 2 km of Beta.', ''),
    ('독도 주변 반경 5km의 해양지명을 찾아줘.', '독도'),
])
def test_actual_spatial_layer_fast_path_uses_shared_reference_extraction(query, expected):
    from services.orchestrator.graph import _requested_layer_anchor_query
    assert _requested_layer_anchor_query(query, [{'layer_type':'marine_gazetteer'}]) == expected


def test_fast_path_passes_complete_reference_for_exact_resolution(monkeypatch):
    import asyncio
    from services.orchestrator import graph, place_router
    captured = {}
    def resolve(query, context):
        captured.update(query=query, context=context)
        return {'status':'NEEDS_CLARIFICATION', 'error_code':'LOCATION_UNCONFIRMED'}
    monkeypatch.setattr(place_router, 'resolve_payload', resolve)
    monkeypatch.setattr(graph, '_place_lookup_update', lambda state, location, capability: location)
    asyncio.run(graph.fast_requested_spatial_layer_execute_node({
        'task_id':'synthetic-test', 'query':'Find marine place names within 5 km of Alpha and Beta.'}))
    assert captured['context']['location_text'] == 'Alpha and Beta'


def test_conjunction_in_single_registered_name_is_still_resolvable():
    name = 'Trinidad and Tobago'
    item = _candidate('synthetic', name, [name], 'POINT(1 1)', [{'source_ref':'fixture:catalogue'}])
    result = resolve_location(name, {'location_text':name}, catalog={'candidates':[item], 'unavailable_sources':[]})
    assert result[1] == name
