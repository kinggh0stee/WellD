# WellD

Battery-powered well-level monitor for the ESP32-C6. Each wakeup it reads a 4–20 mA submersible pressure transducer, a DS18B20 temperature probe, and (optionally) battery voltage; reports them over Zigbee to Zigbee2MQTT; then deep-sleeps until the next cycle.

- **Radio:** Zigbee 3.0 over the C6's built-in 802.15.4 — no extra modules
- **Battery life:** months on a LiPo at the default 5-minute interval (deep sleep between readings)
- **Adaptive sleep:** sleep duration scales with how fast the level is changing — longer windows when stable, shorter when transients are in progress
- **Rate-of-change reporting:** `water_level_rate` in cm/h published as a fourth sensor; distinguishes "well recovering" from "well being drawn down"
- **Self-healing:** wipes Zigbee NVS state and rejoins fresh after 5 consecutive send failures
- **OTA:** Zigbee OTA Upgrade client, dual 1.5 MB app slots
- **Sentinels:** open-loop transducer reports `null` water level so Home Assistant can alert on wiring faults

---

## Hardware

Two hardware paths are supported — see [`hardware/`](hardware/) for a full comparison.

- **Off-the-shelf dev board** — the path documented below; in-hand in days, no PCB lead time.
- **Custom PCB** — purpose-built 80 × 55 mm board with screw terminals, onboard LiPo charger, TVS protection, and a second 4–20 mA channel. See [`hardware/pcb/`](hardware/pcb/) for design reference and BOM.

### Bill of materials

| Part | Notes |
|------|-------|
| ESP32-C6 dev board | Any board with exposed ADC1 pins |
| 4–20 mA submersible pressure transducer | 0–6 m range, two-wire 4–20 mA output |
| 100 Ω resistor (±1 %) | Loop shunt — converts 4–20 mA to 0.4–2.0 V |
| DS18B20 waterproof probe | Any submersible DS18B20 variant |
| 4.7 kΩ resistor | 1-Wire pull-up to 3.3 V |
| Power supply | 3.3 V regulated, or LiPo/18650 with a regulator |
| Zigbee coordinator | e.g. CC2652-based USB stick running Zigbee2MQTT |

### Wiring

**Pressure transducer (water level)**

```
Transducer (+) ─── 3.3 V supply
Transducer (−) ─┬─ 100 Ω shunt ─── GND
                └─ ADC1_CH0 (GPIO0)
```

The 100 Ω shunt drops the 4–20 mA loop to 0.4–2.0 V, well inside the ESP32-C6 ADC range (0–3.1 V at 12 dB attenuation). For other shunt values, set `CONFIG_WELLD_SENSOR_SHUNT_MILLIOHMS` (in milliohms — 100 Ω = `100000`). The Kconfig enforces a 155 Ω upper limit — values above that exceed the ADC absolute-maximum input at full-scale loop current.

**Transient protection (recommended):** 4–20 mA cables in real installations pick up inductive spikes from relay coils, VFDs, and nearby switching supplies. Add a 3.3 V unidirectional TVS diode (e.g. PRTR5V0U2X) from the ADC pin to GND, or at minimum a 100 Ω series resistor plus a 3.3 V zener clamp between the shunt tap and the ADC pin, to protect the GPIO from overvoltage transients on the cable.

**DS18B20 temperature probe**

```
DS18B20 VCC  ─── 3.3 V
DS18B20 GND  ─── GND
DS18B20 DATA ─┬─ GPIO4
              └─ 4.7 kΩ ─── 3.3 V
```

Lower the probe alongside the pressure transducer. The data GPIO is configurable via `CONFIG_WELLD_DS18B20_GPIO`.

**Battery voltage monitoring (optional)**

```
Battery (+) ─┬─ R1 ─┬─ ADC1_CHx
             │      └─ R2 ─── GND
             └─────────────── supply rail
```

Size R1/R2 so the full battery voltage maps to ≤ 3.1 V at the ADC pin. Set `CONFIG_WELLD_BATT_ADC_CHANNEL` to the ADC1 channel used, and `CONFIG_WELLD_BATT_DIVIDER_RATIO` to `(R1+R2)/R2 × 100` (minimum 136 — a 1:1 pass-through at 4.2 V exceeds the ADC absolute maximum). For a 4.2 V Li-ion cell the default 2:1 divider (ratio 200, R1=R2) produces 2.1 V at the ADC pin. For 12 V SLA use a ratio of at least 465. Set the channel to `-1` to disable.

---

## Quickstart

### Prerequisites

- ESP-IDF **v5.3.5** installed and sourced — see the [Espressif getting-started guide](https://docs.espressif.com/projects/esp-idf/en/v5.3.5/esp32c6/get-started/)
- USB cable to the ESP32-C6 board

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

All options have sensible defaults — only change what differs from your hardware.

| Option | Default | Description |
|--------|---------|-------------|
| `CONFIG_WELLD_SENSOR_ADC_CHANNEL` | `0` | ADC1 channel wired to the shunt (CH0 = GPIO0) |
| `CONFIG_WELLD_SENSOR_SHUNT_MILLIOHMS` | `100000` | Shunt resistor in milliohms |
| `CONFIG_WELLD_SENSOR_MAX_DEPTH_CM` | `600` | Full-scale depth at 20 mA, in cm |
| `CONFIG_WELLD_SENSOR_OFFSET_CM` | `0` | Level offset in cm applied after conversion (±600). Persisted in NVS; runtime-writable via `sensor_set_offset_cm()` |
| `CONFIG_WELLD_DS18B20_GPIO` | `7` | GPIO connected to DS18B20 data pin |
| `CONFIG_WELLD_BATT_ADC_CHANNEL` | `-1` | ADC1 channel for battery divider; `-1` disables battery monitoring |
| `CONFIG_WELLD_BATT_DIVIDER_RATIO` | `200` | Divider ratio × 100 (`200` = 2:1) |
| `CONFIG_WELLD_BATT_FULL_MV` | `4200` | Voltage (mV) reported as 100 % by the Z2M converter |
| `CONFIG_WELLD_BATT_EMPTY_MV` | `3000` | Voltage (mV) reported as 0 % by the Z2M converter |
| `CONFIG_WELLD_SLEEP_DURATION_SEC` | `300` | Baseline sleep between readings (seconds). When adaptive sleep is enabled, this is the "normal rate" window |
| `CONFIG_WELLD_ADAPTIVE_SLEEP_ENABLED` | `y` | Scale sleep duration to the observed level rate-of-change |
| `CONFIG_WELLD_SLEEP_MIN_SEC` | `60` | Lower bound on adaptive sleep |
| `CONFIG_WELLD_SLEEP_MAX_SEC` | `1800` | Upper bound on adaptive sleep |
| `CONFIG_WELLD_ZIGBEE_CHANNEL_MASK` | `0x07FFF800` | Channels to scan; narrow to your coordinator's channel to speed up joins |
| `CONFIG_WELLD_ZIGBEE_SEND_DELAY_MS` | `2000` | Time the stack stays alive after sending, to allow coordinator ACK |

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

- `battery_voltage` and `battery` are omitted when battery monitoring is disabled.
- `battery` is a percentage computed by the converter from `battery_voltage` using the device options `battery_full_mv` / `battery_empty_mv` (defaults 4200 / 3000 mV). Override per-device in Z2M if your chemistry differs.
- `temperature` is omitted when the DS18B20 isn't detected.
- `water_level` is `null` when the pressure loop reads below 3.5 mA (open circuit). Trigger a Home Assistant alert on `water_level is null` to catch wiring faults.
- `water_level_rate` is signed cm/h, derived from the previous valid reading. Positive = recovering, negative = drawing down. Omitted on the first valid wakeup after a cold boot (no baseline yet) and during open-loop cycles (carried over to the next valid reading).

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

The device runs a Zigbee OTA Upgrade client. Zigbee2MQTT (`ota: true` in the converter) distributes images automatically once they're placed in its OTA folder.

### 1. Bump the version

Edit `PROJECT_VER` in the root `CMakeLists.txt`:

```cmake
project(welld VERSION 1.0.1)   # MAJOR.MINOR.PATCH
```

The OTA file-version is derived from `PROJECT_VER` at build time — **don't edit `OTA_FW_VERSION` directly.**

### 2. Build the OTA image

After `idf.py build`, wrap the binary using `ota_image_create.py` from the esp-zigbee-sdk:

```bash
python path/to/ota_image_create.py \
    --manufacturer-code 0x1234 \
    --image-type 0x0001 \
    --file-version 0x00010001 \
    --output welld-v1.0.1.zigbee \
    build/welld.bin
```

`--manufacturer-code` and `--image-type` **must** match the constants in `components/zigbee/zigbee.c` (`OTA_MANUFACTURER_CODE = 0x1234`, `OTA_IMAGE_TYPE = 0x0001`). The device rejects mismatched headers — this is a security boundary against rogue OTA servers, so don't wildcard them to `0xFFFF`.

`--file-version` must increase monotonically; the device only installs images with a higher version than the running one.

### 3. Deploy

```bash
cp welld-v1.0.1.zigbee /opt/zigbee2mqtt/data/ota/
```

Zigbee2MQTT picks the file up automatically. On the next wakeup the device queries for an update, downloads it in 128-byte blocks over Zigbee, and reboots into the new firmware. The post-send timeout is extended for the duration of the download.

---

## Operations

### Level offset calibration

Use `CONFIG_WELLD_SENSOR_OFFSET_CM` (or `sensor_set_offset_cm()` at runtime) to shift the reported level without moving the transducer. For example, if the transducer hangs 15 cm above the well bottom, set the offset to `-15` to report depth from the bottom of the well.

The offset is persisted in NVS (key `offset_cm` in namespace `welld`) and clamped to ±600 cm on read to guard against flash corruption.

### Adaptive sleep & rate of change

The device remembers its last valid reading and the elapsed time since then in RTC slow memory (preserved across deep sleep, zeroed on cold boot). At each wakeup it computes a signed rate of change in cm/h and uses it for two things:

1. **Reports `water_level_rate`** to Zigbee2MQTT as a fourth sensor entity. Positive = recovering, negative = drawing down.
2. **Adjusts the next sleep duration** when `CONFIG_WELLD_ADAPTIVE_SLEEP_ENABLED=y`. The mapping (absolute rate, cm/h → multiplier of `WELLD_SLEEP_DURATION_SEC`):

   | Rate (cm/h) | Sleep multiplier | At default 300 s |
   |-------------|------------------|------------------|
   | < 1         | 3×               | 900 s (15 min)   |
   | 1 – 5       | 2×               | 600 s (10 min)   |
   | 5 – 20      | 1×               | 300 s (5 min)    |
   | 20 – 50     | ½×               | 150 s            |
   | ≥ 50        | ¼×               | 75 s             |

   The result is clamped to `[WELLD_SLEEP_MIN_SEC, WELLD_SLEEP_MAX_SEC]`. Cold boot and open-loop cycles fall back to `WELLD_SLEEP_DURATION_SEC` verbatim.

Set `CONFIG_WELLD_ADAPTIVE_SLEEP_ENABLED=n` to keep a fixed `WELLD_SLEEP_DURATION_SEC` regardless of the rate — useful when you want predictable reporting cadence.

### Expected serial output

Normal cycle:

```
I (sensor): raw=1847  voltage=1485 mV  current=14850 µA  level=3.42 m
I (sensor): temperature=12.3 °C
I (zigbee): joined; reporting level=3.42 m battery=3.71 V temp=12.3 °C
I (main):   sleeping 300 s
```

With a non-zero offset:

```
I (sensor): raw=1847  voltage=1485 mV  current=14850 µA  level=3.27 m (offset -15 cm)
```

No coordinator in range:

```
E (zigbee): timeout — no coordinator found
W (main):   Zigbee send failed (1/5)
I (main):   sleeping 300 s
```

After 5 consecutive failures the NVS partition is erased on the next boot, forcing a clean Zigbee rejoin. The counter resets to zero on the first successful send.

Pressure transducer disconnected (open loop, < 3.5 mA):

```
E (sensor): transducer open loop (voltage=12 mV, < 3.5 mA)
```

`water_level` is reported as `null` for that cycle.

DS18B20 not detected:

```
E (sensor): no DS18B20 found on GPIO 7
```

Temperature is omitted from the report and retried on the next wakeup.

---

## Power

The device spends the vast majority of its time in deep sleep. Each wakeup is typically 6–12 seconds of active current, followed by a sleep window of 1–30 minutes depending on the rate of change. At the default 5-minute interval, average current is well under 1 mA — months of runtime on a small LiPo or 18650 cell.

---

## Development

### Project layout

```
main/                 wakeup orchestration, NVS fail counter
components/sensor/    ADC + DS18B20 + battery divider (pure helper exposed for tests)
components/zigbee/    esp-zigbee-lib wrapper, OTA client, BDB commissioning task
components/welld_core/  pure helpers shared across components
zigbee2mqtt/welld.js  external converter for Zigbee2MQTT
test/sensor/          on-device Unity test for sensor_level_from_mv
test/welld_core/      on-device Unity test for welld_core helpers
```

### Host tests

The pure helpers (`sensor_level_from_mv`, `sensor_battery_from_mv`, `sensor_temp_in_range`, `welld_*`) are exercised by a plain CMake project under `test/host/`. No ESP-IDF or hardware required:

```bash
cmake -S test/host -B test/host/build
cmake --build test/host/build
ctest --test-dir test/host/build --output-on-failure
```

CI runs these on every push.

### On-device tests

For NVS round-trips and 1-Wire / ADC paths the host runner can't cover, standalone ESP-IDF test projects live under `test/sensor/` and `test/welld_core/` and run on real hardware via Unity over the serial console:

```bash
idf.py -C test/sensor build flash monitor
idf.py -C test/welld_core build flash monitor
```

CI builds these to catch compile breaks but cannot execute them.

### CI

`.github/workflows/build.yml` runs four jobs in parallel: ESP-IDF v5.3.5 firmware build for esp32c6, host unit tests under ctest, on-device test compilation, and the Zigbee2MQTT converter test suite. Firmware artifacts (`*.bin`, `*.elf`, `*.map`, `dependencies.lock`) are uploaded from the firmware job on success.
