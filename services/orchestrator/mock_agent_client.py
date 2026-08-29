import asyncio
from datetime import datetime
from shared.schemas.agent import AgentRequest, AgentResult, AgentStatus
from services.data_discovery_agent.agent import execute_data_discovery
from services.standard_rag_agent.agent import execute_rag_search
from services.spatial_analysis_agent.agent import execute_spatial_analysis

async def call_agent_mock(request: AgentRequest) -> AgentResult:
    """
    전문 Agent를 호출하는 로직의 모의(Mock) 구현입니다.
    Data Discovery, RAG, Spatial Agent의 경우 실제 구현체로 연결하고,
    나머지 Agent는 Mock 결과를 반환합니다.
    """
    if request.agent_name == "data-discovery-agent":
        return await execute_data_discovery(request)
    elif request.agent_name == "standard-rag-agent":
        return await execute_rag_search(request)
    elif request.agent_name == "spatial-analysis-agent":
        return await execute_spatial_analysis(request)

        
    # 네트워크 지연 시뮬레이션
    await asyncio.sleep(1)
    
    return AgentResult(
        task_id=request.task_id,
        trace_id=request.trace_id,
        agent_name=request.agent_name,
        agent_version="1.0.0-mock",
        status=AgentStatus.COMPLETED,
        summary=f"[{request.agent_name}] 모의 실행 결과 완료",
        structured_result={"count": 5},
        features="s3://mock/results.geojson",
        created_at=datetime.utcnow()
    )
