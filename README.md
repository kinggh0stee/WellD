# WellD

Battery-powered well-level monitor for the ESP32-C6. Each wakeup it reads a 4–20 mA submersible pressure transducer, a DS18B20 temperature probe, and battery voltage; reports them over Zigbee to Zigbee2MQTT; then deep-sleeps until the next cycle.

- **Radio:** Zigbee 3.0 over the C6's built-in 802.15.4 — no extra modules
- **Battery life:** months on a 2S1P 18650 pack at the default 5-minute interval (deep sleep between readings)
- **Adaptive sleep:** sleep duration scales with how fast the level is changing — longer windows when stable, shorter during transients
- **Rate-of-change reporting:** `water_level_rate` in cm/h; distinguishes "well recovering" from "well being drawn down"
- **Self-healing:** wipes Zigbee NVS state and rejoins fresh after 5 consecutive send failures
- **OTA:** Zigbee OTA Upgrade client, dual 1.5 MB app slots
- **Sentinels:** open-loop (< 3.5 mA) and short-circuit (> 21 mA) transducer faults both report `null` water level so Home Assistant can alert on wiring faults

---

## Hardware — Custom PCB

The current design is a purpose-built **100 × 55 mm** custom PCB. Design files, BOM, and assembly guide live in [`hardware/`](hardware/).

### Key ICs

| IC | Role |
|----|------|
| ESP32-C6 module | MCU + Zigbee radio |
| ADS1115 (0x48) | 16-bit I²C ADC — shunt voltage (AIN0) + battery divider (AIN2) |
| AP63203WU | 3.3 V **fixed** synchronous buck converter (22 µA Iq; VIN 3.8–32 V). Changed from the AP63205WU in the 2026-07-05 electrical review — the AP63205 is the 5 V fixed variant of the same family |
| MT3608B | 12 V **asynchronous** boost for the 4–20 mA loop supply (VLOOP, GPIO5-gated). D15 (SS34 Schottky) rectifies the switch node; a Q3/Q4 load-disconnect switch in series with L1 blocks the permanent VBAT leak to the loop terminals during deep sleep |
| CN3722 | MPPT solar charger (8.31 V CV via R33 = 590 kΩ; panel Voc limited to **24 V** by the SMAJ24CA input TVS) |
| TP5100 | USB-C charger — **currently non-functional as designed**: the TP5100 is a step-down charger and cannot charge the 8.4 V 2S pack from 5 V USB. IC replacement (5 V→2S boost charger) pending; do not rely on USB charging |

### Test points (production / field debug)

All 15 test point pads are 1.0 mm SMD, **DNF** (do not fit) — bare copper pads suitable for ICT fixture probes or a hook wire. No component is installed in production. Test points are placed scattered near their associated circuits rather than grouped in a single row, matching the 100 × 55 mm layout on a 1.0 mm grid.

| Ref | Net | Ref | Net |
|-----|-----|-----|-----|
| TP1 | VBAT (6.0–8.4 V, 2S range) | TP9 | I2C SCL |
| TP2 | VLOOP (12 V boost) | TP10 | VSOLAR_IN |
| TP3 | +3V3 | TP11 | VBAT_RAW (2S, before D5 reverse-polarity MOSFET) |
| TP4 | GND | TP12 | ADS1115 DRDY |
| TP5 | LOOP+ (LOOP_TERM_CH1) | TP13 | FACTORY_RESET (GPIO13 — short to GND while powering on) |
| TP6 | LOOP- (LOOP_TERM_CH2) | TP14 | /CHRG_SOLAR (CN3722 charge status) |
| TP7 | 1WIRE | TP15 | /CHRG_USB (TP5100 charge-status, with R38 pull-up) |
| TP8 | I2C SDA | | |

### Thermal improvements

The PCB includes a 10 × 10 mm solid GND copper pour on F.Cu and B.Cu centred on the CN3722 solar charger (U7), connected by four thermal vias (0.6 mm drill / 1.0 mm pad). This reduces the effective θJA during high-current solar charging and reduces the frequency of thermal fold-back. A GND via-stitch ring around the MT3608B / L1 boost island provides a low-inductance return path for the switching node without adding a solid pour under L1.

### GPIO map

| GPIO | Direction | Function |
|------|-----------|----------|
| 10 | SDA | I²C bus (ADS1115 only) |
| 11 | SCL | I²C bus (ADS1115 only) |
| 12 | Input  | ADS1115 ALERT/DRDY |
| 5  | Output | MT3608B EN + Q4 gate — 12 V loop supply (`VLOOP`), with Q3/Q4 load-disconnect; R27 pull-down holds it off during deep sleep |
| 4  | Output | TP5100 USB charger CE — HIGH enables USB-C charging (USB charging is currently non-functional at hardware level; TP5100 replacement pending) |
| 6  | Input  | CN3722 /CHRG — solar-charging-active detect (active-low: LOW = charging; R25 external pull-up) |
| 7  | 1-Wire | DS18B20 data |
| 13 | Input  | Factory reset only (hold LOW at boot → NVS erase + rejoin; field-accessible via TP13 pad) |
| 15 | Output | Battery-divider enable (`BATT_DIV_EN`) — drives the Q2 level-shifter that switches the Q5 high-side P-FET |
| 14 | —      | Status LED (D4 via R14/SJ3 — moved off GPIO13, which is reserved for factory reset; no firmware support yet) |

### Connections (screw terminals)

| Terminal | Wire | ESD / surge protection |
|----------|------|------------------------|
| LOOP+ / LOOP− | 4–20 mA transducer, two-wire | D9 / D10 SMAJ3.3CA bidirectional TVS (200 W, DO-214AC); D11 SMAJ13A unidirectional TVS on VLOOP; D1 PRTR5V0U2X rail clamp at ADS1115 inputs |
| 1W DATA / GND | DS18B20 data + ground | D12 PRTR5V0U2X dual-channel rail clamp (SOT-363) — 0.5 pF added capacitance, well below the 800 pF 1-Wire add limit |
| BAT+ / BAT−   | 2S1P 18650 pack (6.0–8.4 V) via **AMASS XT30PW-F** right-angle THT connector (J1, LCSC C601498; pin 1 = BAT+, pin 2 = BAT−) | D13 SMAJ10CA bidirectional TVS (200 W, DO-214AC) at terminal — 10 V standoff above 8.4 V full charge; D5 AO3407 P-ch MOSFET in series on BAT+ for reverse-polarity protection (RDS(on) max 55 mΩ); R31 10 kΩ gate-to-GND pull-down holds D5 in a defined on-state |
| SOLAR+/−      | Solar panel, ≤ **24 V Voc** (12 V-nominal panels, Voc ≈ 21–22 V, are fine) | D14 SMAJ24CA bidirectional TVS (400 W, DO-214AC) at the terminal, plus second-stage D8 SMAJ24CA at the CN3722 VIN. Was SMAJ28CA — 28 V standoff equalled the CN3722 absolute maximum, leaving zero clamp margin |

### RF / antenna

The ESP32-C6-MINI-1U-H4 module exposes a U.FL RF port. A ~50 mm internal pigtail — **Taoglas CAB.100.07.0050B** (U.FL female to SMA male, RG178 coax) — connects the module to **J3**, an **Amphenol 132289** SMD edge-launch SMA connector on the top board edge. PCBWay hand-attaches the pigtail after reflow. An external 2.4 GHz SMA antenna (e.g. Taoglas FXP73 rubber-duck, 2 dBi) screws directly onto J3.

### Assembly notes (PCBWay)

Connector placement on the 100 × 55 mm board:

- **Bottom edge (left to right):** J12 (solar, 2-pos), J4 (loop ch1, 3-pos), J5 (loop ch2, 3-pos), J6 (DS18B20, 3-pos), J7 (spare sensor, 3-pos), J10 (programming header, 6-pin 1.27 mm pitch)
- **Left edge:** J1 (XT30PW-F battery connector, right-angle THT) and J13 (USB-C charging input, SMD)
- **Top edge:** J3 (Amphenol 132289 SMA edge-launch)

- **J4, J5, J6, J7, J12** — Phoenix Contact MC 1.5/x-G-3.5 THT terminal blocks, wave-soldered.
- **J10** — 1.27 mm pitch THT vertical programming header (6-pin), wave-soldered.
- **J8, J9** (expansion headers) — **DNF** (do not populate) on all production boards. Footprints are present on the PCB for future use; no components are installed.
- **J3** pigtail — hand-attached by PCBWay post-reflow; not wave-soldered.

### 4–20 mA loop

The MT3608B boost converter lifts VLOOP to 12 V to power the transducer loop. The boost is asynchronous: D15 (SS34 Schottky) carries the switch node to VLOOP, and a Q3 (P-FET) / Q4 (level-shifter) load-disconnect switch in series with the inductor prevents VBAT from leaking through L1 + D15 to the loop terminals during deep sleep. GPIO5 drives both the MT3608B EN and the Q4 gate; R27 pulls the net low while GPIO5 is isolated in deep sleep.

Firmware gates GPIO5 high for **10 ms** (MT3608B soft-start plus rail settling through the Q3 load-disconnect P-FET into C20/C22 — raised from 5 ms in the 2026-07 PCB review) before reading, then drives it low immediately after. Maximum ON time is 100 ms.

The ADS1115 measures the voltage across a shunt resistor on the loop return. PGA ±2.048 V, single-shot at 860 SPS, AIN0 vs GND.

10 nF X7R bypass capacitors (C_SH1 / C_SH2) are placed directly across each 100 Ω shunt resistor (R2 / R4) to suppress HF pickup from the loop cable. The RC corner is ~1.6 MHz, well above the measurement bandwidth.

LOOP+ and LOOP– screw terminals are protected by SMAJ3.3CA bidirectional TVS diodes (D9 / D10, 200 W, DO-214AC/SMA). The 3.3 V standoff is above the normal 2 V loop maximum so the TVS does not conduct in normal operation; the ~5.3 V clamp at 10 A provides tighter protection for the ADS1115 AIN absolute-maximum chain than the previous SMAJ5.0CA devices.

The 1W DATA terminal (J6) is protected by D12, a PRTR5V0U2X dual-channel rail clamp in SOT-363 (the same part as D1 at the ADS1115 inputs). D12 clamps the data line to 3V3 + ~0.5 V during an ESD transient in sub-nanosecond response time. The added capacitance per channel is 0.5 pF, which is negligible compared to the 800 pF DS18B20 bus limit and does not affect 1-Wire timing.

### Battery monitoring

Battery voltage is read via the gated resistor divider (R7 330 kΩ / R8 100 kΩ) on ADS1115 AIN2. The divider is disconnected on the **high side** by Q5 (AO3407 P-FET) between VBAT and R7; GPIO15 drives the Q2 level-shifter (BSS123) that pulls Q5's gate low. GPIO15 is pulsed HIGH for 1 ms before reading, then LOW immediately after — C8 across R8 was reduced to 1 nF so the mid-node settles well inside that 1 ms window. With Q5 off the divider is completely dead: AIN2 rests at 0 V through R8, eliminating the ~14 µA sleep leakage that the previous low-side switch pushed into the ADS1115 input ESD diodes. The divider ratio is 4.30 (430/100), mapping 8.4 V full charge to approximately 1.95 V — within the ADS1115 ±2.048 V PGA range.

The BAT+ rail protection chain: **J1 BAT+ → D13 (SMAJ10CA TVS, at terminal) → D5 S→D (AO3407 reverse-polarity MOSFET) → VBAT system rail.**

D13 is a SMAJ10CA bidirectional TVS (200 W, DO-214AC/SMA). Its 10 V standoff is above the 8.4 V 2S full-charge voltage so it does not conduct in normal operation. Cable-induction surges are absorbed before they reach D5 and downstream circuits.

D5 (AO3407, SOT-23) is a P-channel MOSFET placed in series on BAT+. Its body diode blocks reverse current when the battery is connected with reversed polarity; in normal operation the MOSFET is fully on (Vgs = −Vbat, saturated well above the −1.5 V Vgs(th) max at any 2S voltage down to 6.0 V) with a drop of at most 55 mV at 1 A.

R31 (10 kΩ, 0402) connects D5's gate to GND. R31 holds Vgs = −Vbat so the MOSFET is unconditionally on whenever a battery is present, regardless of firmware state.

### Enclosure

The enclosure is designed in [`hardware/case/welld_case.scad`](hardware/case/welld_case.scad). External footprint is **105 × 60 mm** (2.5 mm wall on each side of the 100 × 55 mm PCB). The battery bay is sized for the Sinowatt GR 3350 mAh 2S1P 18650 rectangular pack (41 × 71 × 22 mm) with corner locating posts and hook-and-loop strap slots through the side walls. A USB-C slot on the left short wall accommodates the J13 charging connector (TP5100 USB-C charging input — note that USB charging is currently non-functional at hardware level; the TP5100 replacement is pending).

For concrete underside mounting, the lid grows four corner wings with M6 anchor-bolt clearance holes. The bolt pattern centre-to-centre span is **127 × 82 mm** (X × Y). Use the `drill_template()` module to print a 1:1 paper/card drill guide before installing anchor bolts.

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

# local config — copy the template and edit it (gitignored)
cp sdkconfig.defaults.local.example sdkconfig.defaults.local
$EDITOR sdkconfig.defaults.local

# build and flash
idf.py build
idf.py -p /dev/ttyUSB0 flash monitor
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
| `CONFIG_WELLD_BATT_ADC_CHANNEL` | `-1` | ADS1115 channel for battery voltage. `-1` (default) disables battery monitoring and Zigbee EP2 entirely; set to `2` for the custom PCB (AIN2 via the R7/R8 divider) |
| `CONFIG_WELLD_BATT_DIVIDER_RATIO` | `430` | Divider ratio × 100 — matches 330 kΩ / 100 kΩ divider (R7/R8) scaled for 2S: (330+100)/100 = 4.30 |
| `CONFIG_WELLD_BATT_FULL_MV` | `8400` | Voltage (mV) reported as 100 % by the Z2M converter (2S full charge) |
| `CONFIG_WELLD_BATT_EMPTY_MV` | `6000` | Voltage (mV) at or below which the device skips the Zigbee send and all NVS writes to protect flash (2S minimum safe discharge) |

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
| `CONFIG_WELLD_I2C_SDA_GPIO` | `10` | I²C SDA pin (ADS1115) |
| `CONFIG_WELLD_I2C_SCL_GPIO` | `11` | I²C SCL pin |
| `CONFIG_WELLD_VLOOP_GPIO` | `5` | MT3608B EN + Q3/Q4 load-disconnect — 12 V loop supply enable. Held HIGH ≥ 10 ms before any 4–20 mA read (rail settles through the Q3 P-FET into C20/C22) |
| `CONFIG_WELLD_SOLAR_DETECT_GPIO` | `6` | CN3722 /CHRG — solar-charging-active detect (active-low) |
| `CONFIG_WELLD_USB_CHG_GPIO` | `4` | TP5100 USB charger CE (active-HIGH; R37 passively holds it LOW during deep sleep). USB charging is currently non-functional at hardware level — TP5100 replacement pending |
| `CONFIG_WELLD_BATT_DIV_EN_GPIO` | `15` | Battery-divider enable — Q2 level-shifter gate, switching the Q5 high-side P-FET |
| `CONFIG_WELLD_ADS1115_DRDY_GPIO` | `12` | ADS1115 ALERT/DRDY interrupt input (open-drain, falling edge = conversion complete) |

### Advanced / diagnostics

| Option | Default | Description |
|--------|---------|-------------|
| `CONFIG_WELLD_ADC_OVERSAMPLE_ENABLED` | `n` | Take 3 ADS1115 samples per measurement and report the median. Opt-in for electrically noisy installations (pump motor interference, long cable runs). Costs ~8 ms extra active time per wakeup; leave off for maximum battery life |
| `CONFIG_WELLD_TEMP_COMPENSATION_ENABLED` | `y` | Apply water-density correction to the level reading: `level / (1 + alpha * (temp - 20))`. Suppressed automatically when DS18B20 fails (temp ≤ −127 °C) |
| `CONFIG_WELLD_TEMP_COMPENSATION_PPM_PER_C` | `207` | Water density coefficient in ppm/°C. Depends on `WELLD_TEMP_COMPENSATION_ENABLED`. Typical value for fresh water is 207 ppm/°C; range 0–500 |
| `CONFIG_WELLD_DS18B20_RESOLUTION_BITS` | `11` | DS18B20 conversion resolution: 9 / 10 / 11 / 12 bit. Conversion time: 94 / 188 / 375 / 750 ms. 11-bit gives 0.0625 °C steps — adequate for well water monitoring and saves 375 ms per wakeup vs 12-bit |
| `CONFIG_WELLD_FACTORY_RESET_GPIO` | `13` | If this GPIO is held LOW at boot, NVS is erased and the device rejoins Zigbee fresh. Internal pull-up enabled; leave unconnected for normal operation |
| `CONFIG_WELLD_SELFTEST_ENABLED` | `n` | Exercise all peripherals on every boot and log PASS/FAIL. Adds ~200 ms to boot time; useful for factory QA and PCB bring-up |
| `CONFIG_WELLD_DIAGNOSTIC_MODE_ENABLED` | `n` | Stay awake for `WELLD_DIAGNOSTIC_STAY_AWAKE_SEC` after each sensor read, printing verbose logs. Deep sleep is still entered after the window expires |
| `CONFIG_WELLD_DIAGNOSTIC_STAY_AWAKE_SEC` | `60` | Stay-awake window when diagnostic mode is enabled (seconds, 10–300). Depends on `WELLD_DIAGNOSTIC_MODE_ENABLED` |
| `CONFIG_WELLD_ZIGBEE_BACKOFF_MAX_MS` | `500` | Random delay before Zigbee network steering on each wakeup (0–5000 ms). Jitters start time to avoid simultaneous steering from multiple devices after a power outage |
| `CONFIG_WELLD_OTA_STALL_TIMEOUT_SEC` | `240` | Maximum wall-clock time an OTA download may take before it is considered stalled and aborted (60–600 s) |
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

Enable permit-join in `configuration.yaml`, power up the board, and wait for the join. First pairing takes up to 25 s; subsequent wakeups rejoin in a few seconds using cached network state in NVS. Disable permit-join once paired.

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
  "linkquality": 156,
  "solar_charging": false
}
```

- `water_level` is `null` when the pressure loop reads below 3.5 mA (open circuit / broken wire) or above 21 mA (short circuit / shorted transducer). Trigger a Home Assistant alert on `water_level is null` to catch both fault conditions.
- `water_level_rate` is signed cm/h. Positive = recovering, negative = drawing down. Omitted on the first valid wakeup after a cold boot and during open-loop cycles.
- `temperature` is omitted when the DS18B20 is not detected.
- `battery_voltage` comes from the ADS1115 AIN2 voltage divider (R7 330 kΩ / R8 100 kΩ, switched high-side by Q5 under GPIO15 control).
- `battery` is a percentage derived from `battery_voltage` using the device options `battery_full_mv` / `battery_empty_mv`. Options are coerced to numbers (YAML strings like `"8400"` are accepted) and fall back to the defaults 8400 / 6000 mV for anything missing or non-numeric. If the thresholds are misconfigured (`battery_full_mv <= battery_empty_mv`), the voltage is still published but the percentage is omitted.
- `zb_fails` counts consecutive Zigbee send failures since the last success (0 = healthy; the device auto-rejoins at 5).
- `solar_charging` is a **boolean** (binary expose): `true` = the CN3722 MPPT charger is actively charging, `false` = not charging.
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
| `sensor.<name>_linkquality` | LQI, 0–255 |
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

After `idf.py build`, wrap the binary using `ota_image_create.py` from the esp-zigbee-sdk:

```bash
python path/to/ota_image_create.py \
    --manufacturer-code 0x1234 \
    --image-type 0x0001 \
    --file-version 0x01000200 \
    --output welld-v1.0.2.zigbee \
    build/welld.bin
```

`--manufacturer-code` and `--image-type` **must** match the constants in `components/zigbee/zigbee.c` (`0x1234` / `0x0001`). The device rejects mismatched headers — don't wildcard them to `0xFFFF`.

`--file-version` must increase monotonically and match the `0xMMmmPP00` encoding of `PROJECT_VER`; the device only installs images with a higher version than the running one. (CI derives it automatically and uploads the packed `.zigbee` file as a build artifact.)

### 3. Deploy

```bash
cp welld-v1.0.2.zigbee /opt/zigbee2mqtt/data/ota/
```

Zigbee2MQTT picks the file up automatically. On the next wakeup the device queries for an update, downloads it in 128-byte blocks over Zigbee, and reboots into the new firmware.

### OTA rollback guard

The firmware tracks consecutive boot failures in RTC memory. If 3 consecutive boots complete without a successful Zigbee send, the device automatically rolls back to the previous image in the **inactive OTA slot** (`esp_ota_get_next_update_partition()` — nothing in this app-level scheme ever marks the old slot invalid, so `esp_ota_get_last_invalid_partition()` would never fire). The rollback is skipped when the inactive slot holds no valid image (first flash), and the boot-attempt counter is cleared before the restart so the rolled-back image doesn't immediately bounce back to the broken slot. This prevents a bad OTA image from permanently bricking the device in the field.

---

## Operations

### Level offset calibration

Use `CONFIG_WELLD_SENSOR_OFFSET_CM` (or `sensor_set_offset_cm()` at runtime) to shift the reported level without moving the transducer. For example, if the transducer hangs 15 cm above the well bottom, set the offset to `-15` to report depth from the bottom of the well.

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

Hold `CONFIG_WELLD_FACTORY_RESET_GPIO` (default GPIO13) LOW during boot to erase NVS and force a clean Zigbee rejoin. On the custom PCB, short the TP13 pad to GND (TP4) while powering on. The internal pull-up is enabled; leaving the pin unconnected causes normal operation. This is the same NVS erase that occurs automatically after 5 consecutive Zigbee send failures.

### I2C bus recovery

On every boot, `sensor_i2c_init()` checks whether SDA is stuck LOW (a common symptom of a previous aborted transaction). If SDA is LOW, it clocks 9 SCL pulses to force any stuck I2C slave to release the bus before initialising the I2C master. This is a no-op under normal conditions.

### Pre-sleep GPIO and I2C cleanup

Before every `esp_deep_sleep()` call, `sensor_pre_sleep_cleanup()` is invoked automatically. It removes the ADS1115 DRDY ISR (GPIO12), deletes the I2C semaphore, and releases the I2C bus handles for GPIO10 (SDA) and GPIO11 (SCL). Without this step the I2C driver retains ownership of those GPIOs across the sleep boundary; the driver context is invalid after wakeup and the bus can be left in a partially-driven state. Combined with `esp_sleep_gpio_isolate()`, all GPIOs are in a defined low-leakage state before the core powers down.

### Low-battery protection

When battery voltage drops **to or below** `CONFIG_WELLD_BATT_EMPTY_MV`, the device skips the Zigbee send and all NVS writes, and sleeps for the maximum interval to conserve charge. The rate history is invalidated entirely on this path — the level can drift arbitrarily far across a low-battery blackout, so the first valid reading after recovery re-seeds the history and reports no rate once (the EP4 report is skipped) instead of producing a false rate spike.

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
I (main): solar charging active (CN3722 /CHRG asserted)
```

No coordinator in range:

```
E (zigbee): timeout — no coordinator found
W (main):   Zigbee send failed (1/5)
I (main):   sleeping 300 s
```

After 5 consecutive failures the NVS partition is erased on the next boot, forcing a clean Zigbee rejoin.

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

The device spends nearly all of its time in deep sleep. Each wakeup is typically 6–12 seconds of active current (I²C reads, Zigbee send, 1-Wire conversion), followed by a sleep window of 1–30 minutes depending on rate-of-change. At the default 5-minute interval, average current is well under 1 mA — months of runtime on the 2S1P 18650 pack (7.2 V nominal, 3350 mAh). The AP63203 buck converter's 22 µA quiescent current keeps the standby draw negligible, and the Q3/Q5 high-side disconnect switches leave no DC path from VBAT during sleep except the buck and IC quiescents. Charging is effectively solar-only via the CN3722 MPPT charger: the USB-C path (TP5100) is currently non-functional at hardware level and awaits an IC replacement.

All power-control GPIOs (VLOOP, BATT_DIV_EN, USB_CHG CE) are driven low and the GPIO matrix is isolated (`esp_sleep_gpio_isolate()`) before every `esp_deep_sleep()` call to eliminate leakage through partially-driven outputs during sleep.

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
hardware/case/           OpenSCAD parametric enclosure (2S1P 18650 battery bay)
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

`.github/workflows/build.yml` runs six jobs:

- **ESP-IDF build** — v6.0.1, `esp32c6`, builds firmware and OTA image, uploads `*.bin`, `*.elf`, `*.map`, `*.zigbee`, `dependencies.lock`
- **C static analysis** — cppcheck over all `main/` and `components/` C sources; fails the build on any finding
- **Version bump check** — PR-only gate; fails if firmware sources changed without bumping `PROJECT_VER` in `CMakeLists.txt`
- **Host unit tests** — plain `ubuntu-latest`, ctest, fetches Unity v2.6.0
- **On-device test build** — compile-only check for `test/sensor` and `test/welld_core`
- **Z2M converter tests** — Node 20, `npm test` in `zigbee2mqtt/`

---

## Legacy: dev board wiring

If building from an off-the-shelf ESP32-C6 dev board instead of the custom PCB, wire the pressure transducer shunt directly to an ADC1 pin and power the loop externally. The ADS1115 and MT3608B boost are not available on a bare dev board — configure `CONFIG_WELLD_SENSOR_ADC_CHANNEL` to the ESP ADC channel used and leave `CONFIG_WELLD_BATT_ADC_CHANNEL` at its default of `-1` (battery monitoring disabled). The power-control GPIO options (`VLOOP`, `BATT_DIV_EN`) are still compiled in but can be left disconnected if the solar charger is absent.
