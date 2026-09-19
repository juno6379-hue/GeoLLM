"""Optional PuLP mixed-integer berth model with CBC and HiGHS backends."""

from datetime import timedelta
from typing import Literal

from services.uport.optimization.common import eligible_indices
from services.uport.optimization.contracts import (
    OptimizationInfeasible, OptimizationRequest, OptimizationResult,
    OptimizationUnavailable,
)


class MIPOptimizer:
    """Minimize total wait with berth choice and pairwise no-overlap constraints."""

    def __init__(self, solver: Literal["CBC", "HiGHS"] = "CBC", time_limit_seconds: int = 15):
        self.solver = solver
        self.time_limit_seconds = time_limit_seconds

    def optimize(self, request: OptimizationRequest) -> OptimizationResult:
        try:
            import pulp
        except ImportError as exc:
            raise OptimizationUnavailable("PuLP is not installed; CBC/HiGHS MIP unavailable") from exc
        options = eligible_indices(request)
        jobs = sorted(request.jobs, key=lambda job: (job.arrival_at, -job.priority, job.job_id))
        origin = min([job.arrival_at for job in jobs]
                     + [berth.available_from for berth in request.berths])
        minute = lambda moment: (moment - origin).total_seconds() / 60
        horizon = max(minute(berth.available_until) for berth in request.berths)
        big_m = horizon + sum(job.service_minutes for job in jobs) + 1
        problem = pulp.LpProblem("uport_berth_schedule", pulp.LpMinimize)
        start = pulp.LpVariable.dicts("start", range(len(jobs)), lowBound=0)
        chosen = {(i, b): pulp.LpVariable(f"job_{i}_berth_{b}", cat="Binary")
                  for i, berth_options in enumerate(options) for b in berth_options}
        for i, job in enumerate(jobs):
            problem += pulp.lpSum(chosen[i, b] for b in options[i]) == 1
            problem += start[i] >= minute(job.arrival_at)
            for b in options[i]:
                berth = request.berths[b]
                # Big-M activates berth availability only for the selected berth.
                problem += start[i] >= minute(berth.available_from) - big_m * (1 - chosen[i, b])
                problem += start[i] + job.service_minutes <= minute(berth.available_until) + big_m * (1 - chosen[i, b])
        for i in range(len(jobs)):
            for j in range(i + 1, len(jobs)):
                for b in set(options[i]) & set(options[j]):
                    precedence = pulp.LpVariable(f"before_{i}_{j}_{b}", cat="Binary")
                    inactive = 2 - chosen[i, b] - chosen[j, b]
                    problem += start[i] + jobs[i].service_minutes <= start[j] + big_m * (1 - precedence + inactive)
                    problem += start[j] + jobs[j].service_minutes <= start[i] + big_m * (precedence + inactive)
        problem += pulp.lpSum(start[i] - minute(job.arrival_at) for i, job in enumerate(jobs))
        backend = pulp.PULP_CBC_CMD(msg=False, timeLimit=self.time_limit_seconds) if self.solver == "CBC" else pulp.HiGHS_CMD(msg=False, timeLimit=self.time_limit_seconds)
        if not backend.available():
            raise OptimizationUnavailable(f"{self.solver} executable is not available")
        status = problem.solve(backend)
        if status == pulp.LpStatusInfeasible:
            raise OptimizationInfeasible("MIP found no feasible berth schedule")
        if status != pulp.LpStatusOptimal:
            raise OptimizationUnavailable(f"{self.solver} did not prove an optimal solution: {pulp.LpStatus[status]}")
        # Decode the solver's actual timestamps; FCFS-style rescheduling could
        # silently change its chosen order and objective, so never do that here.
        from services.uport.optimization.contracts import Assignment
        assignments = []
        for i, job in enumerate(jobs):
            selected = [b for b in options[i] if pulp.value(chosen[i, b]) > 0.5]
            if len(selected) != 1:
                raise OptimizationUnavailable("MIP returned an invalid berth choice")
            begin = origin + timedelta(minutes=float(pulp.value(start[i])))
            wait = max(0.0, (begin - job.arrival_at).total_seconds() / 60)
            assignments.append(Assignment(job_id=job.job_id, berth_id=request.berths[selected[0]].berth_id,
                                          start_at=begin, end_at=begin + timedelta(minutes=job.service_minutes),
                                          waiting_minutes=wait))
        waits = [item.waiting_minutes for item in assignments]
        return OptimizationResult(algorithm=f"MIP/{self.solver}", source_dataset_id=request.source_dataset_id,
                                  assignments=assignments, total_waiting_minutes=sum(waits),
                                  maximum_waiting_minutes=max(waits))
