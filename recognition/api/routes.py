from fastapi import APIRouter

from recognition.application.recognize_frame_presence import RecognizeFramePresence
from recognition.application.recognize_spot import RecognizeSpot
from shared.recognition_contract import (
    FramePresenceRequest,
    FramePresenceResponse,
    SpotRecognitionRequest,
    SpotRecognitionResponse,
)


def build_router(
    frame_presence_use_case: RecognizeFramePresence,
    recognize_spot_use_case: RecognizeSpot,
) -> APIRouter:
    router = APIRouter()

    @router.get("/health")
    def healthcheck():
        return {"status": "ok", "service": "recognition"}

    @router.post(
        "/recognition/frame-presence",
        response_model=FramePresenceResponse,
    )
    def recognize_frame_presence(request: FramePresenceRequest) -> FramePresenceResponse:
        return frame_presence_use_case.execute(request)

    @router.post(
        "/recognition/spot",
        response_model=SpotRecognitionResponse,
    )
    def recognize_spot(request: SpotRecognitionRequest) -> SpotRecognitionResponse:
        return recognize_spot_use_case.execute(request)

    return router
