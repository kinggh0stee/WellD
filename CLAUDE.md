# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

WellD is an ESP32-C6 battery-powered well-level monitor. Each wakeup it reads a 4–20 mA pressure transducer, a DS18B20 temperature probe, and (optionally) battery voltage, joins a Zigbee HA network as an end device, reports to Zigbee2MQTT, then deep-sleeps. Built with ESP-IDF **v5.3.5** for the RISC-V ESP32-C6.

## Commands

```bash
# First-time target setup
idf.py set-target esp32c6

# Local config (gitignored — copy and edit)
cp sdkconfig.defaults.local.example sdkconfig.defaults.local

# Build / flash / monitor
idf.py build
idf.py -p /dev/ttyUSB0 flash monitor
idf.py menuconfig          # WellD Configuration submenu
idf.py fullclean           # nukes build/ and managed_components/
```

### Tests

Two test layers:

**Host (`test/host/`)** — plain CMake project, plain gcc, runs in CI. Compiles `welld_core.c` and `sensor_pure.c` directly (both are host-clean — no NVS/ADC/log/freertos), links against Unity (fetched via `FetchContent` to `v2.6.0`):

```bash
cmake -S test/host -B test/host/build
cmake --build test/host/build
ctest --test-dir test/host/build --output-on-failure
```

These are the only tests CI actually runs. Add a new test case here whenever you touch a pure helper.

**On-device (`test/<component>/`)** — standalone ESP-IDF projects that pull a single component in via `EXTRA_COMPONENT_DIRS = "../../components/<component>"` (must be the specific component path, not the whole `components/` dir — otherwise ESP-IDF discovers sibling components like `zigbee` and tries to build them outside their managed-dependency context). Cover NVS round-trips and 1-Wire / ADC paths that the host runner can't:

```bash
idf.py -C test/sensor build flash monitor    # runs UNITY_BEGIN()/UNITY_END() over serial
```

CI only **builds** the on-device tests (no QEMU); they need real hardware to run.

Pure functions intended for host testing belong in `components/sensor/sensor_pure.c` or `components/welld_core/welld_core.c` — both translation units must stay free of NVS/ADC/log/freertos calls so they compile on any host. `sensor_pure.c` includes `sdkconfig.h`; the host harness provides a stub at `test/host/stub_sdkconfig/sdkconfig.h` that mirrors the Kconfig defaults — keep it in sync if `components/sensor/Kconfig` defaults change.

## Architecture

### Wake-cycle flow (`main/main.c`)

One `app_main()` = one report. The order matters and is load-bearing:

1. **NVS init** (erase + retry on `NO_FREE_PAGES` / `NEW_VERSION_FOUND`).
2. **Read consecutive-failure counter** from NVS namespace `"welld"`, key `"zb_fails"`. If ≥ `FAIL_THRESHOLD` (5), `nvs_flash_erase()` to drop stale Zigbee network state and force a fresh join. This also resets the sensor offset to the compile-time default — `main.c` logs a warning when that happens.
3. **Read all sensors before starting the radio.** The ADC is sensitive to 802.15.4 RF interference, so `sensor_read_*` calls must precede `zigbee_send`.
4. **`zigbee_send()` blocks** until the radio is idle (success, timeout, or OTA reboot).
5. **Update fail counter** — only on change, since flash has limited write cycles.
6. **`esp_deep_sleep()`** for `CONFIG_WELLD_SLEEP_DURATION_SEC`.

### Components

- `main/` — orchestration only; owns the NVS fail counter.
- `components/sensor/` — ADC + DS18B20 + battery divider. Owns NVS key `"offset_cm"`. `sensor_level_from_mv()` is the pure conversion function exposed in `sensor.h` so tests can hit it without NVS or hardware.
- `components/zigbee/` — esp-zigbee-lib wrapper. Spawns `zb_task` (10 KB stack, prio 5) which runs the BDB commissioning state machine and the stack main loop. Synchronisation back to the caller uses a FreeRTOS event group with `SENT_BIT` / `FAIL_BIT` / `STOPPED_BIT`. The caller must wait for `STOPPED_BIT` before deep-sleep so the radio is fully released.
- `components/esp_log/` — empty shim component (`REQUIRES log`) so other components can write `REQUIRES esp_log` uniformly. Don't delete; some managed components reference it.

### Zigbee endpoints

- EP 1 — Analog Input (water level, metres). Also hosts the Basic cluster and the OTA Upgrade client.
- EP 2 — Analog Input (battery volts). Only registered when `CONFIG_WELLD_BATT_ADC_CHANNEL >= 0`.
- EP 3 — Temperature Measurement (0x0402, int16 × 0.01 °C). `0x8000` is the ZCL "invalid" sentinel.

Reports are unsolicited `zcl_report_attr_cmd_req` to short address `0x0000` (the coordinator). The Z2M external converter (`zigbee2mqtt/welld.js`) translates EP IDs to `water_level` / `battery_voltage` / `battery` / `temperature` keys and computes battery % from `battery_full_mv` / `battery_empty_mv` device options.

### OTA — the version pipeline

The OTA image version is **derived from `PROJECT_VER`** in the root `CMakeLists.txt` at build time:

```
PROJECT_VER = "MAJOR.MINOR.PATCH"  →  OTA_FW_VERSION = 0x00MMmmPP
```

This conversion lives in `components/zigbee/CMakeLists.txt` and is passed as a `-D` compile definition. **To cut a new firmware release, bump `PROJECT_VER` in the root `CMakeLists.txt`** — don't touch `OTA_FW_VERSION` directly.

`OTA_MANUFACTURER_CODE = 0x1234` and `OTA_IMAGE_TYPE = 0x0001` are hardcoded in `components/zigbee/zigbee.c`. Any `.zigbee` OTA file passed to Zigbee2MQTT must be packed with those exact values via `ota_image_create.py` (`--manufacturer-code 0x1234 --image-type 0x0001`); the device rejects mismatched headers. **Do not wildcard these to `0xFFFF`** — they're a security boundary against rogue OTA servers.

The partition table (`partitions.csv`) defines dual 1.5 MB OTA slots (`ota_0` / `ota_1`); `esp_ota_get_next_update_partition(NULL)` always returns the inactive one. `sdkconfig.defaults` pins `CONFIG_ESPTOOLPY_FLASHSIZE_4MB=y` to fit them — don't drop this without resizing partitions.

### Configuration layering

- `sdkconfig.defaults` — **committed**, contains only settings that must hold regardless of local config (flash size, Zigbee role).
- `sdkconfig.defaults.local` — **gitignored**, user-specific overrides (`.example` template at repo root).
- `sdkconfig` — **committed and regenerated** by `menuconfig`. CI uploads its build-time copy as the `dependencies-lock` artifact for diffing. Updates land via PRs (the auto-commit CI step was removed in commit `174a595`).
- `dependencies.lock` — managed component pins, committed.

All WellD options are under `WellD Configuration` (`main/Kconfig.projbuild`); Kconfig ranges defend against bad values from `sdkconfig.defaults.local`.

### Dependency pinning

`components/sensor/idf_component.yml` and `components/zigbee/idf_component.yml` use **exact `==` pins**, not `^`:

```
espressif/esp-zigbee-lib: "==1.6.8"
espressif/esp-zboss-lib:  "==1.6.4"
espressif/onewire_bus:    "==1.1.1"
espressif/ds18b20:        "==0.2.0"
```

These libraries have rough APIs that have churned across point releases (see commits `13a5338`, `776ce6f`, `11991d8`). Bump them one at a time and run a hardware build; expect to fix API renames.

### Failure recovery semantics

- 5 consecutive Zigbee send failures → next boot erases NVS → fresh join. This is the only self-healing path; there is no watchdog re-pair logic inside a single wake cycle.
- DS18B20 missing or out-of-range → temperature omitted from report, retried next wake.
- Pressure-loop current < 3.5 mA → `water_level = -1.0` reported (converter forwards as `null`, HA marks unavailable).
- OTA timeout watchdog (`zb_timeout_alarm`) reschedules itself while `s_ota_in_progress`, but aborts after `OTA_MAX_TIMEOUT_COUNT = 10` reschedules to prevent infinite hang on a stalled download.

## Conventions

- ESP32-C6-specific code (RISC-V, single core + LP core): guard with `CONFIG_IDF_TARGET_ESP32C6`. There is no plan to support other targets — `set-target` is C6 only.
- New tunables go in `main/Kconfig.projbuild` with a `range` clause, and get a documentation row in `README.md` and a commented line in `sdkconfig.defaults.local.example`.
- Component `REQUIRES` lists are minimal and explicit; prefer adding to `REQUIRES` over reaching for transitive includes.
- Log tag convention: one `static const char *TAG` per `.c` file, named for the component (`"main"`, `"sensor"`, `"zigbee"`).

## CI

`.github/workflows/build.yml` has four jobs:

- **ESP-IDF build (esp32c6)** — runs ESP-IDF v5.3.5 in `espressif/esp-idf-ci-action` (SHA-pinned), builds the firmware, uploads `build/*.bin|elf|map` plus `dependencies.lock`.
- **Host unit tests** — plain `ubuntu-latest`, no Docker, no ESP-IDF. Runs the `test/host/` suite (welld_core + sensor pure helpers) via ctest. Fetches Unity at configure time.
- **On-device unit tests (build only)** — builds `test/sensor` and `test/welld_core` for esp32c6 to catch compile breaks. The tests themselves need real hardware to execute.
- **Zigbee2MQTT converter tests** — Node 20, runs `npm test` in `zigbee2mqtt/` against the external converter.
