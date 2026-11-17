"""Decode exactly specified C packet bytes; gaps are errors, not interpolated data."""

import binascii
import struct
from dataclasses import dataclass

FRAME = struct.Struct("<2sBBIIIiiH")


@dataclass(frozen=True)
class Sample:
    sequence: int
    tick_ms: int
    voltage_mv: int
    current_ma: int
    temperature_mc: int


def decode(packet):
    if len(packet) != FRAME.size:
        raise ValueError("packet length")
    if binascii.crc_hqx(packet[:-2], 0xFFFF) != int.from_bytes(packet[-2:], "little"):
        raise ValueError("CRC mismatch")
    magic, version, flags, sequence, tick, voltage, current, temperature, _ = (
        FRAME.unpack(packet)
    )
    if magic != b"PB" or version != 1:
        raise ValueError("unknown protocol")
    if flags:
        raise ValueError(f"invalid acquisition flags {flags}")
    if not (
        2000 <= voltage <= 5000
        and -10000 <= current <= 10000
        and -20000 <= temperature <= 100000
    ):
        raise ValueError("sensor range")
    return Sample(sequence, tick, voltage, current, temperature)


def decode_recording(data, *, expected_count=None, first_sequence=None):
    if len(data) == 0 or len(data) % FRAME.size:
        raise ValueError("truncated or empty recording")
    samples = [
        decode(data[i : i + FRAME.size]) for i in range(0, len(data), FRAME.size)
    ]
    if expected_count is not None and len(samples) != expected_count:
        raise ValueError("recording sample count")
    if first_sequence is not None and samples[0].sequence != first_sequence:
        raise ValueError("recording start sequence")
    elapsed = [0]
    for a, b in zip(samples, samples[1:]):
        if (b.sequence - a.sequence) & 0xFFFFFFFF != 1:
            raise ValueError("sequence gap or reordering")
        dt = (b.tick_ms - a.tick_ms) & 0xFFFFFFFF
        if not 0 < dt <= 1000:
            raise ValueError("timestamp gap or reordering")
        elapsed.append(elapsed[-1] + dt)
    return samples, [x / 1000 for x in elapsed]
