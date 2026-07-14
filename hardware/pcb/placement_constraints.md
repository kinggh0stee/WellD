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
`Q3 → L1 → U8 SW → D15 → C20/C22` — the SW→D15→C20/C22 loop must be tight.
- L1 within **3mm** of U8 SW pin
- D15 (SS34 rectifier) within **3mm** of U8 SW pin; C20/C22 within **3mm** of D15 cathode
- C_BST (100nF) within **1mm** of U8 BST pin to SW node (fit even if pin 6 proves to be NC)
- C19 within **2mm** of U8 IN pin
- Q3/Q4/R29 (VLOOP disconnect) upstream of L1 — not timing-critical, keep within ~10mm
- R27 (VBOOST_EN pull-down) anywhere on the GPIO5 net
- **No copper pour under L1 on either layer** — switching node EMI
- Keep the SW→L1→VOUT hot trace under **10mm**, min **0.5mm wide**
- Surround this island with a GND via-stitch perimeter

### Group B — AP63203 buck
`U1 → L2 → C_BUCK`
- L2 within **5mm** of U1 SW pin
- C_BUCK (10µF 0805) on the output side of L2, within **3mm**
- C9/C10/C16 on U1 VIN side, within **2mm** (C16 = 10µF bulk)
- C11/C12 on +3V3 output rail, near L2 output
- R_FBH/R_FBL are DNP (fixed-output U1); keep the pads near U1 FB in case the adjustable variant is fitted

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
`J4 → D9 → R2 → C34 → R3 → D1 → C3/C4 → U9 AIN0`
- D9 within **3mm** of J4 SIG terminal
- C34 within **1mm** of R2 pads (across the shunt)
- TP5 (test point) at the R2/R3 shunt-top node
- Same grouping for CH2: `J5 → D10 → R4 → C35 → R5 → D1 CH2 → C5/C6 → U9 AIN1`

### Group F — ESP32-C6 module decoupling
`U6, C13, C30–C33, C15, R15, C36`
- All five 100nF caps (C13, C30–C33) within **2mm** of the module VCC3V3 pads
- C15 (10µF bulk) within **5mm** of module
- R15/C36 (EN reset RC) within **5mm** of the module EN pad, C36 ground via short
- Keep a **15mm no-copper keep-out** zone around the module's on-chip antenna area (the far end from the U.FL pad) on both layers

### Group G — IP2326 USB boost-charger cluster (rewritten 2026-07-13 for the TP5100→IP2326 swap)
`J13, U11, F2, U12, L3, C27, C28, C_SYS1, C_SYS2, C29, C_BST2, R35, R_VSET, R38, R50, R51, RT1`

**Hot loop (synchronous boost, input side):** `C28 (VIN cap) → L3 → U12 LX (15–17) → internal FETs → VSYS (19/20) → C_SYS1/C_SYS2 → PGND (18)`.
- C28 (10µF) within **2mm** of U12 VIN (13); C27 (4.7µF) just behind it on VUSB
- L3 (2.2µH, ≥3A Isat) within **3mm** of the LX pins; **no copper pour under L3 on either layer**
- C_SYS1/C_SYS2 (2×22µF) within **3mm** of VSYS (19/20), ground ends short and direct to PGND (18) — this closes the switching loop; keep the LX→L3→VSYS-caps loop area minimal
- C_BST2 (100nF) within **1mm** of BST (14), other end to the LX node
- C29 (10µF) within **3mm** of VOUT (21/22) — output (VBAT) side
- **EPAD (25) thermal**: solder the exposed pad to a GND pour; **8×8mm solid GND copper on F.Cu** under U12, ≥6 thermal vias (0.5–0.6mm drill) through to a matching B.Cu pour (boost at 1A charge dissipates ~1W)
- R35 (ISET) and R_VSET within **3mm** of pins 11/3; their GND ends to quiet analog ground, not into the power loop
- RT1 (pack NTC) — route the NTC pair away from LX; the thermistor body must be thermally coupled to the pack, so expect a wired stub or pack-adjacent placement
- R50/R51 within **3mm** of J13 CC1/CC2 pins; U11 and F2 between J13 VBUS and U12 VIN — total VUSB trace under **15mm**
- LX node copper: small — enough for ~2A but no larger (EMI); keep LX away from RT1, ISET, VSET sense nets

### Group L — CN3722 external buck stage (added 2026-07-13, senior-review open item)
`U7, M_SOLAR, D16, D_SOLAR, L_SOLAR, R19 (R_CS), C17, C21, C_VG, C_COM1, C_COM2, R_COM2, C_COM3, RT_SOLAR`

**Hot loop (buck):** `C17/C21 (VIN caps) → M_SOLAR S→D → D16 → SOLAR_FW node ← D_SOLAR (catch, GND→FW)`; L_SOLAR carries the FW node to CN_CS.
- C17 (10µF 35V) + C21 (100nF) within **3mm** of M_SOLAR source / U7 VCC (15); the C17-ground → D_SOLAR-anode-ground path must be short — this is the fast di/dt loop
- M_SOLAR, D16, D_SOLAR within **5mm** of each other; SOLAR_SW / SOLAR_FW copper small
- D_SOLAR anode ground and C17 ground tied at one point into the pour (loop closure)
- L_SOLAR after the FW node; no pour under it
- **Kelvin current sense (datasheet):** R19 (R_CS 0.4Ω 1206) in the L_SOLAR→VBAT path; route **CSP (13) and BAT (14) as a paired sense track directly to the two R19 pads** — no shared copper with the power path, ≥0.2mm gap from the switching nodes
- C_VG (100nF) within **2mm** of VG (1), returned to **VCC** (not GND)
- Gate drive DRV (16) → M_SOLAR gate: short, ≤10mm
- Compensation parts C_COM1 / C_COM2+R_COM2 / C_COM3 within **5mm** of pins 8/9/11, grounds to quiet analog ground
- RT_SOLAR (pack NTC): same routing rule as RT1 — away from switching nodes, body thermally coupled to the pack
- Keep the U7 thermal pour rules from Group D (10×10mm F.Cu+B.Cu, ≥4 vias)

### Group H — Battery input protection
`J1, D13, D5, R31`
- D13 (SMAJ10CA) within **5mm** of J1 BAT+ pin
- D5 and R31 between D13 and VBAT rail — R31 within **2mm** of D5 gate

### Group K — Battery divider (gated)
`Q5, R16, Q2, R26, R7, R8, C8`
- Whole group near U9's analog island; the ADC_CH2 trace (R7/R8 mid → U9 AIN2) short and away from L1/L2
- C8 (1nF) directly across R8

### Group I — DS18B20 interface
`J6, D12, R6, R28, R32`
- D12 within **3mm** of J6 DATA terminal (pin 2)
- R6 (pull-up) can be anywhere between +3V3 and the 1WIRE net
- R28 in the VCC line between +3V3 and J6 pin 1

### Group J — Solar input protection
`J12, D14, D6, D8, C17, C21`
- D14 (SMAJ24CA) within **3mm** of J12 SOLAR+ pin (first TVS at the terminal)
- D6 between D14 and U7 VIN (Schottky backfeed block)
- D8 (SMAJ24CA) within **5mm** of C17 (second-stage TVS at CN3722 VIN)
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
| U12 IP2326 | 8×8mm | F.Cu + B.Cu, GND net (EPAD soldered) | ≥6 vias, 0.5–0.6mm drill (≈1W at 1A boost charge) |

---

## Test Point Placement Notes

- TP1/TP3/TP4: near U1 buck (TP1=VBAT at U1 VIN side, TP3=+3V3 at output, TP4=GND)
- TP2: near C20/C22 on VLOOP rail
- TP5/TP6: within 3mm of R2/R4 (on the R3/R5 side of the shunt)
- TP7: near J6 DATA, on the GPIO7 side of D12
- TP8/TP9: near J8 I²C header
- TP10: near J12 solar input terminal
- TP11: near J1 BAT+ terminal (before D5)
- TP12: near U6 GPIO12 area
- TP13 (FACTORY_RESET): board edge or otherwise reachable with the lid off — field-recovery pad, pair visually with TP4 (GND)
- TP14: near U7 /CHRG pin
- TP15: near U12 /CHRG pin
