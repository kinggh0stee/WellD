# WellD Hardware Options

Two hardware paths are supported. Both run identical firmware.

---

## Option 1 — Off-the-shelf dev board (recommended starting point)

Use any ESP32-C6 dev board with exposed ADC1 pins. No custom PCB required. Full
wiring instructions, BOM, and configuration details are in the [main README](../README.md).

**Pros:** in-hand in days; no PCB lead time; easy to prototype and iterate.  
**Cons:** larger footprint; no screw terminals; no onboard LiPo charger or protection circuit.

---

## Option 2 — Custom PCB (`hardware/pcb/`)

A purpose-built 80 × 55 mm 2-layer board. Fabricated by PCBWay (PCBWay hand-attaches the U.FL→SMA pigtail post-reflow).

**Key ICs:**

| IC | Role |
|----|------|
| AP63205 (SOT-23-6) | 3.3 V synchronous buck, 22 µA Iq, fed from 2S LiPo (6.0–8.4 V) |
| MT3608B (SOT-23-6) | 12 V boost for 4–20 mA VLOOP rail, GPIO5-gated |
| CN3722 (SOP-8) | MPPT solar charger, 5–25 V input, 8.4 V CV, 500 mA |
| TP5100 (SOP-8) | USB-C 2S boost charger, 5 V in → 8.4 V / 1 A out |
| ADS1115 (MSOP-10) | 16-bit I²C ADC — all depth and battery voltage measurements |
| ESP32-C6-MINI-1U | MCU + Zigbee 802.15.4 radio, external U.FL antenna |

**Battery:** 2S1P 18650 LiPo, 6.0 V (discharged) to 8.4 V (full). Connected via AMASS XT30PW-F right-angle THT connector (J1, LCSC C601498), Pin 1=BAT+, Pin 2=BAT−. No discrete cell protection on the PCB — the 2S1P pack contains an integrated PCM.

**GPIO map:**

| GPIO | Function |
|------|----------|
| 4 | TP5100 CE — HIGH enables USB-C charging; R37 holds LOW during deep-sleep |
| 5 | MT3608B EN — HIGH activates 12 V VLOOP boost for 4–20 mA measurement window |
| 6 | CN3722 /CHRG input (active-LOW = solar charging in progress) |
| 7 | DS18B20 1-Wire data (J6 screw terminal) |
| 10 | I²C SDA (ADS1115 only) |
| 11 | I²C SCL (ADS1115 only) |
| 12 | ADS1115 ALERT/DRDY interrupt |
| 15 | BATT_DIV_EN — gates Q2 to enable battery voltage divider during measurement only |

**Adds over the dev-board path:**
- Pluggable screw terminals (Phoenix Contact MC 1.5/3-ST-3.5, 3.5 mm pitch) for all sensor wires — no soldered leads in the field
- Dual 2S LiPo charging: TP5100 (USB-C, 1 A) + CN3722 MPPT (solar panel, 500 mA)
- Solar panel input (2-pin screw terminal, J12): 5–25 V panel; MPPT target adjustable via R20/R21
- Reverse-polarity MOSFET (AO3407, D5) — no discrete cell protection needed (pack PCM)
- ADS1115 16-bit I²C ADC replaces ESP32 ADC for all precision measurements (depth + battery)
- PRTR5V0U2X dual-channel TVS on both 4–20 mA ADC inputs
- Second 4–20 mA channel (GPIO2/CH2) pre-wired and ready for a second transducer
- I²C header (J8) and 6-pin GPIO expansion header (J9) for future sensors

**3D-printed enclosure (`hardware/case/`):**
- OpenSCAD parametric design (`hardware/case/welld_case.scad`) — print in ASA or PETG for UV/moisture resistance
- M16 cable gland pass-throughs on all faces (sensor wires, solar cable)
- USB-C slot and programming access on left wall
- Snap-fit lid with M3 corner screws
- External mounting tabs for wall/post mounting (concrete lid underside option in ASSEMBLY.md)

**Files:**

| File | Contents |
|------|----------|
| [`pcb/design.md`](pcb/design.md) | Full schematic block descriptions, GPIO table, PCB layout notes, solar charging |
| [`pcb/bom.csv`](pcb/bom.csv) | Bill of materials with MPNs and LCSC order codes |
| [`pcb/welld.kicad_pro`](pcb/welld.kicad_pro) | KiCad 7 project file |
| [`pcb/welld.kicad_sch`](pcb/welld.kicad_sch) | KiCad 7 schematic (all components, net labels) |
| [`pcb/welld.kicad_pcb`](pcb/welld.kicad_pcb) | KiCad 7 PCB layout (board outline + placements; user routes traces) |
| [`pcb/generate_kicad.py`](pcb/generate_kicad.py) | Script that regenerates the KiCad files from component data |
| [`case/welld_case.scad`](case/welld_case.scad) | OpenSCAD parametric enclosure |
| [`case/README.md`](case/README.md) | Printing and assembly instructions |

**Status:** reference design — KiCad files and case are generated; not yet fabricated or validated on hardware.
