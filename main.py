import logging
import sys

from config import settings
from monitor import ParkingMonitor

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


def main():
    _configure_recognition_logger()
    logger.info("Iniciando LPR Parking Monitor...")
    monitor = ParkingMonitor()
    monitor.start()


if __name__ == "__main__":
    main()
