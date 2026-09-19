"""Read-only U-Port planning endpoint."""

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session
from data.database import get_s101_db
from services.uport.execution import UportExecutionResult, execute_query
from services.uport.planning import UportPlanRequest, plan_query
from shared.schemas.agent import QueryExecutionContext

router = APIRouter(prefix="/uport", tags=["U-Port Planning"])


@router.post("/query/plan", response_model=QueryExecutionContext)
def create_query_plan(request: UportPlanRequest) -> QueryExecutionContext:
    """Return a validated QEC and dependency plan without executing tools."""
    return plan_query(request)


@router.post("/query/execute", response_model=UportExecutionResult)
def run_query(request: UportPlanRequest, db: Session | None = Depends(get_s101_db)) -> UportExecutionResult:
    """Run an authorized read-only specialist after QEC and DB ID validation."""
    return execute_query(request, db)
