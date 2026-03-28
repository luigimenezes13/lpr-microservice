import base64

import numpy as np

from vehicle.infrastructure import recognition_http_gateway
from vehicle.infrastructure.recognition_http_gateway import RecognitionHttpGateway


class FakeHttpResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_detect_frame_presence_sends_contract_payload(monkeypatch):
    sent = {}

    def fake_imencode(_ext, _image):
        return True, np.array([1, 2, 3], dtype=np.uint8)

    def fake_post(url, json, timeout):
        sent["url"] = url
        sent["json"] = json
        sent["timeout"] = timeout
        return FakeHttpResponse(
            {
                "vehicle_detected": True,
                "confidence": 0.91,
                "model_version": "recognition-v1",
                "latency_ms": 12,
            }
        )

    monkeypatch.setattr(recognition_http_gateway.cv2, "imencode", fake_imencode)
    monkeypatch.setattr(recognition_http_gateway.requests, "post", fake_post)
    monkeypatch.setattr(
        recognition_http_gateway.settings,
        "recognition_service_base_url",
        "http://recognition.test:9000",
    )
    monkeypatch.setattr(
        recognition_http_gateway.settings,
        "recognition_request_timeout_seconds",
        5,
    )

    gateway = RecognitionHttpGateway()
    image = np.zeros((10, 10, 3), dtype=np.uint8)
    result = gateway.detect_frame_presence(image)

    assert sent["url"] == "http://recognition.test:9000/recognition/frame-presence"
    assert sent["timeout"] == 5
    assert "frame_image_base64" in sent["json"]
    assert sent["json"]["camera_id"] == "default-camera"
    assert result.vehicle_detected is True
    assert result.confidence == 0.91


def test_detect_spot_sends_spot_id_and_receives_plate(monkeypatch):
    sent = {}

    def fake_imencode(_ext, _image):
        return True, np.array([4, 5, 6], dtype=np.uint8)

    def fake_post(url, json, timeout):
        sent["url"] = url
        sent["json"] = json
        sent["timeout"] = timeout
        return FakeHttpResponse(
            {
                "vehicle_detected": True,
                "plate": "ABC1D23",
                "confidence": 0.97,
                "model_version": "recognition-v1",
                "latency_ms": 21,
            }
        )

    monkeypatch.setattr(recognition_http_gateway.cv2, "imencode", fake_imencode)
    monkeypatch.setattr(recognition_http_gateway.requests, "post", fake_post)
    monkeypatch.setattr(
        recognition_http_gateway.settings,
        "recognition_service_base_url",
        "http://recognition.test:9000",
    )
    monkeypatch.setattr(
        recognition_http_gateway.settings,
        "recognition_request_timeout_seconds",
        7,
    )

    gateway = RecognitionHttpGateway()
    image = np.zeros((12, 12, 3), dtype=np.uint8)
    result = gateway.detect_spot("A", image)

    assert sent["url"] == "http://recognition.test:9000/recognition/spot"
    assert sent["json"]["spot_id"] == "A"
    assert sent["timeout"] == 7
    assert result.vehicle_detected is True
    assert result.plate == "ABC1D23"
    assert result.confidence == 0.97


def test_encode_image_raises_when_imencode_fails(monkeypatch):
    def fake_imencode(_ext, _image):
        return False, None

    monkeypatch.setattr(recognition_http_gateway.cv2, "imencode", fake_imencode)
    image = np.zeros((4, 4, 3), dtype=np.uint8)

    try:
        recognition_http_gateway._encode_image(image)
        assert False, "Era esperado ValueError"
    except ValueError as error:
        assert "Falha ao codificar imagem" in str(error)


def test_encode_image_returns_base64(monkeypatch):
    def fake_imencode(_ext, _image):
        return True, np.array([10, 11, 12], dtype=np.uint8)

    monkeypatch.setattr(recognition_http_gateway.cv2, "imencode", fake_imencode)
    image = np.zeros((3, 3, 3), dtype=np.uint8)
    encoded = recognition_http_gateway._encode_image(image)

    assert isinstance(encoded, str)
    assert base64.b64decode(encoded.encode("utf-8")) == bytes([10, 11, 12])
