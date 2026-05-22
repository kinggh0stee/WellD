# WellD PCB — JLCPCB Fabrication Notes

## Board Specifications

| Parameter | Value |
|-----------|-------|
| Dimensions | 80 × 55 mm |
| Layers | 2 (F.Cu + B.Cu) |
| Board thickness | 1.6 mm |
| Copper weight | 1 oz (35 µm) both layers |
| Surface finish | ENIG (recommended) or HASL |
| Solder mask | Green (both sides) |
| Silkscreen | White, front only |
| Min track width | 0.2 mm (design rule) |
| Min clearance | 0.2 mm (design rule) |
| Via drill | 0.4 mm standard (0.6 mm for thermal vias under U7) |
| Via pad | 0.8 mm standard (1.0 mm for thermal vias under U7) |
| Min annular ring | 0.2 mm (0.4 mm pad minus 0.4 mm drill / 2 = 0.2 mm) |
| Impedance control | Not required |
| Controlled depth drilling | Not required |

## Stack-up

```
Top silkscreen (white)
Top solder mask (green)
F.Cu — 1 oz copper
FR4 core — 1.51 mm
B.Cu — 1 oz copper
Bottom solder mask (green)
Total: 1.6 mm
```

No inner layers. Standard JLCPCB 2-layer FR4, no impedance control needed.
The 2.4 GHz Zigbee RF path is external (U.FL coax → SMA bulkhead → antenna);
the on-board RF trace from U6 ESP32-C6-MINI-1U to J3 U.FL is inside the module
itself — no controlled-impedance trace on the PCB.

## Copper Pour / Board Edge Clearance

- No copper pour (flood fill) is placed in the PCB file — all connections are
  routed as point-to-point tracks or handled by the custom Gerber generator.
- The two GND zone polygons (GND_THERMAL_U7 and GND_THERMAL_U7_B) covering
  the 10×10 mm area under U7 (CN3722) are the only copper regions; they are
  bounded well within the board (55–65 mm X, 5–15 mm Y) with no overlap of
  the Edge.Cuts boundary.
- Board edge to nearest copper: mounting holes are at (3.5, 3.5) and the
  largest pad clearance to any edge is approximately 1.5 mm at the screw
  terminal connectors (J4–J7, J12) on the top edge and USB-C connector (J13)
  on the left edge. JLCPCB standard requires ≥0.3 mm; all pads clear this.
- D11 (SMAJ13A) TVS was corrected from (78.0, 6.0) to (74.0, 6.0). The
  original position placed the anode pad right edge at 81.1 mm — 1.1 mm
  outside the 80 mm board edge. After correction the anode right edge is at
  77.1 mm, giving 2.9 mm clearance. This fix is in welld.kicad_pcb,
  generate_gerbers.py, and jlcpcb_cpl.csv.

## Test Points

All test points (TP1–TP12, TP15) are 1.0 × 1.0 mm SMD pads. They are DNF
(Do Not Fit) in production — leave unsoldered. They are present on the paste
and mask layers for optional probing during board bring-up.

Do NOT instruct JLCPCB to assemble test points. Exclude all TP designators
from the PCBA BOM and CPL files when ordering assembly.

## Components Flagged for Hand-Soldering or Manual Sourcing

### Hand-solder at board bring-up (not PCBA)

| Ref | Part | Reason |
|-----|------|--------|
| J1 | JST PH 2.0mm 2-pin (B2B-PH-K-S) | THT; polarity-critical — verify pin 1 = BAT+ before mating |
| J3 | U.FL-R-SMT-1(10) | Delicate SMD coaxial; hand-place and inspect |
| J4–J7 | Phoenix MC 3.5mm 3-pos screw terminals | THT; field-connection; wave solder or hand |
| J8, J9 | 2.54mm pin headers | THT; hand-solder |
| J10 | 1.27mm 6-pin prog header | SMD or THT depending on variant; hand-solder |
| J12 | Phoenix MC 3.5mm 2-pos solar terminal | THT; hand-solder |
| J13 | USB4135-GF-A USB-C | Hand-place recommended; inspect GND shield tabs under microscope |
| L1, L2 | CDRH4D22NP-4R7NC 4.7µH inductor | High-current; hand-place and confirm orientation |
| SW1, SW2 | 6×6mm tactile switches | Hand-solder; confirm mechanical clearance with case |
| U6 | ESP32-C6-MINI-1U-H4 | Module; JLCPCB can place but requires manual stencil alignment |

### Manual sourcing required (no confirmed LCSC stock)

| Ref | Part | MPN | Source |
|-----|------|-----|--------|
| U1 | AP63205WU | AP63205WU-7 | Mouser / Digi-Key |
| D6 | MBRS140T3G Schottky | MBRS140T3G | Mouser / Digi-Key; alt SS14 |
| D8, D14 | SMAJ28CA 28V TVS | SMAJ28CA | Mouser / Digi-Key; verify LCSC availability |
| D13 | SMAJ10CA 10V TVS | SMAJ10CA | Mouser / LCSC C2836474 (verify variant) |
| F2 | MF-MSMF110/16X PTC | MF-MSMF110/16X | Mouser |
| J3 | U.FL receptacle | U.FL-R-SMT-1(10) | Mouser (Hirose) |
| J4–J7 | Phoenix MC 3.5mm headers | MC 1.5/3-G-3.5 | Phoenix Contact distributor |
| J12 | Phoenix MC 3.5mm 2-pos | MC 1.5/2-G-3.5 | Phoenix Contact distributor |
| J13 | USB4135-GF-A | USB4135-GF-A | Mouser / Digi-Key (GCT) |
| Q2 | BSS123 N-ch MOSFET | BSS123 | Mouser or LCSC C2655531 (verify) |
| R2, R4 | 100Ω 0.1% 0805 shunt | RG2012N-101-W-T1 | Mouser (Susumu) |
| U6 | ESP32-C6-MINI-1U-H4 | ESP32-C6-MINI-1U-H4 | Espressif direct or Mouser |

## Special Instructions for JLCPCB

1. **Gerber set**: upload `hardware/pcb/gerbers/` zip. Layers:
   - F.Cu, B.Cu — copper
   - F.Mask, B.Mask — solder mask
   - F.Paste — SMT stencil
   - F.SilkS — silkscreen
   - Edge.Cuts — board outline
   - PTH.drl, NPTH.drl — drill files (Excellon metric)

2. **PCBA**: Use `jlcpcb_bom.csv` and `jlcpcb_cpl.csv`. Exclude all DNF
   components (D7, R22, R32, all TP designators) from the assembly order.
   Exclude THT components (J1, J4–J9, J10, J12) from SMT assembly.

3. **Mounting holes**: Four M3 NPTH (non-plated) holes at corners — drill only,
   no copper ring. Diameter 3.2 mm.

4. **Stencil**: Order SMT stencil for top side only. Stencil thickness 0.12 mm
   recommended for mixed 0402/0805/MSOP-10 population. No bottom-side paste.

5. **D11 placement corrected**: D11 (SMAJ13A TVS) has been moved from (78.0, 6.0)
   to (74.0, 6.0) to resolve a DRC violation where the anode pad extended 1.1 mm
   outside the right board edge. Anode pad right edge is now at 77.1 mm,
   clearance 2.9 mm. This is already reflected in the Gerber files.

6. **Surface finish**: ENIG preferred for J10 (1.27mm fine-pitch header) and
   J3 (U.FL). HASL acceptable for prototype runs.

7. **PCB colour**: Green solder mask. White silkscreen.

## Critical Notes for Assembly House

- U7 (CN3722) thermal pad: GND copper zone (GND_THERMAL_U7) with thermal
  relief stitching vias (1.0mm pad / 0.6mm drill, 4× at corners) ties the
  exposed pad to back-side ground plane. Ensure via-in-pad is acceptable or
  use tent-and-fill vias.
- R7 = 330kΩ (NOT 100kΩ from previous 1S design). Battery divider ratio is
  4.3× for 2S pack (6.0–8.4V → ≤2.0V at ADS1115).
- R23 = 1.9MΩ (E96: 1.91MΩ). MT3608B boost target is 12.0V. Do not substitute
  with old 1.1MΩ value (that was for TPS61023 Vref=0.5V).
- C17 = 10µF 25V (CN3722 VIN cap). JLCPCB substitution must be ≥25V rated.
- Battery connector J1 polarity: pin 1 = BAT+ (red). Mismatch will bypass D5
  reverse-polarity protection via the body diode and may damage the board.
