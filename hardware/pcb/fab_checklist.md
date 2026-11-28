# Path to fabrication — ordered checklist

Updated 2026-11-28. The schematic is complete and machine-checked (`netlist_check.py`: 447 pins / 81 nets / 0 mismatches; `footprint_check.py`: 163 symbols, every pin has its pad). Everything below is what still stands between this repo and boards on the bench. The background for each step is in [`README.md`](README.md).

## 0. Decisions before layout

- [ ] RF path: bulkhead pigtail and no J3 on the board (recommended), U.FL + 50 Ω trace to J3, or the PCB-antenna MINI-1 (README decision 1)
- [ ] BT1 holder: Keystone 1042 as drawn (off-LCSC), or draw a footprint for an LCSC holder (README decision 2)
- [ ] Sourcing for Q6 FS8205A, J4–J7 Phoenix headers and L_SOLAR (README decision 3) — substitute now if a substitute changes the land
- [ ] Keep or delete the DNF GDT1/GDT2 footprints (README decision 4)

## 1. First KiCad 10 session

- [ ] Open `welld.kicad_pro`, let KiCad re-save the sheets, run ERC; only the waivable categories listed in the README should remain
- [ ] Re-run `netlist_check.py` and `footprint_check.py` after the re-save — both must still pass
- [ ] Apply the RF decision in the schematic (delete J3, or add the U.FL receptacle and trace net) and re-run both checks

Done in the 2026-11-28 pass (no action needed): official Espressif symbol and footprint for U6; USB-C B-row pins wired; AO3400A pin numbers; U1 SOT-89; footprints that did not exist in KiCad 10 replaced; SJ2–SJ5 bridged variants; LCSC fields corrected; DNF flags on C4, C6, C_BST, R22, GDT1, GDT2, J8, J9; test pads and solder jumpers out of the BOM.

## 2. Layout

- [ ] Follow the procedure in `README.md` and the rules in `placement_constraints.md`
- [ ] Mounting holes agreed with the enclosure design; TP13 (factory reset) reachable with the lid off
- [ ] Q8/Q10 collector tabs on ≥ 1 cm² of copper; TP4056 EP pour with ≥ 6 thermal vias; no pour under L1 or L_SOLAR
- [ ] DRC clean

## 3. Order

- [ ] Export the BOM and placement (CPL) files with DNP parts excluded, then check that **C4, C6, C_BST, R22, GDT1, GDT2, J8, J9** are absent and no TP or SJ appears. A fitted C4/C6 slows the AIN0/AIN1 inputs to τ ≈ 11 ms and reads the level 10–40 % low at the default 10 ms warm-up — invisible to the firmware's range checks
- [ ] LCSC numbers were verified against LCSC's catalogue on 2026-11-28; re-check stock at order time, especially the parts in the BOM's *Sourcing risks* table
- [ ] Q8/Q10: if any vendor other than Nexperia or onsemi is substituted, check its BCP53 datasheet for B=1, C=2, E=3 (never an SOT-89 BCX53)
- [ ] Off-board items: STF field plugs, the 18650 cell, the antenna and the RF pigtail (BOM → *Not on the board*)

## 4. First-article bench checks (before sealing the enclosure)

| # | Check | Why |
|---|-------|-----|
| 1 | MT3608B pin continuity (SW ↔ L1 node, IN ↔ VBAT) before first power-on | pinout from the datasheet; never checked on a board |
| 2 | +3V3 regulates; worst-case rail current < 250 mA during 802.15.4 TX + sensor reads | U1 is a 250 mA LDO |
| 3 | With a 3.2 V cell (bench supply on the BT1 pads): +3V3 ≥ 3.0 V during TX, VLOOP ≥ 15.1 V with a 20 mA load, no brownout reset | confirms the margin of `CONFIG_WELLD_BATT_EMPTY_MV` = 3200 |
| 4 | TP4056 charges at ≈1 A without thermal fold-back inside the enclosure (or accept it / R_PROG = 2.4 kΩ) | ≈1.3 W linear dissipation at mid-charge; the pour size is an estimate |
| 5 | Sleep current ≈ 25–30 µA at 4.2 V: ESP32-C6 deep sleep ≈7 µA + HT7333 ≈4 µA + CN3791 BAT/CSP ≈9 µA + DW01A ≈3 µA + TP4056 BAT leak < 2 µA + ADS1115/DS18B20 ≈1.5 µA + FS8205A/TVS leakage. Flag anything above ≈35 µA | battery budget |
| 6 | CN3791 and TP4056 CV agree (both 4.2 V) under co-charge | no oscillation or one charger hogging at the overlap |
| 7 | NTC cut-offs: TP4056 stops outside RT1's computed +8…+44 °C window; the LM393 cutoff clamps solar charging below ≈+2 °C (release ≈+4 °C) with zero charge current while clamped | outdoor Li-ion; thresholds are computed |
| 8 | MT3608B EN-low shutdown < 1 µA; VLOOP 15.1–16.7 V (15.88 V nominal) from VBAT 3.2–4.2 V | sleep budget; boost ratio up to ≈5× at a low cell |
| 9 | CN3791 charge current ≈1.2 A at R19 = 0.1 Ω; L_SOLAR stays out of saturation | sense formula and Isat margin from the datasheet |
| 10 | Loop reading vs a calibrator (4 / 12 / 20 mA) within the shunt's 0.1 %; SMAJ5.0A leakage invisible on the shunt | D9/D10 choice |
| 11 | ADS1115 AIN2 reads correctly up to a 4.2 V cell (÷2 divider, ±4.096 V range) | clipping at full charge was a past failure |
| 12 | Protection trip and recovery: cell isolated below ≈2.4 V and recovers on a charger; over-current trip; a reversed cell is blocked by D5 | DW01A/FS8205A path |
| 13 | USB console and flashing work with the USB-C plug in **both** orientations | B-row data pins wired 2026-11-28 |

**Loop current limiters + 16 V loop (design change #21):**

- VLOOP at TP2 with GPIO5 forced HIGH: 15.1–16.7 V. With a 20 mA calibrator in the loop, VLOOP ≥ 15.1 V and the reading settled within ±20 µA at the 10 ms sample (a 12 V-minimum transducer at 20 mA needs VLOOP ≥ ≈14.5 V)
- J4 LOOP+ shorted to SIG through an ammeter: ≈27–35 mA (≈32 mA at room temperature); the firmware logs `transducer short-circuit`; the device keeps running (no DW01A trip)
- J4 LOOP+ shorted to GND: same current, no DW01A trip; the firmware logs `transducer open loop` (the shunt sees nothing)
- 20 mA calibrator: LOOP+ ≥ VLOOP − 0.55 V (limiter drop ≈0.5 V); repeat on J5 with SJ2 bridged
- With SJ2 open: J5 LOOP+ ≈0 V while VLOOP is on (channel 2 isolated) — leave J5 LOOP+ unconnected in that state
- D9, D10, D11, D13, D18, D20 are unidirectional parts drawn with the generic TVS symbol: polarity comes only from the D_SMA pad 1 = cathode (band) convention, so check every SMAJ orientation at assembly (a reversed D18/D20 is a limited LOOP+→GND short that reads as an open loop)

## 5. Enclosure (after layout freezes the outline)

`hardware/case/` does not exist yet. The case consumes the final outline, connector and mounting-hole positions, the RF decision (bulkhead pigtail position), TP13 access, and ≈19–21 mm of clearance over the top-side 18650 carrier.
