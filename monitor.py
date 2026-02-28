import logging
import time
from dataclasses import dataclass, field

from camera import Camera, CapturedFrame
from config import settings, SpotRegion
from detector import Detector, DetectionResult
from notifier import Notifier

logger = logging.getLogger(__name__)


@dataclass
class SpotState:
    spot_id: str
    region: SpotRegion
    occupied: bool = False
    current_plate: str | None = None


@dataclass
class ParkingMonitor:
    camera: Camera = field(default_factory=Camera)
    detector: Detector = field(default_factory=Detector)
    notifier: Notifier = field(default_factory=Notifier)
    spots: list[SpotState] = field(default_factory=list)

    def __post_init__(self):
        self.spots = [
            SpotState(spot_id="A", region=settings.spot_a),
            SpotState(spot_id="B", region=settings.spot_b),
        ]

    def start(self):
        self.camera.start()
        logger.info("Monitor iniciado — %d vagas configuradas", len(self.spots))

        try:
            self._loop()
        except KeyboardInterrupt:
            logger.info("Monitor interrompido pelo usuario")
        finally:
            self.camera.stop()

    def _loop(self):
        while True:
            frame = self.camera.capture()
            self._process_frame(frame)
            time.sleep(settings.capture_interval_seconds)

    def _process_frame(self, frame: CapturedFrame):
        for spot in self.spots:
            spot_image = self._crop_spot(frame, spot.region)
            result = self.detector.detect(spot_image)
            self._handle_detection(spot, result)

    def _crop_spot(self, frame: CapturedFrame, region: SpotRegion):
        return frame.image[
            region.y : region.y + region.height,
            region.x : region.x + region.width,
        ]

    def _handle_detection(self, spot: SpotState, result: DetectionResult):
        was_occupied = spot.occupied

        if result.vehicle_detected and not was_occupied:
            self._on_vehicle_parked(spot, result)
            return

        if not result.vehicle_detected and was_occupied:
            self._on_vehicle_departed(spot)

    def _on_vehicle_parked(self, spot: SpotState, result: DetectionResult):
        spot.occupied = True

        if result.plate:
            spot.current_plate = result.plate.text
            logger.info(
                "Vaga %s: veiculo estacionou — placa %s (%.0f%%)",
                spot.spot_id,
                result.plate.text,
                result.plate.confidence * 100,
            )
            self.notifier.notify_vehicle_parked(
                spot.spot_id, result.plate.text, result.plate.confidence
            )
            return

        spot.current_plate = None
        logger.info(
            "Vaga %s: veiculo estacionou — placa nao reconhecida",
            spot.spot_id,
        )
        self.notifier.notify_vehicle_parked_without_plate(spot.spot_id)

    def _on_vehicle_departed(self, spot: SpotState):
        logger.info("Vaga %s: veiculo saiu (placa era %s)", spot.spot_id, spot.current_plate)
        self.notifier.notify_vehicle_departed(spot.spot_id)
        spot.occupied = False
        spot.current_plate = None
