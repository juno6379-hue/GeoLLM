"""Read-only ETA model availability and prediction API."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.uport.prediction.agent import PredictionAgent
from services.uport.prediction.contracts import ETAInput, ETAOutput, ModelNotAvailable
from services.uport.prediction.registry import ModelDescriptor, ModelRegistry

router = APIRouter(prefix="/uport/predictions", tags=["U-Port Prediction"])


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


@router.post("/eta", response_model=ETAOutput)
def predict_eta(data: ETAInput) -> ETAOutput:
    """Reject requests while no artifact with accepted evaluation exists."""
    try:
        return PredictionAgent().predict(data)
    except ModelNotAvailable as exc:
        raise HTTPException(status_code=503, detail={
            "code": "MODEL_NOT_AVAILABLE", "message": str(exc),
        }) from exc
