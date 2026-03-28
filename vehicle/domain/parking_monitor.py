import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime

from vehicle.domain.parking_state import ParkingState
from vehicle.domain.recognition_gateway import RecognitionGateway
from vehicle.domain.spot_state import SpotState
from vehicle.infrastructure.camera_picamera2 import CapturedFrame, PiCameraGateway
from vehicle.infrastructure.event_notifier_http import EventNotifierHttp
from vehicle.settings import settings

logger = logging.getLogger(__name__)
recognition_logger = logging.getLogger("lpr.recognition")


@dataclass
class ParkingMonitor:
    camera: PiCameraGateway = field(default_factory=PiCameraGateway)
    recognition_gateway: RecognitionGateway | None = None
    notifier: EventNotifierHttp = field(default_factory=EventNotifierHttp)
    spots: list[SpotState] = field(default_factory=list)
    state: ParkingState = field(default_factory=ParkingState)

    def __post_init__(self):
        if not self.spots:
            self.spots = [
                SpotState(spot_id=spot_id, region=region)
                for spot_id, region in settings.configured_spots()
            ]
        if self.recognition_gateway is None:
            from vehicle.infrastructure.recognition_http_gateway import (
                RecognitionHttpGateway,
            )

            self.recognition_gateway = RecognitionHttpGateway()

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
            self.process_capture_cycle()
            time.sleep(settings.capture_interval_seconds)

    def process_capture_cycle(self):
        frame = self.camera.capture()
        self._process_frame(frame)

    def _process_frame(self, frame: CapturedFrame):
        frame_presence = self.recognition_gateway.detect_frame_presence(frame.image)
        self._handle_parking_presence(frame_presence.vehicle_detected)
        if not frame_presence.vehicle_detected and not self.state.vehicle_in_parking:
            return

        for spot in self.spots:
            spot_image = self._crop_spot(frame, spot)
            spot_recognition = self.recognition_gateway.detect_spot(spot.spot_id, spot_image)
            self._log_recognition_heartbeat(spot, spot_recognition)
            self._handle_spot_recognition(spot, spot_recognition)

    def _crop_spot(self, frame: CapturedFrame, spot: SpotState):
        region = spot.region
        return frame.image[
            region.y : region.y + region.height,
            region.x : region.x + region.width,
        ]

    def _handle_spot_recognition(self, spot: SpotState, recognition):
        was_occupied = spot.occupied
        if recognition.vehicle_detected and not was_occupied:
            self._on_spot_occupied(spot, recognition.plate, recognition.confidence)
            return
        if not recognition.vehicle_detected and was_occupied:
            self._on_spot_released(spot)

    def _on_spot_occupied(self, spot: SpotState, plate: str | None, confidence: float | None):
        spot.occupied = True
        spot.current_plate = plate
        self.notifier.notify_spot_occupied(spot.spot_id, plate, confidence)
        if plate:
            logger.info(
                "Vaga %s: veiculo estacionou — placa %s (%.0f%%)",
                spot.spot_id,
                plate,
                (confidence or 0.0) * 100,
            )
            return
        logger.info("Vaga %s: veiculo estacionou — placa nao reconhecida", spot.spot_id)

    def _on_spot_released(self, spot: SpotState):
        logger.info("Vaga %s: veiculo saiu (placa era %s)", spot.spot_id, spot.current_plate)
        self.notifier.notify_spot_released(spot.spot_id)
        spot.occupied = False
        spot.current_plate = None

    def _handle_parking_presence(self, vehicle_detected_in_frame: bool):
        if vehicle_detected_in_frame:
            self.state.absent_cycles = 0
            if self.state.vehicle_in_parking:
                return
            self.state.vehicle_in_parking = True
            logger.info("Veiculo entrou no estacionamento")
            self.notifier.notify_vehicle_entered()
            return

        if not self.state.vehicle_in_parking:
            return
        self.state.absent_cycles += 1
        if self.state.absent_cycles < settings.transit_confirmation_cycles:
            return
        self._release_all_occupied_spots()
        self.state.vehicle_in_parking = False
        self.state.absent_cycles = 0
        logger.info("Veiculo saiu do estacionamento")
        self.notifier.notify_vehicle_exited()

    def _release_all_occupied_spots(self):
        for spot in self.spots:
            if not spot.occupied:
                continue
            self._on_spot_released(spot)

    def _log_recognition_heartbeat(self, spot: SpotState, recognition):
        if not settings.recognition_heartbeat_enabled:
            return
        payload = {
            "event": "recognition_heartbeat",
            "timestamp": datetime.now().isoformat(),
            "spot_id": spot.spot_id,
            "vehicle_detected": recognition.vehicle_detected,
            "plate": recognition.plate,
            "confidence": recognition.confidence or 0.0,
        }
        recognition_logger.info("%s", json.dumps(payload, ensure_ascii=True))
