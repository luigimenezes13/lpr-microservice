from config import Settings


def test_configured_spots_with_two_spots_enabled():
    settings = Settings(spot_b_enabled=True)

    configured_spots = settings.configured_spots()

    assert len(configured_spots) == 2
    assert configured_spots[0][0] == "A"
    assert configured_spots[1][0] == "B"


def test_configured_spots_with_single_spot():
    settings = Settings(spot_b_enabled=False)

    configured_spots = settings.configured_spots()

    assert len(configured_spots) == 1
    assert configured_spots[0][0] == "A"


def test_transit_confirmation_cycles_default_and_override():
    default_settings = Settings()
    overridden_settings = Settings(transit_confirmation_cycles=4)

    assert default_settings.transit_confirmation_cycles == 2
    assert overridden_settings.transit_confirmation_cycles == 4
