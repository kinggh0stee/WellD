# WellD PCB — Placement Constraints

These are **rules and groupings only** — no positions dictated. Place components wherever you want in KiCad, but respect these constraints. `kicad_place_script.py` gives a rough starting spread; the board outline is free (working target ≈100 × 60 mm).

---

## Board Edge Requirements

These components must land on a specific board edge:

| Component | Edge | Why |
|-----------|------|-----|
| J13 (USB-C) | Any short edge | Connector body extends off-board; case cutout is on this wall |
| J3 (SMA edge-mount) — *if kept* | Any short or long edge | Only if the RF decision keeps an SMA on the board (README decision 1); its port protrudes ~3 mm past Edge.Cuts |
| J4, J5, J6, J7, J12 (Phoenix MC 1,5 pluggable headers) | One long edge | Field wiring exits through cable glands on this face of the enclosure; the plugs pull out horizontally, so leave finger room in front |
| BT1 (18650 carrier) | Body parallel to a long edge | ≈78×21 mm SMD holder (`Battery:BatteryHolder_Keystone_1042_1x18650`, pads 79.4 mm apart) — dominates the board; see Group H. No case battery bay needed (cell lives on the PCB) |
| J10 (programming header) | Any edge or interior — but keep accessible | Pogo-pin fixture needs vertical clearance; keep clear of large caps |

> **J3 (if kept) and J13 must be on different edges** — they cannot share the same short edge (connector bodies will clash).

---

## Must-Be-Near Groups (hard rules from datasheets)

### Group A — MT3608B boost hot loop
`Q3 → L1 → U8 SW → D15 → C20/C22` — the SW→D15→C20/C22 loop must be tight.
- L1 within **3mm** of U8 SW pin
- D15 (SS34 rectifier) within **3mm** of U8 SW pin; C20/C22 within **3mm** of D15 cathode
- C_BST is **DNF** (U8 pin 6 is NC per the MT3608B datasheet) — keep its footprint next to pin 6 or delete it at layout; it carries no current
- C19 within **2mm** of U8 IN pin
- Q3/Q4/R29 (VLOOP disconnect) upstream of L1 — not timing-critical, keep within ~10mm
- R27 (VBOOST_EN pull-down) anywhere on the GPIO5 net
- **No copper pour under L1 on either layer** — switching node EMI
- Keep the SW→L1→VOUT hot trace under **10mm**, min **0.5mm wide**
- Surround this island with a GND via-stitch perimeter

### Group B — HT7333-A LDO (SOT-89-3)
`U1, C9/C10/C16 (VIN), C_BUCK/C11/C12 (VOUT)`
- Pinout **GND=1, VIN=2 (= the tab), VOUT=3** — the tab sits on VBAT copper, which also spreads its (small) heat
- C9/C10/C16 on the VIN side, within **2mm** (C16 = 10µF bulk)
- C_BUCK (10µF 0805) + C11/C12 on VOUT (3), within **3mm** — LDO stability wants the output cap close
- No switching node, no inductor, no pour restrictions — this group is now trivially quiet; placement is only about lead length

### Group C — ADS1115 analog island
`U9, FB1, C23, C24, R9, R10, R_DRDY`
- FB1 in series with +3V3 feed to U9 VDD
- C23 (100nF) and C24 (1µF) on the **U9 side** of FB1, within **1mm** of U9 VDD pin
- Keep U9 **≥20mm from U8** (MT3608B switching noise)
- Keep U9 away from L1 and L_SOLAR (inductor EMI)
- R_DRDY (4.7kΩ pull-up for ADS_DRDY) can be anywhere near U9 or near the GPIO22 trace

### Group D — CN3791 solar charger thermal (corrected 2026-07-19 — controller, external FET carries the heat)
`U7, C17, C18, R19, R20, R21`
- A modest GND pour under U7 suffices (the controller itself dissipates little); the real heat is in M_SOLAR / D16 / D_SOLAR (Group L) — spread copper there
- Mirror the pour on B.Cu and stitch with the same vias
- U7 must be **≥15mm from U6** (ESP32 module)
- U7 and U8 must be **≥8mm apart**

### Group E — 4-20mA shunt and protection chain (CH1)
`J4 → D9 → R2 → C34 → R3 → D1 → C3 (C4 DNP) → U9 AIN0`
- D9 within **3mm** of J4 SIG terminal
- C34 within **1mm** of R2 pads (across the shunt)
- TP5 (test point) at the R2/R3 shunt-top node
- Same grouping for CH2: `J5 → D10 → R4 → C35 → R5 → D1 CH2 → C5 (C6 DNP) → U9 AIN1`

### Group E2 — Loop current limiters (design change #21, one per channel)
`VLOOP → R52 → Q8 → J4 LOOP+` (CH2: `VLOOP_CH2 → R54 → Q10 → J5 LOOP+`), clamp Q9/Q11 and base resistor R53/R55 beside them.
- **D18/D20 (SMAJ18A) within 3 mm of the J4/J5 LOOP+ pin**, short fat return to GND — they are now the only clamp directly on the terminal
- **D17/D19 (SS34 steering) with short, ≥ 0.5 mm traces** — surge current flows LOOP+ → D17 → VLOOP → D11 (CH1) and LOOP+ → D19 → VLOOP_CH2 → **SJ2** → VLOOP → D11 (CH2, ≈45 A at 2 kV): place SJ2 next to D19 and D11, keep the whole path short and ≥ 0.5 mm, and D11 close to where they meet VLOOP
- Q9/Q11 next to R52/R54 (it senses their drop; no other current in that trace)
- **Q8/Q10 (BCP53, SOT-223) collector tab on ≥ 1 cm² of LOOP_PWR copper** — up to ≈0.55 W into a dead short while VLOOP is on (see the thermal table)

### Group F — ESP32-C6 module decoupling
`U6, C13, C30–C33, C15, R15, C36`
- All five 100nF caps (C13, C30–C33) within **2mm** of the module VCC3V3 pads
- C15 (10µF bulk) within **5mm** of module
- R15/C36 (EN reset RC) within **5mm** of the module EN pad, C36 ground via short
- The **-1U has no on-board antenna** (U.FL port instead), so no antenna keep-out is needed; keep the U.FL end of the module clear enough to plug the pigtail in by hand

### Group G — TP4056 USB linear-charger cluster (rewritten 2026-07-19 for the 1S conversion — no switching loop anymore)
`J13, U11, F2, U12, C27, C28, C29, R_PROG, R_NTC, R38, R50, R51, RT1`

**No hot loop** — the TP4056 is linear. The dominant constraint is **thermal**, not di/dt:
- **EPAD thermal**: solder the exposed pad (land 2.41 × 3.3 mm) to a GND pour; **10×10mm solid GND copper on F.Cu** around U12, ≥6 thermal vias (0.3 mm drill in or right beside the EP) through to a matching B.Cu pour — **1 A charge from 5 V dissipates ≈1.3 W at mid-charge** (worse than the old boost's ~1 W; the TP4056 thermally regulates at ≈120 °C die, so an undersized pour silently slows charging rather than failing)
- U12 must be **≥10mm from U6** (ESP32) and away from RT1's pack-coupling path — a hot charger next to the pack NTC would false-trip the charge-temperature window
- C28 (10µF) within **2mm** of U12 VCC (4); C27 (4.7µF) just behind it on VUSB
- C29 (10µF) within **3mm** of BAT (5) — output (VBAT) side
- R_PROG within **3mm** of PROG (2), GND end to quiet ground (it is the current-set sense — keep it off the EPAD pour's high-ripple return)
- R_NTC + RT1: divider junction at TEMP (1); route the NTC pair away from the hot U12 area; thermistor body thermally coupled to the **pack**, so expect a wired stub or pack-adjacent placement
- R50/R51 within **3mm** of J13 CC1/CC2 pins; U11 and F2 between J13 VBUS and U12 VCC — total VUSB trace under **15mm**
- **USB data**: both pad rows are wired (A6+B6 = D+, A7+B7 = D−) — join each pair at the connector, then run D+/D− side by side through U11 to U6 pins 17/18 (full-speed USB: keep the pair short and together; no impedance control needed at this length)

### Group L — CN3791 external buck stage (re-corrected 2026-07-19 — the CN3791 is a controller; FET stage restored)
`U7, M_SOLAR, D16, D_SOLAR, L_SOLAR, R19 (R_CS), R_DRV, C17, C21, C_VG, C_COM, R_COM`

**Hot loop (buck, external P-FET):** `C17/C21 (VIN caps) → M_SOLAR S→D → SOLAR_SW → D16 → SOLAR_FW ← D_SOLAR (catch, GND→FW)`; L_SOLAR carries SOLAR_FW to CN_CS.
- C17 (10µF 35V) + C21 (100nF) within **3mm** of M_SOLAR source / U7 VCC (9); the C17-ground → D_SOLAR-anode-ground path must be short — this is the fast di/dt loop
- M_SOLAR, D16, D_SOLAR within **5mm** of each other; SOLAR_SW / SOLAR_FW copper small
- D_SOLAR anode ground and C17 ground tied at one point into the pour (loop closure)
- L_SOLAR after the FW node; no pour under it
- **Kelvin current sense:** R19 (R_CS 0.1Ω 1206) in the L_SOLAR→VBAT path; route **CSP (8) and BAT (7) as a paired sense track directly to the two R19 pads** — no shared copper with the power path, ≥0.2mm gap from the switching nodes
- C_VG (100nF) within **2mm** of VG (1), returned to **VCC** (✅ datasheet-verified)
- Gate drive DRV (10) → M_SOLAR gate: short, ≤10mm; R_DRV (300k) gate–source at the FET
- C_COM (220nF) + R_COM (120Ω) within **5mm** of COM (5), ground end to quiet analog ground
- RT_SOLAR (revived for the LM393 cutoff): thermistor body thermally coupled to the **cell/carrier**, wired stub or cell-adjacent placement — same rule as RT1; keep the NTC pair away from switching nodes
- The heat now lives in M_SOLAR/D16/D_SOLAR, not U7 — the Group D pour under U7 shrinks in importance; give M_SOLAR a modest copper spread instead

### Group N — Solar cold-charge cutoff (NEW 2026-07-19)
`U14 (LM393), RT_SOLAR, R_NT1, R_NT2, R_NT3, R_PU, R_HYS, C_NTC, Q7`
- Small-signal analog: place near U7's MPPT corner (Q7 drain lands on the MPPT_REF node — keep that trace short)
- C_NTC within **2mm** of U14 VCC (8)
- Divider nodes NTC_T / NTC_REF away from SOLAR_SW/SOLAR_FW switching copper (≥2 mm)
- RT_SOLAR body couples to the cell, not to this cluster — expect a routed pair out to the carrier area

### Group H — Battery carrier + input protection (rewritten 2026-07-19)
`BT1, U13, Q6, R_DW1, C_DW, R_CS_DW, D13, D5, R31`
- **BT1 placement (resolved 2026-07-19 — board size is unconstrained per user)**: put the carrier on the **top side, its own band along one long edge**, and grow the outline to fit — working target ≈**100 × 60 mm** (final dims set at layout; the case consumes them afterwards). Single-sided assembly, no back-side reflow. Keep the carrier band away from the antenna edge and off the MT3608B/CN3791 switching islands.
- Protection cluster (U13/Q6/R_DW1/C_DW/R_CS_DW) tight at BT1's **negative** terminal: the BATT_N → Q6 S1 → drains → S2 → GND path carries every load and charge ampere — short, wide copper (≥1 mm), no via detours if possible
- R_CS_DW's GND end on the **system** side (P−), R_DW1/C_DW referenced to BATT_N — do not mix the two grounds around U13; the DW01A senses the FET-pair drop between them
- D13 (SMAJ5.0A) within **5mm** of BT1 cell+ tab
- D5 and R31 between D13 and VBAT rail — R31 within **2mm** of D5 gate
- RT1 (USB-path TEMP window) and RT_SOLAR (solar-path LM393 cutoff) both thermally coupled to the carrier/cell body

### Group K — Battery divider (gated)
`Q5, R16, Q2, R26, R7, R8, C8`
- Whole group near U9's analog island; the ADC_CH2 trace (R7/R8 mid → U9 AIN2) short and away from L1/L_SOLAR
- C8 (1nF) directly across R8

### Group I — DS18B20 interface
`J6, D12, R6, R28, R32`
- D12 within **3mm** of J6 DATA terminal (pin 2)
- R6 (pull-up) can be anywhere between +3V3 and the 1WIRE net
- R28 in the VCC line between +3V3 and J6 pin 1

### Group J — Solar input protection
`J12, D14, D6, D8, C17, C21`
- D14 (SMAJ10CA) within **3mm** of J12 SOLAR+ pin (first TVS at the terminal)
- D6 between D14 and U7 VIN (Schottky backfeed block)
- D8 (SMAJ10CA) within **5mm** of C17 (second-stage TVS at CN3791 VIN)
- C21 within **3mm** of D8

---

## Must-Be-Apart Rules

| Components | Minimum gap | Reason |
|-----------|-------------|--------|
| U7 (CN3791) and U6 (ESP32) | 15mm | Switching-stage noise (M_SOLAR/D16) and RF isolation |
| U8 (MT3608B) and U9 (ADS1115) | 20mm | 1.2MHz switching noise corrupts ADC readings |
| U8 (MT3608B) and U7 (CN3791) | 8mm | Thermal — both dissipate power simultaneously |
| L1/L_SOLAR (inductors) and U9 (ADS1115) | 15mm | Inductor EMI fields |
| J3 (SMA, if kept) and U6 (module) | — | Route the W1 pigtail away from other signals |

---

## RF Layout Rules (U6, W1, J3)

The module is the **-1U** (U.FL port, no on-board antenna), so the board carries no RF trace. How the antenna reaches the enclosure wall is an **open decision** (README decision 1): the drawn pigtail (U.FL → SMA plug) cannot also leave J3 free for the antenna. Whichever option is chosen:

- leave hand access to the module's U.FL port;
- if an SMA stays on the board (J3), put it on an edge and route the coax away from the boost (U8/L1) and the solar buck (M_SOLAR/L_SOLAR);
- keep high-current traces (VLOOP, VBAT) away from the U.FL area.

---

## Thermal Copper Pours Required

| Component | Pour size | Layer | Via stitching |
|-----------|-----------|-------|---------------|
| M_SOLAR / D16 / D_SOLAR (solar buck) | copper spread at each part | F.Cu, GND/net pours as routing allows | the CN3791 controller itself needs no special pour |
| Q8, Q10 BCP53 (loop limiters, #21 — ≈0.55 W only during a dead short while VLOOP is on, 10–15 ms per wakeup by default) | ≥ 1 cm² on the collector tab (LOOP_PWR_CH1/2 net) | F.Cu (B.Cu mirror optional) | 2–4 vias if mirrored |
| U12 TP4056 | 10×10mm | F.Cu + B.Cu, GND net (EPAD soldered) | ≥6 vias, 0.3 mm drill in/around the EP (≈1.3W at 1A linear charge — thermal regulation folds back if undersized) |

---

## Test Point Placement Notes

- TP1/TP3/TP4: near U1 (TP1=VBAT at U1 VIN side, TP3=+3V3 at output, TP4=GND)
- TP2: near C20/C22 on VLOOP rail
- TP5/TP6: within 3mm of R2/R4 (on the R3/R5 side of the shunt)
- TP7: near J6 DATA, on the GPIO7 side of D12
- TP8/TP9: near J8 I²C header
- TP10: near J12 solar input terminal
- TP11: near the BT1 cell+ pad (VBAT_RAW, before D5)
- TP12: near U6 GPIO22 area
- TP13 (FACTORY_RESET): board edge or otherwise reachable with the lid off — field-recovery pad, pair visually with TP4 (GND)
- TP14: near U7 /CHRG pin
- TP15: near U12 /CHRG pin
