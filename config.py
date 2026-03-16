from pydantic_settings import BaseSettings
from pydantic import BaseModel
from typing import Literal


class SpotRegion(BaseModel):
    x: int
    y: int
    width: int
    height: int


class Settings(BaseSettings):
    camera_resolution_width: int = 4056
    camera_resolution_height: int = 3040
    capture_interval_seconds: int = 5

    spot_a: SpotRegion = SpotRegion(x=0, y=0, width=2028, height=3040)
    spot_b: SpotRegion = SpotRegion(x=2028, y=0, width=2028, height=3040)

    vehicle_model_path: str = "yolov8n.pt"
    vehicle_confidence_threshold: float = 0.5

    plate_confidence_threshold: float = 0.6

    api_base_url: str = "http://localhost:8000"
    api_timeout_seconds: int = 10
    recognition_heartbeat_enabled: bool = True
    recognition_log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    model_config = {"env_prefix": "LPR_"}


settings = Settings()
