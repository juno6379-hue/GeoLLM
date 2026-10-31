"""No model/DB needed: fast paths must preserve operator and target obligations."""
import ast
from pathlib import Path
import re

import pytest

from services.orchestrator.execution_validator import validate_place_resolution, is_execution_authorized


GRAPH = Path(__file__).resolve().parents[2] / 'services/orchestrator/graph.py'
TREE = ast.parse(GRAPH.read_text(encoding='utf-8-sig'))


@pytest.fixture
def problem():
    node = next(n for n in TREE.body if isinstance(n, ast.FunctionDef)
                and n.name == '_spatial_fast_path_contract_problem')
    namespace = {'re': re}
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(GRAPH), 'exec'), namespace)
    return namespace[node.name]


@pytest.mark.parametrize('query', [
    '독도 부근에서 가장 가까운 등대를 찾아줘.',
    '부산항 주변 5km에서 가장 가까운 침선을 찾아줘',
    'Find the closest lighthouse within 2 km.',
    'Find the nearest wreck near the current map.',
    '최근접 등대를 찾아줘',
])
def test_nearest_never_requests_a_radius(problem, query):
    result = problem(query)
    assert result['error_code'] == 'UNSUPPORTED_OPERATOR'
    assert result['search_execution'] == {
        'status': 'NOT_RUN', 'reason': 'UNSUPPORTED_OPERATOR',
        'execution_attempted': False, 'execution_started': False,
        'tool_called': False, 'sql_executed': False,
    }
    assert not is_execution_authorized(validate_place_resolution(query, result))


@pytest.mark.parametrize('query', [
    '부산항 주변 2km의 정박지와 제한구역을 찾아 비교해줘.',
    '독도 주변 5km의 등대와 난파선을 찾아줘',
    'Find wrecks and lighthouses within 5 km',
    'Find the nearest anchorage and wreck',
    'Compare the anchorages within 2 km',
])
@pytest.mark.parametrize('supports_nearest', [True, False])
def test_composite_never_executes_only_one_family(problem, query, supports_nearest):
    result = problem(query, supports_nearest=supports_nearest)
    assert result['error_code'] == 'UNSUPPORTED_COMPOSITE_TASK'
    assert not result['search_execution']['execution_attempted']


@pytest.mark.parametrize('query', [
    '부산항 주변 2km의 침선을 찾아줘',
    'Find wrecks within 1 km',
    '부산항 주변 항로표지를 찾아줘',
    '부산항 부근 정박지를 찾아줘',
])
def test_single_radius_unchanged(problem, query):
    assert problem(query) is None


def test_supported_nearest_keeps_existing_validator_path(problem):
    assert problem('Find the nearest anchorage', supports_nearest=True) is None


def test_complete_multiple_family_binding_is_not_blocked(problem):
    assert problem('Find wrecks and lighthouses within 5 km', selected_targets=['Wreck', 'LightAllAround']) is None


def test_native_multi_feature_selection_is_preserved(problem):
    import yaml
    from services.orchestrator.s101_radius_execution import select_targets
    registry = yaml.safe_load((GRAPH.parents[2] / 'data/derived_concept_registry_v2.yaml').read_text(encoding='utf-8'))
    profile = registry['derived_concepts']['navigation_hazard_object']['execution_profiles']['s101_hazard_radius']
    query = 'Find Wreck and Obstruction within 1 km'
    targets, exclusions = select_targets(query, {}, profile)
    assert set(targets) == {'Wreck', 'Obstruction'} and exclusions == []
    assert problem(query, selected_targets=targets) is None


@pytest.mark.parametrize('handler,execution_name', [
    ('fast_requested_spatial_layer_execute_node', 'resolve_payload'),
    ('fast_s101_nearest_feature_execute_node', 'resolve_payload'),
    ('fast_s101_hazard_radius_execute_node', 'execute_radius_request'),
])
def test_guard_returns_before_first_tool_call(handler, execution_name):
    node = next(n for n in TREE.body if isinstance(n, ast.AsyncFunctionDef) and n.name == handler)
    guard = next(n for n in node.body if isinstance(n, ast.Assign)
                 and isinstance(n.value, ast.Call)
                 and isinstance(n.value.func, ast.Name)
                 and n.value.func.id == '_spatial_fast_path_contract_problem')
    return_guard = next(n for n in node.body if isinstance(n, ast.If)
                        and isinstance(n.test, ast.Name) and n.test.id == 'problem')
    execution_refs = [n.lineno for n in ast.walk(node)
                      if isinstance(n, ast.Name) and n.id == execution_name]
    assert guard.lineno < return_guard.lineno < min(execution_refs)
    assert isinstance(return_guard.body[0], ast.Return)
