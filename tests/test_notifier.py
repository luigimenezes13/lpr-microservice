import notifier
from notifier import Notifier


class FakeResponse:
    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail

    def raise_for_status(self):
        if self.should_fail:
            raise notifier.requests.HTTPError("bad status")


def test_notifier_sends_all_acl_events(monkeypatch):
    sent_payloads = []

    def fake_post(url, json, timeout):
        sent_payloads.append((url, json, timeout))
        return FakeResponse()

    monkeypatch.setattr(notifier.requests, "post", fake_post)
    monkeypatch.setattr(notifier.settings, "api_base_url", "http://api.test")
    monkeypatch.setattr(notifier.settings, "api_timeout_seconds", 3)

    gateway = Notifier()
    gateway.notify_vehicle_entered()
    gateway.notify_spot_occupied("A", "ABC1D23", 0.87)
    gateway.notify_spot_released("A")
    gateway.notify_vehicle_exited()

    events = [item[1]["event"] for item in sent_payloads]
    urls = [item[0] for item in sent_payloads]

    assert events == [
        "vehicle.entered",
        "spot.occupied",
        "spot.released",
        "vehicle.exited",
    ]
    assert all(url == "http://api.test/events" for url in urls)
    assert sent_payloads[1][1]["spot_id"] == "A"
    assert sent_payloads[1][1]["plate"] == "ABC1D23"
    assert sent_payloads[1][1]["confidence"] == 0.87


def test_notifier_handles_http_failure_without_raising(monkeypatch):
    def fake_post(url, json, timeout):
        return FakeResponse(should_fail=True)

    monkeypatch.setattr(notifier.requests, "post", fake_post)
    gateway = Notifier()

    gateway.notify_vehicle_entered()
