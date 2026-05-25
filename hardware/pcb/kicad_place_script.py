"""
WellD PCB — KiCad Scripting Console placement script
Run in PCB Editor: Tools → Scripting Console → paste and press Enter

REQUIREMENTS:
  - Run "Tools → Update PCB from Schematic" (F8) first so all footprints are imported
  - Footprints will appear in a pile; this script moves them to approximate target positions

UNITS: all positions are in millimetres from the board origin (top-left of Edge.Cuts).
Rotate using pcbnew.DEGREES_TO_IU (1 degree = 1e6 internal units in KiCad 7/8/9/10).

HOW TO USE:
  1. Open PCB Editor (welld.kicad_pcb)
  2. Run F8 to import schematic → click "Update PCB" → Close
  3. Open Tools → Scripting Console
  4. Paste the entire contents of this file and press Enter
  5. The script places all components at the positions below
  6. Fine-tune placement manually; these are starting points only

COORDINATE SYSTEM:
  Board origin = (0, 0) = top-left corner of Edge.Cuts rectangle
  X increases rightward, Y increases downward (standard KiCad PCB coords)
  Positions assume an ~80×55mm board
"""

import pcbnew

board = pcbnew.GetBoard()

def place(ref, x_mm, y_mm, rotation_deg=0, flip=False):
    """Move a footprint to (x_mm, y_mm) and set rotation."""
    fp = board.FindFootprintByReference(ref)
    if fp is None:
        print(f"  WARNING: {ref} not found — skip")
        return
    fp.SetPosition(pcbnew.FromMM(x_mm), pcbnew.FromMM(y_mm))
    fp.SetOrientationDegrees(rotation_deg)
    if flip:
        fp.Flip(fp.GetPosition(), False)
    print(f"  placed {ref} → ({x_mm}, {y_mm}) rot={rotation_deg}°{'  [BACK]' if flip else ''}")

print("=== WellD PCB placement script ===")
print("Placing components at target positions...")

# ── Group H — Battery input (J1 bottom-left) ──────────────────────────────
place("J1",   5,   50, 0)       # XT30 right-angle, long edge bottom
place("D13",  14,  48, 0)       # SMAJ10CA battery TVS
place("D5",   19,  48, 0)       # AO3407 P-MOS load switch
place("R31",  23,  48, 0)       # gate pull-up

# ── Group G — TP5100 USB charger cluster (short edge right) ───────────────
place("J13",  78,  10, 270)     # USB-C connector, right short edge
place("F2",   70,  10, 0)       # Polyfuse
place("U11",  62,   8, 0)       # USBLC6-2SC6 ESD
place("U12",  70,  20, 0)       # TP5100 USB charger
place("C27",  64,  18, 0)       # VUSB filter
place("C28",  74,  26, 0)       # U12 VIN bypass
place("C29",  66,  26, 0)       # U12 VBAT bypass
place("R35",  76,  18, 0)       # PROG resistor
place("R36",  76,  14, 0)       # CHRG pull-up
place("R37",  72,  14, 0)       # CE pull-up
place("R38",  74,  30, 0)       # /CHRG pull-up
place("R_CC1", 78, 16, 0)       # CC1 5k1
place("R_CC2", 78, 20, 0)       # CC2 5k1

# ── Group D — CN3722 solar charger (top-centre) ───────────────────────────
place("U7",   40,  18, 0)       # CN3722 solar MPPT charger
place("C17",  34,  22, 0)       # VIN filter
place("C18",  46,  22, 0)       # VBAT bypass
place("C21",  34,  18, 0)       # second VIN filter
place("R19",  32,  14, 0)       # MPPT divider top
place("R20",  32,  18, 0)       # MPPT divider bottom
place("R21",  38,  12, 0)       # CC setpoint
place("R33",  44,  14, 0)       # CV setpoint 590kΩ → 8.31V
place("R34",  48,  14, 0)       # Parallel CV resistor

# ── Group A — MT3608B boost (centre-left) ────────────────────────────────
place("U8",   20,  22, 0)       # MT3608B boost converter
place("L1",   14,  22, 0)       # Boost inductor (SW→L1→VLOOP)
place("C20",  14,  16, 0)       # VOUT decoupling
place("C22",  18,  16, 0)       # VOUT parallel cap
place("C_BST", 20, 16, 0)      # 100nF BST→SW bootstrap cap
place("C19",  26,  22, 0)       # VIN bypass

# ── Group B — AP63205WU buck (top-left) ──────────────────────────────────
place("U1",   12,  10, 0)       # AP63205WU 3.3V buck
place("L2",   20,  10, 0)       # Buck inductor
place("R_FBH", 26, 10, 0)      # 560kΩ FB divider high-side
place("R_FBL", 26, 14, 0)      # 124kΩ FB divider low-side
place("C_BUCK", 28, 10, 0)     # 10µF primary output filter
place("C9",   10,  14, 0)       # VIN decoupling
place("C10",  14,  14, 0)       # VIN decoupling
place("C11",  30,  10, 0)       # +3V3 output cap
place("C12",  34,  10, 0)       # +3V3 output cap

# ── Group J — Solar input protection (left edge) ──────────────────────────
place("J12",   3,  28, 0)       # Solar screw terminal
place("D14",   8,  28, 0)       # First TVS
place("D6",   12,  28, 0)       # Schottky backfeed block
place("D8",   16,  28, 0)       # Second TVS at CN3722 VIN

# ── Group F — ESP32-C6 module (centre) ───────────────────────────────────
place("U6",   50,  28, 0)       # ESP32-C6-MINI-1U; keep antenna (top end) clear
place("C14a", 44,  28, 0)       # 100nF decoupling × 4 (around VCC pads)
place("C14b", 44,  32, 0)
place("C14c", 44,  36, 0)
place("C14d", 44,  40, 0)
place("C15",  60,  28, 0)       # 10µF bulk

# ── Group C — ADS1115 analog island (right of module) ────────────────────
place("U9",   62,  38, 0)       # ADS1115 ADC — ≥20mm from U8
place("FB1",  56,  38, 0)       # Ferrite bead on ADS VDD
place("C23",  56,  42, 0)       # 100nF near U9 VDD
place("C24",  60,  42, 0)       # 1µF near U9 VDD
place("R_DRDY", 68, 38, 0)     # 4.7kΩ DRDY pull-up

# ── Group E — 4-20mA protection chains (bottom edge terminals) ───────────
# Screw terminals on long bottom edge; protection chain runs inward
place("J4",    3,  37, 0)       # CH1 4-20mA terminal
place("D9",    8,  37, 0)       # CH1 TVS
place("R2",   12,  37, 0)       # CH1 100Ω shunt
place("R3",   18,  37, 0)       # CH1 series protection
place("C3",   22,  37, 0)       # CH1 bypass
place("C4",   22,  41, 0)       # CH1 bypass
place("TP5",  15,  37, 0)       # CH1 test point between R2/R3

place("J5",    3,  43, 0)       # CH2 4-20mA terminal
place("D10",   8,  43, 0)       # CH2 TVS
place("R4",   12,  43, 0)       # CH2 100Ω shunt
place("R5",   18,  43, 0)       # CH2 series protection
place("C5",   22,  43, 0)       # CH2 bypass
place("C6",   22,  47, 0)       # CH2 bypass
place("TP6",  15,  43, 0)       # CH2 test point
place("D1",   26,  40, 0)       # PRTR5V0U2X dual-channel clamp

# Battery voltage divider
place("R7",   70,  45, 0)       # VBAT→ADC divider top (330kΩ)
place("R8",   74,  45, 0)       # VBAT→ADC divider bottom (100kΩ)

# ── Group I — DS18B20 interface ───────────────────────────────────────────
place("J6",    3,  49, 90)      # DS18B20 screw terminal
place("D12",   8,  49, 0)       # ESD protection
place("R6",   12,  45, 0)       # 1-Wire pull-up
place("R28",   8,  53, 0)       # VCC line resistor
place("R32",  12,  49, 0)       # 33Ω series (POPULATE — not DNF)

# ── Miscellaneous ─────────────────────────────────────────────────────────
place("J7",    3,  33, 0)       # Spare terminal
place("J8",   72,  44, 0)       # I²C debug header
place("J10",  72,  50, 0)       # Programming header (keep accessible)
place("J3",    3,  12, 90)      # SMA edge-mount antenna (short left edge)

# Buttons and LED
place("SW1",  66,  10, 0)       # BOOT button
place("SW2",  70,  10, 0)       # EN/Reset button
place("D11",  74,   6, 0)       # Status LED
place("R16",  74,  10, 0)       # LED series resistor

# Test points
place("TP1",  32,   6, 0)       # +3V3
place("TP2",  14,  12, 0)       # VLOOP
place("TP3",  36,   6, 0)       # Near buck output
place("TP4",  38,   6, 0)       # Near buck output
place("TP7",  10,  49, 0)       # 1WIRE GPIO side
place("TP8",  58,  36, 0)       # SDA
place("TP9",  60,  36, 0)       # SCL
place("TP10",  6,  28, 0)       # Solar input
place("TP11",  6,  50, 0)       # BAT+
place("TP12", 68,  42, 0)       # GPIO12 / DRDY
place("TP15", 74,  22, 0)       # /CHRG

# SMA needs to be on an edge — script places near left edge
# W1 pigtail: hand-attach after reflow (PCBWay manual install)

print("\n=== Placement complete ===")
print("Next steps:")
print("  1. Review placement — move components to fine-tune")
print("  2. Check placement_constraints.md for must-be-near/apart rules")
print("  3. Ensure U8 (MT3608B) and U9 (ADS1115) are ≥20mm apart")
print("  4. Ensure U7 (CN3722) and U6 (ESP32) are ≥15mm apart")
print("  5. Draw Edge.Cuts board outline (~80×55mm)")
print("  6. Route traces (start with power planes, then signals)")
print("  7. Add GND copper pours (press B to fill zones)")
print("  8. Run DRC before generating Gerbers")

pcbnew.Refresh()
