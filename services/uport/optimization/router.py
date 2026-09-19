"""Compare scheduling algorithms without fabricating live port operations."""

from fastapi import APIRouter
from pydantic import BaseModel

from services.uport.optimization.algorithms import FCFSOptimizer, NSGAIIOptimizer
from services.uport.optimization.contracts import (
    OptimizationInfeasible, OptimizationRequest, OptimizationResult,
    OptimizationUnavailable,
)
from services.uport.optimization.mip import MIPOptimizer

router = APIRouter(prefix="/uport/optimization", tags=["U-Port Optimization"])


class AlgorithmOutcome(BaseModel):
    """A computed plan or an explicit algorithm failure for the same snapshot."""

    algorithm: str
    result: OptimizationResult | None = None
    error_code: str | None = None
    message: str | None = None


class ComparisonResponse(BaseModel):
    port_id: str
    source_dataset_id: str
    outcomes: list[AlgorithmOutcome]


@router.post("/compare", response_model=ComparisonResponse)
def compare_berth_plans(request: OptimizationRequest) -> ComparisonResponse:
    """Run each isolated algorithm on the same source-attributed input."""

    algorithms = (("FCFS", FCFSOptimizer()), ("NSGA-II", NSGAIIOptimizer()),
                  ("MIP/CBC", MIPOptimizer("CBC")), ("MIP/HiGHS", MIPOptimizer("HiGHS")))
    outcomes = []
    for name, optimizer in algorithms:
        try:
            outcomes.append(AlgorithmOutcome(algorithm=name, result=optimizer.optimize(request)))
        except OptimizationInfeasible as exc:
            outcomes.append(AlgorithmOutcome(algorithm=name, error_code="OPTIMIZATION_INFEASIBLE", message=str(exc)))
        except OptimizationUnavailable as exc:
            outcomes.append(AlgorithmOutcome(algorithm=name, error_code="SOLVER_NOT_AVAILABLE", message=str(exc)))
    return ComparisonResponse(port_id=request.port_id, source_dataset_id=request.source_dataset_id,
                              outcomes=outcomes)
