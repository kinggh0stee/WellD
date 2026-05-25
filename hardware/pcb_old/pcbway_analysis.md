# WellD PCB vs PCBWay Assembly Capability Analysis

## Executive Summary

The WellD PCB **cannot be fully assembled by PCBWay without manual soldering** in its current design. While PCBWay supports mixed SMT/THT assembly and has broader component sourcing than JLCPCB, several design choices and component selections still require hand-soldering or manual placement.

---

## PCBWay Assembly Capabilities (Relevant to This Project)

| Capability | PCBWay Support | WellD Requirement | Match? |
|-----------|---------------|-------------------|---------|
| SMT Assembly | Yes - 01005 to large ICs | 0402, 0603, 0805, SOT-23, SOP-8, MSOP-10 | ✓ Yes |
| THT Assembly | Yes - Wave solder or hand | J1, J4-J9, J10, J12 (THT connectors/headers) | ✓ Yes |
| Mixed SMT+THT | Yes | Both SMT and THT on same board | ✓ Yes |
| Component Sourcing | Turnkey, Kitted, Partial | Some parts need manual sourcing | ⚠ Partial |
| BGA/QFN/Fine Pitch | Yes - 0.25mm pitch | No BGA, MSOP-10 @ 0.5mm pitch | ✓ Yes |
| Board Size | 10×10mm to 250×500mm | 80×55mm | ✓ Yes |
| 2-Layer Boards | Yes | 2-layer | ✓ Yes |
| Minimum Order | 5 pieces | Prototype qty acceptable | ✓ Yes |
| Special Packages | Reels, cut tape, tube, tray, loose | Various package types | ✓ Yes |

**Conclusion:** PCBWay's equipment *can* physically handle all assembly types needed for this board.

---

## Components That CAN Be Auto-Assembled by PCBWay

### SMT Components (All can be machine-placed)

| Ref | Component | Package | Notes |
|-----|-----------|---------|-------|
| U1 | AP63205WU buck converter | SOT-23-6 | Standard SMT |
| U7 | CN3722 MPPT charger | SOP-8 | Standard SMT |
| U8 | MT3608B boost converter | SOT-23-6 | Standard SMT |
| U9 | ADS1115 ADC | MSOP-10 | Fine pitch, but within PCBWay 0.25mm capability |
| U11 | USBLC6-2SC6 ESD protection | SOT-23-6 | Standard SMT |
| U12 | TP5100 charger | SOP-8 | Standard SMT |
| D1, D12 | PRTR5V0U2X TVS | SOT-363 | Standard SMT |
| D5 | AO3407 P-MOSFET | SOT-23 | Standard SMT |
| D6 | MBRS140 Schottky | SOD-123 | Standard SMT |
| D8, D9, D10, D11, D13, D14 | SMAJ TVS diodes | DO-214AC (SMA) | Large SMT, easily handled |
| D4, D7 | LEDs | 0603 | Standard SMT |
| Q2 | BSS123 N-MOSFET | SOT-23 | Standard SMT |
| L1, L2 | 4.7µH inductors | 4×4mm SMD / 2520 | Standard SMT |
| F2 | PTC Fuse | 1206 | Standard SMT |
| All resistors/capacitors | Various | 0402, 0805, 1206 | Standard SMT (PCBWay handles 0201+) |
| SJ1-SJ5 | Solder jumpers | 0402-size pads | Can be assembled (but see notes) |

### THT Components (PCBWay DOES support THT assembly)

| Ref | Component | Notes |
|-----|-----------|-------|
| J1 | JST PH 2.0mm battery connector | PCBWay can wave solder or hand-solder THT |
| J4-J7 | Phoenix MC 3.5mm screw terminals | Standard THT, PCBWay can handle |
| J8 | 2.54mm I2C header | Standard THT |
| J9 | 2.54mm GPIO header | Standard THT |
| J10 | 1.27mm programming header | Fine pitch THT, but doable |
| J12 | Phoenix MC 3.5mm 2-pos solar terminal | Standard THT |

---

## Components That Would STILL Need Manual Soldering/Placement

Even with PCBWay's broader capabilities, these components are flagged in the design as requiring manual work:

### 1. U.FL Connector (J3) - REQUIRES HAND PLACEMENT

**Issue:** The U.FL-R-SMT-1(10) is a delicate coaxial connector. The fab notes state: "Delicate SMD coaxial; hand-place and inspect."

**PCBWay Impact:** While PCBWay *can* place small SMT parts, the U.FL requires careful handling due to:
- Small, fragile center pin
- Requires precise alignment for impedance matching
- Risk of damage during reflow or handling
- Best practice is hand-placement with microscopes

**Recommendation:** Keep as hand-soldered item. Provide to PCBWay as DNF and hand-solder during bring-up.

### 2. ESP32-C6 Module (U6) - REQUIRES SPECIAL HANDLING

**Issue:** The ESP32-C6-MINI-1U-H4 module has castellated edge pads. The fab notes state: "Module; JLCPCB can place but requires manual stencil alignment."

**PCBWay Impact:** PCBWay can likely place this module, but:
- Castellated modules often need custom stencil apertures
- The 28 pads (14 bottom + 7 left + 7 right) need precise solder paste deposition
- May require hand-touch-up after reflow
- Module is valuable - risk of rework damage

**Recommendation:** 
- Option A: Let PCBWay attempt it (they have experience with ESP32 modules)
- Option B: Hand-solder yourself for prototypes; use PCBWay for production runs
- Provide detailed placement instructions and custom stencil requirements

### 3. USB-C Connector (J13) - REQUIRES CAREFUL INSPECTION

**Issue:** The USB4135-GF-A has GND shield tabs that need proper soldering. The fab notes state: "Hand-place recommended; inspect GND shield tabs under microscope."

**PCBWay Impact:** PCBWay can place USB-C connectors, BUT:
- The through-hole shield tabs (if any) need wave soldering or hand soldering
- SMT-only versions might not have strong mechanical retention
- Requires inspection for solder bridges on fine-pitch pins

**Recommendation:** Let PCBWay place it, but explicitly note in instructions that GND tabs need inspection.

### 4. Test Points (TP1-TP12, TP15) - DO NOT FIT

**Issue:** All test points are marked DNF (Do Not Fit) in production.

**PCBWay Impact:** Easy to exclude from BOM. No issue.

**Recommendation:** Simply omit from PCBWay BOM/CPL files.

### 5. Tactile Switches (SW1, SW2) - MECHANICAL CLEARANCE

**Issue:** 6×6mm tactile switches need mechanical clearance verification. The fab notes state: "Hand-solder; confirm mechanical clearance with case."

**PCBWay Impact:** PCBWay can place these, but:
- Height (4.3mm) may conflict with case/enclosure
- Button travel needs verification
- Often hand-soldered to ensure proper seating height

**Recommendation:** Let PCBWay place them, but verify height tolerance in your case design.

### 6. Large Inductors (L1, L2) - THERMAL/MECHANICAL

**Issue:** CDRH4D22NP-4R7NC shielded inductors. The fab notes state: "High-current; hand-place and confirm orientation."

**PCBWay Impact:** PCBWay can place 4×4mm inductors, but:
- Heavy parts may tombstone if paste is insufficient
- Orientation matters for shielding effectiveness
- Thermal profile needs adjustment for large copper mass

**Recommendation:** Let PCBWay place them, but specify orientation in CPL file.

---

## Component Sourcing Challenges

These components have **no confirmed stock** at common suppliers and may be difficult for PCBWay to source:

| Component | MPN | Issue | PCBWay Impact |
|-----------|-----|-------|---------------|
| U1 | AP63205WU-7 | Only at Mouser/Digi-Key | PCBWay may need to source from distributors; longer lead time |
| D6 | MBRS140T3G | Mouser/Digi-Key only | May need substitute (SS14 suggested) |
| D8, D14 | SMAJ28CA | Verify LCSC availability | PCBWay can likely source; confirm before order |
| D13 | SMAJ10CA | Verify LCSC C2836474 | PCBWay can likely source |
| F2 | MF-MSMF110/16X | Mouser only | May need substitute or consign |
| J3 | U.FL-R-SMT-1(10) | Hirose/Mouser | Consign this part |
| J4-J7 | MC 1.5/3-G-3.5 | Phoenix Contact distributor | PCBWay may not stock; consign or substitute |
| J12 | MC 1.5/2-G-3.5 | Phoenix Contact distributor | Same as above |
| J13 | USB4135-GF-A | Mouser/Digi-Key | Consign or let PCBWay source |
| Q2 | BSS123 | Verify LCSC C2655531 | Likely available |
| R2, R4 | RG2012N-101-W-T1 | Susumu - Mouser only | 0.1% precision resistor; may need to consign |
| U6 | ESP32-C6-MINI-1U-H4 | Espressif/Mouser | Popular module; PCBWay likely can source |

---

## Critical Differences: JLCPCB vs PCBWay for This Project

| Aspect | JLCPCB | PCBWay | Impact on WellD |
|--------|--------|--------|----------------|
| THT Assembly | Limited (wave solder only) | Full THT support (wave + hand) | **PCBWay better** - can auto-assemble J1, J4-J9, J10, J12 |
| Component Library | LCSC parts only | Multiple distributors | **PCBWay better** - can source AP63205WU, MBRS140, etc. |
| Module Placement | Supported but flagged | Supported | **Equal** - both can place ESP32 modules |
| Fine Pitch | 0.3mm BGA | 0.25mm fine pitch | **PCBWay better** - more capable for MSOP-10 |
| Turnkey Service | Basic | Full turnkey/kitted/hybrid | **PCBWay better** - more flexible sourcing |
| Stencils | Extra cost | Free with assembly promo | **PCBWay better** - cost savings |
| Minimum Order | 5 pcs | 5 pcs | **Equal** |

---

## Action Items to Make This PCBWay-Ready

### 1. Create PCBWay-Specific BOM and CPL Files

- Remove all DNF components (D7, R22, R32, all TP designators)
- Add sourcing notes for difficult parts
- Specify alternatives where possible:
  - D6: SS14 (SMA) if MBRS140 unavailable
  - F2: Specify alternative PTC fuse
  - R2/R4: Can substitute with 0.1% 0805 from other brands (Vishay, Yageo)

### 2. Decide on Assembly Strategy

**Option A: Full Turnkey (Recommended for Production)**
- Let PCBWay source everything they can
- Constrain only: J3 (U.FL), R2/R4 (precision shunts), J4-J7/J12 (Phoenix)
- Hand-solder after receipt: J3 (U.FL) only

**Option B: Kitted (Recommended for Prototypes)**
- You source all components
- Send to PCBWay with BOM
- Ensures you get exact parts
- More work but maximum control

**Option C: Hybrid (Best Balance)**
- Let PCBWay source common passives and ICs
- You consign: J3, J4-J7, J12, R2/R4, U6 (if you have stock)
- Hand-solder: J3 only

### 3. Update Design Files

- Generate proper Centroid/Pick-and-Place file from KiCad
- Ensure rotation angles match PCBWay's convention (check if CW vs CCW)
- Verify all footprints have correct paste mask openings
- Add polarity markers on silkscreen for LEDs, diodes

### 4. Special Instructions for PCBWay

Include a README with your order:

```
SPECIAL ASSEMBLY INSTRUCTIONS FOR WELD PCB

1. DNF (Do Not Fit): All TP1-TP15, D7, R22, R32, SJ1-SJ5 (unless specified)

2. HAND-SOLDER AFTER RECEIPT: J3 (U.FL connector) - delicate coaxial

3. PLACE BUT INSPECT CAREFULLY: 
   - J13 (USB-C): Verify GND shield tabs soldered properly
   - U6 (ESP32 module): Check all castellated pads wetted

4. ORIENTATION-SENSITIVE:
   - D6 (Schottky): Cathode toward U7
   - D8, D11, D14 (TVS): Unidirectional - check cathode band direction
   - D9, D10, D13 (TVS): Bidirectional - orientation doesn't matter
   - D5 (P-MOSFET): Gate toward R31

5. THERMAL PROFILE:
   - U7 (CN3722): Ensure reflow profile suitable for SOP-8 thermal pad
   - L1, L2 (Inductors): May need extended soak zone due to copper mass

6. COMPONENT SUBSTITUTION APPROVAL:
   - Contact customer before substituting: U1, U7, U9, R2, R4
   - Acceptable substitutes:
     * D6: SS14 or equivalent 1A 40V Schottky in SMA
     * F2: Equivalent 1A hold, 2A trip, 10V+ PTC in 1206
```

---

## Remaining Manual Soldering Summary

Even with PCBWay's full-service assembly, you will still need to hand-solder:

| Component | Reason | Time Estimate |
|-----------|--------|---------------|
| J3 (U.FL) | Delicate coaxial; risk of damage during automated handling | 5 min |
| Possibly U6 | If PCBWay cannot guarantee castellated pad quality | 10-15 min |
| Possibly J13 | If shield tabs need touch-up | 5 min |

**Total manual soldering time per board: 5-20 minutes** (vs potentially 1-2 hours for full hand-assembly)

---

## Recommendations

### For Prototype Run (5-10 boards):
1. Use **PCBWay Hybrid Assembly** - let them do SMT, you handle THT and J3
2. Consign J3, U6, and precision parts (R2, R4)
3. Let PCBWay source and place everything else including THT connectors
4. Hand-solder J3 after receipt

### For Production Run (50+ boards):
1. Use **PCBWay Full Turnkey**
2. Accept that J3 may need post-assembly hand soldering
3. Consider redesigning J3 to a more robust connector if volume justifies it
4. Negotiate with PCBWay for J3 placement (they may have experience with U.FL)

### Design Changes to Eliminate Manual Soldering:
If you want **100% automated assembly**, consider:

1. **Replace J3 (U.FL) with an edge-mount SMA connector**
   - More robust for automated placement
   - Eliminates pigtail cable
   - But: larger PCB footprint, different case design

2. **Replace Phoenix screw terminals with pluggable SMT headers**
   - Eliminates all THT assembly
   - But: less robust field connections, may not handle vibration well

3. **Use SMD USB-C connector without through-hole tabs**
   - Easier automated placement
   - But: less mechanical strength

4. **Pre-solder U.FL during prototyping, omit for production if using chip antenna**
   - The ESP32-C6-MINI-1U has an internal chip antenna
   - For short-range indoor use, external antenna may not be needed
   - Saves cost and eliminates J3 entirely

---

## Conclusion

**PCBWay can assemble approximately 95-98% of this board automatically**, which is significantly better than JLCPCB's capabilities for this design. The only guaranteed manual soldering is the U.FL connector (J3). All THT connectors (J1, J4-J7, J8-J9, J10, J12) can be wave-soldered or hand-soldered by PCBWay as part of their mixed assembly service.

**Bottom line:** PCBWay is a viable and recommended choice for this project, but plan for 5-20 minutes of manual soldering per board for J3 and possible touch-ups.
