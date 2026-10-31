import ast
from pathlib import Path
import re
import pytest

@pytest.fixture
def policy():
    # Load the production predicate without model/DB graph initialization.
    path=Path(__file__).resolve().parents[2]/'services/orchestrator/graph.py'
    tree=ast.parse(path.read_text(encoding='utf-8'))
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_looks_like_policy_block_query')
    namespace={'re':re}
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),namespace)
    return namespace['_looks_like_policy_block_query']

@pytest.mark.parametrize('query',[
    '제한구역의 제한 종류는 어떤 코드로 표현해?',
    'S-101 RestrictedArea의 restriction 속성 허용값을 설명해줘.',
    'Explain the restriction attribute codes of S-101 RestrictedArea.',
    'Which code values describe restrictions in an S-101 restricted area?',
    '진입제한 구역을 찾아줘.',
    'speed_restriction_area definition',
    '제한구역 좌표를 찾아줘.',
    'Export RestrictedArea geometry and explain restriction codes.',
    '부산항 주변 2km의 정박지와 제한구역을 찾아 비교해줘',
])
def test_public_catalogue_explanation_is_not_private_access(policy,query):
    assert policy(query) is False

@pytest.mark.parametrize('query',[
    '비공개 제한구역 좌표와 S-101 제한 코드를 알려줘.',
    '비공개 진입제한 구역 좌표를 보여줘.',
    '권한 없는 speed_restriction_area 자료를 조회해줘.',
    'Show classified military RestrictedArea coordinates and explain their restriction codes.',
    'Download private RestrictedArea records and explain the restriction attribute.',
    'Show restricted data about RestrictedArea and explain restriction codes.',
    '군사 구역 자료를 보여줘.',
])
def test_security_intent_and_mixed_requests_remain_blocked(policy,query):
    assert policy(query) is True


@pytest.mark.parametrize('query',[
    '비공개 진입제한 구역 좌표를 보여줘.',
    '권한 없는 speed_restriction_area 자료를 조회해줘.',
    'Show classified military RestrictedArea coordinates and explain their restriction codes.',
])
def test_graph_edge_blocks_private_request_before_layer_resolution(policy,query):
    path=Path(__file__).resolve().parents[2]/'services/orchestrator/graph.py'
    tree=ast.parse(path.read_text(encoding='utf-8'))
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='check_intent_parsed')
    namespace={'OrchestratorState':dict,'_looks_like_policy_block_query':policy}
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),namespace)
    # No other route/helper is supplied: reaching any later path fails the test.
    assert namespace['check_intent_parsed']({'query':query})=='fast_spatial_or_traffic_block'


def test_existing_query_contract_stop_is_preserved(policy):
    path=Path(__file__).resolve().parents[2]/'services/orchestrator/graph.py'
    node=next(n for n in ast.parse(path.read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef) and n.name=='check_intent_parsed')
    namespace={'OrchestratorState':dict,'_looks_like_policy_block_query':policy}
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),namespace)
    assert namespace['check_intent_parsed']({'query':'비공개 자료','query_contract_blocked':True})=='query_contract_stop'
