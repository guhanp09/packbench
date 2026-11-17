#ifndef PACKBENCH_TELEMETRY_H
#define PACKBENCH_TELEMETRY_H

#include <stdint.h>
#include <stddef.h>

#define PB_FRAME_SIZE 26u
#define PB_SENSOR_INVALID 1u
#define PB_TIME_INVALID 2u

typedef struct {
    uint32_t sequence;
    uint32_t previous_ms;
    uint8_t started;
} pb_state;

/* Passive telemetry only. The caller owns sensor drivers, calibration,
 * independent electrical protection and timestamp acquisition. No actuator or
 * charge/discharge command is emitted by this code. */
uint16_t pb_crc16(const uint8_t *data, size_t length);
void pb_encode(pb_state *state, uint32_t now_ms, uint32_t voltage_mv,
               int32_t current_ma, int32_t temperature_mc, int sensor_ok,
               uint8_t out[PB_FRAME_SIZE]);

#endif
