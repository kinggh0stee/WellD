# WellD Assembly Guide

**Revision:** 1.0  
**PCB:** WellD v1 — ESP32-C6 Well-Level Monitor  
**Enclosure:** `hardware/case/welld_case.scad` (3D-printed, FDM)

---

## Table of Contents

1. [Tools and consumables](#1-tools-and-consumables)
2. [Cable glands — what to buy](#2-cable-glands--what-to-buy)
3. [Print the enclosure](#3-print-the-enclosure)
4. [Case preparation — heat-set inserts](#4-case-preparation--heat-set-inserts)
5. [Case preparation — cable glands and SMA bulkhead](#5-case-preparation--cable-glands-and-sma-bulkhead)
6. [PCB assembly (SMD soldering)](#6-pcb-assembly-smd-soldering)
7. [Flash firmware](#7-flash-firmware)
8. [Wiring sensors and solar panel](#8-wiring-sensors-and-solar-panel)
9. [Install PCB into case](#9-install-pcb-into-case)
10. [Battery connection and first power-up](#10-battery-connection-and-first-power-up)
11. [Seal and close](#11-seal-and-close)
12. [Zigbee commissioning](#12-zigbee-commissioning)
13. [Commissioning checklist](#13-commissioning-checklist)

---

## 1. Tools and consumables

| Item | Notes |
|------|-------|
| Soldering iron, 300–350 °C | Fine tip for SMD; brass-tip for heat-set inserts |
| Hot-air rework station | For SOP-8 / SOT packages |
| Solder — 63/37 or SAC305, 0.5 mm | Avoid lead-free on SMD packages smaller than SOT-23 |
| Flux pen | No-clean rosin type |
| Tweezers, ESD-safe | Curved tip for component placement |
| Multimeter | Continuity + voltage checks |
| USB-UART adapter (3.3 V logic) | For firmware flashing — CP2102, CH340, or FTDI |
| Jumper wires (3.3 V tolerant) | For TX/RX/EN/GND connections to J10 |
| M3 hex driver or screwdriver | For lid M3×8 screws |
| 20 mm step drill bit or 20.5 mm hole saw | **Only** if you print on a non-printed blank — case already has holes |
| Soldering iron tip (flat/chisel) | For pressing heat-set inserts |
| Silicone sealant, neutral-cure | e.g. Dow Corning 732 or Loctite SI 5366 |
| Wire strippers | For sensor cable prep |
| Cable ties or velcro strap | For routing internal cables |
| Isopropyl alcohol (IPA) 99 % | PCB cleaning before sealing |

---

## 2. Cable glands — what to buy

The case uses **M16×1.5 compression cable glands** throughout. Every hole in the case wall is 20.5 mm diameter — the exact clearance for an M16 thread. The glands screw in from outside, and their lock nut tightens from inside.

### Gland specification

| Parameter | Value |
|-----------|-------|
| Thread | M16 × 1.5 (metric fine) |
| Panel hole required | 20.5 mm (already in printed case) |
| Cable range | 4–10 mm OD (covers all cables in this design) |
| Body material | PA66 nylon — UV-stable, adequate for outdoor use |
| Rating | IP68 (compression-seal on cable jacket) |
| Colour | Black or grey standard |

### Recommended parts

| Supplier | Part | Notes |
|----------|------|-------|
| **Digi-Key / Mouser** | Heyco M3200-C-01 | M16, PA66, 4–10 mm, IP68 |
| **LCSC** | C5149780 or search "M16 cable gland PA66" | Budget; adequate for protected installs |
| **Phoenix Contact** | 1411136 (GMBH M16) | Higher quality, stocked at Farnell/RS |
| **Lapp Kabel** | SKINDICHT® SHV-M16 (53112060) | Industrial, well-suited for outdoor/wet |
| **Generic (AliExpress)** | Search "M16 cable gland nylon 4-10mm" | $0.40–0.80 each in packs of 10–20 |

> **How many to buy:**
> - 5 × bottom wall (sensor 1, sensor 2, DS18B20, spare sensor, solar panel)
> - 1 × left wall (programming/debug cable — optional; leave blanked if not needed)
> - 1 × right wall (battery cable)
> - 1 × back wall (solar cable — same side as SMA)
> - Subtotal **8 glands** per unit, plus blanking plugs for holes you don't use

### Blanking plugs (unused holes)

For any gland hole you don't route a cable through, install an **M16 blanking plug** to maintain IP68. Options:
- Phoenix Contact 1420563 (M16 PA blind plug)
- Generic M16 hex-head blanking plug (nylon)

### Cable sizes for reference

| Cable | Typical OD | Gland size |
|-------|-----------|------------|
| 4–20 mA transducer, 2-wire | 5–7 mm | M16 (4–10 mm range) ✓ |
| DS18B20 waterproof probe lead | 4–5 mm | M16 ✓ |
| 5W solar panel cable | 5–6 mm | M16 ✓ |
| LiPo pigtail (JST-PH) | 3–4 mm + connector | M16 (may need small grommet) |
| USB-C cable | 5–8 mm | USB-C slot cutout (no gland) |

---

## 3. Print the enclosure

### Material

| Priority | Material | Why |
|----------|----------|-----|
| Recommended | **ASA** | UV-stable, moisture-resistant, outdoor-rated |
| Alternative | **PETG** | Easier to print than ASA; adequate for sheltered installs |
| Avoid | PLA | Degrades in UV and heat; not suitable outdoors |

### Print settings

| Setting | Base | Lid |
|---------|------|-----|
| Layer height | 0.2 mm | 0.15 mm (better label detail) |
| Perimeters / walls | 4 | 4 |
| Top/bottom layers | 5 | 5 |
| Infill | 40 % gyroid | 40 % gyroid |
| Supports | **None** — design is support-free | None |
| Bed temperature | 90 °C (ASA) / 70 °C (PETG) | Same |
| Enclosure | Required for ASA | Recommended for PETG |
| Orientation | Print base open-face-up | Print lid label-face-down for best surface |

### Export from OpenSCAD

```bash
# Base only
openscad -D "SHOW_BASE=true" -D "SHOW_LID=false" \
  --render -o welld_base.stl hardware/case/welld_case.scad

# Lid only  
openscad -D "SHOW_BASE=false" -D "SHOW_LID=true" \
  --render -o welld_lid.stl hardware/case/welld_case.scad
```

---

## 4. Case preparation — heat-set inserts

You need **8 M3 heat-set inserts** total:
- 4 × in the corner boss bores (lid screws) — 6 mm deep blind bore, top of each boss
- 4 × in the standoff bores (PCB mounting) — 3 mm deep, top of each standoff

**Procedure:**

1. Set soldering iron to **200–220 °C** (lower than solder temperature — too hot causes deformation).
2. Place insert on the bore opening, flat end down.
3. Press the flat soldering iron tip onto the insert and apply slow, even downward pressure.
4. The insert sinks flush with (or 0.1–0.2 mm below) the surface. Do **not** push below flush.
5. Let cool 60 seconds before handling.
6. Check with an M3 screw — it should thread in smoothly with light resistance.

> Inserts to use: M3 × 4 mm length, 4.5 mm OD (standard heat-set, e.g. CNC Kitchen or
> Ruthex RX-M3x4). The boss bore is 4.5 mm ID — an exact press-fit before heat.

---

## 5. Case preparation — cable glands and SMA bulkhead

### Cable glands

Each M16 cable gland ships in three pieces: body, sealing insert, lock nut.

1. Remove the sealing insert and set aside.
2. From **outside** the case, thread the gland body into the 20.5 mm hole by hand.
3. From **inside**, tighten the lock nut finger-tight — do not torque yet (cable routing comes first).
4. Repeat for all holes that will carry cables. Install blanking plugs in unused holes now.

### SMA female bulkhead (back wall)

1. The back wall has one 6.5 mm hole (right of the solar cable gland).
2. From outside, insert the SMA female bulkhead connector (e.g. Amphenol RF 132289).
3. Slide the washer and nut onto the thread from inside, tighten to **0.5 N·m** (fingertight + ¼ turn with spanner).
4. Apply a thin bead of neutral-cure silicone around the flange on the outside face for IP68 sealing.

### U.FL to SMA pigtail

1. Connect the U.FL end of the pigtail to J3 on the PCB. Press straight down until you feel a snap. Do not rotate — U.FL connectors are push-on/pull-off.
2. Route the cable along the PCB top edge, coiling any excess slack in a loop.
3. Connect the SMA end to the bulkhead after the PCB is installed.

---

## 6. PCB assembly (SMD soldering)

The PCB uses all SMD components. Refer to `hardware/pcb/bom.csv` for values and packages.

### Recommended soldering order

1. **Paste and reflow (top side):** Apply solder paste to all F.Cu pads, place all SMD components, reflow.
   - If hand-soldering: work smallest to largest — 0402 passives → SOT-23 ICs → SOP-8 ICs → ESP32 module.
2. **Bottom side (if any):** No bottom-side components in this design.
3. **Through-hole / tall components last:** JST-PH battery connector (J1), tactile switches (SW1, SW2), 2.54 mm headers.

### Critical assembly notes

| Item | Note |
|------|------|
| **U7 (CN3791) PROG pin** | R19 sets solar charge current. Default 2.0 kΩ = 500 mA. Do not omit. |
| **D6 orientation** | Cathode (band) toward U7 VIN pin — current flows panel → charger. Reverse polarity destroys U7. |
| **D5 (AO3407) orientation** | Gate to VBAT, source to battery input. Confirm orientation with markings. |
| **J3 (U.FL) soldering** | Reflow only — do not hand-solder. Flux generously, minimal heat. |
| **R20/R21 MPPT divider** | Default R20=36 kΩ + R21=10 kΩ sets MPPT to 5.5 V. Change R20 to 30 kΩ for 5 V regulated panel. |
| **Module antenna clearance** | No solder bridges, no copper pour within 15 mm of ESP32 antenna zone. |
| **DNF components** | D2, D3, D7, R17, R18, R22 are "do not fit" in production — omit unless debugging. |

### Post-assembly checks (before powering)

- [ ] Visual inspection under magnification — no bridges, all pads wetted
- [ ] Continuity: +3V3 rail to GND → no short (expect >1 MΩ with battery absent)
- [ ] Continuity: VBAT to GND → no short
- [ ] Continuity: VSOLAR to GND → no short
- [ ] Check D6 orientation with diode-test mode (forward drop ~0.3 V anode→cathode)
- [ ] IPA wash and hot-air dry

---

## 7. Flash firmware

**Prerequisites:** ESP-IDF v5.3.5 installed and sourced ([Espressif getting-started guide](https://docs.espressif.com/projects/esp-idf/en/v5.3.5/esp32c6/get-started/)).

```bash
# Clone if not already present
git clone https://github.com/kinggh0stee/WellD.git
cd WellD
idf.py set-target esp32c6
cp sdkconfig.defaults.local.example sdkconfig.defaults.local
$EDITOR sdkconfig.defaults.local    # set ADC channel, depth range, sleep interval
idf.py build
```

**Enter download mode:**

1. Connect USB-UART adapter to J10: GND→GND, TX→RX (pin 4), RX→TX (pin 3), 3.3V→3.3V (pin 1 optional if board is battery-powered).
2. Hold **SW2 (BOOT)** down.
3. Press and release **SW1 (RESET)**.
4. Release SW2.
5. The ESP32-C6 is now in download mode.

```bash
idf.py -p /dev/ttyUSB0 flash
```

After flashing, press SW1 (RESET) once to boot normally.

**Verify serial output:**

```bash
idf.py -p /dev/ttyUSB0 monitor
```

Expected on first boot:
```
I (sensor): raw=XXXX  voltage=XXXX mV  current=XXXX µA  level=X.XX m
I (zigbee): starting BDB commissioning...
```

---

## 8. Wiring sensors and solar panel

Prepare each cable before routing through glands. Strip **8 mm** of outer jacket and **3 mm** of each conductor. Tin conductor ends.

### 4–20 mA pressure transducer (J4 or J5)

```
J4 pin 1 — VLOOP  →  transducer (+) / VCC wire
J4 pin 2 — SIG    →  transducer (−) / signal return wire
J4 pin 3 — GND    →  GND (optional shield drain)
```

- VLOOP must be supplied externally (8–24 V DC) unless SJ1 is closed (3.3 V loop, non-standard sensors only).
- Default: SJ2 closed — J4 and J5 share the same VLOOP supply.
- Set `CONFIG_WELLD_SENSOR_ADC_CHANNEL=0` for channel 1 (J4), `=2` for channel 2 (J5).

### DS18B20 temperature probe (J6)

```
J6 pin 1 — VCC   →  DS18B20 red wire (VCC)
J6 pin 2 — DATA  →  DS18B20 yellow/white wire (data)
J6 pin 3 — GND   →  DS18B20 black wire (GND)
```

External power mode only — **do not** tie VCC to GND (parasite mode). Parasite mode will produce invalid out-of-range readings every wakeup and the firmware will discard them silently.

### Solar panel (J12)

```
J12 pin 1 — SOLAR+  →  solar panel positive output
J12 pin 2 — GND     →  solar panel negative / ground
```

- Panel voltage: **5–6.5 V nominal, Voc ≤ 7.5 V**. This is not USB 5V — use a bare panel output, not a regulated USB output that has already limited current.
- A 5 W / 6 V rated panel (e.g. Voltaic P110 or equivalent) connected directly to J12 is correct.
- Reverse polarity on J12 will be blocked by D6 but not corrected — verify polarity before first power-on.

### LiPo battery (J1)

- Use a single-cell LiPo, nominal 3.7 V, capacity 500 mAh–3000 mAh.
- 2-pin JST-PH 2.0 mm connector. Verify polarity against JST marking (+ on left when looking at the PCB from component side).
- Do **not** connect a battery without first verifying there are no assembly shorts.

---

## 9. Install PCB into case

1. Route all sensor cable leads through their respective cable glands (gland bodies already installed in step 5, lock nuts loose).
2. Lower the PCB into the base, aligning the four mounting holes over the standoffs.
3. Secure with M3 × 6 mm pan-head screws or press-fit brass inserts — 4 × M3 screws, hand-tight.
4. Connect the U.FL to SMA pigtail SMA end to the bulkhead (tighten SMA nut finger-tight + ¼ turn with 8 mm spanner).
5. Connect the JST-PH battery connector (J1).
6. Plug sensor connectors into J4–J7 and solar into J12.
7. Dress internal cables — route along the PCB perimeter, secure with a small cable tie or loop of velcro strap to the nearest standoff.

> **Cable tie anchor point:** Thread a 2.5 mm cable tie through one of the two M3 standoff gaps; this keeps the LiPo pigtail from fouling the PCB during lid removal.

---

## 10. Battery connection and first power-up

1. Before connecting the battery, confirm:
   - VBAT to GND: no short with multimeter
   - +3V3 to GND: no short
2. Connect battery J1.
3. The status LED (D4, GPIO13) should blink once and the board begins its first wake cycle.
4. Attach USB-UART adapter to J10 and open the monitor (`idf.py monitor`) to observe the first boot.

**Expected serial sequence (first boot, no Zigbee coordinator):**
```
I (sensor): raw=1847  voltage=1485 mV  current=14850 µA  level=3.42 m
I (sensor): temperature=12.3 °C
E (zigbee): timeout — no coordinator found
W (main):   Zigbee send failed (1/5)
I (main):   sleeping 300 s
```

If `water_level` reads `-1.0` or `null`, check sensor wiring and VLOOP supply.

---

## 11. Seal and close

**IP54 baseline (no sealant, correct glands):**
- All cable glands installed and lock nuts tightened to hand-tight + ¾ turn with spanner (do not overtighten PA66 — 1.5–2 N·m).
- Blanking plugs installed in all unused M16 holes.
- Lid seated with inner lip inside base opening.
- 4 × M3 × 8 mm button-head screws through lid into heat-set inserts. Tighten evenly, diagonal pattern, 0.5–0.8 N·m.

**IP68 upgrade (sealant bead):**
1. Run a 2 mm bead of **neutral-cure silicone** (e.g. Dow Corning 732, Loctite SI 5366) around the lid lip perimeter.
2. Seat lid immediately, tighten screws.
3. Wipe excess sealant from exterior.
4. Cure 24 hours before submerging or pressure-testing.

> Avoid acetoxy ("vinegar smell") silicone near electronics — acetic acid vapours corrode copper pads. Use only neutral-cure or neutral-oxime silicone.

---

## 12. Zigbee commissioning

1. Enable permit-join in Zigbee2MQTT `configuration.yaml`:
   ```yaml
   permit_join: true
   ```
2. Install the external converter **before** pairing:
   ```bash
   cp zigbee2mqtt/welld.js /opt/zigbee2mqtt/data/
   ```
   Add to `configuration.yaml`:
   ```yaml
   external_converters:
     - welld.js
   ```
   Restart Zigbee2MQTT.
3. Power on the WellD board. The first join takes up to 25 seconds.
4. Monitor `zigbee2mqtt/<friendly_name>` for the first payload:
   ```json
   { "water_level": 3.42, "temperature": 12.3, "battery_voltage": 3.95 }
   ```
5. Disable permit-join once paired.

**Solar charge indicator:**  
If D7 is populated (optional DNF), it illuminates during active solar charging. The CN3791 DONE pin goes low when the battery reaches 4.2 V — the LED extinguishes.

---

## 13. Commissioning checklist

### Electrical
- [ ] No assembly shorts — VBAT/3V3/VSOLAR to GND all open
- [ ] Battery voltage reads > 3.5 V at J1 before connecting
- [ ] +3V3 rail measures 3.28–3.32 V (TPS7A0533 ±2 %)
- [ ] D4 status LED visible during active phase (unless SJ3 cut)

### Firmware
- [ ] Serial output shows valid `level` reading (not -1.0)
- [ ] Serial output shows valid `temperature` (not -127)
- [ ] Sleep duration appears in log: `sleeping 300 s`

### Zigbee
- [ ] Device appears in Zigbee2MQTT after pairing
- [ ] MQTT payload received with `water_level`, `temperature`, `battery_voltage`
- [ ] Home Assistant entities auto-created: `sensor.<name>_water_level`, etc.

### Solar
- [ ] Solar LED (D7) illuminates when panel is in sunlight (if D7 populated)
- [ ] Battery voltage rises over ~1 hour in direct sun with no USB connected

### Mechanical
- [ ] All cable glands tightened — no cable movement under moderate tug (5 N)
- [ ] M16 blanking plugs installed in unused holes
- [ ] SMA antenna connector snug — no wobble
- [ ] Lid seated flush — no gaps at perimeter
- [ ] 4 × M3 lid screws tight
- [ ] Antenna attached to SMA bulkhead

---

*gh0stee.com — WellD v1*
