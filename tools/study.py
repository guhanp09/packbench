"""Reduce measured cell records and evaluate a model on a separate DST run."""

from dataclasses import asdict
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "packbench-mpl")
)
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from packbench.cell import fit_model, integrate, soc_proxy, validate
from packbench.pack import screen_pack
from fetch_data import main as fetch_data


def frame(archive, suffix, sheet):
    with zipfile.ZipFile(ROOT / "data/raw" / archive) as z:
        names = [n for n in z.namelist() if n.endswith(suffix)]
        if len(names) != 1:
            raise ValueError("Expected exactly one matching source spreadsheet")
        # CALCE's .xls files in this package are actually OOXML, not BIFF.
        return pd.read_excel(
            io.BytesIO(z.read(names[0])), sheet_name=sheet, engine="openpyxl"
        )


def dynamic(suffix):
    f = frame("dst.zip", suffix, "Channel_1-008")
    validate(f["Test_Time(s)"], -f["Current(A)"], f["Voltage(V)"])
    start = np.flatnonzero(f["Step_Index"].to_numpy() == 7)[0]
    f = f.iloc[start:].copy()
    # Predeclare the 2.7 V analysis cutoff. Below-cutoff points remain raw, but
    # are excluded from this voltage-model exercise, including later rebound.
    below = np.flatnonzero(f["Voltage(V)"].to_numpy() < 2.7)
    stop = int(below[0]) if len(below) else len(f)
    excluded = len(f) - stop
    f = f.iloc[:stop]
    return f, excluded


def main():
    fetch_data()
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    capacity = frame("capacity.zip", ".xlsx", "Sheet1")
    validate(capacity["Test_Time(s)"], -capacity["Current(A)"], capacity["Voltage(V)"])
    dis = capacity[capacity.Step_Index == 6]
    reduced = integrate(dis["Test_Time(s)"], -dis["Current(A)"], dis["Voltage(V)"])
    counter_ah = float(dis["Discharge_Capacity(Ah)"].iloc[-1])
    counter_wh = float(dis["Discharge_Energy(Wh)"].iloc[-1])
    # The segment starts at its first sampled current. No extrapolation is
    # inserted to make integrated totals match the cycler's hidden interval.
    reduced.update(
        cycler_discharge_ah=counter_ah,
        cycler_discharge_wh=counter_wh,
        ah_difference_pct=100 * (reduced["discharge_ah"] / counter_ah - 1),
        wh_difference_pct=100 * (reduced["discharge_wh"] / counter_wh - 1),
    )
    train, excluded_train = dynamic("80SOC.xls")
    test, excluded_test = dynamic("50SOC.xls")
    arrays = lambda f: (
        f["Test_Time(s)"].to_numpy(),
        -f["Current(A)"].to_numpy(),
        f["Voltage(V)"].to_numpy(),
    )
    tt, it, vt = arrays(train)
    te, ie, ve = arrays(test)
    baseline = fit_model(tt, it, vt, 0.8, rc=False)
    model = fit_model(tt, it, vt, 0.8, rc=True)
    base_pred = baseline.predict(te, ie, 0.5)
    prediction = model.predict(te, ie, 0.5)
    metrics = {
        "provider": "CALCE",
        "capacity_cell": "SP20-1",
        "model_cell": "SP20-2",
        "training_file": "11_05_2015_SP20-2_DST_80SOC.xls",
        "test_file": "11_05_2015_SP20-2_DST_50SOC.xls",
        "capacity_reduction": reduced,
        "train_samples": len(train),
        "test_samples": len(test),
        "train_below_cutoff_tail_excluded": excluded_train,
        "test_below_cutoff_tail_excluded": excluded_test,
        "one_rc_test_rmse_v": float(np.sqrt(np.mean((prediction - ve) ** 2))),
        "r_only_test_rmse_v": float(np.sqrt(np.mean((base_pred - ve) ** 2))),
        "one_rc_max_abs_test_error_v": float(max(abs(prediction - ve))),
        "parameters": {
            "coefficients": model.coefficients.tolist(),
            "tau_s": model.tau_s,
            "capacity_prior_ah": model.capacity_ah,
        },
    }
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    # A separate design screen. Cell energy comes from SP20-1, resistance from
    # SP20-2. Combining them describes an assumed representative cell, not an
    # identified specimen or a qualified pack.
    mission_wh = 6980 * (60000 / 26 + 300) / 3600 + 350
    pack_rows = [
        screen_pack(
            series=24,
            parallel=n,
            cell_ocv_v=3.6,
            resistance_ohm=float(model.coefficients[4] + model.coefficients[5]),
            cell_energy_wh=reduced["discharge_wh"],
            required_energy_wh=mission_wh,
            load_w=6980,
        )
        for n in range(10, 71, 2)
    ]
    pd.DataFrame(pack_rows).to_csv(out / "pack_sweep.csv", index=False)
    selected = min(
        (r for r in pack_rows if r["passes"]), key=lambda r: r["pack_mass_kg"]
    )
    (out / "pack_screen.json").write_text(
        json.dumps(
            {
                "assumptions": {
                    "series_cells": 24,
                    "ocv_v": 3.6,
                    "usable_fraction": 0.8,
                    "mass_overhead": 0.2,
                    "cell_mass_kg": 0.045,
                    "load_w": 6980,
                    "required_energy_wh": mission_wh,
                    "cell_current_limit_a": 4.0,
                    "loaded_cell_voltage_limit_v": 2.7,
                    "basis": "illustrative combination of two CALCE specimens; no physical pack",
                },
                "lightest_passing_enumerated": selected,
            },
            indent=2,
        )
        + "\n"
    )
    (out / "pack_report.md").write_text(
        f"""# Pack screen

The assumed mission needs {mission_wh:.0f} Wh including its launch allowance and
reserve. The cell test supplied {reduced['discharge_wh']:.3f} Wh per discharge.
At the provider's 45 g cell mass that is {reduced['discharge_wh']/.045:.1f} Wh/kg
at cell level. Adding an assumed 20% mass overhead reduces gross-pack specific
energy to {reduced['discharge_wh']/(.045*1.2):.1f} Wh/kg before the usable-energy fraction.
The earlier Ground Effect Lab example assumed 190 Wh/kg at pack level; this
particular cell/overhead example does not support that assumption.

Among 31 candidates at 24 series cells, the lightest passing screen is
24S{selected['parallel']}P: {selected['cells']} cells,
{selected['pack_mass_kg']:.2f} kg and {selected['usable_energy_wh']:.0f} Wh usable.
At 6.98 kW its modeled cell current is {selected['cell_current_a']:.2f} A,
cell terminal voltage {selected['loaded_cell_v']:.2f} V, and resistive loss
{selected['loss_w']:.0f} W. These are screening outputs, not verified ratings.

The load duration and required energy stay fixed while pack mass changes; this
screen does not re-close aircraft mass/drag. It also ignores cell variation,
temperature, busbars, transient reserve, cooling, contactors, fault currents and
aging. SP20-1 measured energy and SP20-2 fitted resistance are intentionally
identified as two-specimen inputs, not one characterized production cell.
The voltage prediction was tested at CALCE's dynamic current range, not at
every pack-screen current. No pack or motor-drive hardware has been built.
"""
    )
    pd.DataFrame(
        {
            "time_s": te - te[0],
            "current_discharge_a": ie,
            "measured_v": ve,
            "one_rc_v": prediction,
            "r_only_v": base_pred,
        }
    ).to_csv(out / "test_predictions.csv", index=False)
    plt.rcParams.update(
        {"font.size": 10, "axes.spines.top": False, "axes.spines.right": False}
    )
    fig, axes = plt.subplots(3, 1, figsize=(10, 7), sharex=True, layout="constrained")
    t = te - te[0]
    axes[0].plot(t, ve, label="CALCE measurement", color="#243f50", lw=1)
    axes[0].plot(t, prediction, label="one-RC prediction", color="#bc763f", lw=0.8)
    axes[0].set(
        ylabel="Cell voltage [V]",
        title="Separate 50% initial-SOC DST run · parameters fit only on the 80% run",
    )
    axes[0].legend()
    axes[1].plot(t, (prediction - ve) * 1000, color="#bc763f", label="one-RC")
    axes[1].plot(t, (base_pred - ve) * 1000, color="#708992", alpha=0.6, label="R-only")
    axes[1].set(ylabel="Prediction error [mV]")
    axes[1].legend()
    axes[2].plot(t, ie, color="#243f50", lw=0.7)
    axes[2].set(xlabel="Time from DST start [s]", ylabel="Discharge current [A]")
    fig.savefig(out / "cell_model.png", dpi=170)
    plt.close(fig)
    report = f"""# Cell characterization

Measured data: University of Maryland CALCE. No measurements were collected by
this project. The capacity test is SP20-1; voltage-model runs are SP20-2. The
capacity result is not transferred as a measured property of SP20-2.

SP20-1 integrated discharge: {reduced['discharge_ah']:.4f} Ah and
{reduced['discharge_wh']:.4f} Wh. Relative to the cycler counters, differences
are {reduced['ah_difference_pct']:.4f}% and {reduced['wh_difference_pct']:.4f}%.
Integration begins with the first available segment sample; no missing endpoint
is inferred. The full discharge reaches the source experiment's 2.5 V cutoff;
this is a record reduction, not a proposed cell operating limit.

The SP20-2 80% initial-SOC DST run supplies {len(train)} training samples.
The separate 50% run supplies {len(test)} test samples. Both are cut at the first
voltage below 2.7 V; {excluded_train} and {excluded_test} trailing samples are
excluded respectively. All parameter and time-constant selection uses the
training run. The nominal 2 Ah SOC proxy and source-reported starting SOCs are
fixed priors, not estimated truth. Initial RC polarization is zero after rest.

One-RC test voltage RMSE: {metrics['one_rc_test_rmse_v']*1000:.1f} mV.
R-only baseline: {metrics['r_only_test_rmse_v']*1000:.1f} mV.
Largest one-RC absolute test error: {metrics['one_rc_max_abs_test_error_v']*1000:.1f} mV.
Effective fitted R0={model.coefficients[4]*1000:.1f} mΩ,
R1={model.coefficients[5]*1000:.1f} mΩ, tau={model.tau_s:.2f} s.

The cubic quasi-OCV fit and one RC branch are empirical approximations over one
cell's observed range. These are not chemistry identification, equilibrium OCV,
high-rate aircraft validation or lifetime predictions. A lower test error cannot
qualify a pack or justify extrapolation to another temperature or cell type.

See `data/sources.json` for URLs and hashes, `docs/model.md` for equations and
`docs/evidence.md` for the separation of analysis, firmware and physical tests.
"""
    (out / "cell_report.md").write_text(report)
    print(report)


if __name__ == "__main__":
    main()
