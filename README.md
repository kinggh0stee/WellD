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
| `CONFIG_WELLD_DS18B20_GPIO` | 4 | GPIO connected to DS18B20 data pin |
| `CONFIG_WELLD_BATT_ADC_CHANNEL` | -1 | ADC1 channel for battery divider; -1 = disabled |
| `CONFIG_WELLD_BATT_DIVIDER_RATIO` | 200 | Divider ratio × 100 (200 = 2:1 divider) |
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
  "battery_voltage": 3.71
}
```

`battery_voltage` is omitted if battery monitoring is disabled.

### 4. Home Assistant

With the Zigbee2MQTT–Home Assistant integration, three sensor entities are created automatically:

| Entity | Unit | Notes |
|--------|------|-------|
| `sensor.<name>_water_level` | m | Water depth |
| `sensor.<name>_temperature` | °C | Water temperature |
| `sensor.<name>_battery_voltage` | V | Battery (if enabled) |

---

## Serial output

Normal boot cycle:

```
I (sensor): raw=1847  voltage=1485 mV  current=14850 µA  level=3.42 m
I (sensor): temperature=12.3 °C
I (zigbee): joined; reporting level=3.42 m battery=3.71 V temp=12.3 °C
I (main):   sleeping 300 s
```

No coordinator in range:

```
E (zigbee): timeout — no coordinator found
I (main):   sleeping 300 s
```

DS18B20 not detected:

```
E (sensor): no DS18B20 found on GPIO 4
```

Temperature is skipped in the Zigbee report and retried on the next wakeup.

---

## Power

| State | Current |
|-------|---------|
| Deep sleep | ~7 µA |
| Active (Zigbee join + send) | ~20 mA for ~6–11 s |
| DS18B20 conversion | adds ~750 ms at ~1 mA |

At the default 5-minute interval, average current is well under 1 mA — compatible with a small LiPo or 18650 cell for months of runtime.
