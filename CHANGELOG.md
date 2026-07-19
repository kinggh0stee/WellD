# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Hardware
- **Datasheet-verification pass over every 1S-conversion part** (blockers #10–#11): TP4056, HT7333-A, and DW01A confirmed as drawn (LCSC C16581 / C21583 / C351410-class); **two symbols were wrong and are corrected** — the CN3791 is a *controller*, not an integrated switch (external P-FET stage restored: SI2319CDS + SS34 series diode + 300 k gate resistor; COM compensation 220 nF+120 Ω added; verified pin map VG=1…DRV=10; I_CH = 120 mV/R_CS → 1.2 A at 0.1 Ω), and the FS8205A's real TSSOP-8 map is D=1&8/S1=2&3/G1=4/G2=5/S2=6&7 (redrawn). **The CN3791 has no TEMP pin → RT_SOLAR deleted; the solar path has no cold-charge cutoff** (new decision item #10f — RT1 guards only the USB path). Battery-carrier MPNs picked: MY-18650-02 THT clip pair (C2979182, recommended) or BH-18650-B1BA002 (C2988620). Netlist re-verified: 366 pins / 72 nets / 0 mismatches.
- **Board outline unconstrained** (user decision): the 80 × 55 mm target is dropped — the BT1 18650 carrier goes on the **top side** along a long edge and the outline grows around the finished placement (working target ≈100 × 60 mm, final dims set at layout). Keeps assembly single-sided; the case consumes the final outline afterwards.
- **Battery carrier**: the Sinowatt pack is dropped for a **single generic 18650 in an on-board THT carrier (BT1)**; the XT30 connector (J1) is deleted. Because generic bare cells have no PCM, discrete 1S protection is added — **DW01A + FS8205A** in the cell− path (the standard TP4056-ecosystem pair; pinouts/values flagged for datasheet confirmation as blocker #11). D5 reverse-polarity MOSFET now guards against reversed cell insertion; capacity ≈3–3.4 Ah (single cell). Netlist re-verified: 357 pins / 69 nets / 0 mismatches.
- **1S power-architecture conversion** (user decision — 1S chosen deliberately for simplicity and parts ecosystem after an analysis that slightly favored 2S at ≈320 vs ≈300 days per charge): pack 2S1P → **1S2P** (same Sinowatt 3350 mAh cells, ≈6.7 Ah, VBAT 3.0–4.2 V, XT30 unchanged). IP2326 boost-charger subsystem deleted → **TP4056** 1 A linear USB charger (CE strapped high, NTC window kept, /CHRG on the existing net); CN3722 controller + entire external buck stage deleted → **CN3791** 1S MPPT buck charger (integrated switch, fixed 4.2 V CV, MPPT ≈5.0 V for 6 V panels, /CHRG_SOLAR net unchanged so the GPIO6 firmware contract holds); AP63203WU buck deleted (VIN min 3.8 V fails at 1S empty) → **HT7333-A** 3.3 V LDO; MT3608B 12 V loop boost stage kept. TVS re-rates: D13 → SMAJ5.0A, D8/D14 → SMAJ10CA (6 V-nominal panel, Voc ≤ 10 V). Battery divider R7 330 k → 100 k (÷2). GPIO map unchanged; GPIO4 is now genuinely spare in hardware. Netlist re-verified: 337 pins / 63 nets / 0 mismatches. New datasheet-verification blockers #10a–e recorded in `schematic_connections.md` (CN3791/TP4056/HT7333 datasheets were not fetchable at conversion time). Firmware handoff pending: battery Kconfig defaults 4200/3000 mV, divider ratio 200, and the AIN2 read must move to the ADS1115 ±4.096 V PGA (2.1 V max at the new divider).
- Applied the four user-approved swaps from `alternatives_review_2026-07-15.md`: Q2/Q4 BSS123 → AO3400A (C20917, 2N7002 second source), M_SOLAR AO3407 → SI2319CDS −40 V (C146287, new `welld:SI2319CDS` symbol), J13 GCT USB4135 → HRO TYPE-C-31-M-12 (C165948, footprint `Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12`), and DNF GDT footprints GDT1/GDT2 on the field loop lines (LOOP_TERM_CH1/CH2 → GND); netlist re-verified with zero mismatches.
- `hardware/pcb/alternatives_review_2026-07-15.md`: "better options" review of every BOM position against community track record / LCSC multi-sourcing — all major ICs confirmed KEEP; proposed (not applied): Q2/Q4 BSS123→AO3400A, J13 GCT USB-C→HRO TYPE-C-31-M-12, optional GDT footprints on the field loop lines and −40 V SI2319CDS for M_SOLAR; 1S-vs-2S architecture trade documented.
- `hardware/pcb/fab_checklist.md`: consolidated, ordered path-to-fabrication checklist (first KiCad session + ERC waivables, vendor question, layout constraints, verified order list, first-article bench checks, enclosure sequencing).
- All eight required schematic edits from the component sweep applied (AP63203 renumber + BST bootstrap cap on new net AP_BST, USBLC6/PRTR5V0U2X pinout fixes, SMAJ5.0A clamps, QFN-24 IP2326 footprint, cap voltage uprates); netlist re-verified with zero mismatches.
- Full BOM component-verification sweep against vendor datasheets (`hardware/pcb/component_verification_2026-07-14.md`): AP63203 buck requires a previously-missing 100 nF BST–SW bootstrap cap (new C_BST_AP row — the 3.3 V rail could not start) and its symbol pin numbering was wrong; IP2326 package resolved (QFN24 4×4 mm); D9/D10 loop clamps changed SMAJ3.3CA → SMAJ5.0A (leakage); F2 PTC, L3, L_SOLAR and NTC MPNs fixed; wrong LCSC numbers corrected (PRTR5V0U2X, CN3722, ESP32-C6-MINI-1U-H4); USBLC6/PRTR5V0U2X/MT3608B pinouts verified.

### Changed (1S conversion — firmware/converter side)
- Battery Kconfig defaults now match the 1S board: `CONFIG_WELLD_BATT_DIVIDER_RATIO` 430 → **200** (R7/R8 = 100 k/100 k), `CONFIG_WELLD_BATT_FULL_MV` 8400 → **4200**, `CONFIG_WELLD_BATT_EMPTY_MV` 6000 → **3000**. (No 2S boards were ever fabricated — no migration path is provided or needed.)
- The ADS1115 battery read (AIN2) now uses the **±4.096 V PGA** (the loop shunt read keeps ±2.048 V): the 1S ÷2 divider puts up to 2.1 V on AIN2, which the previous ±2.048 V range clipped exactly at full charge.
- Z2M converter battery defaults follow the firmware: `battery_full_mv`/`battery_empty_mv` defaults 8400/6000 → **4200/3000**, option range now 2500–4500 mV (1S). Converter tests rewritten for the 1S range (47 tests green).
- **Removed** `CONFIG_WELLD_USB_CHG_GPIO` and the GPIO4 charger-CE drive entirely: the TP4056 charges autonomously (CE strapped high in hardware) and GPIO4 has no schematic connection. GPIO4 is fully spare.

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
