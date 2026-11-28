# WellD PCB — Full Component Verification Sweep — 2026-07-14

**Scope:** every row of `bom_footprints.md` checked against real datasheet/vendor data
(web-search snippets, LCSC/JLCPCB listings, the KiCad official symbol library — which is
librarian-reviewed against datasheets — and the IP2326 V1.2 / CN3722 Rev 1.1 datasheets
already on file). Follows up the 2026-07-06 senior review and resolves verification
blockers #1, #2b, #3, #5 (both parts), #6 and #8 in `schematic_connections.md`.

**Verdict key:** ✅ verified · ⚠ issue found (action required) · ❌ could not verify

---

## Priority findings (headline)

1. **U1 AP63203WU needs a 100 nF BST–SW bootstrap cap** — the wiring doc left BST
   unconnected. Diodes DS41326 requires it; the 3.3 V rail will not start without it.
   **And the `welld` symbol numbering is wrong on pins 1–4** (real: FB=1, EN=2, VIN=3,
   GND=4, SW=5, BST=6). Two required schematic edits.
2. **U12 IP2326 package = QFN24, 4×4 mm, 0.5 mm pitch, EPAD 2.5×2.5 mm** (datasheet V1.2
   package drawing + LCSC C2832094 listing). Blocker 2b resolved.
3. **U11 USBLC6-2SC6 symbol confirmed wrong** — real map 1=I/O1, 2=GND, 3=I/O2, 4=I/O2,
   5=VBUS, 6=I/O1. Required symbol edit.
4. **U8 MT3608B pin map confirmed** (SW=1, GND=2, FB=3, EN=4, IN=5, NC=6) — third
   independent source (KiCad official `MT3608` symbol, reviewed against the Aerosemi
   datasheet). Blocker cleared to datasheet-confirmed.
5. **AO3407 fine everywhere** (−30 V VDS, ±20 V VGS, −4.1 A). M_SOLAR Vgs is safe because
   the CN3722 clamps DRV to 5–8 V below VCC. Vds margin at the 24 V panel clamp is ~23 %
   — acceptable; −40 V substitute noted as an optional robustness upgrade.
6. **D1/D12 PRTR5V0U2X**: SOT-143B, 1=GND, 2=I/O1, 3=I/O2, 4=VCC. **BOM LCSC number was
   wrong** — C2687116 is a UMW USBLC6-2SC6 clone; the real part is **C12333**
   (Nexperia PRTR5V0U2X,215).
7. **D9/D10 SMAJ3.3CA FAILS blocker #6** — datasheet IR is **800 µA max at VRWM 3.3 V**;
   ≤1 µA at 2.0 V/60 °C cannot be guaranteed. **Substitute SMAJ5.0A** (VBR ≥6.4 V puts
   the 2.0 V working point far below the knee; ST SMAJ5.0A-TR, LCSC C98802).
8. **F2 = Bourns MF-MSMF250/16X-2** — 2.5 A hold / 5 A trip / 16 V / 1812 / 15 mΩ,
   LCSC **C210838**, in stock. Blocker #8 resolved.
9. **Concrete MPNs picked**: L3 = Sunlord SWPA5040S2R2NT; L_SOLAR = SRN6045TA-470M
   verified adequate; RT1/RT_SOLAR = Sunlord SDNT1608X103F3950FTF.
10. **Sinowatt pack PCM charge rating: still unfindable** — blocker #7a stays open (see
    Issues section for what was tried).

---

## Verification table

### Power — battery input

| Ref | Part | Verdict | Key numbers | Source |
|-----|------|---------|-------------|--------|
| J1 | XT30PW-F | ✅ | AMASS right-angle XT30; LCSC C601498 previously confirmed | prior review (unchanged) |
| D5 | AO3407 | ✅ | VDS −30 V, VGS ±20 V, ID −4.1 A; sees Vds/Vgs −8.4 V max → >3× margin | aosmd.com/res/datasheets/AO3407.pdf (search-verified) |
| R31 | 10 k 0402 | ✅ | generic; C25741 is the UNI-ROYAL 0402 10 k 1 % basic part | LCSC |
| D13 | SMAJ10CA | ⚠ | Part correct for VBAT (10 V standoff > 8.4 V); **LCSC C2836474 could not be confirmed** — verify at order time (Littelfuse/MDD variants stocked) | LCSC search (no hit on C2836474) |

### Power — USB-C / IP2326

| Ref | Part | Verdict | Key numbers | Source |
|-----|------|---------|-------------|--------|
| J13 | USB4135-GF-A | ⚠ (unchanged) | GCT part real; LCSC availability still global-sourcing; HRO TYPE-C-31-M-12 alternate stands | prior review |
| U11 | USBLC6-2SC6 (ST) | ⚠ symbol | LCSC C7519 = genuine ST ✅. Real pinout **1=I/O1, 2=GND, 3=I/O2, 4=I/O2, 5=VBUS, 6=I/O1** — welld symbol (VBUS=1, GND=4) is WRONG → required edit | KiCad official lib `USBLC6-2SC6`→`USBLC6-2P6`; ST DS |
| F2 | **MF-MSMF250/16X-2** | ✅ resolved | 2.5 A hold / 5.0 A trip / 16 V / 100 A max / 15 mΩ / **1812** (4.83×3.41 mm); −40…+85 °C. LCSC **C210838** in stock. At 60 °C enclosure hold derates to ≈1.75–2 A vs ≈1.9 A boost input — margin still thin at full 1 A charge in a hot box; RISET=120 k (0.75 A) fallback stands | Bourns MF-MSMF DS via DigiKey/Newark; LCSC C210838 |
| U12 | IP2326 | ✅ resolved | **QFN24 4×4 mm, e=0.5 mm, EPAD D2/E2 = 2.4–2.6 mm (2.5 nom), height 0.75 mm, lead 0.35–0.45 mm** — datasheet V1.2 §11 + LCSC C2832094 ("4×4mm QFN24", in stock, from $0.30). KiCad standard `Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.6x2.6mm` fits (EP max 2.6). Hand-rework now = hot-air only. Do not confuse with IP2326-NPD (C5441281) | ip2326.txt (scratchpad, V1.2); LCSC C2832094 |
| L3 | 2.2 µH boost inductor | ⚠→MPN picked | **Sunlord SWPA5040S2R2NT**: 2.2 µH ±30 %, 3.8 A rated, 25 mΩ, 5.0×5.0×4.0 mm. Note: IP2326 ref-BOM asks Isat/Idc > 5 A, DCR < 20 mΩ (sized for the chip's full 2 A charge). At our 1 A charge (≈1.9 A avg input, ≈2.4 A peak) 3.8 A gives ≈1.6× margin — acceptable; if layout allows 6×6 mm, a 5 A-class part (SWPA6045S2R2NT class) matches the datasheet BOM exactly | IP2326 DS §10 BOM; evelta/LCSC SWPA5040S data |
| R35 | 90 k ISET | ✅ | I_CH = 90000/R → 1 A, datasheet-firm | IP2326 DS |
| R_VSET | 120 k | ✅ | 8.3 V typ / 8.4 V max CV; strap polarity: RVSET goes **VSET (pin 3) → GND** per ref schematic | IP2326 DS §10 |
| C_BST2 | 100 nF | ✅ | BST(14)↔LX per DS (ref design C2 = 104) | IP2326 DS |
| C_SYS1/2 | 22 µF ×2 | ⚠ rating | DS ref BOM: 22 µF **25 V** 0805, "voltage higher than 16 V is required" → change 16 V → **25 V** rating (1206 X5R 25 V fine) | IP2326 DS §10 BOM |
| C28 | 10 µF U12 VIN | ⚠ rating | DS ref BOM uses 10 µF **25 V** at VIN → uprate from 10 V to 25 V (blocker 2i closed) | IP2326 DS §10 BOM |
| C29 | 10 µF U12 VOUT/BAT | ⚠ rating | DS ref design: VOUT carries 10 µF + 22 µF, all 25 V-class → uprate C29 to 25 V (blocker 2i closed) | IP2326 DS §10 |
| RT1 | 10 k NTC B3950 0603 | ✅ MPN picked | **Sunlord SDNT1608X103F3950FTF** (10 k ±1 %, B25/50=3950, 0603) — real, stocked (DigiKey 14122365; LCSC carries the SDNT1608 family) | DigiKey/LCSC |
| R38/R50/R51/C27 | passives | ✅ | Ref design confirms 5.1 k CC sinks and LED/status drive ≤5 mA | IP2326 DS §10 |

### Power — solar / CN3722

| Ref | Part | Verdict | Key numbers | Source |
|-----|------|---------|-------------|--------|
| U7 | CN3722 TSSOP-16 | ⚠ LCSC | Package TSSOP-16 ✅, VCC 7.5–28 V operating, **VCC abs max 30 V** (CSP/BAT 28 V), MPPT 1.04 V, FB 2.416 V — all re-confirmed from the Rev 1.1 PDF on file. **LCSC number wrong: use C77905** (Consonance CN3722, in stock ~$0.50); C2690716 does not match | cn3722.txt (scratchpad); LCSC C77905 |
| M_SOLAR | AO3407 | ✅ | Vgs drive: DRV clamps to **VCC−6.5 V typ (5–8 V range)** → |Vgs| ≤ 8 V vs ±20 V abs max ✅. Vds worst normal-op = −(24+0.4) ≈ −24.4 V vs −30 V → ~23 % margin (meets ≥20 % on the clamped standoff; switch-node ringing eats into it — see recommendation R-1). Id peak ≈0.65 A vs −4.1 A ✅ | CN3722 DS (DRV section, elec. char.); AOS AO3407 DS |
| D6 | MBRS140T3G SMB | ✅ | 1 A/40 V Schottky, blocks backfeed; 40 V > 24 V clamp ✅ | prior review (unchanged) |
| D8/D14 | SMAJ24CA | ✅ sourcing fixed | 24 V standoff / VBR min 26.7 V / Vc 38.9 V. **LCSC C148223** (Littelfuse, 15 k+ stock; ST C132946, MDD C113963 alternates). Genuine-surge clamp (38.9 V) still exceeds CN3722 30 V abs max — carried warning #4, unchanged | Littelfuse DS; LCSC C148223 |
| D16/D_SOLAR | SS34 | ✅ | 3 A/40 V, LCSC C8678 (MDD) — well-known basic part | LCSC |
| L_SOLAR | SRN6045TA-470M | ✅ | 47 µH ±20 %, **Isat ≈1.3 A, Irms ≈1.1–1.6 A** (source-dependent spec line), DCR ≈0.2 Ω, 6×6×4.5 mm, AEC-Q200. Buck peak ≈0.65 A → ≥2× Isat margin ✅. JLCPCB **C5151734** | Bourns SRN6045TA DS via distributors; JLCPCB |
| R19 (R_CS) | 0.4 Ω 1206 | ✅ | I_CH = 0.2 V/0.4 Ω = 500 mA; P = I²R = 0.1 W → 1206 (0.25 W) 2.5× ✅ | CN3722 DS |
| R20/R21/R33/R34 | dividers | ✅ | 2.416 V FB / 1.04 V MPPT math re-checked: 243k/100k → 8.287 V; 158k/10k → 17.5 V | CN3722 DS |
| C_VG/C_COM1/C_COM2/R_COM2/C_COM3 | compensation | ✅ | VG cap **to VCC** (not GND) confirmed; COM values per DS compensation section | CN3722 DS |
| RT_SOLAR | 10 k NTC B3950 | ✅ | Same MPN as RT1 (SDNT1608X103F3950FTF); TEMP pin 55 µA pull-up, 1.61/0.175 V thresholds | CN3722 DS |
| C17/C18/C21 | filters | ✅ | C17 35 V/1206 at ≤24 V rail ✅ (DC-bias note O-11 stands) | prior review |
| R25/D7/R22 | status | ✅ | generic | — |

### Power — 3.3 V buck (AP63203)

| Ref | Part | Verdict | Key numbers | Source |
|-----|------|---------|-------------|--------|
| U1 | AP63203WU-7 | ⚠⚠ **two required edits** | Variant confirmed: AP63203 = **3.3 V fixed**, 2 A, VIN 3.8–32 V, 22 µA Iq, TSOT-26 (blocker #1 identity ✅). Real pinout (Diodes DS41326 + KiCad official lib): **FB=1, EN=2, VIN=3, GND=4, SW=5, BST=6** — welld symbol (EN=1, GND=2, FB=3, VIN=4) wrong on pins 1–4. **BST requires an external 100 nF cap to SW** ("connect a 100 nF ceramic capacitor between BST and SW"); the wiring doc left BST unconnected — the rail never starts. LCSC **C780769**. KiCad footprint name: `Package_TO_SOT_SMD:TSOT-23-6` | Diodes DS41326; KiCad lib `AP63200WU`/`AP63203WU`; LCSC C780769 |
| **C_BST_AP** | **100 nF 0402 (NEW)** | ⚠ add | BST(6) ↔ SW(5) bootstrap — new BOM row + schematic edit | Diodes DS41326 |
| L2 | CDRH4D22NP-4R7NC | ✅ | 4.7 µH; buck peak ≤ ~1 A at 2 A rating class; HP variant (CDRH4D22HPNP-4R7NC) Isat 2.2 A@20 °C same 4×4 mm if respun | Sumida CDRH4D22/HP DS |
| R_FBH/R_FBL | DNP | ✅ | Fixed-3.3 V part: FB ties to +3V3, divider stays DNP | Diodes DS41326 |
| R11/C9/C10/C11/C12/C16/C_BUCK | passives | ✅ | per DS CIN=10 µF | — |

### Power — 12 V boost (MT3608B)

| Ref | Part | Verdict | Key numbers | Source |
|-----|------|---------|-------------|--------|
| U8 | MT3608B | ✅ pin map confirmed | **SW=1, GND=2, FB=3, EN=4, IN=5, NC=6** — now confirmed by the KiCad official `MT3608` symbol (librarian-reviewed vs the Aerosemi PDF), agreeing with both prior reviews. Blocker #3 pin question closed; routine first-article continuity check only. FB ref 0.6 V matches R23/R24 math (12.06 V). EN-low shutdown current and switch-limit details remain bench/datasheet-PDF items | KiCad lib `MT3608` (DS: Aerosemi MT3608 via olimex) |
| C_BST | 100 nF on pin 6 | ✅ plan | Pin 6 = NC confirmed → cap is harmless; can be marked DNF at first-article | same |
| L1 | CDRH4D22NP-4R7NC | ✅ (warning stands) | Transient saturation during C20/C22 inrush acceptable at 5×10⁻⁵ duty (senior warning #6); HP variant is the drop-in upgrade | Sumida DS |
| D15 | SS34 | ✅ | 40 V > 12 V rail + margin | — |
| Q3 | AO3407 | ✅ | Vds −8.4 V, Vgs −8.4 V vs −30/±20 ✅ | AOS DS |
| Q4 | BSS123 | ✅ (O-3 stands) | Vgs(th) max 1.7 V at 3.3 V drive — works, thin margin; AO3400A substitution recommendation unchanged. Still no LCSC number in BOM | prior review |
| R23/R24/R27/R29/C19/C20/C22 | passives | ✅ | — | — |
| D11 | SMAJ13A | ⚠ LCSC | Part correct (13 V standoff > 12.06 V, Vc 21.5 V < 25 V caps). **C8057 could not be confirmed as SMAJ13A** — known-good: **C110519** (SMAJ13A-13-F, Diodes Inc) | LCSC C110519 |

### Battery divider / MCU / ADC

| Ref | Part | Verdict | Key numbers | Source |
|-----|------|---------|-------------|--------|
| Q2 | BSS123 | ✅ (O-3) | as Q4 | — |
| Q5 | AO3407 | ✅ | 8.4 V node vs −30 V/±20 V | AOS DS |
| R7/R8/R16/R26/C8 | passives | ✅ | C8 1 nF τ math unchanged | — |
| U6 | ESP32-C6-MINI-1U-H4 | ⚠ LCSC | Module real, in stock, ~$3.16. **LCSC number is C20627095**, not C2913202 | LCSC C20627095 |
| C13,C30–C33,C15,R12,R13,R15,C36,SW1,SW2,D4,R14 | ✅ | generic | — |
| U9 | ADS1115IDGST | ✅ | MSOP-10, C37593 = TI-genuine reel (O-6 sourcing note stands) | LCSC |
| FB1 | BLM18KG601SN1D | ⚠ footprint | **BLM18 = 0603 (1608 metric)**, but BOM row says 0402/`L_0402_1005Metric` — footprint/package mismatch. Fix row to 0603 (`L_0603_1608Metric`), or switch to BLM15AX601SN1D (0402). C76537 is the genuine Murata 0603 | Murata BLM18 series |
| R9/R10/R_DRDY C23/C24 | ✅ | R_DRDY add-to-schematic flag unchanged | — |

### Sensors — 4–20 mA and 1-Wire

| Ref | Part | Verdict | Key numbers | Source |
|-----|------|---------|-------------|--------|
| D9/D10 | ~~SMAJ3.3CA~~ → **SMAJ5.0A** | ⚠ **CHANGED** | SMAJ3.3CA IR = **800 µA max at VRWM 3.3 V** (soft knee; VBR min only 3.67 V, 1.67 V above the 2.0 V node; leakage roughly doubles per 10 °C). The blocker-#6 requirement (≤1 µA @ 2.0 V/60 °C) is not guaranteeable on datasheet limits → substitute **SMAJ5.0A** (VBR min 6.4 V → 2.0 V working point 4.4 V below the knee; Vc 9.2 V, R3/R5 + D1 still protect the ADS1115 pins; forward diode clamps negative transients). **ST SMAJ5.0A-TR, LCSC C98802** (Littelfuse/Vishay/FUXINSEMI alternates stocked). Schematic value edit required | Littelfuse/Vishay SMAJ DS; LCSC C98802 |
| D1, D12 | PRTR5V0U2X | ⚠⚠ symbol + LCSC | Real part: **SOT-143B, 4 pins: 1=GND, 2=I/O1, 3=I/O2, 4=VCC** (KiCad official symbol, footprint `Package_TO_SOT_SMD:SOT-143`). welld symbol is a 6-pin SOT-363 — wrong, replace. **BOM LCSC C2687116 is actually a UMW USBLC6-2SC6 clone** — real part is **C12333** (Nexperia PRTR5V0U2X,215, 40 k+ stock, ~$0.14–1.37 dep. qty) | KiCad lib `PRTR5V0U2X`; Nexperia DS; LCSC C12333 |
| R2/R4 | RG2012N-101-W-T1 | ✅ (O-10 stands) | 0.1 %/25 ppm hard spec; LCSC-stocked alternate approval unchanged | prior review |
| R3/R5/C3/C5/C4/C6/C34/C35 | ✅ | generic | — |
| R6/R28/R32/C7 | ✅ | generic | — |

### Connectors / TVS / misc

| Ref | Part | Verdict | Key numbers | Source |
|-----|------|---------|-------------|--------|
| J4–J7, J12 | Phoenix MC 1.5 G + STF plugs | ✅ | G-header/STF compatibility note re-confirmed by prior review | prior review |
| J10/J3/J8/J9 | headers/SMA | ✅ | KiCad standard footprints exist | — |
| TP1–TP15, SJ1–SJ5 | ✅ | — | — |
| Battery pack | Sinowatt GR 2S1P 3350 mAh + PCM | ❌ | Cell = SW18650-34MP (3350 mAh, 10 A discharge, NMC). **Pack-level PCM continuous-charge rating not publishable-source findable**: Sinowatt product page, distributor listings (Liion Wholesale, IMR, Fogstar) cover the bare cell only; the Fogstar cell-spec PDF is proxy-blocked. Cell-class norms (0.5C std charge ≈1.7 A) make 1.5 A co-charge plausible at cell level, but the PCM overcurrent limit must come from the pack vendor/datasheet — **blocker #7a stays open; ask the pack supplier directly** | searches 2026-07-14 |

---

## Issues — required actions

> **Status 2026-07-14 (same-day follow-up pass):** all eight schematic edits below are APPLIED and netlist-re-verified (393 pins / 78 nets / 0 mismatches). Remaining open: pack PCM charge rating (vendor inquiry) and the bench-verify list.

**Required schematic edits (flagged only — no .kicad_sch touched in this pass):**

1. **welld:AP63205WU symbol**: renumber to FB=1, EN=2, VIN=3, GND=4, SW=5, BST=6; rename
   to AP63203WU. As drawn today a netlist would swap FB/EN/VIN/GND.
2. **Add C_BST_AP 100 nF 0402 between U1 BST (6) and SW (5)** (new net `AP_BST`). Without
   it the high-side driver has no supply and +3V3 never starts.
3. **welld:USBLC6_2SC6 symbol**: renumber to 1=I/O1, 2=GND, 3=I/O2, 4=I/O2, 5=VBUS,
   6=I/O1.
4. **welld:PRTR5V0U2X symbol**: redraw as 4-pin SOT-143B (1=GND, 2=I/O1, 3=I/O2, 4=VCC);
   assign `Package_TO_SOT_SMD:SOT-143`.
5. **D9/D10 value**: SMAJ3.3CA → SMAJ5.0A.
6. **welld:IP2326_TBD footprint**: draw as QFN-24 4×4 mm P0.5 EP2.5×2.5 (KiCad standard
   `Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.6x2.6mm` fits).
7. **FB1 footprint**: 0402 → 0603 (`Inductor_SMD:L_0603_1608Metric`) for BLM18KG601SN1D.
8. **Cap value-field edits**: C28 10 µF **25 V**, C29 10 µF **25 V**, C_SYS1/C_SYS2 22 µF
   **25 V** (IP2326 datasheet: ">16 V required" on VIN/VSYS/VOUT caps).
9. **U1 footprint field**: `Package_TO_SOT_SMD:TSOT-23-6` (TSOT-26 land pattern), not
   SOT-23-6.

**BOM corrections applied in `bom_footprints.md` (this pass):**

- D1/D12 LCSC → **C12333**; U7 LCSC → **C77905**; U6 LCSC → **C20627095**;
  U1 LCSC → **C780769**; F2 → MF-MSMF250/16X-2 / **C210838** / 1812;
  D8/D14 LCSC → **C148223**; D11 LCSC → C110519 (C8057 unconfirmed);
  D9/D10 → SMAJ5.0A / C98802; L3 → SWPA5040S2R2NT; L_SOLAR → verified + JLCPCB C5151734;
  RT1/RT_SOLAR → SDNT1608X103F3950FTF; U12 package QFN24 4×4; FB1 0603; C_BST_AP row added.

**Recommendations (non-blocking):**

- **R-1 (M_SOLAR)**: −30 V AO3407 has ~23 % Vds margin over the 24 V clamped panel;
  switch-node ringing and a genuine SMAJ24CA clamp event (Vc ≤38.9 V) exceed it. A −40 V
  SOT-23 P-FET (SI2319CDS class) is a cheap robustness upgrade for M_SOLAR only. The
  CN3722 itself (30 V abs max) is the co-limiting device — carried warning #4 unchanged.
- **R-2 (F2 thermal)**: MF-MSMF250 hold derates to ≈1.75–2 A at 60 °C vs ≈1.9 A boost
  input at full charge — the RISET=120 k (0.75 A charge) fallback stays on the table if
  summer nuisance trips appear.
- **R-3 (L3)**: at full IP2326 capability (2 A charge) the datasheet BOM wants Isat >5 A /
  DCR <20 mΩ; SWPA5040S2R2NT (3.8 A/25 mΩ) is sized for our 1 A setpoint only. Never
  raise RISET above 90 k without resizing L3.
- **R-4**: order-time double-check of the two unconfirmed LCSC numbers kept in the BOM
  (D13 C2836474; anything DOWO-branded).

## Still open after this sweep

- Blocker #7a: pack PCM charge rating (ask Sinowatt/pack vendor).
- Bench items: IP2326 VOUT quiescent <10 µA (2g), weak-source behaviour (2h), BAT_STAT
  polarity (R38); CN3722 dark VCC quiescent; MT3608B EN-low shutdown current; co-charge
  CV handover (senior warning #3).
- U6 Espressif official symbol swap; SJ2–SJ5 bridged-variant swap (both carried).
