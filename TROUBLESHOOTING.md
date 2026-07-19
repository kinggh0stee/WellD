# Troubleshooting WellD

This guide helps diagnose common issues in the field and during bench testing.

## Serial Log Decision Tree

Connect USB and open the serial monitor (`idf.py -p /dev/ttyUSB0 monitor`).

### 1. No serial output at all

- **Check power:** The 1S2P 18650 pack has integrated PCM that cuts out below the cell minimum voltage. Charge the battery first.
- **Check USB cable:** Some cables are charge-only (no data lines). Try a different cable.
- **Check bootloader baud:** ESP32-C6 boots at 115200; ensure your terminal is set correctly.
- **Brownout reset loop:** If you see `rst:0x1 (POWERON)` repeatedly, the USB port may not supply enough current for the 12 V boost + Zigbee TX spike. Power from a charged battery while keeping USB connected for serial.

### 2. `I2C init failed — aborting wakeup`

- **SDA/SCL shorted:** Check GPIO10/11 for solder bridges or debris.
- **ADS1115 absent:** Verify U2 is seated correctly and its I²C address jumper is open (0x48).
- **Pull-ups missing:** The firmware enables internal I²C pull-ups, but if the bus capacitance is high, add external 4.7 kΩ pull-ups to 3V3.

### 3. `transducer open loop (voltage=... mV, < 3.5 mA)`

- **Wiring fault:** Check LOOP+ / LOOP− terminals. A disconnected transducer reads near 0 mV.
- **Transducer polarity reversed:** Some two-wire transducers are polarity-sensitive.
- **Shunt resistor missing:** Verify R2/R4 (100 Ω) are populated.
- **TVS conducting:** If the SMAJ3.3CA (D9/D10) is damaged short, the loop current bypasses the shunt.

### 4. `Zigbee send failed (N/5)` repeatedly

1. **Coordinator down:** Verify Zigbee2MQTT / coordinator are online and on the channel mask configured in `CONFIG_WELLD_ZIGBEE_CHANNEL_MASK`.
2. **Range:** Move the device closer to the coordinator. The C6's on-chip 802.15.4 range is ~10–30 m indoors depending on walls.
3. **Channel mismatch:** Narrow `CONFIG_WELLD_ZIGBEE_CHANNEL_MASK` to the coordinator's exact channel (e.g., `0x00001000` for channel 12) to speed up joins.
4. **NVS corruption:** After 5 failures the device erases NVS and rejoins fresh. Look for `erasing NVS to force rejoin` in the log.
5. **Interference:** The 2.4 GHz band is crowded. Check for Wi-Fi access points on overlapping channels.

### 5. `battery critically low (X.XX V < 6.00 V) — skipping send`

- **Battery genuinely flat:** Charge via USB or solar.
- **Measurement error:** Verify the divider ratio in Kconfig matches R7/R8 (100 kΩ / 100 kΩ, ratio 200).

### 6. OTA issues

- **OTA image rejected:** Ensure `--manufacturer-code 0x1234` and `--image-type 0x0001` match the hardcoded values in `components/zigbee/zigbee.c`. Do not use `0xFFFF` wildcards.
- **OTA stalled:** Check that the `.zigbee` file is in `/opt/zigbee2mqtt/data/ota/` and that `ota: true` is set in the converter. The stall timeout is `CONFIG_WELLD_OTA_STALL_TIMEOUT_SEC` (default 240 s).
- **Version not increasing:** `ota_image_create.py` requires monotonically increasing `--file-version`. Bump `PROJECT_VER` in `CMakeLists.txt`.

## Reading the RTC Event Log

On every cold boot, the firmware prints the last 16 events from RTC memory:

```
I (main): RTC event log (last 5 entries):
I (main):   [0] t=1234s  BOOT
I (main):   [1] t=1250s  SENSOR_OK
I (main):   [2] t=1255s  ZB_FAIL
I (main):   [3] t=1560s  BOOT
I (main):   [4] t=1575s  LOW_BATT_SKIP
```

This is invaluable for diagnosing devices that failed in the field and are later retrieved. The `t=` value is seconds since the most recent cold boot (deep-sleep wakeups do not reset this counter).

| Event code | Meaning |
|-----------|---------|
| `BOOT` | Cold boot or deep-sleep wakeup |
| `SENSOR_OK` | All sensor reads succeeded |
| `ZB_SENT` | Zigbee report acknowledged by coordinator |
| `ZB_FAIL` | Zigbee send failed or timed out |
| `LOW_BATT_SKIP` | Battery below threshold; send skipped |
| `NVS_WIPE` | 5 consecutive failures triggered NVS erase + rejoin |
| `OTA_START` | OTA download began |
| `OTA_COMPLETE` | OTA image validated; reboot imminent |
| `OTA_ABORT` | OTA aborted by stack or stall timeout |

## Diagnostic Mode (Bench Testing)

Enable `CONFIG_WELLD_DIAGNOSTIC_MODE_ENABLED=y` (via `idf.py menuconfig` → WellD Configuration). In this mode:

- The device stays awake for `CONFIG_WELLD_DIAGNOSTIC_STAY_AWAKE_SEC` (default 60 s) after each sensor read.
- Verbose INFO-level logs continue during the awake window.
- Deep sleep is still entered after the window expires, so the device does not run indefinitely.

Use this to verify sensor readings, Zigbee join behavior, and OTA query/response without recompiling between tests.

## Power Measurements

Target deep-sleep current: **< 50 µA** (typical ~20 µA with all GPIOs isolated).

If your measurement is higher:

1. **GPIO leakage:** Ensure VLOOP (GPIO5), BATT_DIV_EN (GPIO15), and CHARGER_CE (GPIO4) are all driven LOW before `esp_deep_sleep()`. The firmware does this automatically in `enter_deep_sleep()`.
2. **I²C pull-ups:** Internal pull-ups are enabled on SDA/SCL. If external pull-ups are also present, the combined resistance may leak current. Remove one set.
3. **ADS1115 power-down:** The ADS1115 enters power-down after each single-shot conversion. If DRDY is stuck low, the device may not sleep. Check GPIO12.

## Quick Checks Checklist

- [ ] Battery voltage > 3.0 V (measure at BAT+ / BAT− terminals — 1S2P pack minimum safe discharge)
- [ ] Solar charging LED (if populated) is off or on as expected
- [ ] `idf.py monitor` shows `BOOT` → `SENSOR_OK` → `ZB_SENT` within ~10 s
- [ ] Zigbee2MQTT logs show `Device 'WellD-v1' joined` on first pairing
- [ ] MQTT payload contains `water_level`, `battery_voltage`, `temperature`
- [ ] OTA `.zigbee` file is picked up by Z2M (`z2m/OTA` log shows query response)
