"""Typed data boundary for ETA models and their source attribution."""

from datetime import datetime, timezone
from typing import Literal, Protocol

from pydantic import BaseModel, Field, field_validator, model_validator


class AISObservation(BaseModel):
    """One ordered AIS sample; position and time are source observations."""
    observed_at: datetime
    longitude: float = Field(ge=-180, le=180)
    latitude: float = Field(ge=-90, le=90)
    speed_knots: float = Field(ge=0, le=102.2)

    @field_validator("observed_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("AIS observation time must include a timezone")
        return value.astimezone(timezone.utc)


class ETAInput(BaseModel):
    """Observed vessel track and declared target port, without guessed fields."""
    mmsi: str = Field(pattern=r"^[0-9]{9}$")
    port_id: str = Field(min_length=1, max_length=120)
    source_dataset_id: str = Field(min_length=1, max_length=120)
    observations: list[AISObservation] = Field(min_length=2, max_length=360)

    @model_validator(mode="after")
    def ordered_observations(self):
        times = [row.observed_at for row in self.observations]
        if any(later <= earlier for earlier, later in zip(times, times[1:])):
            raise ValueError("AIS observations must be strictly increasing in time")
        return self


class ETAOutput(BaseModel):
    """Predicted timestamp with enough provenance to evaluate and display it."""
    mmsi: str
    port_id: str
    eta_at: datetime
    model_id: str
    model_version: str
    source_dataset_id: str
    input_window_start: datetime
    input_window_end: datetime
    generated_at: datetime
    confidence: float | None = Field(default=None, ge=0, le=1)

    @model_validator(mode="after")
    def valid_prediction_window(self):
        """Reject timestamps that cannot represent a forward ETA forecast."""
        times = (self.eta_at, self.input_window_start, self.input_window_end, self.generated_at)
        if any(value.tzinfo is None or value.utcoffset() is None for value in times):
            raise ValueError("ETA output timestamps must include a timezone")
        if self.input_window_end <= self.input_window_start:
            raise ValueError("input window must have positive duration")
        if self.eta_at <= self.input_window_end:
            raise ValueError("predicted ETA must follow the last observation")
        return self


class PredictionModel(Protocol):
    """Common model interface used by LSTM, GRU and TFT implementations."""
    family: Literal["LSTM", "GRU", "TFT"]

    def predict(self, data: ETAInput) -> ETAOutput: ...


class ModelNotAvailable(RuntimeError):
    """No verified model artifact and evaluation are available for inference."""
