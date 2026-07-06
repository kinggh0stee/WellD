# WellD PCB — Component Selection Review — 2026-07-05

**Scope:** selection/architecture review of every active component and key passive in
`bom_footprints.md`. This is *not* a wiring pass — the electrical-gate/wiring review ran
last cycle (`senior_review_2026-05-25.md` + the 2026-07-05 design-change list in
`schematic_connections.md`). No datasheet access was available during this review: every
parameter marked ⚠️ **verify** has been added to the blocker list in
`schematic_connections.md` and must be confirmed against the vendor datasheet before
schematic capture / tape-out.

**Review criteria:** electrical fit for a 2S Li-ion (6.0–8.4 V), sleep-dominated
(≈15 ms VLOOP duty per 5-min wake) outdoor device; quiescent draw; temperature range
(outdoor enclosure, assume −20…+60 °C internal); LCSC/PCBWay sourcing;
hand-solderability where rework is plausible.

**Verdict summary:**

| Item | Decision |
|------|----------|
| 1. TP5100 (USB charger) | **REPLACED (firm)** → Injoinic **IP2326** 5 V→2S synchronous boost charger. BOM + wiring reference updated. |
| 2. CN3722 (solar MPPT) | **Keep.** Co-charging with IP2326 is safe; two verify items added (night-time BAT quiescent, TEMP/NTC pin). |
| 3. AP63203WU (3.3 V buck) | **Keep.** 22 µA Iq is acceptable for the sleep budget; TPS62902 noted as a lower-Iq alternative, not worth the package downgrade. |
| 4. MT3608B (12 V boost) | **Keep** with the existing D15 + Q3/Q4 external load disconnect. No common alternative offers true disconnect at VIN > 8.4 V for this price/package. |
| 5. Everything else | Recommendations only — see findings table. Two new systemic risks flagged: **no battery-temperature charge cutoff** (Li-ion charging below 0 °C) and **PTC F2 undersized for a boost charger's input current** (F2 change made firm as part of the charger swap). |

---

## 1. USB charger: TP5100 → IP2326 (FIRM CHANGE)

### Why TP5100 had to go
TP5100 is a switching **step-down** 1S/2S charger: VIN must exceed the pack CV point
(8.4 V + margin). From 5 V USB it can never charge a 2S pack — the path was
non-functional as designed (already flagged in the BOM header). Two fix architectures
were considered:

| Option | Parts | Assessment |
|--------|-------|------------|
| A. Keep TP5100, add 5 V→12 V pre-boost (e.g. a second MT3608B at ~2 A) | 2 ICs, 2 inductors, diode | Double conversion (boost→buck), ~80 % end-to-end efficiency, two hot loops, TP5100 package still wrong in the schematic (QFN-16, not SOP-8), more board area in an already-tight 80×55 mm layout. |
| **B. Replace with an integrated 5 V→2S boost charger (IP2326)** | **1 IC, 1 inductor** | Single synchronous conversion (~90 %), purpose-built for exactly this topology (2S packs charged from USB — ubiquitous in 2S power tools/lamps/speakers), ESOP-8 is hand-reworkable, Injoinic is an LCSC-native brand with strong stock history. **Chosen.** |

### IP2326 — selection rationale
- **Function:** synchronous boost charger, 5 V VBUS in → 8.4 V CV / CC into a 2S pack,
  up to ~2 A charge current (we set ~1 A), with input-power-adaptive throttling that
  folds back charge current when a weak USB source sags — this is what makes it safe on
  an uncharacterised 5 V wall adapter behind our passive 5.1 kΩ CC sink strapping.
- **Package:** ESOP-8 (SOP-8 + exposed pad). Hand-solderable, and the existing Group G
  8×8 mm thermal pour requirement in `placement_constraints.md` carries over (≈0.9 W
  dissipation at 1 A charge, 90 % efficiency).
- **Sourcing:** Injoinic (英集芯) is stocked directly at LCSC; exact C-number to be looked
  up at order time (deliberately not quoted here — see blockers).
- **Runners-up:** CS5095 (cheaper, less documented, weaker adaptive input limiting);
  SC8815 (Southchip buck-boost, I²C controlled — capability overkill, QFN-32, needs
  firmware driver); MT3608B pre-boost + TP5100 (option A above, rejected).

### Integration changes (applied to BOM + `schematic_connections.md`)
- **U12** TP5100 SOP-8 → **IP2326 ESOP-8**.
- **L3 (NEW):** boost power inductor, placeholder 2.2 µH / Isat ≥ 3 A / 5×5 mm — final
  value per datasheet ⚠️.
- **R35** repurposed: TP5100 PROG (1.2 kΩ = 1 A) → IP2326 **ISET**, value TBD per
  datasheet for ~1 A ⚠️.
- **R36, R37 removed; GPIO4 freed.** IP2326-class chargers auto-run when VBUS is present
  and (per training-data recollection) expose no CE pin. If the datasheet proves an
  enable exists, GPIO4 gating can be restored — flagged in blockers. **Firmware must be
  told GPIO4 is no longer USB_CE** (it currently drives it HIGH to charge; driving an
  unconnected pin is harmless, so firmware can lag the PCB without hazard).
- **R38** kept (4.7 kΩ to +3V3 → TP15): reassign to the IP2326 charge-status/LED pin;
  verify pin, polarity, and whether it is open-drain ⚠️.
- **NTC pin:** IP2326 has an NTC input. Strap components are TBD pending the datasheet
  ⚠️ — and see finding O-1 below: we should *use* it, not strap it out.
- **F2** 1.1 A-hold PTC → **2 A-hold** (e.g. Bourns MF-MSMF200/16X class ⚠️ verify exact
  suffix/voltage). A boost charger's *input* current exceeds its charge current:
  1 A × 8.4 V / (5 V × 0.9) ≈ **1.9 A at VBUS** — the old MF-MSMF110 (1.1 A hold) would
  sit in trip territory during every normal charge.
- **C27/C28/C29** retained (values within IP2326 app-note norms; confirm ⚠️).
- USB-C front end unchanged: J13, U11 USBLC6-2SC6, R50/R51 5.1 kΩ CC sinks.

### Open risk carried as a blocker
IP2326 is documented (from training data) as supporting **2-cell balancing via a
mid-cell pin**. The WellD pack is a sealed 2S1P with integrated PCM and a **2-pin XT30**
— there is no mid-cell tap. Verify from the datasheet whether the balance/mid-cell pin
may be left unconnected (or strapped) when no tap exists. If it is mandatory, the
fallback is either (a) a 3-pin battery connector (J1 change → case + BOM impact) or
(b) the CS5095-class no-balance alternative. This is blocker #2a and is the single item
that could reopen the charger decision.

---

## 2. CN3722 solar MPPT — keep

- **Fit:** 2S CC/CV with resistor-programmed MPPT and CV = 8.31 V (R33 = 590 k, fixed
  last cycle), VIN to 28 V abs max with the panel now clamped to 24 V Voc by SMAJ24CA.
  That is exactly the requirement; TI BQ24650 is the "nicer" alternative (true
  perturb-free VMPPT regulation, ±0.5 % CV) but is a QFN-16 external-FET controller —
  more parts, more cost, harder rework — unjustified for a 500 mA charge rate. Keep.
- **Co-charging with IP2326:** both are current-limited CC/CV sources feeding the same
  pack node; parallel CC/CV chargers onto a battery are inherently safe (each folds back
  as VBAT rises). Worst case combined current ≈ 0.5 A + 1 A = 1.5 A; for a typical
  ≥2.5 Ah 2S1P that is <0.6 C — fine, but ⚠️ **verify the pack PCM charge-current rating
  ≥ 2 A**. CV interaction: IP2326 (presumed fixed 8.40 V) tops the pack slightly above
  CN3722's 8.31 V, so with USB attached the USB charger finishes the charge — acceptable
  (8.40 V is the cell spec max; USB charging is a maintenance event, not the normal
  mode). No shared control pins, no conflict; CN3722 charges autonomously exactly as
  before.
- **New verify items (added to blockers):**
  - CN3722 **battery-pin quiescent when the panel is dark** — this drain is on the pack
    every night, all winter. Expect low single-digit µA; confirm.
  - CN3722 **TEMP/NTC pin** — the current 8-pin symbol is already suspect (blocker #4,
    likely SSOP-10). If the real part exposes a TEMP pin, wire it (finding O-1).
- **/CHRG interaction note:** GPIO6 solar-detect semantics are unchanged.

---

## 3. AP63203WU 3.3 V buck — keep (Iq analysis)

Sleep-current stack-up on the pack, as designed:

| Consumer | Sleep draw |
|----------|------------|
| AP63203WU Iq (VIN pin, PFM/sleep mode) | ~22 µA (datasheet typ ⚠️ verify it applies unloaded) |
| ESP32-C6-MINI-1U deep sleep | ~8–15 µA (on 3V3, ≈4–7 µA reflected to VBAT) |
| ADS1115 in power-down (kept powered on +3V3_ADS) | ~0.5–2 µA |
| DS18B20 standby (J6 VCC always fed via R28) | ~1 µA |
| CN3722 BAT-pin dark quiescent | ⚠️ verify (~3 µA expected) |
| IP2326 BAT-pin quiescent, USB absent | ⚠️ verify (<10 µA required) |
| R11 EN pull-up (10 k to VBAT, EN input leakage only) + FET pull-up leakages | negligible |
| **Total** | **≈ 35–45 µA at VBAT** |

At ~40 µA a 2.5 Ah 2S1P self-drains ≈ 1 mAh/day → ~1.2 %/month — comfortably inside a
solar-topped budget, and the buck's 22 µA is not the dominant term once charger
quiescents are counted. Alternatives considered:

| Part | Iq | Why not |
|------|----|---------|
| TI TPS62840 (60 nA) | superb | VIN max 6.5 V — cannot take 8.4 V. Disqualified. |
| TI TPS62902 (SOT-583) | ~4 µA, VIN 3–17 V | Real contender; saves ~18 µA (≈0.4 mAh/day). Costs a 0.5 mm-pitch leadless package (rework pain) and a TI-at-LCSC stock gamble. Not worth it — **recommendation only**, revisit if the measured sleep floor disappoints. |
| ST ST1PS03, Torex XC9265 etc. | sub-µA | VIN ≤ 5.5–6 V class — disqualified by 2S input. |
| LDO (TPS7A02) | 25 nA | 8.4→3.3 V at the ESP32's ~350 mA TX peak = 1.8 W dissipation. Disqualified. |

Verdict: **AP63203WU-7 stays.** Existing blocker #1 (confirm 3.3 V-fixed variant, FB tie,
BST cap need) already covers the datasheet risk. TSOT-26 is hand-solderable; Diodes Inc
is well stocked at LCSC.

---

## 4. MT3608B 12 V boost — keep, with the external disconnect

- **Duty profile:** ~15 ms per 5-min wake → duty ≈ 5×10⁻⁵. Efficiency at load is
  irrelevant; what matters is (a) zero sleep leakage — solved structurally by Q3
  (input-side P-FET disconnect) + R27, added last cycle, and (b) EN-low quiescent of the
  IC itself (<1 µA class ⚠️ verify).
- **Alternatives with true integrated load disconnect** were searched: parts with output
  disconnect (TPS61230A, TPS610995, MAX17222 …) top out at 5.5 V VIN — none accept
  6.0–8.4 V in. Boosters that do accept 2S input (TPS61175, TPS55340, SGM6623, MT3540)
  are async like the MT3608 and/or bring no disconnect either, at 3–10× the price.
  Conclusion: **there is no drop-in "better" part** — the MT3608B + SS34 + Q3/Q4
  disconnect is the correct minimal architecture. Keep.
- Selection-level notes retained/confirmed:
  - Existing blocker #3 (pin 6 BST vs NC, pin numbering) stands.
  - L1 (CDRH4D22, ~1 A Isat) saturates transiently during C20/C22 inrush at enable
    (senior-review warning #6). Acceptable at this duty cycle; **recommendation:** if L1
    is respun for any reason, choose 4.7 µH with Isat ≥ 2 A in the same 4×4 footprint
    (e.g. NR4018/XAL40xx class).
  - SJ1 (EN-to-VBAT bench tie) bypasses R27's sleep pull-down **and** leaves Q3 gated by
    Q4 anyway — harmless, fine as a debug aid.

---

## 5. Other findings (recommendations unless marked firm)

| # | Component | Finding | Action |
|---|-----------|---------|--------|
| **O-1** | **Charging vs temperature (systemic)** | Outdoor enclosure + Li-ion: **charging below 0 °C causes lithium plating**. Neither charger path currently has a battery-temperature cutoff (pack PCM protects V/I, typically not charge temperature). Both selected chargers likely expose NTC/TEMP pins (IP2326: NTC; CN3722: TEMP ⚠️ verify). | **Recommendation (strong):** add a 10 k NTC thermistor pad near/on the pack, wired to both chargers' temperature pins per datasheet; if the pack can't host one, a board-mounted NTC inside the case is a decent proxy. Added to blockers as datasheet-verify items. |
| O-2 | D5 (AO3407 reverse protection) | A MOSFET carrying a **D** refdes. Electrically fine (Vgs = −8.4 V vs ±12 V abs max — 30 % margin OK; Vds −30 V OK). | Rename **D5 → Q1** at schematic-capture time for refdes hygiene (this is the "missing Q1"). Cosmetic — recommendation. |
| O-3 | Q2/Q4 BSS123 | Vgs(th) max 1.7 V; driven at 3.3 V it only reaches "barely enhanced" spec corners at cold. Loads are trivial (100 k gate pull-ups → <100 µA drain current) so it works, but margin is thin and BSS123's LCSC row in the BOM has no C-number. | **Recommendation:** substitute **AO3400A** (Vgs(th) ≤ 1.45 V, LCSC C20917, same SOT-23) for Q2/Q4 — also consolidates on one N-FET vendor alongside the AO3407s. |
| O-4 | Q3/Q5 AO3407 | Correct: Vds −30 V, Vgs ±12 V vs 8.4 V drive, Rds(on) ~50 mΩ at Vgs −4.5 V — fine for 45 mA (Q3) / µA (Q5). LCSC C31417 stocked. | Keep. |
| O-5 | TVS strategy | Coherent: SMAJ10CA (VBAT, 10 V standoff > 8.4 V), SMAJ24CA ×2 (solar, panel Voc ≤ 24 V), SMAJ13A (VLOOP 12.06 V — 8 % standoff margin, clamp ≈21.5 V < 25 V caps), SMAJ3.3CA (loop SIG, node max 2.0 V). One risk: **low-voltage TVS have soft knees** — SMAJ3.3CA leakage at a 2.0 V working node feeds through the 100 Ω shunt and reads as loop current. 1 µA ≈ 0.005 % FS (harmless); 100 µA would not be. | ⚠️ Verify SMAJ3.3CA leakage at 2.0 V/60 °C ≤ 1 µA (added to blockers). If it fails, move to a 5 V-standoff low-leakage clamp (e.g. SMAJ5.0A) and accept the higher clamp level — R3 + D1 (PRTR5V0U2X to +3V3) still protects the ADS1115 pin. |
| O-6 | ADS1115IDGST | Right part: 16-bit/PGA/ALERT-DRDY/I²C, 2–5.5 V, powers down to <2 µA after single-shot (it stays on +3V3_ADS in sleep — fine). ADS1015 (12-bit) would actually meet the cm-level resolution need, but the saving is pennies and the firmware/driver is written. −40…+125 °C. MSOP-10 hand-solderable. | Keep. **Sourcing note:** buy the TI-genuine C37593 reel, not a "TI-compatible" clone — clone ADS1115s are endemic and have worse PGA accuracy/DRDY behaviour. |
| O-7 | ESP32-C6-MINI-1U-H4 | Correct (external-antenna variant matches the SMA/pigtail case design; −40…+85 °C; 4 MB flash fits the dual-1.5 MB OTA table). Existing blocker #5 (official Espressif symbol) stands. | Keep. |
| O-8 | USBLC6-2SC6 on a power-only port | Works, but 4 of its 6 pins clamp D± stubs that go nowhere. | Optional simplification: a single SMF5.0A on VBUS_IN would do. Not worth churn — keep. |
| O-9 | J13 USB4135-GF-A | Fine mechanically, but LCSC availability is ⚠️ (global sourcing). | **Recommendation:** allow HRO/Korean-J alternates (e.g. TYPE-C-31-M-12, LCSC C165948 class) as an approved second source — same 16-pin power-only footprint family; confirm footprint match before substituting. |
| O-10 | R2/R4 shunts (RG2012N 0.1 %) | Susumu RG-series via global sourcing only. 40 mW dissipation at 20 mA — any 0805 works; what matters is 0.1 % + low TCR (≤25 ppm/°C for outdoor ΔT: 25 ppm × 40 °C = 0.1 % extra — borderline). | **Recommendation:** approve an LCSC-stocked 0.1 % 25 ppm 0805 alternate (UNI-ROYAL/Viking precision series) to avoid a single-line global-sourcing stall. Keep 0.1 %/25 ppm as hard spec. |
| O-11 | Ceramics X5R/X7R | X5R is fine to −55 °C on the low end (outdoor cold is not a rating problem). DC-bias derating is the real issue: C17 (10 µF/35 V/1206 at up to 24 V) will deliver ~3–4 µF effective — acceptable for a TVS-clamped input filter; C20 22 µF/25 V/1206 at 12 V → ~10 µF effective, still fine for a 20 mA load. | No change. Note DC-bias expectation in layout notes if C17 behaviour ever surprises. |
| O-12 | Phoenix MC 1.5 G + STF plugs, XT30PW-F | Good outdoor-serviceability choices; G-header/STF-plug compatibility note in the BOM is correct. | Keep. |
| O-13 | DS18B20 (field probe) | Not on the BOM (external), but same counterfeit warning as O-6: clone DS18B20s dominate the market and misbehave at exactly the parasitic/timing corners this design avoids. | Procurement note: buy probes with genuine ADI/Maxim silicon or from a vetted supplier. |
| O-14 | placement_constraints.md Group G | Now stale: written for TP5100. IP2326 keeps the 8×8 mm pour but **adds a boost hot loop** (L3 ↔ SW ↔ internal sync FET ↔ C29/C28) that needs MT3608B-style tight-loop rules. | Follow-up edit to `placement_constraints.md` once the IP2326 datasheet confirms pinout (deliberately not edited in this review — placement doc is downstream of the datasheet verification). |

---

## BOM diff (firm changes only)

| Ref | Was | Now |
|-----|-----|-----|
| U12 | TP5100, SOP-8 (wrong pkg), LCSC C841540 | **IP2326**, ESOP-8, LCSC C# TBD ⚠️ |
| L3 | — | **NEW** boost inductor, 2.2 µH ≥3 A Isat 5×5 mm (value ⚠️ per datasheet) |
| R35 | 1.2 kΩ (TP5100 PROG, 1 A) | ISET, **value TBD ⚠️** (target ~1 A charge) |
| R36 | 100 kΩ CE pull-up to VUSB | **DELETED** |
| R37 | 4.7 kΩ CE pull-down | **DELETED** (restore only if IP2326 proves to have an EN pin) |
| R38 | 4.7 kΩ /CHRG pull-up (TP5100) | kept — reassigned to IP2326 status pin ⚠️ |
| F2 | MF-MSMF110/16X (1.1 A hold) | **2 A-hold 1206 PTC** (MF-MSMF200/16X class ⚠️ verify suffix) |
| NTC strap | — | **NEW placeholder** — components TBD per IP2326 NTC pin ⚠️ (see O-1) |

Board outline unchanged (80×55 mm). Net BOM delta ≈ +1 inductor, −2 resistors.

## Constraints for other agents

**Firmware** (`firmware-engineer`):
- **GPIO4 is no longer USB_CE.** IP2326 auto-charges on VBUS; there is no charge-enable
  to drive. Current firmware driving GPIO4 HIGH into an unconnected pad is harmless, so
  firmware may lag the PCB, but `components/sensor/` GPIO4 handling, the Kconfig
  default, and the CLAUDE.md GPIO table should be updated (GPIO4 becomes spare, or is
  re-tasked if the datasheet reveals an EN pin — wait for blocker #2 resolution before
  editing).
- All other GPIO assignments unchanged (5, 6, 7, 10, 11, 12, 13, 14, 15; LED on 14 per
  last cycle).
- /CHRG_USB remains hardware-only (TP15), no firmware visibility — unchanged.

**Case** (`case-engineer`):
- No dimension change, no connector change (USB-C, XT30, SMA, terminal edges all as
  before). Only contingency: if blocker #2a (IP2326 mid-cell balance pin) forces a
  3-pin battery connector, J1 and the battery slot change — hold until resolved.
- If O-1 (NTC) is adopted with a pack-mounted thermistor, the battery compartment needs
  a 2-wire thermistor route to the board.

**Layout:**
- `placement_constraints.md` Group G must be rewritten for the IP2326 boost hot loop
  after the datasheet lands (O-14). Do not start USB-section layout before that.

## Verification blockers added (full list in `schematic_connections.md`)

- #2 rewritten for IP2326: pinout/package, CV = 8.4 V, ISET value for 1 A,
  mid-cell/balance pin behaviour with a 2-pin pack (**decision-reopening item**), EN pin
  existence, NTC strap, BAT-pin quiescent < 10 µA with USB absent, input-adaptive limit
  behaviour, inductor value/current, status-pin type for R38.
- #4 extended (CN3722): dark-condition BAT quiescent; TEMP/NTC pin presence and wiring.
- #6 NEW: SMAJ3.3CA leakage at 2.0 V / 60 °C ≤ 1 µA on the loop SIG nodes.
- #7 NEW: pack PCM continuous charge rating ≥ 2 A (solar + USB co-charge), and the
  cold-charge (< 0 °C) strategy per O-1.
- #8 NEW: F2 replacement PTC exact MPN (2 A hold, ≥6 V, 1206), sized for ≈1.9 A boost
  input current.

---

## Datasheet verification results — 2026-07-06 (IP2326 v1.2 datasheet obtained)

Source: ChipSourceTek/Injoinic IP2326 datasheet V1.2 (via done.land mirror + LCSC C2832094 listing). Corrections and confirmations to §1:

**Package correction:** the IP2326 is a **24-pin package with exposed pad** (pins: DM=1, DP=2, VSET=3, NTC=4, BAT_STAT=5, LED=6, TIME_SET=7, VIN_UVSET=8, VIN_OVSET=9, CON_SEL=10, ISET=11, EN=12, VIN=13, BST=14, LX=15/16/17, PGND=18, VSYS=19/20, VOUT=21/22, VBATM=23, VBAT_GND=24, GND=EPAD) — **not ESOP-8** as assumed in §1. Confirm the exact package code (ESSOP-24/QFN-24) on the LCSC C2832094 listing before footprint work; "hand-reworkable" now depends on that answer.

**Blocker 2a (mid-cell balance) — RESOLVED, no connector change:** VBATM (23) and VBAT_GND (24) implement the optional 2S charge-equalisation function and the datasheet states both "should be left floating when doesn't use." Our 2-pin XT30 pack works as-is with balancing disabled (the pack's internal PCM still protects). Optional future upgrade: 3-pin J1 + VBATM wiring enables charger-side balancing.

**Blocker 2e (EN pin) — RESOLVED, EN exists:** pin 12, "the chip does not work after pull down to ground" (pull-low-to-disable, float/high = enabled). Decision stands: leave EN floating → auto-charge on VBUS, GPIO4 stays freed. Note the polarity matches the old TP5100 CE drive exactly (HIGH=charge, LOW=off), so wiring GPIO4→EN is a zero-firmware-change option if charge gating is ever wanted again.

**CV strap — CORRECTION to §1:** RVSET=NC gives 8.4 V *typ* but **8.5 V max** — above the 8.40 V 2S limit. Use **RVSET = 120 kΩ → 8.3 V typ / 8.4 V max**, which also converges with the CN3722's 8.31 V CV for co-charging. R_VSET added to the BOM implication list.

**Other confirmed facts:** ISET = pin 11, must not float, ICHG = 90000/RISET (RISET=90 kΩ → 1 A; datasheet efficiency specs quoted at that value) — R35 value now firm at 90 kΩ for 1 A. CON_SEL floating = 2S (correct for us; 1 kΩ to GND = 3S). NTC = pin 4 with a 20 µA source current — **this is the concrete path to the sub-zero charge cutoff (review finding O-1 / blocker #7)** for the USB path; strap a 10 kΩ-class NTC per the datasheet threshold table. BST cap 0.1 µF between BST(14) and LX; inductor 2.2 µH (datasheet-supported value, ≥3 A Isat per §1 stands); VSYS needs 2×22 µF at pins 19/20; VIN abs max 25 V; USB DM/DP (1/2) give input-adaptive current limiting. BAT_STAT (5) is the charge-state output → R38/TP15 reassignment in §1 confirmed viable (verify open-drain vs push-pull polarity on bench).

## Firmware API note — esp-zigbee-lib 2.0.1 (verified 2026-07-06)

Verified against the pinned 2.0.1 headers (esp-zigbee-sdk checkout, `components/esp-zigbee-lib/include/ezbee/nwk.h`): `ezb_nwk_get_next_neighbor(ezb_nwk_info_iterator_t *, ezb_nwk_neighbor_info_t *)` exists with `uint8_t lqi` and `uint8_t relationship` (`EZB_NWK_RELATIONSHIP_PARENT = 0`) fields; iterator init is `EZB_NWK_INFO_ITERATOR_INIT` (NULL); success code `EZB_ERR_NONE` (`ezbee/error.h`). The CONFIG_ZB_SDK_1xx compat layer maps `esp_zb_nwk_get_next_neighbor` onto it. The EP6 device-LQI stub in `components/zigbee/zigbee.c` has been replaced with a real parent-neighbor read on this basis.
