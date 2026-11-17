import binascii
from pathlib import Path
import struct
import subprocess

import pytest

from packbench.telemetry import FRAME, decode, decode_recording

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def recording():
    subprocess.run(
        ["make", "build/emit_fixture"], cwd=ROOT, check=True, capture_output=True
    )
    return subprocess.check_output([str(ROOT / "build/emit_fixture")])


def fix_crc(packet):
    return packet[:-2] + binascii.crc_hqx(packet[:-2], 0xFFFF).to_bytes(2, "little")


def test_c_encoder_is_decoded_by_independent_python_crc_and_struct(recording):
    samples, t = decode_recording(recording, expected_count=120, first_sequence=0)
    assert len(samples) == 120 and t[-1] == pytest.approx(11.9)
    assert samples[-1].voltage_mv == 3643
    assert samples[0].current_ma == 1000


def test_sequence_and_timer_wrap_and_negative_current(recording):
    data = subprocess.check_output([str(ROOT / "build/emit_fixture"), "wrap"])
    samples, t = decode_recording(data)
    assert t == pytest.approx([0, 0.128, 0.256, 0.384])
    assert samples[2].sequence == 0 and samples[2].tick_ms == 0
    assert all(s.current_ma == -500 for s in samples)


def test_every_single_bit_change_is_rejected(recording):
    packet = recording[: FRAME.size]
    for bit in range(8 * FRAME.size):
        corrupt = bytearray(packet)
        corrupt[bit // 8] ^= 1 << (bit % 8)
        with pytest.raises(ValueError):
            decode(corrupt)


def test_whole_frame_drops_at_recording_edges_need_manifest(recording):
    with pytest.raises(ValueError, match="sample count"):
        decode_recording(recording[: -FRAME.size], expected_count=120)
    with pytest.raises(ValueError, match="start sequence"):
        decode_recording(recording[FRAME.size :], first_sequence=0)


def test_interior_gap_duplicate_and_reordering_are_not_interpolated(recording):
    packets = [
        recording[i : i + FRAME.size] for i in range(0, len(recording), FRAME.size)
    ]
    for samples in (
        packets[:10] + packets[11:],
        packets[:10] + packets[9:],
        packets[:10] + [packets[11], packets[10]] + packets[12:],
    ):
        with pytest.raises(ValueError, match="sequence"):
            decode_recording(b"".join(samples))


def test_crc_valid_but_invalid_fields_rejected(recording):
    for offset, value in ((2, 2), (3, 1), (3, 2)):
        packet = bytearray(recording[: FRAME.size])
        packet[offset] = value
        with pytest.raises(ValueError):
            decode(fix_crc(packet))
    packet = bytearray(recording[: FRAME.size])
    struct.pack_into("<I", packet, 12, 100000)
    with pytest.raises(ValueError, match="sensor range"):
        decode(fix_crc(packet))


def test_truncated_recording_rejected(recording):
    with pytest.raises(ValueError, match="truncated"):
        decode_recording(recording[:-1])
