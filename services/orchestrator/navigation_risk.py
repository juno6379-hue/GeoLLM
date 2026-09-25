"""Navigation risk evidence assembly with explicit spatial and evidence limits."""
import asyncio

from services.orchestrator.port_context import PortContextError, resolve_port_context
from services.orchestrator.quality import unmeasured_quality


async def navigation_risk_analysis_node(state):
    from services.orchestrator.graph import _legal_notice_documents_for_query
    from services.orchestrator.traffic_execution import execute_traffic_request

    query = state.get("query") or ""
    spatial = state.get("spatial_context") or {}
    if hasattr(spatial, "model_dump"):
        spatial = spatial.model_dump()
    task_id = state["task_id"]
    docs, traffic, errors = [], None, []
    location = None
    executed_tools = []
    status, code = "PARTIAL", None
    try:
        location = await asyncio.to_thread(resolve_port_context, query, spatial)
    except PortContextError as exc:
        code = exc.code
        status = "BLOCKED" if code in {"PORT_SOURCE_UNAVAILABLE", "INVALID_PORT_POLICY"} else "NEEDS_CLARIFICATION"
        answer = str(exc)
    else:
        grounded_query = query + " " + location["port"]
        docs = _legal_notice_documents_for_query(grounded_query)
        executed_tools.append({"tool_id": "registry.legal_notice_lookup", "status": "SUCCESS", "result_count": len(docs)})
        traffic_state = {**state, "spatial_context": {
            "geometry": location["geometry"], "crs": "EPSG:4326",
            "base_location": location["port"],
            "buffer_distance": spatial.get("buffer_distance"),
        }}
        try:
            traffic = await asyncio.to_thread(execute_traffic_request, traffic_state)
            executed_tools.append({"tool_id": "traffic.dynamic_layer_search", "status": "SUCCESS"})
        except Exception as exc:
            errors.append(str(exc))
            executed_tools.append({"tool_id": "traffic.dynamic_layer_search", "status": "FAILED"})
        answer = ("연결된 고시: " + ", ".join(str(doc.get("title") or doc.get("document_id")) for doc in docs) + ". 고시의 존재만으로 실제 위험도가 높다고 판정할 수 없습니다.") if docs else "해당 항만에 연결된 통항 고시 근거를 확보하지 못했습니다."
        if traffic:
            summary = traffic.get("structured_result") or {}
            window = summary.get("effective_temporal_window") or {}
            answer += (f" 분석 범위의 적재 통항자료 합계는 {int(summary.get('total_traffic_count') or 0):,}건입니다."
                       " 이는 격자·월별 AIS/V-Pass 집계의 합계이며 고유 선박 수나 실시간 위험도가 아닙니다.")
            if window:
                answer += f" 자료 기간: {window.get('min_available_month')} ~ {window.get('max_available_month')}."
        else:
            answer += " 통항자료 실행 결과를 확보하지 못했으며 통항량을 0으로 간주하지 않습니다."
        answer += " 사고·수심/UKC·기상 근거를 같은 시공간으로 결합하지 못했으므로 종합 위험도는 확정하지 않았습니다."

    quality = unmeasured_quality(method="navigation_evidence_availability",
                                regulatory_documents=len(docs), traffic_available=bool(traffic),
                                missing_evidence=["accident_history", "depth_ukc", "weather"])
    route = {"intent": "ANALYSIS", "analysis_type": "navigation_risk_explanation",
             "context": "navigation_risk", "primary_agent": "Navigation Risk Analysis Agent",
             "secondary_agents": [], "status": status, "route_plan_status": status,
             "execution_ready": False, "clarification_required": status == "NEEDS_CLARIFICATION",
             "slots": {"resolved_location": location["port"] if location else None},
             "tools": [item["tool_id"] for item in executed_tools],
             "data": (["projection.s101_feature_valid"] if location else [])
                     + (["legal_notice_registry"] if docs else [])
                     + (["serving.dynamic_traffic_layer"] if traffic else []),
             "outputs": ["EvidenceBundle", "Summary"]}
    qec = {"readiness": status, "blockers": [code] if code else [], "warnings": errors,
           "data_bindings": [{"dataset_id": name, "relation": name} for name in route["data"]],
           "tool_bindings": executed_tools}
    citations = [{**doc, "similarity": None, "relevance_score": None,
                  "match_method": "legal_notice_registry_lookup"} for doc in docs]
    final = {"task_id": task_id, "request_id": task_id, "trace_id": f"tr-{task_id}",
             "agent_name": "Navigation Risk Analysis Agent", "status": status, "error_code": code,
             "summary": answer, "answer_text": answer,
             "clarification_questions": [answer] if status == "NEEDS_CLARIFICATION" else [],
             "structured_result": {"analysis_type": "navigation_risk_explanation",
                                   "documents": citations, "citations": citations,
                                   "nearest_port_resolution": location,
                                   "traffic_analysis": (traffic or {}).get("structured_result"),
                                   "traffic_error": errors[0] if errors else None,
                                   "quality_metrics": quality},
             "quality_metrics": quality,
             "orchestrator_v2": {"route_plan": route, "query_execution_context": qec, "quality_metrics": quality},
             "evidence_bundle": {**((traffic or {}).get("evidence_bundle") or {}),
                                 "regulatory_evidence": citations, "rag_evidence": citations,
                                 "accident_relation_evidence": []},
             "map_layers": (traffic or {}).get("map_layers") or [],
             "features": (traffic or {}).get("features"),
             "contract_version": "geollm.execution.v1"}
    return {"final_dict": final, "status": status, "task_plan": route, "query_execution_context": qec}
