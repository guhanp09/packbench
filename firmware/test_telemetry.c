#include "telemetry.h"
#include <stdio.h>
#include <stdlib.h>

static void require(int okay, const char *message) {
    if (!okay) { fprintf(stderr, "%s\n", message); exit(1); }
}

int main(void) {
    const uint8_t check[] = "123456789";
    require(pb_crc16(check, 9u) == 0x29b1u, "CRC-16/CCITT-FALSE standard vector");
    pb_state state = {0};
    uint8_t frame[PB_FRAME_SIZE];
    pb_encode(&state, 0xfffffff0u, 3700u, -500, 25000, 1, frame);
    require(frame[3] == 0u, "initial sample");
    pb_encode(&state, 0x10u, 3700u, 500, 25000, 1, frame);
    require(frame[3] == 0u, "timer wrap is valid");
    require(frame[4] == 1u && frame[12] == 0x74u && frame[13] == 0x0eu, "little endian fields");
    pb_encode(&state, 0x10u, 3700u, 0, 25000, 1, frame);
    require((frame[3] & PB_TIME_INVALID) != 0, "duplicate timestamp flagged");
    pb_encode(&state, 0x09u, 3700u, 0, 25000, 1, frame);
    require((frame[3] & PB_TIME_INVALID) != 0, "backwards time flagged");
    pb_encode(&state, 0x2000u, 6000u, 0, 25000, 1, frame);
    require(frame[3] == (PB_SENSOR_INVALID | PB_TIME_INVALID), "time gap and invalid voltage both retained");
    pb_encode(&state, 0x2010u, 3700u, 10001, 25000, 1, frame);
    require(frame[3] == PB_SENSOR_INVALID, "invalid current flagged");
    pb_encode(&state, 0x2020u, 3700u, 0, 100001, 1, frame);
    require(frame[3] == PB_SENSOR_INVALID, "invalid temperature flagged");
    pb_encode(&state, 0x2030u, 3700u, 0, 25000, 0, frame);
    require(frame[3] == PB_SENSOR_INVALID, "sensor quality flagged");
    puts("Telemetry CRC, encoding, input and timer invariants passed");
    return 0;
}
