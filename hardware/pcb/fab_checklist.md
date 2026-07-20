# Path to fabrication — ordered checklist (updated 2026-07-19 for the 1S conversion + battery carrier)

Consolidates the remaining work from `senior_review_2026-07-06.md`, `component_verification_2026-07-14.md`, and the blocker list in `schematic_connections.md`. The schematic is fully wired (stub+label) and machine-verified (**391 pins / 75 nets / 0 mismatches** after the 1S conversion + battery carrier + CN3791 correction + solar cold-charge cutoff, `netlist_check_output.txt`), but the 1S conversion introduced three new parts whose datasheets were not fetchable at conversion time — **blockers #10 (a–e) and #11 (a–c) in `schematic_connections.md` are now the top of this list**. Everything below is what still stands between this repo and ordering boards.

## 0. Datasheet checks — ✅ DONE 2026-07-19 (web-verification pass; see blockers #10–#11 for details)

- **CN3791** (#10b): ✅ verified **with major corrections applied** — it is a *controller* (external P-FET restored: M_SOLAR/D16/R_DRV; COM network added; **no TEMP pin → RT_SOLAR deleted, see #10f**); pin map + 120 mV/R_CS formula + VG cap confirmed; symbol redrawn, netlist re-verified.
- **TP4056** (#10a): ✅ pinout + TEMP window (45–80 % VIN) confirmed; R_PROG 1.2 k → 0.9–1.0 A depending on DS revision; LCSC **C16581** (ESOP-8).
- **HT7333-A** (#10d): ✅ pinout confirmed (GND=1/VOUT=2/VIN=3); LCSC **C21583**.
- **DW01A** (#11a): ✅ pinout + thresholds + app values confirmed (LCSC candidate C351410).
- **FS8205A** (#11b): ✅ verified **with correction** — real map D=1&8/S1=2&3/G1=4/G2=5/S2=6&7; symbol redrawn (LCSC candidates C14212/C908265).
- **BT1 carrier** (#11c): MPNs picked — **recommended MY-18650-02 THT clip pair (C2979182 ×2)**, alt BH-18650-B1BA002 one-piece (C2988620); draw the footprint from the LCSC drawing at order time (drawing PDFs proxy-blocked here). Placement already resolved: top-side along a long edge, board ≈100 × 60 mm.
- **#10f — ✅ RESOLVED (user decision)**: discrete **LM393 cold-charge cutoff added** — solar-powered (zero night draw), ratiometric NTC threshold, clamps the CN3791 MPPT pin below ≈+2 °C (release ≈+4 °C). Bench-verify trip/release and zero charge current while clamped.
- ✅ **Bench-math done 2026-07-19**: TP4056 TEMP window computed **+8…+44 °C** (R_NTC 5.6 k / RT1 10 k B3950 — conservative-safe, kept). L_SOLAR resized to **SRN6045TA-220M** (22 µH, Isat 3.3 A) — peak ≈1.24 A gives 1.7× margin, same footprint.

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
| 6 | NTC cutoffs: TP4056 stops outside RT1's **computed +8…+44 °C** window; **LM393 cutoff clamps solar charge below ≈+2 °C (release ≈+4 °C), zero charge current while clamped** | outdoor Li-ion; thresholds computed — confirm on bench |
| 7 | MT3608B EN-low shutdown current < 1 µA; boost still makes 12 V from VBAT = 3.0 V (ratio 4×, higher input current) | sleep-budget + low-battery loop-read assumptions |
| 8 | CN3791 charge current ≈ 1.2 A at R_CS 0.1 Ω (sense-formula assumption); L_SOLAR stays out of saturation | 1S blocker #10b — formula and Isat margin both assumed |
| 9 | Loop reading sanity vs known pressure; SMAJ5.0A leakage invisible on the shunt | D9/D10 substitution validation |
| 10 | ADS1115 AIN2 reads correctly up to 4.2 V cell (±4.096 V PGA, ratio 200) | shipped in fw 1.1.0 — clipping at full charge was the failure mode |
| 11 | Protection trip + recovery: cell isolated below ≈2.4 V, recovers on charger; over-current trip; reversed-cell insertion blocked (D5) | new DW01A/FS8205A path + carrier (#11a–c); values assumed from the module ecosystem |

## 6. Enclosure (after layout freezes connector positions)

- `hardware/case/` does not exist yet. Case work is deliberately last — the board outline is now free (set at layout, working target ≈100 × 60 mm), and the case consumes the final outline plus connector/TP positions (TP13 factory-reset pad must stay reachable with the lid off; ~19–21 mm clearance over the top-side 18650 carrier).
