import logging
import sys

from monitor import ParkingMonitor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def main():
    logger.info("Iniciando LPR Parking Monitor...")
    monitor = ParkingMonitor()
    monitor.start()


if __name__ == "__main__":
    main()
