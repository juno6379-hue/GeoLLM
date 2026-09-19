"""ETA contracts, holdout metrics and model availability gates."""

from datetime import datetime, timedelta, timezone
from math import sqrt

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from services.uport.prediction.contracts import ETAInput, ETAOutput
from services.uport.prediction.agent import PredictionAgent
from services.uport.prediction.evaluation import ETACase, ModelEvaluation, evaluate_eta
from services.uport.prediction.registry import ModelDescriptor, ModelRegistry
from services.uport.prediction.router import router

NOW = datetime(2026, 9, 19, 10, 0, tzinfo=timezone.utc)


def _eta_input():
    return {
        "mmsi": "440123456", "port_id": "ulsan", "source_dataset_id": "ais-live",
        "observations": [
            {"observed_at": NOW.isoformat(), "longitude": 129.4, "latitude": 35.5,
             "speed_knots": 8.2},
            {"observed_at": (NOW + timedelta(minutes=5)).isoformat(),
             "longitude": 129.41, "latitude": 35.51, "speed_knots": 8.3},
        ],
    }


def test_eta_input_rejects_unordered_or_naive_ais_observations():
    data = _eta_input()
    data["observations"][1]["observed_at"] = NOW.isoformat()
    with pytest.raises(ValidationError):
        ETAInput.model_validate(data)
    data["observations"][1]["observed_at"] = "2026-09-19T10:05:00"
    with pytest.raises(ValidationError):
        ETAInput.model_validate(data)


def test_eta_output_rejects_arrival_before_last_observation():
    with pytest.raises(ValidationError):
        ETAOutput(
            mmsi="440123456", port_id="ulsan", eta_at=NOW,
            model_id="uport.eta.gru", model_version="1", source_dataset_id="ais-live",
            input_window_start=NOW - timedelta(minutes=5), input_window_end=NOW,
            generated_at=NOW,
        )


def test_holdout_metrics_use_observed_arrivals_in_minutes():
    cases = [
        ETACase(sample_id="a", observed_at=NOW, predicted_eta_at=NOW + timedelta(minutes=70),
                actual_arrival_at=NOW + timedelta(minutes=60)),
        ETACase(sample_id="b", observed_at=NOW, predicted_eta_at=NOW + timedelta(minutes=40),
                actual_arrival_at=NOW + timedelta(minutes=60)),
    ]
    result = evaluate_eta("uport.eta.lstm", "1", "holdout-1", cases)
    assert result.sample_count == 2
    assert result.mae_minutes == 15
    assert result.rmse_minutes == pytest.approx(sqrt(250))
    assert result.p90_absolute_error_minutes == 20
    assert result.bias_minutes == -5
    with pytest.raises(ValueError, match="unique"):
        evaluate_eta("uport.eta.lstm", "1", "holdout-1", [cases[0], cases[0]])


def test_registry_requires_artifact_matching_holdout_and_minimum_samples(tmp_path):
    artifact = tmp_path / "trained-model.bin"
    artifact.write_bytes(b"artifact-presence-only")
    registry = ModelRegistry(models=[
        ModelDescriptor(model_id="a", family="LSTM", version="1", status="ready",
                        artifact_path=str(artifact), evaluation_dataset_id="holdout-1"),
        ModelDescriptor(model_id="b", family="GRU", version="1", status="ready",
                        artifact_path=str(artifact), evaluation_dataset_id="holdout-1"),
    ], minimum_holdout_samples=30)
    evaluations = [
        ModelEvaluation(model_id="a", model_version="1", evaluation_dataset_id="holdout-1",
                        sample_count=30, mae_minutes=12, rmse_minutes=18,
                        p90_absolute_error_minutes=25, bias_minutes=1, evaluated_at=NOW),
        ModelEvaluation(model_id="b", model_version="1", evaluation_dataset_id="holdout-1",
                        sample_count=30, mae_minutes=9, rmse_minutes=15,
                        p90_absolute_error_minutes=20, bias_minutes=0, evaluated_at=NOW),
    ]
    assert registry.select_best(evaluations).model_id == "b"
    # 메타데이터와 평가가 준비되어도 추론 어댑터가 없으면 서비스를 열지 않는다.
    registry.evaluations = evaluations
    assert PredictionAgent(registry).can_predict() is False
    assert registry.select_best([evaluations[1].model_copy(update={"sample_count": 29})]) is None
    artifact.unlink()
    assert registry.select_best(evaluations) is None


def test_untrained_registry_and_api_never_return_an_eta():
    registry = ModelRegistry.load()
    assert {model.family for model in registry.models} == {"LSTM", "GRU", "TFT"}
    assert registry.select_best([]) is None
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    client = TestClient(app)
    status = client.get("/api/v1/uport/predictions/models")
    assert status.status_code == 200
    assert status.json()["inference_available"] is False
    response = client.post("/api/v1/uport/predictions/eta", json=_eta_input())
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "MODEL_NOT_AVAILABLE"
