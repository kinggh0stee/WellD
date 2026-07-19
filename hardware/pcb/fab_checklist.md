# Path to fabrication — ordered checklist (updated 2026-07-19 for the 1S conversion + battery carrier)

Consolidates the remaining work from `senior_review_2026-07-06.md`, `component_verification_2026-07-14.md`, and the blocker list in `schematic_connections.md`. The schematic is fully wired (stub+label) and machine-verified (**357 pins / 69 nets / 0 mismatches** after the 1S conversion + battery carrier, `netlist_check_output.txt`), but the 1S conversion introduced three new parts whose datasheets were not fetchable at conversion time — **blockers #10 (a–e) and #11 (a–c) in `schematic_connections.md` are now the top of this list**. Everything below is what still stands between this repo and ordering boards.

## 0. 1S-conversion datasheet checks (NEW 2026-07-19 — before anything else)

- **CN3791** (#10b): pin numbering, VG cap arrangement, I_CH sense formula (0.1 Ω assumed → 1.2 A), VIN range, TEMP thresholds; L_SOLAR saturation margin at 1.2 A (Isat ≈1.3 A — tight, may need a 2 A-class part).
- **TP4056** (#10a): SOP-8+EPAD pinout confirm, I_CH = 1200/R_PROG formula, TEMP window math (R_NTC 5.6 k / RT1 10 k → target ≈ +5…+44 °C), LCSC part pick (EPAD variant).
- **HT7333-A** (#10d): SOT-23 pinout confirm (GND=1/VOUT=2/VIN=3), 250 mA ceiling vs worst-case 3.3 V rail draw.
- **Firmware handoff** (#10c): ✅ done (AIN2 on ±4.096 V PGA; Kconfig 200 / 4200 / 3000 shipped in v1.1.0).
- **DW01A + FS8205A** (#11a/b): pinouts and the 100 Ω / 100 nF / 1 kΩ values are the community TP4056-module topology — confirm both datasheets; check the FET pair's ≈60 mΩ in the discharge path against the DW01A over-current trip point.
- **BT1 carrier** (#11c): pick the THT holder MPN and draw `WellD:BH-18650_THT`. Placement is resolved: board size is unconstrained (user, 2026-07-19) — carrier top-side along a long edge, outline grows (working target ≈100 × 60 mm, set at layout).

## 1. First interactive KiCad 10 session (~1 hour, needs a desktop)

1. Open `welld.kicad_pro`, let KiCad migrate/resave all sheets (normalises the generated formatting).
2. Run **ERC**. Expected waivable items (from the wiring-pass notes — anything *else* is a real finding):
   - off-1.27-grid stub endpoints on the handful of off-grid symbol placements;
   - "input pin not driven" on passive-driven analog inputs (ADS1115 AINx, FB pins);
   - style-grade label/wire overlaps from generated placement.
3. Re-run `python3 hardware/pcb/netlist_check.py` after the resave — it must still report zero mismatches (guards against the migration moving anything).
4. Replace the custom `welld:ESP32_C6_MINI_1U` symbol with the official Espressif library part (pin numbering of the custom one was never verified) and re-run ERC + `netlist_check.py`.
5. Swap SJ2–SJ5 to the *Bridged* solder-jumper variants (currently Open).

## 2. Cell choice (no vendor question any more)

- The pack (and its unanswerable PCM question, old blocker #7a) is gone — protection is the on-board DW01A/FS8205A. What remains is a **cell choice**: worst-case co-charge is TP4056 1 A + CN3791 ≈1.2 A ≈ 2.2 A into a single ≈3.4 Ah cell (**≈0.65C**). Use a quality high-rate 18650, or drop R_PROG to 2.4 kΩ (0.5 A USB) if the cell runs warm under co-charge.

## 3. Layout (in KiCad, using the written constraints)

- `placement_constraints.md` is current (rewritten 2026-07-19): Group G = TP4056 **thermal** cluster (no switching loop — EPAD pour is the constraint, ≈1.3 W at 1 A), Group L = CN3791 integrated buck (C17→VIN→SW→D_SOLAR hot loop; **CSP/BAT Kelvin pair routed together to R19**), Group B = HT7333-A LDO (trivially quiet now).
- `kicad_place_script.py` (PCB-editor scripting console) gives starting placements.
- Board outline: **unconstrained** (user, 2026-07-19) — draw it around the finished placement; working target ≈100 × 60 mm with the BT1 carrier top-side along a long edge (Group H). All 1S replacement parts are iron-friendly except the two EPADs (TP4056 SOP-8-EP, and the ESP32 module) — hot air preferred; the carrier is THT.

## 4. Order (all LCSC numbers verified 2026-07-14)

- BOM: `bom_footprints.md` — updated 2026-07-19 for the 1S conversion. Verified numbers carried over: PRTR5V0U2X **C12333**, SMAJ5.0A **C98802** (now also D13), PTC C210838, AO3400A C20917, HRO USB-C C165948.
- **Order-time checks (grew with the 1S conversion + carrier)**: TP4056 EPAD variant (LCSC TBD), CN3791 (C124423 verify), HT7333-A (C21583 verify), SMAJ10CA for D8/D14 (C2836474 unconfirmed), D11 (C8057 / alternate C110519), DW01A-G (TBD), FS8205A (TBD), BT1 18650 THT holder (TBD).

## 5. First-article bench-verify list (before enclosure sealing)

| # | Check | Why |
|---|-------|-----|
| 1 | MT3608B pin continuity (SW↔L1 node, IN↔VBAT) before first power-on | pin map confirmed from library sources, never from the raw Aerosemi PDF |
| 2 | +3V3 rail regulates 3.3 V; worst-case rail current < 250 mA during 802.15.4 TX + sensor reads | U1 is now a 250 mA HT7333-A LDO (1S blocker #10d) |
| 3 | TP4056 1 A charge without thermal fold-back in the enclosure (or accept fold-back / drop R_PROG to 2.4 k) | ≈1.3 W linear dissipation at mid-charge; pour sizing is a guess until measured |
| 4 | Sleep floor < 15 µA total: HT7333 Iq + TP4056 BAT leak + CN3791 BAT dark current + TVS at 4.2 V | nightly battery budget (1S blocker #10e) |
| 5 | Charger CV agreement: CN3791 vs TP4056, both nominally 4.2 V, under co-charge | verify no oscillation / one-charger-hogging at the overlap |
| 6 | NTC cutoffs: both chargers stop outside their windows (RT1 ≈ +5…+44 °C, RT_SOLAR per CN3791 DS) | outdoor Li-ion; thresholds computed, not measured |
| 7 | MT3608B EN-low shutdown current < 1 µA; boost still makes 12 V from VBAT = 3.0 V (ratio 4×, higher input current) | sleep-budget + low-battery loop-read assumptions |
| 8 | CN3791 charge current ≈ 1.2 A at R_CS 0.1 Ω (sense-formula assumption); L_SOLAR stays out of saturation | 1S blocker #10b — formula and Isat margin both assumed |
| 9 | Loop reading sanity vs known pressure; SMAJ5.0A leakage invisible on the shunt | D9/D10 substitution validation |
| 10 | ADS1115 AIN2 reads correctly up to 4.2 V cell (±4.096 V PGA, ratio 200) | shipped in fw 1.1.0 — clipping at full charge was the failure mode |
| 11 | Protection trip + recovery: cell isolated below ≈2.4 V, recovers on charger; over-current trip; reversed-cell insertion blocked (D5) | new DW01A/FS8205A path + carrier (#11a–c); values assumed from the module ecosystem |

## 6. Enclosure (after layout freezes connector positions)

- `hardware/case/` does not exist yet. Case work is deliberately last — the board outline is now free (set at layout, working target ≈100 × 60 mm), and the case consumes the final outline plus connector/TP positions (TP13 factory-reset pad must stay reachable with the lid off; ~19–21 mm clearance over the top-side 18650 carrier).
