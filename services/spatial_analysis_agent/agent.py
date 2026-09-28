import os
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from shared.schemas.agent import AgentRequest, AgentResult, AgentStatus, ToolCallLog, PlanStatus, QueryExecutionContext
from services.spatial_analysis_agent.schemas import SpatialDSL, SpatialFunctionName, QueryPlan, TargetInfo, LocationInfo, SpatialInfo, OutputInfo
from services.spatial_analysis_agent.validator import validate_dsl, validate_query_plan
from services.spatial_analysis_agent.tool_executor import execute_spatial_tool
from services.spatial_analysis_agent.risk_evaluator import risk_evaluator
from shared.observability.logger import get_logger
from services.llm_config import llm_api_enabled
from services.orchestrator.specialist_kg_context import build_specialist_kg_context

logger = get_logger("spatial_analysis_agent")

def _readiness_value(qec: QueryExecutionContext | None) -> str:
    if not qec:
        return ""
    return qec.readiness.value if hasattr(qec.readiness, "value") else str(qec.readiness)

def _contract_blocked_result(request: AgentRequest, status: AgentStatus, reason: str, blockers: list[str] | None = None) -> AgentResult:
    blockers = blockers or [reason]
    return AgentResult(
        task_id=request.task_id,
        trace_id=request.trace_id,
        agent_name="spatial-analysis-agent",
        agent_version="2.0.0-contract",
        status=status,
        error_code="EXECUTION_CONTRACT_NOT_READY",
        summary="검증된 실행계약이 없어 공간분석을 실행하지 않았습니다.",
        answer_text="공간분석 실행에 필요한 위치, 대상, 도구 또는 데이터 연결 정보가 아직 확정되지 않았습니다.",
        structured_result={
            "blockers": blockers,
            "query_execution_context": request.query_execution_context.model_dump(mode="json") if request.query_execution_context else None,
        },
        warnings=blockers,
        provenance={"contract_required": True},
        created_at=datetime.utcnow(),
    )

def _spatial_context_geometry(qec: QueryExecutionContext) -> Optional[str]:
    spatial_context = qec.spatial.get("spatial_context") if isinstance(qec.spatial, dict) else None
    if isinstance(spatial_context, dict):
        return spatial_context.get("geometry")
    return None

def _query_plan_from_contract(request: AgentRequest, qec: QueryExecutionContext) -> QueryPlan:
    slots = qec.slots
    route_plan = qec.route_plan or {}
    analysis_type = route_plan.get("analysis_type") or slots.analysis_type or slots.operation
    if analysis_type in ("feature_search_by_radius", "feature_dwithin"):
        qp_analysis_type = "feature_dwithin"
        relation = "dwithin"
    elif analysis_type in ("feature_within_area", "spatial_feature_search"):
        qp_analysis_type = "feature_within_area"
        relation = "intersects"
    elif analysis_type in ("nearest_feature", "nearest_feature_search"):
        qp_analysis_type = "nearest_feature"
        relation = "nearest"
    else:
        qp_analysis_type = analysis_type or "feature_within_area"
        relation = slots.spatial_relation or "intersects"

    feature_names = slots.resolved_target_set or slots.target_features
    target_layers = slots.target_layers or [binding.dataset_id for binding in qec.data_bindings] or ["GBENC_S101_feature"]
    base_geometry = slots.reference_geometry or _spatial_context_geometry(qec)
    limit = slots.filters.get("k", slots.filters.get("limit", 1)) if analysis_type in ("nearest_feature", "nearest_feature_search") else slots.filters.get("limit", 100)

    return QueryPlan(
        query_id=request.task_id,
        intent=route_plan.get("intent") or (request.parsed_intent.intent_type if request.parsed_intent else "spatial_search"),
        analysis_type=qp_analysis_type,
        target=TargetInfo(
            original_term=slots.target_term,
            concept_id=slots.concept_id or slots.derived_concept,
            nftc_codes=slots.nftc_codes,
            feature_names=feature_names,
            resolution_status="RESOLVED",
        ),
        location=LocationInfo(
            original_text=slots.location_text or slots.location,
            geometry_source="EXECUTION_CONTRACT",
            resolution_status=slots.resolution_status or "RESOLVED",
        ),
        spatial=SpatialInfo(
            relation=relation,
            distance_m=slots.distance_m,
        ),
        output=OutputInfo(limit=int(limit)),
        required_tools=[binding.tool_id for binding in qec.tool_bindings],
        execution_status="READY",
        conditions={
            "target_layers": target_layers,
            "_query_execution_context": qec.model_dump(mode="json"),
            "_contract_enforced": True,
        },
        base_geometry=base_geometry,
    )

from services.orchestrator.agent_execution_gate import validated_agent


@validated_agent('Spatial Analysis Agent')
async def execute_spatial_analysis(request: AgentRequest) -> AgentResult:
    """
    Spatial Analysis Agent Core Logic.
    LLM을 통해 Spatial DSL을 생성하고, 엄격한 Validation을 거친 뒤 Executor를 호출합니다.
    """
    logger.info("Starting spatial analysis", task_id=request.task_id)
    
    qec = request.query_execution_context
    readiness = _readiness_value(qec)
    if not qec:
        return _contract_blocked_result(request, AgentStatus.FAILED, "BLOCKED_CONFIG: query_execution_context is required")
    from services.orchestrator.execution_validator import is_execution_authorized
    if not is_execution_authorized(qec):
        blockers = qec.blockers or [f"Execution readiness is {readiness or 'UNKNOWN'}"]
        status = AgentStatus.NEEDS_CLARIFICATION if any(str(b).startswith("NEEDS_USER_INPUT") for b in blockers) else AgentStatus.BLOCKED
        return _contract_blocked_result(request, status, "Execution contract is not ready", blockers)
    contract_enforced = True
    query = request.original_query
    exec_slots = qec.slots
    try:
        kg_context = build_specialist_kg_context("spatial", request)
    except Exception as exc:
        logger.warning("Specialist KG context unavailable; continuing with execution contract", error=str(exc))
        kg_context = {
            "target_layers": exec_slots.target_layers or [binding.dataset_id for binding in qec.data_bindings],
            "target_features": exec_slots.resolved_target_set or exec_slots.target_features,
            "graph_paths": qec.rag.get("graph_paths", {}),
            "provenance": qec.kg.get("provenance", {}) if isinstance(qec.kg, dict) else {},
            "source": "query_execution_context",
        }
    
    # 기본 Fallback DSL 세팅 (geometry가 없으면 None으로 두고 나중에 지오코딩으로 채움)
    fallback_target_layers = kg_context["target_layers"]
    fallback_features = kg_context["target_features"]
    if exec_slots and exec_slots.target_layers:
        fallback_target_layers = exec_slots.target_layers
    if exec_slots and exec_slots.target_features:
        fallback_features = exec_slots.target_features
    if request.task_plan and request.task_plan.slots:
        if request.task_plan.slots.get("target_features"):
            fallback_target_layers = ["gbenc_feature"]  # S-101 features usually go to GBENC
            fallback_features = request.task_plan.slots.get("target_features")

    requested_location = None
    if exec_slots and exec_slots.location:
        requested_location = exec_slots.location
    elif request.spatial_context and request.spatial_context.base_location:
        requested_location = request.spatial_context.base_location
    elif request.task_plan and request.task_plan.slots:
        requested_location = request.task_plan.slots.get("location")

    requested_geometry = (
        request.spatial_context.geometry
        if request.spatial_context and request.spatial_context.geometry
        else None
    )
    requested_distance_m = None
    if exec_slots and exec_slots.distance_m is not None:
        requested_distance_m = exec_slots.distance_m
    elif request.task_plan and request.task_plan.slots:
        requested_distance_m = request.task_plan.slots.get("distance_m")
    elif request.spatial_context:
        requested_distance_m = request.spatial_context.buffer_distance

    dsl = QueryPlan(
        query_id=request.task_id,
        intent=request.parsed_intent.intent_type if request.parsed_intent else "spatial_search",
        analysis_type="feature_dwithin" if requested_distance_m is not None else "feature_within_area",
        target=TargetInfo(
            feature_names=fallback_features,
            nftc_codes=exec_slots.nftc_codes if exec_slots else []
        ),
        location=LocationInfo(
            original_text=requested_location
        ),
        spatial=SpatialInfo(
            relation="intersects",
            distance_m=requested_distance_m
        ),
        output=OutputInfo(limit=100),
        base_geometry=requested_geometry
    )
    if contract_enforced:
        dsl = _query_plan_from_contract(request, qec)
    if not contract_enforced:
        dsl.conditions["target_layers"] = fallback_target_layers
    dsl.conditions["source"] = kg_context.get("source", "S100_dev_postgis v2")
    if qec:
        dsl.conditions["_query_execution_context"] = qec.model_dump(mode="json")
    
    tool_calls = []
    validation_payload = {"status": "SUCCESS", "errors": []}
    
    # 메타데이터를 기반으로 DSL 초기 속성 세팅 (LLM 스킵 안 함)
    resolved_metadata = None if contract_enforced else request.previous_agent_outputs.get("resolved_metadata")
    if resolved_metadata:
        logger.info("Injecting resolved_metadata into DSL conditions and LLM context.")
        
        feature_policies = resolved_metadata.get("feature_policies", {})
        render_styles = {}
        popup_fields = {}
        post_processors = {}
        
        for fname, policy in feature_policies.items():
            if "default_style" in policy:
                render_styles[fname] = policy["default_style"]
            if "default_popup_fields" in policy:
                popup_fields[fname] = policy["default_popup_fields"]
            if "post_processor" in policy:
                post_processors[fname] = policy["post_processor"]
                
        if render_styles:
            dsl.conditions["_render_styles"] = render_styles
        if popup_fields:
            dsl.conditions["_popup_fields"] = popup_fields
        if post_processors:
            dsl.conditions["_post_processors"] = post_processors
            
        dsl.target.nftc_codes = resolved_metadata.get("nftc_codes", [])
        
        resolved_features = resolved_metadata.get("resolved_features", [])
        dsl.target.feature_names = [f["feature_name"] for f in resolved_features if "feature_name" in f]
            
    elif not contract_enforced and request.previous_agent_outputs and request.previous_agent_outputs.get("resolved_nftc_codes"):
        dsl.target.nftc_codes = request.previous_agent_outputs.get("resolved_nftc_codes")

    # 1. LLM Spatial DSL Extraction
    if (not contract_enforced) and llm_api_enabled():
        try:
            from services.spatial_analysis_agent.spatial_catalog_tool import lookup_spatial_catalog
            from services.spatial_analysis_agent.geocoding_tool import get_maritime_coordinates
            from services.spatial_analysis_agent.reverse_geocoding_tool import get_location_name_from_coordinates
            from services.spatial_analysis_agent.s111_semantic_tool import search_s111_semantic
            from langchain_core.messages import ToolMessage
            
            model_name = os.environ.get("LLM_MODEL", "gpt-4o")
            llm = ChatOpenAI(model=model_name, temperature=0)
            
            metadata_prompt = ""
            # === [NEW BYPASS LOGIC] ===
            # If the orchestrator has already resolved the target features perfectly,
            # we can bypass the heavy LLM DSL generation and go straight to the rule-based fallback.
            if request.parsed_intent and request.parsed_intent.intent_type == "SPATIAL_SEARCH" and resolved_metadata and "resolved_nftc_codes" in request.previous_agent_outputs:
                logger.info("Bypassing LLM spatial extraction because resolved metadata is present. Fast-path triggered.")
            
                # Orchestrator (semantic_router)에서 이미 '부근/근처' 규칙으로 추출한 거리가 있다면 우선 적용
                buffer_dist = None
                if request.spatial_context and request.spatial_context.buffer_distance is not None:
                    buffer_dist = request.spatial_context.buffer_distance
                else:
                    cond_str = " ".join(request.parsed_intent.spatial_conditions) if request.parsed_intent and request.parsed_intent.spatial_conditions else ""
                    import re
                    m = re.search(r'(\d+)(km|m)', cond_str)
                    if m:
                        val = float(m.group(1))
                        buffer_dist = val * 1000 if m.group(2) == 'km' else val
                    elif any(k in cond_str for k in ["부근", "근처", "주변"]):
                        buffer_dist = 3000
                        logger.info("Rule-based fallback: Found '부근/근처/주변', setting default buffer to 3000m")
                
                analysis_type = "feature_dwithin" if buffer_dist else "feature_within_area"
            
                dsl = QueryPlan(
                    query_id=request.task_id,
                    intent=request.parsed_intent.intent_type if request.parsed_intent else "spatial_search",
                    analysis_type=analysis_type,
                    target=TargetInfo(
                        original_term=resolved_metadata.get("input_term"),
                        concept_id=resolved_metadata.get("canonical_term"),
                        nftc_codes=request.previous_agent_outputs.get("resolved_nftc_codes", []),
                        feature_names=[resolved_metadata.get("selected_feature", "")] if resolved_metadata.get("selected_feature") else [],
                        resolution_status="RESOLVED"
                    ),
                    location=LocationInfo(
                        original_text=request.spatial_context.base_location if request.spatial_context else None,
                        place_id=None,
                        geometry_source="GAZETTEER",
                        resolution_status="RESOLVED"
                    ),
                    spatial=SpatialInfo(
                        relation="dwithin" if buffer_dist else "intersects",
                        distance_m=buffer_dist
                    ),
                    output=OutputInfo(limit=100)
                )
            else:
                if resolved_metadata:
                    metadata_prompt = f"\n[오케스트레이터 전달 사항] 사용자 대상 객체 메타데이터: {resolved_metadata}\n이를 최우선으로 참고하여 가장 적합한 분석 함수(tool_name)를 선택하세요."
            
                sys_msg = f"""당신은 해양공간 지능플랫폼의 Spatial Analysis Agent입니다.
    사용자가 특정 공간 객체나 데이터셋(예: 양식장, 항로, 침선, 등대, 조난사고 등)을 찾고자 할 경우, 
    반드시 `lookup_spatial_catalog` 도구를 호출하여 정확한 target_layer와 nftc 코드를 먼저 알아내세요.
    단, [오케스트레이터 전달 사항]이 있다면 이를 최우선으로 활용하세요.
    또한, 사용자가 특정 지명(예: "여수 앞바다", "부산항")을 언급한 경우,
    반드시 `get_maritime_coordinates` 도구를 호출하여 해당 지명의 WKT 좌표(POINT)를 알아내세요.
    반대로 사용자가 특정 좌표(예: POINT(127.7 34.7))를 주고 "여기가 어디야?"라고 묻거나 주변 지명을 요구하는 경우,
    반드시 `get_location_name_from_coordinates` 도구를 호출하여 인접 랜드마크와의 거리 정보를 알아내세요.

    [중요] 사용자가 "조류", "해수유동", "물살"과 관련된 추상적 위험도나 상태(예: "물살이 거세서 배가 지나가기 힘든 곳")를 검색하려 한다면,
    반드시 `search_s111_semantic` 도구를 호출하여 시맨틱 검색을 수행하세요.
    그 외의 경우 즉시 답변을 진행합니다.{metadata_prompt}
    """
                messages = [
                    SystemMessage(content=sys_msg),
                    HumanMessage(content=query)
                ]
                # 1단계 (Optional): 추가 정보 조회가 필요한 경우 Tool 호출
                tools = [
                    search_s111_semantic,
                    lookup_spatial_catalog,
                    get_maritime_coordinates,
                    get_location_name_from_coordinates
                ]
                try:
                    llm_with_tools = llm.bind_tools(tools)
                    tool_res = await llm_with_tools.ainvoke(messages)
                
                    if hasattr(tool_res, "tool_calls") and tool_res.tool_calls:
                        messages.append(tool_res)
                        for tc in tool_res.tool_calls:
                            if tc["name"] == "search_s111_semantic":
                                tool_res = search_s111_semantic.invoke(tc["args"])
                                if "structured_result" in tool_res:
                                    # Tool이 바로 최종 결과를 만들어낸 특수한 경우
                                    return AgentResult(
                                        task_id=request.task_id,
                                        trace_id=request.trace_id,
                                        agent_name="spatial-analysis-agent",
                                        agent_version="2.0.0-dsl",
                                        status=AgentStatus.COMPLETED,
                                        summary=f"특수 동적 분석 완료: {tool_res['structured_result']['map_spec']['title']}",
                                        structured_result=tool_res["structured_result"],
                                        output_layers=[{"layer_id": tool_res["structured_result"]["map_spec"]["layer_id"], "type": "GEOMETRY"}],
                                        tool_calls=[ToolCallLog(tool_name="search_s111_semantic", status="SUCCESS", execution_time_ms=tool_res["execution_time"])],
                                        created_at=datetime.utcnow()
                                    )
                                else:
                                    messages.append(ToolMessage(content=str(tool_res), tool_call_id=tc["id"]))
                            elif tc["name"] == "lookup_spatial_catalog":
                                tool_res = lookup_spatial_catalog.invoke(tc["args"])
                                messages.append(ToolMessage(content=str(tool_res), tool_call_id=tc["id"]))
                            elif tc["name"] == "get_maritime_coordinates":
                                tool_res = get_maritime_coordinates.invoke(tc["args"])
                                messages.append(ToolMessage(content=str(tool_res), tool_call_id=tc["id"]))
                            elif tc["name"] == "get_location_name_from_coordinates":
                                tool_res = get_location_name_from_coordinates.invoke(tc["args"])
                                messages.append(ToolMessage(content=str(tool_res), tool_call_id=tc["id"]))
                except Exception as e:
                    logger.warning("Tool binding or execution failed (likely unsupported model). Skipping Step 1.", error=str(e))

                # 2단계: 최종 QueryPlan 추출
                structured_llm = llm.with_structured_output(QueryPlan, method="json_mode")
                final_sys_msg = (
                    "이제 수집된 정보를 바탕으로 다음 작업을 수행하세요:\n"
                    "1. 사용자의 질의에 가장 적합한 공간 분석 함수를 선택하여 QueryPlan JSON으로 변환하세요.\n"
                    "2. analysis_type은 'feature_dwithin', 'feature_within_area', 'nearest_feature' 중 하나를 선택하세요.\n"
                    "3. target.nftc_codes 에 검색된 코드 배열을 넣으세요.\n"
                    "4. location.place_id 에 get_maritime_coordinates 등에서 알아낸 place_id가 있다면 넣고, 없다면 original_text라도 채우세요."
                )
                messages.append(SystemMessage(content=final_sys_msg))
            
                qp_result: QueryPlan = await structured_llm.ainvoke(messages)
            
                # 3. Validation
                is_valid, errors = validate_query_plan(qp_result)
                if not is_valid:
                    logger.warning("DSL Validation Failed", errors=errors)
                    validation_payload["status"] = "FAILED"
                    validation_payload["errors"] = errors
                    # TODO: Re-planning 로직 (에러 피드백을 주고 LLM 재호출)
                else:
                    dsl = qp_result
                    logger.info("QueryPlan generated and validated successfully", analysis_type=dsl.analysis_type)
                
        except Exception as e:
            logger.error("LLM DSL extraction failed", error=str(e))
            # 오류 발생 시 dsl을 기본 fallback 객체로 유지하되, 기존 분석 결과가 있다면 최대한 활용
            if resolved_metadata:
                dsl.target.feature_names = [resolved_metadata.get("selected_feature", "")]
                dsl.target.nftc_codes = request.previous_agent_outputs.get("resolved_nftc_codes", [])
                logger.info("Using resolved_metadata for fallback DSL due to LLM failure")
            
    # LLM이 없는 환경이거나 LLM이 실패하여 location 정보가 없는 경우 룰베이스 보정
    if (not contract_enforced) and not dsl.location.place_id and not dsl.location.original_text:
        if request.spatial_context and request.spatial_context.base_location:
            dsl.location.original_text = request.spatial_context.base_location
            logger.info("Rule-based location fallback", location=dsl.location.original_text)

    # Resolve named places before SQL compilation. The compiler requires a
    # place_id or a concrete WKT base geometry for spatial operations.
    if (not contract_enforced) and not dsl.base_geometry and dsl.location.original_text:
        try:
            from services.spatial_analysis_agent.geocoding_tool import get_maritime_coordinates

            place_name = dsl.location.original_text
            for suffix in ("입구", "주변", "근처", "일대", "반경", "이내"):
                place_name = place_name.replace(suffix, " ")
            place_name = " ".join(place_name.split())
            resolved_wkt = get_maritime_coordinates.invoke(place_name)
            if isinstance(resolved_wkt, str) and resolved_wkt.upper().startswith("POINT"):
                dsl.base_geometry = resolved_wkt
                dsl.location.geometry_source = "GAZETTEER"
                dsl.location.resolution_status = "RESOLVED"
                logger.info("Location resolved for spatial query", location=place_name, geometry=resolved_wkt)
            else:
                logger.warning("Location geocoding did not return WKT", location=place_name, result=resolved_wkt)
        except Exception as e:
            logger.warning("Location geocoding failed", location=dsl.location.original_text, error=str(e))
                
    # Fallback 시 buffer_distance가 없다면 orchestrator가 파싱한 텍스트에서 추출
    if (not contract_enforced) and dsl.spatial.distance_m is None and request.parsed_intent and request.parsed_intent.spatial_conditions:
        cond_str = " ".join(request.parsed_intent.spatial_conditions)
        import re
        m = re.search(r'(\d+)(km|m)', cond_str)
        if m:
            val = float(m.group(1))
            if m.group(2) == 'km':
                dsl.spatial.distance_m = val * 1000
            else:
                dsl.spatial.distance_m = val
            dsl.analysis_type = "feature_dwithin"
            logger.info(f"Rule-based extracted distance_m: {dsl.spatial.distance_m}")
                
    # Orchestrator(Feature Resolver)에서 분석된 NFTC 코드가 있다면 무조건 강제로 덮어쓰기 (LLM Fallback 상황 포함)
    if (not contract_enforced) and request.previous_agent_outputs and request.previous_agent_outputs.get("resolved_nftc_codes"):
        dsl.target.nftc_codes = request.previous_agent_outputs["resolved_nftc_codes"]
        # target_feature_names 도 덮어쓰기 (쿼리 템플릿 호환용)
        resolved_md = request.previous_agent_outputs.get("resolved_metadata", {})
        if "selected_feature" in resolved_md and resolved_md["selected_feature"]:
            if not dsl.target.feature_names:
                dsl.target.feature_names = [resolved_md["selected_feature"]]

    if (not contract_enforced) and not dsl.target.nftc_codes:
        dsl.target.nftc_codes = [0]
    if dsl.spatial.distance_m is not None:
        dsl.analysis_type = "feature_dwithin"
    elif dsl.analysis_type == "feature_search_by_radius":
        dsl.analysis_type = "feature_within_area"
        
    # Frontend에서 map_bounds가 넘어온 경우
    if request.spatial_context and request.spatial_context.map_bounds:
        dsl.spatial.map_bounds_required = True
        
    # Clarification Check (Missing parameter)
    if dsl.analysis_type == "feature_dwithin" and dsl.spatial.distance_m is None:
        logger.warning("Missing buffer_distance for dwithin/buffer. Requesting clarification.")
        return AgentResult(
            task_id=request.task_id,
            trace_id=request.trace_id,
            agent_name="spatial-analysis-agent",
            agent_version="2.0.0-dsl",
            status=AgentStatus.NEEDS_CLARIFICATION,
            clarification_questions=["분석에 필요한 거리(반경) 정보가 없습니다. 어느 정도 범위로 탐색할까요?"],
            clarification_options=[
                {"label": "1km 이내", "value": "1000"},
                {"label": "3km 이내", "value": "3000"},
                {"label": "5km 이내", "value": "5000"},
                {"label": "10km 이내", "value": "10000"}
            ],
            structured_result={"reason": "Missing buffer_distance"},
            created_at=datetime.utcnow()
        )
            
    # 3. Tool 실행
    clearance_level = request.security_context.clearance_level if request.security_context else "PUBLIC"
    tool_result = execute_spatial_tool(
        dsl=dsl, 
        trace_id=request.trace_id,
        task_id=request.task_id,
        user_id=request.user_id,
        clearance_level=clearance_level
    )
    
    tool_calls.append(ToolCallLog(
        tool_name=tool_result.tool_name,
        status=tool_result.status,
        execution_time_ms=tool_result.execution_time
    ))
    
    # 4. 결과 통합
    if tool_result.status == "FAILED":
        return AgentResult(
            task_id=request.task_id,
            trace_id=request.trace_id,
            agent_name="spatial-analysis-agent",
            agent_version="2.0.0-dsl",
            status=AgentStatus.FAILED,
            error_code=getattr(tool_result, "error_code", "UNKNOWN_ERROR"),
            summary="공간 분석 툴 실행에 실패했습니다.",
            warnings=tool_result.errors,
            tool_calls=tool_calls,
            validation_payload=validation_payload,
            created_at=datetime.utcnow()
        )
        
    res_dict = tool_result.structured_result or {}
    count = res_dict.get("count", 0)
    map_spec_dict = res_dict.get("map_spec")
    qec_payload = qec.model_dump(mode="json") if qec else {}
    
    # [MOCK INJECTION REMOVED] DB에 데이터가 없으면 즉시 에러(실패) 반환
    if count == 0:
        logger.warning("No features found from spatial query.")
        
        # dsl 속성 접근 분기 (QueryPlan vs SpatialDSL)
        if hasattr(dsl, "analysis_type"):
            tool_name_val = getattr(dsl, "analysis_type", "")
            distance_val = dsl.spatial.distance_m if dsl.spatial else None
            crs_val = "EPSG:4326"
            reasoning_val = "QueryPlan 기반 공간 분석"
            query_dump = dsl.model_dump()
        else:
            tool_name_val = dsl.tool_name.value if hasattr(dsl.tool_name, "value") else str(dsl.tool_name)
            distance_val = getattr(dsl, "buffer_distance", None)
            crs_val = getattr(dsl, "crs", "EPSG:4326")
            reasoning_val = getattr(dsl, "reasoning", "")
            query_dump = dsl.model_dump()
            
        return AgentResult(
            task_id=request.task_id,
            trace_id=request.trace_id,
            agent_name="spatial-analysis-agent",
            agent_version="2.0.0-dsl",
            status=AgentStatus.COMPLETED,
            error_code=getattr(tool_result, "error_code", "EMPTY_RESULT"),
            summary="해당 조건(범위) 내에서 일치하는 객체를 찾을 수 없습니다.",
            answer_text="해당 조건(범위) 내에서 일치하는 객체를 찾을 수 없습니다.",
            spatial_result_summary={"feature_count": 0, "distance_m": distance_val, "crs": crs_val},
            warnings=["조회된 데이터가 없습니다."],
            structured_result={
                "count": count,
                "crs": crs_val,
                "distance": distance_val,
                "map_spec": map_spec_dict,
                "kg_context": kg_context,
                "query_execution_context": qec_payload,
                "spatial_provenance": {"query_template": "postgis.intersection" if "intersection" in tool_name_val else "", "executed_query": res_dict.get("executed_query", ""), "dsl_query": query_dump},
                "kg_provenance": kg_context,
            },
            output_layers=[{"layer_id": map_spec_dict["layer_id"], "type": "GEOMETRY"}] if map_spec_dict else [],
            tool_calls=tool_calls,
            validation_payload=validation_payload,
            provenance={
                "spatial": {"query_template": "postgis.intersection" if "intersection" in tool_name_val else "", "executed_query": res_dict.get("executed_query", ""), "dsl_query": query_dump},
                "kg": kg_context,
                "rag": qec_payload.get("rag", {}),
                "kg_context": kg_context,
                "dsl_query": query_dump, 
                "query_template": "postgis.intersection" if "intersection" in tool_name_val else "",
                "executed_query": res_dict.get("executed_query", "")
            },
            created_at=datetime.utcnow()
        )
    
    # dsl 속성 접근 분기
    if hasattr(dsl, "analysis_type"):
        tool_name_val = getattr(dsl, "analysis_type", "")
        distance_val = dsl.spatial.distance_m if dsl.spatial else None
        crs_val = "EPSG:4326"
        reasoning_val = "QueryPlan 기반 공간 분석"
        query_dump = dsl.model_dump()
    else:
        tool_name_val = dsl.tool_name.value if hasattr(dsl.tool_name, "value") else str(dsl.tool_name)
        distance_val = getattr(dsl, "buffer_distance", None)
        crs_val = getattr(dsl, "crs", "EPSG:4326")
        reasoning_val = getattr(dsl, "reasoning", "")
        query_dump = dsl.model_dump()

    # 5. 결과를 사람이 이해하기 쉽게 요약 (LLM 활용)
    final_summary = f"공간 연산({tool_name_val}) 결과, 총 {count}개의 객체가 식별되었습니다. (논리: {reasoning_val})"
    
    if llm_api_enabled():
        try:
            model_name = os.environ.get("LLM_MODEL", "gpt-4o-mini")
            summary_llm = ChatOpenAI(model=model_name, temperature=0)
            summary_msg = SystemMessage(content="당신은 분석 결과를 사람이 이해하기 쉽게 요약해주는 어시스턴트입니다. 사용자의 질문과 도출된 객체 수, 쿼리 논리를 바탕으로 친절하고 명확하게 1~2문장으로 요약하세요.")
            user_msg = HumanMessage(content=f"질문: {query}\n발견된 객체 수: {count}\n판단 논리: {reasoning_val}")
            res = await summary_llm.ainvoke([summary_msg, user_msg])
            final_summary = res.content.strip()
        except Exception as e:
            logger.warning("LLM Summary failed", error=str(e))
            
    return AgentResult(
        task_id=request.task_id,
        trace_id=request.trace_id,
        agent_name="spatial-analysis-agent",
        agent_version="2.0.0-dsl",
        status=AgentStatus.COMPLETED,
        summary=final_summary,
        answer_text=final_summary,
        spatial_result_summary={"feature_count": count, "distance_m": distance_val, "crs": crs_val},
        structured_result={
            "count": count,
            "crs": crs_val,
            "distance": distance_val,
            "map_spec": map_spec_dict,
            "kg_context": kg_context,
            "query_execution_context": qec_payload,
            "spatial_provenance": {"query_template": "postgis.intersection" if "intersection" in tool_name_val else "", "executed_query": res_dict.get("executed_query", ""), "dsl_query": query_dump},
            "kg_provenance": kg_context,
        },
        output_layers=[{"layer_id": map_spec_dict["layer_id"], "type": "GEOMETRY"}] if map_spec_dict else [],
        tool_calls=tool_calls,
        validation_payload=validation_payload,
        features=json.dumps(tool_result.output_references[0], ensure_ascii=False) if tool_result.output_references else None,
        provenance={
            "spatial": {"query_template": "postgis.intersection" if "intersection" in tool_name_val else "", "executed_query": res_dict.get("executed_query", ""), "dsl_query": query_dump},
            "kg": kg_context,
            "rag": qec_payload.get("rag", {}),
            "kg_context": kg_context,
            "dsl_query": query_dump, 
            "query_template": "postgis.intersection" if "intersection" in tool_name_val else "",
            "executed_query": res_dict.get("executed_query", "")
        },
        created_at=datetime.utcnow()
    )
