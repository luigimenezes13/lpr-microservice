import numpy as np

import detector
from detector import DetectionResult, Detector
from recognition.domain.detection_result import DetectionResult as RecognitionDetectionResult
from recognition.domain.plate_reading import PlateReading as RecognitionPlateReading

class FakeRuntime:
    def __init__(self):
        self.frame_presence_queue = []
        self.spot_detection_queue = []

    def queue_frame_presence(self, value: tuple[bool, float]):
        self.frame_presence_queue.append(value)

    def queue_spot_detection(self, value):
        self.spot_detection_queue.append(value)

    def detect_frame_presence(self, _image):
        return self.frame_presence_queue.pop(0)

    def detect_spot(self, _image):
        return self.spot_detection_queue.pop(0)


def test_detect_vehicle_presence_true_when_vehicle_is_found(monkeypatch):
    fake_runtime = FakeRuntime()
    fake_runtime.queue_frame_presence((True, 0.91))
    monkeypatch.setattr(detector, "RecognitionModelRuntime", lambda: fake_runtime)

    model = Detector()
    image = np.zeros((50, 50, 3), dtype=np.uint8)

    assert model.detect_vehicle_presence(image) is True


def test_detect_spot_returns_plate_when_vehicle_and_plate_are_valid(monkeypatch):
    fake_runtime = FakeRuntime()
    fake_runtime.queue_spot_detection(
        RecognitionDetectionResult(
            vehicle_detected=True,
            plate=RecognitionPlateReading(
                text="ABC1D23",
                confidence=0.92,
            ),
            confidence=0.88,
        )
    )
    monkeypatch.setattr(detector, "RecognitionModelRuntime", lambda: fake_runtime)

    model = Detector()
    image = np.zeros((50, 50, 3), dtype=np.uint8)
    result = model.detect_spot(image)

    assert result.vehicle_detected is True
    assert result.plate is not None
    assert result.plate.text == "ABC1D23"
    assert result.plate.confidence == 0.92


def test_detect_spot_returns_empty_when_vehicle_not_detected(monkeypatch):
    fake_runtime = FakeRuntime()
    fake_runtime.queue_spot_detection(
        RecognitionDetectionResult(
            vehicle_detected=False,
            plate=None,
            confidence=0.0,
        )
    )
    monkeypatch.setattr(detector, "RecognitionModelRuntime", lambda: fake_runtime)

    model = Detector()
    image = np.zeros((50, 50, 3), dtype=np.uint8)
    result = model.detect_spot(image)

    assert result == DetectionResult(vehicle_detected=False, plate=None)
