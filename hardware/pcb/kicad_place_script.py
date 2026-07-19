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
  Positions assume a ~100×60mm board (outline unconstrained — grown 2026-07-19
  for the top-side BT1 18650 carrier band along the bottom long edge)
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

# ── Group H — Battery carrier + protection (bottom band, 2026-07-19) ─────
place("BT1",  48,  50, 0)       # 18650 carrier ≈78×21 mm, TOP side, bottom long-edge band
place("U13",  10,  44, 0)       # DW01A supervisor (near BT1 − tab)
place("Q6",   14,  44, 0)       # FS8205A dual FET (cell− → GND path, wide copper)
place("R_DW1", 6,  44, 0)       # DW01A VCC filter R
place("C_DW",  8,  46, 0)       # DW01A VCC filter C (to BATT_N)
place("R_CS_DW", 12, 46, 0)     # DW01A CS resistor (to system GND)
place("D13",  14,  48, 0)       # SMAJ10CA battery TVS
place("D5",   19,  48, 0)       # AO3407 P-MOS load switch
place("R31",  23,  48, 0)       # D5 gate pull-down (holds switch ON)

# ── Group G — TP4056 USB charger cluster (short edge right, 1S 2026-07-19) ─
place("J13",  78,  10, 270)     # USB-C connector, right short edge
place("F2",   70,  10, 0)       # Polyfuse
place("U11",  62,   8, 0)       # USBLC6-2SC6 ESD
place("U12",  70,  20, 0)       # TP4056 1S linear charger (EPAD thermal pour)
place("C27",  64,  18, 0)       # VUSB filter
place("C28",  74,  26, 0)       # U12 VCC bypass 10µF
place("C29",  66,  26, 0)       # U12 BAT bypass 10µF
place("R_PROG", 76, 18, 0)      # PROG resistor 1.2k → 1A
place("R_NTC", 76, 14, 0)       # TEMP divider top (VUSB→TEMP)
place("RT1",  72,  14, 0)       # TEMP NTC (thermally couple to pack)
place("R38",  74,  30, 0)       # /CHRG pull-up
place("R50", 78, 16, 0)         # CC1 5k1 (was R_CC1)
place("R51", 78, 20, 0)         # CC2 5k1 (was R_CC2)

# ── Group D — CN3791 solar charger (top-centre, 1S 2026-07-19) ────────────
place("U7",   40,  18, 0)       # CN3791 solar MPPT buck charger (int. switch)
place("C17",  34,  22, 0)       # VIN filter
place("C18",  46,  22, 0)       # BAT bypass
place("C21",  34,  18, 0)       # second VIN filter
place("D_SOLAR", 42, 12, 0)     # SS34 catch diode (GND→SW)
place("L_SOLAR", 46, 12, 0)     # 47µH buck inductor (SW→CN_CS); no pour under
place("R19",  32,  14, 0)       # R_CS 0.1Ω CSP–BAT sense (1.2A)
place("C_VG", 44, 16, 0)        # VG↔VCC bypass 100nF
place("M_SOLAR", 36, 14, 0)     # SI2319CDS buck P-FET (restored — CN3791 is a controller)
place("D16", 38, 16, 0)         # SS34 series diode (night back-feed block)
place("R_DRV", 34, 16, 0)       # 300k gate-source pull-off at M_SOLAR
place("C_COM", 36, 20, 0)       # COM compensation 220nF (series R_COM)
place("R_COM", 38, 20, 0)       # COM compensation 120R to GND
place("U14", 44, 22, 0)         # LM393 cold-cutoff comparator (solar-powered)
place("RT_SOLAR", 46, 26, 0)    # cutoff NTC (thermally couple to cell/carrier)
place("R_NT1", 40, 24, 0)       # temp divider top 30k
place("R_NT2", 42, 26, 0)       # ref divider top 100k
place("R_NT3", 44, 28, 0)       # ref divider bottom 100k
place("R_PU", 46, 22, 0)        # OUT1 pull-up 100k
place("R_HYS", 48, 24, 0)       # hysteresis 330k
place("C_NTC", 42, 22, 0)       # U14 VCC bypass
place("Q7", 48, 20, 0)          # AO3400A MPPT clamp
place("R20",  32,  18, 0)       # MPPT divider top (VSOLAR side) 316k
place("R21",  38,  12, 0)       # MPPT divider bottom (GND side) 100k
place("R25",  48,  10, 0)       # /CHRG_SOLAR pull-up to +3V3
place("D7",   52,  12, 0)       # Solar charge LED (DNF R22)
place("R22",  52,  16, 0)       # LED series 1k DNF

# ── Group A — MT3608B boost (centre-left) ────────────────────────────────
place("U8",   20,  22, 0)       # MT3608B boost converter
place("L1",   14,  22, 0)       # Boost inductor (VBAT→Q3→L1→SW)
place("Q3",   10,  22, 0)       # VLOOP disconnect P-FET (VBAT→L1)
place("Q4",   10,  18, 0)       # Q3 gate driver (GPIO5)
place("R29",  12,  18, 0)       # Q3 gate pull-up 100k
place("R27",  12,  26, 0)       # VBOOST_EN pull-down 100k
place("D15",  17,  18, 0)       # SS34 boost rectifier SW→VLOOP
place("C20",  14,  16, 0)       # VOUT decoupling
place("C22",  18,  16, 0)       # VOUT parallel cap
place("D11",  16,  13, 0)       # SMAJ13A VLOOP TVS (near C20/C22, J4/J5 side)
place("C_BST", 20, 16, 0)      # 100nF BST→SW bootstrap cap
place("C19",  26,  22, 0)       # VIN bypass
place("R23",  24,  16, 0)       # VLOOP FB divider 1.91M
place("R24",  24,  18, 0)       # VLOOP FB divider 100k

# ── Group B — HT7333-A 3.3V LDO (top-left, 1S 2026-07-19) ────────────────
place("U1",   12,  10, 0)       # HT7333-A SOT-23 LDO (VBAT→+3V3)
place("C16",  10,  18, 0)      # 10µF VIN bulk
place("C_BUCK", 28, 10, 0)     # 10µF primary output cap
place("C9",   10,  14, 0)       # VIN decoupling
place("C10",  14,  14, 0)       # VIN decoupling
place("C11",  30,  10, 0)       # +3V3 output cap
place("C12",  34,  10, 0)       # +3V3 output cap

# ── Group J — Solar input protection (left edge) ──────────────────────────
place("J12",   3,  28, 0)       # Solar screw terminal
place("D14",   8,  28, 0)       # First TVS
place("D6",   12,  28, 0)       # Schottky backfeed block
place("D8",   16,  28, 0)       # Second TVS at CN3791 VIN

# ── Group F — ESP32-C6 module (centre) ───────────────────────────────────
place("U6",   50,  28, 0)       # ESP32-C6-MINI-1U; keep antenna (top end) clear
place("C13",  44,  28, 0)       # 100nF decoupling × 5 (around VCC pads)
place("C30",  44,  32, 0)
place("C31",  44,  36, 0)
place("C32",  44,  40, 0)
place("C33",  46,  42, 0)
place("C15",  60,  28, 0)       # 10µF bulk
place("R15",  60,  32, 0)       # EN pull-up 10k
place("C36",  60,  34, 0)       # EN delay cap 1µF

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
place("C34",  12,  35, 0)       # 10nF across R2 shunt
place("TP5",  15,  37, 0)       # CH1 test point at shunt top

place("J5",    3,  43, 0)       # CH2 4-20mA terminal
place("D10",   8,  43, 0)       # CH2 TVS
place("R4",   12,  43, 0)       # CH2 100Ω shunt
place("R5",   18,  43, 0)       # CH2 series protection
place("C5",   22,  43, 0)       # CH2 bypass
place("C6",   22,  47, 0)       # CH2 bypass
place("C35",  12,  45, 0)       # 10nF across R4 shunt
place("TP6",  15,  43, 0)       # CH2 test point
place("D1",   26,  40, 0)       # PRTR5V0U2X dual-channel clamp

# Battery voltage divider (Group K — high-side gated)
place("Q5",   66,  45, 0)       # AO3407 high-side divider switch
place("R16",  66,  48, 0)       # Q5 gate pull-up 100k
place("Q2",   68,  48, 0)       # AO3400A level shifter (GPIO15)
place("R26",  70,  48, 0)       # Q2 gate pull-down 4.7k
place("R7",   70,  45, 0)       # divider top (100kΩ — 1S divide-by-2)
place("R8",   74,  45, 0)       # divider bottom (100kΩ)
place("C8",   74,  48, 0)       # 1nF across R8

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
place("SW1",  66,  10, 0)       # RESET button (EN to GND)
place("SW2",  70,  10, 0)       # BOOT button (GPIO9 to GND)
place("D4",   74,   6, 0)       # Status LED (GPIO14)
place("R14",  74,  10, 0)       # LED series resistor 1k

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
place("TP13", 76,  52, 0)       # GPIO13 / FACTORY_RESET (keep reachable)
place("TP14", 44,  12, 0)       # /CHRG_SOLAR
place("TP15", 74,  22, 0)       # /CHRG_USB

# SMA needs to be on an edge — script places near left edge
# W1 pigtail: hand-attach after reflow (PCBWay manual install)

print("\n=== Placement complete ===")
print("Next steps:")
print("  1. Review placement — move components to fine-tune")
print("  2. Check placement_constraints.md for must-be-near/apart rules")
print("  3. Ensure U8 (MT3608B) and U9 (ADS1115) are ≥20mm apart")
print("  4. Ensure U7 (CN3791) and U6 (ESP32) are ≥15mm apart")
print("  5. Draw Edge.Cuts board outline around the finished placement (~100x60mm working target; size unconstrained)")
print("  6. Route traces (start with power planes, then signals)")
print("  7. Add GND copper pours (press B to fill zones)")
print("  8. Run DRC before generating Gerbers")

pcbnew.Refresh()
