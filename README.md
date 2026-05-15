# WellD

Battery-powered well-level monitor for the ESP32-C6. Each wakeup it reads a 4–20 mA submersible pressure transducer, a DS18B20 temperature probe, and (optionally) battery voltage; reports them over Zigbee to Zigbee2MQTT; then deep-sleeps until the next cycle.

- **Radio:** Zigbee 3.0 over the C6's built-in 802.15.4 — no extra modules
- **Battery life:** months on a LiPo at the default 5-minute interval (~7 µA in deep sleep)
- **Self-healing:** wipes Zigbee NVS state and rejoins fresh after 5 consecutive send failures
- **OTA:** Zigbee OTA Upgrade client, dual 1.5 MB app slots
- **Sentinels:** open-loop transducer reports `null` water level so Home Assistant can alert on wiring faults

---

## Hardware

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

The 100 Ω shunt drops the 4–20 mA loop to 0.4–2.0 V, well inside the ESP32-C6 ADC range (0–3.1 V at 12 dB attenuation). For other shunt values, set `CONFIG_WELLD_SENSOR_SHUNT_MILLIOHMS` (in milliohms — 100 Ω = `100000`).

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

Size R1/R2 so the full battery voltage maps to ≤ 3.1 V at the ADC pin. Set `CONFIG_WELLD_BATT_ADC_CHANNEL` to the ADC1 channel used, and `CONFIG_WELLD_BATT_DIVIDER_RATIO` to `(R1+R2)/R2 × 100`. Set the channel to `-1` to disable.

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
| `CONFIG_WELLD_DS18B20_GPIO` | `4` | GPIO connected to DS18B20 data pin |
| `CONFIG_WELLD_BATT_ADC_CHANNEL` | `-1` | ADC1 channel for battery divider; `-1` disables battery monitoring |
| `CONFIG_WELLD_BATT_DIVIDER_RATIO` | `200` | Divider ratio × 100 (`200` = 2:1) |
| `CONFIG_WELLD_BATT_FULL_MV` | `4200` | Voltage (mV) reported as 100 % by the Z2M converter |
| `CONFIG_WELLD_BATT_EMPTY_MV` | `3000` | Voltage (mV) reported as 0 % by the Z2M converter |
| `CONFIG_WELLD_SLEEP_DURATION_SEC` | `300` | Deep sleep between readings (seconds) |
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
  "temperature": 12.3,
  "battery_voltage": 3.71,
  "battery": 59
}
```

- `battery_voltage` and `battery` are omitted when battery monitoring is disabled.
- `battery` is a percentage computed by the converter from `battery_voltage` using the device options `battery_full_mv` / `battery_empty_mv` (defaults 4200 / 3000 mV). Override per-device in Z2M if your chemistry differs.
- `temperature` is omitted when the DS18B20 isn't detected.
- `water_level` is `null` when the pressure loop reads below 3.5 mA (open circuit). Trigger a Home Assistant alert on `water_level is null` to catch wiring faults.

### 4. Home Assistant

The Z2M–Home Assistant integration auto-creates these sensor entities:

| Entity | Unit |
|--------|------|
| `sensor.<name>_water_level` | m |
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
E (sensor): no DS18B20 found on GPIO 4
```

Temperature is omitted from the report and retried on the next wakeup.

---

## Power

| State | Current |
|-------|---------|
| Deep sleep | ~7 µA |
| Active (Zigbee join + send) | ~20 mA for 6–11 s |
| DS18B20 conversion | adds ~750 ms at ~1 mA |

At the default 5-minute interval, average current is well under 1 mA — months of runtime on a small LiPo or 18650 cell.

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

### On-device tests

Tests are standalone ESP-IDF projects that pull each component in via `EXTRA_COMPONENT_DIRS` and run under Unity over the serial console. Each runs on real hardware:

```bash
idf.py -C test/sensor build flash monitor
idf.py -C test/welld_core build flash monitor
```

There's no host-side test runner — pure helpers (e.g. `sensor_level_from_mv`, `welld_zb_encode_temp`) are kept free of NVS, ADC, and log calls so they're callable from `app_main` on a bare device.

### CI

`.github/workflows/build.yml` runs ESP-IDF v5.3.5 (SHA-pinned via `espressif/esp-idf-ci-action`), builds the firmware and both test projects for esp32c6, and runs the Zigbee2MQTT converter test suite with Node.js. Build artifacts (`*.bin`, `*.elf`, `*.map`, `dependencies.lock`) are uploaded on success.
