import base64
from datetime import datetime

import cv2
import numpy as np
import requests

from shared.recognition_contract import (
    FramePresenceRequest,
    FramePresenceResponse,
    SpotRecognitionRequest,
    SpotRecognitionResponse,
)
from vehicle.domain.recognition_gateway import FramePresence, RecognitionGateway, SpotRecognition
from vehicle.settings import settings


class RecognitionHttpGateway(RecognitionGateway):
    def __init__(self):
        self._base_url = settings.recognition_service_base_url.rstrip("/")
        self._timeout = settings.recognition_request_timeout_seconds

    def detect_frame_presence(self, frame_image: np.ndarray) -> FramePresence:
        payload = FramePresenceRequest(
            frame_image_base64=_encode_image(frame_image),
            capture_timestamp=datetime.now().isoformat(),
        )
        response = requests.post(
            f"{self._base_url}/recognition/frame-presence",
            json=payload.model_dump(),
            timeout=self._timeout,
        )
        response.raise_for_status()
        body = FramePresenceResponse.model_validate(response.json())
        return FramePresence(
            vehicle_detected=body.vehicle_detected,
            confidence=body.confidence,
        )

    def detect_spot(self, spot_id: str, spot_image: np.ndarray) -> SpotRecognition:
        payload = SpotRecognitionRequest(
            spot_id=spot_id,
            spot_image_base64=_encode_image(spot_image),
            capture_timestamp=datetime.now().isoformat(),
        )
        response = requests.post(
            f"{self._base_url}/recognition/spot",
            json=payload.model_dump(),
            timeout=self._timeout,
        )
        response.raise_for_status()
        body = SpotRecognitionResponse.model_validate(response.json())
        return SpotRecognition(
            vehicle_detected=body.vehicle_detected,
            plate=body.plate,
            confidence=body.confidence,
        )


def _encode_image(image: np.ndarray) -> str:
    success, encoded = cv2.imencode(".jpg", image)
    if not success:
        raise ValueError("Falha ao codificar imagem para JPEG.")
    return base64.b64encode(encoded.tobytes()).decode("utf-8")
