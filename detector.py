import logging
from dataclasses import dataclass

import numpy as np
try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

try:
    from paddleocr import PaddleOCR
except ImportError:
    PaddleOCR = None

from config import settings

logger = logging.getLogger(__name__)

VEHICLE_CLASSES = {2, 3, 5, 7}  # car, motorcycle, bus, truck


@dataclass
class PlateReading:
    text: str
    confidence: float


@dataclass
class DetectionResult:
    vehicle_detected: bool
    plate: PlateReading | None


class VehicleDetector:
    def __init__(self):
        if YOLO is None:
            raise RuntimeError("Ultralytics YOLO nao esta instalado no ambiente.")
        self._model = YOLO(settings.vehicle_model_path)
        logger.info("Modelo YOLO carregado: %s", settings.vehicle_model_path)

    def has_vehicle(self, image: np.ndarray) -> bool:
        results = self._model(image, verbose=False)
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                if (
                    class_id in VEHICLE_CLASSES
                    and confidence >= settings.vehicle_confidence_threshold
                ):
                    logger.debug(
                        "Veiculo detectado (class=%d, conf=%.2f)",
                        class_id,
                        confidence,
                    )
                    return True
        return False


class PlateReader:
    def __init__(self):
        if PaddleOCR is None:
            raise RuntimeError("PaddleOCR nao esta instalado no ambiente.")
        self._ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
        logger.info("PaddleOCR inicializado")

    def read_plate(self, image: np.ndarray) -> PlateReading | None:
        results = self._ocr.ocr(image, cls=True)

        if not results or not results[0]:
            return None

        best_text = ""
        best_confidence = 0.0

        for line in results[0]:
            text = line[1][0]
            confidence = line[1][1]

            cleaned = self._clean_plate_text(text)
            if not cleaned:
                continue

            if confidence > best_confidence:
                best_text = cleaned
                best_confidence = confidence

        if not best_text or best_confidence < settings.plate_confidence_threshold:
            return None

        return PlateReading(text=best_text, confidence=best_confidence)

    def _clean_plate_text(self, raw_text: str) -> str:
        cleaned = "".join(char for char in raw_text if char.isalnum())
        cleaned = cleaned.upper()

        if len(cleaned) != 7:
            return ""

        return cleaned


class Detector:
    def __init__(self):
        self._vehicle_detector = VehicleDetector()
        self._plate_reader = PlateReader()

    def detect_vehicle_presence(self, frame_image: np.ndarray) -> bool:
        return self._vehicle_detector.has_vehicle(frame_image)

    def detect_spot(self, spot_image: np.ndarray) -> DetectionResult:
        if not self._vehicle_detector.has_vehicle(spot_image):
            return DetectionResult(vehicle_detected=False, plate=None)

        plate = self._plate_reader.read_plate(spot_image)
        return DetectionResult(vehicle_detected=True, plate=plate)

    def detect(self, spot_image: np.ndarray) -> DetectionResult:
        return self.detect_spot(spot_image)
