import numpy as np

import detector
from detector import DetectionResult, Detector


class FakeBox:
    def __init__(self, class_id: int, confidence: float):
        self.cls = [class_id]
        self.conf = [confidence]


class FakeYoloResult:
    def __init__(self, boxes):
        self.boxes = boxes


class FakeYOLO:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.calls = []
        self.next_results = []

    def queue_results(self, results):
        self.next_results.append(results)

    def __call__(self, image, verbose=False):
        self.calls.append((image.shape, verbose))
        return self.next_results.pop(0)


class FakePaddleOCR:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.next_results = []

    def queue_results(self, results):
        self.next_results.append(results)

    def ocr(self, image, cls=True):
        return self.next_results.pop(0)


def test_detect_vehicle_presence_true_when_vehicle_is_found(monkeypatch):
    fake_yolo = FakeYOLO("fake.pt")
    fake_yolo.queue_results([FakeYoloResult([FakeBox(2, 0.91)])])
    fake_ocr = FakePaddleOCR()

    monkeypatch.setattr(detector, "YOLO", lambda _: fake_yolo)
    monkeypatch.setattr(detector, "PaddleOCR", lambda **_: fake_ocr)
    monkeypatch.setattr(detector.settings, "vehicle_confidence_threshold", 0.5)

    model = Detector()
    image = np.zeros((50, 50, 3), dtype=np.uint8)

    assert model.detect_vehicle_presence(image) is True


def test_detect_spot_returns_plate_when_vehicle_and_plate_are_valid(monkeypatch):
    fake_yolo = FakeYOLO("fake.pt")
    fake_yolo.queue_results([FakeYoloResult([FakeBox(2, 0.88)])])
    fake_ocr = FakePaddleOCR()
    fake_ocr.queue_results(
        [[[[0, 0], ("ABC1D23", 0.92)]]]
    )

    monkeypatch.setattr(detector, "YOLO", lambda _: fake_yolo)
    monkeypatch.setattr(detector, "PaddleOCR", lambda **_: fake_ocr)
    monkeypatch.setattr(detector.settings, "vehicle_confidence_threshold", 0.5)
    monkeypatch.setattr(detector.settings, "plate_confidence_threshold", 0.6)

    model = Detector()
    image = np.zeros((50, 50, 3), dtype=np.uint8)
    result = model.detect_spot(image)

    assert result.vehicle_detected is True
    assert result.plate is not None
    assert result.plate.text == "ABC1D23"
    assert result.plate.confidence == 0.92


def test_detect_spot_returns_empty_when_vehicle_not_detected(monkeypatch):
    fake_yolo = FakeYOLO("fake.pt")
    fake_yolo.queue_results([FakeYoloResult([FakeBox(0, 0.99)])])
    fake_ocr = FakePaddleOCR()

    monkeypatch.setattr(detector, "YOLO", lambda _: fake_yolo)
    monkeypatch.setattr(detector, "PaddleOCR", lambda **_: fake_ocr)
    monkeypatch.setattr(detector.settings, "vehicle_confidence_threshold", 0.5)

    model = Detector()
    image = np.zeros((50, 50, 3), dtype=np.uint8)
    result = model.detect_spot(image)

    assert result == DetectionResult(vehicle_detected=False, plate=None)
