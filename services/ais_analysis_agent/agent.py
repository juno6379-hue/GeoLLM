import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from shared.schemas.agent import AgentRequest, AgentStatus, AgentResult
from shared.observability.logger import get_logger
from services.ais_analysis_agent.tools import search_ais_track
from services.orchestrator.specialist_kg_context import build_specialist_kg_context
import os

logger = get_logger("ais_analysis_agent")

from services.orchestrator.agent_execution_gate import validated_agent


@validated_agent('AIS Analysis Agent')
async def execute_ais_analysis(request: AgentRequest) -> AgentResult:
    logger.info(f"[AIS Analysis Agent] Started task for query: {request.original_query}")
    
    intent = request.parsed_intent
    target_objects = intent.target_objects if intent else []
    kg_context = build_specialist_kg_context("traffic", request)
    
    # 1. 대상 선박 파악
    target = target_objects[0] if target_objects else ""
    if not target:
        for word in request.original_query.split():
            if word.isdigit() and len(word) == 9:
                target = word
                break
        if not target:
            # 쿼리에서 직접 추출 시도
            target = request.original_query.replace("항적", "").replace("찾아줘", "").replace("분석해줘", "").strip()
            
    if not target:
        return AgentResult(
            task_id=request.task_id,
            trace_id=request.trace_id,
            agent_name="AIS Analysis Agent",
            agent_version="1.0",
            status=AgentStatus.NEEDS_CLARIFICATION,
            clarification_questions=["분석할 대상 선박의 이름이나 MMSI(9자리 숫자)를 알려주세요."]
        )
        
    logger.info(f"Target ship/MMSI identified: {target}")
    
    # 2. AIS 데이터 검색 툴 호출 (No Mocks, Data-Driven)
    search_result = search_ais_track(target)
    
    if "error" in search_result:
        logger.error(f"AIS Search failed: {search_result['error']}")
        return AgentResult(
            task_id=request.task_id,
            trace_id=request.trace_id,
            agent_name="AIS Analysis Agent",
            agent_version="1.0",
            status=AgentStatus.FAILED,
            error_message=search_result["error"]
        )
        
    # 3. LLM을 통한 분석 브리핑 생성
    point_count = search_result.get("point_count", 0)
    stats = search_result.get("stats", {})
    ship_name = search_result.get("ship_name") or target
    mmsi = search_result.get("mmsi") or target
    
    briefing = "분석 불가"
    
    try:
        from services.llm_config import llm_api_enabled
        if llm_api_enabled():
            model_name = os.environ.get("LLM_MODEL", "gpt-4o-mini")
            llm = ChatOpenAI(model=model_name, temperature=0.2)
            
            sys_msg = SystemMessage(content='''당신은 해상 통항 및 선박 궤적을 분석하는 AIS 분석 전문가입니다.
주어진 AIS 데이터 통계를 바탕으로 선박의 운항 특징(평균 속도, 최대 속도, 데이터 볼륨 등)을 전문가처럼 요약하여 브리핑하세요.
짧고 명료하게 3~4문장으로 답변하십시오.''')
            
            prompt = f"""
분석 대상 선박: {ship_name} (MMSI: {mmsi})
항적 데이터(Points) 수: {point_count}
평균 속도(SOG): {stats.get('avg_speed', 'N/A')} 노트
최대 속도(SOG): {stats.get('max_speed', 'N/A')} 노트

위 데이터를 바탕으로 분석 보고서(브리핑)를 작성해주세요.
"""
            response = await llm.ainvoke([sys_msg, HumanMessage(content=prompt)])
            briefing = response.content.strip()
    except Exception as e:
        logger.error(f"LLM Summary generation failed: {e}")
        briefing = f"{ship_name} (MMSI: {mmsi}) 선박의 항적 {point_count}개가 확인되었습니다. (LLM 브리핑 실패)"
        
    logger.info(f"[AIS Analysis Agent] Finished task. Briefing generated.")
    
    return AgentResult(
        task_id=request.task_id,
        trace_id=request.trace_id,
        agent_name="AIS Analysis Agent",
        agent_version="1.0",
        status=AgentStatus.RESULTS_AGGREGATED,
        structured_result={
            "briefing": briefing,
            "mmsi": mmsi,
            "ship_name": ship_name,
            "stats": stats,
            "point_count": point_count,
            "kg_context": kg_context,
            "traffic_analysis": kg_context["traffic_metrics"],
            "target_dynamic_layers": kg_context["target_dynamic_layers"],
            "dynamic_traffic_geojson": search_result.get("geojson"),
            "static_feature_relations": [
                {"relation": "nearFeature", "status": "PENDING_STATIC_FEATURE_GEOMETRY", "verified": False},
                {"relation": "overlapsFeature", "status": "PENDING_STATIC_FEATURE_GEOMETRY", "verified": False},
                {"relation": "relatedTo", "status": "CANDIDATE", "verified": False, "reason": "DynamicTrafficLayer to S-101 feature relation requires evidence"},
            ],
        },
        provenance=kg_context["provenance"],
        validation_payload={
            "type": "ais_track",
            "point_count": point_count
        }
    )
