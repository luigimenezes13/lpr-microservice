from pydantic_settings import BaseSettings


class RecognitionSettings(BaseSettings):
    vehicle_model_path: str = "recognition/yolov8n.pt"
    vehicle_confidence_threshold: float = 0.5
    plate_confidence_threshold: float = 0.6
    model_version: str = "recognition-v1"

    model_config = {"env_prefix": "RECOGNITION_"}


settings = RecognitionSettings()
