"""Validated, source-attributed inputs and outputs for berth scheduling."""

from datetime import datetime
from typing import Literal, Protocol

from pydantic import BaseModel, Field, model_validator


class Berth(BaseModel):
    """Physical limits and cargo compatibility of one operational berth."""

    berth_id: str = Field(min_length=1)
    length_m: float = Field(gt=0)
    water_depth_m: float = Field(gt=0)
    max_beam_m: float | None = Field(default=None, gt=0)
    cargo_types: set[str] = Field(min_length=1)
    available_from: datetime
    available_until: datetime

    @model_validator(mode="after")
    def validate_window(self):
        if self.available_from.tzinfo is None or self.available_until.tzinfo is None:
            raise ValueError("berth availability must include a timezone")
        if self.available_from >= self.available_until:
            raise ValueError("berth availability window is empty")
        return self


class VesselJob(BaseModel):
    """A vessel request with explicit dimensions and service time."""

    job_id: str = Field(min_length=1)
    loa_m: float = Field(gt=0)
    beam_m: float = Field(gt=0)
    draft_m: float = Field(gt=0)
    cargo_type: str = Field(min_length=1)
    arrival_at: datetime
    service_minutes: int = Field(gt=0)
    priority: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_time(self):
        if self.arrival_at.tzinfo is None:
            raise ValueError("arrival time must include a timezone")
        return self


class OptimizationRequest(BaseModel):
    """One comparable snapshot supplied by an identified data source."""

    port_id: str = Field(min_length=1)
    source_dataset_id: str = Field(min_length=1)
    berths: list[Berth] = Field(min_length=1)
    jobs: list[VesselJob] = Field(min_length=1)
    safety_distance_m: float = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_ids(self):
        # Stable IDs are essential: the public CSVs lack a reliable cross-file vessel key.
        for items, field in ((self.berths, "berth_id"), (self.jobs, "job_id")):
            values = [getattr(item, field) for item in items]
            if len(values) != len(set(values)):
                raise ValueError(f"duplicate {field}")
        return self


class Assignment(BaseModel):
    """A calculated occupied interval on a qualified berth."""

    job_id: str
    berth_id: str
    start_at: datetime
    end_at: datetime
    waiting_minutes: float = Field(ge=0)


class OptimizationResult(BaseModel):
    """Comparable algorithm result, never an LLM-generated schedule."""

    algorithm: Literal["FCFS", "NSGA-II", "MIP/CBC", "MIP/HiGHS"]
    source_dataset_id: str
    assignments: list[Assignment]
    total_waiting_minutes: float = Field(ge=0)
    maximum_waiting_minutes: float = Field(ge=0)


class BerthOptimizer(Protocol):
    """Every optimizer evaluates the same validated request contract."""

    def optimize(self, request: OptimizationRequest) -> OptimizationResult: ...


class OptimizationUnavailable(Exception):
    """An optional solver or required operational input is unavailable."""


class OptimizationInfeasible(Exception):
    """No assignment satisfies the supplied physical and time constraints."""
