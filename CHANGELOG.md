# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- OTA rollback guard was inert: it looked up `esp_ota_get_last_invalid_partition()`, which never matches in this app-level scheme. It now targets the inactive OTA slot (validated to contain an app image) and clears the RTC boot-attempt counter before restarting so the rolled-back image cannot immediately bounce back to the broken slot.
- OTA firmware version encoding now matches the documented `0xMMmmPP00` format used by the CI-packed `.zigbee` image (the firmware previously advertised `0xMMmm00PP`, so an identically-versioned OTA file looked like an upgrade).
- `zigbee_send()` no longer times out mid-OTA: it keeps waiting while a download is in progress instead of deleting the event group/timers still used by the Zigbee task and deep-sleeping with the radio active (the OTA stall watchdog still bounds the wait).
- Store-and-forward backlog is now burst-reported *before* the current reading, so Zigbee2MQTT's last-received state reflects the newest measurement instead of the oldest backlog entry.
- A low-battery wakeup now invalidates the rate-of-change history; previously the stale level was paired with a reset elapsed accumulator, producing a false rate spike on the first report after battery recovery. The low-battery threshold check is now at-or-below, as documented.
- Self-test VLOOP GPIO readback always failed (output-only pins read back 0); the input buffer is now enabled for the check.
- RTC event-log write index no longer wraps at 256 events (which made the log print as empty/short once per wrap).

### Changed
- Battery voltage is now reported over Zigbee (EP2) by default: the stale `CONFIG_WELLD_BATT_ADC_CHANNEL` int option (default `-1`, which silently disabled EP2 while the battery was still measured internally) is replaced by `CONFIG_WELLD_BATT_REPORT_ENABLED` (bool, default `y`).
- Z2M converter: the device-side LQI (EP6) is now exposed as `device_lqi` instead of `linkquality`, which Zigbee2MQTT's own coordinator-side key was shadowing. A value of 0 means "unknown" and is not published — current firmware always sends 0 (the device-side reading is a stub), so `device_lqi` will not appear until a future firmware release populates it.
- VLOOP (MT3608B EN) settling wait before a 4–20 mA read raised from 5 ms to 10 ms — the 12 V output caps now charge through the Q3 load-disconnect P-FET (PCB review 2026-07).
- **Migration notes for the battery change**: (1) devices OTA-upgraded from ≤ 1.0.2 need a Zigbee2MQTT re-interview (or re-pair) to surface the new EP2 battery entities — Z2M caches the endpoint list from the original interview; (2) a stale `CONFIG_WELLD_BATT_ADC_CHANNEL` line in `sdkconfig.defaults.local` is silently ignored by Kconfig — operators who used `-1` to disable battery reporting must now set `CONFIG_WELLD_BATT_REPORT_ENABLED=n`.

### Added
- `.editorconfig`, `.clang-format`, and `.pre-commit-config.yaml` for consistent code style.
- CI static-analysis job (`cppcheck`) and automatic OTA image artifact generation.
- `CHANGELOG.md` and version-bump enforcement in CI.
- `TROUBLESHOOTING.md` with field-debugging decision trees.
- Kconfig options for diagnostic mode, Zigbee steering backoff, and OTA stall timeout.
- Compile-time asserts in `sensor_pure.c` for shunt resistance and max depth.
- Watchdog timer and brownout detection enabled by default.
- Randomized backoff before Zigbee network steering to mitigate steer storms.
- `zb_fails` counter exposed as a ZCL attribute (Analog Input, endpoint 5).

### Changed
- OTA stall timeout is now configurable via `CONFIG_WELLD_OTA_STALL_TIMEOUT_SEC`.

## [1.0.0] – 2026-05-18

### Added
- Initial release: ESP32-C6 well-level monitor with 4–20 mA pressure transducer, DS18B20 temperature, ADS1115 battery monitoring.
- Zigbee 3.0 End Device reporting to Zigbee2MQTT.
- Adaptive sleep based on rate-of-change.
- OTA upgrade client with dual 1.5 MB app slots.
- Self-healing: 5 consecutive Zigbee send failures erase NVS and force rejoin.
- Host unit-test harness (Unity) and on-device test apps.
- Custom PCB design (80 × 55 mm) and OpenSCAD parametric enclosure.
