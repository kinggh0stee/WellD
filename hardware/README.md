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
- Onboard LiPo charger (TP4056) + cell protection (DW01A + FS8205A)
- TPS7A0533 1 µA-Iq LDO to maximise deep-sleep battery life
- PRTR5V0U2X dual-channel TVS on both 4–20 mA ADC inputs
- Second 4–20 mA channel (GPIO2/CH2) pre-wired and ready for a second transducer
- I²C header and 6-pin GPIO expansion header for future sensors
- All seven ADC1 channels (GPIO0–GPIO6) reserved for analog; DS18B20 on GPIO7

**Files:**

| File | Contents |
|------|----------|
| [`pcb/design.md`](pcb/design.md) | Full schematic block descriptions, GPIO table, PCB layout notes |
| [`pcb/bom.csv`](pcb/bom.csv) | Bill of materials with MPNs and LCSC order codes |

**Status:** reference design — not yet fabricated or validated on hardware.
