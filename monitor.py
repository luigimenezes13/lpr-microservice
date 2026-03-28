import logging
import time
import json
from dataclasses import dataclass, field
from datetime import datetime

from camera import Camera, CapturedFrame
from config import settings, SpotRegion
from detector import Detector, DetectionResult
from notifier import Notifier

logger = logging.getLogger(__name__)
recognition_logger = logging.getLogger("lpr.recognition")


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
    vehicle_in_parking: bool = False
    absent_cycles: int = 0

    def __post_init__(self):
        if self.spots:
            return
        self.spots = [
            SpotState(spot_id=spot_id, region=region)
            for spot_id, region in settings.configured_spots()
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
        vehicle_detected_in_frame = self.detector.detect_vehicle_presence(frame.image)
        self._handle_parking_presence(vehicle_detected_in_frame)
        if not vehicle_detected_in_frame and not self.vehicle_in_parking:
            return

        for spot in self.spots:
            spot_image = self._crop_spot(frame, spot.region)
            result = self.detector.detect_spot(spot_image)
            self._log_recognition_heartbeat(spot, result)
            self._handle_detection(spot, result)

    def _crop_spot(self, frame: CapturedFrame, region: SpotRegion):
        return frame.image[
            region.y : region.y + region.height,
            region.x : region.x + region.width,
        ]

    def _handle_detection(self, spot: SpotState, result: DetectionResult):
        was_occupied = spot.occupied

        if result.vehicle_detected and not was_occupied:
            self._on_spot_occupied(spot, result)
            return

        if not result.vehicle_detected and was_occupied:
            self._on_spot_released(spot)

    def _on_spot_occupied(self, spot: SpotState, result: DetectionResult):
        spot.occupied = True
        plate_text = None
        plate_confidence = 0.0

        if result.plate:
            spot.current_plate = result.plate.text
            plate_text = result.plate.text
            plate_confidence = result.plate.confidence
            logger.info(
                "Vaga %s: veiculo estacionou — placa %s (%.0f%%)",
                spot.spot_id,
                result.plate.text,
                result.plate.confidence * 100,
            )
        else:
            spot.current_plate = None
            logger.info(
                "Vaga %s: veiculo estacionou — placa nao reconhecida",
                spot.spot_id,
            )

        self.notifier.notify_spot_occupied(
            spot.spot_id,
            plate_text,
            plate_confidence,
        )

    def _on_spot_released(self, spot: SpotState):
        logger.info("Vaga %s: veiculo saiu (placa era %s)", spot.spot_id, spot.current_plate)
        self.notifier.notify_spot_released(spot.spot_id)
        spot.occupied = False
        spot.current_plate = None

    def _handle_parking_presence(self, vehicle_detected_in_frame: bool):
        if vehicle_detected_in_frame:
            self._handle_vehicle_detected()
            return
        self._handle_vehicle_absence_cycle()

    def _handle_vehicle_detected(self):
        self.absent_cycles = 0
        if self.vehicle_in_parking:
            return
        self.vehicle_in_parking = True
        logger.info("Veiculo entrou no estacionamento")
        self.notifier.notify_vehicle_entered()

    def _handle_vehicle_absence_cycle(self):
        if not self.vehicle_in_parking:
            return

        self.absent_cycles += 1
        if self.absent_cycles < settings.transit_confirmation_cycles:
            return

        self._release_all_occupied_spots()
        self.vehicle_in_parking = False
        self.absent_cycles = 0
        logger.info("Veiculo saiu do estacionamento")
        self.notifier.notify_vehicle_exited()

    def _release_all_occupied_spots(self):
        for spot in self.spots:
            if not spot.occupied:
                continue
            self._on_spot_released(spot)

    def _log_recognition_heartbeat(self, spot: SpotState, result: DetectionResult):
        if not settings.recognition_heartbeat_enabled:
            return

        plate_text = None
        plate_confidence = 0.0

        if result.plate:
            plate_text = result.plate.text
            plate_confidence = result.plate.confidence

        payload = {
            "event": "recognition_heartbeat",
            "timestamp": datetime.now().isoformat(),
            "spot_id": spot.spot_id,
            "vehicle_detected": result.vehicle_detected,
            "plate": plate_text,
            "confidence": plate_confidence,
        }

        recognition_logger.info("%s", json.dumps(payload, ensure_ascii=True))
