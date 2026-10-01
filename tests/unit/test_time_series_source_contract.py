import pytest

from services.orchestrator import schema_binding_adapter as binding


@pytest.fixture
def adapter(monkeypatch, tmp_path):
    monkeypatch.setattr(binding, 'PROJECT_ROOT', tmp_path)
    obj = binding.SchemaBindingAdapter()
    obj.time_series_registry = {'version': 'test', 'datasets': {
        'fixture': {'path': 'fixture.csv', 'execution_status': 'fixture_only'},
        'real': {'path': 'observations.csv', 'execution_status': 'executable'}}}
    (tmp_path / 'fixture.csv').write_text('observed_at,value\n2026-01-01,1\n')
    (tmp_path / 'observations.csv').write_text('observed_at,value\n2026-01-01,2\n')
    return obj


@pytest.mark.parametrize('filters', [
    {'dataset_id': 'fixture'}, {'source_path': 'fixture.csv'},
    {'source_path': 'sub/../fixture.csv'}, {'source_path': 'missing.csv'},
    {'source_path': '../outside.csv'}, {'source_path': '.'},
])
def test_invalid_source_never_produces_binding(adapter, filters):
    result = adapter.build_bindings({'analysis_type': 'observed_time_series_analysis'}, {'filters': filters})
    assert result.blockers
    assert not result.data_bindings


def test_existing_source_is_bound_and_removed_source_is_rechecked(adapter, tmp_path):
    plan, slots = {'analysis_type': 'observed_time_series_analysis'}, {'filters': {'dataset_id': 'real'}}
    assert adapter.build_bindings(plan, slots).data_bindings
    (tmp_path / 'observations.csv').unlink()
    result = adapter.build_bindings(plan, slots)
    assert not result.data_bindings
    assert any(item.startswith('BLOCKED_DATA') for item in result.blockers)


def test_tool_resolves_parent_segments_before_scope_check(monkeypatch, tmp_path):
    from services.time_series_agent import tools
    monkeypatch.setattr(tools, 'ROOT', tmp_path)
    with pytest.raises(ValueError):
        tools._resolve_under_root('../outside.csv')
