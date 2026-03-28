import logging
from datetime import datetime

import requests

from vehicle.settings import settings

logger = logging.getLogger(__name__)


class EventNotifierHttp:
    def notify_vehicle_entered(self):
        self._send(
            {
                "event": "vehicle.entered",
                "timestamp": datetime.now().isoformat(),
            }
        )

    def notify_vehicle_exited(self):
        self._send(
            {
                "event": "vehicle.exited",
                "timestamp": datetime.now().isoformat(),
            }
        )

    def notify_spot_occupied(
        self,
        spot_id: str,
        plate: str | None,
        confidence: float | None,
    ):
        self._send(
            {
                "event": "spot.occupied",
                "spot_id": spot_id,
                "plate": plate,
                "confidence": confidence if confidence is not None else 0.0,
                "timestamp": datetime.now().isoformat(),
            }
        )

    def notify_spot_released(self, spot_id: str):
        self._send(
            {
                "event": "spot.released",
                "spot_id": spot_id,
                "timestamp": datetime.now().isoformat(),
            }
        )

    def _send(self, payload: dict):
        url = f"{settings.api_base_url}/events"
        try:
            response = requests.post(url, json=payload, timeout=settings.api_timeout_seconds)
            response.raise_for_status()
            logger.info("Evento enviado: %s", payload["event"])
        except requests.RequestException as error:
            logger.error("Falha ao enviar evento: %s", error)
