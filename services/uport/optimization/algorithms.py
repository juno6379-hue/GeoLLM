"""FCFS baseline and bounded NSGA-II search over feasible berth choices."""

import random
from datetime import timedelta

from services.uport.optimization.common import eligible_indices, schedule
from services.uport.optimization.contracts import (
    OptimizationInfeasible, OptimizationRequest, OptimizationResult,
)


class FCFSOptimizer:
    """Assign arrivals to the berth with the earliest feasible completion."""

    def optimize(self, request: OptimizationRequest) -> OptimizationResult:
        options = eligible_indices(request)
        jobs = sorted(request.jobs, key=lambda job: (job.arrival_at, -job.priority, job.job_id))
        free = {berth.berth_id: berth.available_from for berth in request.berths}
        choices = []
        for job, matches in zip(jobs, options):
            candidates = []
            for index in matches:
                berth = request.berths[index]
                start = max(job.arrival_at, free[berth.berth_id])
                end = start + timedelta(minutes=job.service_minutes)
                if end <= berth.available_until:
                    candidates.append((start, end, berth.berth_id, index))
            if not candidates:
                raise OptimizationInfeasible(f"no available time slot for {job.job_id}")
            start, end, berth_id, index = min(candidates)
            free[berth_id] = end
            choices.append(index)
        return schedule(request, tuple(choices), "FCFS")


def _dominates(left: OptimizationResult, right: OptimizationResult) -> bool:
    """Minimize both total and worst individual waiting time."""

    return (left.total_waiting_minutes <= right.total_waiting_minutes
            and left.maximum_waiting_minutes <= right.maximum_waiting_minutes
            and (left.total_waiting_minutes < right.total_waiting_minutes
                 or left.maximum_waiting_minutes < right.maximum_waiting_minutes))


def _rank(results: list[OptimizationResult]) -> tuple[list[int], list[float]]:
    """Compute NSGA-II non-dominated fronts and crowding distances."""

    n = len(results)
    dominated = [[] for _ in results]
    count = [0] * n
    ranks = [0] * n
    fronts = [[]]
    for i in range(n):
        for j in range(i + 1, n):
            if _dominates(results[i], results[j]):
                dominated[i].append(j)
                count[j] += 1
            elif _dominates(results[j], results[i]):
                dominated[j].append(i)
                count[i] += 1
    fronts[0] = [i for i, value in enumerate(count) if value == 0]
    depth = 0
    while fronts[depth]:
        following = []
        for index in fronts[depth]:
            for other in dominated[index]:
                count[other] -= 1
                if count[other] == 0:
                    ranks[other] = depth + 1
                    following.append(other)
        fronts.append(following)
        depth += 1
    crowding = [0.0] * n
    for front in fronts[:-1]:
        for metric in ("total_waiting_minutes", "maximum_waiting_minutes"):
            ordered = sorted(front, key=lambda i: getattr(results[i], metric))
            crowding[ordered[0]] = crowding[ordered[-1]] = float("inf")
            extent = getattr(results[ordered[-1]], metric) - getattr(results[ordered[0]], metric)
            if extent:
                for position in range(1, len(ordered) - 1):
                    crowding[ordered[position]] += (
                        getattr(results[ordered[position + 1]], metric)
                        - getattr(results[ordered[position - 1]], metric)) / extent
    return ranks, crowding


class NSGAIIOptimizer:
    """Seeded genetic search with Pareto rank, crowding and elitist survival."""

    def __init__(self, population_size: int = 24, generations: int = 20, seed: int = 0):
        if population_size < 4 or generations < 1:
            raise ValueError("NSGA-II needs at least four individuals and one generation")
        self.population_size = population_size
        self.generations = generations
        self.seed = seed

    def optimize(self, request: OptimizationRequest) -> OptimizationResult:
        options = eligible_indices(request)
        baseline = FCFSOptimizer().optimize(request)
        berth_index = {berth.berth_id: i for i, berth in enumerate(request.berths)}
        baseline_genes = tuple(berth_index[item.berth_id] for item in baseline.assignments)
        rng = random.Random(self.seed)
        population = [baseline_genes]
        population.extend(tuple(rng.choice(matches) for matches in options)
                          for _ in range(self.population_size - 1))

        def assess(genes):
            try:
                return schedule(request, genes, "NSGA-II")
            except OptimizationInfeasible:
                return None

        for _ in range(self.generations):
            feasible = [(genes, result) for genes in population
                        if (result := assess(genes)) is not None]
            if not feasible:
                raise OptimizationInfeasible("no feasible NSGA-II population")
            ranks, crowding = _rank([result for _, result in feasible])
            ordered = sorted(range(len(feasible)), key=lambda i: (ranks[i], -crowding[i]))
            parents = [feasible[i][0] for i in ordered[:self.population_size]]
            children = []
            while len(children) < self.population_size:
                first, second = rng.choice(parents), rng.choice(parents)
                genes = tuple(rng.choice((a, b)) for a, b in zip(first, second))
                if rng.random() < 0.35:
                    position = rng.randrange(len(genes))
                    genes = genes[:position] + (rng.choice(options[position]),) + genes[position + 1:]
                children.append(genes)
            # Preserve the best feasible parents while allowing offspring to compete.
            pool = parents + children + [baseline_genes]
            scored = [(genes, result) for genes in pool if (result := assess(genes)) is not None]
            ranks, crowding = _rank([result for _, result in scored])
            indices = sorted(range(len(scored)), key=lambda i: (ranks[i], -crowding[i]))
            population = [scored[i][0] for i in indices[:self.population_size]]
        finalists = [result for genes in population if (result := assess(genes)) is not None]
        # The API returns a single reproducible Pareto candidate for comparison.
        return min(finalists, key=lambda result: (result.total_waiting_minutes,
                                                 result.maximum_waiting_minutes))
