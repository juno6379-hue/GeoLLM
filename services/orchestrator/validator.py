from shared.schemas.agent import AgentResult, AgentStatus
from shared.observability.logger import get_logger

logger = get_logger("orchestrator.validator")

def validate_agent_result(agent_result: AgentResult) -> AgentResult:
    """
    각 에이전트의 수행 결과를 검증(Validation)합니다.
    환각 현상(근거 없는 답변)이나 치명적 오류가 의심될 경우 NEEDS_HITL 상태로 전환합니다.
    """
    warnings = agent_result.warnings or []
    confidence_score = 1.0
    needs_hitl = False
    
    if agent_result.status == AgentStatus.FAILED:
        return agent_result # 이미 실패한 경우 그대로 통과
        
    # 1. RAG Agent 검증: 근거(Evidence) 없이 요약만 있는 경우 의심
    if agent_result.agent_name == "standard-rag-agent":
        retrieved_count = agent_result.structured_result.get("retrieved_count", 0) if agent_result.structured_result else 0
        if retrieved_count == 0:
            warnings.append("검색된 문서(Evidence)가 없어 환각 가능성이 있습니다.")
            confidence_score = 0.3
            needs_hitl = True
            
    # 2. Spatial Analysis Agent 검증: 비정상적인 파라미터나 너무 많은 데이터 반환 시 경고
    if agent_result.agent_name == "spatial-analysis-agent":
        count = agent_result.structured_result.get("count", 0) if agent_result.structured_result else 0
        if count > 10000:
            warnings.append("반환된 공간 객체가 너무 많습니다(10000개 초과). 시스템 과부하 또는 화면 렌더링 지연이 우려됩니다.")
            confidence_score = 0.5
            needs_hitl = True
            
    agent_result.warnings = warnings
    
    # 만약 결과가 의심스럽다면 상태를 NEEDS_HITL (Human-In-The-Loop 대기)로 변경
    if needs_hitl:
        logger.warning("Agent result needs human validation (HITL)", task_id=agent_result.task_id, warnings=warnings)
        agent_result.status = AgentStatus.NEEDS_HITL
        
    return agent_result
