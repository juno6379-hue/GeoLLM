"""Explicit inference adapter boundaries for the three ETA model families.

These classes are intentionally non-executable until a trained artifact loader
and validation pipeline are registered. They never synthesize an ETA value.
"""

from typing import Literal

from services.uport.prediction.contracts import ETAInput, ETAOutput, ModelNotAvailable


class _UnavailableAdapter:
    family: Literal["LSTM", "GRU", "TFT"]
    # 학습 가중치 로더와 실제 추론 경로가 구현되기 전에는 준비 완료로 표시하지 않는다.
    inference_ready = False

    def predict(self, data: ETAInput) -> ETAOutput:
        """Reject inference because no fitted model implementation is bound."""
        raise ModelNotAvailable(f"{self.family} ETA model artifact is not registered")


class LSTMAdapter(_UnavailableAdapter):
    family = "LSTM"


class GRUAdapter(_UnavailableAdapter):
    family = "GRU"


class TFTAdapter(_UnavailableAdapter):
    family = "TFT"
