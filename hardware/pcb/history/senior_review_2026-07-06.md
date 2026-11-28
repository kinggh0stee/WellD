# Senior Hardware Review — 2026-07-06

Reviewer: Claude Fable 5 (direct review, per project owner's request).
Scope: full `hardware/pcb/` state after the 2026-07-05/06 cycle — electrical review pass (`bd3c3f0`), component selection review (`2e48249`), IP2326 datasheet verification (`a758a26`) — plus the firmware↔hardware contract changes on this branch.

## VERDICT: APPROVED for continued schematic work — **BLOCKED for layout/ordering** (unchanged from 2026-07-05; the gating item is symbol/BOM reconciliation, not a design flaw)

## CRITICAL (must fix before any layout or ordering)

1. **Schematic symbols still lag the BOM.** Verified by grep of `power.kicad_sch`: D15 (boost rectifier), Q3/Q4/Q5 (disconnect/driver/divider FETs), R15/R16/R25/R27/R29, C36, TP13, L3, RT1, R_VSET, and the IP2326 (U12) itself have BOM rows and net documentation but **no schematic symbols**; D8/D14 still carry `SMAJ28CA` values and C8 still 100 nF in the sheets vs SMAJ24CA / 1 nF in the BOM. Anyone generating a netlist or BOM from the schematic today builds the *old* design. This was warning #3 on 2026-07-05 and remains the tape-out gate.
2. **MT3608B symbol pinout is inverted vs the real part.** The custom symbol has IN=1/SW=5; the MT3608 family SOT23-6 standard is **SW=1, GND=2, FB=3, EN=4, IN=5, NC=6** (consistent with the 2026-07-05 review's independent suspicion and general family documentation; direct datasheet fetch was proxy-blocked — re-verify from the Aerosemi PDF before the symbol edit). As drawn, VBAT would be routed into the switch node and the inductor into VIN. Fix the symbol before any wiring pass.
3. **U12 footprint assumption was wrong and is now corrected in docs only.** The IP2326 is a 24-pin + EPAD part (datasheet V1.2, pin map recorded in `component_selection_review.md`), not ESOP-8. The BOM row is fixed; the symbol does not exist yet (folded into CRITICAL 1). Confirm the exact package code on the LCSC C2832094 listing before drawing the footprint.

## Verified sound this cycle

- **IP2326 selection stands and got stronger**: VBATM/VBAT_GND float-when-unused resolves the decision-reopening balance question with zero connector change; EN (pin 12) exists with TP5100-CE-compatible polarity, so the auto-charge decision is reversible in firmware-free fashion; RVSET=120 kΩ CV correction (8.3 V typ / 8.4 V max) removes the 8.5 V-max hazard of the NC strap and converges with CN3722's 8.31 V for co-charge; RISET=90 kΩ → 1 A is now datasheet-firm; the NTC pin (20 µA source) is a concrete implementation path for the previously-missing sub-zero charge cutoff (systemic finding O-1) — **wire RT1 as a real pack NTC, do not strap it fixed**.
- **AP63203WU (3.3 V fixed) reasoning re-checked**: variant table logic (03 = 3.3 V fixed, 05 = 5 V fixed) matches family documentation; FB-to-VOUT with R_FBH/R_FBL DNP'd is internally consistent across all three docs.
- **Boost rewire + Q3/Q4 disconnect and Q5 high-side battery divider**: topology and polarity re-verified against the firmware (GPIO5/GPIO15 semantics unchanged, 10 ms VLOOP settle now in code and Kconfig help); the sleep-leak analyses (L1+D15 path, AIN2 ESD-diode bias) remain correct.
- **Firmware↔hardware contract**: GPIO map (4 pending-swap annotated, 13 factory-reset, 14 LED) consistent across CLAUDE.md / README / Kconfig / main.c comments; EP6 LQI implementation verified against the pinned esp-zigbee-lib 2.0.1 headers (`ezbee/nwk.h`) — not against guesses.

## WARNINGS (non-blocking)

1. **F2 PTC margin is thin**: ≈1.9 A continuous boost input vs 2 A hold, and PTC hold current derates ~20 % at 60 °C enclosure ambient → nuisance-trip risk in summer. Recommendation recorded in the BOM: 2.5 A-hold part, or RISET=120 kΩ (0.75 A charge) if unavailable.
2. **CN3722 dark-quiescent and package (SSOP-10 vs the 8-pin symbol) remain unverified** — datasheet fetch attempts were partially proxy-blocked. Family knowledge says SSOP-10 with CSP/CSN current sense (not a PROG resistor), which would invalidate the current R19 "VPROG" wiring note. Treat blocker #4 as still open and assume the symbol is wrong until proven otherwise.
3. **Co-charge CV stack-up**: with RVSET=120 kΩ the IP2326 max CV (8.4 V) still tops the CN3722 (8.31 V); acceptable (pack limit 8.4 V, PCM backstop) but means USB presence always "wins" the final 90 mV — bench-verify both chargers' behaviour at handover before enclosure sealing.
4. **SMAJ24CA clamp vs CN3722 abs max** (carried from 2026-07-05): standoff margin is fixed; genuine surge still clamps ~39 V > 28 V abs max. If lightning-adjacent installs are expected, add a series element or a gas-discharge stage; out of scope for the current revision.

## Open items going into the next cycle (ordered)

1. Draw the missing symbols + sync values (CRITICAL 1), fixing the MT3608B pinout (CRITICAL 2) and drawing the 24-pin U12 (CRITICAL 3) in the same pass, then wire the sheets — `schematic_connections.md` is complete enough to wire from.
2. Clear remaining blockers: CN3722 package/current-set (#4), USBLC6-2SC6 pinout (#5 — family standard is I/O1=1, GND=2, I/O2=3, I/O2'=4, VBUS=5, I/O1'=6; verify), PRTR5V0U2X package, SMAJ3.3CA leakage (#6), pack PCM ≥2 A + sub-zero strategy via RT1 (#7), F2 MPN (#8), ESP32-C6-MINI-1U official symbol swap.
3. ERC + netlist-vs-`schematic_connections.md` diff once wired; then `placement_constraints.md` Group G rewrite for the IP2326 hot loop.
