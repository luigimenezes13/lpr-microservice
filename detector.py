from dataclasses import dataclass

import numpy as np

from recognition.infrastructure.model_runtime import RecognitionModelRuntime


@dataclass
class PlateReading:
    text: str
    confidence: float


@dataclass
class DetectionResult:
    vehicle_detected: bool
    plate: PlateReading | None


class VehicleDetector:
    def __init__(self):
        self._runtime = RecognitionModelRuntime()

    def has_vehicle(self, image: np.ndarray) -> bool:
        detected, _ = self._runtime.detect_frame_presence(image)
        return detected


class PlateReader:
    def __init__(self):
        self._runtime = RecognitionModelRuntime()

    def read_plate(self, image: np.ndarray) -> PlateReading | None:
        result = self._runtime.detect_spot(image)
        if result.plate is None:
            return None
        return PlateReading(
            text=result.plate.text,
            confidence=result.plate.confidence,
        )


class Detector:
    def __init__(self):
        self._runtime = RecognitionModelRuntime()

    def detect_vehicle_presence(self, frame_image: np.ndarray) -> bool:
        detected, _ = self._runtime.detect_frame_presence(frame_image)
        return detected

    def detect_spot(self, spot_image: np.ndarray) -> DetectionResult:
        result = self._runtime.detect_spot(spot_image)
        plate = None
        if result.plate is not None:
            plate = PlateReading(text=result.plate.text, confidence=result.plate.confidence)
        return DetectionResult(vehicle_detected=result.vehicle_detected, plate=plate)

    def detect(self, spot_image: np.ndarray) -> DetectionResult:
        return self.detect_spot(spot_image)
