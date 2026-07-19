# WellD PCB — "Better Options" Alternatives Review — 2026-07-15

**Scope:** every active position in `bom_footprints.md`, reviewed through a different
lens than `component_verification_2026-07-14.md` (which established that every part is
*correct*). This pass asks, position by position: **is there a better and more commonly
used alternative?** Judged on: community track record / design-in volume (appearance in
shipped open-hardware and commercial designs), LCSC/JLCPCB availability and
multi-sourcing, simplicity (fewer externals, fewer failure modes), documentation
quality, and price — against the WellD profile: outdoor solar+USB 2S Li-ion,
deep-sleep-dominated (nightly µA budget dominates over efficiency at load), hobby-scale
assembly (hot-air OK, no stencil oven guaranteed), 80×55 mm board.

**Nothing in this document is applied to the BOM or schematic.** SWAP and OPTIONAL
verdicts are proposals for user approval only.

---

## Proposed changes (awaiting approval — not applied)

| # | Position | Proposal | Effort |
|---|----------|----------|--------|
| P-1 | Q2/Q4 (BSS123) | **SWAP → AO3400A** (LCSC C20917). Settles review finding O-3: Vgs(th) max 1.45 V vs BSS123's 1.7 V at 3.3 V drive, ~10× cheaper, 1M+ LCSC stock, consolidates on the AOS reel family already used for Q3/Q5/D5/M_SOLAR. Same SOT-23 footprint — value-field edit only. | Trivial |
| P-2 | J13 (USB4135-GF-A) | **SWAP → HRO TYPE-C-31-M-12** (LCSC C165948) as *primary*, GCT demoted to approved alternate. Removes the last global-sourcing connector; ~$0.10 vs ~$1+; the de-facto standard USB-C receptacle of hobby/low-volume boards; 4 THT shell legs give better field retention than the GCT's SMT shell. Requires a footprint swap (not pin-compatible with the USB4135 land pattern). | Footprint change |
| P-3 | J4/J5 field lines | **OPTIONAL: add 2-electrode GDT footprints (DNF)** between each loop terminal and chassis/GND (90 V class, SMD 3216/4532, e.g. Littelfuse GTCS23-900M-R05 / BOURNS 2038-09-SM class). Completes the industrial 3-stage GDT → series-R → TVS norm for buried outdoor cable runs; DNF by default, populate only for long exposed runs. | 2 footprints |
| P-4 | M_SOLAR (AO3407) | **OPTIONAL: SI2319CDS** (−40 V, Vishay LCSC C146287, in stock ~$0.16) for the solar buck high-side only. Restores >60 % Vds margin over the 24 V-clamped panel + switch-node ringing (currently ~23 %). Endorses verification-sweep recommendation R-1. Same SOT-23 pinout. | Value-field edit |

Everything else: **KEEP** — details below.

---

## Position-by-position verdicts

### 1. U12 — IP2326 (USB 5 V → 2S boost charger, QFN-24) — **KEEP**

| | |
|---|---|
| Current | Injoinic IP2326, QFN-24 4×4 mm, LCSC C2832094, ~$0.30 |
| Verdict | **KEEP** |
| Best common alternative | none better; CS5095E is the runner-up on paper only |

**Design-in commonality — confirmed strong.** The IP2326 is not an obscure pick: it is
*the* module-market standard for USB→2S/3S boost charging. Evidence: a whole ecosystem
of off-the-shelf IP2326 charge boards (Aaenics, Hailue on Amazon, GooGadget,
Masterlexon, Micro Ohm, ICStation clones), a dedicated done.land documentation page and
mirrored datasheet, and healthy LCSC stock at C2832094. That is exactly the "appears in
shipped designs" track record we want, and Injoinic is an LCSC-native brand
(IP5306/IP2312 family ubiquity).

**Alternatives weighed:**
- **CS5095/CS5095E** — SOP-8 (hand-iron-friendly, a real advantage vs our QFN
  constraint), cheaper. But documentation is thin (Chinese-only, sparse distributor
  data — a 2026-07 search surfaces almost nothing beyond a bare "three-section boost
  charging chip" description), weaker/absent input-adaptive current limiting (which is
  what makes the IP2326 safe on uncharacterised 5 V adapters), and far fewer shipped
  boards. The package win does not outweigh the documentation and behaviour gap.
- **SC8815** — Southchip buck-boost with I²C control. More capable, but QFN-32, needs a
  firmware driver, and is capability overkill; commonality is in DIY bench-supply
  projects, not set-and-forget chargers.
- **IP2312-class** — 1S buck chargers; wrong topology for 2S from 5 V.
- **Architecture alternative (5 V→2S via a dedicated module soldered on)** — common in
  one-offs but indefensible for a fabbed PCBA (uncontrolled module BOM churn).

**QFN caveat, honestly:** QFN-24 + EPAD means hot-air only — already accepted in
`fab_checklist.md` §3. No SOP-packaged part matches the IP2326's commonality +
documentation; if a future rev insists on an iron-solderable charger, CS5095E is the
candidate to re-evaluate *after* obtaining and reading its full datasheet.

### 2. U7 — CN3722 (solar MPPT buck controller, TSSOP-16) — **KEEP**

| | |
|---|---|
| Current | Consonance CN3722, TSSOP-16, LCSC C77905, ~$0.50, external P-FET buck stage |
| Verdict | **KEEP** |
| Best common alternative | TI BQ24650 (the commercial standard) — for a future rev only |

- **CN3791 (the hugely common hobby solar part) cannot do 2S.** Community sources are
  unambiguous: CN3791 boards are 1S Li-ion/LiPo (4.2 V CV) and "you cannot use two
  cells in series without a different charger" (jrattechworks). There is no multi-cell
  CN3791 variant — **the CN3722 *is* Consonance's multi-cell sibling**, sold on the same
  hobby-module channels (ICStation "CN3722 MPPT controller 18 V panel" boards). Within
  the CN-family ecosystem we are already on the correct, commonly-used part for 2S.
- **BQ24650** is the commercial standard (Voltaic Systems chargers, the Hackaday "Open
  MPPT" project, CircuitMaker open designs, countless AliExpress/Amazon boards — mostly
  3S/4S builds). It offers true synchronous rectification and ±0.5 % CV. But it is a
  VQFN-16 external-dual-N-FET controller: *more* externals than the CN3722's ~10 (two
  FETs + bootstrap + sense + dividers), harder rework than TSSOP, ~6× the price, and a
  TI-at-LCSC stock gamble. At our 500 mA charge rate the efficiency and regulation
  deltas buy nothing measurable. The right choice *if* a future rev raises solar charge
  current ≥2 A.
- **LT3652** — excellent, monolithic (fewer externals than CN3722), well documented,
  and genuinely common in Western open hardware. Disqualified on price (~$6–8) and
  ADI single-sourcing; ~10× the CN3722 for the same function at our power level.
- The CN3722's external count is already placed and netlist-verified (2026-07-14);
  swapping now would re-open the solar sheet for zero field benefit.

### 3. U1 — AP63203WU (6–30 V → 3.3 V buck) — **KEEP**

| | |
|---|---|
| Current | Diodes AP63203WU-7, TSOT-26, LCSC C780769, 22 µA Iq, VIN 3.8–32 V |
| Verdict | **KEEP — already the sweet spot** |
| Best common alternative | TPS62902 (lower Iq) — bench-data-contingent only |

The field of "truly common 6–30 V-in, 3.3 V-out, low-Iq, hand-solderable bucks" is
smaller than it looks, and the AP63203 sits at its centre:

| Candidate | Iq | Why not |
|-----------|----|---------|
| **AP63203WU (current)** | **22 µA** | SparkFun sells a dedicated AP63203 breakout — real hobby design-in volume; LCSC-native Diodes stock; TSOT-26 iron-solderable; EMI-optimised (FSS) |
| TPS54202 (the JLCPCB-era favourite) | ~35–50 µA Eco-mode class | More common in cheap boards, but *higher* Iq — wrong direction for a nightly-µA budget; no advantage elsewhere |
| MP2315S | ~66 µA AAM | Common, good part, higher Iq, costs more |
| TPS62841 / TLV62569 / SY8089 / ST1PS03 / XC9265 | sub-µA–µA | All VIN ≤ 5.5–6.5 V — disqualified by the 2S 8.4 V input |
| XL1509 / MC34063 class | mA | Iq disqualifies instantly |
| ME3116 (Microne 30 V) | ~100 µA class | Less documented, higher Iq |
| TPS62902 | ~4 µA | The only genuinely *better* electrical option (saves ~18 µA ≈ 0.4 mAh/day) — at the cost of a 0.5 mm-pitch leadless SOT-583 (rework pain) and TI stock risk. Already logged in `component_selection_review.md` §3 as revisit-if-sleep-floor-disappoints. Stands. |

The 2026-07-05 Iq analysis (~40 µA total sleep floor, buck not the dominant term)
remains valid; nothing found in this pass displaces it.

### 4. U8 — MT3608B (12 V VLOOP boost) — **KEEP**

| | |
|---|---|
| Current | MT3608B SOT-23-6, LCSC C84005, + SS34 + Q3/Q4 external load disconnect |
| Verdict | **KEEP** |
| Best common alternative | none — the disconnect architecture is the differentiator |

The MT3608 is arguably the most-cloned boost converter on earth (module volume rivals
the TP4056); commonality is beyond question. Re-checked the two conceivable "better"
shapes:
- **Fixed-output boosts / boosts with true output disconnect** (TPS61230A, TPS610995,
  MAX17222…): all top out at ~5.5 V VIN — none accept 6.0–8.4 V. Unchanged from the
  2026-07-05 search; no new part class found.
- **Charge pump** for 12 V @ 45 mA from 6–8.4 V: an unregulated doubler lands at
  12–16.8 V (needs a post-regulator) and no common charge pump delivers 45 mA at this
  ratio. Worse in every dimension.

At a 5×10⁻⁵ duty cycle, efficiency is irrelevant and leakage is everything — and
leakage is solved *structurally* by the Q3 input-side P-FET disconnect, which no
integrated alternative at this VIN provides. The L1 Isat upgrade note (NR4018/XAL40xx
class if respun) and the MT3608B EN-low quiescent bench check stand.

### 5. U9 — ADS1115 (16-bit I²C ADC) — **KEEP**

| | |
|---|---|
| Current | ADS1115IDGST MSOP-10, LCSC C37593 (TI-genuine), 100 Ω shunt front-ends |
| Verdict | **KEEP** |
| Best common alternative | INA226 (seriously evaluated below) — elegant but not better *here* |

- **Community-standard check:** the ADS1115 + precision shunt is literally the
  productised norm for hobby/industrial-lite 4–20 mA receivers — NCD.io sells 1/2/3/4
  channel "4-20 mA Current Loop Receiver 16-Bit ADS1115" modules as a product line.
  Our topology (100 Ω 0.1 % shunt, RC filter, ADS1115 AIN) *is* the reference
  architecture. Driver written, DRDY interrupt flow tested, host-test coverage exists.
- **INA226 — the serious alternative.** Purpose-built current monitor: 16-bit, I²C,
  ALERT pin, ±81.92 mV shunt range (2.5 µV/LSB), 0–36 V bus measurement. Genuinely
  attractive properties for this design: at ~4 Ω shunt, 20 mA → 80 mV FS with ~0.6 µA
  loop resolution (ample); burden voltage drops from 2 V to 80 mV (more transducer
  compliance headroom); and its 36 V bus input could read VBAT *directly* — deleting
  the whole gated battery divider (Q2, Q5, R7, R8, R16, R26, C8). Why it still loses:
  1. **Channel count** — INA226 is one current channel. WellD has two loop channels
     (J4/J5) plus battery → two INA226s + rework, vs one ADS1115 doing all of it on
     four muxed inputs.
  2. **Signal robustness at the terminals** — an 80 mV full-scale node behind outdoor
     surge clamps is far less forgiving of TVS/GDT leakage and offset than our 2 V
     node; the SMAJ5.0A leakage analysis (blocker #6) would have to be redone ~25×
     tighter. 4 Ω 0.1 % low-TCR shunts are also a less standard value than 100 Ω.
  3. **Continuous-monitor DNA** — INA226's strength is always-on power telemetry with
     averaging; our profile is one single-shot conversion per wake. ADS1115 powers
     down to <2 µA automatically after single-shot; INA226 needs explicit mode
     management (its power-down is fine, but nothing is gained).
  4. Firmware rewrite of a working, host-tested driver for zero field-visible benefit.
- **ADS1015**: 12 bit meets the cm-level need, saves pennies — not worth touching a
  written driver (unchanged from O-6).
- **ESP32-C6 internal ADC**: 12-bit SAR with well-documented INL/offset problems,
  needs per-unit calibration, and shares the die with the 802.15.4 radio whose
  interference is exactly why the wake-cycle orders ADC-before-radio. Eliminating the
  ADS1115 would save ~$1 and cost the design its measurement integrity. Rejected.
- Sourcing note from O-6 stands: buy the TI-genuine C37593 reel — ADS1115 clones are
  endemic.

### 6. Q2/Q4 — BSS123 → **SWAP RECOMMENDED: AO3400A** (settles O-3)

| | |
|---|---|
| Current | BSS123 SOT-23 (no LCSC number in BOM — itself a symptom) |
| Verdict | **SWAP RECOMMENDED → AO3400A** (P-1) |
| Best common alternative | AO3400A, LCSC C20917; 2N7002 approved second source |

Three-way settle:
- **BSS123**: Vgs(th) max **1.7 V** — at 3.3 V drive it is only "barely enhanced" at
  cold spec corners; community sources also flag it as *pricier* than 2N7002 for worse
  Rds(on). No LCSC number was ever pinned. Weakest of the three on every axis.
- **2N7002** (the most common N-FET on earth, LCSC basic-part class, massive multi-vendor
  stock): fine for 5 V systems, but Vgs(th) max 2.5 V — at 3.3 V gate drive the margin
  is *worse* than BSS123's on datasheet limits. Works at our µA-class loads, but
  commonality shouldn't buy a thinner corner.
- **AO3400A** (LCSC C20917, AOS, 1M+ stock, ~$0.02): Vgs(th) max **1.45 V**, fully
  enhanced at 2.5 V, 5.7 A-class Rds(on) headroom, and the community's default choice
  precisely for 3.3 V-driven gates ("better in 3.3 V logic-level applications" is the
  standing community consensus vs 2N7002-class parts). Also consolidates on the AOS
  reel family already on the board (AO3407 ×4).

Same SOT-23 G-S-D pinout; the swap is a value/LCSC-field edit in two BOM rows plus the
schematic value fields. 2N7002 stays listed as an emergency second source (it will
switch these µA loads despite the thin margin).

### 7. D5/Q3/Q5 AO3407 — **KEEP** · M_SOLAR — **OPTIONAL: SI2319CDS**

| | |
|---|---|
| Current | AO3407 (−30 V/±20 V/−4.1 A), LCSC C31417, four positions |
| Verdict | **KEEP** for D5/Q3/Q5; **OPTIONAL swap** for M_SOLAR only (P-4) |
| Best common alternative | AO3401A (approved alternate); SI2319CDS for M_SOLAR |

- **Commonality:** AO3407 and AO3401A are both top-tier common (AO3401A: LCSC C15127,
  1.8M+ stock, multi-vendor including clone brands). They are the same −30 V class —
  swapping D5/Q3/Q5 to AO3401A/SI2301 buys nothing (identical ratings, marginal price
  delta) and costs a BOM churn. AO3401A is hereby noted as an approved drop-in
  alternate for all −30 V P-FET positions (same pinout, same class); SI2301 likewise
  (−20 V — acceptable only for Q5/D5/Q3 which see ≤8.4 V, *not* for M_SOLAR).
- **M_SOLAR** is the one position where "better" exists: it faces the 24 V-clamped
  panel node plus switch-node ringing with only ~23 % Vds margin (verification-sweep
  R-1). **SI2319CDS** (−40 V, SOT-23, same pinout) is stocked at LCSC as genuine
  Vishay (C146287, ~$0.16) *and* as a VBsemi clone (C558254, ~$0.05) — real
  multi-sourcing. AO3415A was checked and rejected: it is a **−20 V** part, not −40 V.
  This stays OPTIONAL: the SMAJ24CA clamp + CN3722's own 30 V abs max mean the FET is
  not the first thing to die in a genuine surge, but at $0.16 it is cheap robustness.

### 8. TVS strategy (SMAJ family) — **KEEP** · GDT stage — **OPTIONAL footprint** (P-3)

| | |
|---|---|
| Current | SMAJ10CA (VBAT), SMAJ24CA ×2 (solar), SMAJ13A (VLOOP), SMAJ5.0A ×2 (loop SIG), + PRTR5V0U2X second stage |
| Verdict | **KEEP** SMAJ family; **OPTIONAL** GDT footprints on field loop lines |
| Best common alternative | n/a — SMAJ is already the most common SMD TVS family |

- The SMAJ family is the commodity standard: multi-vendor at LCSC (Littelfuse, ST,
  Vishay, MDD, FUXINSEMI all stocked), already verified numbers (C148223, C98802,
  C110519). No more-common family exists; SMBJ would only buy pulse power we don't need.
- **GDT question:** the industrial norm for outdoor/long-cable 4–20 mA lines is the
  3-stage coordination **GDT (coarse, kA-class) → series R (coordinating impedance) →
  TVS (fine clamp)** — confirmed as current best practice (Littelfuse/CITEL/PROSEMI
  application guidance). WellD already has stages 2 and 3 (R3/R5 100 Ω + SMAJ5.0A +
  PRTR5V0U2X). For a wellhead with a buried or aerial transducer cable run, a
  2-electrode 90 V GDT from each field terminal (J4/J5 SIG and VLOOP feed) to the GND
  lug is the missing industrial stage. Proposal P-3: **footprints only, DNF default** —
  pennies of board area, populated per-site. Not a SWAP because the SMAJ-only design
  is already adequate for induced (non-direct-strike) transients at typical runs.

### 9. U11 USBLC6-2SC6 / D1·D12 PRTR5V0U2X — **KEEP both**

| | |
|---|---|
| Current | USBLC6-2SC6 (ST, C7519, genuine); PRTR5V0U2X (Nexperia, C12333) |
| Verdict | **KEEP both** |
| Best common alternative | BAV199 (multi-vendor) as functional second source for D1/D12 |

- **USBLC6-2SC6**: one of the most-designed-in USB ESD arrays in existence; genuine ST
  at LCSC. O-8 (a lone SMF5.0A would suffice on a power-only port) remains true and
  remains not worth churn. KEEP.
- **PRTR5V0U2X**: yes, Nexperia-single-source as an exact part, but C12333 shows 40k+
  genuine stock, and the position's requirement (rail-to-rail low-capacitance,
  low-leakage clamp on ADS1115 inputs / 1-Wire) is genuinely well matched. The
  *more-common multi-vendor* alternative for an **analog clamp** position is the
  **BAV199** (dual series clamp diode, low leakage 3 pA typ, SOT-23/SOT-323, made by
  Nexperia, Diodes, onsemi, MCC, UTC — true multi-sourcing, classic instrumentation
  front-end part). Trade: BAV199 has no IEC 61000-4-2 rating and far lower pulse
  capability (140 mA-class diodes vs 180 W TVS) — acceptable *only because* the SMAJ
  first stage and 100 Ω series resistors do the energy work. Verdict: keep
  PRTR5V0U2X as primary (better surge contribution, already symbol-fixed and
  netlist-verified); record BAV199 as the approved functional alternate if C12333
  ever dries up. The clone hazard note stands: the previous LCSC number for this very
  position was a mislabelled UMW clone of a *different chip* — order Nexperia-genuine
  only.

### 10. DS18B20 / J13 USB-C / J1 XT30 / F2 PTC

| Position | Verdict | Notes |
|----------|---------|-------|
| DS18B20 probe | **note only** | Counterfeit epidemic confirmed ongoing; clones dominate marketplace probes and fail at timing/parasite corners. Procurement rule (O-13) stands: genuine ADI/Maxim silicon from authorized channels or vetted probe vendors only. Firmware's external-power-only requirement already sidesteps the worst clone failure mode. |
| J13 USB-C | **SWAP RECOMMENDED** (P-2) | GCT USB4135-GF-A is a fine connector with an official KiCad footprint but is global-sourcing at ~$1+. The **HRO TYPE-C-31-M-12 (LCSC C165948, ~$0.10)** is the de-facto standard USB-C receptacle of the hobby/low-volume world ("the connector on a large share of hobby and low-volume boards"), 16-pin USB-2.0 subset (exactly our power-only need), 5 A/10k-cycle rated, with four THT shell legs — mechanically *better* for a field-serviced port than the GCT's SMT shell. Cost: a footprint change (not land-compatible) before layout starts — which is now, i.e. the cheapest possible moment. Caveat: the part is endlessly cloned; order the Korean Hroparts C165948 listing specifically. |
| J1 XT30PW-F | **KEEP** | Amass XT30 is the uncontested hobby-power standard; right-angle PCB variant verified (C601498). Nothing is more common in this class. |
| F2 MF-MSMF250/16X-2 | **KEEP** | Bourns MF-MSMF is the reference polyfuse family (multi-clone ecosystem exists, but genuine Bourns C210838 is stocked and cheap). Sizing verified 2026-07-14; the 60 °C derating note and RISET=120 k fallback stand. |

### 11. Architecture — would 1S have been more common/simpler? (ANALYSIS ONLY — no change)

**Yes, 1S is the more common architecture — and 2S remains the right call for this
device. Recorded honestly for future revisions:**

The canonical hobby solar-ESP32 stack is **1S 18650 + TP4056/TC4056 (USB) + CN3791
module (solar MPPT) + HT7333/ME6211 LDO or small buck** — all SOP/SOT jellybean parts,
all sub-$0.10, all with millions of shipped design-ins and infinite community
documentation. Against WellD's actual USB+solar+buck section it would delete the
IP2326 (QFN), the CN3722 external buck stage (~14 parts), and the AP63203 buck, and
sidestep the pack-PCM co-charge question entirely. That is a real simplicity and
commonality win, and it should be the default starting point for any future
lower-spec variant.

Why 2S still wins *here*:
1. **The 12 V loop rail is the design driver.** From 1S (2.8–4.2 V) the VLOOP boost
   runs a 3–4.3× ratio at ~4× the input current (~180 mA peak input during reads at
   battery-empty), with worse transient sag into C20/C22 inrush; from 2S it is a
   lazy 1.4–2× ratio. Loop compliance margin at cold/low-battery corners is the one
   thing this instrument must never lose.
2. **Solar path efficiency and panel standard.** A "12 V" (17–18 V V_MP) panel into a
   2S pack is a clean ~2:1 buck (CN3722's native regime). Into 1S it is ~4.3:1 —
   CN3791 modules do it, but at meaningfully worse conversion efficiency and higher
   buck peak currents for the same watts.
3. **Energy per cell count:** 2S1P doubles pack voltage, halving currents everywhere
   (charge path, buck input, XT30 contacts) for the same power — every copper and
   connector margin relaxes.
4. The 1S stack's LDO habit (HT7333) would burn dropout margin exactly at the
   3.0–3.4 V end of discharge where the ESP32-C6's TX bursts brown out — the common
   architecture is common partly because most of its users tolerate flakiness at
   end-of-charge that a winter-unattended well monitor cannot.

Trade-off honestly stated: WellD pays for headroom with a QFN charger, a 16-pin MPPT
controller + FET stage, a mandatory pack-PCM question (blocker #7a), and 2S-specific
risks (no balancing with a 2-pin pack — mitigated by the pack's internal PCM and the
IP2326's floating VBATM). A future rev that drops the 4–20 mA loop (e.g. an I²C/RS-485
sensor) loses reason #1 and should re-open the 1S question first thing.

---

## Verdict summary

| # | Position | Current part | Verdict | Best common alternative |
|---|----------|--------------|---------|-------------------------|
| 1 | U12 | IP2326 QFN-24 | **KEEP** | CS5095E (SOP-8, under-documented — not better) |
| 2 | U7 | CN3722 TSSOP-16 | **KEEP** | BQ24650 (commercial standard; future ≥2 A rev only). CN3791 disqualified: 1S-only |
| 3 | U1 | AP63203WU | **KEEP** (sweet spot) | TPS62902 (lower Iq, worse package/stock) |
| 4 | U8 | MT3608B + Q3/Q4 disconnect | **KEEP** | none at VIN > 6 V with true disconnect |
| 5 | U9 | ADS1115 + 100 Ω shunts | **KEEP** (community-standard 4–20 mA receiver) | INA226 (elegant, loses on channels/robustness/rewrite) |
| 6 | Q2/Q4 | BSS123 | **SWAP RECOMMENDED** | **AO3400A** (C20917); 2N7002 second source |
| 7 | D5/Q3/Q5 | AO3407 | **KEEP** (AO3401A approved alternate) | — |
| 7b | M_SOLAR | AO3407 | **OPTIONAL** | **SI2319CDS** −40 V (C146287) |
| 8 | TVS | SMAJ family | **KEEP** | — |
| 8b | Loop surge | (2-stage only) | **OPTIONAL** | + GDT footprints, DNF (industrial 3-stage norm) |
| 9 | U11 | USBLC6-2SC6 | **KEEP** | — |
| 9b | D1/D12 | PRTR5V0U2X | **KEEP** | BAV199 (multi-vendor functional alternate) |
| 10a | DS18B20 | field probe | note only | genuine-silicon procurement rule stands |
| 10b | J13 | GCT USB4135-GF-A | **SWAP RECOMMENDED** | **HRO TYPE-C-31-M-12** (C165948) |
| 10c | J1 | XT30PW-F | **KEEP** | — |
| 10d | F2 | MF-MSMF250/16X-2 | **KEEP** | — |
| 11 | Architecture | 2S | **KEEP** (analysis only) | 1S TP4056+CN3791 stack — more common; re-open only if the 12 V loop requirement ever falls |

## Sources

- IP2326 module ecosystem & docs: [done.land IP2326](https://done.land/components/power/powersupplies/battery/chargers/charge/powermanagementics/ip2326/), [datasheet mirror](https://done.land/assets/files/ip2326_datasheet.pdf), [LCSC C2832094](https://www.lcsc.com/product-detail/C2832094.html), [Aaenics module](https://store.aaenics.com/product/ip2326-lithium-battery-fast-charging-module-2s-3s-15w/), [Masterlexon module](https://masterlexon.com/en/2s-li-ion-battery-charging-module-with-balancing-ip2326)
- CN3791 1S-only / CN3722 multi-cell: [jrattechworks CN3791 guide](https://jrattechworks.com/cn3791-mppt-solar-charger/), [ICStation CN3722 module](https://www.icstation.com/series-lithium-battery-charger-mppt-controller-cn3722-solar-panel-p-15810.html)
- BQ24650 commonality: [TI product page](https://www.ti.com/product/BQ24650), [Beyondlogic review ("commonplace on AliExpress/eBay/Amazon")](https://www.beyondlogic.org/review-bq24650-5a-mppt-solar-controller-3s-4s-li-ion-lifepo4-12v-lead-acid/), [Hackaday Open MPPT](https://hackaday.io/project/25530-open-mppt), [CircuitMaker open design](https://circuitmaker.com/Projects/Details/Craig-Peacock-4/BQ24650-MPPT-3S-4S-Li-Ion-LiFePO4-Lead-Acid-Battery-Charger)
- AP63203 design-in: [SparkFun AP63203 breakout](https://www.sparkfun.com/sparkfun-buck-regulator-breakout-3-3v-ap63203.html), [Diodes AP63203](https://www.diodes.com/part/view/AP63203), [LCSC C780769](https://www.lcsc.com/product-detail/C780769.html)
- ADS1115-as-loop-receiver product norm: [NCD 2-ch](https://store.ncd.io/product/2-channel-4-20-ma-current-loop-receiver-16-bit-ads1115-i2c-mini-module/) / [4-ch 4-20 mA ADS1115 receivers](https://store.ncd.io/product/4-channel-4-20-ma-current-loop-receiver-16-bit-ads1115-i2c-mini-module/); INA226: [TI INA226](https://www.ti.com/product/INA226), [ComponentIndex guide](https://componentindex.net/components/ina226/)
- N-FET comparison: [components101 BSS123 (price/margin note)](https://components101.com/mosfets/bss123-mosfet-pinout-datasheet-equivalent), [BSS138 vs 2N7002 3.3 V consensus](https://www.aliexpress.com/s/wiki-ssr/article/bss138-vs-2n7002)
- P-FETs: [AO3401A LCSC C15127 (1.8M stock)](https://www.lcsc.com/product-detail/C15127.html), [SI2319CDS Vishay C146287](https://lcsc.com/product-detail/MOSFETs_Vishay-Intertech-SI2319CDS-T1-GE3_C146287.html), [VBsemi C558254](https://www.lcsc.com/product-detail/C558254.html)
- GDT 3-stage norm: [passive-components.eu GDT design-in](https://passive-components.eu/gdt-gas-discharge-tubes-surge-protection-fundamentals-selection-and-design-in-tips/), [Littelfuse GDT](https://www.littelfuse.com/products/overvoltage-protection/gas-discharge-tubes/low-to-medium-surge), [CITEL RS-485 gas tubes](https://citel.us/en/gas-tube-surge-arrestors-for-rs-485)
- ESD/clamp: [Nexperia PRTR5V0U2X](https://www.nexperia.com/product/PRTR5V0U2X), [Nexperia BAV199 (3 pA)](https://assets.nexperia.com/documents/data-sheet/BAV199.pdf), [Diodes BAV199](https://www.diodes.com/datasheet/download/BAV199.pdf), [MCC BAV199](https://www.mccsemi.com/pdf/Products/BAV199(SOT-23).pdf)
- USB-C: [TYPE-C-31-M-12 LCSC C165948](https://www.lcsc.com/product-detail/C165948.html), [pcbwiki design guide](https://pcbwiki.com/parts/type-c-31-m-12), [DigiKey forum alternates thread](https://forum.digikey.com/t/type-c-31-m-12-alternative/66351)
