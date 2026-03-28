from dataclasses import dataclass


@dataclass(frozen=True)
class PlateReading:
    text: str
    confidence: float
