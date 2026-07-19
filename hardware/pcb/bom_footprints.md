# WellD PCB — BOM with KiCad 10 Footprints

**Board:** 80 × 55 mm (or your chosen size), 2-layer, 1.6 mm FR4, 1 oz Cu  
**Assembler:** PCBWay PCBA  
**Sourcing key:** ✅ LCSC (direct PCBWay) · ⚠️ PCBWay global sourcing · 📦 Customer-supply to PCBWay

> **2026-07-05 electrical review:** several parts changed (U1, D8/D14, C8, C17, LED GPIO) and new components were added (D15, Q3–Q5, R15/R16/R25/R27/R29, C36, TP13). See `schematic_connections.md` → "Design changes" and "Datasheet verification blockers" before ordering.
>
> **2026-07-05 component-selection review** (`component_selection_review.md`): the non-functional TP5100 USB charge path is **replaced by an Injoinic IP2326 5 V→2S synchronous boost charger** (U12; +L3, R35 repurposed as ISET, R36/R37 deleted, F2 uprated to 2 A hold). Do not order the USB-charger section until verification blocker #2 (IP2326 datasheet items) is resolved — the mid-cell/balance-pin question could still reopen the choice.
>
> **2026-07-13 reconciliation pass:** all rows below now have matching schematic symbols (senior review 2026-07-06 CRITICAL 1–3 cleared). **CN3722 CRITICAL CV fix**: R33 590k→243k, R20 36k→158k, R19 repurposed as R_CS 0.4 Ω, U7 redrawn TSSOP-16 with its external buck stage (see the solar section). The IP2326 mid-cell question is resolved (VBATM/VBAT_GND float).
>
> **2026-07-14 full component verification sweep** (`component_verification_2026-07-14.md`): IP2326 package = **QFN24 4×4 mm** ✅, F2 = **MF-MSMF250/16X-2** ✅, NTCs = **SDNT1608X103F3950FTF** ✅, L_SOLAR **verified** ✅, L3 MPN picked ✅. Wrong LCSC numbers fixed (D1/D12, U6, U7); **D9/D10 changed SMAJ3.3CA → SMAJ5.0A** (leakage fail); **U1 needs a BST–SW 100 nF cap (C_BST_AP, new row) and its symbol renumbered** — see blocker #9 in `schematic_connections.md` for the required schematic edits. Remaining order blocker: pack PCM charge rating (#7a).

---

## Power — Battery Input

| Ref | Value | Package | KiCad 10 Footprint | MPN | LCSC | Notes |
|-----|-------|---------|-------------------|-----|------|-------|
| J1 | XT30PW-F right-angle | THT | `WellD:XT30PW-F_RightAngle` (custom, in WellD.pretty) | XT30PW-F | C601498 ✅ | Pin 1=BAT+, Pin 2=BAT− |
| D5 | AO3407 P-ch MOSFET | SOT-23 | `Package_TO_SOT_SMD:SOT-23` | AO3407 | C31417 ✅ | Reverse-polarity protection |
| R31 | 10kΩ 1% | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | C25741 ✅ | D5 gate pull-down to GND (holds load switch ON) |
| D13 | SMAJ10CA TVS 10V bidi | DO-214AC | `Diode_SMD:D_SMA` | SMAJ10CA | C2836474 ⚠️ | Battery terminal TVS. ⚠️ C2836474 could not be confirmed against an LCSC listing (2026-07-14) — verify at order time; Littelfuse/MDD SMAJ10CA variants are stocked |

---

## Power — USB-C Charging (IP2326 boost path — replaced TP5100, 2026-07-05)

> TP5100 (step-down charger) could not make 8.4 V from 5 V USB. Replaced with the Injoinic **IP2326** synchronous 5 V→2S **boost** charger. Every ⚠️ item below must be checked against the IP2326 datasheet before schematic capture — see verification blocker #2 in `schematic_connections.md`, especially the **mid-cell/balance pin vs 2-pin XT30 pack** question, which could reopen this selection.

| Ref | Value | Package | KiCad 10 Footprint | MPN | LCSC | Notes |
|-----|-------|---------|-------------------|-----|------|-------|
| J13 | USB-C 2.0 power-only | 16-pin SMD + 4 THT shell legs | `Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12` ⚠️ verify exact footprint name in installed KiCad 10 lib before layout | **HRO TYPE-C-31-M-12** | **C165948** ✅ (order the Korean Hroparts listing specifically — part is endlessly cloned) | **SWAPPED 2026-07-19** (alternatives review P-2): was GCT USB4135-GF-A (~$1+, global sourcing) — GCT demoted to approved alternate (needs its own land pattern back). 16-pin USB-2.0 subset; symbol pins A1/A4/A5/A6/A7/B5 unchanged. ⚠️ Layout note: B-side mirror pins (B1/B4/B6/B7/B9/B12 etc.) tie to the same nets inside the footprint (GND/VBUS/D±) — check pad-to-net map when the footprint lands |
| U11 | USBLC6-2SC6 ESD | SOT-23-6 | `Package_TO_SOT_SMD:SOT-23-6` | USBLC6-2SC6 | C7519 ✅ | VBUS + D+/D− clamp. Pinout verified 2026-07-14: 1=I/O1, 2=GND, 3=I/O2, 4=I/O2, 5=VBUS, 6=I/O1 — **welld symbol must be renumbered** (blocker #9) |
| F2 | **MF-MSMF250/16X-2 PTC 2.5A hold** | **1812** | `Fuse:Fuse_1812_4532Metric` | MF-MSMF250/16X-2 | C210838 ✅ | **Resolved 2026-07-14** (blocker #8): 2.5 A hold / 5.0 A trip / 16 V / 100 A max / 15 mΩ, −40…+85 °C. Series with J13 VBUS; boost charger input ≈1.9 A at 1 A charge. Hold derates to ≈1.75–2 A at 60 °C — if hot-enclosure nuisance trips appear, drop RISET to 120 kΩ (0.75 A charge → ≈1.4 A input) |
| U12 | **IP2326 2S boost charger** | **QFN24 4×4 mm, 0.5 mm pitch, EPAD 2.5×2.5 mm** (✅ resolved 2026-07-14: DS V1.2 §11 + LCSC listing) | `welld:IP2326_TBD` → draw from `Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.6x2.6mm` (KiCad standard fits; EP max 2.6) | IP2326 | C2832094 ✅ (in stock; do NOT order IP2326-NPD C5441281) | 5 V VBUS → 8.3 V (RVSET=120k) CC/CV sync boost, 1 A charge (RISET=90k), input-power-adaptive. Auto-runs on VBUS (EN pin 12 left floating = enabled; VBATM/VBAT_GND 23/24 left floating = balance off, 2-pin pack OK). Keep the 8×8 mm GND pour from Group G (~0.9 W at 1 A charge). Hand-rework = hot-air only (QFN + EPAD). Symbol placed 2026-07-13 |
| **L3** | **2.2µH 3.8A** | 5.0×5.0×4.0mm SMD | create `WellD:L_5050` (5.0×5.0 mm) | **SWPA5040S2R2NT** (Sunlord) | — ✅ look up C# | IP2326 boost inductor, MPN picked 2026-07-14: 2.2 µH ±30 %, 3.8 A, 25 mΩ. Datasheet ref-BOM asks Isat/Idc >5 A / DCR <20 mΩ for the chip's full 2 A charge — 3.8 A gives ≈1.6× margin at our 1 A setpoint; **do not raise RISET above 90 k without resizing L3** (6×6 SWPA6045S class matches the DS BOM exactly) |
| R35 | **90kΩ 1% (ISET)** | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | I_CH = 90000/R_ISET → **1 A** (datasheet-firm 2026-07-06; was TP5100 PROG 1.2 kΩ). Value updated in schematic 2026-07-13 |
| **R_VSET** | **120kΩ 1%** | 0603 | `Resistor_SMD:R_0603_1608Metric` | — | ✅ | VSET (pin 3) strap → CV **8.3 V typ / 8.4 V max**. Do NOT leave NC (NC strap maxes at 8.5 V — unsafe for 2S). Symbol placed 2026-07-13; ⚠️ verify strap polarity (GND vs VOUT) |
| **C_BST2** | **100nF 25V** | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | **NEW 2026-07-13** — BST (14) ↔ LX bootstrap per datasheet |
| **C_SYS1, C_SYS2** | **22µF 25V X5R ×2** | 1206 | `Capacitor_SMD:C_1206_3216Metric` | — | ✅ | **NEW 2026-07-13** — VSYS (19/20) caps, 2×22 µF per datasheet. **Uprated 16 V → 25 V 2026-07-14**: IP2326 DS ref BOM requires >16 V rating on VIN/VSYS/VOUT caps |
| ~~R36~~ | — | — | — | — | — | **DELETED 2026-07-05** — TP5100 CE pull-up; IP2326 has no CE (⚠️ verify) |
| ~~R37~~ | — | — | — | — | — | **DELETED 2026-07-05** — TP5100 CE pull-down; **GPIO4 freed** (coordinate with firmware). Restore only if IP2326 proves to have an EN pin |
| R38 | 4.7kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | /CHRG_USB pull-up to +3V3 (routes to TP15 only). ⚠️ Reassign to IP2326 charge-status/LED pin — verify pin, polarity, open-drain |
| RT1 | **10kΩ NTC B3950 1%** | 0603 | `Resistor_SMD:R_0603_1608Metric` | **SDNT1608X103F3950FTF** (Sunlord) ✅ | — ✅ look up C# (3450 sibling is C95953) | IP2326 NTC (pin 4, 20 µA source) → GND, thermally coupled to the pack — USB-path cold-charge (<0 °C) cutoff (`component_selection_review.md` O-1). MPN picked 2026-07-14. ⚠️ derive the exact threshold math from the datasheet table at layout time |
| R50 | 5.1kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | J13 CC1 → GND (was "R_CC1") |
| R51 | 5.1kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | J13 CC2 → GND (was "R_CC2") |
| C27 | 4.7µF 10V X5R | 0805 | `Capacitor_SMD:C_0805_2012Metric` | — | ✅ | VUSB input filter after F2 |
| C28 | 10µF **25V** X5R | 0805 | `Capacitor_SMD:C_0805_2012Metric` | — | ✅ | U12 VIN bypass. Value ✅ confirmed vs IP2326 DS ref BOM 2026-07-14; **uprated 10 V → 25 V** (DS requires >16 V rating) |
| C29 | 10µF **25V** X5R | 0805 | `Capacitor_SMD:C_0805_2012Metric` | — | ✅ | U12 BAT-side bypass. Value ✅ confirmed 2026-07-14 (DS ref design: 10 µF + 22 µF at VOUT — 10 µF suffices at 1 A with the pack on the node); **uprated 16 V → 25 V** per DS |

---

## Power — Solar MPPT Charging (CN3722 path)

> **2026-07-13 CRITICAL correction + datasheet verification (Consonance Rev 1.1):** the CN3722's FB reference is **2.416 V** (not the CN3791's 1.205 V used in all earlier math — the old R33=590k divider would have regulated the pack at ≈16.7 V), its MPPT reference is **1.04 V**, the package is **TSSOP-16**, and it is a **controller** requiring an external P-FET buck stage (M_SOLAR/D16/D_SOLAR/L_SOLAR) with a CSP–BAT sense resistor (R19 repurposed as R_CS; there is no VPROG pin). Formula: **V_REG = 2.416 × (1 + R_FBH/R_FBL)**.

| Ref | Value | Package | KiCad 10 Footprint | MPN | LCSC | Notes |
|-----|-------|---------|-------------------|-----|------|-------|
| U7 | CN3722 MPPT buck charge controller | **TSSOP-16** | `Package_SO:TSSOP-16_4.4x5mm_P0.65mm` | CN3722 | **C77905** ✅ (**corrected 2026-07-14** — old C2690716 does not match) | VCC 7.5–28V operating, **abs max 30 V** (CSP/BAT 28 V); external P-FET buck; BAT-pin sleep current 10µA typ @ 12V; ~$0.50, in stock |
| D6 | MBRS140 Schottky 1A 40V | SMB | `Diode_SMD:D_SMB` | MBRS140T3G | — ✅ | Solar backfeed block (MBRS140T3G is SMB, not SOD-123) |
| D8 | **SMAJ24CA TVS 24V bidi** | DO-214AC | `Diode_SMD:D_SMA` | SMAJ24CA | **C148223** ✅ (Littelfuse; sourced 2026-07-14) | At CN3722 VIN; same reel as D14. Was SMAJ28CA (zero margin vs CN3722 abs max). Panel Voc limit **24V**; VBR min 26.7 V, Vc 38.9 V |
| **M_SOLAR** | **SI2319CDS P-ch MOSFET −40 V** | SOT-23 | `Package_TO_SOT_SMD:SOT-23` | **SI2319CDS-T1-GE3** (Vishay) | **C146287** ✅ (VBsemi clone **C558254** approved alternate) | **SWAPPED 2026-07-19** (alternatives review P-4, settles verification-sweep R-1): was AO3407 (−30 V, ~23 % Vds margin vs the 24 V-clamped panel + switch-node ringing). −40 V restores >60 % margin; same SOT-23 G/S/D pinout, gate driven by DRV (16), DRV clamps |Vgs| to 5–8 V ✅. D5/Q3/Q5 stay AO3407 |
| **D16** | **SS34 Schottky 3A 40V** | DO-214AC | `Diode_SMD:D_SMA` | SS34 | C8678 ✅ | **NEW 2026-07-13** — series diode after M_SOLAR (datasheet Fig. 1): blocks night back-feed VBAT→L_SOLAR→M_SOLAR body diode→R20/R21 (≈45µA) |
| **D_SOLAR** | **SS34 Schottky 3A 40V** | DO-214AC | `Diode_SMD:D_SMA` | SS34 | C8678 ✅ | **NEW 2026-07-13** — buck catch/freewheel diode (GND→SOLAR_FW) |
| **L_SOLAR** | **47µH shielded** | 6×6×4.5mm SMD | `Inductor_SMD:L_Bourns-SRN6045TA` | SRN6045TA-470M ✅ **verified 2026-07-14** | — (JLCPCB **C5151734**) | Buck inductor; ΔI≈0.3A at 300kHz/17.5V→8.4V/0.5A → peak ≈0.65 A vs **Isat ≈1.3 A / Irms ≈1.1 A / DCR ≈0.2 Ω** — ≥2× margin ✅; AEC-Q200 |
| **R19** | **0.4Ω 1% (R_CS)** | **1206** | `Resistor_SMD:R_1206_3216Metric` | — | ✅ | **REPURPOSED 2026-07-13** — CSP–BAT sense resistor: I_CH = 0.2V/R_CS = **500mA**; P = 0.1W. (Was "2.0kΩ VPROG" — no such pin exists) |
| R20 | **158kΩ 1% E96** | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | MPPT divider high-side → V_MP = 1.04×(1+158/10) ≈ **17.5V** (12V-nominal panel; was 36k assuming a 1.205V ref → 5.5V, below UVLO). ⚠️ Recompute for the actual panel |
| R21 | 10kΩ 1% | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | MPPT divider low-side (MPPT pin→GND) |
| R33 | **243kΩ 1% E96** | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | CV FB divider high-side (VBAT→FB) → V_REG = 2.416×(1+243/100) = **8.287V** ✓ (**was 590kΩ → ≈16.7V with the real 2.416V reference — CRITICAL fix 2026-07-13**) |
| R34 | 100kΩ 1% | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | CV FB divider low-side (FB→GND) |
| **C_VG** | **100nF 50V** | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | **NEW 2026-07-13** — VG (1) ↔ **VCC** (not GND) per datasheet |
| **C_COM1** | **470pF 50V** | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | **NEW 2026-07-13** — COM1 (8) → GND |
| **C_COM2** | **220nF 25V** | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | **NEW 2026-07-13** — COM2 (9) → C_COM2 → R_COM2 → GND |
| **R_COM2** | **120Ω 5%** | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | **NEW 2026-07-13** — series with C_COM2 |
| **C_COM3** | **100nF 25V** | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | **NEW 2026-07-13** — COM3 (11) → GND |
| **RT_SOLAR** | **10kΩ NTC B3950 1%** | 0603 | `Resistor_SMD:R_0603_1608Metric` | **SDNT1608X103F3950FTF** (Sunlord) ✅ | — ✅ look up C# | **NEW 2026-07-13** — TEMP (6) → GND, thermally coupled to the pack: charge suspended below ≈+2°C / above ≈+54°C (55µA pull-up, 1.61V/0.175V thresholds). Solar-path cold-charge cutoff (review O-1). Same reel as RT1 (MPN picked 2026-07-14) |
| C17 | 10µF **35V** X5R | **1206** | `Capacitor_SMD:C_1206_3216Metric` | — | ✅ | CN3722 VIN filter (rail can sit at panel Voc up to 24V; 25V rating had no margin) |
| C18 | 10µF 16V | 0805 | `Capacitor_SMD:C_0805_2012Metric` | — | ✅ | CN3722 VBAT filter |
| C21 | 100nF **50V** | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | HF bypass at CN3722 VIN (across D8) |
| R25 | 4.7kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | **NEW** — /CHRG_SOLAR pull-up to +3V3 (GPIO6; was internal pull-up only) |
| D7 | Green LED | 0603 | `LED_SMD:LED_0603_1608Metric` | — | ✅ | Solar-charging indicator: +3V3→R22→D7→/CHRG_SOLAR |
| R22 | 1kΩ **DNF** | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | D7 series resistor — DNF by default (fit for bench debug) |

---

## Power — 3.3V Buck (AP63203)

| Ref | Value | Package | KiCad 10 Footprint | MPN | LCSC | Notes |
|-----|-------|---------|-------------------|-----|------|-------|
| U1 | **AP63203WU buck 3.3V fixed** | TSOT-26 | `Package_TO_SOT_SMD:TSOT-23-6` (**corrected 2026-07-14** — TSOT, not SOT) | AP63203WU-7 | **C780769** ✅ | 22µA Iq, 2A, VIN 3.8–32V. Variant table ✅ verified 2026-07-14 (03 = 3.3 V fixed). Real pinout **FB=1, EN=2, VIN=3, GND=4, SW=5, BST=6** — **welld symbol pins 1–4 are wrong, renumber** (blocker #9a) |
| **C_BST_AP** | **100nF 25V** | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | **NEW 2026-07-14 — REQUIRED**: BST (6) ↔ SW (5) bootstrap cap per Diodes DS41326 ("connect a 100 nF ceramic capacitor between BST and SW"). Bootstrap is NOT integrated; **+3V3 never starts without this cap** (blocker #9a / #1) |
| L2 | 4.7µH 1A shielded | 4×4mm SMD | `Inductor_SMD:L_4.0x4.0mm_H2.6mm` ⚠️verify name | CDRH4D22NP-4R7NC | C376098 ✅ | Same part as L1 |
| R_FBH | **DNP** (390kΩ 1% if AP63200WU alt) | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | DNP for fixed-3.3V AP63203WU (FB ties to +3V3). Only for adjustable AP63200WU: 390k/124k → 0.8×(1+390/124)=3.32V. The old 560k/124k assumed a 0.6V ref that no AP6320x part has |
| R_FBL | **DNP** (124kΩ 1% if AP63200WU alt) | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | See R_FBH |
| R11 | 10kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | EN pull-up to VIN (always-on) |
| C16 | 10µF 16V X5R | 0805 | `Capacitor_SMD:C_0805_2012Metric` | — | ✅ | U1 VIN bulk (AP6320x datasheet CIN = 10µF; was an orphan symbol, now assigned) |
| C9 | 100nF 16V | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | VIN bypass |
| C10 | 1µF 16V | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | VIN bulk |
| C11 | 100nF | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | VOUT bypass |
| C12 | 1µF | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | VOUT bulk |
| C_BUCK | 10µF 10V X5R | 0805 | `Capacitor_SMD:C_0805_2012Metric` | — | ✅ | Primary output filter cap after L2 (symbol present, needs wiring) |

---

## Power — 12V VLOOP Boost (MT3608B)

| Ref | Value | Package | KiCad 10 Footprint | MPN | LCSC | Notes |
|-----|-------|---------|-------------------|-----|------|-------|
| U8 | MT3608B boost 12V | SOT-23-6 | `Package_TO_SOT_SMD:SOT-23-6` | MT3608B | C84005 ✅ | GPIO5-gated, EN=HIGH during 4-20mA reads. Pin map **datasheet-confirmed 2026-07-14** (SW=1, GND=2, FB=3, EN=4, IN=5, NC=6 — KiCad official `MT3608` symbol agrees with both prior reviews); routine first-article check only |
| L1 | 4.7µH 1A shielded | 4×4mm SMD | `Inductor_SMD:L_4.0x4.0mm_H2.6mm` ⚠️verify name | CDRH4D22NP-4R7NC | C376098 ✅ | Same part as L2 |
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
| R7 | 330kΩ 1% | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | Divider high-side (VBAT→midpoint) |
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
| D14 | **SMAJ24CA TVS 24V bidi** | DO-214AC | `Diode_SMD:D_SMA` | SMAJ24CA | **C148223** ✅ (Littelfuse; sourced 2026-07-14) | At J12 SOLAR+ terminal; same reel as D8 (was SMAJ28CA — see D8 note) |

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
| D8 | SMAJ24CA 24V bidi | DO-214AC | `Diode_SMD:D_SMA` | SMAJ24CA | C148223 ✅ |

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
| TP11 | VBAT_RAW | At J1 BAT+, before D5 |
| TP12 | ADS_DRDY | GPIO12 interrupt line |
| TP13 | FACTORY_RESET | **NEW** — GPIO13; short to GND at power-on for NVS erase + rejoin |
| TP14 | /CHRG_SOLAR | Solar charge status (present in interfaces sheet, was missing here) |
| TP15 | /CHRG_USB | IP2326 charge status (⚠️ verify status pin) |

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
| XT30PW-F right-angle | In `WellD.pretty/` already | Verify pad dimensions against AMASS datasheet |
| TYPE-C-31-M-12 (J13) | `Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12` expected in KiCad official lib | ⚠️ Verify the exact footprint name against the installed KiCad 10 `Connector_USB` library before layout (swapped from GCT USB4135-GF-A 2026-07-19; GCT KiCad files remain the fallback for the approved-alternate part) |
| GDT1/GDT2 (BOURNS 2038-SM class) | Not in standard lib | Draw `WellD:GDT_BOURNS_2038_SM` (8×6 mm SMD 2-pole land pattern per Bourns 2038-SM datasheet) — pads required even though DNF |
| CDRH4D22 inductors (L1, L2) | May need verification | Check `Inductor_SMD:L_4.0x4.0mm_H2.6mm` exists; if not, use KiCad footprint editor to create 4.0×4.0mm SMD pad |
| L3 (IP2326 boost inductor) | ✅ MPN picked 2026-07-14: SWPA5040S2R2NT | Draw a 5.0×5.0 mm pad set (`WellD:L_5050`) per the Sunlord SWPA5040S land pattern |
| L_SOLAR (CN3722 buck inductor) | ✅ SRN6045TA-470M verified 2026-07-14 (Isat ≈1.3 A ≥2× need) | `Inductor_SMD:L_Bourns-SRN6045TA` matches |
| IP2326 (U12) | ✅ Package resolved 2026-07-14: **QFN24 4×4 mm, 0.5 mm pitch, EPAD 2.5×2.5 mm** | Draw `welld:IP2326_TBD` → real footprint in `WellD.pretty/` from KiCad standard `Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.6x2.6mm` (EP max 2.6 fits the 2.4–2.6 drawing). The previously assumed SOIC-8-1EP footprint is WRONG |
