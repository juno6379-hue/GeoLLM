from __future__ import annotations

from typing import Any

from services.orchestrator.definition_router import resolve_definition
from services.orchestrator.execution_validator import validate_lookup_request, is_execution_authorized, project_execution_decision


def build_definition_response(state: dict[str, Any]) -> dict[str, Any] | None:
    entry = resolve_definition(str(state.get("query") or ""))
    if not entry:
        return None
    canonical = str(entry["canonical_term"])
    definition = str(entry["definition_ko"])
    lexical = entry['source_kind'] == 'mof_terminology_relation'
    analysis_type = 'terminology_relation_lookup' if lexical else 'definition_lookup'
    validated = validate_lookup_request(state, analysis_type)
    if not is_execution_authorized(validated):
        return None
    source_title = str(entry["source_title"])
    source_ref = str(entry["source_ref"])
    task_id = str(state["task_id"])
    evidence_id = f"definition:{entry['term_id']}:v1"
    feature_code = entry["term_id"] if entry["source_kind"] == "s101_feature_catalogue" else None
    answer = f"{canonical}" + (f" ({feature_code})" if feature_code else "") + f"란 {definition} 근거: {source_title}."
    comparison = entry.get("comparison_entries") or []
    if comparison:
        answer = "등록된 원문의 정의를 나란히 비교하면 다음과 같습니다.\n\n" + "\n\n".join(
            f"**{item['canonical_term']} ({item['term_id']})**: {item['definition_ko']}\n근거: {item['source_title']} ({item['source_ref']})"
            for item in comparison
        ) + "\n\n이는 용어 정의 비교이며 특정 위치의 객체 존재 여부를 조회한 결과는 아닙니다."
    if lexical:
        answer = (f"해양수산부 순화 자료에서 ‘{canonical}’의 바꿔 쓰는 용어는 ‘{entry['recommended_label']}’입니다. "
                  f"근거: {source_title}. 이 자료의 용어 관계이며, 현재 법적 의무나 S-101 객체 매핑을 확정한 것은 아닙니다.")
    route_plan = {
        "task_id": f"TASK-DEFINITION-{task_id[:3].upper()}",
        "status": "COMPLETED", "intent": "DEFINITION",
        "context": entry.get("context") or "marine_standard",
        "analysis_type": analysis_type, "derived_concept": None,
        "primary_agent": "Standard RAG Agent", "secondary_agents": [],
        "slots": {"target_term": canonical, "analysis_type": analysis_type},
        "tools": ["definition.registry_lookup"], "data": list(dict.fromkeys(item["source_kind"] for item in (comparison or [entry]))),
        "outputs": ["StandardDocumentOutput", "EvidenceBundle", "Summary"],
        "clarification_required": False, "confidence": None if lexical else 1.0,
        "execution_ready": False, "route_plan_status": "PLAN_READY",
    }
    evidence = {
        "evidence_id": evidence_id, "evidence_type": "verified_definition" if entry.get("verification_status") == "VERIFIED" else "source_definition",
        "source_ref": source_ref, "summary": f"{source_title}: {canonical}",
        "data": {"term_id": entry["term_id"], "canonical_term": canonical,
                 "definition": definition, "verification_status": entry["verification_status"]},
    }
    if lexical:
        evidence['evidence_type'] = 'source_lexical_relation'
        evidence['data'] = entry['source_relation']
    bundle = {"rag_evidence": [evidence], "kg_provenance": [],
              "regulatory_evidence": [], "spatial_feature_evidence": [],
              "spatial_layer_evidence": [], "accident_relation_evidence": []}
    if comparison:
        bundle["rag_evidence"] = [{
            "evidence_id": f"definition:{item['term_id']}:v1", "evidence_type": "source_definition",
            "source_ref": item["source_ref"], "summary": item["source_title"],
            "data": {"term_id": item["term_id"], "definition": item["definition_ko"],
                     "verification_status": item["verification_status"]},
        } for item in comparison]
    qec = {
        "readiness": validated.readiness.value, "blockers": validated.blockers, "warnings": [],
        "semantic_resolution": {"intent": "DEFINITION", "canonical_term": canonical,
                                "source": entry["source_kind"]},
        "data_bindings": [{"dataset_id": entry["source_kind"], "source_ref": source_ref}],
        "tool_bindings": [{"tool_id": "definition.registry_lookup", "status": "EXECUTED", "term_id": entry["term_id"]}],
    }
    project_execution_decision(validated, route_plan)
    qec.update(validated.model_dump(mode="json"))
    qec["route_plan"] = route_plan
    final = {
        "task_id": task_id, "trace_id": f"tr-{task_id}",
        "agent_name": "Standard RAG Agent",
        "agent_version": "2.3.0-definition-fast-path", "status": "COMPLETED",
        "summary": answer, "answer_text": answer,
        "structured_result": {
            "status": "COMPLETED", "analysis_type": analysis_type,
            "canonical_term": canonical, "definition": None if lexical else definition,
            "feature_code": feature_code,
            "source_ref": source_ref,
            "web_rag_usage": {"web_used": False, "rag_used": False,
                              "llm_used": False,
                              "execution_path": entry["source_kind"],
                              "embedding_independent": True,
                              "evidence_used": True},
        },
        "orchestrator_v2": {"route_plan": route_plan,
                            "query_execution_context": qec,
                            "embedding_independent": True,
                            "fast_path": "verified_definition_registry"},
        "evidence_bundle": bundle, "rag_evidence": bundle["rag_evidence"],
        "kg_provenance": [], "contract_version": "geollm.execution.v1",
        "request_id": task_id,
    }
    if lexical:
        final['structured_result']['terminology_relation'] = entry['source_relation']
        final['orchestrator_v2']['fast_path'] = 'source_terminology_relation'
    if entry['source_kind'] == 's100_product_registry':
        final['orchestrator_v2']['fast_path'] = 'source_product_registry'
        final['structured_result']['verification_status'] = entry['verification_status']
    if comparison:
        final['structured_result']['definitions'] = comparison
        final['structured_result']['definition'] = None
        final['structured_result']['analysis_type'] = 'definition_comparison'
        final['orchestrator_v2']['fast_path'] = 'source_definition_comparison'
    return {"final_dict": final, "task_plan": route_plan,
            "query_execution_context": qec}
