import sys
import types

import numpy as np

from camera import Camera
from config import settings


class FakePicamera2:
    def __init__(self):
        self.configured_with = None
        self.started = False
        self.stopped = False

    def create_still_configuration(self, main):
        return {"main": main}

    def configure(self, capture_config):
        self.configured_with = capture_config

    def start(self):
        self.started = True

    def capture_array(self):
        width = settings.camera_resolution_width
        height = settings.camera_resolution_height
        return np.zeros((height, width, 3), dtype=np.uint8)

    def stop(self):
        self.stopped = True


def test_camera_start_capture_and_stop(monkeypatch):
    fake_module = types.SimpleNamespace(Picamera2=FakePicamera2)
    monkeypatch.setitem(sys.modules, "picamera2", fake_module)
    monkeypatch.setattr(settings, "camera_resolution_width", 320)
    monkeypatch.setattr(settings, "camera_resolution_height", 240)

    camera = Camera()
    camera.start()
    captured = camera.capture()
    camera.stop()

    assert captured.width == 320
    assert captured.height == 240
    assert camera._picamera.started is True
    assert camera._picamera.stopped is True
