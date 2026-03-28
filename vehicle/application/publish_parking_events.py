from vehicle.infrastructure.event_notifier_http import EventNotifierHttp


class PublishParkingEvents:
    def __init__(self, notifier: EventNotifierHttp):
        self._notifier = notifier

    def notify_vehicle_entered(self):
        self._notifier.notify_vehicle_entered()

    def notify_vehicle_exited(self):
        self._notifier.notify_vehicle_exited()

    def notify_spot_occupied(self, spot_id: str, plate: str | None, confidence: float | None):
        self._notifier.notify_spot_occupied(spot_id, plate, confidence)

    def notify_spot_released(self, spot_id: str):
        self._notifier.notify_spot_released(spot_id)
