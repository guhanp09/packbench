import numpy as np
import pytest

from packbench.cell import fit_model, integrate, polarization, soc_proxy, validate


def test_constant_current_energy_and_charge_are_independent_integrals():
    t = np.linspace(0, 3600, 101)
    result = integrate(t, np.full_like(t, 2), np.full_like(t, 3.7))
    assert result["discharge_ah"] == pytest.approx(2)
    assert result["discharge_wh"] == pytest.approx(7.4)
    assert result["charge_ah"] == 0


def test_regeneration_does_not_cancel_discharge_accounting():
    result = integrate([0, 1, 2, 3], [2, 2, -1, -1], [4, 4, 4, 4])
    assert result["discharge_ah"] == pytest.approx(3 / 3600)
    assert result["charge_ah"] == pytest.approx(1.5 / 3600)


def test_rc_step_matches_exponential_and_charge_proxy():
    t = np.arange(0.0, 61)
    i = np.full_like(t, 2)
    assert polarization(t, i, 10) == pytest.approx(2 * (1 - np.exp(-t / 10)))
    assert soc_proxy(t, i, 0.8)[-1] == pytest.approx(0.8 - 2 * 60 / (3600 * 2))


def test_synthetic_identification_predicts_a_separate_profile():
    rng = np.random.default_rng(813)
    t = np.arange(0.0, 4000.0, 2)
    i = np.repeat(rng.uniform(-0.5, 3, 100), 20)
    soc = soc_proxy(t, i, 0.8)
    rc = polarization(t, i, 20)
    v = 3.1 + 1.1 * soc - 0.03 * i - 0.02 * rc
    fitted = fit_model(t, i, v, 0.8)
    test_t = np.arange(0.0, 2000.0, 2)
    test_i = np.repeat(rng.uniform(-0.5, 3, 50), 20)
    test_soc = soc_proxy(test_t, test_i, 0.5)
    test_rc = polarization(test_t, test_i, 20)
    test_v = 3.1 + 1.1 * test_soc - 0.03 * test_i - 0.02 * test_rc
    predicted = fitted.predict(test_t, test_i, 0.5)
    assert np.sqrt(np.mean((predicted - test_v) ** 2)) < 0.002
    assert fitted.coefficients[4] >= 0 and fitted.coefficients[5] >= 0


@pytest.mark.parametrize("time", [[0, 1, 1], [0, 2, 1], [0, float("nan"), 2]])
def test_invalid_time_cannot_be_repaired_silently(time):
    with pytest.raises(ValueError):
        validate(time, [1, 1, 1], [4, 4, 4])
