import pytest
from packbench.pack import screen_pack


def inputs(**overrides):
    return dict(
        series=24,
        parallel=50,
        cell_ocv_v=3.6,
        resistance_ohm=0.08,
        cell_energy_wh=7,
        required_energy_wh=5000,
        load_w=7000,
        **overrides,
    )


def test_constant_power_balance_and_loss():
    p = inputs()
    r = screen_pack(**p)
    terminal = r["loaded_cell_v"] * p["series"]
    assert terminal * r["pack_current_a"] == pytest.approx(p["load_w"])
    assert p["series"] * p["cell_ocv_v"] * r["pack_current_a"] - p[
        "load_w"
    ] == pytest.approx(r["loss_w"])
    assert r["passes"]


def test_impossible_power_and_energy_are_not_silent():
    p = inputs()
    p["load_w"] = 1000000
    r = screen_pack(**p)
    assert not r["passes"] and "operating point" in r["reason"]
    p = inputs()
    p["required_energy_wh"] = 100000
    assert "energy deficit" in screen_pack(**p)["reason"]


def test_current_and_usable_energy_screen():
    p = inputs()
    p["parallel"] = 10
    assert not screen_pack(**p)["passes"]
    p = inputs()
    p["usable_fraction"] = 1.1
    with pytest.raises(ValueError):
        screen_pack(**p)
