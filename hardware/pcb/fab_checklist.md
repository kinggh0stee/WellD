# Path to fabrication — ordered checklist (2026-07-15)

Consolidates the remaining work from `senior_review_2026-07-06.md`, `component_verification_2026-07-14.md`, and the blocker list in `schematic_connections.md`. The schematic is **complete**: all symbols datasheet-verified, fully wired (stub+label), netlist machine-verified (393 pins / 78 nets / 0 mismatches, `netlist_check_output.txt`). Everything below is what still stands between this repo and ordering boards.

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

- Ask the pack vendor for the **PCM continuous charge rating** of the Sinowatt GR 3350 mAh 2S1P pack (blocker #7a). Nothing is published. Until answered, do not run solar (0.5 A) + USB (1 A) co-charge; either path alone is fine at cell-class norms.

## 3. Layout (in KiCad, using the written constraints)

- `placement_constraints.md` is current: Group G = IP2326 hot loop (VIN cap → L3/LX → VSYS caps → VOUT, EPAD thermal vias), Group L = CN3722 external buck (M_SOLAR/D16/D_SOLAR/L_SOLAR hot loop; **CSP/BAT Kelvin pair routed together to R19**).
- `kicad_place_script.py` (PCB-editor scripting console) gives starting placements.
- Board outline stays 80 × 55 mm. IP2326 is QFN-24 with EPAD — plan hot-air/reflow, not iron.

## 4. Order (all LCSC numbers verified 2026-07-14)

- BOM: `bom_footprints.md` — every active part now carries a verified LCSC number (headline: IP2326 **C2832094** — *not* the similarly-listed IP2326-NPD C5441281; AP63203WU-7 C780769; PRTR5V0U2X **C12333** — the old number was a clone of a different chip; SMAJ5.0A C98802; PTC C210838).
- Two order-time checks left: D13 (C2836474) and D11 (C8057 — known-good alternate C110519) availability.

## 5. First-article bench-verify list (before enclosure sealing)

| # | Check | Why |
|---|-------|-----|
| 1 | MT3608B pin continuity (SW↔L1 node, IN↔VBAT) before first power-on | pin map confirmed from library sources, never from the raw Aerosemi PDF |
| 2 | +3V3 rail starts and regulates 3.3 V | new C_BST_AP bootstrap path; U1 was renumbered |
| 3 | IP2326 BAT_STAT polarity (open-drain vs push-pull) | R38 fit decision depends on it |
| 4 | IP2326 VOUT dark quiescent < 10 µA; CN3722 VCC dark quiescent | nightly battery budget |
| 5 | Charger CV handover: solar 8.29 V vs USB 8.3 V setpoints under co-charge | verify no oscillation at the 90 mV overlap |
| 6 | NTC cutoffs: both chargers stop below ~0–3 °C (RT1, RT_SOLAR) | outdoor Li-ion; thresholds computed, not measured |
| 7 | MT3608B EN-low shutdown current < 1 µA | sleep-budget assumption |
| 8 | IP2326 behaviour on weak 5 V sources (input-adaptive limiting) | blocker 2h; DM/DP floated by design |
| 9 | Loop reading sanity vs known pressure; SMAJ5.0A leakage invisible on the shunt | D9/D10 substitution validation |

## 6. Enclosure (after layout freezes connector positions)

- `hardware/case/` does not exist yet; the README's case section describes the *old* 100 × 55 board (current: 80 × 55). Case work is deliberately last — it consumes final connector/TP positions from the layout (TP13 factory-reset pad must stay reachable with the lid off).
