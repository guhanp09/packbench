# Evidence register and review scope

`make evidence` executes the numerical/packet tests, host sanitizers, target
compilation and data study. It stops on any failed command, writes the exact logs
and records hashes. `results/requirements.csv` links local requirements to those
artifacts while keeping unexecuted physical requirements open.

This register is a documentation exercise for a passive cell-test analysis and
telemetry subsystem. It does not establish safety of an electric craft, an
approved battery pack or compliance with a class society's requirements.

## Relation to WIG safety documentation

[IMO MSC.1/Circ.1592](https://wwwcdn.imo.org/localresources/en/OurWork/Safety/Documents/MSC.1-CIRC.1592.pdf),
Part C chapter 2, describes safety assessment across requirements, implementation
and verification. That distinction motivates the register's status fields and
failure records. This repository neither selects a class-society approval basis
nor assigns regulatory hazard probabilities. Craft-level operation and the
demonstrations discussed in Part B chapter 16 require different evidence.

| Failure / effect | Current evidence | Open work |
| --- | --- | --- |
| Corrupted measurement could distort energy results | CRC and independent decoder; all single-bit packet changes rejected | Transport-level fault rate and resynchronization |
| Missing/reordered samples could hide load transients | Sequence, timestamp and session count checks | Actual DAQ buffering and sustained transport tests |
| Biased calibration can pass every packet check | Known unresolved limitation | Calibrated reference measurements and uncertainty budget |
| Cell voltage model understates low-SOC sag | Separate-run test retains 310 mV maximum error | More cells, temperatures, aging and pulse regimes |
| Thermal/electrical faults damage a physical setup | No physical evidence in this project | Qualified test equipment, independent protection, qualified lab procedures |
| A model or firmware change invalidates prior results | Source, raw-input and artifact hashes | Configuration control of real instruments and hardware revisions |

## Review before use

Read source provenance, specimen identity, current sign, missing-data policy,
model limits and calibration assumptions before interpreting a result. Any
physical deployment needs independent design review, sensor calibration, target
timing, electrical isolation, protection and failure testing. Those items remain
open and cannot be replaced by a software test pass.
