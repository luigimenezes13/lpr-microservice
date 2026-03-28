from vehicle.domain.parking_monitor import ParkingMonitor


class ProcessCaptureCycle:
    def __init__(self, monitor: ParkingMonitor):
        self._monitor = monitor

    def execute(self):
        self._monitor.process_capture_cycle()
