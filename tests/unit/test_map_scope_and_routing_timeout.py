import asyncio
import ast
from pathlib import Path
import pytest
from services.orchestrator.request_semantics import missing_map_scope
from services.orchestrator.korean_query_analysis import contract_problem
from services.orchestrator.request_obligations import audit_outputs
from services.orchestrator.routing_timeout import invoke_routing_fallback, routing_timeout_seconds


def test_missing_map_scope_is_clarified_before_model_routing():
    query='Explain Wreck attributes and show wrecks on the map.'
    problem=contract_problem(query, {'slots': [], 'constraints': []}, {})
    assert problem['code']=='MAP_SCOPE_REQUIRED'
    assert problem['status']=='NEEDS_CLARIFICATION'


@pytest.mark.parametrize('query,context', [
    ('Show wrecks near Busan on the map.', {}),
    ('Show Dokdo on the map.', {}),
    ('부산항 주변 침선을 지도에 표시해줘.', {}),
    ('Show wrecks on the map.', {'geometry':'POINT (129 35)'}),
    ('Show wrecks on the map.', {'map_bounds':[128,34,129,35]}),
    ('Show wrecks on the map.', {'location_text':'an unresolved place'}),
])
def test_explicit_scope_is_preserved_for_resolver_validation(query,context):
    assert not missing_map_scope(query,context)


def test_no_map_document_output_is_not_completed():
    result=audit_outputs('Explain Wreck attributes and show wrecks on the map.',
                         {'status':'COMPLETED','summary':'Documents found','structured_result':{'documents':[{'title':'Wreck'}]}})
    assert result['status']=='PARTIAL'
    assert 'map_spatial_result' in result['structured_result']['unmet_outputs']


def test_requested_geometry_and_fake_empty_collection_do_not_prove_execution():
    result=audit_outputs('Show wrecks on the map.', {'status':'COMPLETED',
        'structured_result': {'geojson': {'type':'FeatureCollection','features':[]}, 'status':'SUCCESS_EMPTY'},
        'map_layers':[{'id':'requested-scope'}]})
    assert result['status']=='PARTIAL'


def test_stalled_fallback_is_cancelled_without_retries():
    class Stalled:
        calls=0
        cancelled=False
        async def ainvoke(self,messages):
            self.calls+=1
            try:
                await asyncio.Event().wait()
            finally:
                self.cancelled=True
    async def run():
        model=Stalled()
        with pytest.raises(asyncio.TimeoutError):
            await invoke_routing_fallback(model,[],0.02)
        assert model.calls==1 and model.cancelled
    asyncio.run(run())


@pytest.mark.parametrize('value,expected', [('nan',15),('garbage',15),('999',60),('0',0.1),('7',7)])
def test_timeout_configuration_is_finite_and_bounded(monkeypatch,value,expected):
    monkeypatch.setenv('GEOLLM_ROUTING_FALLBACK_TIMEOUT_SEC',value)
    assert routing_timeout_seconds()==expected


def test_graph_transport_timeout_and_retry_budget_are_explicit():
    tree=ast.parse(Path('services/orchestrator/graph.py').read_text(encoding='utf-8'))
    constructors=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='ChatOpenAI']
    assert constructors
    for call in constructors:
        keywords={k.arg:k.value for k in call.keywords}
        assert 'timeout' in keywords
        assert isinstance(keywords['max_retries'],ast.Constant) and keywords['max_retries'].value==0

@pytest.mark.parametrize('query,context', [
    ('Find wrecks intersecting the selected area.', {}),
    ('Find wrecks intersecting the selected area.', {'geometry':'POLYGON ((0 0,1 0,1 1,0 0))'}),
    ('Explain Wreck attributes and show wrecks on the map.', {}),
])
def test_guard_qec_is_typed_and_never_authorized(query,context):
    from services.orchestrator.korean_query_analysis import guard_result
    from services.orchestrator.execution_validator import is_execution_authorized
    from shared.schemas.agent import QueryExecutionContext
    analysis={'slots':[], 'constraints':[]}
    problem=contract_problem(query,analysis,context)
    result=guard_result({'task_id':'typed-guard','query':query},analysis,problem)
    typed=QueryExecutionContext.model_validate(result['query_execution_context'])
    assert typed.readiness.value in {'NEEDS_USER_INPUT','BLOCKED_CONFIG'}
    assert not is_execution_authorized(typed)
