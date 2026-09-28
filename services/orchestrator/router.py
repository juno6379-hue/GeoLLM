from services.orchestrator.quality import unmeasured_quality
import asyncio
import json
import os
import argparse
import re
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
import uuid
import yaml

from shared.schemas.agent import AgentStatus
from services.orchestrator.fast_path_policy import instant_place_navigation_decision, is_instant_place_navigation_allowed
from services.orchestrator.graph import orchestrator_graph
from services.orchestrator.place_router import place_navigation_target, resolve_payload, allow_display_navigation
from services.orchestrator.live_intent_comparison import store as comparison_store, observe as observe_comparison
from services.orchestrator.execution_validator import validate_place_resolution, project_execution_decision, is_execution_authorized
from services.orchestrator.state import OrchestratorState
from services.orchestrator.task_store import PersistentTaskStore

router = APIRouter()
ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_REVIEW_DECISIONS = ROOT / "outputs" / "review" / "evidence_candidate_review_decisions.yaml"
EVIDENCE_REGISTRY = ROOT / "data" / "evidence_registry.yaml"
EVIDENCE_CANDIDATE_FILES = [
    ROOT / "outputs" / "evidence" / "kg_provenance_candidates.jsonl",
    ROOT / "outputs" / "evidence" / "rag_evidence_candidates.jsonl",
    ROOT / "outputs" / "evidence" / "regulatory_evidence_candidates.jsonl",
]


def _valid_debug_derived_concept(value):
    text = str(value or "").strip()
    if not text:
        return None
    for name in ("derived_concept_registry_v2.yaml", "derived_concept_registry.yaml"):
        path = ROOT / "data" / name
        if not path.exists():
            continue
        try:
            concepts = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("derived_concepts") or {}
        except Exception:
            concepts = {}
        for key, payload in concepts.items():
            concept_id = payload.get("concept_id") if isinstance(payload, dict) else None
            if text in {str(key), str(concept_id or "")}:
                return concept_id or key
    return None


def _is_instant_place_navigation(query: str) -> bool:
    return is_instant_place_navigation_allowed(query)


def _point_coordinates(wkt: str | None) -> list[float] | None:
    match = re.match(r"\s*POINT\s*\(\s*([0-9.+-]+)\s+([0-9.+-]+)\s*\)\s*$", str(wkt or ""), re.I)
    if not match:
        return None
    return [float(match.group(1)), float(match.group(2))]


def _place_candidate_features(candidates: list[dict]) -> dict:
    features = []
    for candidate in candidates or []:
        coords = _point_coordinates(candidate.get("geometry"))
        geojson = candidate.get("geometry_geojson")
        geometry = geojson if isinstance(geojson, dict) else ({"type": "Point", "coordinates": coords} if coords else None)
        if not geometry:
            continue
        features.append({
            "type": "Feature",
            "id": candidate.get("place_id"),
            "geometry": geometry,
            "properties": {
                "name": candidate.get("label") or candidate.get("base_location"),
                "place_id": candidate.get("place_id"),
                "place_version": candidate.get("place_version"),
                "authority_level": candidate.get("authority_level"),
                "promotion_status": candidate.get("promotion_status"),
                "review_required": candidate.get("review_required", True),
                "source_ref": candidate.get("source_ref"),
                "source_url": candidate.get("source_url"),
                "category": candidate.get("category"),
                "evidence_summary": candidate.get("evidence_summary"),
                "longitude": coords[0] if coords else candidate.get("longitude"),
                "latitude": coords[1] if coords else candidate.get("latitude"),
                "coordinate_text": f"경도 {coords[0]:.6f}, 위도 {coords[1]:.6f} · EPSG:4326" if coords else None,
            },
        })
    return {"type": "FeatureCollection", "features": features}


def _instant_place_final(task_id: str, query: str, payload: dict) -> dict:
    validated = validate_place_resolution(query, payload, task_id=task_id)
    resolved = is_execution_authorized(validated)
    if payload.get("status") == "RESOLVED" and not resolved:
        payload = {**payload, "status": "BLOCKED", "error_code": "EXECUTION_GATE",
                   "summary": "위치 실행 검증을 통과하지 못했습니다.", "geometry": None}
    target = place_navigation_target(query)
    coords = _point_coordinates(payload.get("geometry"))
    candidates = payload.get("location_candidates") or []
    features = (
        {"type": "FeatureCollection", "features": [{
            "type": "Feature",
            "id": payload.get("place_id") or f"place:{task_id}",
            "geometry": {"type": "Point", "coordinates": coords},
            "properties": {
                "name": payload.get("location_text"),
                "place_id": payload.get("place_id"),
                "place_version": payload.get("place_version"),
                "source_ref": (payload.get("location_resolution") or {}).get("source_ref"),
                "source_url": (payload.get("location_resolution") or {}).get("source_url"),
                "operation": "map_navigation",
                "authority_level": (payload.get("location_resolution") or {}).get("authority_level"),
                "execution_permission": payload.get("execution_permission"),
            },
        }]} if resolved and coords else _place_candidate_features(candidates)
    )
    status = "COMPLETED" if resolved else payload.get("status", "BLOCKED")
    summary = payload.get("summary") or ""
    if not resolved and features.get("features"):
        summary = summary or "외부 보조 지명 후보를 찾았습니다. 후보를 확인해 주세요."
    slots = {
        "location_text": target,
        "target_term": "place",
        "derived_concept": "place_lookup",
        "analysis_type": "place_lookup",
        "operation": "map_navigation",
        "reference_geometry": payload.get("geometry"),
        "crs": payload.get("crs"),
        "resolution_status": payload.get("status"),
        "unresolved_slots": [] if resolved else ["location_confirmation"],
    }
    route_plan = {
        "intent": "PLACE_LOOKUP",
        "context": "map_navigation",
        "analysis_type": "place_lookup",
        "derived_concept": "place_lookup",
        "primary_agent": "Spatial Analysis Agent",
        "required_tools": ["place.resolve"],
        "required_data": ["local_place_registry", "external_evidence_registry"],
        "execution_ready": False,
        "status": "DRAFT",
        "route_plan_status": "DRAFT",
        "slots": slots,
    }
    qec = {
        "request_id": task_id,
        "task_id": task_id,
        "original_query": query,
        "normalized_query": target,
        "slots": slots,
        "readiness": validated.readiness.value,
        "blockers": validated.blockers,
        "warnings": (["supplemental location permitted for map display only"] if payload.get("execution_permission", {}).get("allowed") else ([] if resolved else ["location confirmation is required"])),
        "execution_permission": payload.get("execution_permission"),
        "data_bindings": [{"dataset_id": "place_registry", "status": "available"}],
        "tool_bindings": [{"tool_id": "place.resolve", "status": "available"}],
        "route_plan": route_plan,
        "provenance": {
            "fast_path": "instant_place_navigation",
            "normalizer": "services.orchestrator.place_router.place_navigation_target",
            "resolver": "services.orchestrator.place_router.resolve_payload",
        },
    }
    project_execution_decision(validated, route_plan)
    qec.update(validated.model_dump(mode="json"))
    qec["normalized_query"] = target
    qec["route_plan"] = route_plan
    qec["execution_permission"] = payload.get("execution_permission")
    norm_result = {
        "normalized_query": target,
        "canonical_terms": [target],
        "candidate_contexts": ["place_lookup", "map_navigation"],
        "matched_rules": [f"지도 이동 명령 정규화: '{query}' -> '{target}'"],
    }
    fast_path_decision = instant_place_navigation_decision(query)
    debug_state = {
        "task_id": task_id,
        "query": query,
        "normalized_query": target,
        "normalization_debug": norm_result["matched_rules"],
        "norm_result": norm_result,
        "task_plan": route_plan,
        "query_execution_context": qec,
        "extracted_slots": slots,
        "fast_path_policy": {"instant_place_navigation": fast_path_decision},
        "final_dict": {"structured_result": payload, "orchestrator_v2": {"route_plan": route_plan, "query_execution_context": qec}},
    }
    debug_trace = build_debug_trace(debug_state)
    return {
        "task_id": task_id,
        "request_id": task_id,
        "status": status,
        "agent_name": "Spatial Analysis Agent",
        "summary": summary,
        "answer_text": summary,
        "error_code": payload.get("error_code"),
        "structured_result": {
            **payload,
            "analysis_type": "place_lookup",
            "original_query": query,
            "normalization": norm_result,
            "extracted_slots": slots,
            "derived_concept_mapping": {
                "derived_concept": "place_lookup",
                "mapping_source": "instant_place_navigation_fast_path",
                "verified_by": ["place_router", "execution_context"],
            },
            "count": len(features.get("features", [])),
            "returned_count": len(features.get("features", [])),
            "geojson": features,
            "quality_metrics": unmeasured_quality(method="place_resolution", resolved=resolved),
        },
        "debug_trace": debug_trace,
        "clarification_questions": [summary] if status == "NEEDS_CLARIFICATION" else [],
        "clarification_options": candidates,
        "features": features,
        "map_layers": [{
            "layer_id": f"place:{task_id}",
            "title": place_navigation_target(query),
            "source_type": "geojson",
            "geometry_type": "MIXED",
            "inline_geojson": features,
            "feature_count": len(features.get("features", [])),
        }] if features.get("features") else [],
        "orchestrator_v2": {
            "route_plan": route_plan,
            "query_execution_context": qec,
            "embedding_independent": True,
            "fast_path": "instant_place_navigation",
            "fast_path_policy": {"instant_place_navigation": fast_path_decision},
        },
    }

# MVP 에서는 DB 대신 인메모리 딕셔너리로 최상위 메타 정보만 들고 있고, 
# 실제 세부 상태는 LangGraph의 Checkpointer(MemorySaver)가 Thread ID 단위로 관리합니다.
TASK_STORE = PersistentTaskStore()

class TaskCreateRequest(BaseModel):
    query: str
    organization_id: str = "default_org"
    user_id: str = "default_user"
    task_id: str = None  # 기존 세션을 이어서 실행할 때 프론트엔드가 전달
    spatial_context: dict = None  # UI에서 넘겨주는 지도 뷰포트 등 공간 정보

class TaskResponse(BaseModel):
    task_id: str
    status: str
    history: list = []


class EvidenceDecisionRequest(BaseModel):
    decision: str
    reviewer: str
    reason: str
    review_required_accepted: bool = False
    verification_status_override: str | None = None


class EvidenceApplyRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    write: bool = False
    overwrite: bool = False
    validate_decisions: bool = Field(default=True, alias="validate")


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _write_yaml(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _load_evidence_candidates() -> dict[str, dict]:
    candidates: dict[str, dict] = {}
    for path in EVIDENCE_CANDIDATE_FILES:
        for row in _load_jsonl(path):
            evidence_id = row.get("evidence_id")
            if evidence_id:
                candidates[evidence_id] = row
    return candidates


def _candidate_summary(row: dict) -> dict:
    data = row.get("data") if isinstance(row.get("data"), dict) else {}
    return {
        "evidence_id": row.get("evidence_id"),
        "partition": row.get("partition"),
        "evidence_type": row.get("evidence_type"),
        "summary": row.get("summary"),
        "source_ref": row.get("source_ref"),
        "score": row.get("score"),
        "review_required": row.get("review_required"),
        "dataset_id": data.get("dataset_id"),
        "layer_id": data.get("layer_id"),
        "document_type": data.get("document_type"),
        "title": data.get("title"),
        "source_file": data.get("source_file"),
        "source_id": data.get("source_id"),
        "feature_code": data.get("feature_code"),
        "chunk_id": data.get("chunk_id"),
        "legal_notice_id": data.get("legal_notice_id"),
        "official_dataset_id": data.get("official_dataset_id"),
        "authority_id": data.get("authority_id"),
        "edge_candidates": data.get("edge_candidates") or [],
        "verification_status": data.get("verification_status"),
    }


def _ensure_evidence_review_doc() -> dict:
    doc = _load_yaml(EVIDENCE_REVIEW_DECISIONS)
    if doc.get("decisions"):
        return doc
    candidates = _load_evidence_candidates()
    decisions = {}
    for evidence_id, row in sorted(candidates.items()):
        decisions[evidence_id] = {
            "decision": "hold",
            "reviewer": None,
            "reviewed_at": None,
            "reason": "자동 생성된 evidence 후보입니다. 검토자가 승인/반려/보류 사유를 작성합니다.",
            "review_required_accepted": False,
            "verification_status_override": None,
            "candidate": _candidate_summary(row),
        }
    doc = {
        "version": "0.1",
        "phase": "8.8",
        "status": "review_template",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "policy": {
            "default_decision": "hold",
            "allowed_decisions": ["approved", "rejected", "hold"],
            "review_required_candidates_require_acceptance": True,
            "ui_enabled": True,
        },
        "decisions": decisions,
    }
    _write_yaml(EVIDENCE_REVIEW_DECISIONS, doc)
    return doc


@router.get("/evidence-candidates")
def list_evidence_candidates(
    partition: str | None = None,
    decision: str | None = None,
    review_required: bool | None = None,
    limit: int = 100,
    offset: int = 0,
):
    candidates = _load_evidence_candidates()
    doc = _ensure_evidence_review_doc()
    decisions = doc.get("decisions") or {}
    rows = []
    for evidence_id, candidate in candidates.items():
        item = _candidate_summary(candidate)
        decision_doc = decisions.get(evidence_id, {})
        item["decision"] = decision_doc.get("decision", "hold")
        item["reviewer"] = decision_doc.get("reviewer")
        item["reviewed_at"] = decision_doc.get("reviewed_at")
        item["reason"] = decision_doc.get("reason")
        item["review_required_accepted"] = decision_doc.get("review_required_accepted", False)
        if partition and item.get("partition") != partition:
            continue
        if decision and item.get("decision") != decision:
            continue
        if review_required is not None and bool(item.get("review_required")) != review_required:
            continue
        rows.append(item)
    rows.sort(key=lambda row: (row.get("decision") != "hold", row.get("partition") or "", -(float(row.get("score") or 0))))
    safe_limit = max(1, min(limit, 500))
    safe_offset = max(0, offset)
    selected = rows[safe_offset:safe_offset + safe_limit]
    counts = {
        "total": len(rows),
        "approved": sum(1 for row in rows if row.get("decision") == "approved"),
        "rejected": sum(1 for row in rows if row.get("decision") == "rejected"),
        "hold": sum(1 for row in rows if row.get("decision") == "hold"),
    }
    registry = _load_yaml(EVIDENCE_REGISTRY)
    return {
        "items": selected,
        "counts": counts,
        "limit": safe_limit,
        "offset": safe_offset,
        "registry_items": len(registry.get("evidence_items") or {}),
        "decision_source": str(EVIDENCE_REVIEW_DECISIONS.relative_to(ROOT)).replace("\\", "/"),
        "registry_source": str(EVIDENCE_REGISTRY.relative_to(ROOT)).replace("\\", "/"),
    }


@router.get("/evidence-candidates/{evidence_id}")
def get_evidence_candidate(evidence_id: str):
    candidates = _load_evidence_candidates()
    candidate = candidates.get(evidence_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Evidence candidate not found")
    doc = _ensure_evidence_review_doc()
    decision = (doc.get("decisions") or {}).get(evidence_id, {})
    return {
        "candidate": candidate,
        "decision": decision,
    }


@router.post("/evidence-candidates/{evidence_id}/decision")
def set_evidence_candidate_decision(evidence_id: str, req: EvidenceDecisionRequest):
    if req.decision not in {"approved", "rejected", "hold"}:
        raise HTTPException(status_code=400, detail="decision must be approved, rejected, or hold")
    if req.decision == "approved":
        if not req.reviewer.strip() or not req.reason.strip():
            raise HTTPException(status_code=400, detail="approved decision requires reviewer and reason")
    candidates = _load_evidence_candidates()
    candidate = candidates.get(evidence_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Evidence candidate not found")
    if req.decision == "approved" and candidate.get("review_required") and not req.review_required_accepted:
        raise HTTPException(status_code=400, detail="review_required candidate requires review_required_accepted=true")
    doc = _ensure_evidence_review_doc()
    decisions = doc.setdefault("decisions", {})
    previous = decisions.get(evidence_id, {})
    decisions[evidence_id] = {
        **previous,
        "decision": req.decision,
        "reviewer": req.reviewer.strip() or None,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "reason": req.reason.strip() or "검토 사유 미입력",
        "review_required_accepted": req.review_required_accepted,
        "verification_status_override": req.verification_status_override,
        "candidate": previous.get("candidate") or _candidate_summary(candidate),
    }
    doc["status"] = "review_in_progress"
    doc["updated_at"] = datetime.now(timezone.utc).isoformat()
    _write_yaml(EVIDENCE_REVIEW_DECISIONS, doc)
    return {"status": "PASS", "evidence_id": evidence_id, "decision": decisions[evidence_id]}


@router.post("/evidence-candidates/apply")
def apply_evidence_candidate_decisions(req: EvidenceApplyRequest):
    from scripts.apply_approved_evidence_candidates import apply_approved
    from scripts.validate_approved_evidence_candidates import validate_approved

    args = argparse.Namespace(
        inputs=EVIDENCE_CANDIDATE_FILES,
        decisions=EVIDENCE_REVIEW_DECISIONS,
        registry=EVIDENCE_REGISTRY,
        write=req.write,
        overwrite=req.overwrite,
        nodes=ROOT / "outputs" / "graph" / "kg_nodes_v2.jsonl",
        edges=ROOT / "outputs" / "graph" / "kg_edges_v2.jsonl",
        report=ROOT / "outputs" / "review" / "approved_evidence_validation_report.json",
        write_report=req.write,
    )
    validation = validate_approved(args)
    if req.validate_decisions and validation.get("status") != "PASS":
        raise HTTPException(status_code=400, detail=validation)
    result = apply_approved(args)
    if result.get("status") != "PASS":
        raise HTTPException(status_code=400, detail=result)
    result["validation"] = {
        "status": validation.get("status"),
        "counts": validation.get("counts"),
        "report": validation.get("report"),
    }
    return result


@router.post("/evidence-candidates/validate")
def validate_evidence_candidate_decisions():
    from scripts.validate_approved_evidence_candidates import validate_approved

    args = argparse.Namespace(
        inputs=EVIDENCE_CANDIDATE_FILES,
        decisions=EVIDENCE_REVIEW_DECISIONS,
        registry=EVIDENCE_REGISTRY,
        nodes=ROOT / "outputs" / "graph" / "kg_nodes_v2.jsonl",
        edges=ROOT / "outputs" / "graph" / "kg_edges_v2.jsonl",
        report=ROOT / "outputs" / "review" / "approved_evidence_validation_report.json",
        write_report=True,
    )
    return validate_approved(args)


def _to_jsonable(value):
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {k: _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_jsonable(v) for v in value]
    return value


def _compact_agent_result_for_stream(agent_result):
    result = _to_jsonable(agent_result) or {}
    structured = result.get("structured_result") if isinstance(result.get("structured_result"), dict) else {}
    orch = result.get("orchestrator_v2") if isinstance(result.get("orchestrator_v2"), dict) else {}
    quality_metrics = structured.get("quality_metrics") or orch.get("quality_metrics")
    evidence_bundle = result.get("evidence_bundle") if isinstance(result.get("evidence_bundle"), dict) else {}
    evidence_counts = {
        key: len(value)
        for key, value in evidence_bundle.items()
        if isinstance(value, list)
    }
    compact = {
        "task_id": result.get("task_id"),
        "agent_name": result.get("agent_name"),
        "agent_version": result.get("agent_version"),
        "status": result.get("status"),
        "error_code": result.get("error_code"),
        "summary": result.get("summary"),
        "answer_text": result.get("answer_text"),
        "structured_result": {
            "retrieved_count": structured.get("retrieved_count"),
            "documents": structured.get("documents", [])[:3] if isinstance(structured.get("documents"), list) else [],
            "citations": structured.get("citations", [])[:3] if isinstance(structured.get("citations"), list) else [],
            "external_data_requirement": structured.get("external_data_requirement"),
            "requires_external_api": structured.get("requires_external_api"),
            "api_params": structured.get("api_params"),
            "count": structured.get("count"),
            "status": structured.get("status"),
            "evidence_candidate_summary": structured.get("evidence_candidate_summary"),
            "quality_metrics": quality_metrics,
        },
        "quality_metrics": quality_metrics,
        "evidence_counts": evidence_counts,
        "provenance": result.get("provenance", {}),
    }
    _preserve_spatial_stream_payload(result, compact)
    return compact


def _preserve_spatial_stream_payload(result: dict, compact: dict) -> None:
    structured = result.get("structured_result") if isinstance(result.get("structured_result"), dict) else {}
    orch = result.get("orchestrator_v2") if isinstance(result.get("orchestrator_v2"), dict) else {}
    # Preserve typed domain outputs for every analysis, not just a hardcoded
    # spatial allowlist. Document previews remain bounded by the caller.
    for key, value in structured.items():
        compact.setdefault("structured_result", {}).setdefault(key, value)
    if "evidence_bundle" in result:
        compact["evidence_bundle"] = result["evidence_bundle"]
    if "orchestrator_v2" in compact:
        for key, value in orch.items():
            compact["orchestrator_v2"].setdefault(key, value)
        for key, value in (orch.get("query_execution_context") or {}).items():
            compact["orchestrator_v2"].setdefault("query_execution_context", {}).setdefault(key, value)
    route = orch.get("route_plan") if isinstance(orch.get("route_plan"), dict) else {}
    spatial_stream_analysis_types = {
        "feature_search_by_radius",
        "place_lookup",
        "nearest_feature",
        "traffic_search_by_time_space",
        "accident_spatial_history_lookup",
        "accident_event_lookup",
    }
    is_radius = (
        structured.get("analysis_type") in spatial_stream_analysis_types
        or route.get("analysis_type") in spatial_stream_analysis_types
        or "location_candidates" in structured
    )
    for key in ("task_id", "intent_comparison_id", "clarification_questions", "clarification_options", "warnings"):
        if key in result:
            compact[key] = result[key]
    if not is_radius:
        return
    qec = orch.get("query_execution_context")
    if isinstance(qec, dict) and "orchestrator_v2" in compact:
        compact_qec = compact["orchestrator_v2"]["query_execution_context"]
        for key in ("request_id", "task_id", "revision", "plan_hash", "slots", "semantic_resolution", "snapshot_versions", "route_plan", "provenance"):
            if key in qec:
                compact_qec[key] = qec[key]
    # The executor bounds this result. Keep every returned surface together.
    for key in (
        "analysis_type", "count", "total_count", "returned_count", "result_limit", "truncated",
        "nearest_returned_count", "feature_ids", "features", "geojson", "result_id", "query_execution_id",
        "returned_counts_by_type", "total_counts_by_type", "location_candidates",
        "feature_type_breakdown", "location_text", "distance_m", "original_query",
        "buffer_distance", "target_layers",
        "reference_geometry", "reference_crs", "geometry", "crs", "source_layer", "blockers",
        "offset", "target_features", "exclusions", "spatial_context",
        "place_id", "place_version", "location_resolution", "execution_permission",
        "geojson_feature_count", "map_layer_count", "evidence_bundle_counts",
        "web_rag_usage", "result_surface", "distance_policy", "user_evidence_summary",
        "result_surface_contract",
        "execution_contract",
        "events", "radius_m",
        "total_traffic_count", "grid_count", "source_breakdown", "monthly_breakdown",
        "tile_layer_summary", "temporal_window", "effective_temporal_window",
    ):
        if key in structured:
            compact["structured_result"][key] = structured[key]
    for key in ("map_layers", "features", "evidence_bundle", "spatial_result_summary", "claims", "task_results"):
        if key in result:
            compact[key] = result[key]


def _compact_final_result_for_stream(final_result):
    result = _to_jsonable(final_result) or {}
    structured = result.get("structured_result") if isinstance(result.get("structured_result"), dict) else {}
    orch = result.get("orchestrator_v2") if isinstance(result.get("orchestrator_v2"), dict) else {}
    quality_metrics = structured.get("quality_metrics") or orch.get("quality_metrics")
    candidate_trace = orch.get("candidate_trace") if isinstance(orch.get("candidate_trace"), dict) else result.get("candidate_trace")
    qec = orch.get("query_execution_context") if isinstance(orch.get("query_execution_context"), dict) else {}
    evidence_bundle = result.get("evidence_bundle") if isinstance(result.get("evidence_bundle"), dict) else {}
    evidence_counts = {
        key: len(value)
        for key, value in evidence_bundle.items()
        if isinstance(value, list)
    }
    compact = {
        "status": result.get("status"),
        "error_code": result.get("error_code"),
        "agent_name": result.get("agent_name"),
        "summary": result.get("summary"),
        "answer_text": result.get("answer_text"),
        "external_data_requirement": result.get("external_data_requirement"),
        "structured_result": {
            "retrieved_count": structured.get("retrieved_count"),
            "documents": structured.get("documents", [])[:3] if isinstance(structured.get("documents"), list) else [],
            "citations": structured.get("citations", [])[:3] if isinstance(structured.get("citations"), list) else [],
            "requires_external_api": structured.get("requires_external_api"),
            "api_params": structured.get("api_params"),
            "external_data_requirement": structured.get("external_data_requirement"),
            "count": structured.get("count"),
            "status": structured.get("status"),
            "evidence_candidate_summary": structured.get("evidence_candidate_summary"),
            "quality_metrics": quality_metrics,
        },
        "quality_metrics": quality_metrics,
        "orchestrator_v2": {
            "route_plan": orch.get("route_plan") or {},
            "quality_metrics": quality_metrics,
            "candidate_trace": candidate_trace or {},
            "execution_contract": orch.get("execution_contract") or (candidate_trace or {}).get("execution_contract") or {},
            "query_execution_context": {
                "readiness": qec.get("readiness"),
                "blockers": qec.get("blockers"),
                "execution_permission": qec.get("execution_permission"),
                "warnings": qec.get("warnings"),
                "data_bindings": qec.get("data_bindings"),
                "tool_bindings": qec.get("tool_bindings"),
            },
        },
        "evidence_counts": evidence_counts,
    }
    if isinstance(result.get("debug_trace"), dict):
        compact["debug_trace"] = result["debug_trace"]
    for key in ("normalization", "extracted_slots", "derived_concept_mapping", "nearest_port_resolution", "traffic_analysis", "traffic_error", "analysis_type"):
        if key in structured:
            compact["structured_result"][key] = structured[key]
    _preserve_spatial_stream_payload(result, compact)
    return compact


def _terminal_result_for_stream(state_vals: dict) -> dict:
    final_result = _to_jsonable(state_vals.get("final_dict") or state_vals.get("agent_result"))
    candidate_trace = _to_jsonable(state_vals.get("candidate_trace")) or {}
    if isinstance(final_result, dict) and candidate_trace:
        final_result.setdefault("orchestrator_v2", {})
        if isinstance(final_result["orchestrator_v2"], dict):
            final_result["orchestrator_v2"].setdefault("candidate_trace", candidate_trace)
        final_result.setdefault("structured_result", {})
        if isinstance(final_result["structured_result"], dict):
            final_result["structured_result"].setdefault("candidate_trace_summary", {
                "contract": candidate_trace.get("contract"),
                "mode": candidate_trace.get("mode"),
                "top_routes": (candidate_trace.get("route_candidates") or [])[:3],
                "top_capabilities": (candidate_trace.get("capability_candidates") or [])[:5],
                "verified_ready_count": sum(
                    1 for row in candidate_trace.get("verified_candidates") or []
                    if isinstance(row, dict) and row.get("status") == "verified_ready"
                ),
                "ollama_needed": (candidate_trace.get("ollama_policy") or {}).get("needed"),
            })
    payload = {"error_message": state_vals.get("error_message")}
    if final_result:
        if os.environ.get("GEOLLM_STREAM_FULL_RESULT", "").lower() in {"1", "true", "yes", "on"}:
            payload["final_result"] = final_result
        else:
            payload["final_result"] = _compact_final_result_for_stream(final_result)
        for key in ("clarification_questions", "clarification_options"):
            payload[key] = final_result.get(key) or []
    return payload


def _is_radius_state(state: dict) -> bool:
    final = _to_jsonable(state.get("final_dict")) or {}
    qec = _to_jsonable(state.get("query_execution_context")) or {}
    plan = _to_jsonable(state.get("task_plan")) or {}
    sources = [plan, qec.get("route_plan") or {}, final.get("structured_result") or {}]
    return any(isinstance(source, dict) and source.get("analysis_type") == "feature_search_by_radius" for source in sources)


def _is_place_clarification_state(state: dict) -> bool:
    final = _to_jsonable(state.get("final_dict")) or {}
    structured = final.get("structured_result") or {}
    status = final.get("status") or _to_jsonable(state.get("status"))
    return (
        isinstance(structured, dict)
        and structured.get("analysis_type") in {"place_lookup", "nearest_feature"}
        and status in {"NEEDS_CLARIFICATION", "NEEDS_USER_INPUT", "BLOCKED", "COMPLETED"}
    )


def _radius_restart_state(current_state: dict, req) -> dict:
    restarted = dict(current_state)
    restarted["task_id"] = restarted.get("task_id") or req.task_id or str(uuid.uuid4())
    restarted["organization_id"] = restarted.get("organization_id") or req.organization_id or "default_org"
    restarted["user_id"] = restarted.get("user_id") or req.user_id or "default_user"
    previous_query = current_state.get("query") or ""
    incoming_query = req.query.strip()
    query = incoming_query if not previous_query or previous_query in incoming_query else f"{previous_query} {incoming_query}".strip()
    spatial = dict(_to_jsonable(current_state.get("spatial_context")) or {})
    supplied = req.spatial_context or {}
    changed_generic_query = _is_place_clarification_state(current_state) and incoming_query and incoming_query != previous_query
    if changed_generic_query:
        query = incoming_query
        if "buffer_distance" not in supplied:
            spatial.pop("buffer_distance", None)
    selection_fields = ("place_id", "place_version", "location_resolution")
    selection_changed = any(key in supplied and supplied[key] != spatial.get(key) for key in ("place_id", "place_version"))
    manual_geometry = "geometry" in supplied and not supplied.get("place_id")
    location_changed = supplied.get("base_location") and supplied.get("base_location") != spatial.get("base_location") and "geometry" not in supplied
    if selection_changed or location_changed:
        spatial.pop("geometry", None)
        spatial.pop("crs", None)
    if selection_changed or location_changed or manual_geometry:
        for key in selection_fields:
            spatial.pop(key, None)
    spatial.update(supplied)
    if manual_geometry:
        for key in selection_fields:
            spatial.pop(key, None)
    previous_qec = _to_jsonable(current_state.get("query_execution_context")) or {}
    revision = int(current_state.get("execution_revision") or previous_qec.get("revision") or 1) + 1
    restarted.update(query=query, spatial_context=spatial, execution_revision=revision, status=AgentStatus.RECEIVED)
    for field in (
        "final_dict", "agent_request", "agent_result", "task_plan", "query_execution_context",
        "context_result", "extracted_slots", "norm_result", "normalized_query", "normalization_debug",
        "graph_context", "graph_rag_context", "candidate_trace", "data_discovery_result", "clarification_questions", "error_message",
    ):
        restarted[field] = None
    restarted.update(approval_granted=None, retry_count=0)
    return restarted


def _persist_state(task_id: str, state_vals: dict) -> None:
    if not state_vals:
        return

    TASK_STORE.update(
        task_id,
        query=state_vals.get("query", ""),
        status=state_vals.get("status", "FAILED"),
        organization_id=state_vals.get("organization_id") or "default_org",
        user_id=state_vals.get("user_id") or "default_user",
        spatial_context=_to_jsonable(state_vals.get("spatial_context")),
        state_history=_to_jsonable(state_vals.get("state_history", [])),
        agent_result=_to_jsonable(state_vals.get("agent_result")),
        final_result=_to_jsonable(state_vals.get("final_dict")),
        snapshot=_to_jsonable(state_vals),
        error_message=state_vals.get("error_message"),
    )

async def run_langgraph_workflow(task_id: str, req: TaskCreateRequest):
    """LangGraph를 Thread ID 기반으로 실행하는 비동기 래퍼"""
    config = {"configurable": {"thread_id": task_id}}
    
    initial_state = {
        "task_id": task_id,
        "query": req.query,
        "organization_id": req.organization_id or "default_org",
        "user_id": req.user_id or "default_user",
        "status": AgentStatus.RECEIVED,
        "spatial_context": req.spatial_context,
        "state_history": []
    }
    
    # LangGraph 백그라운드 실행
    try:
        final_state = await orchestrator_graph.ainvoke(initial_state, config=config)
        _persist_state(task_id, final_state)
    except Exception as e:
        TASK_STORE.update(task_id, status=AgentStatus.FAILED, error_message=str(e))
        print(f"Graph execution failed: {e}")

@router.post("/tasks", response_model=TaskResponse, status_code=202)
def create_task(req: TaskCreateRequest, background_tasks: BackgroundTasks):
    task_id = req.task_id if req.task_id else str(uuid.uuid4())
    
    # 이전 세션 이어서 진행 (기존 쿼리와 병합 로직은 graph 내부나 앞단에서 처리)
    if task_id in TASK_STORE:
        TASK_STORE.append_query(task_id, req.query)
        TASK_STORE.update(task_id, status=AgentStatus.RECEIVED, error_message=None)
    else:
        TASK_STORE[task_id] = {
            "query": req.query,
            "status": AgentStatus.RECEIVED,
            "organization_id": req.organization_id or "default_org",
            "user_id": req.user_id or "default_user",
            "spatial_context": req.spatial_context,
            "state_history": []
        }
    
    # 비동기 백그라운드로 LangGraph State Machine 실행
    # Starlette TestClient drains BackgroundTasks before returning the response.
    # Preserve the accepted state for tests; production remains asynchronous.
    if not os.environ.get("PYTEST_CURRENT_TEST"):
        background_tasks.add_task(run_langgraph_workflow, task_id, req)
    
    return TaskResponse(task_id=task_id, status=AgentStatus.RECEIVED)

@router.post("/tasks/stream")
async def stream_task(req: TaskCreateRequest):
    """실시간 SSE 스트리밍 엔드포인트"""
    task_id = req.task_id if req.task_id else str(uuid.uuid4())
    if req.task_id and req.task_id in TASK_STORE:
        previous = TASK_STORE.get(req.task_id, {})
        previous_status = str(previous.get("status") or "")
        resumable_statuses = {
            AgentStatus.NEEDS_CLARIFICATION.value,
            AgentStatus.WAITING_FOR_REVIEW.value,
        }
        if previous_status not in resumable_statuses:
            # Completed/blocked/failed tasks are immutable executions. Even an
            # older UI must not attach a new query to their checkpoints.
            task_id = str(uuid.uuid4())
    req.task_id = task_id
    req.organization_id = req.organization_id or "default_org"
    req.user_id = req.user_id or "default_user"
    
    # 세션 재진입 여부 파악
    is_resume = task_id in TASK_STORE
    
    if is_resume:
        TASK_STORE.append_query(task_id, req.query)
        TASK_STORE.update(task_id, status=AgentStatus.RECEIVED, error_message=None)
    else:
        TASK_STORE[task_id] = {
            "query": req.query,
            "status": AgentStatus.RECEIVED,
            "organization_id": req.organization_id,
            "user_id": req.user_id,
            "spatial_context": req.spatial_context,
            "state_history": []
        }

    instant_place_navigation = (not is_resume) and _is_instant_place_navigation(req.query)
    comparison_id = comparison_store().submit(task_id, req.query, req.spatial_context)
    
    config = {"configurable": {"thread_id": task_id}}
    
    # 새 세션일 때만 초기화
    if not is_resume:
        initial_state = {
            "task_id": task_id,
            "query": req.query,
            "organization_id": req.organization_id,
            "user_id": req.user_id,
            "status": AgentStatus.RECEIVED,
            "spatial_context": req.spatial_context,
            "state_history": []
        }
    else:
        # 이어서 시작하는 경우에는 Graph의 get_state를 통해 기존 상태를 읽어와 업데이트
        # 스트림 내부에서 orchestrator_graph.update_state를 통해 쿼리 업데이트
        pass
    
    async def event_generator():
        # 시작 이벤트
        yield f"data: {json.dumps({'event': 'started', 'task_id': task_id, 'comparison_id': comparison_id})}\n\n"
        if instant_place_navigation:
            yield f"data: {json.dumps({'event': 'progress', 'status': 'FAST_PLACE_LOOKUP', 'message': '지명 후보를 바로 확인하는 중...'})}\n\n"
            try:
                payload = await asyncio.to_thread(resolve_payload, req.query, req.spatial_context or {})
                payload = allow_display_navigation(req.query, payload, req.spatial_context)
                final_result = _instant_place_final(task_id, req.query, payload)
                final_result["intent_comparison_id"] = comparison_id
                observe_comparison(comparison_id, final_result)
                from services.orchestrator.korean_query_analysis import analyze_query
                analysis = await asyncio.to_thread(analyze_query, req.query)
                final_result["structured_result"]["korean_query_analysis"] = analysis
                final_result["orchestrator_v2"]["korean_query_analysis"] = analysis
                status = final_result["status"]
                snapshot = {
                    "task_id": task_id,
                    "query": req.query,
                    "status": status,
                    "final_dict": final_result,
                    "task_plan": final_result["orchestrator_v2"]["route_plan"],
                    "instant_fast_path": True,
                }
                TASK_STORE.update(
                    task_id,
                    status=status,
                    final_result=final_result,
                    result=final_result,
                    snapshot=snapshot,
                    agent_result=None,
                    error_message=None,
                )
                yield f"data: {json.dumps({'event': 'node_finished', 'node': 'instant_place_lookup', 'status': status}, default=str)}\n\n"
                yield f"data: {json.dumps({'event': 'completed', 'status': status, 'final_result': _compact_final_result_for_stream(final_result)}, default=str)}\n\n"
                return
            except Exception as e:
                TASK_STORE.update(task_id, status=AgentStatus.FAILED, error_message=str(e))
                observe_comparison(comparison_id, {"status": "FAILED", "summary": str(e)})
                yield f"data: {json.dumps({'event': 'error', 'message': str(e)}, default=str)}\n\n"
                return
        
        # 콜드 스타트 시 UI가 멈추지 않도록 진행 상황 사전 알림
        yield f"data: {json.dumps({'event': 'progress', 'status': 'INTENT_PARSING', 'message': '지능형 라우팅 및 시맨틱 캐시 확인 중...'})}\n\n"
        
        try:
            if is_resume:
                # 상태 머신의 현재 상태(NEEDS_CLARIFICATION 등)를 가져와서 최신 쿼리를 반영합니다.
                state_snapshot = orchestrator_graph.get_state(config)
                restart_state = None
                if state_snapshot and state_snapshot.values:
                    current_state = state_snapshot.values
                    if (_is_radius_state(current_state) or _is_place_clarification_state(current_state)) and (req.spatial_context is not None or not state_snapshot.next):
                        restart_state = _radius_restart_state(current_state, req)
                        TASK_STORE.update(
                            task_id, query=restart_state["query"], spatial_context=restart_state["spatial_context"],
                            final_result=None, agent_result=None, snapshot=_to_jsonable(restart_state),
                        )
                    else:
                        current_state = dict(current_state)
                        current_state["task_id"] = current_state.get("task_id") or task_id
                        current_state["organization_id"] = current_state.get("organization_id") or req.organization_id or "default_org"
                        current_state["user_id"] = current_state.get("user_id") or req.user_id or "default_user"
                        current_state["query"] = f"{current_state.get('query', '')} {req.query}"
                        current_state["status"] = AgentStatus.RECEIVED
                        orchestrator_graph.update_state(config, current_state)
                    
                stream_iter = orchestrator_graph.astream(restart_state, config=config, stream_mode="updates")
            else:
                stream_iter = orchestrator_graph.astream(initial_state, config=config, stream_mode="updates")
                
            # LangGraph astream (노드 완료 시마다 상태 업데이트 yield)
            async for chunk in stream_iter:
                for node_name, state_update in chunk.items():
                    current_status = state_update.get("status", "PROCESSING")
                    
                    # 객체 직렬화 문제 방지를 위해 필요한 항목만 추출
                    safe_update = {
                        "event": "node_finished",
                        "node": node_name,
                        "status": current_status
                    }
                    if current_status == AgentStatus.NEEDS_CLARIFICATION:
                        agent_res = state_update.get("agent_result")
                        if agent_res:
                            safe_update["clarification_questions"] = agent_res.clarification_questions
                    
                    if "context_result" in state_update and state_update["context_result"]:
                        safe_update["context_result"] = state_update["context_result"].__dict__
                    if "task_plan" in state_update and state_update["task_plan"]:
                        safe_update["task_plan"] = state_update["task_plan"].model_dump(mode='json') if hasattr(state_update["task_plan"], "model_dump") else state_update["task_plan"]
                    if "normalization_debug" in state_update and state_update["normalization_debug"]:
                        safe_update["normalization_debug"] = state_update["normalization_debug"]
                    if "normalized_query" in state_update and state_update["normalized_query"]:
                        safe_update["normalized_query"] = state_update["normalized_query"]
                    if "agent_result" in state_update and state_update["agent_result"] and current_status == AgentStatus.RESULTS_AGGREGATED:
                        safe_update["agent_result"] = _compact_agent_result_for_stream(state_update["agent_result"])
                    
                    TASK_STORE.update(
                        task_id,
                        status=current_status,
                        snapshot=_to_jsonable(state_update),
                        agent_result=_to_jsonable(state_update.get("agent_result")),
                        error_message=state_update.get("error_message"),
                    )
                    yield f"data: {json.dumps(safe_update, default=str)}\n\n"
                    
            # 실행 종료 후 최종 상태
            state_snapshot = orchestrator_graph.get_state(config)
            final_status = state_snapshot.values.get("status", "FAILED")
            
            # --- Debug Trace 구성 ---
            state_vals = state_snapshot.values
            debug_trace = build_debug_trace(state_vals)
            _persist_state(task_id, state_vals)
            
            safe_final = {"event": "completed", "status": final_status, "debug_trace": debug_trace}
            safe_final.update(_terminal_result_for_stream(state_vals))
            safe_final["comparison_id"] = comparison_id
            observe_comparison(comparison_id, safe_final.get("final_result") or {"status": final_status})
                
            yield f"data: {json.dumps(safe_final, default=str)}\n\n"
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error in stream generator: {e}")
            TASK_STORE.update(task_id, status=AgentStatus.FAILED, error_message=str(e))
            observe_comparison(comparison_id, {"status": "FAILED", "summary": str(e)})
            yield f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

def build_debug_trace(state_vals: dict) -> dict:
    def _as_dict(value):
        return value.model_dump(mode="json") if hasattr(value, "model_dump") else (value if isinstance(value, dict) else {})

    agent_result = state_vals.get("agent_result")
    task_plan_val = state_vals.get("task_plan")
    
    # 1. LLM 추출 Slot (실패 시 빈 객체 대비)
    agent_req = state_vals.get("agent_request")
    pi = None
    if agent_req:
        if hasattr(agent_req, "parsed_intent"):
            pi = agent_req.parsed_intent
        elif isinstance(agent_req, dict):
            pi = agent_req.get("parsed_intent")
    pi_dict = pi.model_dump(mode='json') if hasattr(pi, "model_dump") else (pi if isinstance(pi, dict) else {})
    
    final_dict = _to_jsonable(state_vals.get("final_dict")) or {}
    final_orch = final_dict.get("orchestrator_v2") if isinstance(final_dict.get("orchestrator_v2"), dict) else {}
    qec_dict = _as_dict(state_vals.get("query_execution_context")) or final_orch.get("query_execution_context") or {}
    qec_slots = qec_dict.get("slots") if isinstance(qec_dict.get("slots"), dict) else {}
    state_slots = state_vals.get("extracted_slots") if isinstance(state_vals.get("extracted_slots"), dict) else {}
    candidate_trace = _to_jsonable(state_vals.get("candidate_trace")) or final_orch.get("candidate_trace") or {}
    if not isinstance(candidate_trace, dict):
        candidate_trace = {}
    fast_path_policy = _to_jsonable(state_vals.get("fast_path_policy")) or final_orch.get("fast_path_policy") or {}
    if not isinstance(fast_path_policy, dict):
        fast_path_policy = {}

    # 2. Rule-based Normalizer Result (무조건 존재함)
    norm_res = state_vals.get("norm_result", {})
    
    # 추출 Slot 병합 (LLM Slot 파싱 결과가 있으면 쓰고, 없으면 빈 배열)
    fallback_spatial = []
    slot_location = qec_slots.get("location_text") or qec_slots.get("location") or state_slots.get("location_text") or state_slots.get("location")
    slot_relation = qec_slots.get("spatial_relation") or state_slots.get("spatial_relation")
    slot_distance = qec_slots.get("distance_m") or state_slots.get("distance_m")
    if slot_location or slot_relation or slot_distance:
        parts = [str(item) for item in (slot_location, slot_relation, f"{slot_distance:g}m" if isinstance(slot_distance, (int, float)) else slot_distance) if item]
        fallback_spatial = [" ".join(parts)]
    extracted_slots = {
        "공간조건": pi_dict.get("spatial_conditions", []) or fallback_spatial,
        "시간조건": pi_dict.get("temporal_conditions", [])
    }
    
    norm_dict = {
        "정제된 질의": norm_res.get("normalized_query", state_vals.get("normalized_query", "")),
        "표준 용어": norm_res.get("canonical_terms", []),
        "추출 Slot": extracted_slots,
        "확정 Slot": qec_slots or state_slots,
        "후보 Context/Intent": norm_res.get("candidate_contexts", []),
        "상세 로그": state_vals.get("normalization_debug", [])
    }
    
    ctx_res = state_vals.get("context_result")
    if isinstance(ctx_res, dict):
        ctx_dict = ctx_res
    else:
        ctx_dict = ctx_res.__dict__ if ctx_res else {}
        
    tp = task_plan_val if isinstance(task_plan_val, dict) else (task_plan_val.__dict__ if task_plan_val else {})
    if not tp and isinstance(final_orch.get("route_plan"), dict):
        tp = final_orch["route_plan"]
    canonical_list = norm_res.get("canonical_terms", [])
    derived_from_qec = (
        qec_slots.get("derived_concept")
        or qec_slots.get("concept_id")
        or (qec_dict.get("semantic_resolution") or {}).get("derived_concept")
    )
    derived_from_norm = next(
        (valid for item in canonical_list for valid in [_valid_debug_derived_concept(item)] if valid),
        None,
    )
    derived_from_context = next(
        (valid for item in ctx_dict.get("derived_concepts", []) for valid in [_valid_debug_derived_concept(item)] if valid),
        None,
    )
    verified_derived = tp.get("derived_concept") or _valid_debug_derived_concept(derived_from_qec) or derived_from_context or derived_from_norm or "None"
    from services.orchestrator.execution_validator import is_execution_authorized
    from shared.schemas.agent import QueryExecutionContext
    try:
        authorized_execution = is_execution_authorized(QueryExecutionContext.model_validate(qec_dict))
    except (ValueError, TypeError):
        authorized_execution = False
    intent_dict = {
        "Intent": tp.get("intent", ctx_dict.get("intent", "None")),
        "Context": tp.get("context", ctx_dict.get("selected_context", "None")),
        "Analysis Type": tp.get("analysis_type", ctx_dict.get("analysis_type", "None")),
        "Derived Concept": verified_derived,
        "Slot Check": ctx_dict.get("debug_scores", {}).get("slot_check_result", {}),
        "Target Agent": tp.get("primary_agent", "None"),
        "Required Tools": tp.get("tools", tp.get("required_tools", [])),
        "Required Data": tp.get("data", tp.get("required_data", [])),
        "Execution Ready": authorized_execution,
        "Route Plan Status": tp.get("route_plan_status", "UNKNOWN")
    }

    loc = slot_location or ""
    dist_m = slot_distance or 0
    if extracted_slots["공간조건"]:
        sp = extracted_slots["공간조건"][0]
        if isinstance(sp, dict) and not loc:
            loc = sp.get("location", "")
            val = sp.get("value", 0)
            if val:
                dist_m = val if sp.get("distance_unit") == "m" else val * 1000
            elif sp.get("distance") == "3km":
                dist_m = 3000
        elif isinstance(sp, str) and not loc:
            # parse from string like '부산항입구 반경 3000m'
            import re
            loc_match = re.search(r'^(.+?)\s*(?:반경|기준)', sp)
            if loc_match:
                loc = loc_match.group(1).strip()
            dist_match = re.search(r'(\d+)\s*m', sp)
            if dist_match:
                dist_m = int(dist_match.group(1))
                
    tgt_list = pi_dict.get("target_objects", [])
    if qec_slots.get("target_term") or state_slots.get("target_term"):
        tgt = qec_slots.get("target_term") or state_slots.get("target_term")
    elif tgt_list and isinstance(tgt_list, list) and len(tgt_list) > 0:
        tgt = tgt_list[0]
    else:
        tgt = "None"
        
    plan_tools = []
    if task_plan_val:
        if isinstance(task_plan_val, dict):
            plan_tools = task_plan_val.get("tools", task_plan_val.get("required_tools", []))
        elif hasattr(task_plan_val, "tools"):
            plan_tools = task_plan_val.tools
    if not plan_tools and isinstance(tp, dict):
        plan_tools = tp.get("tools", tp.get("required_tools", []))
            
    mapping_result = {
        "location_text": loc,
        "distance_m": dist_m,
        "target_term": tgt,
        "spatial_relation": qec_slots.get("spatial_relation") or state_slots.get("spatial_relation"),
        "derived_concept": verified_derived if verified_derived != "None" else "",
        "candidate_canonical_terms": canonical_list,
        "context": ctx_dict.get("analysis_type") or ctx_dict.get("selected_context", ""),
        "agent": ctx_dict.get("selected_agents", [""])[0] if ctx_dict.get("selected_agents") else "",
        "tools": plan_tools or ([ctx_dict.get("selected_tool")] if ctx_dict.get("selected_tool") else []),
        "execution_ready": authorized_execution,
        "readiness": qec_dict.get("readiness") or tp.get("route_plan_status"),
        "blockers": qec_dict.get("blockers", []),
        "warnings": qec_dict.get("warnings", []),
    }
    mapping_result["KG"] = state_vals.get("graph_context", state_vals.get("graph_rag_context", {}))
    mapping_result["Data Lake"] = state_vals.get("data_discovery_result", {})
    router_trace = {
        "semantic_prior": candidate_trace.get("semantic_prior"),
        "fast_path_policy": fast_path_policy,
        "route_candidates": (candidate_trace.get("route_candidates") or [])[:5],
        "capability_candidates": (candidate_trace.get("capability_candidates") or [])[:8],
        "verified_candidates": (candidate_trace.get("verified_candidates") or [])[:8],
        "execution_contract": candidate_trace.get("execution_contract") or final_orch.get("execution_contract") or {},
        "ollama_policy": candidate_trace.get("ollama_policy") or {},
        "retrieval_mode": candidate_trace.get("mode"),
        "contract": candidate_trace.get("contract"),
    }

    structured_res = agent_result.structured_result if agent_result and hasattr(agent_result, "structured_result") and agent_result.structured_result else {}
    query_result_summary = {
        "count": structured_res.get("count", 0),
        "distance": structured_res.get("distance", "")
    } if structured_res else None

    spatial_exec = {
        "도구 호출": [tc.model_dump() if hasattr(tc, "model_dump") else tc for tc in agent_result.tool_calls] if agent_result and hasattr(agent_result, "tool_calls") and agent_result.tool_calls else [],
        "쿼리 결과값": query_result_summary,
        "warnings": agent_result.warnings if agent_result and hasattr(agent_result, "warnings") else [],
        "reference_point": {
            "location_text": loc,
            "lon": pi_dict.get("spatial_conditions")[0].get("lon", 0) if pi_dict.get("spatial_conditions") and isinstance(pi_dict.get("spatial_conditions")[0], dict) else 0,
            "lat": pi_dict.get("spatial_conditions")[0].get("lat", 0) if pi_dict.get("spatial_conditions") and isinstance(pi_dict.get("spatial_conditions")[0], dict) else 0,
        },
        "query_template": agent_result.provenance.get("query_template", "") if agent_result and hasattr(agent_result, "provenance") and agent_result.provenance else "",
        "geometry_types": pi_dict.get("spatial_conditions")[0].get("geometry_types", []) if pi_dict.get("spatial_conditions") and isinstance(pi_dict.get("spatial_conditions")[0], dict) else [],
        "executed_query": agent_result.provenance.get("executed_query", "") if agent_result and hasattr(agent_result, "provenance") and agent_result.provenance else ""
    }
    spatial_exec["RAG"] = {
        "filters": structured_res.get("rag_filters", {}),
        "graph_paths": structured_res.get("graph_paths", []),
        "citations": structured_res.get("citations", [])
    }
    spatial_exec["Agent"] = {
        "agent_name": agent_result.agent_name if agent_result else None,
        "status": agent_result.status if agent_result else None,
        "provenance": agent_result.provenance if agent_result else {}
    }

    debug_trace = {
        "1. 사용자 질의": state_vals.get("query"),
        "2. 질의 정규화": norm_dict,
        "3. 오케스트레이터 의도분석": intent_dict,
        "질의_정규화_매핑_결과": mapping_result,
        "4. 작업계획 수립": task_plan_val.model_dump() if hasattr(task_plan_val, "model_dump") else task_plan_val,
        "5. 공간쿼리 실행": spatial_exec
    }
    debug_trace.update({
        "user_query": state_vals.get("query"),
        "normalization": norm_dict,
        "normalization_mapping": mapping_result,
        "orchestrator_intent": intent_dict,
        "task_plan": task_plan_val.model_dump() if hasattr(task_plan_val, "model_dump") else task_plan_val,
        "spatial_execution": spatial_exec,
        "router_trace": router_trace,
    })
    return debug_trace

@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    if task_id not in TASK_STORE:
        raise HTTPException(status_code=404, detail="Task not found")

    task_data = TASK_STORE.get(task_id, {})
    stored_final = task_data.get("final_result") if isinstance(task_data.get("final_result"), dict) else {}
    if task_data.get("instant_fast_path") or (stored_final.get("orchestrator_v2") or {}).get("fast_path") == "instant_place_navigation":
        return {
            "task_id": task_id,
            "status": task_data.get("status"),
            "query": task_data.get("query"),
            "error_message": task_data.get("error_message"),
            "history": task_data.get("state_history", []),
            "parsed_intent": None,
            "agent_result": task_data.get("agent_result"),
            "final_result": stored_final,
            "normalization_debug": None,
            "normalized_query": ((stored_final.get("orchestrator_v2") or {}).get("query_execution_context") or {}).get("normalized_query"),
            "task_plan": (stored_final.get("orchestrator_v2") or {}).get("route_plan"),
            "debug_trace": stored_final.get("debug_trace"),
            "persisted": True,
            "updated_at": task_data.get("updated_at"),
        }
    # A test client (or a caller immediately after POST) can observe the
    # durable accepted state before a workflow checkpoint exists.
    if task_data.get("status") == AgentStatus.RECEIVED:
        return {
            "task_id": task_id,
            "status": task_data.get("status"),
            "query": task_data.get("query"),
            "error_message": task_data.get("error_message"),
            "history": task_data.get("state_history", []),
            "parsed_intent": None,
            "agent_result": task_data.get("agent_result"),
            "final_result": task_data.get("final_result"),
            "normalization_debug": None,
            "debug_trace": stored_final.get("debug_trace"),
            "persisted": True,
            "updated_at": task_data.get("updated_at"),
        }
        
    config = {"configurable": {"thread_id": task_id}}
    state_snapshot = orchestrator_graph.get_state(config)
    
    if not state_snapshot or not state_snapshot.values:
        task_data = TASK_STORE.get(task_id, {})
        stored_final = task_data.get("final_result") if isinstance(task_data.get("final_result"), dict) else {}
        return {
            "task_id": task_id, 
            "status": task_data.get("status", "PENDING_OR_NOT_STARTED"),
            "query": task_data.get("query"),
            "error_message": task_data.get("error_message"),
            "history": task_data.get("state_history", []),
            "parsed_intent": None,
            "agent_result": task_data.get("agent_result"),
            "final_result": task_data.get("final_result"),
            "normalization_debug": None,
            "debug_trace": stored_final.get("debug_trace"),
            "persisted": True,
            "updated_at": task_data.get("updated_at")
        }
        
    current_state = state_snapshot.values
    
    agent_request = current_state.get("agent_request")
    parsed_intent = None
    if agent_request:
        if hasattr(agent_request, "parsed_intent") and agent_request.parsed_intent:
            parsed_intent = agent_request.parsed_intent.model_dump()
        elif isinstance(agent_request, dict) and agent_request.get("parsed_intent"):
            pi = agent_request.get("parsed_intent")
            parsed_intent = pi.model_dump() if hasattr(pi, "model_dump") else pi
        
    query_text = current_state.get("query")
    if agent_request:
        if hasattr(agent_request, "original_query") and agent_request.original_query:
            query_text = agent_request.original_query
        elif isinstance(agent_request, dict) and agent_request.get("original_query"):
            query_text = agent_request.get("original_query")
            
    # --- Debug Trace 구성 ---
    debug_trace = build_debug_trace(current_state)
    _persist_state(task_id, current_state)
            
    return {
        "task_id": task_id,
        "query": query_text,
        "status": current_state.get("status", "FAILED"),
        "error_message": current_state.get("error_message"),
        "history": current_state.get("state_history", []),
        "parsed_intent": parsed_intent,
        "agent_result": current_state.get("agent_result").model_dump() if current_state.get("agent_result") and hasattr(current_state.get("agent_result"), "model_dump") else current_state.get("agent_result"),
        "final_result": current_state.get("final_dict"),
        "normalization_debug": current_state.get("normalization_debug", []),
        "normalized_query": current_state.get("normalized_query"),
        "context_result": current_state.get("context_result").__dict__ if current_state.get("context_result") else None,
        "task_plan": current_state.get("task_plan"),
        "debug_trace": debug_trace
    }

@router.post("/tasks/{task_id}/approve")
async def approve_hitl_task(task_id: str):
    """
    WAITING_FOR_REVIEW 상태에 있는 태스크를 관리자가 검토 후 강제 승인 처리하고 
    중단되었던 LangGraph 실행을 재개(Resume)합니다.
    """
    if task_id not in TASK_STORE:
        raise HTTPException(status_code=404, detail="Task not found")
        
    config = {"configurable": {"thread_id": task_id}}
    state_snapshot = orchestrator_graph.get_state(config)
    
    if not state_snapshot or not state_snapshot.values:
        raise HTTPException(status_code=404, detail="State not found in memory checkpointer")
        
    current_state = state_snapshot.values
    if current_state.get("status") != AgentStatus.WAITING_FOR_REVIEW:
        raise HTTPException(status_code=400, detail="Task is not in WAITING_FOR_REVIEW state")
        
    # 상태 업데이트 (Resume을 위한 플래그 삽입)
    # LangGraph의 update_state를 사용하여 현재 스레드에 approval_granted 플래그를 주입합니다.
    orchestrator_graph.update_state(config, {"approval_granted": True})
    TASK_STORE.update(task_id, status="RESUMED")
    
    # 중단된 지점부터 비동기 재실행 (다음 노드로 이동)
    asyncio.create_task(orchestrator_graph.ainvoke(None, config=config))
    
    return {"task_id": task_id, "status": "RESUMED", "message": "Task approved and resumed by human"}
