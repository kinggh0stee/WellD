# WellD — ESP32-C6 Well Monitor

Reads a 4–20 mA submersible pressure transducer and a DS18B20 temperature probe, reports water level, temperature, and battery voltage to Zigbee2MQTT, then deep-sleeps until the next reading cycle. Built on the ESP32-C6 (RISC-V, built-in IEEE 802.15.4 radio).

---

## Hardware

### Parts

| Part | Notes |
|------|-------|
| ESP32-C6 dev board | Any board with exposed ADC1 pins |
| 4–20 mA submersible pressure transducer | 0–6 m range, 4–20 mA output |
| 100 Ω resistor (±1%) | Shunt — converts 4–20 mA loop to 0.4–2.0 V |
| DS18B20 waterproof probe | Any submersible DS18B20 variant |
| 4.7 kΩ resistor | Pull-up for DS18B20 data line |
| Power supply | 3.3 V regulated, or LiPo/18650 with regulator |
| Zigbee coordinator | CC2652-based USB stick running Zigbee2MQTT |

### Wiring

**Pressure transducer (water level)**
```
Transducer (+) ─── 3.3 V supply
Transducer (−) ─┬─ 100 Ω shunt ─── GND
                └─ ADC1_CH0 (GPIO0)
```
The 100 Ω shunt converts the 4–20 mA loop current to 0.4–2.0 V, within the ESP32-C6 ADC input range (0–3.1 V at 12 dB attenuation).

> If your shunt differs, set `CONFIG_WELLD_SENSOR_SHUNT_MILLIOHMS` (milliohms: 100 Ω = 100 000 mΩ).

**DS18B20 temperature probe (water temperature)**
```
DS18B20 VCC  ─── 3.3 V
DS18B20 GND  ─── GND
DS18B20 DATA ─┬─ GPIO4
              └─ 4.7 kΩ ─── 3.3 V
```
Any waterproof DS18B20 probe works. Lower it alongside the pressure transducer. GPIO is configurable via `CONFIG_WELLD_DS18B20_GPIO`.

**Battery voltage monitoring (optional)**
```
Battery (+) ─┬─ R1 ─┬─ ADC1_CHx
             │      └─ R2 ─── GND
             └─────────────── supply rail
```
Choose R1/R2 so the full battery voltage maps to ≤ 3.1 V at the ADC pin. Set `CONFIG_WELLD_BATT_ADC_CHANNEL` to the ADC1 channel used and `CONFIG_WELLD_BATT_DIVIDER_RATIO` to `(R1+R2)/R2 * 100`. Leave `BATT_ADC_CHANNEL=-1` to disable.

---

## Build & Flash

### Prerequisites

- [ESP-IDF v5.x](https://docs.espressif.com/projects/esp-idf/en/stable/esp32c6/get-started/) installed and sourced
- USB cable to the ESP32-C6 board

### First-time setup

```bash
git clone https://github.com/kinggh0stee/WellD.git
cd WellD

# set the target chip
idf.py set-target esp32c6

# create and edit your local config (never committed to git)
cp sdkconfig.defaults.local.example sdkconfig.defaults.local
$EDITOR sdkconfig.defaults.local

# build and flash
idf.py build
idf.py -p /dev/ttyUSB0 flash monitor
```

### Configuration

Edit `sdkconfig.defaults.local`. All options have sensible defaults — only change what differs from your hardware.

| Option | Default | Description |
|--------|---------|-------------|
| `CONFIG_WELLD_SENSOR_ADC_CHANNEL` | 0 | ADC1 channel wired to the shunt (CH0 = GPIO0) |
| `CONFIG_WELLD_SENSOR_SHUNT_MILLIOHMS` | 100000 | Shunt resistor in milliohms (100 Ω = 100 000) |
| `CONFIG_WELLD_SENSOR_MAX_DEPTH_CM` | 600 | Full-scale depth at 20 mA in cm (600 = 6 m) |
| `CONFIG_WELLD_SENSOR_OFFSET_CM` | 0 | Level offset in cm applied after conversion (±600). Use to zero the reading at a known water depth. Persisted in NVS; runtime-writable via `sensor_set_offset_cm()`. |
| `CONFIG_WELLD_DS18B20_GPIO` | 4 | GPIO connected to DS18B20 data pin |
| `CONFIG_WELLD_BATT_ADC_CHANNEL` | -1 | ADC1 channel for battery divider; -1 = disabled |
| `CONFIG_WELLD_BATT_DIVIDER_RATIO` | 200 | Divider ratio × 100 (200 = 2:1 divider) |
| `CONFIG_WELLD_BATT_FULL_MV` | 4200 | Battery voltage (mV) considered 100 %. Used by the Z2M converter to compute battery percentage. |
| `CONFIG_WELLD_BATT_EMPTY_MV` | 3000 | Battery voltage (mV) considered 0 %. |
| `CONFIG_WELLD_SLEEP_DURATION_SEC` | 300 | Deep sleep between readings in seconds |
| `CONFIG_WELLD_ZIGBEE_CHANNEL_MASK` | 0x07FFF800 | Channels to scan; narrow to your coordinator's channel to speed up joining |
| `CONFIG_WELLD_ZIGBEE_SEND_DELAY_MS` | 2000 | Time (ms) the stack stays alive after sending, to allow coordinator ACK |

Or use the interactive menu: `idf.py menuconfig` → **WellD Configuration**.

---

## Zigbee2MQTT Setup

### 1. Install the external converter first

Copy the converter before pairing so Zigbee2MQTT recognises the device on first join:

```bash
cp zigbee2mqtt/welld.js /opt/zigbee2mqtt/data/
```

Add to `/opt/zigbee2mqtt/data/configuration.yaml`:

```yaml
external_converters:
  - welld.js
```

Restart Zigbee2MQTT:

```bash
sudo systemctl restart zigbee2mqtt
```

### 2. Pair the device

Enable permit join in `configuration.yaml`:

```yaml
permit_join: true
```

Power the ESP32-C6. It scans for the coordinator, joins, and sends its first reading. First-time pairing takes up to 25 seconds; subsequent wakeups rejoin in a few seconds using network state cached in NVS.

Disable permit join once paired:

```yaml
permit_join: false
```

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

`battery_voltage` and `battery` are omitted if battery monitoring is disabled. `battery` is a percentage computed by the Z2M converter from the measured voltage using the `battery_full_mv` / `battery_empty_mv` device options (default 4200 / 3000 mV). Override these per-device in the Z2M device options if your battery chemistry differs.

`temperature` is omitted if the DS18B20 is not detected. `water_level` is `-1` if the pressure transducer loop current is below 3.5 mA (open circuit / disconnected) — set a Home Assistant alert on `water_level < 0` to detect wiring faults.

### 4. Home Assistant

With the Zigbee2MQTT–Home Assistant integration, three sensor entities are created automatically:

| Entity | Unit | Notes |
|--------|------|-------|
| `sensor.<name>_water_level` | m | Water depth |
| `sensor.<name>_temperature` | °C | Water temperature |
| `sensor.<name>_battery_voltage` | V | Battery voltage (if enabled) |
| `sensor.<name>_battery` | % | Battery percentage (if enabled) |

---

## OTA firmware updates

The device includes a Zigbee OTA Upgrade client (`ota: true` in the converter). Zigbee2MQTT handles image distribution automatically once an image file is placed in its OTA folder.

### Build an OTA image

After `idf.py build`, wrap the binary in a Zigbee OTA file using the image generator from the esp-zigbee-sdk:

```bash
python path/to/ota_image_create.py \
    --manufacturer-code 0x1234 \
    --image-type 0x0001 \
    --file-version 0x00010001 \
    --output welld-v1.0.1.zigbee \
    build/welld.bin
```

**The `--manufacturer-code` and `--image-type` values must match the constants in `zigbee.c`** (`OTA_MANUFACTURER_CODE = 0x1234`, `OTA_IMAGE_TYPE = 0x0001`). The device will reject any image whose header doesn't match, preventing a rogue OTA server from pushing foreign firmware.

Bump `--file-version` on every release (monotonically increasing 32-bit integer). The device will only install an image with a higher file version than its current one.

### Deploy via Zigbee2MQTT

```bash
cp welld-v1.0.1.zigbee /opt/zigbee2mqtt/data/ota/
```

Zigbee2MQTT detects the file automatically. On the next wakeup the device queries for an update, downloads the image in 128-byte blocks over Zigbee, and reboots into the new firmware. The timeout alarm is extended automatically during download so the device doesn't sleep mid-transfer.

---

## Level offset calibration

Use `CONFIG_WELLD_SENSOR_OFFSET_CM` (or `sensor_set_offset_cm()` at runtime) to shift the reported level without touching the transducer position. Positive values add to the reading; negative values subtract.

For example, if the transducer is mounted 15 cm above the well bottom, set `OFFSET_CM = -15` to report depth from the bottom rather than from the transducer face.

The offset is stored in NVS and survives deep sleep and power cycles. It is clamped to ±600 cm on read to guard against flash corruption.

---

## Serial output

Normal boot cycle (no offset):

```
I (sensor): raw=1847  voltage=1485 mV  current=14850 µA  level=3.42 m
I (sensor): temperature=12.3 °C
I (zigbee): joined; reporting level=3.42 m battery=3.71 V temp=12.3 °C
I (main):   sleeping 300 s
```

With a non-zero level offset:

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

Pressure transducer disconnected (open loop):

```
E (sensor): transducer open loop (voltage=12 mV, < 3.5 mA)
```

`water_level` is reported as `-1` for that cycle.

DS18B20 not detected:

```
E (sensor): no DS18B20 found on GPIO 4
```

Temperature is omitted from the Zigbee report and retried on the next wakeup.

---

## Power

| State | Current |
|-------|---------|
| Deep sleep | ~7 µA |
| Active (Zigbee join + send) | ~20 mA for ~6–11 s |
| DS18B20 conversion | adds ~750 ms at ~1 mA |

At the default 5-minute interval, average current is well under 1 mA — compatible with a small LiPo or 18650 cell for months of runtime.
