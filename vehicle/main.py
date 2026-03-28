import logging
import sys

from fastapi import FastAPI

from vehicle.api.routes import build_router
from vehicle.application.process_capture_cycle import ProcessCaptureCycle
from vehicle.domain.parking_monitor import ParkingMonitor
from vehicle.settings import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def _configure_recognition_logger():
    recognition_logger = logging.getLogger("lpr.recognition")
    configured_level = getattr(logging, settings.recognition_log_level, logging.INFO)
    recognition_logger.setLevel(configured_level)


def create_app() -> FastAPI:
    _configure_recognition_logger()
    monitor = ParkingMonitor()
    process_capture_cycle = ProcessCaptureCycle(monitor)

    app = FastAPI(title="LPR Vehicle Service", version="1.0.0")
    app.include_router(build_router(process_capture_cycle))
    return app


app = create_app()


def run_monitor_forever():
    _configure_recognition_logger()
    logger.info("Iniciando Vehicle Monitor (modo continuo)...")
    ParkingMonitor().start()
