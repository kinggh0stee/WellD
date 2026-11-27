# WellD

Battery-powered well-level monitor for the ESP32-C6. Each wakeup it reads a 4–20 mA submersible pressure transducer, a DS18B20 temperature probe, and battery voltage; reports them over Zigbee to Zigbee2MQTT; then deep-sleeps until the next cycle.

- **Radio:** Zigbee 3.0 over the C6's built-in 802.15.4 — no extra modules
- **Battery life:** months on a single 18650 cell at the default 5-minute interval (deep sleep between readings)
- **Adaptive sleep:** sleep duration scales with how fast the level is changing — longer windows when stable, shorter during transients
- **Rate-of-change reporting:** `water_level_rate` in cm/h; distinguishes "well recovering" from "well being drawn down"
- **Outage-tolerant:** keeps its network membership through coordinator outages (resumes on its own when the coordinator is back), buffers failed readings for a burst re-send, and backs off to the maximum sleep interval after 3 consecutive failed sends to save the battery
- **OTA:** Zigbee OTA Upgrade client (queries the coordinator every wakeup), dual 1.5 MB app slots, rollback guard
- **Sentinels:** open-loop (< 3.5 mA) and short-circuit (> 21 mA) transducer faults both report `null` water level so Home Assistant can alert on wiring faults

---

## Hardware — Custom PCB

The current design is a purpose-built custom PCB (outline set at layout — working target ≈100 × 60 mm, sized around the on-board 18650 carrier). Design files, BOM, and assembly guide live in [`hardware/`](hardware/).

### Key ICs

| IC | Role |
|----|------|
| ESP32-C6 module | MCU + Zigbee radio |
| ADS1115 (0x48) | 16-bit I²C ADC — shunt voltage (AIN0) + battery divider (AIN2) |
| HT7333-A | 3.3 V LDO (≈4 µA Iq, 250 mA, ~90 mV dropout). Replaced the AP63203WU buck in the 2026-07-19 1S conversion — the buck's 3.8 V minimum input fails at 1S empty (3.0 V). Below ≈3.4 V the output follows the battery minus dropout; the ESP32-C6 runs down to 3.0 V |
| MT3608B | 12 V **asynchronous** boost for the 4–20 mA loop supply (VLOOP, GPIO5-gated). D15 (SS34 Schottky) rectifies the switch node; a Q3/Q4 load-disconnect switch in series with L1 blocks the permanent VBAT leak to the loop terminals during deep sleep |
| CN3791 | 1S MPPT solar buck charge **controller** (external SI2319CDS P-FET stage; fixed 4.2 V CV, MPPT ≈5.0 V for 6 V-nominal panels; panel Voc limited to **10 V** by the SMAJ10CA input TVS). A solar-powered LM393 cold-charge cutoff clamps charging below ≈+2 °C — zero battery draw at night |
| TP4056 | USB-C 1 A linear charger (2026-07-19 1S conversion — replaced the IP2326 boost selection, which itself replaced the non-functional TP5100). Auto-charges whenever VBUS is present (CE strapped high); charge-temperature NTC window ≈ +5…+44 °C |
| DW01A + FS8205A | On-board 1S battery protection (supervisor + dual N-FET in the cell− path) — added 2026-07-19 with the generic-18650 carrier; a bare cell has no PCM |

### Test points (production / field debug)

All 15 test point pads are 1.0 mm SMD, **DNF** (do not fit) — bare copper pads suitable for ICT fixture probes or a hook wire. No component is installed in production. Test points are placed scattered near their associated circuits rather than grouped in a single row.

| Ref | Net | Ref | Net |
|-----|-----|-----|-----|
| TP1 | VBAT (3.0–4.2 V, 1S range) | TP9 | I2C SCL |
| TP2 | VLOOP (12 V boost) | TP10 | VSOLAR_IN |
| TP3 | +3V3 | TP11 | VBAT_RAW (before D5 reverse-polarity MOSFET) |
| TP4 | GND | TP12 | ADS1115 DRDY (GPIO22) |
| TP5 | LOOP+ (LOOP_TERM_CH1) | TP13 | FACTORY_RESET (GPIO23 — short to GND while powering on) |
| TP6 | LOOP- (LOOP_TERM_CH2) | TP14 | /CHRG_SOLAR (CN3791 charge status) |
| TP7 | 1WIRE | TP15 | /CHRG_USB (TP4056 charge status, with R38 pull-up) |
| TP8 | I2C SDA | | |

### Thermal improvements

The PCB includes a 10 × 10 mm solid GND copper pour on F.Cu and B.Cu centred on the CN3791 solar charger (U7), connected by four thermal vias (0.6 mm drill / 1.0 mm pad) — the CN3791's integrated switch dissipates in-package, so this pour matters more than it did for the CN3722 controller it replaced. A matching pour under the TP4056 EPAD carries the ≈1.3 W of linear charge dissipation at 1 A. A GND via-stitch ring around the MT3608B / L1 boost island provides a low-inductance return path for the switching node without adding a solid pour under L1.

### GPIO map

| GPIO | Direction | Function |
|------|-----------|----------|
| 18 | SDA | I²C bus (ADS1115 only) — GPIO10/11 are not bonded out on the ESP32-C6-MINI-1 module, so I²C is on GPIO18/19 |
| 19 | SCL | I²C bus (ADS1115 only) |
| 12 | USB    | Native USB D− → USB-C (console/programming); from U11 USBLC6 |
| 5  | Output | MT3608B EN + Q4 gate — 12 V loop supply (`VLOOP`), with Q3/Q4 load-disconnect; R27 pull-down holds it off during deep sleep |
| 4  | —      | Spare — no schematic connection (the TP4056 USB charger is autonomous, CE strapped high in hardware) |
| 6  | Input  | Solar charger /CHRG (CN3791) — solar-charging-active detect (active-low: LOW = charging; R25 external pull-up) |
| 7  | 1-Wire | DS18B20 data |
| 13 | USB    | Native USB D+ → USB-C (console/programming) |
| 22 | Input  | ADS1115 ALERT/DRDY (moved off GPIO12) |
| 23 | Input  | Factory reset (hold LOW at boot → NVS + Zigbee network erase, re-pair with permit-join; via TP13; moved off GPIO13) |
| 15 | Output | Battery-divider enable (`BATT_DIV_EN`) — drives the Q2 level-shifter that switches the Q5 high-side P-FET |
| 14 | —      | Status LED (D4 via R14/SJ3 — moved off GPIO13, now native USB D+; no firmware support yet) |

### Connections (screw terminals)

| Terminal | Wire | ESD / surge protection |
|----------|------|------------------------|
| LOOP+ / LOOP− | 4–20 mA transducer, two-wire | D9 / D10 SMAJ5.0A TVS (400 W, DO-214AC); D11 SMAJ13A unidirectional TVS on VLOOP; D1 PRTR5V0U2X rail clamp at ADS1115 inputs |
| 1W DATA / GND | DS18B20 data + ground | D12 PRTR5V0U2X dual-channel rail clamp (SOT-363) — 0.5 pF added capacitance, well below the 800 pF 1-Wire add limit |
| Battery | Single generic 18650 (3.0–4.2 V) in the on-board THT carrier **BT1** — no cable, no connector (the XT30 was deleted 2026-07-19) | On-board 1S protection **DW01A + FS8205A** in the cell− path (generic bare cells have no PCM): over-discharge ≈2.4 V, over-charge ≈4.3 V, over-current. D13 SMAJ5.0A TVS at the cell+ tab; D5 AO3407 P-ch MOSFET in series on cell+ blocks a **reversed-inserted cell**; R31 10 kΩ gate pull-down holds D5 on |
| SOLAR+/−      | Solar panel, ≤ **10 V Voc** (6 V-nominal panels — 1S conversion 2026-07-19; the 2S design accepted 12 V panels) | D14 SMAJ10CA bidirectional TVS (400 W, DO-214AC) at the terminal, plus second-stage D8 SMAJ10CA at the CN3791 VIN |

### RF / antenna

The ESP32-C6-MINI-1U-H4 module exposes a U.FL RF port. A ~50 mm internal pigtail — **Taoglas CAB.100.07.0050B** (U.FL female to SMA male, RG178 coax) — connects the module to **J3**, an **Amphenol 132289** SMD edge-launch SMA connector on the top board edge. PCBWay hand-attaches the pigtail after reflow. An external 2.4 GHz SMA antenna (e.g. Taoglas FXP73 rubber-duck, 2 dBi) screws directly onto J3.

### Assembly notes (PCBWay)

Connector placement:

- **Bottom edge (left to right):** J12 (solar, 2-pos), J4 (loop ch1, 3-pos), J5 (loop ch2, 3-pos), J6 (DS18B20, 3-pos), J7 (spare sensor, 3-pos), J10 (programming header, 6-pin 1.27 mm pitch)
- **Left edge:** J13 (USB-C — charging **and** console/programming, SMD; D± wired to the ESP32 native USB pins). The BT1 18650 carrier occupies its own top-side band along one long edge (board size is unconstrained, so the outline grows to fit)
- **Top edge:** J3 (Amphenol 132289 SMA edge-launch)

- **J4, J5, J6, J7, J12** — Phoenix Contact MC 1.5/x-G-3.5 THT terminal blocks, wave-soldered.
- **J10** — 1.27 mm pitch THT vertical programming header (6-pin), wave-soldered.
- **J8, J9** (expansion headers) — **DNF** (do not populate) on all production boards. Footprints are present on the PCB for future use; no components are installed.
- **J3** pigtail — hand-attached by PCBWay post-reflow; not wave-soldered.

### 4–20 mA loop

The MT3608B boost converter lifts VLOOP to 12 V to power the transducer loop. The boost is asynchronous: D15 (SS34 Schottky) carries the switch node to VLOOP, and a Q3 (P-FET) / Q4 (level-shifter) load-disconnect switch in series with the inductor prevents VBAT from leaking through L1 + D15 to the loop terminals during deep sleep. GPIO5 drives both the MT3608B EN and the Q4 gate; R27 pulls the net low while GPIO5 is isolated in deep sleep.

Firmware gates GPIO5 high for `CONFIG_WELLD_VLOOP_SETTLE_MS` — **10 ms** by default: MT3608B soft-start plus rail settling through the Q3 load-disconnect P-FET into C20/C22 (raised from 5 ms in the 2026-07 PCB review) — before reading, then drives it low immediately after. The transducer must also produce a valid output within that window: if its datasheet start-up (switch-on) time is longer, raise the option to match.

The ADS1115 measures the voltage across a shunt resistor on the loop return: PGA ±4.096 V, single-shot at 860 SPS, AIN0 vs GND. (20 mA × 100 Ω = 2.0 V would sit at the very top of the ±2.048 V range, which clips at 20.47 mA — too low to see the > 21 mA short-circuit fault.)

10 nF X7R bypass capacitors (C34 / C35) are placed directly across each 100 Ω shunt resistor (R2 / R4) to suppress HF pickup from the loop cable. The RC corner is ~160 kHz, well above the measurement bandwidth.

The loop signal terminals are protected by SMAJ5.0A TVS diodes (D9 / D10, 400 W, DO-214AC/SMA). The 5 V standoff (6.4 V minimum breakdown) keeps the 2.0 V working point far below the knee, so leakage stays negligible; Behind them, R3 / R5 (1 kΩ) and the D1 rail clamp protect the ADS1115 inputs: with the cable shorted, D9 holds the signal at ≈7–8 V while VLOOP is on, and 1 kΩ limits the current D1 dumps into +3V3 to ≈3.5 mA (with the earlier 100 Ω it was ≈40 mA, more than the LDO-fed rail can absorb). C3 / C5 (100 nF) form a filter with the shunt and the series resistor (τ = (R2 + R3)·C3 ≈ 110 µs, ≈1.45 kHz) that settles to 0.01 % in about 1 ms; C4 / C6 are DNP footprints (value `10uF DNF`) — fitting them would slow the input to τ ≈ 11 ms. The forward diode of the TVS clamps negative transients. (The earlier SMAJ3.3CA leaked up to 800 µA at its standoff — replaced 2026-07-14.)

The 1W DATA terminal (J6) is protected by D12, a PRTR5V0U2X dual-channel rail clamp in SOT-363 (the same part as D1 at the ADS1115 inputs). D12 clamps the data line to 3V3 + ~0.5 V during an ESD transient in sub-nanosecond response time. The added capacitance per channel is 0.5 pF, which is negligible compared to the 800 pF DS18B20 bus limit and does not affect 1-Wire timing.

### Battery monitoring

Battery voltage is read via the gated resistor divider (R7 100 kΩ / R8 100 kΩ) on ADS1115 AIN2. The divider is disconnected on the **high side** by Q5 (AO3407 P-FET) between VBAT and R7; GPIO15 drives the Q2 level-shifter (AO3400A) that pulls Q5's gate low. GPIO15 is pulsed HIGH for 1 ms (a busy-wait, exact at any tick rate) before reading, then LOW immediately after — C8 across R8 is 1 nF so the mid-node settles well inside that 1 ms window. With Q5 off the divider is completely dead: AIN2 rests at 0 V through R8, eliminating sleep leakage into the ADS1115 input ESD diodes. The divider ratio is 2.00 (200/100), mapping 4.2 V full charge to 2.1 V — the firmware reads AIN2 with the ADS1115 **±4.096 V** PGA (±2.048 V would clip right at full charge).

The BAT+ rail protection chain: **J1 BAT+ → D13 (SMAJ10CA TVS, at terminal) → D5 S→D (AO3407 reverse-polarity MOSFET) → VBAT system rail.**

D13 is a SMAJ5.0A unidirectional TVS (400 W, DO-214AC/SMA). Its 5 V standoff is above the 4.2 V 1S full-charge voltage so it does not conduct in normal operation; its forward diode clamps negative transients. Cable-induction surges are absorbed before they reach D5 and downstream circuits.

D5 (AO3407, SOT-23) is a P-channel MOSFET placed in series on BAT+. Its body diode blocks reverse current when the battery is connected with reversed polarity; in normal operation the MOSFET is on (Vgs = −Vbat — still twice the −1.5 V Vgs(th) max even at the 3.0 V 1S cutoff, though RDS(on) rises somewhat below the −4.5 V datasheet test point; the drop stays in the tens of millivolts at ≤1 A).

R31 (10 kΩ, 0402) connects D5's gate to GND. R31 holds Vgs = −Vbat so the MOSFET is unconditionally on whenever a battery is present, regardless of firmware state.

### Enclosure

The enclosure is **not designed yet** — the previous OpenSCAD case was deleted with the old PCB on 2026-05-25, and case work deliberately comes last because it consumes the final board outline and connector / test-point positions (see `hardware/pcb/fab_checklist.md`). Constraints already fixed: **no separate battery bay is needed** — the single 18650 lives in the top-side on-board carrier (BT1), so the case only has to clear ≈19–21 mm above the board. The external footprint follows the final board outline (unconstrained; working target ≈100 × 60 mm) and is sized at layout time. A USB-C slot on the left short wall accommodates the J13 connector (TP4056 charging **and** USB console/programming via the ESP32 native USB). The case dimensions consume the final board layout, so case work stays last.

The TP13 factory-reset pad must stay reachable with the lid off. (The old case's corner-wing mounting and 127 × 82 mm bolt pattern belonged to the deleted design and will be redone for the new outline.)

---

## Quickstart

### Prerequisites

- ESP-IDF **v6.0.1** installed and sourced — see the [Espressif getting-started guide](https://docs.espressif.com/projects/esp-idf/en/v6.0.1/esp32c6/get-started/)
- Custom PCB (or dev board — see legacy section below)

### Build and flash

```bash
git clone https://github.com/kinggh0stee/WellD.git
cd WellD

# one-time: select the target chip
idf.py set-target esp32c6

# local config — copy the template and edit it (gitignored; the root
# CMakeLists.txt layers it over sdkconfig.defaults). Defaults only seed a NEW
# sdkconfig — re-run `idf.py set-target esp32c6` after editing it.
cp sdkconfig.defaults.local.example sdkconfig.defaults.local
$EDITOR sdkconfig.defaults.local
idf.py set-target esp32c6

# build and flash
idf.py build
idf.py -p /dev/ttyACM0 flash monitor   # PCB USB-C (native USB); a dev board's UART port is usually /dev/ttyUSB0
```

Or use the interactive menu: `idf.py menuconfig` → **WellD Configuration**.

---

## Configuration

All options have sensible defaults. Only change what differs from your hardware.

### Sensor

| Option | Default | Description |
|--------|---------|-------------|
| `CONFIG_WELLD_SENSOR_SHUNT_MILLIOHMS` | `100000` | Loop shunt resistor value in milliohms (100 Ω = `100000`) |
| `CONFIG_WELLD_SENSOR_MAX_DEPTH_CM` | `600` | Full-scale depth at 20 mA, in cm |
| `CONFIG_WELLD_SENSOR_OFFSET_CM` | `0` | Level offset in cm applied after conversion (±600). Persisted in NVS; runtime-writable via `sensor_set_offset_cm()` |
| `CONFIG_WELLD_DS18B20_GPIO` | `7` | GPIO connected to DS18B20 data pin |

### Battery

| Option | Default | Description |
|--------|---------|-------------|
| `CONFIG_WELLD_BATT_REPORT_ENABLED` | `y` | Report battery voltage over Zigbee (EP2, Analog Input). The battery is always measured internally via ADS1115 AIN2 (R7/R8 divider) for the low-battery guard; disabling this only removes the Zigbee endpoint |
| `CONFIG_WELLD_BATT_DIVIDER_RATIO` | `200` | Divider ratio × 100 — matches the 100 kΩ / 100 kΩ divider (R7/R8): (100+100)/100 = 2.00 |
| `CONFIG_WELLD_BATT_FULL_MV` | `4200` | Voltage (mV) reported as 100 % by the Z2M converter (1S full charge) |
| `CONFIG_WELLD_BATT_EMPTY_MV` | `3200` | Voltage (mV) at or below which the device skips the Zigbee send and all NVS writes to protect flash. 3.2 V keeps the HT7333-fed 3.3 V rail ≥ 3.0 V (the ESP32-C6 minimum) under the TX burst; at a 3.0 V cell the rail sags to ≈2.9 V. Costs the last ≈5 % of capacity |

### Sleep

| Option | Default | Description |
|--------|---------|-------------|
| `CONFIG_WELLD_SLEEP_DURATION_SEC` | `300` | Baseline sleep between readings (seconds). When adaptive sleep is enabled, this is the "normal rate" window; the heavy-pumping band targets default/2 (integer division), so very short base values fall below `WELLD_SLEEP_MIN_SEC` and are clamped, making that band unreachable |
| `CONFIG_WELLD_ADAPTIVE_SLEEP_ENABLED` | `y` | Scale sleep duration to the observed level rate-of-change |
| `CONFIG_WELLD_SLEEP_MIN_SEC` | `60` | Lower bound on adaptive sleep (seconds) |
| `CONFIG_WELLD_SLEEP_MAX_SEC` | `1800` | Upper bound on adaptive sleep (seconds) |

### Zigbee

| Option | Default | Description |
|--------|---------|-------------|
| `CONFIG_WELLD_ZIGBEE_CHANNEL_MASK` | `0x07FFF800` | Channels to scan; narrow to your coordinator's channel to speed up joins |
| `CONFIG_WELLD_ZIGBEE_SEND_DELAY_MS` | `2000` | Time the stack stays alive after sending, to allow coordinator ACK |

### Hardware I/O

| Option | Default | Description |
|--------|---------|-------------|
| `CONFIG_WELLD_I2C_SDA_GPIO` | `18` | I²C SDA pin (ADS1115). GPIO10/11 unavailable on the MINI-1 module |
| `CONFIG_WELLD_I2C_SCL_GPIO` | `19` | I²C SCL pin (ADS1115) |
| `CONFIG_WELLD_VLOOP_GPIO` | `5` | MT3608B EN + Q3/Q4 load-disconnect — 12 V loop supply enable. Held HIGH for `CONFIG_WELLD_VLOOP_SETTLE_MS` before each 4–20 mA read, LOW right after |
| `CONFIG_WELLD_VLOOP_SETTLE_MS` | `10` | Loop warm-up before the reading (10–1000 ms). 10 ms covers the PCB's 12 V rail (it settles through the Q3 P-FET into C20/C22); raise it to the transducer's datasheet start-up / switch-on time if that is longer. Above 10 ms the firmware samples AIN0 once the rail is up and switches the loop straight off on a dead short (≥ 3.0 V) instead of holding it on for the whole warm-up |
| `CONFIG_WELLD_SOLAR_DETECT_GPIO` | `6` | Solar charger /CHRG (CN3791) — solar-charging-active detect (active-low) |
| `CONFIG_WELLD_BATT_DIV_EN_GPIO` | `15` | Battery-divider enable — Q2 level-shifter gate, switching the Q5 high-side P-FET |
| `CONFIG_WELLD_ADS1115_DRDY_GPIO` | `22` | ADS1115 ALERT/DRDY interrupt input (moved off GPIO12, now native USB D−) |

### Advanced / diagnostics

| Option | Default | Description |
|--------|---------|-------------|
| `CONFIG_WELLD_ADC_OVERSAMPLE_ENABLED` | `n` | Take 3 ADS1115 samples per measurement and report the median. Opt-in for electrically noisy installations (pump motor interference, long cable runs). Costs ~6 ms extra active time per wakeup (two extra ~1.2 ms conversions per channel); leave off for maximum battery life |
| `CONFIG_WELLD_TEMP_COMPENSATION_ENABLED` | `y` | Correct the level for water density: `level × ρ(ref) / ρ(T)`, with the pure-water density of Tanaka (2001). Water warmer than the reference is less dense, so the transducer reads low and the level is raised — by 0.03 % at 10 °C and 0.43 % at 30 °C for the default reference. Skipped when the DS18B20 fails and outside 0–40 °C |
| `CONFIG_WELLD_TEMP_COMPENSATION_REF_C` | `4` | Water temperature the transducer's metre scale assumes (0–40 °C). Nearly every datasheet uses the conventional metre of water column (9.80665 kPa = 1000 kg/m³, water at ≈4 °C), so leave 4 unless yours states e.g. "calibrated in 20 °C water". Replaces the linear `…_PPM_PER_C` coefficient (removed in 1.2.1) |
| `CONFIG_WELLD_DS18B20_RESOLUTION_BITS` | `11` | DS18B20 conversion resolution: 9 / 10 / 11 / 12 bit. Conversion wait: 100 / 200 / 400 / 800 ms (the ds18b20 driver's timing). 11-bit gives 0.125 °C steps — adequate for well water monitoring and saves 400 ms per wakeup vs 12-bit |
| `CONFIG_WELLD_FACTORY_RESET_GPIO` | `23` | If this GPIO is held LOW at boot, NVS and the Zigbee network state are erased and the device reboots factory-new — re-pair it with permit-join (moved off GPIO13, now native USB D+). Internal pull-up enabled; leave unconnected for normal operation |
| `CONFIG_WELLD_SELFTEST_ENABLED` | `n` | Exercise all peripherals on every boot and log PASS/FAIL. Adds ~200 ms to boot time; useful for factory QA and PCB bring-up |
| `CONFIG_WELLD_DIAGNOSTIC_MODE_ENABLED` | `n` | Stay awake for `WELLD_DIAGNOSTIC_STAY_AWAKE_SEC` after each sensor read, printing verbose logs. Deep sleep is still entered after the window expires |
| `CONFIG_WELLD_DIAGNOSTIC_STAY_AWAKE_SEC` | `60` | Stay-awake window when diagnostic mode is enabled (seconds, 10–300). Depends on `WELLD_DIAGNOSTIC_MODE_ENABLED` |
| `CONFIG_WELLD_ZIGBEE_BACKOFF_MAX_MS` | `500` | Random delay before the Zigbee stack starts commissioning on each wakeup (0–5000 ms). Jitters start time to avoid simultaneous joins from multiple devices after a power outage |
| `CONFIG_WELLD_OTA_STALL_TIMEOUT_SEC` | `240` | Abort an OTA download after this long without receiving a block (60–600 s). Measured since the last block — a full ~650 KB transfer takes many minutes and is never cut off while it is moving |
| `CONFIG_WELLD_RTC_LOG_PRINT_ENABLED` | `n` | Print RTC event log on wakeup — enable when diagnosing a retrieved device over USB; leave off in production |

---

## Zigbee2MQTT integration

### 1. Install the external converter (before pairing)

```bash
cp zigbee2mqtt/welld.js /opt/zigbee2mqtt/data/
```

Add it to `/opt/zigbee2mqtt/data/configuration.yaml`:

```yaml
external_converters:
  - welld.js
```

Restart Zigbee2MQTT:

```bash
sudo systemctl restart zigbee2mqtt
```

### 2. Pair the device

Enable permit-join in `configuration.yaml`, power up the board, and wait for the join. First pairing takes up to 25 s; subsequent wakeups resume the network in a few seconds from the state cached in the `zb_storage` partition (no permit-join needed). Disable permit-join once paired.

### 3. MQTT payload

The device publishes to `zigbee2mqtt/<friendly_name>` on each wakeup:

```json
{
  "water_level": 3.42,
  "water_level_rate": 12.5,
  "temperature": 12.3,
  "battery_voltage": 7.41,
  "battery": 59,
  "zb_fails": 0,
  "device_lqi": 156,
  "solar_charging": false
}
```

- `water_level` is `null` when the pressure loop reads below 3.5 mA (open circuit / broken wire) or above 21 mA (short circuit / shorted transducer). Trigger a Home Assistant alert on `water_level is null` to catch both fault conditions.
- `water_level_rate` is signed cm/h. Positive = recovering, negative = drawing down. Omitted on the first valid wakeup after a cold boot and during open-loop cycles.
- `temperature` is omitted when the DS18B20 is not detected.
- `battery_voltage` comes from the ADS1115 AIN2 voltage divider (R7/R8 100 kΩ / 100 kΩ, switched high-side by Q5 under GPIO15 control).
- `battery` is a percentage derived from `battery_voltage` using the device options `battery_full_mv` / `battery_empty_mv`. Options are coerced to numbers (YAML strings like `"4200"` are accepted) and fall back to the defaults 4200 / 3200 mV (matching the firmware's `CONFIG_WELLD_BATT_FULL_MV` / `CONFIG_WELLD_BATT_EMPTY_MV`) for anything missing or non-numeric. If the thresholds are misconfigured (`battery_full_mv <= battery_empty_mv`), the voltage is still published but the percentage is omitted. When the firmware cannot trust its battery reading (read failed, or below 2.0 V / above 125 % of full charge) it reports −1 and both `battery_voltage` and `battery` are published as `null`, so Home Assistant shows them unavailable — the low-battery guard is blind until the reading recovers.
- `zb_fails` is the number of consecutive failed send attempts that preceded this report (0 = healthy). From 3 failures the device sleeps its maximum interval between attempts until one succeeds.
- `device_lqi` is the link quality measured on the device side (EP6, 1–255) — the LQI of the device's parent entry in its own neighbor table. It is distinct from Zigbee2MQTT's own `linkquality` field, which comes from the coordinator side of the link. A value of 0 means "unknown" (no parent entry found) and is not published. Firmware ≤ 1.0.2 always sent 0, so the key only appears from firmware 1.0.3 onwards.
- `solar_charging` is a **boolean** (binary expose): `true` = the solar MPPT charger (CN3791) is actively charging, `false` = not charging.
- When previous sends failed, the buffered readings (up to 8, RTC store-and-forward) are burst-reported oldest-first before the current reading, so the coordinator receives the full history in order.
- The converter rejects malformed reports: any non-numeric or non-finite `presentValue` is dropped instead of being published.

### 4. Home Assistant

The Z2M–Home Assistant integration auto-creates these entities:

| Entity | Unit / values |
|--------|---------------|
| `sensor.<name>_water_level` | m |
| `sensor.<name>_water_level_rate` | cm/h |
| `sensor.<name>_temperature` | °C |
| `sensor.<name>_battery_voltage` | V |
| `sensor.<name>_battery` | % (omitted when `battery_full_mv <= battery_empty_mv`) |
| `sensor.<name>_zb_fails` | count, 0–255 |
| `sensor.<name>_device_lqi` | device-side LQI, 1–255 (needs firmware ≥ 1.0.3; 0 = unknown is never published) |
| `binary_sensor.<name>_solar_charging` | on / off |

---

## OTA firmware updates

The device runs a Zigbee OTA Upgrade client. Zigbee2MQTT (`ota: true` in the converter) distributes images automatically once placed in its OTA folder.

### 1. Bump the version

Edit `PROJECT_VER` in the root `CMakeLists.txt`:

```cmake
set(PROJECT_VER "1.0.2")   # MAJOR.MINOR.PATCH
```

The OTA file-version `0xMMmmPP00` (major << 24 | minor << 16 | patch << 8; e.g. `1.0.2` → `0x01000200`) is derived from `PROJECT_VER` at build time — **don't edit `OTA_FW_VERSION` directly.** The build fails loudly on a malformed `PROJECT_VER`.

### 2. Build the OTA image

After `idf.py build`, wrap the binary with the in-repo packer (stdlib Python; same file layout as esp-zigbee-sdk's `image_builder_tool`):

```bash
python tools/ota_image_create.py \
    --manufacturer-code 0x1234 \
    --image-type 0x0001 \
    --file-version 0x01000200 \
    --output welld-v1.0.2.zigbee \
    build/welld.bin
```

`--manufacturer-code` and `--image-type` **must** match the constants in `components/zigbee/zigbee.c` (`0x1234` / `0x0001`). The device rejects mismatched headers — don't wildcard them to `0xFFFF`.

`--file-version` must increase monotonically and match the `0xMMmmPP00` encoding of `PROJECT_VER`; the device only installs images with a higher version than the running one. (CI derives it automatically and packs `build/welld.ota.zigbee` on every build to prove the step works; the no-third-party-actions policy means it is not uploaded as an artifact.)

### 3. Deploy

```bash
cp welld-v1.0.2.zigbee /opt/zigbee2mqtt/data/ota/
```

List the file in a local OTA override index (`ota: zigbee_ota_override_index_location:` in Zigbee2MQTT's `configuration.yaml` — see the Zigbee2MQTT OTA documentation for the index format), then request the update for the device in the frontend. The device sends a Query Next Image request on every wakeup (a sleepy device can't be reached by an Image Notify), so the download starts on its next wakeup after the request; it arrives in ≤ 128-byte blocks — expect many minutes for a ~650 KB image — and the device reboots into the new firmware.

> **Upgrading from ≤ 1.0.2:** firmware 1.0.3 adds the battery endpoint (EP2) to the device descriptor. Zigbee2MQTT caches the endpoint list from the original interview, so after the OTA completes, re-interview the device (Z2M frontend → device → *Reconfigure/Interview*, or re-pair) to surface the new `battery_voltage` / `battery` entities. Also note the Kconfig option rename below — a stale `CONFIG_WELLD_BATT_ADC_CHANNEL=-1` line in `sdkconfig.defaults.local` is silently ignored; set `CONFIG_WELLD_BATT_REPORT_ENABLED=n` if you want battery reporting to stay off.

### OTA rollback guard

The firmware tracks consecutive boot failures in RTC memory. If 3 consecutive boots complete without a successful Zigbee send, the device automatically rolls back to the previous image in the **inactive OTA slot** (`esp_ota_get_next_update_partition()` — nothing in this app-level scheme ever marks the old slot invalid, so `esp_ota_get_last_invalid_partition()` would never fire). The rollback is skipped when the inactive slot holds no valid image (first flash), and the boot-attempt counter is cleared before the restart so the rolled-back image doesn't immediately bounce back to the broken slot. This prevents a bad OTA image from permanently bricking the device in the field.

---

## Operations

### Level offset calibration

Use `CONFIG_WELLD_SENSOR_OFFSET_CM` (or `sensor_set_offset_cm()` at runtime) to shift the reported level without moving the transducer. For example, if the transducer hangs 15 cm above the well bottom, set the offset to `+15` to report depth from the bottom of the well (`level = column above the transducer + offset`); use a negative offset when your zero point is above the transducer, e.g. `-50` when it hangs 50 cm below the outlet pipe you want to measure from.

The offset is persisted in NVS (key `offset_cm` in namespace `welld`) and clamped to ±600 cm.

### Adaptive sleep & rate of change

The device remembers its last valid reading and elapsed time in RTC slow memory (preserved across deep sleep, zeroed on cold boot). At each wakeup it computes a signed rate of change in cm/h and uses it to:

1. **Report `water_level_rate`** to Zigbee2MQTT.
2. **Adjust the next sleep duration** when `CONFIG_WELLD_ADAPTIVE_SLEEP_ENABLED=y`:

   | Rate (cm/h) | Sleep target | Interval at defaults | Condition |
   |-------------|--------------|----------------------|-----------|
   | 0 – 2       | max          | 1800 s | well at rest |
   | 2 – 5       | default × 2  | 600 s  | slow drawdown |
   | 5 – 10      | default      | 300 s  | active pumping |
   | 10 – 20     | default / 2  | 150 s  | heavy pumping |
   | ≥ 20        | min          | 60 s   | rapid event |

   The middle bands scale from `WELLD_SLEEP_DURATION_SEC` (integer division for the /2 band); the result is always clamped to `[WELLD_SLEEP_MIN_SEC, WELLD_SLEEP_MAX_SEC]`, so a very short base value makes the heavy-pumping band collapse into the minimum.

Set `CONFIG_WELLD_ADAPTIVE_SLEEP_ENABLED=n` for a fixed reporting cadence.

### Factory reset

Hold `CONFIG_WELLD_FACTORY_RESET_GPIO` (default GPIO23) LOW during boot to erase NVS (calibration offset, counters, cached DS18B20 ROM) and the Zigbee network state; the device reboots factory-new and joins again once permit-join is open on the coordinator. On the custom PCB, short the TP13 pad to GND (TP4) while powering on. The internal pull-up is enabled; leaving the pin unconnected causes normal operation. This is the only way the network state is erased — the device never wipes it on its own.

### I2C bus recovery

On every boot, `sensor_i2c_init()` checks whether SDA is stuck LOW (a common symptom of a previous aborted transaction). If SDA is LOW, it clocks 9 SCL pulses to force any stuck I2C slave to release the bus before initialising the I2C master. This is a no-op under normal conditions.

### Pre-sleep GPIO and I2C cleanup

Before every `esp_deep_sleep()` call, `sensor_pre_sleep_cleanup()` is invoked automatically. It removes the ADS1115 DRDY ISR (GPIO22), deletes the I2C semaphore, and releases the I2C bus handles for GPIO18 (SDA) and GPIO19 (SCL). Without this step the I2C driver retains ownership of those GPIOs across the sleep boundary; the driver context is invalid after wakeup and the bus can be left in a partially-driven state. Combined with `esp_sleep_gpio_isolate()`, all GPIOs are in a defined low-leakage state before the core powers down.

### Low-battery protection

When battery voltage drops **to or below** `CONFIG_WELLD_BATT_EMPTY_MV`, the device skips the Zigbee send and all NVS writes, and sleeps for the maximum interval to conserve charge. The rate history is invalidated entirely on this path — the level can drift arbitrarily far across a low-battery blackout, so the first valid reading after recovery re-seeds the history and reports no rate once (the EP4 report is skipped) instead of producing a false rate spike.

A reading **below 2.0 V** or **above 125 % of `CONFIG_WELLD_BATT_FULL_MV`** is not treated as a battery level at all: a running device cannot have such a cell (the DW01A disconnects it at 2.4 V and 4.3 V), so the measurement path has failed — divider not fitted (dev-board builds), Q5/R7 open or AIN2 floating (reads ≈0 V), or R8 open (AIN2 pulled to the clamp, ≈7 V). The device logs `battery reading … is implausible` (or `battery read failed` when the ADS1115 does not answer), records `BATT_INVALID` in the RTC event log, skips the low-battery guard and keeps reporting — with the battery published as `null` (unavailable) so the fault is visible remotely. Without the window, a missing divider would read a few mV of noise and silence the device for good, and an open R8 would disable the guard without any sign.

### Expected serial output

Normal cycle:

```
I (sensor): voltage=1485 mV  current=14850 µA  level=3.42 m
I (sensor): temperature=12.3 °C
I (sensor): battery=7.41 V (ADS1115 AIN2)
I (zigbee): joined; reporting level=3.42 m battery=7.41 V temp=12.3 °C rate=12.5 cm/h
I (main):   sleeping 300 s
```

Solar charging active:

```
I (main): solar charging active (solar /CHRG asserted)
```

No coordinator in range:

```
E (zigbee): timeout — no coordinator found
W (main):   Zigbee send failed (1 consecutive)
I (main):   sleeping 300 s
```

From the third consecutive failure the device backs off (`W (main): 3 consecutive send failures — backing off to 1800 s`) and keeps retrying at the maximum interval; its network membership is kept, so it resumes on its own when the coordinator is back.

Pressure transducer disconnected (open loop, < 3.5 mA):

```
E (sensor): transducer open loop (voltage=12 mV, 120 µA < 3.5 mA)
```

Pressure transducer short circuit (> 21 mA):

```
E (sensor): transducer short-circuit (voltage=2400 mV, 24000 µA > 21 mA)
```

DS18B20 ROM change (sensor replaced):

```
W (sensor): DS18B20 ROM changed: stored=28ff1234ab000002 active=28ff5678cd000003
```

---

## Power

The device spends nearly all of its time in deep sleep. Each wakeup is typically 6–12 seconds of active current (I²C reads, Zigbee send, 1-Wire conversion), followed by a sleep window of 1–30 minutes depending on rate-of-change. At the default 5-minute interval, average current is well under 1 mA — months of runtime on a single 18650 (3.6 V nominal, ≈3–3.4 Ah for a quality generic cell). The HT7333-A LDO's ≈4 µA quiescent current keeps the standby draw negligible, and the Q3/Q5 high-side disconnect switches leave no DC path from VBAT during sleep except the LDO and IC quiescents. Charging is dual-path: solar via the CN3791 MPPT charger and USB-C via the TP4056 (both autonomous — they charge whenever their input is present).

Both power-control GPIOs (VLOOP, BATT_DIV_EN) are driven low and the GPIO matrix is isolated (`esp_sleep_gpio_isolate()`) before every `esp_deep_sleep()` call to eliminate leakage through partially-driven outputs during sleep.

---

## Development

### Project layout

```
main/                    wakeup orchestration, NVS fail counter, RTC history
components/sensor/       I²C (ADS1115), DS18B20, GPIO power control
components/zigbee/       esp-zigbee-lib wrapper, OTA client, BDB commissioning task
components/welld_core/   pure helpers (rate-of-change, adaptive sleep, ZCL encoding)
zigbee2mqtt/welld.js     external converter for Zigbee2MQTT
hardware/pcb/            PCB design reference, BOM, Gerber generation script
hardware/case/           (planned) OpenSCAD enclosure — not created yet; designed after board layout
test/sensor/             on-device Unity tests (1-Wire, NVS round-trips)
test/welld_core/         on-device Unity tests (rate, sleep, ZCL helpers)
test/host/               host CMake test project — no ESP-IDF required
```

### Host tests

Pure helpers (`sensor_level_from_mv`, `sensor_battery_from_mv`, `sensor_temp_in_range`, `welld_*`) are exercised by a plain CMake project under `test/host/`:

```bash
cmake -S test/host -B test/host/build
cmake --build test/host/build
ctest --test-dir test/host/build --output-on-failure
```

CI runs these on every push. No ESP-IDF or hardware required.

### On-device tests

For NVS round-trips and 1-Wire / ADC paths the host runner can't cover:

```bash
idf.py -C test/sensor build flash monitor
idf.py -C test/welld_core build flash monitor
```

CI builds these to catch compile breaks but cannot execute them (real hardware needed).

### CI

`.github/workflows/build.yml` runs seven jobs:

- **ESP-IDF build** — v6.0.1, `esp32c6`, builds the firmware and packs the `.zigbee` OTA image with `tools/ota_image_create.py` (nothing is uploaded — no third-party actions)
- **ESP-IDF build variants** — matrix `features_on` / `features_off`: compiles the code behind non-default Kconfig options
- **C static analysis** — cppcheck over all `main/` and `components/` C sources; fails the build on any finding
- **Version bump check** — PR-only gate; fails if firmware sources changed without bumping `PROJECT_VER` in `CMakeLists.txt`
- **Host unit tests** — plain `ubuntu-latest`, ctest, fetches Unity v2.6.0
- **On-device test build** — compile-only check for `test/sensor` and `test/welld_core`
- **Z2M converter tests** — Node 20, `npm test` in `zigbee2mqtt/`

---

## Dev-board build (without the PCB)

The firmware has no ESP32-C6 internal-ADC path — every analog reading goes through the ADS1115. To build on an off-the-shelf ESP32-C6 dev board, follow **[`docs/wiring.md`](docs/wiring.md)**: an ADS1115 breakout on GPIO18/19 (address 0x48, ALERT on GPIO22), the transducer shunt into AIN0 through a 4.7 kΩ protection resistor with an externally powered loop, the DS18B20 on GPIO7, and either a 100 kΩ/100 kΩ battery divider on AIN2 or **AIN2 tied to GND** with `CONFIG_WELLD_BATT_REPORT_ENABLED=n` (a floating AIN2 can read like a flat cell and trip the low-battery guard). Leave the PCB-only GPIOs (5, 6, 15, 23) unconnected. The guide includes a wiring diagram, a net-by-net checklist and the log lines to expect on first boot.
