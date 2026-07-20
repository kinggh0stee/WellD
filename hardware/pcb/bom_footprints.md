# WellD PCB — BOM with KiCad 10 Footprints

**Board:** size unconstrained — drawn around the finished placement (working target ≈100 × 60 mm with the top-side 18650 carrier); 2-layer, 1.6 mm FR4, 1 oz Cu  
**Assembler:** PCBWay PCBA  
**Sourcing key:** ✅ LCSC (direct PCBWay) · ⚠️ PCBWay global sourcing · 📦 Customer-supply to PCBWay

> **2026-07-05 electrical review:** several parts changed (U1, D8/D14, C8, C17, LED GPIO) and new components were added (D15, Q3–Q5, R15/R16/R25/R27/R29, C36, TP13). See `schematic_connections.md` → "Design changes" and "Datasheet verification blockers" before ordering.
>
> **2026-07-05 component-selection review** *(superseded by the 1S conversion — see the 2026-07-19 note below)* (`component_selection_review.md`): the non-functional TP5100 USB charge path is **replaced by an Injoinic IP2326 5 V→2S synchronous boost charger** (U12; +L3, R35 repurposed as ISET, R36/R37 deleted, F2 uprated to 2 A hold). Do not order the USB-charger section until verification blocker #2 (IP2326 datasheet items) is resolved — the mid-cell/balance-pin question could still reopen the choice.
>
> **2026-07-13 reconciliation pass:** all rows below now have matching schematic symbols (senior review 2026-07-06 CRITICAL 1–3 cleared). **CN3722 CRITICAL CV fix**: R33 590k→243k, R20 36k→158k, R19 repurposed as R_CS 0.4 Ω, U7 redrawn TSSOP-16 with its external buck stage (see the solar section). The IP2326 mid-cell question is resolved (VBATM/VBAT_GND float).
>
> **2026-07-19 — 1S CONVERSION (design change #18):** the pack is now **1S2P** (VBAT 3.0–4.2 V). U12 IP2326 → **TP4056** (L3/R_VSET/C_BST2/C_SYS1/C_SYS2/R35 deleted; R_PROG/R_NTC added); U7 CN3722 + external buck → **CN3791** (M_SOLAR/D16/C_COM1-3/R_COM2/R33/R34 deleted; D_SOLAR/L_SOLAR/C_VG/RT_SOLAR/R19 kept); U1 AP63203WU → **HT7333-A** (L2/C_BST_AP/R_FBH/R_FBL/R11 deleted); D13 → SMAJ5.0A, D8/D14 → SMAJ10CA; R7 → 100 k (÷2 divider). Verification status: see 1S blocker #10 in `schematic_connections.md`. Historical 2S rows below are marked rather than erased.

> **2026-07-14 full component verification sweep** (`component_verification_2026-07-14.md`): IP2326 package = **QFN24 4×4 mm** ✅, F2 = **MF-MSMF250/16X-2** ✅, NTCs = **SDNT1608X103F3950FTF** ✅, L_SOLAR **verified** ✅, L3 MPN picked ✅. Wrong LCSC numbers fixed (D1/D12, U6, U7); **D9/D10 changed SMAJ3.3CA → SMAJ5.0A** (leakage fail); **U1 needs a BST–SW 100 nF cap (C_BST_AP, new row) and its symbol renumbered** — see blocker #9 in `schematic_connections.md` for the required schematic edits. Remaining order blocker: pack PCM charge rating (#7a).

---

## Power — Battery Input

| Ref | Value | Package | KiCad 10 Footprint | MPN | LCSC | Notes |
|-----|-------|---------|-------------------|-----|------|-------|
| BT1 | **18650 battery carrier** (replaced J1 XT30, 2026-07-19) | THT clip pair (recommended) or SMD holder | `WellD:BH-18650_THT` (custom — draw from the chosen part's LCSC drawing at order time) | **Recommended: MYOUNG MY-18650-02 clip ×2 (THT, strongest retention)**; alt: MYOUNG BH-18650-B1BA002 one-piece holder (SMD); alt: Keystone 1042/1042P | MY-18650-02 = **C2979182**; BH-18650-B1BA002 = **C2988620** (both in stock, found 2026-07-19) | Pin 1=cell+, Pin 2=cell− (→ BATT_N, through protection). Single generic 18650, ≈3–3.4 Ah |
| **U13** | **DW01A-G 1S protection supervisor** | SOT-23-6 | `Package_TO_SOT_SMD:SOT-23-6` | DW01A (Fortune / PUOLOP et al.) | **C351410** (PUOLOP) or equivalent ✅ candidates found | **✅ verified 2026-07-19** (blocker #11a): OD=1/CS=2/OC=3/TD=4/VCC=5/GND=6; trip 2.40 V (release 3.0) / 4.30 V (release 4.1); 100Ω+100nF+1kΩ = datasheet typical app |
| **Q6** | **FS8205A dual N-FET** | TSSOP-8 | `Package_SO:TSSOP-8_4.4x3mm_P0.65mm` | FS8205A (Fortune) | **C14212** (Fortune) / C908265 (clone) ✅ candidates found | **✅ verified + symbol corrected 2026-07-19** (blocker #11b): D=1&8 (internally common), S1=2&3, G1=4, G2=5, S2=6&7; 20 V, ~6 A |
| **R_DW1** | 100Ω | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | **NEW** — DW01A VCC filter (with C_DW) |
| **C_DW** | 100nF | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | **NEW** — DW01A VCC filter (to cell−/BATT_N) |
| **R_CS_DW** | 1kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | **NEW** — DW01A CS series resistor to system GND |
| D5 | AO3407 P-ch MOSFET | SOT-23 | `Package_TO_SOT_SMD:SOT-23` | AO3407 | C31417 ✅ | Reverse-polarity protection |
| R31 | 10kΩ 1% | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | C25741 ✅ | D5 gate pull-down to GND (holds load switch ON) |
| D13 | **SMAJ5.0A TVS 5V uni** | DO-214AC | `Diode_SMD:D_SMA` | SMAJ5.0A | **C98802** ✅ (same reel as D9/D10) | Battery terminal TVS, **re-rated 2026-07-19** (1S): 5 V standoff clears the 4.2 V full charge; unidirectional — the forward diode clamps negative transients (reverse-battery is D5's job) |

---

## Power — USB-C Charging (TP4056 linear path — 1S conversion 2026-07-19; was IP2326 boost, was TP5100)

> **1S lineage:** TP5100 (couldn't boost 5 V→8.4 V) → IP2326 2S boost (2026-07-05) → **TP4056 1 A linear** (2026-07-19, 1S conversion — a 1S pack charges directly from 5 V USB; the entire boost stage is unnecessary). Open items: 1S blocker #10a in `schematic_connections.md` (pinout confirm, TEMP window math, thermal derating decision).

| Ref | Value | Package | KiCad 10 Footprint | MPN | LCSC | Notes |
|-----|-------|---------|-------------------|-----|------|-------|
| J13 | USB-C 2.0 power-only | 16-pin SMD + 4 THT shell legs | `Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12` ⚠️ verify exact footprint name in installed KiCad 10 lib before layout | **HRO TYPE-C-31-M-12** | **C165948** ✅ (order the Korean Hroparts listing specifically — part is endlessly cloned) | **SWAPPED 2026-07-19** (alternatives review P-2): was GCT USB4135-GF-A (~$1+, global sourcing) — GCT demoted to approved alternate (needs its own land pattern back). 16-pin USB-2.0 subset; symbol pins A1/A4/A5/A6/A7/B5 unchanged. ⚠️ Layout note: B-side mirror pins (B1/B4/B6/B7/B9/B12 etc.) tie to the same nets inside the footprint (GND/VBUS/D±) — check pad-to-net map when the footprint lands |
| U11 | USBLC6-2SC6 ESD | SOT-23-6 | `Package_TO_SOT_SMD:SOT-23-6` | USBLC6-2SC6 | C7519 ✅ | VBUS + D+/D− clamp. Pinout verified 2026-07-14: 1=I/O1, 2=GND, 3=I/O2, 4=I/O2, 5=VBUS, 6=I/O1 — **welld symbol must be renumbered** (blocker #9) |
| F2 | **MF-MSMF250/16X-2 PTC 2.5A hold** | **1812** | `Fuse:Fuse_1812_4532Metric` | MF-MSMF250/16X-2 | C210838 ✅ | **Resolved 2026-07-14** (blocker #8): 2.5 A hold / 5.0 A trip / 16 V / 100 A max / 15 mΩ, −40…+85 °C. Series with J13 VBUS; TP4056 draws ≈1 A charge (linear — no boost input multiplication), comfortable inside the derated 1.75–2 A hold at 60 °C. Schematic footprint field fixed 1206 → 1812 (2026-07-19) |
| U12 | **TP4056 1S linear charger 1A** | **SOP-8 + EPAD** | `Package_SO:SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.29x2.29mm` (KiCad standard) | TP4056-42-ESOP8 (TopPower/NanJing) | **C16581** ✅ (found 2026-07-19 — the ESOP-8/EPAD variant) | **1S CONVERSION 2026-07-19** (replaced IP2326): 5 V VBUS → 4.2 V CC/CV linear, 1 A (R_PROG 1.2 k). CE (8) strapped to VUSB = auto-charge; /CHRG (7) open-drain → R38/TP15; /STDBY (6) NC. **EPAD GND pour required** (≈1.3 W at mid-charge; thermal regulation folds back at ≈120 °C die — drop R_PROG to 2.4 k → 0.5 A if the enclosure runs hot). Pinout confirm = 1S blocker #10a |
| **R_PROG** | **1.2kΩ 1%** | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | **NEW 2026-07-19** — TP4056 PROG (2) → GND; I_CH = 1200 V/R_PROG = **1 A** |
| **R_NTC** | **5.6kΩ 1%** | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | **NEW 2026-07-19** — TEMP-node divider top (VUSB → TEMP); with RT1 10 k B3950 → ✅ **computed** charge window **+8…+44 °C** |
| ~~L3, R35, R_VSET, C_BST2, C_SYS1, C_SYS2~~ | — | — | — | — | — | **DELETED 2026-07-19** — IP2326 boost support parts, gone with the 1S conversion |
| ~~R36~~ | — | — | — | — | — | **DELETED 2026-07-05** — TP5100 CE pull-up (historical) |
| ~~R37~~ | — | — | — | — | — | **DELETED 2026-07-05** — TP5100 CE pull-down; **GPIO4 spare** (TP4056 CE is strapped high in hardware — 2026-07-19) |
| R38 | 4.7kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | /CHRG_USB pull-up to +3V3 (routes to TP15 only). TP4056 /CHRG (7) is open-drain per datasheet — fit unconditionally |
| RT1 | **10kΩ NTC B3950 1%** | 0603 | `Resistor_SMD:R_0603_1608Metric` | **SDNT1608X103F3950FTF** (Sunlord) ✅ | — ✅ look up C# (3450 sibling is C95953) | TP4056 TEMP (1) low side (R_NTC 5.6 k top), thermally coupled to the pack — charge-temperature cutoff (`component_selection_review.md` O-1). MPN picked 2026-07-14. ✅ window math computed +8…+44 °C (1S blocker #10a resolved) |
| R50 | 5.1kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | J13 CC1 → GND (was "R_CC1") |
| R51 | 5.1kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | J13 CC2 → GND (was "R_CC2") |
| C27 | 4.7µF 10V X5R | 0805 | `Capacitor_SMD:C_0805_2012Metric` | — | ✅ | VUSB input filter after F2 |
| C28 | 10µF **25V** X5R | 0805 | `Capacitor_SMD:C_0805_2012Metric` | — | ✅ | U12 TP4056 VCC (4) bypass (10 µF per every TP4056 reference design; 25 V rating kept from the IP2326 era — harmless margin) |
| C29 | 10µF **25V** X5R | 0805 | `Capacitor_SMD:C_0805_2012Metric` | — | ✅ | U12 BAT-side bypass. Value ✅ confirmed 2026-07-14 (DS ref design: 10 µF + 22 µF at VOUT — 10 µF suffices at 1 A with the pack on the node); **uprated 16 V → 25 V** per DS |

---

## Power — Solar MPPT Charging (CN3791 path — 1S conversion 2026-07-19; was CN3722 + external buck)

> **2026-07-19 (1S conversion):** the CN3722 2S controller and its external buck stage are **deleted** — the CN3791 is the 1S sibling with an **integrated switch** and a **fixed 4.2 V CV at the BAT pin** (no CV divider at all), MPPT reference **1.205 V**. Kept from the old stage: D_SOLAR, L_SOLAR, C_VG, RT_SOLAR, R19 (now 0.1 Ω). Open verifications: 1S blocker #10b in `schematic_connections.md` (the Consonance CN3791 datasheet was not fetchable at conversion time — pinout, VG cap, sense formula, VIN range, TEMP thresholds all flagged). Historical CN3722 CV-reference saga: `component_verification_2026-07-14.md` and design changes #13–#15.

| Ref | Value | Package | KiCad 10 Footprint | MPN | LCSC | Notes |
|-----|-------|---------|-------------------|-----|------|-------|
| U7 | **CN3791 1S MPPT buck charge CONTROLLER** | **SSOP-10** | `Package_SO:SSOP-10_3.9x4.9mm_P1.00mm` | CN3791 | C124423 ⚠️ verify listing | **✅ datasheet-verified 2026-07-19** (blocker #10b, with corrections): external-P-FET controller (DRV pin, 8 V gate clamp), fixed 4.2 V ±1 % CV, MPPT ref 1.205 V ✅, VCC 4.5–28 V, I_CH = 120 mV/R_CS ✅ → **1.2 A** at R19 = 0.1 Ω, 300 kHz, BAT+CSP sleep ≈9 µA @ 4.2 V. **No TEMP pin** (→ blocker #10f) |
| **M_SOLAR** | **SI2319CDS P-ch MOSFET −40 V** | SOT-23 | `Package_TO_SOT_SMD:SOT-23` | SI2319CDS-T1-GE3 (Vishay) | **C146287** ✅ (clone alt C558254) | **RESTORED 2026-07-19** — the CN3791 is a controller; external buck P-FET is required after all (same part the alternatives review picked for the CN3722 stage) |
| **D16** | **SS34 Schottky 3A 40V** | DO-214AC | `Diode_SMD:D_SMA` | SS34 | C8678 ✅ | **RESTORED 2026-07-19** — series diode after M_SOLAR: blocks night back-feed VBAT→L_SOLAR→FET body diode→MPPT divider/VCC |
| **R_DRV** | 300kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | **NEW 2026-07-19** — M_SOLAR gate–source pull-off (per the Soldered Electronics CN3791 reference design) |
| **C_COM** | 220nF | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | **NEW 2026-07-19** — CN3791 COM (5) compensation, series with R_COM (datasheet-required) |
| **R_COM** | 120Ω | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | **NEW 2026-07-19** — COM network low side to GND |
| **U14** | **LM393 dual comparator** | SOIC-8 | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` | LM393DR (TI/onsemi/second sources) | LCSC TBD ⚠️ (ubiquitous — e.g. C7955-class, pick at order) | **NEW 2026-07-19** — solar cold-charge cutoff (#10f resolved): powered from VSOLAR (zero night draw), ratiometric NTC threshold, clamps CN3791 MPPT via Q7 when < ≈+2 °C |
| RT_SOLAR | **10kΩ NTC B3950 1%** | 0603 | `Resistor_SMD:R_0603_1608Metric` | **SDNT1608X103F3950FTF** (Sunlord) ✅ | — ✅ (same reel as RT1) | **REVIVED 2026-07-19** for the LM393 cutoff (was deleted when the CN3791 turned out to have no TEMP pin) — thermally couple to the **cell** |
| **R_NT1** | **30kΩ 1%** | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | **NEW** — cutoff temp divider top; 30 k ≈ NTC B3950 at +2 °C → trip threshold |
| **R_NT2, R_NT3** | **100kΩ 1% ×2** | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | **NEW** — cutoff reference divider (0.5·VSOLAR, ratiometric) |
| **R_PU** | 100kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | **NEW** — LM393 OUT1 pull-up to VSOLAR |
| **R_HYS** | 330kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | **NEW** — hysteresis (≈2 °C: trip +2 °C falling, release ≈+4 °C) |
| **C_NTC** | 100nF | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | **NEW** — U14 supply bypass |
| **Q7** | **AO3400A N-FET** | SOT-23 | `Package_TO_SOT_SMD:SOT-23` | AO3400A | **C20917** ✅ (same reel as Q2/Q4) | **NEW** — MPPT clamp switch (small-signal; Vgs ≈ VSOLAR ≤10 V vs ±12 V abs max — OK for ≤6 V-nominal panels) |
| D6 | MBRS140 Schottky 1A 40V | SMB | `Diode_SMD:D_SMB` | MBRS140T3G | — ✅ | Solar backfeed block (MBRS140T3G is SMB, not SOD-123) |
| D8 | **SMAJ10CA TVS 10V bidi** | DO-214AC | `Diode_SMD:D_SMA` | SMAJ10CA | C2836474 ⚠️ (unconfirmed listing — verify at order time; Littelfuse/MDD SMAJ10CA variants stocked) | **Re-rated 2026-07-19** (1S conversion): at CN3791 VIN; same reel as D14. Panel is now 6 V-nominal → Voc limit **10 V** (was SMAJ24CA / 24 V for the 12 V-panel 2S design) |
| ~~M_SOLAR, D16, C_COM1, C_COM2, C_COM3, R_COM2, R33, R34~~ | — | — | — | — | — | **DELETED 2026-07-19** (1S conversion) — the CN3791's integrated switch needs no external P-FET/series diode/compensation, and its fixed 4.2 V CV needs no divider. (M_SOLAR had been swapped to SI2319CDS earlier the same day — the swap died young; C146287 is simply not ordered) |
| **D_SOLAR** | **SS34 Schottky 3A 40V** | DO-214AC | `Diode_SMD:D_SMA` | SS34 | C8678 ✅ | Catch/freewheel diode (GND → SOLAR_SW), kept for the CN3791 stage — sanity-check against the CN3791 typical application (1S blocker #10b) |
| **L_SOLAR** | **22µH shielded** | 6×6×4.5mm SMD (same footprint) | `Inductor_SMD:L_Bourns-SRN6045TA` | **SRN6045TA-220M** | — ✅ (Isat 3.3 A) | **Resized 2026-07-19** (was 47µH SRN6045TA-470M, Isat 1.3 A ≈ 5 % margin). Computed peak ≈1.24 A; the 220M gives **Isat 3.3 A / Irms 2.3 A / DCR 96 mΩ**, 1.7× margin. Same 6045 footprint — no redraw. Ripple 182 mApp at 300 kHz, trivial |
| **R19** | **0.1Ω 1% (R_CS)** | **1206** | `Resistor_SMD:R_1206_3216Metric` | — | ✅ | **Re-valued 2026-07-19**: CSP–BAT sense; assumed I_CH = 120 mV/R_CS = **1.2 A**; P ≈ 0.14 W. ⚠️ Formula verify = 1S blocker #10b |
| R20 | **316kΩ 1% E96** | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | **Re-valued 2026-07-19**: MPPT divider high-side → V_MP = 1.205×(1+316/100) ≈ **5.01 V** (6 V-nominal panel). ⚠️ Recompute for the actual panel |
| R21 | **100kΩ 1%** | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | MPPT divider low-side (MPPT pin→GND); re-valued 10 k → 100 k 2026-07-19 (divider impedance scaled with R20) |
| **C_VG** | **100nF 50V** | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | **NEW 2026-07-13** — VG (1) ↔ **VCC** (not GND) per datasheet |
| **C_COM1** | **470pF 50V** | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | **NEW 2026-07-13** — COM1 (8) → GND |
| **C_COM2** | **220nF 25V** | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | **NEW 2026-07-13** — COM2 (9) → C_COM2 → R_COM2 → GND |
| **R_COM2** | **120Ω 5%** | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | **NEW 2026-07-13** — series with C_COM2 |
| **C_COM3** | **100nF 25V** | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | **NEW 2026-07-13** — COM3 (11) → GND |
| **RT_SOLAR** | **10kΩ NTC B3950 1%** | 0603 | `Resistor_SMD:R_0603_1608Metric` | **SDNT1608X103F3950FTF** (Sunlord) ✅ | — ✅ look up C# | **NEW 2026-07-13** — TEMP (6) → GND, thermally coupled to the pack: charge suspended below ≈+2°C / above ≈+54°C (55µA pull-up, 1.61V/0.175V thresholds). Solar-path cold-charge cutoff (review O-1). Same reel as RT1 (MPN picked 2026-07-14) |
| C17 | 10µF **35V** X5R | **1206** | `Capacitor_SMD:C_1206_3216Metric` | — | ✅ | CN3791 VIN filter (35 V rating generous now that the rail clamps at 10 V — keep, zero-cost margin) |
| C18 | 10µF 16V | 0805 | `Capacitor_SMD:C_0805_2012Metric` | — | ✅ | CN3791 BAT filter |
| C21 | 100nF **50V** | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | HF bypass at CN3791 VIN (across D8) |
| R25 | 4.7kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | **NEW** — /CHRG_SOLAR pull-up to +3V3 (GPIO6; was internal pull-up only) |
| D7 | Green LED | 0603 | `LED_SMD:LED_0603_1608Metric` | — | ✅ | Solar-charging indicator: +3V3→R22→D7→/CHRG_SOLAR |
| R22 | 1kΩ **DNF** | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | D7 series resistor — DNF by default (fit for bench debug) |

---

## Power — 3.3 V LDO (HT7333-A — 1S conversion 2026-07-19; was AP63203 buck)

| Ref | Value | Package | KiCad 10 Footprint | MPN | LCSC | Notes |
|-----|-------|---------|-------------------|-----|------|-------|
| U1 | **HT7333-A LDO 3.3V 250mA** | SOT-23 | `Package_TO_SOT_SMD:SOT-23` | HT7333-A (Holtek) | **C21583** ✅ (confirmed 2026-07-19) | **✅ pinout verified 2026-07-19** (blocker #10d): GND=1, VOUT=2, VIN=3 (same as XC6206). 3.5–4 µA Iq, dropout ≈60 mV @ 100 mA, VIN 2–12 V. 250 mA ceiling fine for Zigbee-only (TX ≈ 80 mA); **Wi-Fi must stay disabled** |
| ~~C_BST_AP, L2, R_FBH, R_FBL, R11~~ | — | — | — | — | — | **DELETED 2026-07-19** — AP63203 support parts (bootstrap cap, inductor, DNP divider, EN pull-up); an LDO needs none of them |
| C16 | 10µF 16V X5R | 0805 | `Capacitor_SMD:C_0805_2012Metric` | — | ✅ | U1 VIN bulk (AP6320x datasheet CIN = 10µF; was an orphan symbol, now assigned) |
| C9 | 100nF 16V | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | VIN bypass |
| C10 | 1µF 16V | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | VIN bulk |
| C11 | 100nF | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | VOUT bypass |
| C12 | 1µF | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | VOUT bulk |
| C_BUCK | 10µF 10V X5R | 0805 | `Capacitor_SMD:C_0805_2012Metric` | — | ✅ | Primary output filter cap at U1 VOUT (ref kept from the buck era) |

---

## Power — 12V VLOOP Boost (MT3608B)

| Ref | Value | Package | KiCad 10 Footprint | MPN | LCSC | Notes |
|-----|-------|---------|-------------------|-----|------|-------|
| U8 | MT3608B boost 12V | SOT-23-6 | `Package_TO_SOT_SMD:SOT-23-6` | MT3608B | C84005 ✅ | GPIO5-gated, EN=HIGH during 4-20mA reads. Pin map **datasheet-confirmed 2026-07-14** (SW=1, GND=2, FB=3, EN=4, IN=5, NC=6 — KiCad official `MT3608` symbol agrees with both prior reviews); routine first-article check only |
| L1 | 4.7µH 1A shielded | 4×4mm SMD | `Inductor_SMD:L_4.0x4.0mm_H2.6mm` ⚠️verify name | CDRH4D22NP-4R7NC | C376098 ✅ | MT3608B boost inductor (was "same part as L2" — L2 deleted 2026-07-19) |
| R23 | 1.91MΩ 1% E96 | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | VOUT divider high-side → VOUT=0.6×(1+1910/100)=12.06V (matches schematic value) |
| R24 | 100kΩ 1% | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | VOUT divider low-side |
| C_BST | 100nF 16V | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | C14663 ✅ | Pin 6 ↔ SW. Pin 6 = NC **confirmed 2026-07-14** (KiCad official symbol) — cap is harmless; can be marked **DNF** at first article |
| **D15** | **SS34 Schottky 3A 40V** | DO-214AC | `Diode_SMD:D_SMA` | SS34 | C8678 ✅ | **NEW** — boost rectifier SW→VLOOP (MT3608 is an async boost; there was no rectifier in the BOM) |
| **Q3** | **AO3407 P-ch MOSFET** | SOT-23 | `Package_TO_SOT_SMD:SOT-23` | AO3407 | C31417 ✅ | **NEW** — VLOOP input disconnect (VBAT→Q3→L1); kills the permanent VBAT−0.4V leak through L1+D15 to the loop terminals during sleep |
| **Q4** | **AO3400A N-ch MOSFET** | SOT-23 | `Package_TO_SOT_SMD:SOT-23` | **AO3400A** (AOS) | **C20917** ✅ | Q3 gate driver, gate on VBOOST_EN (GPIO5). **SWAPPED 2026-07-19 from BSS123** (alternatives review P-1, settles O-3): Vgs(th) max 1.45 V vs 1.7 V — fully enhanced at 3.3 V drive; 2N7002 approved emergency second source (thinner 2.5 V-max threshold margin, fine at these µA loads) |
| **R29** | **100kΩ** | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | **NEW** — Q3 gate pull-up to VBAT (off by default) |
| **R27** | **100kΩ** | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | **NEW** — VBOOST_EN pull-down (GPIO5 floats in deep sleep) |
| C19 | 10µF 16V | 0805 | `Capacitor_SMD:C_0805_2012Metric` | — | ✅ | VIN bypass |
| C20 | 22µF 25V X5R | 1206 | `Capacitor_SMD:C_1206_3216Metric` | — | ✅ | VOUT filter |
| C22 | 10µF 25V X5R | 0805 | `Capacitor_SMD:C_0805_2012Metric` | — | ✅ | VOUT parallel with C20 |
| D11 | SMAJ13A TVS 13V uni | DO-214AC | `Diode_SMD:D_SMA` | SMAJ13A | C8057 ⚠️ | VLOOP terminal clamp. ⚠️ C8057 could not be confirmed as SMAJ13A (2026-07-14) — known-good alternate: **C110519** (SMAJ13A-13-F, Diodes Inc) |
| SJ1 | Solder jumper NO | — | `Jumper:SolderJumper-2_P1.3mm_Open_TrianglePad1.0x1.5mm` | — | — | MT3608B EN permanent tie, DNF |
| SJ2 | Solder jumper NC | — | `Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm` | — | — | J4/J5 VLOOP bus share |

---

## Battery Divider

| Ref | Value | Package | KiCad 10 Footprint | MPN | LCSC | Notes |
|-----|-------|---------|-------------------|-----|------|-------|
| Q2 | **AO3400A N-ch MOSFET** | SOT-23 | `Package_TO_SOT_SMD:SOT-23` | **AO3400A** (AOS) | **C20917** ✅ | Gate=GPIO15; drives Q5's gate (level shifter). **SWAPPED 2026-07-19 from BSS123** (alternatives review P-1) — see Q4; 2N7002 approved second source |
| **Q5** | **AO3407 P-ch MOSFET** | SOT-23 | `Package_TO_SOT_SMD:SOT-23` | AO3407 | C31417 ✅ | **NEW** — high-side divider disconnect (old low-side switch leaked ~14µA into ADS1115 AIN2 during sleep) |
| **R16** | **100kΩ** | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | **NEW** — Q5 gate pull-up to VBAT |
| R7 | **100kΩ 1%** | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | Divider high-side (VBAT→midpoint). **Re-valued 2026-07-19** (1S): ÷2 with R8 → 2.1 V max at AIN2 (firmware ratio 430 → 200; AIN2 read must move to the ±4.096 V PGA — 1S blocker #10c) |
| R8 | 100kΩ 1% | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | Divider low-side (midpoint→GND, direct) |
| R26 | 4.7kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | Q2 gate pull-down |
| C8 | **1nF** X7R | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | Across R8. Was 100nF → τ≈7.7ms, too slow for the firmware's ≥1ms enable window; 1nF settles in <1ms |

---

## MCU — ESP32-C6

| Ref | Value | Package | KiCad 10 Footprint | MPN | LCSC | Notes |
|-----|-------|---------|-------------------|-----|------|-------|
| U6 | ESP32-C6-MINI-1U-H4 | Module | `RF_Module:ESP32-C6-MINI-1` 📦 or Espressif KiCad lib | ESP32-C6-MINI-1U-H4 | **C20627095** ✅ (**corrected 2026-07-14** — old C2913202 does not match; ~$3.16, in stock) | Download Espressif KiCad libraries from github.com/espressif/kicad-libraries |
| C13, C30–C33 | 100nF ×5 | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | VCC3V3 decoupling, within 2mm of module pads (schematic refs; were documented as "C14a–C14d") |
| **R15** | **10kΩ** | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | **NEW** — ESP32 EN pull-up to +3V3 |
| **C36** | **1µF** | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | **NEW** — ESP32 EN→GND reset-delay cap (10ms RC with R15) |
| C15 | 10µF 10V | 0805 | `Capacitor_SMD:C_0805_2012Metric` | — | ✅ | VCC3V3 bulk |
| R12 | 10kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | GPIO9 BOOT pull-up |
| R13 | 10kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | GPIO8 strapping pull-up |
| SW1 | Reset tactile 6×6mm | SMD | `Button_Switch_SMD:SW_Push_6mm_H4.3mm` | — | ✅ | Pulls ESP32 EN to GND |
| SW2 | Boot tactile 6×6mm | SMD | `Button_Switch_SMD:SW_Push_6mm_H4.3mm` | — | ✅ | Pulls GPIO9 to GND |
| D4 | Status LED green | 0603 | `LED_SMD:LED_0603_1608Metric` | — | ✅ | **GPIO14** → R14 → D4 → SJ3 → GND (moved off GPIO13: a green LED + 1k to GND held the factory-reset strap below V_IH → NVS wipe every boot) |
| R14 | 1.0kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | LED current limit |
| SJ3 | Solder jumper NC | — | `Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm` | — | — | LED disconnect to save current |

---

## ADC — ADS1115

| Ref | Value | Package | KiCad 10 Footprint | MPN | LCSC | Notes |
|-----|-------|---------|-------------------|-----|------|-------|
| U9 | ADS1115IDGST 16-bit I²C | MSOP-10 | `Package_SO:MSOP-10_3x3mm_P0.5mm` | ADS1115IDGST | C37593 ✅ | Addr 0x48 (ADDR→GND) |
| FB1 | 600Ω@100MHz ferrite | **0603** | `Inductor_SMD:L_0603_1608Metric` | BLM18KG601SN1D | C76537 ✅ | In +3V3 feed to U9 VDD. **Footprint corrected 2026-07-14**: BLM18 series is 1608-metric = **0603** (the old row said 0402 — that would be BLM15AX601SN1D) |
| C23 | 100nF | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | U9 VDD bypass, U9 side of FB1 |
| C24 | 1µF | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | U9 VDD bulk |
| R9 | 4.7kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | I²C SDA pull-up (GPIO10) |
| R10 | 4.7kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | I²C SCL pull-up (GPIO11) |
| **R_DRDY** | **4.7kΩ** | **0402** | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | **ADD TO SCHEMATIC** — ADS_DRDY to +3V3; required open-drain pull-up |

---

## Sensors — 4-20mA Channels

| Ref | Value | Package | KiCad 10 Footprint | MPN | LCSC | Notes |
|-----|-------|---------|-------------------|-----|------|-------|
| D9 | **SMAJ5.0A TVS 5V uni** | DO-214AC | `Diode_SMD:D_SMA` | SMAJ5.0A-TR (ST) | **C98802** ✅ | J4 SIG surge clamp. **CHANGED 2026-07-14 from SMAJ3.3CA** (blocker #6 FAIL: IR = 800 µA max at VRWM — un-guaranteeable at the 2.0 V node). VBR min 6.4 V → 2.0 V working point far below the knee; Vc 9.2 V; forward diode clamps negatives; R3/R5 + D1 still protect the ADS1115 pins. **Schematic value edit required** (blocker #9c) |
| D10 | **SMAJ5.0A TVS 5V uni** | DO-214AC | `Diode_SMD:D_SMA` | SMAJ5.0A-TR (ST) | **C98802** ✅ | J5 SIG surge clamp — see D9 |
| **GDT1** | **GDT 90V DNF** | 8×6 mm SMD 2-pole | `WellD:GDT_BOURNS_2038_SM` ⚠️ draw in WellD.pretty (no standard lib footprint) | BOURNS 2038-09-SM class (e.g. 2038-09-SM-RPLF; Littelfuse GTCS23-900M-R05 alternate) | — ⚠️ | **NEW 2026-07-19 (DNF)** — alternatives review P-3: coarse kA-class stage of the industrial GDT → series-R → TVS 3-stage loop protection, LOOP_TERM_CH1 → GND. **Footprint only, do not fit by default** — populate per site only for long/buried/aerial transducer cable runs |
| **GDT2** | **GDT 90V DNF** | 8×6 mm SMD 2-pole | `WellD:GDT_BOURNS_2038_SM` ⚠️ draw in WellD.pretty | same as GDT1 | — ⚠️ | **NEW 2026-07-19 (DNF)** — LOOP_TERM_CH2 → GND, see GDT1 |
| D1 | PRTR5V0U2X dual ESD | SOT-143B | `Package_TO_SOT_SMD:SOT-143` | PRTR5V0U2X,215 | **C12333** ✅ (**corrected 2026-07-14** — old C2687116 is a UMW USBLC6-2SC6 clone) | ADS1115 AIN0/AIN1 input clamp. Pinout verified: **1=GND, 2=I/O1, 3=I/O2, 4=VCC** — welld 6-pin SOT-363 symbol must be redrawn (blocker #9b) |
| R2 | 100Ω ±0.1% 0.25W | 0805 | `Resistor_SMD:R_0805_2012Metric` | RG2012N-101-W-T1 | — ⚠️ | CH1 shunt (AIN0 reads across this) |
| R4 | 100Ω ±0.1% 0.25W | 0805 | `Resistor_SMD:R_0805_2012Metric` | RG2012N-101-W-T1 | — ⚠️ | CH2 shunt |
| C34 | 10nF X7R 25V | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | HF bypass directly across R2 (was "C_SH1") |
| C35 | 10nF X7R 25V | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | HF bypass directly across R4 (was "C_SH2") |
| R3 | 100Ω | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | CH1 series limiter to AIN0 |
| R5 | 100Ω | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | CH2 series limiter to AIN1 |
| C3 | 1µF X5R | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | CH1 RC filter with R3 (fc≈1.6kHz) |
| C5 | 1µF X5R | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | CH2 RC filter with R5 |
| C4 | 10µF 10V | 0805 | `Capacitor_SMD:C_0805_2012Metric` | — | ✅ | CH1 bulk |
| C6 | 10µF 10V | 0805 | `Capacitor_SMD:C_0805_2012Metric` | — | ✅ | CH2 bulk |

---

## Sensors — DS18B20 1-Wire

| Ref | Value | Package | KiCad 10 Footprint | MPN | LCSC | Notes |
|-----|-------|---------|-------------------|-----|------|-------|
| D12 | PRTR5V0U2X dual ESD | SOT-143B | `Package_TO_SOT_SMD:SOT-143` | PRTR5V0U2X,215 | **C12333** ✅ (corrected 2026-07-14) | Same part as D1; 1-Wire DATA ESD clamp (I/O2 channel NC) |
| R6 | 4.7kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | 1-Wire pull-up to +3V3 |
| R28 | 100Ω | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | VCC series protection |
| R32 | 33Ω | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | **POPULATE** (was DNF) — GPIO abs-max protection for cable runs; resolves review warning #15 |
| C7 | 100nF | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | J6 VCC bypass |

---

## Solar Input Protection

| Ref | Value | Package | KiCad 10 Footprint | MPN | LCSC | Notes |
|-----|-------|---------|-------------------|-----|------|-------|
| D14 | **SMAJ10CA TVS 10V bidi** | DO-214AC | `Diode_SMD:D_SMA` | SMAJ10CA | C2836474 ⚠️ (verify at order time) | At J12 SOLAR+ terminal; same reel as D8. **Re-rated 2026-07-19** (1S, 6 V-nominal panel — was SMAJ24CA for 12 V panels) |

---

## Connectors — Field Side

> **Connector strategy:** PCB headers (G series, screw-clamp side that stays on the board) are LCSC-available and wave-soldered by PCBWay. Field plugs have been upgraded to **spring-cage** (STF series) — no screws to strip. Order field plugs from Mouser/Digi-Key and include them in the box with the product; they do not go to PCBWay.

| Ref | PCB Header (PCBWay assembles) | KiCad 10 Footprint | LCSC | Field Plug (ship separately) | MPN |
|-----|------------------------------|-------------------|------|------------------------------|-----|
| J4 | Phoenix MC 1.5/3-G-3.5 | `Connector_Phoenix_MC:PhoenixContact_MC_1,5_3-G-3,5_1x03_P3.50mm_Horizontal` | ✅ | **MC 1.5/3-STF-3.5** (spring-cage, no screws) | 1827755 |
| J5 | Phoenix MC 1.5/3-G-3.5 | same as J4 | ✅ | **MC 1.5/3-STF-3.5** | 1827755 |
| J6 | Phoenix MC 1.5/3-G-3.5 | same as J4 | ✅ | **MC 1.5/3-STF-3.5** | 1827755 |
| J7 | Phoenix MC 1.5/3-G-3.5 | same as J4 | ✅ | **MC 1.5/3-STF-3.5** | 1827755 |
| J12 | Phoenix MC 1.5/2-G-3.5 | `Connector_Phoenix_MC:PhoenixContact_MC_1,5_2-G-3,5_1x02_P3.50mm_Horizontal` | ✅ | **MC 1.5/2-STF-3.5** (spring-cage, 2-pos) | 1827742 |

> **Why spring-cage works with the same PCB header:** Phoenix Contact's MC 1.5 G-series headers accept both ST (screw) and STF (spring-cage) plugs of the same pitch. No board change needed — just swap the plug type.

---

## Connectors — Programming & Expansion

| Ref | Value | Package | KiCad 10 Footprint | Notes |
|-----|-------|---------|-------------------|-------|
| J10 | 6-pin 1.27mm prog header | THT | `Connector_PinHeader_1.27mm:PinHeader_1x06_P1.27mm_Vertical` | UART TX/RX/GND/3V3/GPIO9/EN |
| J3 | SMA edge-launch (Amphenol 132289) | SMD edge | `Connector_Coaxial:SMA_Amphenol_132289_EdgeMount` | ✅ in KiCad standard lib |
| J8 | I²C header 4-pin 2.54mm | THT DNF | `Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical` | DNF |
| J9 | GPIO header 8-pin 2.54mm | THT DNF | `Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical` | DNF |

---

## ESD / Reverse Polarity

| Ref | Value | Package | KiCad 10 Footprint | MPN | LCSC |
|-----|-------|---------|-------------------|-----|------|
| D8 | SMAJ10CA 10V bidi | DO-214AC | `Diode_SMD:D_SMA` | SMAJ10CA | C2836474 ⚠️ |

---

## Test Points (all DNF — pads only)

All test points use: `TestPoint:TestPoint_Pad_1.0x1.0mm`

| Ref | Net | Notes |
|-----|-----|-------|
| TP1 | VBAT | After D5 |
| TP2 | VLOOP | After U8 VOUT |
| TP3 | +3V3 | After U1 |
| TP4 | GND | Reference |
| TP5 | LOOP_TERM_CH1 | Between R2 and R3 |
| TP6 | LOOP_TERM_CH2 | Between R4 and R5 |
| TP7 | 1WIRE | At J6 DATA |
| TP8 | I2C_SDA | GPIO10 |
| TP9 | I2C_SCL | GPIO11 |
| TP10 | VSOLAR_IN | At J12 |
| TP11 | VBAT_RAW | At BT1 cell+, before D5 |
| TP12 | ADS_DRDY | GPIO12 interrupt line |
| TP13 | FACTORY_RESET | **NEW** — GPIO13; short to GND at power-on for NVS erase + rejoin |
| TP14 | /CHRG_SOLAR | Solar charge status (present in interfaces sheet, was missing here) |
| TP15 | /CHRG_USB | TP4056 /CHRG charge status (open-drain, R38 pull-up) |

---

## Solder Jumpers

| Ref | Type | KiCad 10 Footprint | Default |
|-----|------|-------------------|---------|
| SJ1 | 2-pad open | `Jumper:SolderJumper-2_P1.3mm_Open_TrianglePad1.0x1.5mm` | Open (DNF) |
| SJ2 | 2-pad bridged | `Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm` | Closed |
| SJ3 | 2-pad bridged | `Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm` | Closed |
| SJ4 | 2-pad bridged | `Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm` | Closed — UART_TX to J10 (was missing here; symbol exists in interfaces sheet) |
| SJ5 | 2-pad bridged | `Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm` | Closed — UART_RX to J10 (was missing here) |

---

## Custom Footprints Needed (not in KiCad standard library)

| Component | Status | Action |
|-----------|--------|--------|
| ESP32-C6-MINI-1U | In `WellD.pretty/` already, verify | Download Espressif KiCad libs as backup |
| ~~XT30PW-F~~ | Deleted 2026-07-19 with J1 (battery-carrier change) | — |
| BT1 18650 carrier | **To draw** (`WellD:BH-18650_THT`, blocker #11c) | From the chosen holder's drawing — body ≈78×21 mm, two THT tabs |
| TYPE-C-31-M-12 (J13) | `Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12` expected in KiCad official lib | ⚠️ Verify the exact footprint name against the installed KiCad 10 `Connector_USB` library before layout (swapped from GCT USB4135-GF-A 2026-07-19; GCT KiCad files remain the fallback for the approved-alternate part) |
| GDT1/GDT2 (BOURNS 2038-SM class) | Not in standard lib | Draw `WellD:GDT_BOURNS_2038_SM` (8×6 mm SMD 2-pole land pattern per Bourns 2038-SM datasheet) — pads required even though DNF |
| CDRH4D22 inductors (L1, L2) | May need verification | Check `Inductor_SMD:L_4.0x4.0mm_H2.6mm` exists; if not, use KiCad footprint editor to create 4.0×4.0mm SMD pad |
| ~~L3~~ | **Deleted 2026-07-19** with the IP2326 | — |
| L_SOLAR (CN3791 buck inductor) | ✅ resolved 2026-07-19: **SRN6045TA-220M** (22µH, Isat 3.3 A) | `Inductor_SMD:L_Bourns-SRN6045TA` — same footprint, no redraw |
| TP4056 (U12) | ✅ Standard package (SOP-8 + EPAD) | KiCad standard `Package_SO:SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.29x2.29mm` — no custom footprint needed (the IP2326's custom QFN-24 footprint task dies with it) |
