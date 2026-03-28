from dataclasses import dataclass
from typing import Protocol

import numpy as np


@dataclass(frozen=True)
class FramePresence:
    vehicle_detected: bool
    confidence: float


@dataclass(frozen=True)
class SpotRecognition:
    vehicle_detected: bool
    plate: str | None
    confidence: float | None


class RecognitionGateway(Protocol):
    def detect_frame_presence(self, frame_image: np.ndarray) -> FramePresence:
        ...

    def detect_spot(self, spot_id: str, spot_image: np.ndarray) -> SpotRecognition:
        ...
