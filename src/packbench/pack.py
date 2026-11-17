"""Balanced series/parallel pack screen; no hardware protection or qualification."""

import math


def screen_pack(
    *,
    series,
    parallel,
    cell_ocv_v,
    resistance_ohm,
    cell_energy_wh,
    required_energy_wh,
    load_w,
    cell_mass_kg=0.045,
    mass_overhead=0.2,
    usable_fraction=0.8,
    current_limit_a=4.0,
    voltage_limit_v=2.7,
):
    values = (
        cell_ocv_v,
        resistance_ohm,
        cell_energy_wh,
        required_energy_wh,
        load_w,
        cell_mass_kg,
        current_limit_a,
        voltage_limit_v,
    )
    if any(not math.isfinite(x) or x <= 0 for x in values):
        raise ValueError("Positive finite cell, load and energy values required")
    if (
        not isinstance(series, int)
        or not isinstance(parallel, int)
        or min(series, parallel) <= 0
    ):
        raise ValueError("Positive integer series/parallel cell counts required")
    if (
        not 0 < usable_fraction <= 1
        or not math.isfinite(mass_overhead)
        or mass_overhead < 0
    ):
        raise ValueError("Invalid usable fraction or mass overhead")
    count = series * parallel
    open_v = series * cell_ocv_v
    pack_r = series * resistance_ohm / parallel
    disc = open_v * open_v - 4 * pack_r * load_w
    reasons = []
    current = math.nan
    loaded_cell_v = math.nan
    if disc < 0:
        reasons.append("no constant-power operating point")
    else:
        current = 2 * load_w / (open_v + math.sqrt(disc))
        loaded_cell_v = cell_ocv_v - current / parallel * resistance_ohm
        if current / parallel > current_limit_a:
            reasons.append("assumed cell-current limit")
        if loaded_cell_v < voltage_limit_v:
            reasons.append("assumed loaded-cell-voltage limit")
    usable_wh = count * cell_energy_wh * usable_fraction
    if usable_wh < required_energy_wh:
        reasons.append("energy deficit")
    return {
        "series": series,
        "parallel": parallel,
        "cells": count,
        "usable_energy_wh": usable_wh,
        "pack_mass_kg": count * cell_mass_kg * (1 + mass_overhead),
        "pack_current_a": current,
        "cell_current_a": current / parallel,
        "loaded_cell_v": loaded_cell_v,
        "loss_w": current * current * pack_r,
        "passes": not reasons,
        "reason": "; ".join(reasons),
    }
