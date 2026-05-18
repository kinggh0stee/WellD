# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
- Initial release: ESP32-C6 well-level monitor with 4–20 mA pressure transducer, DS18B20 temperature, MAX17048/ADS1115 battery monitoring.
- Zigbee 3.0 End Device reporting to Zigbee2MQTT.
- Adaptive sleep based on rate-of-change.
- OTA upgrade client with dual 1.5 MB app slots.
- Self-healing: 5 consecutive Zigbee send failures erase NVS and force rejoin.
- Host unit-test harness (Unity) and on-device test apps.
- Custom PCB design (80 × 55 mm) and OpenSCAD parametric enclosure.
