# WellD

Battery-powered well-level monitor for the ESP32-C6. Each wakeup it reads a 4–20 mA submersible pressure transducer, a DS18B20 temperature probe, and battery voltage; reports them over Zigbee to Zigbee2MQTT; then deep-sleeps until the next cycle.

- **Radio:** Zigbee 3.0 over the C6's built-in 802.15.4 — no extra modules
- **Battery life:** months on a single-cell LiPo at the default 5-minute interval (deep sleep between readings)
- **Adaptive sleep:** sleep duration scales with how fast the level is changing — longer windows when stable, shorter during transients
- **Rate-of-change reporting:** `water_level_rate` in cm/h; distinguishes "well recovering" from "well being drawn down"
- **Self-healing:** wipes Zigbee NVS state and rejoins fresh after 5 consecutive send failures
- **OTA:** Zigbee OTA Upgrade client, dual 1.5 MB app slots
- **Sentinels:** open-loop (< 3.5 mA) and short-circuit (> 21 mA) transducer faults both report `null` water level so Home Assistant can alert on wiring faults

---

## Hardware — Custom PCB

The current design is a purpose-built **80 × 55 mm** custom PCB. Design files, BOM, and assembly guide live in [`hardware/`](hardware/).

### Key ICs

| IC | Role |
|----|------|
| ESP32-C6 module | MCU + Zigbee radio |
| ADS1115 (0x48) | 16-bit I²C ADC — shunt voltage (AIN0) + battery divider (AIN2) |
| MAX17048 (0x36) | Fuel-gauge IC — primary battery voltage & state-of-charge via I²C |
| TPS61023 | 12 V synchronous boost for the 4–20 mA loop supply (VLOOP, GPIO5) |
| CN3791 | MPPT solar charger |
| TP4056 | USB Li-ion charger with dual-charger interlock via BSS123 Q1 (GPIO4 software) and BSS84 Q3 (hardware, /CHRG_SOLAR) |
| S-8261AAYFT | Single-cell over-discharge protection (2.9 V cutoff) |

### Decoupling additions

| Ref | Value | IC bypassed | Notes |
|-----|-------|-------------|-------|
| C25 | 100 nF 0402 X7R | MAX17048 (U10) VDD | Required by datasheet; previously absent |
| C26 | 100 nF 0402 X7R | S-8261AAYFT (U3) VCC | Required by datasheet; previously absent |

### Test points (production / field debug)

All 14 test point pads are 1.0 mm SMD, **DNF** (do not fit) — bare copper pads suitable for ICT fixture probes or a hook wire. No component is installed in production.

| Ref | Net | Ref | Net |
|-----|-----|-----|-----|
| TP1 | VBAT | TP8 | I2C SDA |
| TP2 | VLOOP | TP9 | I2C SCL |
| TP3 | +3V3 | TP10 | VSOLAR_IN |
| TP4 | GND | TP11 | VBAT_RAW |
| TP5 | LOOP+ (LOOP_TERM_CH1) | TP12 | ADS1115 DRDY |
| TP6 | LOOP- (LOOP_TERM_CH2) | TP13 | MAX17048 ALRT |
| TP7 | 1WIRE | TP14 | /CHRG_SOLAR |

### Thermal improvements

The PCB now includes a 10 × 10 mm solid GND copper pour on F.Cu and B.Cu centred on the CN3791 solar charger (U7), connected by four thermal vias (0.6 mm drill / 1.0 mm pad). This reduces the effective θJA during high-current solar charging and reduces the frequency of thermal fold-back. A GND via-stitch ring around the TPS61023 / L1 boost island provides a low-inductance return path for the switching node without adding a solid pour under L1.

### GPIO map

| GPIO | Direction | Function |
|------|-----------|----------|
| 10 | SDA | I²C bus (ADS1115 + MAX17048) |
| 11 | SCL | I²C bus |
| 12 | Input  | ADS1115 ALERT/DRDY |
| 5  | Output | TPS61023 EN — 12 V loop supply (`VLOOP`) |
| 4  | Output | TP4056 CE interlock — disable USB charger when solar is active |
| 6  | Input  | CN3791 CHRG — solar-charging-active detect (active-low: LOW = charging) |
| 7  | 1-Wire | DS18B20 data |
| 15 | Output | Battery-divider enable gate (`BATT_DIV_EN`) |
| 14 | Input  | MAX17048 ALRT (active-low open-drain; R27 pull-up to 3V3) |

### Connections (screw terminals)

| Terminal | Wire | ESD / surge protection |
|----------|------|------------------------|
| LOOP+ / LOOP− | 4–20 mA transducer, two-wire | D9 / D10 SMAJ3.3CA bidirectional TVS (200 W, DO-214AC); D11 SMAJ13A unidirectional TVS on VLOOP; D1 PRTR5V0U2X rail clamp at ADS1115 inputs |
| 1W DATA / GND | DS18B20 data + ground | D12 PRTR5V0U2X dual-channel rail clamp (SOT-363) — 0.5 pF added capacitance, well below the 800 pF 1-Wire add limit |
| BAT+ / BAT−   | Single-cell LiPo / 18650 | D13 SMAJ5.0CA bidirectional TVS (200 W, DO-214AC) at terminal; D5 AO3407 P-ch MOSFET in series on BAT+ for reverse-polarity protection (RDS(on) max 55 mΩ); R31 10 kΩ gate-to-GND pull-down holds D5 in a defined on-state |
| SOLAR+/−      | Optional solar panel (5–6 V, 1 W) | D14 SMAJ7.0A unidirectional TVS (400 W, DO-214AC) — 7.0 V standoff, below CN3791 7.5 V absolute maximum |
| USB-C          | Charging / flashing | U5 USBLC6-2SC6 on-board USB ESD clamp |

### 4–20 mA loop

The TPS61023 boost converter lifts VLOOP to 12 V to power the transducer loop. Firmware gates EN high for ≥ 5 ms (soft-start) before reading, then drives it low immediately after. Maximum ON time is 100 ms.

The ADS1115 measures the voltage across a shunt resistor on the loop return. PGA ±2.048 V, single-shot at 860 SPS, AIN0 vs GND.

10 nF X7R bypass capacitors (C_SH1 / C_SH2) are placed directly across each 100 Ω shunt resistor (R2 / R4) to suppress HF pickup from the loop cable. The RC corner is ~1.6 MHz, well above the measurement bandwidth.

LOOP+ and LOOP– screw terminals are protected by SMAJ3.3CA bidirectional TVS diodes (D9 / D10, 200 W, DO-214AC/SMA). The 3.3 V standoff is above the normal 2 V loop maximum so the TVS does not conduct in normal operation; the ~5.3 V clamp at 10 A provides tighter protection for the ADS1115 AIN absolute-maximum chain than the previous SMAJ5.0CA devices.

The 1W DATA terminal (J6) is protected by D12, a PRTR5V0U2X dual-channel rail clamp in SOT-363 (the same part as D1 at the ADS1115 inputs). D12 clamps the data line to 3V3 + ~0.5 V during an ESD transient in sub-nanosecond response time. The added capacitance per channel is 0.5 pF, which is negligible compared to the 800 pF DS18B20 bus limit and does not affect 1-Wire timing.

### Battery monitoring

MAX17048 is the primary source (coulomb-counted VCELL and SOC registers read over I²C). If not present, firmware falls back to the gated voltage divider on ADS1115 AIN2.

The BAT+ rail has a two-layer protection chain: **J1 BAT+ → D13 (SMAJ5.0CA TVS, at terminal) → D5 S→D (AO3407 reverse-polarity MOSFET) → VBAT system rail.**

D13 is a SMAJ5.0CA bidirectional TVS (200 W, DO-214AC/SMA). Its 5.0 V standoff is above the 4.2 V Li-Ion full-charge voltage so it does not conduct in normal operation. The ~9.2 V clamp at 10 A absorbs cable-induction surges before they reach D5, the S-8261AAYFT protection IC, and downstream circuits.

D5 (AO3407, SOT-23) is a P-channel MOSFET placed in series on BAT+. Its body diode blocks reverse current when the battery is connected with reversed polarity; in normal operation the MOSFET is fully on (Vgs = −Vbat, saturated well above the −1.5 V Vgs(th) max at any battery voltage down to 3.0 V) with a drop of at most 55 mV at 1 A. A series diode was explicitly rejected: a 300 mV forward drop would shift the VBAT measurement seen by both the MAX17048 fuel gauge and the ADS1115 battery-divider path, corrupting the S-8261AAYFT 2.9 V over-discharge cutoff reference. The AO3407 drop at ≤55 mV @ 1 A is within measurement uncertainty and requires no calibration adjustment.

R31 (10 kΩ, 0402) connects D5's gate to GND. Without this pull-down the gate floats on cold-start and during hot-plug, leaving D5 in an undefined state. R31 holds Vgs = −Vbat so the MOSFET is unconditionally on whenever a battery is present, regardless of firmware state.

### Dual-charger interlock

Two layers prevent simultaneous dual-charger operation:

1. **Hardware (Q3 BSS84, R30)** — Q3 is a P-channel MOSFET wired so that the CN3791 /CHRG_SOLAR open-drain signal directly drives the TP4056 CE line. When /CHRG_SOLAR is pulled low (solar charging active), Q3 conducts and holds TP4056 CE low, disabling USB charging without any firmware involvement. This eliminates the boot-window race before firmware asserts GPIO4.

2. **Firmware (Q1 BSS123, GPIO4)** — CN3791 CHRG (GPIO6) is active-low: the firmware reads LOW as solar charging active and responds by driving GPIO4 high to disable the TP4056 USB charger via Q1. HIGH on GPIO6 means no solar charging. The firmware layer reinforces the hardware interlock at runtime.

The SOLAR+ terminal (J12) is protected by D14, a SMAJ7.0A unidirectional TVS (400 W, DO-214AC/SMA). Its 7.0 V standoff is above the 6.5 V maximum MPPT operating voltage so it does not conduct in normal operation. D14 is the first stage of a two-stage protection chain: it absorbs the bulk of a cable-induced transient at J12 before it reaches D8 (a second SMAJ7.0A placed across CN3791 VIN after D6). Both devices use the same MPN and can be sourced from a single tape reel.

### Enclosure

Two variants in [`hardware/case/welld_case.scad`](hardware/case/welld_case.scad):

- **Default** — sized for the PCB with a single-cell (18650) battery in the base.
- **2S variant** — set `USE_2S_BATTERY = true` in the SCAD file to add a deeper battery bay (73 × 40 × 22 mm, e.g. CS-ARS200SL 2S1P 7.4 V 3400 mAh) with corner locating posts and hook-and-loop strap slots through the side walls.

> **⚠ 2S electrical warning:** The 2S battery variant requires hardware modifications to the PCB. The TPS7A0533 LDO (abs-max 6.5 V), CN3791 (max 6 V input), and TP4056 (max 8 V input) are all rated below the 2S pack's 8.4 V charge voltage. Do not connect a 2S pack without replacing U1, U2, U7, and U3 with 2S-rated equivalents. The enclosure design is provided for convenience only.

---

## Quickstart

### Prerequisites

- ESP-IDF **v5.5.4** installed and sourced — see the [Espressif getting-started guide](https://docs.espressif.com/projects/esp-idf/en/v5.5.4/esp32c6/get-started/)
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
| `CONFIG_WELLD_BATT_ADC_CHANNEL` | `-1` | ADS1115 channel for battery divider fallback; `-1` to disable ADC fallback (MAX17048 only) |
| `CONFIG_WELLD_BATT_DIVIDER_RATIO` | `200` | Divider ratio × 100 for the ADS1115 fallback path |
| `CONFIG_WELLD_BATT_FULL_MV` | `4200` | Voltage (mV) reported as 100 % by the Z2M converter |
| `CONFIG_WELLD_BATT_EMPTY_MV` | `3000` | Voltage (mV) below which the device skips the Zigbee send to protect NVS |

### Sleep

| Option | Default | Description |
|--------|---------|-------------|
| `CONFIG_WELLD_SLEEP_DURATION_SEC` | `300` | Baseline sleep between readings (seconds). When adaptive sleep is enabled, this is the "normal rate" window |
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
| `CONFIG_WELLD_I2C_SDA_GPIO` | `10` | I²C SDA pin (ADS1115 + MAX17048) |
| `CONFIG_WELLD_I2C_SCL_GPIO` | `11` | I²C SCL pin |
| `CONFIG_WELLD_VLOOP_GPIO` | `5` | TPS61023 EN — 12 V loop supply enable |
| `CONFIG_WELLD_CHARGER_CE_GPIO` | `4` | TP4056 CE — USB charger interlock |
| `CONFIG_WELLD_SOLAR_DETECT_GPIO` | `6` | CN3791 CHRG — solar-charging-active detect |
| `CONFIG_WELLD_BATT_DIV_EN_GPIO` | `15` | Battery-divider FET gate |
| `CONFIG_WELLD_MAX17048_ALRT_GPIO` | `14` | MAX17048 ALRT input (active-low open-drain; R27 pull-up to 3V3) |
| `CONFIG_WELLD_ADS1115_DRDY_GPIO` | `12` | ADS1115 ALERT/DRDY interrupt input (open-drain, falling edge = conversion complete) |

### Advanced / diagnostics

| Option | Default | Description |
|--------|---------|-------------|
| `CONFIG_WELLD_ADC_OVERSAMPLE_ENABLED` | `n` | Take 3 ADS1115 samples per measurement and report the median. Opt-in for electrically noisy installations (pump motor interference, long cable runs). Costs ~8 ms extra active time per wakeup; leave off for maximum battery life |
| `CONFIG_WELLD_TEMP_COMPENSATION_ENABLED` | `n` | Apply water-density correction to the level reading: `level / (1 + alpha * (temp - 20))`. Only useful when the well has large thermal swings (> 20 °C) |
| `CONFIG_WELLD_TEMP_COMPENSATION_PPM_PER_C` | `207` | Water density coefficient in ppm/°C. Depends on `WELLD_TEMP_COMPENSATION_ENABLED`. Typical value for fresh water is 207 ppm/°C; range 0–500 |
| `CONFIG_WELLD_DS18B20_RESOLUTION_BITS` | `12` | DS18B20 conversion resolution: 9 / 10 / 11 / 12 bit. Conversion time: 94 / 188 / 375 / 750 ms. Lower resolution saves active time and battery |
| `CONFIG_WELLD_FACTORY_RESET_GPIO` | `13` | If this GPIO is held LOW at boot, NVS is erased and the device rejoins Zigbee fresh. Internal pull-up enabled; leave unconnected for normal operation |
| `CONFIG_WELLD_SELFTEST_ENABLED` | `n` | Exercise all peripherals on every boot and log PASS/FAIL. Adds ~200 ms to boot time; useful for factory QA and PCB bring-up |
| `CONFIG_WELLD_DIAGNOSTIC_MODE_ENABLED` | `n` | Stay awake for `WELLD_DIAGNOSTIC_STAY_AWAKE_SEC` after each sensor read, printing verbose logs. Deep sleep is still entered after the window expires |
| `CONFIG_WELLD_DIAGNOSTIC_STAY_AWAKE_SEC` | `60` | Stay-awake window when diagnostic mode is enabled (seconds, 10–300). Depends on `WELLD_DIAGNOSTIC_MODE_ENABLED` |
| `CONFIG_WELLD_ZIGBEE_BACKOFF_MAX_MS` | `500` | Random delay before Zigbee network steering on each wakeup (0–5000 ms). Jitters start time to avoid simultaneous steering from multiple devices after a power outage |
| `CONFIG_WELLD_OTA_STALL_TIMEOUT_SEC` | `240` | Maximum wall-clock time an OTA download may take before it is considered stalled and aborted (60–600 s) |

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
  "battery_voltage": 3.71,
  "battery": 59
}
```

- `water_level` is `null` when the pressure loop reads below 3.5 mA (open circuit / broken wire) or above 21 mA (short circuit / shorted transducer). Trigger a Home Assistant alert on `water_level is null` to catch both fault conditions.
- `water_level_rate` is signed cm/h. Positive = recovering, negative = drawing down. Omitted on the first valid wakeup after a cold boot and during open-loop cycles.
- `temperature` is omitted when the DS18B20 is not detected.
- `battery_voltage` comes from the MAX17048 VCELL register (coulomb-counted) or the ADS1115 AIN2 divider fallback.
- `battery` is a percentage derived from `battery_voltage` using the device options `battery_full_mv` / `battery_empty_mv` (defaults 4200 / 3000 mV).

### 4. Home Assistant

The Z2M–Home Assistant integration auto-creates these sensor entities:

| Entity | Unit |
|--------|------|
| `sensor.<name>_water_level` | m |
| `sensor.<name>_water_level_rate` | cm/h |
| `sensor.<name>_temperature` | °C |
| `sensor.<name>_battery_voltage` | V |
| `sensor.<name>_battery` | % |

---

## OTA firmware updates

The device runs a Zigbee OTA Upgrade client. Zigbee2MQTT (`ota: true` in the converter) distributes images automatically once placed in its OTA folder.

### 1. Bump the version

Edit `PROJECT_VER` in the root `CMakeLists.txt`:

```cmake
project(welld VERSION 1.0.1)   # MAJOR.MINOR.PATCH
```

The OTA file-version `0xMMmmPP00` is derived from `PROJECT_VER` at build time — **don't edit `OTA_FW_VERSION` directly.**

### 2. Build the OTA image

After `idf.py build`, wrap the binary using `ota_image_create.py` from the esp-zigbee-sdk:

```bash
python path/to/ota_image_create.py \
    --manufacturer-code 0x1234 \
    --image-type 0x0001 \
    --file-version 0x01000100 \
    --output welld-v1.0.1.zigbee \
    build/welld.bin
```

`--manufacturer-code` and `--image-type` **must** match the constants in `components/zigbee/zigbee.c` (`0x1234` / `0x0001`). The device rejects mismatched headers — don't wildcard them to `0xFFFF`.

`--file-version` must increase monotonically; the device only installs images with a higher version than the running one.

### 3. Deploy

```bash
cp welld-v1.0.1.zigbee /opt/zigbee2mqtt/data/ota/
```

Zigbee2MQTT picks the file up automatically. On the next wakeup the device queries for an update, downloads it in 128-byte blocks over Zigbee, and reboots into the new firmware.

### OTA rollback guard

The firmware tracks consecutive boot failures in RTC memory. If 3 consecutive boots complete without a successful Zigbee send, the device automatically rolls back to the previous firmware partition. This prevents a bad OTA image from permanently bricking the device in the field.

---

## Operations

### Level offset calibration

Use `CONFIG_WELLD_SENSOR_OFFSET_CM` (or `sensor_set_offset_cm()` at runtime) to shift the reported level without moving the transducer. For example, if the transducer hangs 15 cm above the well bottom, set the offset to `-15` to report depth from the bottom of the well.

The offset is persisted in NVS (key `offset_cm` in namespace `welld`) and clamped to ±600 cm.

### Adaptive sleep & rate of change

The device remembers its last valid reading and elapsed time in RTC slow memory (preserved across deep sleep, zeroed on cold boot). At each wakeup it computes a signed rate of change in cm/h and uses it to:

1. **Report `water_level_rate`** to Zigbee2MQTT.
2. **Adjust the next sleep duration** when `CONFIG_WELLD_ADAPTIVE_SLEEP_ENABLED=y`:

   | Rate (cm/h) | Sleep multiplier | At default 300 s |
   |-------------|------------------|------------------|
   | < 1         | 3×               | 900 s (15 min)   |
   | 1 – 5       | 2×               | 600 s (10 min)   |
   | 5 – 20      | 1×               | 300 s (5 min)    |
   | 20 – 50     | ½×               | 150 s            |
   | ≥ 50        | ¼×               | 75 s             |

   Result is clamped to `[WELLD_SLEEP_MIN_SEC, WELLD_SLEEP_MAX_SEC]`.

Set `CONFIG_WELLD_ADAPTIVE_SLEEP_ENABLED=n` for a fixed reporting cadence.

### Factory reset

Hold `CONFIG_WELLD_FACTORY_RESET_GPIO` (default GPIO13) LOW during boot to erase NVS and force a clean Zigbee rejoin. The internal pull-up is enabled; leaving the pin unconnected causes normal operation. This is the same NVS erase that occurs automatically after 5 consecutive Zigbee send failures.

### I2C bus recovery

On every boot, `sensor_i2c_init()` checks whether SDA is stuck LOW (a common symptom of a previous aborted transaction). If SDA is LOW, it clocks 9 SCL pulses to force any stuck I2C slave to release the bus before initialising the I2C master. This is a no-op under normal conditions.

### MAX17048 alert handling

On every boot, firmware checks GPIO14 (MAX17048 ALRT, active-low) before the sensor reads begin. If the pin is asserted, it reads the MAX17048 STATUS register, logs each asserted flag (RI / VH / VL / VR / HD / SC), and clears the alert. The alert threshold is configured in NVS; if none is set, the default low-battery threshold from the MAX17048 power-on default applies.

### Low-battery protection

When battery voltage drops below `CONFIG_WELLD_BATT_EMPTY_MV`, the device skips the Zigbee send and all NVS writes, and sleeps for the maximum interval to conserve charge. The rate accumulator is reset on exit from this path so the next valid wakeup doesn't produce a false rate spike.

### Expected serial output

Normal cycle:

```
I (sensor): voltage=1485 mV  current=14850 µA  level=3.42 m
I (sensor): temperature=12.3 °C
I (sensor): battery=3.71 V (MAX17048)
I (zigbee): joined; reporting level=3.42 m battery=3.71 V temp=12.3 °C rate=12.5 cm/h
I (main):   sleeping 300 s
```

Solar charging active:

```
I (main): solar charging active — USB charger disabled
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
E (sensor): transducer open loop (voltage=12 mV, < 3.5 mA)
```

Pressure transducer short circuit (> 21 mA):

```
E (sensor): transducer short circuit (current=24000 µA, > 21 mA)
```

DS18B20 ROM change (sensor replaced):

```
W (sensor): DS18B20 ROM changed: stored=28ff1234ab000002 active=28ff5678cd000003
```

---

## Power

The device spends nearly all of its time in deep sleep. Each wakeup is typically 6–12 seconds of active current (I²C reads, Zigbee send, 1-Wire conversion), followed by a sleep window of 1–30 minutes depending on rate-of-change. At the default 5-minute interval, average current is well under 1 mA — months of runtime on a single 18650 cell.

All power-control GPIOs (VLOOP, BATT_DIV_EN, CHARGER_CE) are driven low and the GPIO matrix is isolated (`esp_sleep_gpio_isolate()`) before every `esp_deep_sleep()` call to eliminate leakage through partially-driven outputs during sleep.

---

## Development

### Project layout

```
main/                    wakeup orchestration, NVS fail counter, RTC history
components/sensor/       I²C (ADS1115/MAX17048), DS18B20, GPIO power control
components/zigbee/       esp-zigbee-lib wrapper, OTA client, BDB commissioning task
components/welld_core/   pure helpers (rate-of-change, adaptive sleep, ZCL encoding)
zigbee2mqtt/welld.js     external converter for Zigbee2MQTT
hardware/pcb/            PCB design reference, BOM, Gerber generation script
hardware/case/           OpenSCAD parametric enclosure (default + 2S battery variant)
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

`.github/workflows/build.yml` runs four jobs in parallel:

- **ESP-IDF build** — v5.5.4, `esp32c6`, uploads `*.bin`, `*.elf`, `*.map`, `dependencies.lock`
- **Host unit tests** — plain `ubuntu-latest`, ctest, fetches Unity v2.6.0
- **On-device test build** — compile-only check for `test/sensor` and `test/welld_core`
- **Z2M converter tests** — Node 20, `npm test` in `zigbee2mqtt/`

---

## Legacy: dev board wiring

If building from an off-the-shelf ESP32-C6 dev board instead of the custom PCB, wire the pressure transducer shunt directly to an ADC1 pin and power the loop externally. The ADS1115, MAX17048, and TPS61023 boost are not available on a bare dev board — configure `CONFIG_WELLD_SENSOR_ADC_CHANNEL` to the ESP ADC channel used and set `CONFIG_WELLD_BATT_ADC_CHANNEL=-1` to disable battery monitoring. The power-control GPIO options (`VLOOP`, `CHARGER_CE`, etc.) are still compiled in but the interlock GPIOs can be left disconnected if the solar/USB chargers are absent.
