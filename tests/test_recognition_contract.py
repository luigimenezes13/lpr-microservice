import base64

import cv2
import numpy as np
from fastapi.testclient import TestClient

from recognition.main import create_app


def _dummy_image_payload() -> str:
    image = np.zeros((16, 16, 3), dtype=np.uint8)
    success, encoded = cv2.imencode(".jpg", image)
    assert success is True
    return base64.b64encode(encoded.tobytes()).decode("utf-8")


def test_recognition_endpoints_return_expected_contract():
    class FakeRuntime:
        def detect_frame_presence(self, _image):
            return True, 0.93

        def detect_spot(self, _image):
            from recognition.domain.detection_result import DetectionResult
            from recognition.domain.plate_reading import PlateReading

            return DetectionResult(
                vehicle_detected=True,
                plate=PlateReading(text="ABC1D23", confidence=0.91),
                confidence=0.95,
            )

    app = create_app(runtime=FakeRuntime())
    client = TestClient(app)
    image_base64 = _dummy_image_payload()

    frame_response = client.post(
        "/recognition/frame-presence",
        json={
            "frame_image_base64": image_base64,
            "capture_timestamp": "2026-03-28T00:00:00",
            "camera_id": "cam-a",
        },
    )
    assert frame_response.status_code == 200
    assert frame_response.json()["vehicle_detected"] is True
    assert "model_version" in frame_response.json()
    assert "latency_ms" in frame_response.json()

    spot_response = client.post(
        "/recognition/spot",
        json={
            "spot_id": "A",
            "spot_image_base64": image_base64,
            "capture_timestamp": "2026-03-28T00:00:00",
        },
    )
    assert spot_response.status_code == 200
    assert spot_response.json()["vehicle_detected"] is True
    assert spot_response.json()["plate"] == "ABC1D23"
    assert "model_version" in spot_response.json()
    assert "latency_ms" in spot_response.json()
