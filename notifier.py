import logging
from datetime import datetime

import requests

from config import settings

logger = logging.getLogger(__name__)


class Notifier:
    def notify_vehicle_parked(
        self, spot_id: str, plate: str, confidence: float
    ):
        payload = {
            "event": "vehicle_parked",
            "spot_id": spot_id,
            "plate": plate,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
        }
        self._send(payload)

    def notify_vehicle_departed(self, spot_id: str):
        payload = {
            "event": "vehicle_departed",
            "spot_id": spot_id,
            "timestamp": datetime.now().isoformat(),
        }
        self._send(payload)

    def notify_vehicle_parked_without_plate(self, spot_id: str):
        payload = {
            "event": "vehicle_parked",
            "spot_id": spot_id,
            "plate": None,
            "confidence": 0.0,
            "timestamp": datetime.now().isoformat(),
        }
        self._send(payload)

    def _send(self, payload: dict):
        url = f"{settings.api_base_url}/events"
        try:
            response = requests.post(
                url, json=payload, timeout=settings.api_timeout_seconds
            )
            response.raise_for_status()
            logger.info("Evento enviado: %s", payload["event"])
        except requests.RequestException as error:
            logger.error("Falha ao enviar evento: %s", error)
