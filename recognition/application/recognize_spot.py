import time

from recognition.infrastructure.model_runtime import (
    RecognitionModelRuntime,
    decode_image_base64,
)
from recognition.settings import settings
from shared.recognition_contract import SpotRecognitionRequest, SpotRecognitionResponse


class RecognizeSpot:
    def __init__(self, runtime: RecognitionModelRuntime):
        self._runtime = runtime

    def execute(self, request: SpotRecognitionRequest) -> SpotRecognitionResponse:
        started_at = time.perf_counter()
        image = decode_image_base64(request.spot_image_base64)
        detection = self._runtime.detect_spot(image)
        latency_ms = int((time.perf_counter() - started_at) * 1000)
        return SpotRecognitionResponse(
            vehicle_detected=detection.vehicle_detected,
            plate=detection.plate.text if detection.plate else None,
            confidence=detection.plate.confidence if detection.plate else None,
            model_version=settings.model_version,
            latency_ms=latency_ms,
        )
