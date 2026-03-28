import time

from recognition.infrastructure.model_runtime import (
    RecognitionModelRuntime,
    decode_image_base64,
)
from recognition.settings import settings
from shared.recognition_contract import FramePresenceRequest, FramePresenceResponse


class RecognizeFramePresence:
    def __init__(self, runtime: RecognitionModelRuntime):
        self._runtime = runtime

    def execute(self, request: FramePresenceRequest) -> FramePresenceResponse:
        started_at = time.perf_counter()
        image = decode_image_base64(request.frame_image_base64)
        vehicle_detected, confidence = self._runtime.detect_frame_presence(image)
        latency_ms = int((time.perf_counter() - started_at) * 1000)
        return FramePresenceResponse(
            vehicle_detected=vehicle_detected,
            confidence=confidence,
            model_version=settings.model_version,
            latency_ms=latency_ms,
        )
