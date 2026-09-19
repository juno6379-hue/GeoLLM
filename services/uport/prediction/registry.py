"""Registry and quality gate for deployable ETA prediction artifacts."""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

from services.uport.prediction.evaluation import ModelEvaluation

REGISTRY_PATH = Path(__file__).resolve().parents[3] / "data" / "uport_prediction_models.yaml"


class ModelDescriptor(BaseModel):
    """Versioned model metadata; status alone does not make inference ready."""
    model_id: str
    family: Literal["LSTM", "GRU", "TFT"]
    version: str
    status: Literal["unavailable", "ready"]
    artifact_path: str | None = None
    evaluation_dataset_id: str | None = None


class ModelRegistry(BaseModel):
    """Read model metadata and select only comparable, verified candidates."""
    models: list[ModelDescriptor]
    minimum_holdout_samples: int = Field(ge=1)
    evaluations: list[ModelEvaluation] = Field(default_factory=list)

    @classmethod
    def load(cls, path: Path = REGISTRY_PATH) -> "ModelRegistry":
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if payload.get("task") != "eta_prediction":
            raise ValueError("prediction registry task must be eta_prediction")
        return cls(models=payload["models"],
                   minimum_holdout_samples=payload["minimum_holdout_samples"],
                   evaluations=payload.get("evaluations") or [])

    def best_available(self) -> ModelDescriptor | None:
        """Apply the same holdout gate to the Registry's approved metrics."""
        return self.select_best(self.evaluations)

    def select_best(self, evaluations: list[ModelEvaluation]) -> ModelDescriptor | None:
        """Choose lowest holdout MAE only among comparable ready artifacts.

        A ready flag, artifact on disk, matching version/dataset and enough
        holdout samples are all required. No model is selected by family name.
        """
        qualified: list[tuple[float, float, ModelDescriptor]] = []
        datasets = {evaluation.evaluation_dataset_id for evaluation in evaluations}
        if len(datasets) != 1:
            return None
        for descriptor in self.models:
            if descriptor.status != "ready" or not descriptor.artifact_path:
                continue
            if not Path(descriptor.artifact_path).is_file():
                continue
            for evaluation in evaluations:
                if (evaluation.model_id == descriptor.model_id
                    and evaluation.model_version == descriptor.version
                    and evaluation.evaluation_dataset_id == descriptor.evaluation_dataset_id
                    and evaluation.sample_count >= self.minimum_holdout_samples):
                    qualified.append((evaluation.mae_minutes, evaluation.rmse_minutes, descriptor))
        return min(qualified, key=lambda row: (row[0], row[1], row[2].model_id))[2] if qualified else None
