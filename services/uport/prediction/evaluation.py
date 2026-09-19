"""Holdout ETA error measurement for registered prediction models."""

import math
from datetime import datetime, timezone
from statistics import mean

from pydantic import BaseModel, Field, field_validator, model_validator


class ETACase(BaseModel):
    """One previously unseen arrival with model prediction and actual time."""
    sample_id: str = Field(min_length=1)
    observed_at: datetime
    predicted_eta_at: datetime
    actual_arrival_at: datetime

    @field_validator("observed_at", "predicted_eta_at", "actual_arrival_at")
    @classmethod
    def utc_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("ETA evaluation timestamps must include a timezone")
        return value.astimezone(timezone.utc)

    @model_validator(mode="after")
    def arrival_after_observation(self):
        if self.actual_arrival_at <= self.observed_at:
            raise ValueError("actual arrival must follow the observation")
        if self.predicted_eta_at <= self.observed_at:
            raise ValueError("predicted ETA must follow the observation")
        return self


class ModelEvaluation(BaseModel):
    """Comparable holdout metrics, all in minutes and tied to one dataset."""
    model_id: str
    model_version: str
    evaluation_dataset_id: str
    sample_count: int = Field(ge=1)
    mae_minutes: float = Field(ge=0, allow_inf_nan=False)
    rmse_minutes: float = Field(ge=0, allow_inf_nan=False)
    p90_absolute_error_minutes: float = Field(ge=0, allow_inf_nan=False)
    bias_minutes: float = Field(allow_inf_nan=False)
    evaluated_at: datetime


def evaluate_eta(
    model_id: str, model_version: str, evaluation_dataset_id: str,
    cases: list[ETACase],
) -> ModelEvaluation:
    """Measure actual minus predicted arrival on a de-duplicated holdout set."""
    if not cases:
        raise ValueError("evaluation requires holdout cases")
    if len({case.sample_id for case in cases}) != len(cases):
        raise ValueError("holdout sample IDs must be unique")
    errors = [(case.predicted_eta_at - case.actual_arrival_at).total_seconds() / 60
              for case in cases]
    absolute = sorted(abs(value) for value in errors)
    p90_index = math.ceil(0.9 * len(absolute)) - 1
    return ModelEvaluation(
        model_id=model_id, model_version=model_version,
        evaluation_dataset_id=evaluation_dataset_id, sample_count=len(cases),
        mae_minutes=mean(absolute),
        rmse_minutes=math.sqrt(mean(value * value for value in errors)),
        p90_absolute_error_minutes=absolute[p90_index],
        bias_minutes=mean(errors), evaluated_at=datetime.now(timezone.utc),
    )
