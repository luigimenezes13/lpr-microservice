from typing import Literal

from pydantic import BaseModel
from pydantic_settings import BaseSettings


class SpotRegion(BaseModel):
    x: int
    y: int
    width: int
    height: int


class VehicleSettings(BaseSettings):
    camera_resolution_width: int = 4056
    camera_resolution_height: int = 3040
    capture_interval_seconds: int = 5

    spot_a: SpotRegion = SpotRegion(x=0, y=0, width=2028, height=3040)
    spot_b: SpotRegion = SpotRegion(x=2028, y=0, width=2028, height=3040)
    spot_b_enabled: bool = True

    api_base_url: str = "http://localhost:8000"
    api_timeout_seconds: int = 10
    transit_confirmation_cycles: int = 2
    recognition_heartbeat_enabled: bool = True
    recognition_log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = (
        "INFO"
    )
    recognition_service_base_url: str = "http://localhost:9000"
    recognition_request_timeout_seconds: int = 8

    model_config = {"env_prefix": "LPR_"}

    def configured_spots(self) -> list[tuple[str, SpotRegion]]:
        spots = [("A", self.spot_a)]
        if self.spot_b_enabled:
            spots.append(("B", self.spot_b))
        return spots


settings = VehicleSettings()
