# WellD PCB — PCBWay 100% Automated Assembly Instructions

## Goal: Zero Manual Soldering

This document configures the WellD PCB for **fully automated assembly by PCBWay**.
Every component is machine-placed and soldered. You receive boards that are ready
for firmware flashing and enclosure assembly — no soldering iron required.

---

## What Changed from the JLCPCB Version

| Item | JLCPCB Approach | PCBWay Approach (This File) |
|------|----------------|---------------------------|
| J3 (Amphenol 132289 SMA edge-launch) | Hand-solder recommended | **Machine-placed** SMD reflow; SMA male port flush to board edge |
| W1 (U.FL-to-SMA pigtail, ~50mm RG178) | N/A | **PCBWay hand-attaches** after reflow — not pick-and-place; U.FL end snaps to ESP32 module, SMA male end connects to J3 |
| THT connectors (J1, J4-J10, J12) | Exclude from SMT; hand-solder later | **Included in mixed assembly** (wave + reflow) |
| SW1, SW2 (tactile switches) | Hand-solder for clearance check | **Machine-placed** — verify case clearance at design stage |
| L1, L2 (power inductors) | Hand-place for orientation | **Machine-placed** — orientation in CPL file |
| U6 (ESP32 module) | Manual stencil alignment | **Machine-placed** — castellated pads are standard for PCBWay |
| SJ2, SJ3 (solder jumpers) | Hand-bridge or omit | **Machine-bridged during assembly** |

---

## Files to Submit to PCBWay

1. **Gerbers**: `hardware/pcb/gerbers/welld-*.gbr` + drill files (same as JLCPCB)
2. **BOM**: `hardware/pcb/pcbway_bom.csv` (this directory)
3. **CPL / Centroid**: `hardware/pcb/pcbway_cpl.csv` (this directory)
4. **Instructions**: Paste the text block below into the PCBWay order comments

---

## Paste This Into Your PCBWay Order

```
SPECIAL ASSEMBLY INSTRUCTIONS — WELD PCB — 100% AUTOMATED

1. SOLDER JUMPERS (bridge during assembly):
   - SJ2: BRIDGE with solder (connects VLOOP bus)
   - SJ3: BRIDGE with solder (enables status LED)
   - SJ1, SJ4, SJ5: DO NOT POPULATE

2. DO NOT FIT (omit entirely):
   - All test points: TP1, TP2, TP3, TP4, TP5, TP6, TP7, TP8, 
     TP9, TP10, TP11, TP12, TP14, TP15
   - D7 (solar charge LED)
   - R22 (solar LED series resistor)
   - R32 (DS18B20 series protection — DNF by design)

3. SMA EDGE-LAUNCH CONNECTOR — J3 (Amphenol 132289):
   - SMD reflow on F.Cu; mount flush to bottom board edge
   - Signal pad (pin 1) carries net RF_ANT; shell pads (pin 2) to GND
   - AOI inspect solder fillet on all three pads after reflow
   - Provide in tape/reel or bulk; standard SMT placement force acceptable

4. ANTENNA PIGTAIL — W1 (U.FL-to-SMA-male, ~50mm RG178):
   - NOT pick-and-place — attach by hand AFTER reflow and AOI
   - Step 1: Snap U.FL female connector onto ESP32-C6-MINI-1U module U.FL port (top-side, on-module)
   - Step 2: Route ~50mm RG178 cable along board surface toward J3 at bottom board edge
   - Step 3: Mate SMA male plug on pigtail with J3 (Amphenol 132289 receptacle) — thread finger-tight
   - NOTE: J3 is the PCB-mounted SMA female receptacle; the rubber-duck antenna screws onto J3 from outside the enclosure. The pigtail W1 carries the RF signal internally from the ESP32 module to J3.
   - Secure cable with a small cable tie or adhesive dot to prevent vibration stress on U.FL snap
   - Include W1 in PCBWay "value-added services" / manual assembly step; specify MPN Taoglas CAB.100.07.0050B or equivalent (50mm RG178 U.FL female to SMA male)

5. MODULE PLACEMENT — U6 (ESP32-C6-MINI-1U-H4):
   - Castellated LCC pads on 3 sides (28 total pads)
   - Verify all pads fully wetted under microscope
   - Check for solder bridges between adjacent castellations

6. THT CONNECTORS — Mixed Assembly:
   - J1 (JST PH 2-pin): Wave or selective solder
   - J4, J5, J6, J7 (Phoenix 3-pos 3.5mm): Wave or selective solder  
   - J8 (2.54mm 1x4), J9 (2.54mm 1x8): Wave or selective solder
   - J10 (1.27mm 1x6 SMD): Reflow + inspect
   - J12 (Phoenix 2-pos 3.5mm): Wave or selective solder
   - J13 (USB-C): Reflow SMT pins, then wave/solder shield tabs

7. ORIENTATION-SENSITIVE COMPONENTS:
   - D6 (MBRS140 SOD-123): Cathode band toward U7 (CN3722 VIN)
   - D8, D14 (SMAJ28CA): Bidirectional — band orientation irrelevant
   - D9, D10, D13 (SMAJ3.3CA, SMAJ10CA): Bidirectional
   - D11 (SMAJ13A): Unidirectional — cathode band toward VLOOP rail
   - D5 (AO3407 SOT-23): Gate toward R31 / GND side
   - U7 (CN3722 SOP-8): Pin 1 dot at top-left per footprint
   - U8 (MT3608B SOT-23-6): Pin 1 dot at top-left per footprint
   - U9 (ADS1115 MSOP-10): Pin 1 dot at top-left per footprint
   - U12 (TP5100 SOP-8): Pin 1 dot at top-left per footprint
   - D4 (LED 0603): Cathode toward R14 / positive voltage side
   - D7 (LED 0603): Omit — DNF

8. THERMAL MANAGEMENT:
   - U7 (CN3722): SOP-8 with thermal vias under body. Ensure reflow 
     profile allows adequate heat transfer to ground plane.
   - L1 (4×4mm shielded inductor): No copper pour directly under 
     inductor body on either layer.

9. COMPONENT SUBSTITUTION POLICY:
   - APPROVAL REQUIRED BEFORE SUBSTITUTION:
     * U1 (AP63205WU) — Diodes Inc buck converter
     * U7 (CN3722) — MPPT solar charger
     * U9 (ADS1115IDGST) — Texas Instruments ADC
     * R2, R4 (RG2012N-101-W-T1) — Susumu 0.1% precision shunts
     * U6 (ESP32-C6-MINI-1U-H4) — Espressif module
     * W1 (pigtail cable) — exact MPN or equivalent 50mm RG178 U.FL(f)-SMA(m)
   
   - ACCEPTABLE SUBSTITUTES (notify but no approval needed):
     * W1: Amphenol 095-850-198-100 or TE 2118651-1 if Taoglas CAB.100.07.0050B unavailable
     * D6: SS14 (SMA) or equivalent 1A 40V Schottky
     * F2: Equivalent 1A hold / 2A trip PTC fuse, 1206, ≥10V
     * L1, L2: Any 4.7µH ≥1A shielded SMD inductor, 4×4mm or 2520
     * C20: 22µF 16V 1206 X5R (any major brand)
     * Passives (0402/0805): Any A-brand (Murata, TDK, Yageo, Samsung)

10. CONSIGNED PARTS (customer will supply):
   [ ] J3 (Amphenol 132289) — Mouser 523-132289
   [ ] W1 (Taoglas CAB.100.07.0050B pigtail) — Taoglas or Mouser; supply to PCBWay for manual attachment
   [ ] R2, R4 (RG2012N-101-W-T1) — Susumu 0.1%, Mouser
   [ ] U6 (ESP32-C6-MINI-1U-H4) — Espressif, Mouser
   [ ] (Optional) J4-J7, J12 (Phoenix terminals) — if PCBWay cannot source

11. QUALITY REQUIREMENTS:
    - AOI after reflow for all SMT components
    - X-Ray not required (no BGA)
    - 100% electrical test (flying probe) after assembly
    - Visual inspection under 10× magnification for U6 castellations
    - Verify W1 pigtail U.FL connection is fully snapped (audible click); verify SMA male is hand-tight on J3
    - Sample photos of first article before full production run
```

---

## Consignment Strategy (Recommended: Hybrid)

For **prototypes (5-10 units)**, we recommend **hybrid assembly**:

| Component | Source | Why |
|-----------|--------|-----|
| Passives, common ICs | PCBWay turnkey | Cheaper, no MOQ issues |
| U6 (ESP32 module) | **Consigned** | High value; you control exact revision |
| J3 (Amphenol 132289 SMA edge-launch) | **Consigned** | Specific Amphenol RF part; confirm PCBWay can source or consign from Mouser 523-132289 |
| W1 (Taoglas CAB.100.07.0050B pigtail) | **Consigned** | Cable assembly — not a PCBWay stock SMD part; supply for manual attachment step |
| R2, R4 (0.1% shunts) | **Consigned** | Precision critical; exact MPN required |
| J4-J7, J12 (Phoenix) | PCBWay turnkey or consign | PCBWay can usually source; confirm first |

**Total consigned parts: 5-7 lines.** Everything else is turnkey.

---

## Board Received from PCBWay — What You Do

1. **Visual inspection** — check J3 SMA solder joints, USB-C shield tabs, ESP32 castellations, W1 pigtail connections (U.FL snap + SMA thread)
2. **Flash firmware** via J10 UART header (see `hardware/ASSEMBLY.md` section 7)
3. **Install into case** — screw terminals, thread rubber-duck antenna onto J3 from outside enclosure, battery (see `hardware/ASSEMBLY.md`)
4. **Commission Zigbee** — pair with coordinator

**No soldering required.**

---

## If Something Goes Wrong

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| W1 U.FL won't snap onto module | Module U.FL port obstructed or misaligned | Clear obstruction; align connector squarely before pressing |
| Poor RF range | W1 SMA male loose on J3 | Tighten SMA male finger-tight; inspect J3 solder joints |
| J3 pad lifted / no solder | Reflow issue on edge-launch connector | Rework J3 with hot air + solder; verify RF_ANT pad continuity |
| No 3.3V rail | U1 not soldered properly | Reflow U1 (AP63205) with hot air |
| USB-C loose | Shield tabs not soldered | Touch up with iron |
| Zigbee won't pair | U6 castellation bridge | Inspect under microscope, rework if needed |

These are **rare** with proper instructions — we've specified AOI and visual checks to catch them.

---

## Comparison: What Manual Work Remains

| Task | JLCPCB (Old) | PCBWay (This Config) |
|------|-------------|---------------------|
| Solder all SMT | Done by JLCPCB | Done by PCBWay |
| Solder all THT | Hand-solder 20+ joints | Done by PCBWay |
| Solder J3 (Amphenol 132289 SMA) | Hand-solder | Done by PCBWay (SMD reflow) |
| Attach W1 pigtail (U.FL snap + SMA thread) | N/A | Done by PCBWay (manual value-add step) |
| Bridge SJ2, SJ3 | Hand-bridge | Done by PCBWay |
| Flash firmware | You | You |
| Thread rubber-duck antenna onto J3 | You | You (at install time) |
| Install in case | You | You |
| **Total solder time** | **1-2 hours/board** | **0 minutes** |

---

## KiCad-to-PCBWay Coordinate Mapping

The `pcbway_cpl.csv` in this directory uses **KiCad native coordinates** (mm, origin at top-left of page, Y increases downward). PCBWay's online quote tool automatically handles standard KiCad CPL format. If you use a different format, convert with:

```python
# PCBWay expects: Designator, X, Y, Layer, Rotation
# KiCad outputs:  Designator, X, Y, Rotation (implicit Top layer)
# For WellD, all components are on Top layer — just add "Top" column.
```

The provided `pcbway_cpl.csv` already has the correct format.

---

## Validation Checklist Before Ordering

- [ ] `pcbway_bom.csv` excludes: all TP, D7, R22, R32, SJ1, SJ4, SJ5
- [ ] `pcbway_bom.csv` includes W1 (Taoglas CAB.100.07.0050B pigtail) as consigned manual-attach item
- [ ] `pcbway_cpl.csv` includes every SMT/THT line item from BOM (W1 cable assembly is NOT in CPL — attach by hand)
- [ ] J3 (Amphenol 132289) net RF_ANT connects to ESP32-C6-MINI-1U U.FL port via W1 pigtail
- [ ] Gerber zip includes: F.Cu, B.Cu, F.Mask, B.Mask, F.Paste, F.SilkS, Edge.Cuts, PTH.drl, NPTH.drl
- [ ] PCBWay order comment includes the 11-point instruction block above
- [ ] Consignment parts ordered and in-hand (if doing hybrid): J3, W1, R2/R4, U6
- [ ] Case design: rubber-duck antenna access hole aligns with J3 position on bottom board edge (X=40mm from left edge)
- [ ] Case design verified for SW1/SW2 height clearance (4.3mm + board thickness)
- [ ] First article photos requested; verify W1 cable routing does not obstruct any component

---

*gh0stee.com — WellD — Zero-Solder Assembly Config*
