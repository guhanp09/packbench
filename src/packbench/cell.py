"""Discharge-positive current convention; time in seconds, current in amperes."""

from dataclasses import dataclass
import numpy as np
from scipy.optimize import lsq_linear


def validate(time_s, current_a, voltage_v):
    arrays = tuple(np.asarray(x, dtype=float) for x in (time_s, current_a, voltage_v))
    if (
        any(x.ndim != 1 for x in arrays)
        or len({len(x) for x in arrays}) != 1
        or len(arrays[0]) < 3
    ):
        raise ValueError("At least three paired one-dimensional samples required")
    if any(not np.all(np.isfinite(x)) for x in arrays):
        raise ValueError("Cell measurements must be finite")
    if np.any(np.diff(arrays[0]) <= 0):
        raise ValueError(
            "Time must be strictly increasing; do not sort or interpolate silently"
        )
    return arrays


def integrate(time_s, current_a, voltage_v):
    t, i, v = validate(time_s, current_a, voltage_v)
    dt = np.diff(t)
    discharge = np.maximum(i, 0)
    charge = np.maximum(-i, 0)
    trapezoid = lambda x: float(np.dot((x[1:] + x[:-1]) / 2, dt) / 3600)
    return {
        "discharge_ah": trapezoid(discharge),
        "charge_ah": trapezoid(charge),
        "discharge_wh": trapezoid(discharge * v),
        "charge_wh": trapezoid(charge * v),
        "max_gap_s": float(max(dt)),
    }


def soc_proxy(t, i, initial_soc, capacity_ah=2.0):
    """Nominal-capacity Coulomb-count proxy, not an independently measured SOC."""
    if not np.isfinite(capacity_ah) or capacity_ah <= 0 or not 0 <= initial_soc <= 1:
        raise ValueError("Positive capacity and initial SOC in [0,1] required")
    dq = (i[1:] + i[:-1]) / 2 * np.diff(t) / 3600
    return initial_soc - np.r_[0, np.cumsum(dq)] / capacity_ah


def polarization(t, i, tau_s):
    """RC response to piecewise-constant current; state starts at zero after rest."""
    if not np.isfinite(tau_s) or tau_s <= 0:
        raise ValueError("Time constant must be positive")
    state = np.zeros(len(t))
    for k in range(1, len(t)):
        a = np.exp(-(t[k] - t[k - 1]) / tau_s)
        state[k] = a * state[k - 1] + (1 - a) * i[k - 1]
    return state


def design_matrix(soc, current, rc=None):
    # Polynomial coefficients describe a fitted quasi-OCV curve, not equilibrium
    # electrochemical parameters. Negative current terms enforce voltage sag.
    terms = [np.ones(len(soc)), soc, soc**2, soc**3, -current]
    if rc is not None:
        terms.append(-rc)
    return np.column_stack(terms)


@dataclass(frozen=True)
class VoltageModel:
    coefficients: np.ndarray
    tau_s: float | None
    capacity_ah: float

    def predict(self, time_s, current_a, initial_soc):
        t, i = np.asarray(time_s), np.asarray(current_a)
        soc = soc_proxy(t, i, initial_soc, self.capacity_ah)
        rc = None if self.tau_s is None else polarization(t, i, self.tau_s)
        return design_matrix(soc, i, rc) @ self.coefficients


def fit_model(time_s, current_a, voltage_v, initial_soc, *, rc=True, capacity_ah=2.0):
    t, i, v = validate(time_s, current_a, voltage_v)
    soc = soc_proxy(t, i, initial_soc, capacity_ah)
    candidates = np.geomspace(1, 200, 25) if rc else [None]
    best = None
    for tau in candidates:
        transient = None if tau is None else polarization(t, i, tau)
        x = design_matrix(soc, i, transient)
        lo = [-20] * 4 + [0] * (x.shape[1] - 4)
        hi = [20] * 4 + [0.5] * (x.shape[1] - 4)
        fitted = lsq_linear(x, v, bounds=(lo, hi), tol=1e-10)
        if not fitted.success:
            raise RuntimeError("Voltage-model coefficient fit failed")
        mse = float(np.mean((x @ fitted.x - v) ** 2))
        if best is None or mse < best[0]:
            best = mse, VoltageModel(fitted.x, tau, capacity_ah)
    return best[1]
