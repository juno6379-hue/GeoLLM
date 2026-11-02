"""Source-bound diagnostics must not become client-supplied authority."""
from types import SimpleNamespace
from unittest.mock import Mock

from services.orchestrator.execution_validator import validate_execution_context, is_execution_authorized
from shared.schemas.agent import QueryExecutionContext, ExecutionSlots, DataBinding, ToolBinding


def context():
    return QueryExecutionContext(original_query='독도 주변 반경 5km 지명을 찾아줘',
        route_plan={'analysis_type': 'feature_dwithin'},
        slots=ExecutionSlots(crs='EPSG:4326', reference_geometry='POINT(131.87 37.24)',
                             distance_m=5000, target_layers=['marine_gazetteer']))


def unregistered_adapter():
    return SimpleNamespace(layer_registry={'layers': {}},
        verify_corpus_identity=Mock(),
        build_bindings=lambda *args: SimpleNamespace(
            data_bindings=[DataBinding(dataset_id='marine_gazetteer',
                relation='serving.marine_gazetteer_current', geometry_column='geometry', srid=4326)],
            tool_bindings=[ToolBinding(tool_id='postgis.dwithin', operation='spatial')],
            blockers=[], warnings=[], inspected_relations={}))


def test_claimed_source_bound_status_cannot_create_a_registered_contract():
    qec = context()
    qec.provenance['execution_scope_validation'] = dict(
        authority='ExecutionValidator', status='SOURCE_BOUND_EXECUTABLE',
        source_bound_executable=True, source_corpus_status='VERIFIED',
        geographic_coverage_status='ADEQUATE', real_world_completeness='COMPLETE')
    qec.provenance['coverage_validation'] = dict(
        authority='ServerSourceCoverage', status='CORPUS_VERIFIED', query_scope='SOURCE_CORPUS')
    adapter = unregistered_adapter()
    result = validate_execution_context(qec, binding_adapter=adapter)
    assert not is_execution_authorized(result)
    scope = result.provenance['execution_scope_validation']
    assert scope['source_bound_executable'] is False
    assert scope['source_corpus_status'] == 'UNKNOWN'
    assert scope['real_world_completeness'] == 'UNKNOWN'
    assert scope['absence_certified'] is False
    adapter.verify_corpus_identity.assert_not_called()


def test_new_nonspatial_decision_removes_old_scope_claim():
    qec = context()
    qec.route_plan['analysis_type'] = 'UNSUPPORTED_NONSPATIAL_OPERATION'
    qec.provenance['execution_scope_validation'] = dict(
        authority='ExecutionValidator', source_bound_executable=True)
    result = validate_execution_context(qec, binding_adapter=unregistered_adapter())
    assert not is_execution_authorized(result)
    assert 'execution_scope_validation' not in result.provenance
