# KiCad 10 Setup Guide — ELI5

This guide walks you from opening KiCad to having a routable PCB with all components placed. You do the placement and routing; this just covers the setup steps.

---

## Step 0 — Before You Open KiCad

Download the Espressif KiCad library (needed for the ESP32-C6 module symbol and footprint):

```
git clone https://github.com/espressif/kicad-libraries
```

Remember where you put this folder — you will add it in Step 2.

Also download the GCT footprint for the USB-C connector (USB4135-GF-A) from:
`https://gct.co/connector/usb4135` → Downloads → KiCad

---

## Step 1 — Open the Project

1. Open **KiCad 10**
2. **File → Open Project**
3. Navigate to `hardware/pcb/` and open `welld.kicad_pro`

You will see the KiCad project manager with links to the schematic and PCB editor.

---

## Step 2 — Add the Espressif Library

Do this once before touching the schematic:

1. In the KiCad project manager, go to **Preferences → Manage Symbol Libraries**
2. Click the **+** button at the bottom
3. Set **Library Path** to the folder where you cloned the Espressif library (the `.kicad_sym` files)
4. Click **OK**
5. Repeat for **Preferences → Manage Footprint Libraries**, adding the Espressif footprint folder

---

## Step 3 — Open and Check the Schematic

Click **Schematic Editor** in the project manager.

The schematic has 4 sub-sheets:
- **power** — battery, USB-C charging, solar charger, buck converter, boost converter
- **mcu** — ESP32-C6 module, buttons, LED, decoupling
- **sensors** — ADS1115, 4-20mA protection chains, DS18B20
- **interfaces** — all screw terminal connectors, programming header, test points

### Important: the schematic has symbols but NO wires yet

The schematic files were originally auto-generated. They contain all the component symbols in the right sub-sheets, but **no wire connections, no net labels, and no junctions exist**. This means the schematic cannot produce a useful PCB netlist until you draw all the connections manually.

**Use `schematic_connections.md` as your wiring reference.** It lists every net by name and every component pin that belongs to it. Work through it net by net in the schematic editor.

The new symbols (R_FBH, R_FBL, R_DRDY, C_BST, C_BUCK) have already been added to the schematic files by script. You will see them when you open KiCad — they just need wiring.

> **2026-07-05 review:** R_FBH/R_FBL are now marked **DNP** (U1 changed to the fixed-3.3V AP63203WU — see Fix 1), C25 has been deleted, C16 is assigned as U1's VIN bulk cap, and the status LED moved to **GPIO14**. Several new components (D15, Q3, Q4, Q5, R15, R16, R25, R27, R29, C36, TP13) still need symbols added — see the resolution table at the end of `schematic_connections.md`.

---

### C25 and C16 — resolved (2026-07-05)

- **C25** was a duplicate of C_BST and has been **deleted** from power.kicad_sch.
- **C16** (10µF, right of U1) is now the U1 **VIN bulk cap**: wire it VBAT → C16 → GND next to C9/C10.

---

### Critical fixes you MUST wire in the schematic

The following components have been added to the schematic as symbols (already done). Now you need to **draw the wires** that connect them:

---

#### Fix 1 — U1 buck feedback (CRITICAL — updated 2026-07-05)

**The original fix was wrong.** AP63205WU is the **5V fixed** variant, and the 560k/124k divider assumed a 0.6V reference that no AP6320x part has. Any combination of the old parts would have over-volted the 3V3 rail and destroyed the ESP32.

U1 is now **AP63203WU (3.3V fixed)**:
1. Wire U1 **FB pin directly to the +3V3 output rail** (after L2) — fixed-output parts sense VOUT on this pin.
2. Leave **R_FBH / R_FBL as DNP** (they are already marked DNP in the schematic).
3. *Alternative:* if you fit the adjustable **AP63200WU** instead, change R_FBH to **390kΩ** and R_FBL to **124kΩ** (VFB = 0.8V → 3.32V) and clear the DNP flags.
4. **Verify the variant table in the Diodes datasheet before ordering** — this change was made without datasheet access (see `schematic_connections.md` → verification blockers).

---

#### Fix 2 — ADS1115 DRDY pull-up resistor (CRITICAL — DRDY interrupt will miss edges)

The ADS1115 ALERT/DRDY pin is open-drain and needs an external pull-up. Without it, the firmware intermittently misses the conversion-done interrupt.

**In the sensors sub-sheet, near U9:**
1. Add resistor **R_DRDY = 4.7kΩ 0402**
   - Connect one end to **+3V3**
   - Connect the other end to the **ADS_DRDY net** (the wire going to GPIO12)

---

#### Fix 3 — MT3608B boost topology (CRITICAL — updated 2026-07-05)

The boost was documented backwards (SW→L1→VOUT is a *buck* arrangement). Correct wiring:

1. **VBAT → Q3 (P-FET) → L1 pin 1; L1 pin 2 → U8 SW pin** (boost inductor goes on the *input* side)
2. **D15 (SS34): anode → SW node, cathode → VLOOP** — the MT3608 family is an async boost and needs this external rectifier (it was missing entirely)
3. **C_BST = 100nF between U8 BST pin and the SW node** (if pin 6 turns out to be NC on the real part, the fitted cap is harmless)
4. **Q4 (BSS123)**: gate → VBOOST_EN (GPIO5, with R27 100k pull-down), drain → Q3 gate (with R29 100k pull-up to VBAT), source → GND. Without Q3/Q4, VBAT−0.4V leaks through L1+D15 to the loop terminals permanently and drains the battery during sleep.

See the VLOOP section of `schematic_connections.md` for the full net list.

---

#### Fix 4 — C_BUCK output filter cap (WARNING — buck will have poor ripple)

**In the power sub-sheet, on the +3V3 rail after L2:**
1. Add **C_BUCK = 10µF 10V X5R 0805**
   - Connect across +3V3 and GND, on the output side of L2

---

### After making the fixes

Run the ERC: **Tools → Electrical Rules Checker → Run**

Expected remaining warnings are "pin not connected" for DNF components and some label warnings — these are fine. Fix any unexpected errors before continuing.

---

## Step 4 — Set Up the PCB Board

Click **PCB Editor** in the project manager.

### Board Setup (do this before importing the netlist)

Go to **File → Board Setup**:

**Stackup tab:**
- Layers: **2** (F.Cu + B.Cu)
- Board thickness: **1.6mm**
- Copper weight: **1oz (35µm)**

**Constraints tab (minimum values):**
| Setting | Value |
|---------|-------|
| Minimum clearance | 0.15mm |
| Minimum track width | 0.15mm |
| Minimum via drill | 0.3mm |
| Minimum via annular ring | 0.15mm |
| Minimum hole to hole | 0.25mm |

**Net Classes tab:**
Create these net classes after importing the schematic:

| Net Class | Clearance | Track width | Via drill |
|-----------|-----------|-------------|-----------|
| Default (+3V3, GND, signal) | 0.15mm | 0.2mm | 0.3mm |
| Power (VBAT, VLOOP, VUSB) | 0.2mm | 0.5mm | 0.6mm |
| RF (not needed — W1 pigtail handles RF, no RF PCB trace) | — | — | — |

Click **OK**.

---

## Step 5 — Draw the Board Outline

1. Select layer **Edge.Cuts** (in the dropdown on the right, or press `Ctrl+L` and pick it)
2. Use the **Rectangle tool** (press `R`) to draw your board outline
3. Click one corner, drag to the opposite corner, click again
4. The outline must be a **closed shape** — KiCad will warn you if it is not

The current enclosure expects something around 80×55mm but you decide the final size.

---

## Step 6 — Import the Netlist

This brings all your schematic components into the PCB editor.

1. Go to **Tools → Update PCB from Schematic** (or press `F8`)
2. A dialog appears showing components to add — click **Update PCB**
3. All components appear as a pile in the center of the screen — this is normal
4. Click **Close**

You now have all footprints loaded, connected by ratsnest (thin lines showing required connections). Start placing them using `placement_constraints.md` as your guide.

---

## Step 6b — Auto-Placement via Scripting Console (optional but saves hours)

Instead of manually arranging 80+ components from the pile, run the placement script:

1. Make sure you have done **Step 6** (imported the netlist via F8) first
2. Go to **Tools → Scripting Console** (opens a Python prompt at the bottom of the PCB editor)
3. In the scripting console, type:

```python
exec(open('/home/gh0stee/Projects/WellD/hardware/pcb/kicad_place_script.py').read())
```

4. Press Enter — all components move to their approximate target positions
5. The script prints a list of any references it couldn't find (warnings only)

After running the script:
- All components are placed in functional groups following `placement_constraints.md`
- U8 (MT3608B) and U9 (ADS1115) are ≥20mm apart ✓
- U7 (CN3722) and U6 (ESP32) are ≥15mm apart ✓
- Screw terminals are clustered on one long edge ✓

You still need to:
- Fine-tune component positions to eliminate courtyard overlaps
- Ensure L1 has no copper pour beneath it on either layer (MT3608B switching EMI)
- Verify J3 (SMA) and J13 (USB-C) are on different edges
- Route all traces manually (the script does not route)
- Add copper pours (GND fill, thermal islands for U7 and U12)

---

## Step 7 — Useful KiCad Shortcuts While Placing

| Key | Action |
|-----|--------|
| `G` | Grab and move a component (keeps ratsnest attached) |
| `R` | Rotate 90° |
| `E` | Edit properties of selected component |
| `F` | Flip to back copper layer |
| `X` | Start drawing a trace |
| `U` | Select entire connected trace |
| `D` | Delete |
| `Ctrl+Z` | Undo |
| `/` | Toggle 45° / free-angle routing |
| `Spacebar` | Clear selection |
| `` ` `` | Toggle ratsnest visibility |

---

## Step 8 — Copper Pours (GND Fill)

After placing and routing:

1. Select **F.Cu** layer
2. Press `A` → choose **Zone**
3. Click around the area you want filled, set net to **GND**
4. Press `B` to fill all zones
5. Repeat for **B.Cu**

Add thermal relief pours for U7 (CN3722) and U12 (TP5100) — see `placement_constraints.md` for sizes.

---

## Step 9 — DRC (Design Rule Check)

Before generating Gerbers, run the DRC:

1. **Tools → Design Rules Checker → Run DRC**
2. Fix all **Errors** (red) — these are real problems
3. Review **Warnings** (yellow) — some are acceptable (like courtyard overlaps on intentionally tight components)

Common false positives you can ignore:
- "Courtyard overlap" on thermal vias inside a copper pour island
- "Pad not connected" on DNF test points (TP1–TP15 are DNF pads, no component body)

Note: the placement script and older docs may still call the CC resistors R_CC1/R_CC2 (schematic: **R50/R51**) and the module caps C14a–C14d (schematic: **C13, C30–C33**).

---

## Step 10 — Generate Gerbers for PCBWay

1. **File → Fabrication Outputs → Gerbers (.gbr)**
2. Output folder: `hardware/pcb/gerbers/`
3. Check these layers: F.Cu, B.Cu, F.Mask, B.Mask, F.Silkscreen, B.Silkscreen, Edge.Cuts
4. Click **Plot**
5. Then click **Generate Drill Files** (same dialog)
6. Zip the `gerbers/` folder and upload to PCBWay

For PCBWay PCBA, also generate:
- **File → Fabrication Outputs → Component Placement (.pos)** — the CPL file
- Export BOM from schematic: **Tools → Generate BOM** — use the CSV plugin

---

## Things to Double-Check Before Sending to PCBWay

> **Schematic wiring checklist** — before generating Gerbers, verify in the schematic editor that every net listed in `schematic_connections.md` is wired. The "Components Still Needing Resolution" table at the end of that document must be cleared first.

- [ ] All nets in `schematic_connections.md` are wired (no floating symbols)
- [ ] C25 deleted ✓ / C16 wired as U1 VIN bulk
- [ ] U1 = AP63203WU with FB tied to +3V3 (R_FBH/R_FBL DNP) — or AP63200WU with 390k/124k fitted
- [ ] R_DRDY (4.7kΩ) wired: +3V3 → R_DRDY → ADS_DRDY net (→ GPIO12)
- [ ] Boost wired VBAT → Q3 → L1 → SW → D15 → VLOOP, with C_BST on BST↔SW
- [ ] C_BUCK (10µF 0805) wired: +3V3 rail (after L2) → C_BUCK → GND
- [ ] R33 = 590kΩ in schematic (already done — Vchg = 8.31V, safe for 2S Li-ion)
- [ ] R32 (DS18B20 33Ω series) is populated (not DNF — needed for cable runs)
- [ ] Status LED D4 wired to **GPIO14** (not GPIO13 — that is the factory-reset strap); TP13 wired to GPIO13
- [ ] New symbols added and wired: D15, Q3, Q4, Q5, R15, R16, R25, R27, R29, C36, TP13 (see resolution table in `schematic_connections.md`)
- [ ] Datasheet verification blockers in `schematic_connections.md` cleared (U1 variant, TP5100 replacement, MT3608B pinout, CN3722 package)
- [ ] ERC passes (Tools → Electrical Rules Checker) before generating netlist
- [ ] Board outline is on Edge.Cuts and is closed
- [ ] DRC passes with no errors
- [ ] All connector headers (J4–J7, J12) use the G-series (PCB-mount side)
- [ ] PCBWay order includes all BOM items from bom_footprints.md
- [ ] Field plugs (STF spring-cage, spring side) are on a separate order — NOT PCBWay-assembled
