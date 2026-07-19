# Path to fabrication — ordered checklist (updated 2026-07-19 for the 1S conversion)

Consolidates the remaining work from `senior_review_2026-07-06.md`, `component_verification_2026-07-14.md`, and the blocker list in `schematic_connections.md`. The schematic is fully wired (stub+label) and machine-verified (**337 pins / 63 nets / 0 mismatches** after the 1S conversion, `netlist_check_output.txt`), but the 1S conversion introduced three new parts whose datasheets were not fetchable at conversion time — **1S blocker #10 (a–e) in `schematic_connections.md` is now the top of this list**. Everything below is what still stands between this repo and ordering boards.

## 0. 1S-conversion datasheet checks (NEW 2026-07-19 — before anything else)

- **CN3791** (#10b): pin numbering, VG cap arrangement, I_CH sense formula (0.1 Ω assumed → 1.2 A), VIN range, TEMP thresholds; L_SOLAR saturation margin at 1.2 A (Isat ≈1.3 A — tight, may need a 2 A-class part).
- **TP4056** (#10a): SOP-8+EPAD pinout confirm, I_CH = 1200/R_PROG formula, TEMP window math (R_NTC 5.6 k / RT1 10 k → target ≈ +5…+44 °C), LCSC part pick (EPAD variant).
- **HT7333-A** (#10d): SOT-23 pinout confirm (GND=1/VOUT=2/VIN=3), 250 mA ceiling vs worst-case 3.3 V rail draw.
- **Firmware handoff** (#10c): ADS1115 AIN2 read must move to the ±4.096 V PGA (÷2 divider → 2.1 V max); Kconfig ratio 430 → 200, full/empty 4200/3000 mV.

## 1. First interactive KiCad 10 session (~1 hour, needs a desktop)

1. Open `welld.kicad_pro`, let KiCad migrate/resave all sheets (normalises the generated formatting).
2. Run **ERC**. Expected waivable items (from the wiring-pass notes — anything *else* is a real finding):
   - off-1.27-grid stub endpoints on the handful of off-grid symbol placements;
   - "input pin not driven" on passive-driven analog inputs (ADS1115 AINx, FB pins);
   - style-grade label/wire overlaps from generated placement.
3. Re-run `python3 hardware/pcb/netlist_check.py` after the resave — it must still report zero mismatches (guards against the migration moving anything).
4. Replace the custom `welld:ESP32_C6_MINI_1U` symbol with the official Espressif library part (pin numbering of the custom one was never verified) and re-run ERC + `netlist_check.py`.
5. Swap SJ2–SJ5 to the *Bridged* solder-jumper variants (currently Open).

## 2. One vendor question (email, blocks co-charge only)

- Ask the pack vendor for the **PCM continuous charge rating** of a **1S2P** Sinowatt GR 3350 mAh build (blocker #7a, re-scoped 2026-07-19). Worst-case co-charge is now TP4056 1 A + CN3791 ≈1.2 A ≈ 2.2 A into ≈6.7 Ah of parallel cells (≈0.33C — comfortable at cell level). Until answered, do not rely on simultaneous solar + USB charging; either path alone is fine at cell-class norms.

## 3. Layout (in KiCad, using the written constraints)

- `placement_constraints.md` is current (rewritten 2026-07-19): Group G = TP4056 **thermal** cluster (no switching loop — EPAD pour is the constraint, ≈1.3 W at 1 A), Group L = CN3791 integrated buck (C17→VIN→SW→D_SOLAR hot loop; **CSP/BAT Kelvin pair routed together to R19**), Group B = HT7333-A LDO (trivially quiet now).
- `kicad_place_script.py` (PCB-editor scripting console) gives starting placements.
- Board outline stays 80 × 55 mm. All 1S replacement parts are iron-friendly except the two EPADs (TP4056 SOP-8-EP, and the ESP32 module) — hot air preferred.

## 4. Order (all LCSC numbers verified 2026-07-14)

- BOM: `bom_footprints.md` — updated 2026-07-19 for the 1S conversion. Verified numbers carried over: PRTR5V0U2X **C12333**, SMAJ5.0A **C98802** (now also D13), PTC C210838, AO3400A C20917, HRO USB-C C165948.
- **Order-time checks (grew with the 1S conversion)**: TP4056 EPAD variant (LCSC TBD), CN3791 (C124423 verify), HT7333-A (C21583 verify), SMAJ10CA for D8/D14 (C2836474 unconfirmed), D11 (C8057 / alternate C110519).

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
| 10 | ADS1115 AIN2 reads correctly up to 4.2 V pack (±4.096 V PGA, ratio 200) | 1S firmware handoff (#10c) — clipping at full charge is the failure mode |

## 6. Enclosure (after layout freezes connector positions)

- `hardware/case/` does not exist yet; the README's case section describes the *old* 100 × 55 board (current: 80 × 55). Case work is deliberately last — it consumes final connector/TP positions from the layout (TP13 factory-reset pad must stay reachable with the lid off).
