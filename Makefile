PYTHON ?= python3
CC ?= cc
ARM_CC ?= clang
CFLAGS = -std=c11 -O2 -Wall -Wextra -Werror -pedantic

.PHONY: test study arm sanitize evidence
build:
	mkdir -p build
build/emit_fixture: firmware/emit_fixture.c firmware/telemetry.c firmware/telemetry.h | build
	$(CC) $(CFLAGS) firmware/telemetry.c firmware/emit_fixture.c -o $@
build/test_telemetry: firmware/test_telemetry.c firmware/telemetry.c firmware/telemetry.h | build
	$(CC) $(CFLAGS) firmware/telemetry.c firmware/test_telemetry.c -o $@
test: build/test_telemetry build/emit_fixture
	./build/test_telemetry
	$(PYTHON) -m pytest -q
arm: | build
	$(ARM_CC) --target=arm-none-eabi -mcpu=cortex-m0plus -mthumb -ffreestanding -std=c11 -O2 -Wall -Wextra -Werror -pedantic -c firmware/telemetry.c -o build/telemetry-m0.o
	file build/telemetry-m0.o
sanitize: | build
	$(CC) -std=c11 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer firmware/telemetry.c firmware/test_telemetry.c -o build/test_telemetry_san
	./build/test_telemetry_san
study:
	$(PYTHON) tools/study.py
evidence:
	$(PYTHON) tools/evidence.py
