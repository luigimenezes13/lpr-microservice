from dataclasses import dataclass

from recognition.domain.plate_reading import PlateReading


@dataclass(frozen=True)
class DetectionResult:
    vehicle_detected: bool
    plate: PlateReading | None
    confidence: float
