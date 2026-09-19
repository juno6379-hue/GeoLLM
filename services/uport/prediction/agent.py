"""ETA specialist that refuses inference without a verified model."""

from services.uport.prediction.adapters import GRUAdapter, LSTMAdapter, TFTAdapter
from services.uport.prediction.contracts import ETAInput, ETAOutput, ModelNotAvailable
from services.uport.prediction.evaluation import ModelEvaluation
from services.uport.prediction.registry import ModelRegistry

_ADAPTERS = {"LSTM": LSTMAdapter, "GRU": GRUAdapter, "TFT": TFTAdapter}


class PredictionAgent:
    """Select a validated ETA model before invoking its family adapter."""

    def __init__(self, registry: ModelRegistry | None = None):
        self.registry = registry or ModelRegistry.load()

    def can_predict(self) -> bool:
        """평가를 통과한 아티팩트와 실행 가능한 어댑터를 모두 확인한다."""
        descriptor = self.registry.best_available()
        return bool(descriptor and _ADAPTERS[descriptor.family].inference_ready)

    def predict(self, data: ETAInput, evaluations: list[ModelEvaluation] | None = None) -> ETAOutput:
        """Return a model value only after an artifact and evaluation qualify.

        Phase 7 adapters have no fitted weights. They raise ModelNotAvailable,
        so the API cannot invent an ETA when inputs or Registry metadata exist.
        """
        descriptor = self.registry.select_best(evaluations) if evaluations is not None else self.registry.best_available()
        if descriptor is None:
            raise ModelNotAvailable("No trained ETA model passed the Registry quality gate")
        adapter = _ADAPTERS[descriptor.family]()
        if not adapter.inference_ready:
            raise ModelNotAvailable(f"{descriptor.family} ETA inference adapter is not implemented")
        return adapter.predict(data)
