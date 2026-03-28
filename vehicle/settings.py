from typing import Literal

from pydantic import BaseModel
from pydantic_settings import BaseSettings


class SpotRegion(BaseModel):
    x: int
    y: int
    width: int
    height: int


class VehicleSettings(BaseSettings):
    camera_resolution_width: int = 4608
    camera_resolution_height: int = 2592
    capture_interval_seconds: int = 5

    # Coordenadas calibradas para a vaga unica com base na imagem de referencia
    # (proporcao 16:9, equivalente a captura 4608x2592).
    spot_a: SpotRegion = SpotRegion(x=1350, y=315, width=2790, height=2277)
    spot_b: SpotRegion = SpotRegion(x=2304, y=0, width=2304, height=2592)
    spot_b_enabled: bool = False

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
