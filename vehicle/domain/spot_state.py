from dataclasses import dataclass

from vehicle.settings import SpotRegion


@dataclass
class SpotState:
    spot_id: str
    region: SpotRegion
    occupied: bool = False
    current_plate: str | None = None
