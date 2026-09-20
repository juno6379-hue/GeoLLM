"""Read-only ETA model availability, data readiness and prediction API."""

import json
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.uport.prediction.agent import PredictionAgent
from services.uport.prediction.contracts import ETAInput, ETAOutput, ModelNotAvailable
from services.uport.prediction.registry import ModelDescriptor, ModelRegistry

router = APIRouter(prefix="/uport/predictions", tags=["U-Port Prediction"])
MAX_READINESS_BYTES = 16_384


class ModelStatusResponse(BaseModel):
    """Show registered families without implying that inference is available."""
    task: str
    inference_available: bool
    models: list[ModelDescriptor]


@router.get("/models", response_model=ModelStatusResponse)
def list_prediction_models() -> ModelStatusResponse:
    """Expose model provenance and training status for the dashboard."""
    registry = ModelRegistry.load()
    return ModelStatusResponse(task="eta_prediction",
                               inference_available=PredictionAgent(registry).can_predict(),
                               models=registry.models)


@router.get("/eta-readiness")
def get_eta_readiness() -> dict:
    """Expose the collector's aggregate gate without its vessel-level DB.

    The collector writes a complete temporary file and renames it atomically,
    so a dashboard request sees one consistent quality snapshot. The backend
    mount is read-only and this endpoint never accepts a caller-selected path.
    """
    path = Path(os.getenv("UPORT_ETA_READINESS_PATH", "")).expanduser()
    if not path.is_file():
        raise HTTPException(status_code=503, detail={
            "code": "ETA_READINESS_NOT_AVAILABLE",
            "message": "ETA collection report is not available",
        })
    try:
        with path.open("rb") as handle:
            raw = handle.read(MAX_READINESS_BYTES + 1)
        if len(raw) > MAX_READINESS_BYTES:
            raise ValueError("readiness report exceeds size limit")
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError("readiness report is not an object")
        quality = payload.get("quality", {})
        if not isinstance(quality, dict):
            raise ValueError("readiness quality is not an object")
        # Only expected aggregate fields enter the public response. This
        # allowlist prevents a future collector change from leaking MMSI,
        # callsign, coordinates or provider credentials by accident.
        names = ("stored_positions", "stored_voyages",
                 "voyages_with_repeated_update_times", "arrival_event_rows",
                 "voyages_with_prearrival_update",
                 "structural_prearrival_update_sequences", "minimum_voyages",
                 "timezone_verified", "arrival_definition_verified",
                 "position_clock_verified", "train_voyages", "holdout_voyages",
                 "export_ready", "position_clock_source_field")
        public_quality = {name: quality[name] for name in names if name in quality}
        if not isinstance(public_quality.get("stored_positions"), int):
            raise ValueError("readiness report is missing position count")
        return {"status": "ready" if public_quality.get("export_ready") else "blocked",
                "last_collection_utc": payload.get("last_collection_utc"),
                "quality": public_quality}
    except (OSError, UnicodeError, ValueError, TypeError, KeyError):
        raise HTTPException(status_code=503, detail={
            "code": "ETA_READINESS_INVALID",
            "message": "ETA collection report cannot be read",
        }) from None


@router.post("/eta", response_model=ETAOutput)
def predict_eta(data: ETAInput) -> ETAOutput:
    """Reject requests while no artifact with accepted evaluation exists."""
    try:
        return PredictionAgent().predict(data)
    except ModelNotAvailable as exc:
        raise HTTPException(status_code=503, detail={
            "code": "MODEL_NOT_AVAILABLE", "message": str(exc),
        }) from exc
