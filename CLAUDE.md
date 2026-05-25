# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

WellD is an ESP32-C6 battery-powered well-level monitor. Each wakeup it reads a 4–20 mA pressure transducer, a DS18B20 temperature probe, and (optionally) battery voltage, joins a Zigbee HA network as an end device, reports to Zigbee2MQTT, then deep-sleeps. Built with ESP-IDF **v6.0.1** for the RISC-V ESP32-C6.

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

**Host (`test/host/`)** — plain CMake project, plain gcc, runs in CI. Reuses the on-device test sources as-is with `-DHOST_BUILD` (each test file ends with an `#ifdef HOST_BUILD` block that swaps `app_main()` for `int main(void)`). Compiles `welld_core.c` and `sensor_pure.c` (both host-clean — no NVS/ADC/log/freertos), links against Unity (fetched via `FetchContent` to `v2.6.0`):

```bash
cmake -S test/host -B test/host/build
cmake --build test/host/build
ctest --test-dir test/host/build --output-on-failure
```

These are the only tests CI actually runs. Add new test cases to the on-device test files (`test/welld_core/main/test_welld_core.c`, `test/sensor/main/test_sensor.c`) — host and device share the same source. Guard NVS / hardware-only tests with `#ifndef HOST_BUILD`.

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
3. **Read all sensors before starting the radio.** The ADC is sensitive to 802.15.4 RF interference, so `sensor_read_*` calls must precede `zigbee_send`. GPIO5 (VLOOP) must be driven HIGH ≥5 ms before any 4–20 mA read and LOW immediately after. GPIO5 (VLOOP) and GPIO15 (BATT_DIV_EN) must be held LOW through deep-sleep via `esp_sleep_gpio_isolate()`.
4. **Compute rate of change** from RTC-memory history (the previous valid level + cumulative elapsed time across any intervening invalid wakeups). NaN if there's no prior valid reading yet.
5. **`zigbee_send()` blocks** until the radio is idle (success, timeout, or OTA reboot). Receives level / battery / temperature / rate.
6. **Update fail counter** — only on change, since flash has limited write cycles.
7. **Update RTC history** — only when this wakeup's reading was valid (`level_m >= 0`). On an open-loop reading the previous `last_level_m` is kept and `elapsed_since_last_valid_sec` keeps accumulating so the next valid reading spans the full gap.
8. **Pick next sleep duration** via `welld_adaptive_sleep_sec()` when `CONFIG_WELLD_ADAPTIVE_SLEEP_ENABLED` and a rate is available; otherwise fall back to `CONFIG_WELLD_SLEEP_DURATION_SEC`. Stored in `s_history.pending_sleep_sec` so the next wakeup knows how long it slept.
9. **`esp_deep_sleep()`** for the chosen duration.

### Components

- `main/` — orchestration only; owns the NVS fail counter and the RTC-memory level history (`s_history`: `last_level_m`, accumulated `elapsed_since_last_valid_sec`, `pending_sleep_sec`). `RTC_DATA_ATTR` keeps it across deep sleep; cold boot zeroes it (and `valid = false` is the cold-boot signal).
- `components/sensor/` — ADC + DS18B20 + battery divider. Owns NVS keys `"offset_cm"` and `"ds18b20_rom"`. `sensor_level_from_mv()` is the pure conversion function exposed in `sensor.h` so tests can hit it without NVS or hardware. DS18B20 default GPIO is 7 (PCB design). PCB GPIO assignments:

  | GPIO | PCB function |
  |------|---------------|
  | 4 | TP5100 USB charger CE — HIGH enables USB-C charging; isolated before deep-sleep (R37 pulls LOW passively) |
  | 5 | MT3608B VLOOP boost enable — HIGH → 12 V VLOOP active |
  | 6 | Solar charging detect input (CN3722 /CHRG, active-low — LOW = solar charging in progress) |
  | 7 | DS18B20 1-Wire data (default; CONFIG_WELLD_DS18B20_GPIO) |
  | 10 | I2C SDA (ADS1115 only) |
  | 11 | I2C SCL (ADS1115 only) |
  | 12 | ADS1115 ALERT/DRDY (comparator / data-ready output) |
  | 14 | Spare |
  | 15 | Battery divider enable (Q2 gate; pulse HIGH before AIN2 read) |
- `components/zigbee/` — esp-zigbee-lib wrapper. Spawns `zb_task` (10 KB stack, prio 5) which runs the BDB commissioning state machine and the stack main loop. Synchronisation back to the caller uses a FreeRTOS event group with `SENT_BIT` / `FAIL_BIT` / `STOPPED_BIT`. The caller must wait for `STOPPED_BIT` before deep-sleep so the radio is fully released.

### Zigbee endpoints

- EP 1 — Analog Input (water level, metres). Also hosts the Basic cluster and the OTA Upgrade client.
- EP 2 — Analog Input (battery volts). Only registered when `CONFIG_WELLD_BATT_ADC_CHANNEL >= 0`.
- EP 3 — Temperature Measurement (0x0402, int16 × 0.01 °C). `0x8000` is the ZCL "invalid" sentinel.
- EP 4 — Analog Input (level rate of change, cm/h, signed). Always registered (the descriptor has to be stable across wakeups), but **only reported when `s_rate_cm_per_hour` is finite** — `isnan(rate)` means there is no prior valid reading to compare against and we skip the EP4 report frame.

Reports are unsolicited `zcl_report_attr_cmd_req` to short address `0x0000` (the coordinator). The Z2M external converter (`zigbee2mqtt/welld.js`) translates EP IDs to `water_level` / `battery_voltage` / `battery` / `temperature` / `water_level_rate` keys and computes battery % from `battery_full_mv` / `battery_empty_mv` device options.

### OTA — the version pipeline

The OTA image version is **derived from `PROJECT_VER`** in the root `CMakeLists.txt` at build time:

```
PROJECT_VER = "MAJOR.MINOR.PATCH"  →  OTA_FW_VERSION = 0xMMmmPP00
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
espressif/esp-zigbee-lib: "==2.0.1"
espressif/onewire_bus:    "==1.1.1"
espressif/ds18b20:        "==0.3.1"
```

`esp-zboss-lib` was removed as a separate dependency in 2.0.1 — zboss is now bundled inside `esp-zigbee-lib`. These libraries have rough APIs that have churned across point releases (see commits `13a5338`, `776ce6f`, `11991d8`). Bump them one at a time and run a hardware build; expect to fix API renames.

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

## Sub-Agent Routing Rules

Agents live in `.claude/agents/`. Spawn them via the Agent tool when a task cleanly maps to one domain.

## Agent responsibilities summary
- `pcb-engineer`      → `hardware/pcb/`
- `case-engineer`     → `hardware/case/`
- `firmware-engineer` → `main/`, `components/`
- `z2m-converter`     → `zigbee2mqtt/`
- `test-engineer`     → `test/`, runs `zigbee2mqtt/npm test`
- `docs-writer`       → `README.md`, `docs/`
- `ci-engineer`       → `.github/workflows/`
- `senior-reviewer`   → final review gate; reads `hardware/pcb/`, `main/`, `components/`; uses Kimi K2 via opencode MCP; blocks the `/improve` cycle on CRITICAL findings

## Handoff order for hardware changes
PCB agent → firmware agent (pin map) → case agent (dimensions) → test agent → docs agent

## Handoff order for firmware-only changes
Firmware agent → test agent → docs agent

**Parallel** (no shared files — safe to run simultaneously):
- `firmware-engineer` + `test-engineer` + `z2m-converter` + `case-engineer`

**Sequential** (output of one constrains the next):
- `pcb-engineer` → `firmware-engineer` (pin map may change) → `case-engineer` (board dimensions may change)

**PCB agent required outputs** on every invocation:
1. Summary of what changed and why
2. Updated GPIO map (if any pin changed)
3. PCB dimensions (if board outline changed)
4. BOM diff (if components changed)
5. Any constraints `firmware` or `case` agents must know about

**Handoff contract**: when the PCB agent changes a GPIO assignment, the firmware agent must update `components/sensor/sensor.c`, `main/Kconfig.projbuild` defaults, and the GPIO table in this file before any case work begins.

**Hardware sub-agent routing**:
- PCB changes first → outputs GPIO map + dimensions → case and firmware agents consume those outputs
- Case-only changes (no PCB change) → case-engineer runs independently
- Never run PCB and case agents on the same files simultaneously

**`senior-reviewer` runs last** in every `/improve` cycle that touches PCB or firmware. It is a gate, not a contributor — it reads but never writes. If it returns BLOCKED, resolve the CRITICAL items before marking the cycle complete.

## Electrical correctness gate (hardware changes)

**Before any PCB layout work begins after a schematic change**, perform this checklist inline or via the senior-reviewer:

1. **IC companion passives** — every active IC must have all required passive components present in the schematic: feedback dividers (buck/boost), bootstrap caps, decoupling caps, pull-ups on open-drain pins, PG/EN resistors per datasheet.
2. **Net connectivity** — verify `hardware/pcb/schematic_connections.md` reflects any new or changed nets. If wires are missing from a schematic sheet, this document is the authoritative reference.
3. **Voltage ratings** — all component ratings must cover the operating range with ≥20% margin: VBAT 6.0–8.4V, VLOOP 12V, VUSB 5V, +3V3.
4. **CV/CC setpoints** — verify charger output voltage is ≤8.40V for 2S Li-ion (CN3722 CV = 8.31V via R33=590kΩ).
5. **Open-drain pull-ups** — any open-drain signal (ADS_DRDY, I²C) must have an external pull-up resistor; do not rely on internal weak pull-ups alone.

**Why this gate exists**: the Python-generated schematics (pre-2026-05-25) had correct component symbols but zero wire connections and missing critical passives (R_FBH/R_FBL for the AP63205WU feedback divider, R_DRDY for ADS1115 DRDY). These were not caught until the senior reviewer ran on 2026-05-25 (BLOCKED, 4 CRITICAL). The gate prevents tape-out with a schematic that has symbols but no electrical correctness verification.

## CI

`.github/workflows/build.yml` has six jobs:

- **ESP-IDF build (esp32c6)** — runs ESP-IDF v6.0.1 in `espressif/esp-idf-ci-action` (SHA-pinned), builds the firmware, also generates the `.zigbee` OTA image, and uploads `build/*.bin|elf|map|zigbee` plus `dependencies.lock`.
- **C static analysis (cppcheck)** — runs `cppcheck` over all C source files under `components/` and `main/`; fails on any warning, style, performance, or portability finding.
- **Version bump check** — on pull requests only; fails if any `main/` or `components/` source changed without a matching bump to `PROJECT_VER` in `CMakeLists.txt`.
- **Host unit tests** — plain `ubuntu-latest`, no Docker, no ESP-IDF. Runs the `test/host/` suite (welld_core + sensor pure helpers) via ctest. Fetches Unity at configure time.
- **On-device unit tests (build only)** — builds `test/sensor` and `test/welld_core` for esp32c6 to catch compile breaks. The tests themselves need real hardware to execute.
- **Zigbee2MQTT converter tests** — Node 20, runs `npm test` in `zigbee2mqtt/` against the external converter.
