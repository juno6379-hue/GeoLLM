"""Read-only U-Port planning endpoint."""

from fastapi import APIRouter
from fastapi import Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from data.database import get_s101_db
from services.uport.execution import UportExecutionResult, execute_query
from services.uport.planning import UportPlanRequest, plan_query
from services.orchestrator.query_candidate_broker import query_candidate_broker
from shared.schemas.agent import QueryExecutionContext

router = APIRouter(prefix="/uport", tags=["U-Port Planning"])


class UportRouteResponse(BaseModel):
    """Explain the Registry-selected UI execution path before any Tool runs."""

    mode: str
    selected_capabilities: list[str]


@router.post("/query/route", response_model=UportRouteResponse)
def route_dashboard_query(request: UportPlanRequest) -> UportRouteResponse:
    """Choose only implemented paths from Registry candidates and map context.

    The vessel-centered hazard capability takes precedence over a viewport
    match so missing AIS cannot be silently replaced by chart-only results.
    """

    candidates = query_candidate_broker.retrieve_domain_capabilities(request.query, "uport")
    selected = [row["candidate_id"] for row in candidates]
    if "uport.s101.hazard.search" in selected:
        mode = "unavailable"
    elif "uport.s101.hazard.viewport" in selected:
        mode = "s101_hazard_viewport"
    elif ((request.map_selection is not None or "uport.s101.berth.search" in selected)
          and set(selected) <= {"uport.s101.berth.search", "uport.map.visualize"}):
        mode = "s101_berth"
    else:
        mode = "unavailable"
    return UportRouteResponse(mode=mode, selected_capabilities=selected)


@router.post("/query/plan", response_model=QueryExecutionContext)
def create_query_plan(request: UportPlanRequest) -> QueryExecutionContext:
    """Return a validated QEC and dependency plan without executing tools."""
    return plan_query(request)


@router.post("/query/execute", response_model=UportExecutionResult)
def run_query(request: UportPlanRequest, db: Session | None = Depends(get_s101_db)) -> UportExecutionResult:
    """Run an authorized read-only specialist after QEC and DB ID validation."""
    return execute_query(request, db)
