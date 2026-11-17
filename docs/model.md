# Reduction and model

CALCE current is positive for charge. The importer reverses it once so that
discharge is positive throughout the Python model, telemetry and reported plots.
For each strictly increasing sample interval, trapezoidal integration accumulates
positive and negative current separately. Ah is integral(I dt)/3600; Wh uses V I.
It does not cancel regenerative charge against discharge throughput or infer
unobserved samples. The maximum input gap is reported with the reduction.

## Separate specimens and runs

The initial-capacity file is SP20-1. The two DST files are SP20-2, with nominal
starting SOCs of 80% and 50%. The first file checks integration against the
cycler's capacity/energy counters. The second cell's 80% run supplies every
voltage-model fit and time-constant choice; the 50% run is evaluated afterward.
The voltage model does not use the measured SP20-1 capacity as if it belonged to
SP20-2. Both use a declared 2 Ah nominal capacity prior.

`soc = soc_start - integral(I dt)/(3600 Q_nominal)`

The quasi-open-circuit curve is a cubic polynomial in that proxy SOC. It is fit
under load and is not a separately measured equilibrium OCV curve. The one-RC
model is

```text
v_rc[k] = exp(-dt/tau) v_rc[k-1] + (1-exp(-dt/tau)) I[k-1]
V[k] = b0 + b1 soc + b2 soc² + b3 soc³ - R0 I[k] - R1 v_rc[k]
```

R0 and R1 are constrained to 0–0.5 ohm. A 25-point logarithmic tau grid spans
1–200 s. Each choice is fit by bounded linear least squares on training data;
training MSE selects tau. An R-only baseline is fit separately on the same run.
Neither fit sees the test file. The current is held over each RC update interval.
Modeling stops before the first measurement below 2.7 V, retaining the source
tail in the raw archive but excluding it and later rebound from evaluation.

The worst individual error must be read alongside RMS. Low-SOC knees, current
steps, initial polarization, capacity error and the limited polynomial/RC model
remain sources of error. Two runs from one cell are not cell-to-cell validation.

## Pack screen

The screen combines SP20-1 energy with SP20-2 resistance as an explicitly assumed
representative cell. It fixes a 24-series architecture and enumerates parallel
counts; it does not design busbars, a BMS, cooling or pack construction.

For Ns series, Np parallel, Voc=Ns*Voc_cell and Rpack=Ns*Rcell/Np. The lower-current
constant-power root is `I = 2P/(Voc + sqrt(Voc² - 4 Rpack P))`. No real root is an
infeasible operating point. Separate current, loaded-voltage and usable-energy
screens retain their reasons. Cell mass and pack overhead are explicit inputs.
Mass/mission feedback is deliberately not closed in this screen.

## Data citation

[University of Maryland CALCE battery data](https://calce.umd.edu/data): INR
18650-20R initial-capacity and 25°C DST records. The provider describes the cell,
test profiles and related publication: F. Zheng et al., *Influence of different
open circuit voltage tests on state of charge online estimation for lithium-ion
batteries*, Applied Energy 183 (2016), 513–525. Cite the provider and paper when
using the underlying measurements. The repository's MIT license covers its code,
not a relicensing of CALCE's raw spreadsheets.
