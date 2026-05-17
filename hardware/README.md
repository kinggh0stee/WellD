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

A purpose-built 80 × 55 mm 2-layer board targeting the Hammond 1551K IP65 enclosure.

**Adds over the dev-board path:**
- Pluggable screw terminals (Phoenix Contact MC 1.5/3-ST-3.5, 3.5 mm pitch) for all sensor wires — no soldered leads in the field
- Dual LiPo charging: TP4056 (USB-C, 580 mA) + CN3791 MPPT (solar panel, 500 mA)
- Solar panel input (2-pin screw terminal, J12): 5 W / 5–6.5 V panel for trickle charging
- Cell protection (S-8261AAYFT + FS8205A) and reverse-polarity MOSFET (AO3407)
- TPS7A0533 1 µA-Iq LDO to maximise deep-sleep battery life
- PRTR5V0U2X dual-channel TVS on both 4–20 mA ADC inputs
- Second 4–20 mA channel (GPIO2/CH2) pre-wired and ready for a second transducer
- I²C header and 6-pin GPIO expansion header for future sensors
- ADC1 channels GPIO0–GPIO3 available for analog backup (GPIO4–GPIO6 are power-control pins); DS18B20 on GPIO7

**3D-printed enclosure (`hardware/case/`):**
- OpenSCAD parametric design — print in ASA or PETG for UV/moisture resistance
- M16 cable gland pass-throughs on all faces (sensor wires, solar cable)
- USB-C slot and programming access
- Snap-fit lid with M3 corner screws
- External mounting tabs for wall/post mounting

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
