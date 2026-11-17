# PackBench execution plan

17 November 2026. Question: can measured cell-test records be turned into a
repeatable energy/voltage study and an auditable telemetry/evidence workflow?

1. Import two public CALCE archives with source URLs and content hashes. Preserve
   the current sign and sheet names; reject invalid time series. Capacity tests
   belong to SP20-1; dynamic profiles belong to SP20-2. Do not merge cell identities.
2. Integrate discharge Ah/Wh and compare with cycler counters. Fit a bounded
   one-RC voltage model on the first part of one dynamic discharge record, then
   evaluate a later contiguous portion without retuning.
3. Implement a fixed-size C telemetry core: explicit byte layout, CRC-16, sequence
   and timestamp handling, calibration validity, monotonic timing and loss flags.
   Exercise the same packet bytes from Python. Compile for Cortex-M0+ as well as
   the host; hardware drivers and real MCU execution remain separate work.
4. Link local engineering requirements to test results and artifacts. Keep open
   hardware, safety and class-review evidence explicitly open. Produce a failure
   log, proposed rig interfaces and a bounded test plan.
5. Review provenance, sign conventions, leakage, missing samples, numeric limits,
   misleading pass counts and unexecuted-work claims. Publish the code/evidence
   and add only executed results to the application resume.

The scope includes analysis of someone else's measured commercial cells. It does
not include cell fabrication, electrolyte/electrode work, pack assembly, sea trials
or approval by a class society.
