import pytest
from shared.schemas.agent import AgentResult, AgentStatus
from services.orchestrator.map_adapter import convert_to_map_layer

def test_convert_to_map_layer_success():
    agent_result = AgentResult(
        task_id="test1",
        trace_id="tr1",
        agent_name="spatial-analysis-agent",
        agent_version="1.0",
        status=AgentStatus.COMPLETED,
        summary="교차 분석 완료",
        features="s3://mock/data.geojson",
        structured_result={"count": 10},
        provenance={"query_template": "postgis.intersection"}
    )
    
    layer = convert_to_map_layer(agent_result)
    assert layer is not None
    assert layer.layer_type == "geojson"
    assert layer.source_uri == "s3://mock/data.geojson"
    # intersection 이므로 파란색이어야 함
    assert layer.style.fill_color == "#0000FF"
    assert layer.metadata["generated_count"] == 10

def test_convert_to_map_layer_no_features():
    agent_result = AgentResult(
        task_id="test2",
        trace_id="tr2",
        agent_name="standard-rag-agent",
        agent_version="1.0",
        status=AgentStatus.COMPLETED,
        summary="문서 검색 완료"
        # features 없음
    )
    
    layer = convert_to_map_layer(agent_result)
    assert layer is None
