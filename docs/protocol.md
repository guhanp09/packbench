# Telemetry interface

The fixed-size C core accepts calibrated engineering units from a caller and
produces a 26-byte little-endian frame. It contains no ADC/UART driver, dynamic
allocation, floating-point calculation, actuator output or battery protection.

| Byte offset | Type | Field |
| --- | --- | --- |
| 0 | two bytes | `PB` magic |
| 2 | uint8 | Version, currently 1 |
| 3 | uint8 | Flags: bit 0 invalid sensor/quality, bit 1 invalid sample timing |
| 4 | uint32 | Sequence number, increments modulo 2³² |
| 8 | uint32 | Acquisition tick in milliseconds, modulo 2³² |
| 12 | uint32 | Cell voltage in mV |
| 16 | int32 | Discharge-positive current in mA |
| 20 | int32 | Temperature in milli-degrees Celsius |
| 24 | uint16 | CRC-16/CCITT-FALSE over the preceding 24 bytes |

Transport validation is separate from electrical safety. The diagnostic range
checks are 2–5 V, ±10 A and -20–100°C; they are deliberately broad measurement
sanity bounds, not permitted cell operation limits. Sensor quality must be set
by independently validated acquisition/driver logic.

Intervals must be positive and no longer than 1000 ms. Unsigned subtraction
permits one timer wrap at the expected cadence. A missing 49-day interval cannot
be distinguished from a single wrap by the clock field alone. A session boundary
therefore requires a new recording manifest, not reuse of an old clock epoch.

The Python recording parser rejects CRC errors, unknown versions, flags, invalid
values, truncation, sequence loss/reordering and invalid time. It never interpolates
over them. Complete frame loss at the beginning or end needs the session's
expected start sequence and sample count; those optional checks are tested.
Framing is fixed-length within an established session. Stream resynchronization
and retransmission are not implemented.

`make arm` creates an ARM EABI object for Cortex-M0+. This checks target compilation
of the core, not a linked board image. Actual memory layout, startup, transport,
ADC calibration, isolation and real-time behavior remain integration tasks.
