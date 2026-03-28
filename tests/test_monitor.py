import numpy as np

from camera import CapturedFrame
from config import SpotRegion, settings
from detector import DetectionResult, PlateReading
from monitor import ParkingMonitor, SpotState


class StubDetector:
    def __init__(self, frame_presence_sequence, spot_sequence):
        self._frame_presence_sequence = list(frame_presence_sequence)
        self._spot_sequence = list(spot_sequence)

    def detect_vehicle_presence(self, frame_image):
        return self._frame_presence_sequence.pop(0)

    def detect_spot(self, spot_image):
        return self._spot_sequence.pop(0)


class StubNotifier:
    def __init__(self):
        self.events = []

    def notify_vehicle_entered(self):
        self.events.append("vehicle.entered")

    def notify_vehicle_exited(self):
        self.events.append("vehicle.exited")

    def notify_spot_occupied(self, spot_id, plate, confidence):
        self.events.append(f"spot.occupied:{spot_id}")

    def notify_spot_released(self, spot_id):
        self.events.append(f"spot.released:{spot_id}")


def build_frame():
    image = np.zeros((200, 200, 3), dtype=np.uint8)
    return CapturedFrame(image=image, width=200, height=200)


def build_spot(spot_id: str, x: int):
    return SpotState(
        spot_id=spot_id,
        region=SpotRegion(x=x, y=0, width=100, height=100),
    )


def test_monitor_happy_path_entered_occupied_released_exited(monkeypatch):
    monkeypatch.setattr(settings, "transit_confirmation_cycles", 2)
    detector = StubDetector(
        frame_presence_sequence=[True, True, True, False, False],
        spot_sequence=[
            DetectionResult(vehicle_detected=False, plate=None),
            DetectionResult(
                vehicle_detected=True,
                plate=PlateReading(text="ABC1D23", confidence=0.9),
            ),
            DetectionResult(vehicle_detected=False, plate=None),
            DetectionResult(vehicle_detected=False, plate=None),
        ],
    )
    notifier = StubNotifier()
    monitor = ParkingMonitor(
        detector=detector,
        notifier=notifier,
        spots=[build_spot("A", 0)],
    )

    for _ in range(5):
        monitor._process_frame(build_frame())

    assert notifier.events == [
        "vehicle.entered",
        "spot.occupied:A",
        "spot.released:A",
        "vehicle.exited",
    ]


def test_monitor_vehicle_enters_and_exits_without_occupying(monkeypatch):
    monkeypatch.setattr(settings, "transit_confirmation_cycles", 2)
    detector = StubDetector(
        frame_presence_sequence=[True, False, False],
        spot_sequence=[
            DetectionResult(vehicle_detected=False, plate=None),
            DetectionResult(vehicle_detected=False, plate=None),
        ],
    )
    notifier = StubNotifier()
    monitor = ParkingMonitor(
        detector=detector,
        notifier=notifier,
        spots=[build_spot("A", 0)],
    )

    for _ in range(3):
        monitor._process_frame(build_frame())

    assert notifier.events == ["vehicle.entered", "vehicle.exited"]


def test_monitor_two_spots_with_transition_and_coherent_order(monkeypatch):
    monkeypatch.setattr(settings, "transit_confirmation_cycles", 2)
    detector = StubDetector(
        frame_presence_sequence=[True, True, True, False, False],
        spot_sequence=[
            DetectionResult(vehicle_detected=False, plate=None),
            DetectionResult(vehicle_detected=False, plate=None),
            DetectionResult(vehicle_detected=True, plate=None),
            DetectionResult(vehicle_detected=False, plate=None),
            DetectionResult(vehicle_detected=False, plate=None),
            DetectionResult(vehicle_detected=True, plate=None),
            DetectionResult(vehicle_detected=False, plate=None),
            DetectionResult(vehicle_detected=False, plate=None),
        ],
    )
    notifier = StubNotifier()
    monitor = ParkingMonitor(
        detector=detector,
        notifier=notifier,
        spots=[build_spot("A", 0), build_spot("B", 100)],
    )

    for _ in range(5):
        monitor._process_frame(build_frame())

    assert notifier.events == [
        "vehicle.entered",
        "spot.occupied:A",
        "spot.released:A",
        "spot.occupied:B",
        "spot.released:B",
        "vehicle.exited",
    ]
