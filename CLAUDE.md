# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

WellD is an ESP32-C6 battery-powered well-level monitor. Each wakeup it reads a 4–20 mA pressure transducer and battery divider through an ADS1115 I²C ADC, reads a DS18B20 temperature probe, joins a Zigbee HA network as an end device, reports to Zigbee2MQTT, then deep-sleeps. Built with ESP-IDF **v6.0.1** for the RISC-V ESP32-C6.

## Commands

```bash
# First-time target setup
idf.py set-target esp32c6

# Local config (gitignored — copy and edit)
cp sdkconfig.defaults.local.example sdkconfig.defaults.local

# Build / flash / monitor
idf.py build
idf.py -p /dev/ttyUSB0 flash monitor
idf.py menuconfig          # WellD Configuration / WellD Sensor / WellD Zigbee submenus
idf.py fullclean           # nukes build/ and managed_components/
```

### Tests

Three test layers:

**Host (`test/host/`)** — plain CMake project, plain gcc, runs in CI. Reuses the on-device test sources as-is with `-DHOST_BUILD` (each test file ends with an `#ifdef HOST_BUILD` block that swaps `app_main()` for `int main(void)`). Compiles `welld_core.c` and `sensor_pure.c` (both host-clean — no NVS/ADC/log/freertos), links against Unity (fetched via `FetchContent` to `v2.6.0`):

```bash
cmake -S test/host -B test/host/build
cmake --build test/host/build
ctest --test-dir test/host/build --output-on-failure
```

These are the only firmware tests CI actually runs. Add new test cases to the on-device test files (`test/welld_core/main/test_welld_core.c`, `test/sensor/main/test_sensor.c`) — host and device share the same source. Guard NVS / hardware-only tests with `#ifndef HOST_BUILD`.

**On-device (`test/<component>/`)** — standalone ESP-IDF projects that pull a single component in via `EXTRA_COMPONENT_DIRS = "../../components/<component>"` (must be the specific component path, not the whole `components/` dir — otherwise ESP-IDF discovers sibling components like `zigbee` and tries to build them outside their managed-dependency context). Cover NVS round-trips and 1-Wire / I²C paths that the host runner can't:

```bash
idf.py -C test/sensor build flash monitor       # runs UNITY_BEGIN()/UNITY_END() over serial
idf.py -C test/welld_core build flash monitor
```

CI only **builds** the on-device tests (no QEMU); they need real hardware to run.

**Z2M converter (`zigbee2mqtt/test/`)** — Node's built-in test runner against the pure conversion logic in `zigbee2mqtt/lib/welld_convert.js`:

```bash
cd zigbee2mqtt && npm ci && npm test
```

Pure functions intended for host testing belong in `components/sensor/sensor_pure.c` or `components/welld_core/welld_core.c` — both translation units must stay free of NVS/ADC/log/freertos calls so they compile on any host. `sensor_pure.c` includes `sdkconfig.h`; the host harness provides a stub at `test/host/stub_sdkconfig/sdkconfig.h` that mirrors the Kconfig defaults — keep it in sync if `components/sensor/Kconfig` defaults change.

## Architecture

### Wake-cycle flow (`main/main.c`)

One `app_main()` = one report. The order matters and is load-bearing:

1. **RTC event log + boot reason** — a 16-entry RTC-memory ring buffer records structured events (boot, send, fail, OTA, brownout, watchdog…). Printing on wakeup is gated behind `CONFIG_WELLD_RTC_LOG_PRINT_ENABLED` (default off).
2. **NVS init** (erase + retry on `NO_FREE_PAGES` / `NEW_VERSION_FOUND`).
3. **Factory reset check** — `CONFIG_WELLD_FACTORY_RESET_GPIO` (default 13, internal pull-up) held LOW at boot erases NVS and reboots for a clean join.
4. **OTA rollback guard** — an RTC boot-attempt counter increments each boot and is cleared on a successful Zigbee send. At 3 consecutive boots without a send, `esp_ota_set_boot_partition()` rolls back to the previous partition (protects against a broken OTA image that crashes before reporting).
5. **RTC struct validation** — each `RTC_DATA_ATTR` struct carries a magic constant; a mismatch (cold boot, or an OTA that changed the layout) zeroes the struct. **Bump the magic whenever you change an RTC struct layout.**
6. **`sensor_i2c_init()`** — brings up the I²C bus + ADS1115 and drives the power-control GPIOs to safe idle. Must precede any sensor read.
7. **Solar detect** — GPIO6 (CN3722 /CHRG, active-low input) sampled and later reported on EP7.
8. **Fail-counter check** — NVS namespace `"welld"`, key `"zb_fails"` (names centralised in `components/welld_core/include/welld_nvs.h`). If ≥ `FAIL_THRESHOLD` (5), `nvs_flash_erase()` drops stale Zigbee network state to force a fresh join. The calibrated sensor offset is read out first and re-saved immediately after the wipe, so calibration survives.
9. **Read all sensors before starting the radio.** The ADC is sensitive to 802.15.4 RF interference, so all `sensor_read_*` calls must precede `zigbee_send`. GPIO5 (VLOOP) must be HIGH ≥10 ms before any 4–20 mA read (12 V rail settles through the Q3 load-disconnect P-FET into C20/C22) and LOW immediately after. A valid level reading is temperature-compensated for water density (`CONFIG_WELLD_TEMP_COMPENSATION_ENABLED`, default on).
10. **Low-battery guard** — if battery ≤ `CONFIG_WELLD_BATT_EMPTY_MV`, skip the Zigbee send *and all NVS writes* (flash programming below 2.7 V during a TX spike corrupts NVS), invalidate the rate history (the level can drift arbitrarily during the blackout, so the first reading after recovery reports rate = NaN), and sleep for `CONFIG_WELLD_SLEEP_MAX_SEC`.
11. **Compute rate of change** from RTC-memory history: the previous valid level plus cumulative elapsed time (sleep durations **and** active-phase durations) across any intervening invalid wakeups. NaN if there's no prior valid reading yet.
12. **`zigbee_send()` blocks** until the radio is idle (success, timeout, or OTA reboot). Receives level / battery / temperature / rate / fail count / solar state, plus the store-and-forward backlog.
13. **Post-send bookkeeping** via `welld_post_send_action()` — the fail counter is written only on change (an in-RAM cache skips redundant NVS commits; flash has limited write cycles). On failure the reading is pushed into the 8-entry RTC store-and-forward buffer; on success the buffer and boot-attempt counter are cleared.
14. **Update RTC history** — only when this wakeup's reading was valid (`level_m >= 0`). On an open-loop reading the previous `last_level_m` is kept and elapsed time keeps accumulating so the next valid reading spans the full gap.
15. **Pick next sleep duration** via `welld_adaptive_sleep_sec()` when `CONFIG_WELLD_ADAPTIVE_SLEEP_ENABLED` and a rate is available; otherwise `CONFIG_WELLD_SLEEP_DURATION_SEC`. Stored in `s_history.pending_sleep_sec` so the next wakeup knows how long it slept.
16. **`enter_deep_sleep()`** — every exit path goes through this helper: `sensor_pre_sleep_cleanup()` (removes the DRDY ISR, deletes the I²C bus), drives VLOOP / BATT_DIV_EN / USB_CHG LOW, then `esp_sleep_config_gpio_isolate()` and `esp_deep_sleep()`. Never call `esp_deep_sleep()` directly.

### RTC-memory state (survives deep sleep, zeroed on cold boot)

All in `main/main.c`, each guarded by its own magic constant:

- `s_history` — `last_level_m`, `elapsed_since_last_valid_sec`, `pending_sleep_sec`, `last_active_sec` (`valid = false` is the cold-boot signal).
- `s_store` — 8-entry store-and-forward ring of readings whose send failed; burst-reported on the next successful send so the coordinator gets the full history.
- `s_rtc_log` — 16-entry event ring for field debugging.
- `s_boot_attempts` — OTA rollback counter.

### Components

- `main/` — orchestration only; owns the NVS fail counter and all RTC-memory state.
- `components/welld_core/` — pure decision/math helpers (`welld_should_wipe_nvs`, `welld_post_send_action`, `welld_rate_cm_per_hour`, `welld_adaptive_sleep_sec`, ZCL encoding helpers) with zero ESP-IDF dependencies, plus `welld_nvs.h` (shared NVS namespace/key defines).
- `components/sensor/` — ADS1115 (I²C addr 0x48) + DS18B20 + power-control GPIOs. AIN0 reads the 4–20 mA shunt, AIN2 the gated battery divider. Conversions run single-shot with the ALERT/DRDY pin in conversion-ready mode: a falling-edge ISR on GPIO12 releases a semaphore (10 ms timeout fallback). Owns NVS keys `"offset_cm"` and `"ds18b20_rom"`. `sensor_level_from_mv()` / `sensor_battery_from_mv()` / `sensor_temp_in_range()` are the pure functions exposed for host tests. Optional median-of-three oversampling (`CONFIG_WELLD_ADC_OVERSAMPLE_ENABLED`) and a peripheral self-test (`CONFIG_WELLD_SELFTEST_ENABLED`). PCB GPIO assignments (all configurable via `WellD Sensor` Kconfig):

  | GPIO | PCB function |
  |------|---------------|
  | 4 | TP5100 USB charger CE — HIGH enables USB-C charging; isolated before deep-sleep (R37 pulls LOW passively). **Pending hardware change**: the BOM replaces the TP5100 with an IP2326 (auto-charge, no CE pin — GPIO4 becomes spare, R36/R37 deleted); firmware keeps the TP5100 drive until the swap is datasheet-confirmed (`hardware/pcb/component_selection_review.md`) |
  | 5 | MT3608B VLOOP boost enable — HIGH → 12 V VLOOP active |
  | 6 | Solar charging detect input (CN3722 /CHRG, active-low — LOW = solar charging in progress) |
  | 7 | DS18B20 1-Wire data (external power mode required; parasite power unsupported) |
  | 10 | I2C SDA (ADS1115 only) |
  | 11 | I2C SCL (ADS1115 only) |
  | 12 | ADS1115 ALERT/DRDY (open-drain conversion-ready output, external 4.7 kΩ pull-up) |
  | 13 | Factory reset (hold LOW at boot → NVS erase + rejoin) |
  | 14 | Status LED (D4, optional — no firmware support yet) |
  | 15 | Battery divider enable (Q2 gate; pulse HIGH ≥1 ms before AIN2 read) |
- `components/zigbee/` — esp-zigbee-lib wrapper. Spawns `zb_task` which runs the BDB commissioning state machine and the stack main loop, with a randomised steering backoff (`CONFIG_WELLD_ZIGBEE_BACKOFF_MAX_MS`) to avoid steer storms after a power outage. Synchronisation back to the caller uses a FreeRTOS event group with `SENT_BIT` / `FAIL_BIT` / `STOPPED_BIT`. The caller must wait for `STOPPED_BIT` before deep-sleep so the radio is fully released.

### Zigbee endpoints

- EP 1 — Analog Input (water level, metres). Also hosts the Basic cluster and the OTA Upgrade client.
- EP 2 — Analog Input (battery volts). Only registered when `CONFIG_WELLD_BATT_REPORT_ENABLED` (default on). The battery is always measured internally for the low-battery guard regardless.
- EP 3 — Temperature Measurement (0x0402, int16 × 0.01 °C). `0x8000` is the ZCL "invalid" sentinel.
- EP 4 — Analog Input (level rate of change, cm/h, signed). Always registered (the descriptor has to be stable across wakeups), but **only reported when the rate is finite** — `isnan(rate)` means there is no prior valid reading and the EP4 report frame is skipped.
- EP 5 — Analog Input (consecutive Zigbee failure counter). Always reported.
- EP 6 — Analog Input (device-side LQI). Always reported, but **current firmware sends a constant 0** (stub — no verified stack API for a device-side reading yet; see the TODO in `zigbee.c`). The converter publishes nonzero values as `device_lqi` and treats 0 as "unknown" (not published) — Z2M's own `linkquality` key comes from the coordinator and was shadowing this endpoint.
- EP 7 — Analog Input (solar charging state, 0/1). Always reported.

When the store-and-forward buffer is non-empty, previously-failed readings are burst-reported before the current one. Reports are unsolicited `zcl_report_attr_cmd_req` to short address `0x0000` (the coordinator). The Z2M external converter (`zigbee2mqtt/welld.js`, logic in `zigbee2mqtt/lib/welld_convert.js`) translates EP IDs to `water_level` / `battery_voltage` / `battery` / `temperature` / `water_level_rate` / `zb_fails` / `device_lqi` / `solar_charging` keys and computes battery % from the `battery_full_mv` / `battery_empty_mv` device options.

### OTA — the version pipeline

The OTA image version is **derived from `PROJECT_VER`** in the root `CMakeLists.txt` at build time:

```
PROJECT_VER = "MAJOR.MINOR.PATCH"  →  OTA_FW_VERSION = 0xMMmmPP00
```

This conversion lives in `components/zigbee/CMakeLists.txt` (it fails the build loudly on a malformed `PROJECT_VER`) and is passed as a `-D` compile definition. **To cut a new firmware release, bump `PROJECT_VER` in the root `CMakeLists.txt`** — don't touch `OTA_FW_VERSION` directly. CI enforces a version bump on any PR that touches `main/` or `components/`.

`OTA_MANUFACTURER_CODE = 0x1234` and `OTA_IMAGE_TYPE = 0x0001` are hardcoded in `components/zigbee/zigbee.c`. Any `.zigbee` OTA file passed to Zigbee2MQTT must be packed with those exact values via `ota_image_create.py` (`--manufacturer-code 0x1234 --image-type 0x0001`); the device rejects mismatched headers. **Do not wildcard these to `0xFFFF`** — they're a security boundary against rogue OTA servers. CI generates the `.zigbee` image automatically as a build artifact.

OTA failure handling is two-layered:
- **Stall watchdog** — a download that exceeds `CONFIG_WELLD_OTA_STALL_TIMEOUT_SEC` (default 240 s wall clock) is aborted so a hung transfer can't keep the radio alive indefinitely.
- **Rollback guard** — 3 consecutive boots without a successful Zigbee send roll the boot partition back to the previous image (see wake-cycle step 4).

The partition table (`partitions.csv`) defines dual 1.5 MB OTA slots (`ota_0` / `ota_1`); `esp_ota_get_next_update_partition(NULL)` always returns the inactive one. `sdkconfig.defaults` pins `CONFIG_ESPTOOLPY_FLASHSIZE_4MB=y` to fit them — don't drop this without resizing partitions.

### Secure Boot V2

`sdkconfig.defaults` enables Secure Boot V2 (ECDSA-P256). Because the bootloader grows to ~44 KB, the partition table is pushed to offset `0x10000` — keep `partitions.csv` and `CONFIG_PARTITION_TABLE_OFFSET` in agreement. **CI builds are intentionally unsigned**; `CONFIG_SECURE_BOOT_BUILD_SIGNED_BINARIES` is enabled only in `sdkconfig.defaults.local` on the machine holding `secure_boot_signing_key.pem` (gitignored — never commit it). Signing instructions are in the comments of `sdkconfig.defaults`.

### Configuration layering

- `sdkconfig.defaults` — **committed**, contains only settings that must hold regardless of local config (flash size, Zigbee role, watchdog, brownout, secure boot).
- `sdkconfig.defaults.local` — **gitignored**, user-specific overrides (`.example` template at repo root).
- `sdkconfig` — **committed and regenerated** by `menuconfig` (CI regenerates its own copy from `sdkconfig.defaults` via `set-target`). Updates land via PRs (the auto-commit CI step was removed in commit `174a595`).
- `dependencies.lock` — managed component pins, committed.

WellD Kconfig options are split across three menus: `main/Kconfig.projbuild` (`WellD Configuration` — sleep, diagnostics, OTA stall, factory reset), `components/sensor/Kconfig` (`WellD Sensor` — GPIOs, ADS1115, calibration, battery thresholds, temperature compensation), and `components/zigbee/Kconfig` (`WellD Zigbee` — channel mask, send delay). Kconfig `range` clauses defend against bad values from `sdkconfig.defaults.local`.

### Dependency pinning

`components/sensor/idf_component.yml` and `components/zigbee/idf_component.yml` use **exact `==` pins**, not `^`:

```
espressif/esp-zigbee-lib: "==2.0.1"
espressif/onewire_bus:    "==1.1.1"
espressif/ds18b20:        "==0.3.1"
```

`esp-zboss-lib` was removed as a separate dependency in 2.0.1 — zboss is now bundled inside `esp-zigbee-lib` (with `CONFIG_ZB_SDK_1xx=y` providing the 1.x API compat layer). These libraries have rough APIs that have churned across point releases (see commits `13a5338`, `776ce6f`, `11991d8`). Bump them one at a time and run a hardware build; expect to fix API renames.

### Failure recovery semantics

- 5 consecutive Zigbee send failures → next boot erases NVS → fresh join. The calibrated sensor offset is preserved across the wipe (read before, re-saved after). This is the only self-healing path for join state; there is no watchdog re-pair logic inside a single wake cycle.
- Failed sends are buffered (8 entries, RTC memory) and burst-reported after the next successful send, preserving rate accuracy.
- DS18B20 missing or out-of-range → temperature omitted from report, retried next wake. Temperature compensation is skipped when the probe read fails.
- Pressure-loop current < 3.5 mA → `water_level = -1.0` reported (converter forwards as `null`, HA marks unavailable).
- Battery at/below `CONFIG_WELLD_BATT_EMPTY_MV` → send and NVS writes skipped entirely; device sleeps the maximum interval.
- Task watchdog (30 s) and brownout detection are enabled in `sdkconfig.defaults`; the reset reason is logged into the RTC event ring on the next boot.
- Field recovery without tools: hold GPIO13 LOW at boot for a factory reset (NVS erase + rejoin).

## Conventions

- ESP32-C6-specific code (RISC-V, single core + LP core): guard with `CONFIG_IDF_TARGET_ESP32C6`. There is no plan to support other targets — `set-target` is C6 only.
- New tunables go in the appropriate Kconfig menu with a `range` clause, and get a documentation row in `README.md` and a commented line in `sdkconfig.defaults.local.example`.
- User-visible changes get an entry under `[Unreleased]` in `CHANGELOG.md` (Keep a Changelog format, SemVer).
- Component `REQUIRES` lists are minimal and explicit; prefer adding to `REQUIRES` over reaching for transitive includes.
- Log tag convention: one `static const char *TAG` per `.c` file, named for the component (`"main"`, `"sensor"`, `"zigbee"`).
- Code style is enforced by `.clang-format` / `.editorconfig`; `.pre-commit-config.yaml` is available for local hooks.
- NVS namespace/key strings live only in `components/welld_core/include/welld_nvs.h` — never inline the literals.
- `AGENTS.md` is a compact mirror of this file for OpenCode sessions; keep the two consistent when commands or architecture change.

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

**Handoff contract**: when the PCB agent changes a GPIO assignment, the firmware agent must update `components/sensor/sensor.c`, `components/sensor/Kconfig` defaults, and the GPIO table in this file before any case work begins.

**Hardware sub-agent routing**:
- PCB changes first → outputs GPIO map + dimensions → case and firmware agents consume those outputs
- Case-only changes (no PCB change) → case-engineer runs independently
- Never run PCB and case agents on the same files simultaneously

**`senior-reviewer` runs last** in every `/improve` cycle that touches PCB or firmware. It is a gate, not a contributor — it reads but never writes. If it returns BLOCKED, resolve the CRITICAL items before marking the cycle complete.

## Hardware layout

`hardware/pcb/` is the **current** fresh-start KiCad 10 design (manual layout in progress); `hardware/pcb_old/` is the archived auto-generated design — reference only, never modify it. Because the current schematic sheets have symbols but incomplete wiring, `hardware/pcb/schematic_connections.md` is the authoritative net-by-net wiring reference; `bom_footprints.md` and `placement_constraints.md` carry the BOM and datasheet placement rules.

## Electrical correctness gate (hardware changes)

**Before any PCB layout work begins after a schematic change**, perform this checklist inline or via the senior-reviewer:

1. **IC companion passives** — every active IC must have all required passive components present in the schematic: feedback dividers (buck/boost), bootstrap caps, decoupling caps, pull-ups on open-drain pins, PG/EN resistors per datasheet.
2. **Net connectivity** — verify `hardware/pcb/schematic_connections.md` reflects any new or changed nets. If wires are missing from a schematic sheet, this document is the authoritative reference.
3. **Voltage ratings** — all component ratings must cover the operating range with ≥20% margin: VBAT 6.0–8.4V, VLOOP 12V, VUSB 5V, +3V3.
4. **CV/CC setpoints** — verify charger output voltage is ≤8.40V for 2S Li-ion (CN3722 CV = 8.31V via R33=590kΩ).
5. **Open-drain pull-ups** — any open-drain signal (ADS_DRDY, I²C) must have an external pull-up resistor; do not rely on internal weak pull-ups alone.

**Why this gate exists**: the Python-generated schematics (pre-2026-05-25) had correct component symbols but zero wire connections and missing critical passives (R_FBH/R_FBL for the AP63205WU feedback divider, R_DRDY for ADS1115 DRDY). These were not caught until the senior reviewer ran on 2026-05-25 (BLOCKED, 4 CRITICAL). The gate prevents tape-out with a schematic that has symbols but no electrical correctness verification.

## CI

`.github/workflows/build.yml` has six jobs. No third-party actions are used — every job does an inline git checkout, and ESP-IDF jobs run inside `docker run espressif/idf:v6.0.1`:

- **ESP-IDF build (esp32c6)** — builds the firmware, derives the OTA file version from `PROJECT_VER`, packs the `.zigbee` OTA image via `ota_image_create.py`, and guards against `CONFIG_SECURE_BOOT_BUILD_SIGNED_BINARIES=y` leaking into the CI sdkconfig (build outputs are not uploaded as artifacts — that would need `actions/upload-artifact`, which the no-third-party-actions policy excludes).
- **C static analysis (cppcheck)** — runs `cppcheck` over all C source files under `components/` and `main/`; fails on any warning, style, performance, or portability finding.
- **Version bump check** — on pull requests only; fails if any `main/` or `components/` source changed without a matching bump to `PROJECT_VER` in `CMakeLists.txt`.
- **Host unit tests** — plain `ubuntu-latest`, no Docker, no ESP-IDF. Runs the `test/host/` suite (welld_core + sensor pure helpers) via ctest. Fetches Unity at configure time.
- **On-device unit tests (build only)** — builds `test/sensor` and `test/welld_core` for esp32c6 to catch compile breaks. The tests themselves need real hardware to execute.
- **Zigbee2MQTT converter tests** — Node 20, runs `npm test` in `zigbee2mqtt/` against the external converter.
