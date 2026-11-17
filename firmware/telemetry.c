#include "telemetry.h"

uint16_t pb_crc16(const uint8_t *data, size_t length) {
    uint16_t crc = 0xffffu;
    for (size_t k = 0; k < length; ++k) {
        crc ^= (uint16_t)data[k] << 8;
        for (unsigned bit = 0; bit < 8; ++bit)
            crc = (uint16_t)((crc & 0x8000u) ? (crc << 1) ^ 0x1021u : crc << 1);
    }
    return crc;
}

static void put32(uint8_t *out, uint32_t value) {
    for (unsigned k = 0; k < 4; ++k) out[k] = (uint8_t)(value >> (8u * k));
}

void pb_encode(pb_state *state, uint32_t now_ms, uint32_t voltage_mv,
               int32_t current_ma, int32_t temperature_mc, int sensor_ok,
               uint8_t out[PB_FRAME_SIZE]) {
    uint8_t flags = 0;
    if (!sensor_ok || voltage_mv < 2000u || voltage_mv > 5000u ||
        current_ma < -10000 || current_ma > 10000 ||
        temperature_mc < -20000 || temperature_mc > 100000)
        flags |= PB_SENSOR_INVALID;
    if (state->started) {
        /* Unsigned subtraction handles the single 32-bit timer wrap. The
         * sample cadence must remain <=1 s; multi-wrap intervals are invalid. */
        const uint32_t elapsed = now_ms - state->previous_ms;
        if (elapsed == 0u || elapsed > 1000u) flags |= PB_TIME_INVALID;
    }
    out[0] = 0x50u; out[1] = 0x42u; out[2] = 1u; out[3] = flags;
    put32(out + 4, state->sequence);
    put32(out + 8, now_ms);
    put32(out + 12, voltage_mv);
    put32(out + 16, (uint32_t)current_ma);
    put32(out + 20, (uint32_t)temperature_mc);
    const uint16_t crc = pb_crc16(out, 24u);
    out[24] = (uint8_t)crc;
    out[25] = (uint8_t)(crc >> 8);
    ++state->sequence;
    state->previous_ms = now_ms;
    state->started = 1u;
}
