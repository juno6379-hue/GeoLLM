"""Shared physical feasibility and deterministic schedule evaluation."""

from datetime import timedelta

from services.uport.optimization.contracts import (
    Assignment, Berth, OptimizationInfeasible, OptimizationRequest,
    OptimizationResult, VesselJob,
)


def eligible(job: VesselJob, berth: Berth, safety_distance_m: float) -> bool:
    """Check each physical constraint before any algorithm ranks a berth."""

    return (job.loa_m + safety_distance_m <= berth.length_m
            and job.draft_m <= berth.water_depth_m
            and (berth.max_beam_m is None or job.beam_m <= berth.max_beam_m)
            and job.cargo_type in berth.cargo_types)


def schedule(request: OptimizationRequest, choices: tuple[int, ...], algorithm: str) -> OptimizationResult:
    """Build nonoverlapping intervals from a berth choice per sorted job.

    Jobs are processed in arrival order. Each chosen berth has one next-free
    timestamp, so assignments cannot overlap even when arrival times coincide.
    """

    jobs = sorted(request.jobs, key=lambda job: (job.arrival_at, -job.priority, job.job_id))
    if len(choices) != len(jobs):
        raise ValueError("one berth choice is required per job")
    next_free = {berth.berth_id: berth.available_from for berth in request.berths}
    assignments = []
    for job, berth_index in zip(jobs, choices):
        if berth_index < 0 or berth_index >= len(request.berths):
            raise ValueError("invalid berth index")
        berth = request.berths[berth_index]
        if not eligible(job, berth, request.safety_distance_m):
            raise OptimizationInfeasible(f"{job.job_id} does not fit {berth.berth_id}")
        start = max(job.arrival_at, next_free[berth.berth_id])
        end = start + timedelta(minutes=job.service_minutes)
        if end > berth.available_until:
            raise OptimizationInfeasible(f"{job.job_id} exceeds {berth.berth_id} availability")
        wait = (start - job.arrival_at).total_seconds() / 60
        assignments.append(Assignment(job_id=job.job_id, berth_id=berth.berth_id,
                                      start_at=start, end_at=end, waiting_minutes=wait))
        next_free[berth.berth_id] = end
    waits = [item.waiting_minutes for item in assignments]
    return OptimizationResult(algorithm=algorithm, source_dataset_id=request.source_dataset_id,
                              assignments=assignments, total_waiting_minutes=sum(waits),
                              maximum_waiting_minutes=max(waits))


def eligible_indices(request: OptimizationRequest) -> list[list[int]]:
    """Reject an impossible vessel before spending time on a search."""

    jobs = sorted(request.jobs, key=lambda job: (job.arrival_at, -job.priority, job.job_id))
    options = [[index for index, berth in enumerate(request.berths)
                if eligible(job, berth, request.safety_distance_m)
                and max(job.arrival_at, berth.available_from) + timedelta(minutes=job.service_minutes) <= berth.available_until]
               for job in jobs]
    for job, matches in zip(jobs, options):
        if not matches:
            raise OptimizationInfeasible(f"no physically available berth for {job.job_id}")
    return options
