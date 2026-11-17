/* Host replay fixture, not a hardware capture. Same encoder as the ARM object. */
#include "telemetry.h"
#include <stdio.h>
#include <string.h>

int main(int argc, char **argv) {
    pb_state state = {0};
    if (argc > 1 && strcmp(argv[1], "wrap") == 0) {
        state.sequence = 0xfffffffeu;
        uint32_t times[] = {0xffffff00u, 0xffffff80u, 0u, 0x80u};
        for (unsigned i = 0; i < 4; ++i) {
            uint8_t frame[PB_FRAME_SIZE];
            pb_encode(&state, times[i], 3700u, -500, 25000, 1, frame);
            if (fwrite(frame, 1, PB_FRAME_SIZE, stdout) != PB_FRAME_SIZE) return 1;
        }
    } else {
        for (uint32_t i = 0; i < 120; ++i) {
            uint8_t frame[PB_FRAME_SIZE];
            pb_encode(&state, i * 100u, 4000u-i*3u, 1000, 25000, 1, frame);
            if (fwrite(frame, 1, PB_FRAME_SIZE, stdout) != PB_FRAME_SIZE) return 1;
        }
    }
    return 0;
}
