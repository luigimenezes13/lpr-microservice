import base64
import logging
from dataclasses import dataclass

import cv2
import numpy as np

from recognition.domain.detection_result import DetectionResult
from recognition.domain.plate_reading import PlateReading
from recognition.domain.plate_text_normalizer import PlateTextNormalizer
from recognition.settings import settings

logger = logging.getLogger(__name__)

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

try:
    from paddleocr import PaddleOCR
except ImportError:
    PaddleOCR = None

VEHICLE_CLASSES = {2, 3, 5, 7}


def decode_image_base64(image_base64: str) -> np.ndarray:
    raw_bytes = base64.b64decode(image_base64.encode("utf-8"))
    image_array = np.frombuffer(raw_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Imagem invalida no payload base64.")
    return image


@dataclass
class RecognitionModelRuntime:
    _normalizer: PlateTextNormalizer = PlateTextNormalizer()

    def __post_init__(self):
        if YOLO is None:
            raise RuntimeError("Ultralytics YOLO nao esta instalado no ambiente.")
        if PaddleOCR is None:
            raise RuntimeError("PaddleOCR nao esta instalado no ambiente.")

        self._vehicle_model = YOLO(settings.vehicle_model_path)
        self._ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)

    def detect_frame_presence(self, frame_image: np.ndarray) -> tuple[bool, float]:
        results = self._vehicle_model(frame_image, verbose=False)
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                if (
                    class_id in VEHICLE_CLASSES
                    and confidence >= settings.vehicle_confidence_threshold
                ):
                    return True, confidence
        return False, 0.0

    def detect_spot(self, spot_image: np.ndarray) -> DetectionResult:
        vehicle_detected, vehicle_confidence = self.detect_frame_presence(spot_image)
        if not vehicle_detected:
            return DetectionResult(
                vehicle_detected=False,
                plate=None,
                confidence=vehicle_confidence,
            )

        plate = self._read_plate(spot_image)
        return DetectionResult(
            vehicle_detected=True,
            plate=plate,
            confidence=vehicle_confidence,
        )

    def _read_plate(self, image: np.ndarray) -> PlateReading | None:
        results = self._ocr.ocr(image, cls=True)
        if not results or not results[0]:
            return None

        best_text = ""
        best_confidence = 0.0

        for line in results[0]:
            text = line[1][0]
            confidence = float(line[1][1])
            cleaned = self._normalizer.normalize(text)
            if not cleaned:
                continue
            if confidence > best_confidence:
                best_text = cleaned
                best_confidence = confidence

        if not best_text or best_confidence < settings.plate_confidence_threshold:
            return None
        return PlateReading(text=best_text, confidence=best_confidence)
