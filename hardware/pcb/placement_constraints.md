# WellD PCB — Placement Constraints

These are **rules and groupings only** — no positions dictated. Place components wherever you want in KiCad, but respect these constraints.

---

## Board Edge Requirements

These components must land on a specific board edge:

| Component | Edge | Why |
|-----------|------|-----|
| J13 (USB-C) | Any short edge (55mm side) | Connector body extends off-board; case cutout is on this wall |
| J3 (SMA edge-mount) | Any short or long edge | Antenna port must clear the board outline; RF port protrudes ~3mm past Edge.Cuts |
| J4, J5, J6, J7, J12 (screw terminals) | One long edge (80mm side) | Field wiring exits through cable glands on this face of the enclosure |
| J1 (XT30 battery) | Same long edge as terminals, or short edge | Right-angle body exits toward one wall; match the case battery slot |
| J10 (programming header) | Any edge or interior — but keep accessible | Pogo-pin fixture needs vertical clearance; keep clear of large caps |

> **J3 and J13 must be on different edges** — they cannot share the same short edge (connector bodies will clash).

---

## Must-Be-Near Groups (hard rules from datasheets)

### Group A — MT3608B boost hot loop
`U8 → L1 → C20/C22` must form a tight triangle.
- L1 within **3mm** of U8 SW pin (pin 3)
- C20 and C22 within **3mm** of U8 VOUT
- C_BST (100nF) within **1mm** of U8 BST pin (pin 6) to SW node
- C19 within **2mm** of U8 VIN pin
- **No copper pour under L1 on either layer** — switching node EMI
- Keep the SW→L1→VOUT hot trace under **10mm**, min **0.5mm wide**
- Surround this island with a GND via-stitch perimeter

### Group B — AP63205 buck
`U1 → L2 → C_BUCK`
- L2 within **5mm** of U1 SW pin
- C_BUCK (10µF 0805) on the output side of L2, within **3mm**
- C9/C10 on U1 VIN side, within **2mm**
- C11/C12 on +3V3 output rail, near L2 output

### Group C — ADS1115 analog island
`U9, FB1, C23, C24, R9, R10, R_DRDY`
- FB1 in series with +3V3 feed to U9 VDD
- C23 (100nF) and C24 (1µF) on the **U9 side** of FB1, within **1mm** of U9 VDD pin
- Keep U9 **≥20mm from U8** (MT3608B switching noise)
- Keep U9 away from L1 and L2 (inductor EMI)
- R_DRDY (4.7kΩ pull-up for ADS_DRDY) can be anywhere near U9 or near GPIO12 trace

### Group D — CN3722 solar charger thermal
`U7, C17, C18, R19, R20, R21, R33, R34`
- Place a **10×10mm solid copper pour on F.Cu** under and around U7, connected to GND via ≥4 thermal vias (0.6mm drill)
- Mirror the pour on B.Cu and stitch with the same vias
- U7 must be **≥15mm from U6** (ESP32 module)
- U7 and U8 must be **≥8mm apart**

### Group E — 4-20mA shunt and protection chain (CH1)
`J4 → D9 → R2 → C_SH1 → R3 → D1 → C3/C4 → U9 AIN0`
- D9 within **3mm** of J4 SIG terminal
- C_SH1 within **1mm** of R2 pads (across the shunt)
- TP5 (test point) between R2 and R3
- Same grouping for CH2: `J5 → D10 → R4 → C_SH2 → R5 → D1 CH2 → C5/C6 → U9 AIN1`

### Group F — ESP32-C6 module decoupling
`U6, C14a–C14d, C15`
- All four 100nF caps (C14a–C14d) within **2mm** of the module VCC3V3 pads
- C15 (10µF bulk) within **5mm** of module
- Keep a **15mm no-copper keep-out** zone around the module's on-chip antenna area (the far end from the U.FL pad) on both layers

### Group G — TP5100 USB charger cluster
`J13, U11, F2, U12, C27, C28, C29, R35, R36, R37, R38, R_CC1, R_CC2`
- U12 near J13; keep VIN trace (F2 → U12 VIN) under **10mm**
- R_CC1 and R_CC2 within **3mm** of J13 CC1/CC2 pins
- C28 within **2mm** of U12 VIN pin
- C29 within **3mm** of U12 VBAT pin
- R35 within **3mm** of U12 PROG pin
- Add **8×8mm solid GND copper pour on F.Cu** under U12 for thermal relief
- U11 and F2 between J13 VBUS pin and U12 VIN — keep total VUSB trace under **15mm**

### Group H — Battery input protection
`J1, D13, D5, R31`
- D13 (SMAJ10CA) within **5mm** of J1 BAT+ pin
- D5 and R31 between D13 and VBAT rail — R31 within **2mm** of D5 gate

### Group I — DS18B20 interface
`J6, D12, R6, R28, R32`
- D12 within **3mm** of J6 DATA terminal (pin 2)
- R6 (pull-up) can be anywhere between +3V3 and the 1WIRE net
- R28 in the VCC line between +3V3 and J6 pin 1

### Group J — Solar input protection
`J12, D14, D6, D8, C17, C21`
- D14 within **3mm** of J12 SOLAR+ pin (first TVS at the terminal)
- D6 between D14 and U7 VIN (Schottky backfeed block)
- D8 within **5mm** of C17 (second-stage TVS at CN3722 VIN)
- C21 within **3mm** of D8

---

## Must-Be-Apart Rules

| Components | Minimum gap | Reason |
|-----------|-------------|--------|
| U7 (CN3722) and U6 (ESP32) | 15mm | CN3722 dissipates up to 0.35W; thermal and RF isolation |
| U8 (MT3608B) and U9 (ADS1115) | 20mm | 1.2MHz switching noise corrupts ADC readings |
| U8 (MT3608B) and U7 (CN3722) | 8mm | Thermal — both dissipate power simultaneously |
| L1/L2 (inductors) and U9 (ADS1115) | 15mm | Inductor EMI fields |
| J3 (SMA) and U6 (module) | Route W1 pigtail — keep coax away from other signals |

---

## RF Layout Rules (J3, W1, U6)

The RF path is: **U6 U.FL pad → W1 pigtail cable → J3 SMA edge-mount**

W1 is a hand-attached cable — it is NOT pick-and-place. PCBWay installs it manually after reflow.

- J3 must be near the edge so the pigtail (~50mm) can reach U6's U.FL port without strain
- No PCB trace is needed for RF — W1 handles it
- Keep a **15mm no-copper keep-out** around the module's chip antenna area (opposite end from U.FL)
- Keep high-current power traces (VLOOP, VBAT) away from the U.FL pad area

---

## Thermal Copper Pours Required

| Component | Pour size | Layer | Via stitching |
|-----------|-----------|-------|---------------|
| U7 CN3722 | 10×10mm | F.Cu + B.Cu, GND net | ≥4 vias, 0.6mm drill, through to B.Cu |
| U12 TP5100 | 8×8mm | F.Cu, GND net | optional; helps with 1.5W dissipation |

---

## Test Point Placement Notes

- TP1/TP3/TP4: group near U1 AP63205 buck output
- TP2: near C20/C22 on VLOOP rail
- TP5/TP6: within 3mm of R2/R4 (on the R3/R5 side of the shunt)
- TP7: near J6 DATA, on the GPIO7 side of D12
- TP8/TP9: near J8 I²C header
- TP10: near J12 solar input terminal
- TP11: near J1 BAT+ terminal (before D5)
- TP12: near U6 GPIO12 area
- TP15: near U12 /CHRG pin
