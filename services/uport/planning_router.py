"""Read-only U-Port planning endpoint."""

from fastapi import APIRouter
from services.uport.planning import UportPlanRequest, plan_query
from shared.schemas.agent import QueryExecutionContext

router = APIRouter(prefix="/uport", tags=["U-Port Planning"])


@router.post("/query/plan", response_model=QueryExecutionContext)
def create_query_plan(request: UportPlanRequest) -> QueryExecutionContext:
    """Return a validated QEC and dependency plan without executing tools."""
    return plan_query(request)
