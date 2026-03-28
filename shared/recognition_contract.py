from pydantic import BaseModel, Field


class FramePresenceRequest(BaseModel):
    frame_image_base64: str
    capture_timestamp: str
    camera_id: str = Field(default="default-camera")


class SpotRecognitionRequest(BaseModel):
    spot_id: str
    spot_image_base64: str
    capture_timestamp: str


class FramePresenceResponse(BaseModel):
    vehicle_detected: bool
    confidence: float
    model_version: str
    latency_ms: int


class SpotRecognitionResponse(BaseModel):
    vehicle_detected: bool
    plate: str | None
    confidence: float | None
    model_version: str
    latency_ms: int
