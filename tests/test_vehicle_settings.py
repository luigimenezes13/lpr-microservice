from vehicle.settings import VehicleSettings


def test_vehicle_settings_default_recognition_url_and_timeout():
    configured = VehicleSettings()

    assert configured.recognition_service_base_url == "http://localhost:9000"
    assert configured.recognition_request_timeout_seconds == 8


def test_vehicle_settings_can_disable_spot_b():
    configured = VehicleSettings(spot_b_enabled=False)
    spots = configured.configured_spots()

    assert len(spots) == 1
    assert spots[0][0] == "A"
