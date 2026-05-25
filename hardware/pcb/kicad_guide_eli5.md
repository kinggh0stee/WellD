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

---

### Resolving C25 and C16 before wiring

Before you start adding wires, sort out two ambiguous components in the power sub-sheet:

| Symbol | Where | What to do |
|--------|-------|------------|
| **C25** (100nF, lower area near U8) | power.kicad_sch | Either: wire it as C_BST (BST pin 6 → SW node) and **delete the new C_BST symbol**, or delete C25 if it's not needed |
| **C16** (10µF, right of U1) | power.kicad_sch | Either: rename it to C_BUCK and **delete the new C_BUCK symbol**, or delete C16 if it has no purpose |

If you use the existing C25/C16, just delete the new duplicate. If you delete C25/C16, use the new symbols.

---

### Critical fixes you MUST wire in the schematic

The following components have been added to the schematic as symbols (already done). Now you need to **draw the wires** that connect them:

---

#### Fix 1 — AP63205 output voltage divider (CRITICAL — board won't work without this)

The 3.3V buck converter (U1, AP63205) has no feedback divider. Without it, the output voltage is undefined and will destroy the ESP32 on first power-on.

**In the power sub-sheet, near U1:**
1. Add resistor **R_FBH = 560kΩ 1% 0402**
   - Connect one end to the **+3V3 output net** (VOUT of AP63205)
   - Connect the other end to the **FB pin** of U1
2. Add resistor **R_FBL = 124kΩ 1% 0402**
   - Connect one end to the **FB pin** of U1 (same node as R_FBH bottom)
   - Connect the other end to **GND**

This sets VOUT = 0.6 × (1 + 560/124) = **3.31V**. ✓

---

#### Fix 2 — ADS1115 DRDY pull-up resistor (CRITICAL — DRDY interrupt will miss edges)

The ADS1115 ALERT/DRDY pin is open-drain and needs an external pull-up. Without it, the firmware intermittently misses the conversion-done interrupt.

**In the sensors sub-sheet, near U9:**
1. Add resistor **R_DRDY = 4.7kΩ 0402**
   - Connect one end to **+3V3**
   - Connect the other end to the **ADS_DRDY net** (the wire going to GPIO12)

---

#### Fix 3 — MT3608B bootstrap capacitor (CRITICAL — boost converter may fail at low battery)

The MT3608B requires a 100nF capacitor from BST pin (pin 6) to the SW node for its gate driver circuit.

**In the power sub-sheet, near U8:**
1. Find if **C_BST** (100nF) is already connected from U8 pin 6 (BST) to the SW node
2. If it is missing or connected to GND instead of SW: add/fix **C_BST = 100nF 0402**
   - One end: U8 pin 6 (BST)
   - Other end: U8 SW node (the same net as L1 pin 1)

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
- [ ] C25 / C16 ambiguity resolved (see "Resolving C25 and C16" section above)
- [ ] R_FBH (560kΩ) and R_FBL (124kΩ) wired: +3V3 → R_FBH → FB → R_FBL → GND
- [ ] R_DRDY (4.7kΩ) wired: +3V3 → R_DRDY → ADS_DRDY net (→ GPIO12)
- [ ] C_BST (100nF) wired: U8 BST pin6 → C_BST → U8 SW pin3 node
- [ ] C_BUCK (10µF 0805) wired: +3V3 rail (after L2) → C_BUCK → GND
- [ ] R33 = 590kΩ in schematic (already done — Vchg = 8.31V, safe for 2S Li-ion)
- [ ] R32 (DS18B20 33Ω series) is populated (not DNF — needed for cable runs)
- [ ] ERC passes (Tools → Electrical Rules Checker) before generating netlist
- [ ] Board outline is on Edge.Cuts and is closed
- [ ] DRC passes with no errors
- [ ] All connector headers (J4–J7, J12) use the G-series (PCB-mount side)
- [ ] PCBWay order includes all BOM items from bom_footprints.md
- [ ] Field plugs (STF spring-cage, spring side) are on a separate order — NOT PCBWay-assembled
