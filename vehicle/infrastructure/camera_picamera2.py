import logging
from dataclasses import dataclass

import numpy as np

from vehicle.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class CapturedFrame:
    image: np.ndarray
    width: int
    height: int


class PiCameraGateway:
    def __init__(self):
        self._picamera = None

    def start(self):
        from picamera2 import Picamera2

        self._picamera = Picamera2()
        capture_config = self._picamera.create_still_configuration(
            main={
                "size": (
                    settings.camera_resolution_width,
                    settings.camera_resolution_height,
                ),
                "format": "RGB888",
            }
        )
        self._picamera.configure(capture_config)
        self._picamera.start()
        logger.info(
            "Camera iniciada (%dx%d)",
            settings.camera_resolution_width,
            settings.camera_resolution_height,
        )

    def capture(self) -> CapturedFrame:
        image = self._picamera.capture_array()
        height, width = image.shape[:2]
        return CapturedFrame(image=image, width=width, height=height)

    def stop(self):
        if self._picamera:
            self._picamera.stop()
            logger.info("Camera parada")
