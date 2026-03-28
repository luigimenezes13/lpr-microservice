import logging

from fastapi import FastAPI

from recognition.api.routes import build_router
from recognition.application.recognize_frame_presence import RecognizeFramePresence
from recognition.application.recognize_spot import RecognizeSpot
from recognition.infrastructure.model_runtime import RecognitionModelRuntime

logger = logging.getLogger(__name__)


def create_app(runtime: RecognitionModelRuntime | None = None) -> FastAPI:
    runtime = runtime or RecognitionModelRuntime()
    frame_presence_use_case = RecognizeFramePresence(runtime)
    spot_use_case = RecognizeSpot(runtime)

    app = FastAPI(title="LPR Recognition Service", version="1.0.0")
    app.include_router(build_router(frame_presence_use_case, spot_use_case))
    return app


def get_app() -> FastAPI:
    return create_app()
