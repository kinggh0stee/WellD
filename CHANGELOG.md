# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Hardware
- Applied the four user-approved swaps from `alternatives_review_2026-07-15.md`: Q2/Q4 BSS123 → AO3400A (C20917, 2N7002 second source), M_SOLAR AO3407 → SI2319CDS −40 V (C146287, new `welld:SI2319CDS` symbol), J13 GCT USB4135 → HRO TYPE-C-31-M-12 (C165948, footprint `Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12`), and DNF GDT footprints GDT1/GDT2 on the field loop lines (LOOP_TERM_CH1/CH2 → GND); netlist re-verified with zero mismatches.
- `hardware/pcb/alternatives_review_2026-07-15.md`: "better options" review of every BOM position against community track record / LCSC multi-sourcing — all major ICs confirmed KEEP; proposed (not applied): Q2/Q4 BSS123→AO3400A, J13 GCT USB-C→HRO TYPE-C-31-M-12, optional GDT footprints on the field loop lines and −40 V SI2319CDS for M_SOLAR; 1S-vs-2S architecture trade documented.
- `hardware/pcb/fab_checklist.md`: consolidated, ordered path-to-fabrication checklist (first KiCad session + ERC waivables, vendor question, layout constraints, verified order list, first-article bench checks, enclosure sequencing).
- All eight required schematic edits from the component sweep applied (AP63203 renumber + BST bootstrap cap on new net AP_BST, USBLC6/PRTR5V0U2X pinout fixes, SMAJ5.0A clamps, QFN-24 IP2326 footprint, cap voltage uprates); netlist re-verified with zero mismatches.
- Full BOM component-verification sweep against vendor datasheets (`hardware/pcb/component_verification_2026-07-14.md`): AP63203 buck requires a previously-missing 100 nF BST–SW bootstrap cap (new C_BST_AP row — the 3.3 V rail could not start) and its symbol pin numbering was wrong; IP2326 package resolved (QFN24 4×4 mm); D9/D10 loop clamps changed SMAJ3.3CA → SMAJ5.0A (leakage); F2 PTC, L3, L_SOLAR and NTC MPNs fixed; wrong LCSC numbers corrected (PRTR5V0U2X, CN3722, ESP32-C6-MINI-1U-H4); USBLC6/PRTR5V0U2X/MT3608B pinouts verified.

### Fixed
- OTA rollback can no longer flip a healthy image to the old slot during a coordinator outage: the boot-attempt counter is armed only while the running image is unproven (NVS marker `img_ok` stores the version string of the last image that completed a successful send), and low-battery-skip wakeups no longer count as failed boot attempts.
- An OTA download failure (stall abort, flash error) no longer counts as a Zigbee send failure when the sensor report itself was delivered — previously five OTA-plagued wakeups could wipe NVS and force a needless rejoin.
- `zigbee_send()` no longer deletes its synchronisation objects while `zb_task` may still be unwinding (>5 s teardown): the objects are deliberately leaked for the one remaining wake cycle instead (deep sleep resets the chip), eliminating a narrow use-after-free window.
- EP6 now reports the real device-side LQI, read from the Zigbee stack's neighbor table (parent entry). Previously it sent a constant 0 stub, which the converter suppresses as "unknown".
- OTA rollback guard was inert: it looked up `esp_ota_get_last_invalid_partition()`, which never matches in this app-level scheme. It now targets the inactive OTA slot (validated to contain an app image) and clears the RTC boot-attempt counter before restarting so the rolled-back image cannot immediately bounce back to the broken slot.
- OTA firmware version encoding now matches the documented `0xMMmmPP00` format used by the CI-packed `.zigbee` image (the firmware previously advertised `0xMMmm00PP`, so an identically-versioned OTA file looked like an upgrade).
- `zigbee_send()` no longer times out mid-OTA: it keeps waiting while a download is in progress instead of deleting the event group/timers still used by the Zigbee task and deep-sleeping with the radio active (the OTA stall watchdog still bounds the wait).
- Store-and-forward backlog is now burst-reported *before* the current reading, so Zigbee2MQTT's last-received state reflects the newest measurement instead of the oldest backlog entry.
- A low-battery wakeup now invalidates the rate-of-change history; previously the stale level was paired with a reset elapsed accumulator, producing a false rate spike on the first report after battery recovery. The low-battery threshold check is now at-or-below, as documented.
- Self-test VLOOP GPIO readback always failed (output-only pins read back 0); the input buffer is now enabled for the check.
- RTC event-log write index no longer wraps at 256 events (which made the log print as empty/short once per wrap).

### Changed
- Battery voltage is now reported over Zigbee (EP2) by default: the stale `CONFIG_WELLD_BATT_ADC_CHANNEL` int option (default `-1`, which silently disabled EP2 while the battery was still measured internally) is replaced by `CONFIG_WELLD_BATT_REPORT_ENABLED` (bool, default `y`).
- Z2M converter: the device-side LQI (EP6) is now exposed as `device_lqi` instead of `linkquality`, which Zigbee2MQTT's own coordinator-side key was shadowing. A value of 0 means "unknown" and is not published (firmware ≤ 1.0.2 always sent 0; this release populates the real reading — see Fixed).
- VLOOP (MT3608B EN) settling wait before a 4–20 mA read raised from 5 ms to 10 ms — the 12 V output caps now charge through the Q3 load-disconnect P-FET (PCB review 2026-07).
- The battery is now read before the water level and temperature so the low-battery guard can skip the remaining sensor reads entirely (no VLOOP boost power or DS18B20 NVS write on a wakeup that won't report).
- The post-send ACK window now scales with the store-and-forward backlog size (up to 4× `CONFIG_WELLD_ZIGBEE_SEND_DELAY_MS`), so a full 8-entry burst isn't cut off mid-flight.
- **Migration notes for the battery change**: (1) devices OTA-upgraded from ≤ 1.0.2 need a Zigbee2MQTT re-interview (or re-pair) to surface the new EP2 battery entities — Z2M caches the endpoint list from the original interview; (2) a stale `CONFIG_WELLD_BATT_ADC_CHANNEL` line in `sdkconfig.defaults.local` is silently ignored by Kconfig — operators who used `-1` to disable battery reporting must now set `CONFIG_WELLD_BATT_REPORT_ENABLED=n`.

### Added
- Hardware: schematic fully wired (stub+label connectivity across all four sheets, explicit no-connects, PWR_FLAGs); netlist machine-verified against `schematic_connections.md` with zero mismatches (`hardware/pcb/kicad_wire_script.py` + `netlist_check.py`; KiCad-native ERC pending KiCad 10 availability).
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
