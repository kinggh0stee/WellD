# Troubleshooting WellD

This guide helps diagnose common issues in the field and during bench testing.

## Serial Log Decision Tree

Connect USB and open the serial monitor: `idf.py -p /dev/ttyACM0 monitor` for the PCB's USB-C (the ESP32-C6's native USB — Windows shows a COM port, macOS `/dev/cu.usbmodem…`). A dev board's separate UART port is usually `/dev/ttyUSB0`. The native USB port drops off the bus while the chip deep-sleeps; `idf.py monitor` waits and reconnects at the next wakeup.

### 1. No serial output at all

- **Check power:** The on-board DW01A protection isolates the cell below ≈2.4 V (and the low-battery guard stops reporting at or below 3.2 V). Charge the cell first — either charger input (USB or solar) recovers a protection-tripped cell. Also check the cell is seated in the BT1 carrier with correct polarity.
- **Check USB cable:** Some cables are charge-only (no data lines). Try a different cable.
- **Check bootloader baud:** ESP32-C6 boots at 115200; ensure your terminal is set correctly.
- **Brownout reset loop:** If you see `rst:0x1 (POWERON)` repeatedly, the USB port may not supply enough current for the 12 V boost + Zigbee TX spike. Power from a charged battery while keeping USB connected for serial.

### 2. `I2C init failed — aborting wakeup`

- **SDA/SCL shorted:** Check GPIO18/19 (and the U9 SDA/SCL pins) for solder bridges or debris.
- **ADS1115 not answering:** Check U9's MSOP-10 solder joints and its 3V3 supply. Its ADDR pin is tied to GND on the PCB (address 0x48 — there is no jumper). On a dev-board build, see [`docs/wiring.md`](docs/wiring.md).
- **Pull-ups missing:** The firmware enables internal I²C pull-ups, but if the bus capacitance is high, add external 4.7 kΩ pull-ups to 3V3.

### 3. `transducer open loop (voltage=... mV, < 3.5 mA)`

- **Wiring fault:** Check LOOP+ / LOOP− terminals. A disconnected transducer reads near 0 mV.
- **Transducer polarity reversed:** Some two-wire transducers are polarity-sensitive.
- **Shunt resistor missing:** Verify R2/R4 (100 Ω) are populated.
- **TVS conducting:** If D9/D10 (SMAJ5.0A) has failed short, the loop current bypasses the shunt.

### 4. `Zigbee send failed (N consecutive)` repeatedly

1. **Coordinator down:** Verify Zigbee2MQTT / coordinator are online and on the channel mask configured in `CONFIG_WELLD_ZIGBEE_CHANNEL_MASK`.
2. **Range:** Move the device closer to the coordinator. The C6's on-chip 802.15.4 range is ~10–30 m indoors depending on walls.
3. **Channel mismatch:** Narrow `CONFIG_WELLD_ZIGBEE_CHANNEL_MASK` to the coordinator's exact channel (e.g., `0x00001000` for channel 12) to speed up joins.
4. **Coordinator replaced / network re-formed:** the device keeps its old network membership and never wipes it on its own (an outage would otherwise orphan it). Factory-reset it (hold GPIO23 / TP13 LOW at power-on) and re-pair with permit-join open. From the third consecutive failure the device backs off to its maximum sleep interval (`backing off to … s` in the log), so expect up to `CONFIG_WELLD_SLEEP_MAX_SEC` before it retries.
5. **Interference:** The 2.4 GHz band is crowded. Check for Wi-Fi access points on overlapping channels.

### 5. `battery critically low (X.XX V <= 3.20 V) — skipping send`

- **Battery genuinely flat:** Charge via USB or solar.
- **Measurement error:** Verify the divider ratio in Kconfig matches R7/R8 (100 kΩ / 100 kΩ, ratio 200).

### 5a. `battery reading X.XX V is implausible — divider/AIN2 fault? ignoring it`

The device read under 2.0 V on the battery divider, which a running device cannot have, so it treats this as a measurement fault. The reading is dropped (no `battery_voltage` / `battery` published) and the low-battery guard is skipped, so reports keep flowing.

- **Dev board without a divider:** expected, provided AIN2 is tied to GND — set `CONFIG_WELLD_BATT_REPORT_ENABLED=n` to drop the EP2 endpoint entirely. Never leave AIN2 floating: a floating input can read like a flat cell and trip the low-battery guard instead.
- **WellD PCB:** check R7/R8, the Q5 high-side P-FET and its Q2 driver on GPIO15 (TP for VBAT and the divider mid-point), and the AIN2 trace.

### 6. OTA issues

- **OTA image rejected:** Ensure `--manufacturer-code 0x1234` and `--image-type 0x0001` match the hardcoded values in `components/zigbee/zigbee.c`. Do not use `0xFFFF` wildcards.
- **OTA never starts:** the device asks for an image (Query Next Image) once per wakeup, so after requesting the update in Zigbee2MQTT wait for its next wakeup. Check that the `.zigbee` file is listed in Z2M's local OTA override index and that `ota: true` is set in the converter.
- **OTA stalled:** a download is aborted after `CONFIG_WELLD_OTA_STALL_TIMEOUT_SEC` (default 240 s) **without receiving a block** — slow but moving transfers are never cut off. The abort is logged as `OTA_ABORT`.
- **`OTA failed: malformed .zigbee file`:** pack images with `tools/ota_image_create.py` — the device parses the Zigbee OTA file format and writes only the Upgrade Image element.
- **Version not increasing:** the device only installs a higher `--file-version`. Bump `PROJECT_VER` in `CMakeLists.txt` and re-pack.

## Reading the RTC Event Log

With `CONFIG_WELLD_RTC_LOG_PRINT_ENABLED=y` (WellD Configuration menu; off by default because it adds up to 17 lines to every wakeup), each wakeup prints the last 16 events kept in RTC memory:

```
I (35) main: RTC event log (last 5 entries):
I (35) main:   [0] t=1234s  BOOT
I (35) main:   [1] t=1250s  SENSOR_OK
I (36) main:   [2] t=1255s  ZB_FAIL
I (36) main:   [3] t=1560s  BOOT
I (36) main:   [4] t=1575s  LOW_BATT_SKIP
```

This is invaluable for diagnosing devices that failed in the field and are later retrieved. The `t=` value is seconds since the most recent cold boot, from the RTC-backed system clock, which keeps counting through deep sleep (a power loss resets it).

| Event code | Meaning |
|-----------|---------|
| `BOOT` | Cold boot or deep-sleep wakeup |
| `SENSOR_OK` | Valid water-level reading |
| `ZB_SENT` | Reports queued with the network up and the send window elapsed (no end-to-end ACK is requested) |
| `ZB_FAIL` | Zigbee send failed or timed out |
| `LOW_BATT_SKIP` | Battery at/below threshold; sensors, send and NVS writes skipped |
| `OTA_ABORT` | OTA download aborted (stall, malformed file, flash/validation error, or by the server) |
| `FACTORY_RESET` | GPIO23 factory reset — NVS and Zigbee network state erased |
| `BROWNOUT` | Previous reset was a brownout |
| `WATCHDOG` | Previous reset was a task/interrupt watchdog |
| `NVS_WIPE` | Retired in 1.2.0 (the automatic 5-failure wipe was removed); appears only in logs written by older firmware |

## Diagnostic Mode (Bench Testing)

Enable `CONFIG_WELLD_DIAGNOSTIC_MODE_ENABLED=y` (via `idf.py menuconfig` → WellD Configuration). In this mode:

- The device stays awake for `CONFIG_WELLD_DIAGNOSTIC_STAY_AWAKE_SEC` (default 60 s) after each sensor read.
- Verbose INFO-level logs continue during the awake window.
- Deep sleep is still entered after the window expires, so the device does not run indefinitely.

Use this to verify sensor readings, Zigbee join behavior, and OTA query/response without recompiling between tests.

## Power Measurements

Target deep-sleep current: **< 50 µA**. The PCB's budget is ≈25–30 µA at 4.2 V — ESP32-C6 ≈7 µA, HT7333 ≈4 µA, CN3791 ≈9 µA, DW01A ≈3 µA plus small leakages (fab blocker 10e in [`hardware/pcb/schematic_connections.md`](hardware/pcb/schematic_connections.md)); flag anything above ≈35 µA.

If your measurement is higher:

1. **Loop or divider switch left on:** VLOOP (GPIO5) and BATT_DIV_EN (GPIO15) must be LOW in sleep — `enter_deep_sleep()` drives them LOW before isolating the pads, and the R27/R26 pull-downs hold the switches off. Measure TP2 (VLOOP): it should be 0 V while the device sleeps.
2. **I²C or ALERT held low:** the pull-ups on SDA/SCL (GPIO18/19) and ALERT/RDY (GPIO22) only draw current while something holds a line LOW. If one measures LOW during sleep, a stuck device is holding it — power-cycle and check for a solder bridge.
3. **ADS1115 power-down:** it powers down after each single-shot conversion (≈0.5 µA typical); a higher figure points at a damaged part or a leaking input-protection diode.

## Quick Checks Checklist

- [ ] Cell voltage > 3.2 V (measure across the BT1 carrier tabs — the firmware's reporting floor; DW01A protection trips at ≈2.4 V)
- [ ] Solar charging LED (if populated) is off or on as expected
- [ ] `idf.py monitor` shows the sensor lines and `zigbee: joined; reporting level=…` (or `rejoined; …`) within ~10 s of the wakeup
- [ ] Zigbee2MQTT logs show `Device 'WellD-v1' joined` on first pairing
- [ ] MQTT payload contains `water_level`, `battery_voltage`, `temperature`
- [ ] OTA `.zigbee` file is picked up by Z2M (`z2m/OTA` log shows query response)
