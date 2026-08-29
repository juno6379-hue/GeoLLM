"""Evidence-first accident layer integration for the orchestrator."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from shared.schemas.agent import AgentRequest, AgentResult, AgentStatus
from services.orchestrator.specialist_kg_context import build_specialist_kg_context

ROOT = Path(__file__).resolve().parents[2]
ACCIDENT_LAYER = ROOT / "outputs/standardized/accident_spatial_layers.geojson"


async def execute_accident_risk(request: AgentRequest) -> AgentResult:
    context = build_specialist_kg_context("accident", request)
    geojson = None
    source_status = "PENDING_ACCIDENT_LAYER"
    if ACCIDENT_LAYER.exists():
        try:
            geojson = json.loads(ACCIDENT_LAYER.read_text(encoding="utf-8"))
            source_status = "AVAILABLE"
        except (OSError, ValueError):
            source_status = "INVALID_ACCIDENT_LAYER"

    relations = [
        {"relation": "nearFeature", "status": "PENDING_STATIC_FEATURE_GEOMETRY", "verified": False},
        {"relation": "overlapsFeature", "status": "PENDING_STATIC_FEATURE_GEOMETRY", "verified": False},
        {"relation": "relatedTo", "status": "CANDIDATE", "verified": False, "reason": "Accident event and navigation hazard relation requires spatial/evidence validation"},
    ]
    result = {
        "accident_events": context.get("required_inputs", []),
        "accident_spatial_geojson": geojson,
        "accident_layer_status": source_status,
        "accident_feature_relations": relations,
        "kg_context": context,
    }
    return AgentResult(
        task_id=request.task_id,
        trace_id=request.trace_id,
        agent_name="Accident/Risk Agent",
        agent_version="2.0.0-evidence-first",
        status=AgentStatus.COMPLETED,
        summary=f"Accident layer status: {source_status}",
        structured_result=result,
        provenance={"source_file": "outputs/standardized/accident_spatial_layers.geojson", **context.get("provenance", {})},
        validation_payload={"relation_status": relations, "source_status": source_status},
        created_at=datetime.utcnow(),
    )
