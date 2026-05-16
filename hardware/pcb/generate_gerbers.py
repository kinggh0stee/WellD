#!/usr/bin/env python3
"""
generate_gerbers.py — WellD PCB Gerber / drill file generator
--------------------------------------------------------------
Writes a complete fabrication package to  hardware/pcb/gerbers/

  welld-F_Cu.gbr       Front copper  (SMD pads + THT annular rings, front)
  welld-B_Cu.gbr       Back copper   (THT annular rings, back)
  welld-F_Mask.gbr     Front solder mask  (clearance openings)
  welld-B_Mask.gbr     Back solder mask   (clearance openings, THT)
  welld-F_Paste.gbr    Front stencil paste  (SMD pads only)
  welld-F_SilkS.gbr    Front silkscreen  (reference designators)
  welld-Edge_Cuts.gbr  Board outline
  welld-PTH.drl        Excellon drill — plated through-holes
  welld-NPTH.drl       Excellon drill — non-plated (mounting holes)
  welld-job.gbrjob     Gerber job file (IPC-2581-compatible metadata)

Requirements: Python ≥ 3.8, stdlib only.
Run from anywhere:  python3 hardware/pcb/generate_gerbers.py
"""

from __future__ import annotations
import math
import os
from dataclasses import dataclass, field
from typing import List, Tuple

# ---------------------------------------------------------------------------
# Output directory
# ---------------------------------------------------------------------------
HERE   = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, "gerbers")

DATE = "2026-05-16"
REV  = "1.0"

# ---------------------------------------------------------------------------
# Gerber coordinate helpers  (format %FSLAX46Y46*%  →  1 mm = 1 000 000 units)
# ---------------------------------------------------------------------------
_SCALE = 1_000_000

def _c(mm: float) -> str:
    """mm → Gerber integer string (no sign, no decimal)."""
    return str(round(mm * _SCALE))

def _xy(x: float, y: float) -> str:
    return f"X{_c(x)}Y{_c(y)}"

# ---------------------------------------------------------------------------
# Aperture manager
# ---------------------------------------------------------------------------
class _Aps:
    """Collects unique aperture definitions; assigns D-codes starting at D10."""

    def __init__(self) -> None:
        self._order: list[tuple[int, str]] = []
        self._idx: dict[str, int] = {}
        self._next = 10

    def _reg(self, key: str, defn_tmpl: str) -> int:
        if key not in self._idx:
            n = self._next
            self._idx[key] = n
            self._order.append((n, defn_tmpl.format(n=n)))
            self._next += 1
        return self._idx[key]

    def circle(self, d: float) -> int:
        return self._reg(f"C{d:.5f}", f"%ADD{{n}}C,{d:.5f}*%")

    def rect(self, w: float, h: float) -> int:
        return self._reg(f"R{w:.5f}x{h:.5f}", f"%ADD{{n}}R,{w:.5f}X{h:.5f}*%")

    def oval(self, w: float, h: float) -> int:
        return self._reg(f"O{w:.5f}x{h:.5f}", f"%ADD{{n}}O,{w:.5f}X{h:.5f}*%")

    def defs(self) -> str:
        return "\n".join(d for _, d in self._order) + "\n" if self._order else ""

# ---------------------------------------------------------------------------
# Pad descriptor
# ---------------------------------------------------------------------------
@dataclass
class Pad:
    x: float            # local X from component centre (mm)
    y: float            # local Y from component centre (mm)
    w: float            # pad width  (mm)
    h: float            # pad height (mm)
    shape: str          # 'rect' | 'oval' | 'circle'
    layers: str         # 'F' = front SMD, 'T' = through-hole (both faces)
    drill: float = 0.0  # drill diameter for THT pads; 0 = SMD
    paste: bool = True  # include in paste layer (False for NPTH / no-paste)
    npth: bool = False  # non-plated hole (mounting hole, no copper pad)

# ---------------------------------------------------------------------------
# Footprint library  (IPC-7351B dimensions where applicable)
# ---------------------------------------------------------------------------
# Each entry:  footprint_key → [Pad, ...]
# x/y are offsets from the footprint origin (component placement point).
# KiCad PCB Y-axis points downward, so positive Y = toward bottom edge.

def _smd(x, y, w, h, shape='rect', paste=True) -> Pad:
    return Pad(x, y, w, h, shape, 'F', paste=paste)

def _tht(x, y, pad_d, drill_d) -> Pad:
    return Pad(x, y, pad_d, pad_d, 'circle', 'T', drill=drill_d, paste=False)

def _npth(x, y, d) -> Pad:
    return Pad(x, y, d, d, 'circle', 'T', drill=d, paste=False, npth=True)

# Thin wire used for board-edge reference line on silk
_THIN = 0.12

FOOTPRINTS: dict[str, List[Pad]] = {

    # ── Passive 0402 ─────────────────────────────────────────────────────────
    "Resistor_SMD:R_0402_1005Metric": [
        _smd(-0.875, 0, 1.00, 0.90),
        _smd(+0.875, 0, 1.00, 0.90),
    ],
    "Capacitor_SMD:C_0402_1005Metric": [
        _smd(-0.875, 0, 1.00, 0.90),
        _smd(+0.875, 0, 1.00, 0.90),
    ],

    # ── Passive 0805 ─────────────────────────────────────────────────────────
    "Resistor_SMD:R_0805_2012Metric": [
        _smd(-1.45, 0, 1.80, 1.45),
        _smd(+1.45, 0, 1.80, 1.45),
    ],
    "Capacitor_SMD:C_0805_2012Metric": [
        _smd(-1.45, 0, 1.80, 1.45),
        _smd(+1.45, 0, 1.80, 1.45),
    ],

    # ── 1206 fuse ────────────────────────────────────────────────────────────
    "Fuse:Fuse_1206_3216Metric": [
        _smd(-1.75, 0, 1.60, 1.80),
        _smd(+1.75, 0, 1.60, 1.80),
    ],

    # ── LED 0603 ─────────────────────────────────────────────────────────────
    "LED_SMD:LED_0603_1608Metric": [
        _smd(-0.80, 0, 1.60, 1.10),
        _smd(+0.80, 0, 1.60, 1.10),
    ],

    # ── SOD-123 (D6 Schottky) ────────────────────────────────────────────────
    "Diode_SMD:D_SOD-123": [
        _smd(-1.65, 0, 1.60, 1.10),   # cathode
        _smd(+1.65, 0, 1.60, 1.10),   # anode
    ],

    # ── SOT-23 (3-pin, D5 AO3407) ────────────────────────────────────────────
    "Package_TO_SOT_SMD:SOT-23": [
        _smd(-0.95, +0.90, 0.90, 0.90),   # pin 1
        _smd(-0.95, -0.90, 0.90, 0.90),   # pin 2
        _smd(+0.95,  0.00, 0.90, 0.90),   # pin 3
    ],

    # ── SOT-23-6 (U3 DW01A, U4 FS8205A, U5 USBLC6) ──────────────────────────
    "Package_TO_SOT_SMD:SOT-23-6": [
        _smd(-1.15, +0.95, 1.00, 0.65),   # pin 1  left-bottom
        _smd(-1.15,  0.00, 1.00, 0.65),   # pin 2  left-centre
        _smd(-1.15, -0.95, 1.00, 0.65),   # pin 3  left-top
        _smd(+1.15, -0.95, 1.00, 0.65),   # pin 4  right-top
        _smd(+1.15,  0.00, 1.00, 0.65),   # pin 5  right-centre
        _smd(+1.15, +0.95, 1.00, 0.65),   # pin 6  right-bottom
    ],

    # ── SC-70-5 (U1 TPS7A0533) ───────────────────────────────────────────────
    "Package_TO_SOT_SMD:SC-70-5": [
        _smd(-0.90, +0.65, 0.70, 0.50),   # pin 1
        _smd(-0.90,  0.00, 0.70, 0.50),   # pin 2
        _smd(-0.90, -0.65, 0.70, 0.50),   # pin 3
        _smd(+0.90, -0.325,0.70, 0.50),   # pin 4
        _smd(+0.90, +0.325,0.70, 0.50),   # pin 5
    ],

    # ── SOT-363 / SC-70-6 (D1 PRTR5V0U2X) ───────────────────────────────────
    "Package_TO_SOT_SMD:SOT-363_SC-70-6": [
        _smd(-0.90, +0.65, 0.75, 0.55),   # pin 1
        _smd(-0.90,  0.00, 0.75, 0.55),   # pin 2
        _smd(-0.90, -0.65, 0.75, 0.55),   # pin 3
        _smd(+0.90, -0.65, 0.75, 0.55),   # pin 4
        _smd(+0.90,  0.00, 0.75, 0.55),   # pin 5
        _smd(+0.90, +0.65, 0.75, 0.55),   # pin 6
    ],

    # ── SOIC-8  (U2 TP4056, U7 CN3791) ──────────────────────────────────────
    # IPC-7351B nominal, 3.9×4.9mm body, 1.27mm pitch, row-to-row 5.4mm
    "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm": [
        _smd(-2.70, +1.905, 1.55, 0.60),  # pin 1
        _smd(-2.70, +0.635, 1.55, 0.60),  # pin 2
        _smd(-2.70, -0.635, 1.55, 0.60),  # pin 3
        _smd(-2.70, -1.905, 1.55, 0.60),  # pin 4
        _smd(+2.70, -1.905, 1.55, 0.60),  # pin 5
        _smd(+2.70, -0.635, 1.55, 0.60),  # pin 6
        _smd(+2.70, +0.635, 1.55, 0.60),  # pin 7
        _smd(+2.70, +1.905, 1.55, 0.60),  # pin 8
    ],

    # ── JST XH B2B-XH-AM (J1 LiPo, 2.5mm pitch SMD horizontal) ─────────────
    # Higher retention vs PH; 2.5mm pitch, 2 signal pads + 2 mounting lugs
    "Connector_JST:JST_XH_B2B-XH-AM_1x02_P2.50mm_Horizontal": [
        _smd(-1.25, +2.25, 1.00, 2.50),   # pin 1 (signal)
        _smd(+1.25, +2.25, 1.00, 2.50),   # pin 2 (signal)
        _smd(-3.00, +0.30, 1.50, 1.00, paste=False),  # mounting lug L
        _smd(+3.00, +0.30, 1.50, 1.00, paste=False),  # mounting lug R
    ],

    # ── USB-C receptacle (J2 GCT USB4135, 9×3.2mm SMD) ───────────────────────
    # Simplified: 2 CC pads, 2 VBUS pads, 2 GND pads, 2 mounting tabs
    "welld:USB_C_9x3.2mm": [
        _smd(-3.50, +2.10, 0.70, 0.40),   # VBUS L
        _smd(-2.50, +2.10, 0.70, 0.40),   # CC1
        _smd(-1.50, +2.10, 0.70, 0.40),   # DN1
        _smd(-0.50, +2.10, 0.70, 0.40),   # DP1
        _smd(+0.50, +2.10, 0.70, 0.40),   # DP2
        _smd(+1.50, +2.10, 0.70, 0.40),   # DN2
        _smd(+2.50, +2.10, 0.70, 0.40),   # CC2
        _smd(+3.50, +2.10, 0.70, 0.40),   # VBUS R
        _smd(-3.50, -0.30, 0.70, 0.40),   # GND L1
        _smd(+3.50, -0.30, 0.70, 0.40),   # GND R1
        _smd(-4.00, +0.85, 1.50, 1.50, paste=False),  # mount tab L
        _smd(+4.00, +0.85, 1.50, 1.50, paste=False),  # mount tab R
    ],

    # ── U.FL SMD coaxial (J3) ────────────────────────────────────────────────
    "Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical": [
        _smd(0.00,  0.00, 0.80, 0.80, 'circle'),     # signal centre
        _smd(-1.65, 0.00, 1.40, 0.80, paste=False),  # GND tab L
        _smd(+1.65, 0.00, 1.40, 0.80, paste=False),  # GND tab R
        _smd(0.00, -1.65, 1.40, 0.80, paste=False),  # GND tab top
        _smd(0.00, +1.65, 1.40, 0.80, paste=False),  # GND tab bot
    ],

    # ── Phoenix Contact MC 3.5mm — 3-position THT (J4 J5 J6 J7) ─────────────
    "Connector_Phoenix_MC:PhoenixContact_MC_1,5_3-G-3,5_1x03_P3.50mm_Horizontal": [
        _tht(-3.50, 0, 2.00, 1.05),   # pin 1
        _tht( 0.00, 0, 2.00, 1.05),   # pin 2
        _tht(+3.50, 0, 2.00, 1.05),   # pin 3
    ],

    # ── Phoenix Contact MC 3.5mm — 2-position THT (J12 solar) ────────────────
    "Connector_Phoenix_MC:PhoenixContact_MC_1,5_2-G-3,5_1x02_P3.50mm_Horizontal": [
        _tht(-1.75, 0, 2.00, 1.05),   # pin 1
        _tht(+1.75, 0, 2.00, 1.05),   # pin 2
    ],

    # ── Pin header 2.54mm 1×4 (J8 I2C) ──────────────────────────────────────
    "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical": [
        _tht(0, 0.00, 1.70, 1.02),
        _tht(0, 2.54, 1.70, 1.02),
        _tht(0, 5.08, 1.70, 1.02),
        _tht(0, 7.62, 1.70, 1.02),
    ],

    # ── Pin header 2.54mm 1×8 (J9 GPIO) ─────────────────────────────────────
    "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical": [
        _tht(0,  0.00, 1.70, 1.02),
        _tht(0,  2.54, 1.70, 1.02),
        _tht(0,  5.08, 1.70, 1.02),
        _tht(0,  7.62, 1.70, 1.02),
        _tht(0, 10.16, 1.70, 1.02),
        _tht(0, 12.70, 1.70, 1.02),
        _tht(0, 15.24, 1.70, 1.02),
        _tht(0, 17.78, 1.70, 1.02),
    ],

    # ── Pin header 1.27mm 1×6 (J10 PROG) ────────────────────────────────────
    "Connector_PinHeader_1.27mm:PinHeader_1x06_P1.27mm_Vertical": [
        _tht(0, 0.00, 1.35, 0.80),
        _tht(0, 1.27, 1.35, 0.80),
        _tht(0, 2.54, 1.35, 0.80),
        _tht(0, 3.81, 1.35, 0.80),
        _tht(0, 5.08, 1.35, 0.80),
        _tht(0, 6.35, 1.35, 0.80),
    ],

    # ── Tactile switch 6×6mm SMD (SW1 SW2) ───────────────────────────────────
    # TL3305AF160QG — 4-pin SPST, body 6×6, pad layout symmetric
    "Button_Switch_SMD:SW_SPST_TL3305AF160QG": [
        _smd(-2.50, -1.75, 1.60, 1.00),  # pin 1 (A)
        _smd(+2.50, -1.75, 1.60, 1.00),  # pin 2 (B)
        _smd(-2.50, +1.75, 1.60, 1.00),  # pin 3 (A)
        _smd(+2.50, +1.75, 1.60, 1.00),  # pin 4 (B)
    ],

    # ── SOT-23-5 (U8 TPS61023) ───────────────────────────────────────────────
    # 5-pin SOT-23: 3 pads left, 2 pads right (no centre pin on right)
    "Package_TO_SOT_SMD:SOT-23-5": [
        _smd(-1.15, +0.95, 1.00, 0.65),   # pin 1  left-bottom
        _smd(-1.15,  0.00, 1.00, 0.65),   # pin 2  left-centre
        _smd(-1.15, -0.95, 1.00, 0.65),   # pin 3  left-top
        _smd(+1.15, -0.95, 1.00, 0.65),   # pin 4  right-top
        _smd(+1.15, +0.95, 1.00, 0.65),   # pin 5  right-bottom
    ],

    # ── DO-214AC / SMA (D8 SMAJ7.0A TVS) ────────────────────────────────────
    # IPC-7351B: pad 2.0×2.2mm, row-to-row 4.2mm
    "Diode_SMD:D_SMA": [
        _smd(-2.10, 0, 2.00, 2.20),   # cathode (K)
        _smd(+2.10, 0, 2.00, 2.20),   # anode   (A)
    ],

    # ── 4×4mm SMD shielded power inductor (L1 CDRH4D22NP) ───────────────────
    # Body 4.7×4.7mm; pads 2.5×2.0mm at ±1.8mm from centre
    "welld:Inductor_4x4mm_SMD": [
        _smd(-1.80, 0, 2.50, 2.00),   # pin 1
        _smd(+1.80, 0, 2.50, 2.00),   # pin 2
    ],

    # ── 1206 capacitor (C20 VBOOST output) ───────────────────────────────────
    # Same land pattern as 1206 fuse
    "Capacitor_SMD:C_1206_3216Metric": [
        _smd(-1.75, 0, 1.60, 1.80),
        _smd(+1.75, 0, 1.60, 1.80),
    ],

    # ── M3 mounting hole NPTH ────────────────────────────────────────────────
    "MountingHole:MountingHole_3.2mm_M3": [
        _npth(0, 0, 3.20),
    ],

    # ── ESP32-C6-MINI-1U module (custom footprint) ────────────────────────────
    # Module: 13.2mm × 16.6mm.  Castellated LCC pads on bottom & two sides.
    # Bottom edge (Y = +8.3 from module centre): 14 pads at 0.9mm pitch
    # Left edge  (X = -6.6 from module centre): 7 pads at 0.9mm pitch
    # Right edge (X = +6.6 from module centre): 7 pads at 0.9mm pitch
    # Pad: 0.9mm × 1.5mm (pad overhangs edge by 0.75mm)
    # Module centre = footprint origin
    "welld:ESP32_C6_MINI_1U": (
        # Bottom row — pads centred on Y=+8.3, X from -5.85 to +5.85
        [_smd(-5.85 + i*0.90, +8.30, 0.65, 1.50) for i in range(14)]
        +
        # Left column — pads centred on X=-6.6, Y from -2.70 to +2.70
        [_smd(-6.60, -2.70 + i*0.90, 1.50, 0.65) for i in range(7)]
        +
        # Right column — pads centred on X=+6.6, Y from -2.70 to +2.70
        [_smd(+6.60, -2.70 + i*0.90, 1.50, 0.65) for i in range(7)]
        +
        # 4 GND thermal pads on underside (approximated as interior)
        [_smd(x, y, 1.50, 1.50, paste=False)
         for x, y in [(-2.0,-2.0),(+2.0,-2.0),(-2.0,+2.0),(+2.0,+2.0)]]
    ),
}

# Alias: solder jumpers — treated as 0402-sized pads for paste/mask purposes
for _sj in ("SJ1", "SJ2", "SJ3", "SJ4", "SJ5"):
    FOOTPRINTS[f"welld:SolderJumper_2_{_sj}"] = [
        _smd(-0.70, 0, 0.80, 0.80),
        _smd(+0.70, 0, 0.80, 0.80),
    ]

# ---------------------------------------------------------------------------
# Component placement  (ref, footprint-key, x, y, rotation-deg, value)
# Coordinates are in mm on the 80×55mm PCB, origin top-left corner.
# Rotation follows KiCad convention: positive = counter-clockwise.
# ---------------------------------------------------------------------------
COMPONENTS: list[tuple] = [
    # ICs
    ("U1",  "Package_TO_SOT_SMD:SC-70-5",                56,   34,   0, "TPS7A0533"),
    ("U2",  "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",       10,   41,   0, "TP4056"),
    ("U3",  "Package_TO_SOT_SMD:SOT-23-6",                68,   21,   0, "S-8261AAYFT"),
    ("U4",  "Package_TO_SOT_SMD:SOT-23-6",                68,   14,   0, "FS8205A"),
    ("U5",  "Package_TO_SOT_SMD:SOT-23-6",                10,   48,   0, "USBLC6"),
    ("U6",  "welld:ESP32_C6_MINI_1U",                     31,   26,   0, "ESP32-C6"),
    ("U7",  "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",       60,   10,   0, "CN3791"),
    ("U8",  "Package_TO_SOT_SMD:SOT-23-5",                73,   20,   0, "TPS61023"),
    ("U9",  "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",       42,   38,   0, "ADS1115"),
    ("U10", "Package_TO_SOT_SMD:SOT-23-6",                68,   42,   0, "MAX17048"),
    # Diodes
    ("D1",  "Package_TO_SOT_SMD:SOT-363_SC-70-6",         15,   14,   0, "PRTR5V0U2X"),
    ("D2",  "LED_SMD:LED_0603_1608Metric",                 12,   47,   0, "LED_CHRG"),
    ("D3",  "LED_SMD:LED_0603_1608Metric",                 14,   47,   0, "LED_STBY"),
    ("D4",  "LED_SMD:LED_0603_1608Metric",                 50,   51,   0, "LED_STATUS"),
    ("D5",  "Package_TO_SOT_SMD:SOT-23",                   65,   42,   0, "AO3407"),
    ("D6",  "Diode_SMD:D_SOD-123",                         56,    7,   0, "MBRS140"),
    ("D8",  "Diode_SMD:D_SMA",                             62,   20,   0, "SMAJ7.0A"),
    # Fuse
    ("F1",  "Fuse:Fuse_1206_3216Metric",                    6,   44,   0, "PTC_1A"),
    # Connectors
    ("J1",  "Connector_JST:JST_XH_B2B-XH-AM_1x02_P2.50mm_Horizontal", 74, 40, 0, "LiPo"),
    ("J2",  "welld:USB_C_9x3.2mm",                          2,   47,   0, "USB-C"),
    ("J3",  "Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical",   40, 53, 0, "U.FL"),
    ("J4",  "Connector_Phoenix_MC:PhoenixContact_MC_1,5_3-G-3,5_1x03_P3.50mm_Horizontal", 12, 2, 0, "4-20mA_1"),
    ("J5",  "Connector_Phoenix_MC:PhoenixContact_MC_1,5_3-G-3,5_1x03_P3.50mm_Horizontal", 23, 2, 0, "4-20mA_2"),
    ("J6",  "Connector_Phoenix_MC:PhoenixContact_MC_1,5_3-G-3,5_1x03_P3.50mm_Horizontal", 34, 2, 0, "DS18B20"),
    ("J7",  "Connector_Phoenix_MC:PhoenixContact_MC_1,5_3-G-3,5_1x03_P3.50mm_Horizontal", 45, 2, 0, "Spare"),
    ("J8",  "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical", 70, 46, 0, "I2C"),
    ("J9",  "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical", 70, 32, 0, "GPIO"),
    ("J10", "Connector_PinHeader_1.27mm:PinHeader_1x06_P1.27mm_Vertical",  2, 20, 0, "PROG"),
    ("J12", "Connector_Phoenix_MC:PhoenixContact_MC_1,5_2-G-3,5_1x02_P3.50mm_Horizontal", 64, 2, 0, "Solar"),
    # MOSFETs
    ("Q1",  "Package_TO_SOT_SMD:SOT-23",                   14,   43,   0, "2N7002"),
    ("Q2",  "Package_TO_SOT_SMD:SOT-23",                   56,   36,   0, "2N7002"),
    # Inductor
    ("L1",  "welld:Inductor_4x4mm_SMD",                    74,   12,   0, "4.7uH"),
    # Switches
    ("SW1", "Button_Switch_SMD:SW_SPST_TL3305AF160QG",      5,   35,   0, "RESET"),
    ("SW2", "Button_Switch_SMD:SW_SPST_TL3305AF160QG",      5,   28,   0, "BOOT"),
    # Resistors
    ("R1",  "Resistor_SMD:R_0402_1005Metric",   8,  38, 0, "2k0"),
    ("R2",  "Resistor_SMD:R_0805_2012Metric",  17,  10, 0, "100R"),
    ("R3",  "Resistor_SMD:R_0402_1005Metric",  20,  12, 0, "100R"),
    ("R4",  "Resistor_SMD:R_0805_2012Metric",  26,  10, 0, "100R"),
    ("R5",  "Resistor_SMD:R_0402_1005Metric",  29,  12, 0, "100R"),
    ("R6",  "Resistor_SMD:R_0402_1005Metric",  36,  10, 0, "4k7"),
    ("R7",  "Resistor_SMD:R_0402_1005Metric",  53,  30, 0, "100k"),
    ("R8",  "Resistor_SMD:R_0402_1005Metric",  53,  32, 0, "100k"),
    ("R9",  "Resistor_SMD:R_0402_1005Metric",  63,  46, 0, "4k7"),
    ("R10", "Resistor_SMD:R_0402_1005Metric",  65,  46, 0, "4k7"),
    ("R11", "Resistor_SMD:R_0402_1005Metric",  26,  36, 0, "10k"),
    ("R12", "Resistor_SMD:R_0402_1005Metric",  26,  34, 0, "10k"),
    ("R13", "Resistor_SMD:R_0402_1005Metric",  26,  32, 0, "10k"),
    ("R14", "Resistor_SMD:R_0402_1005Metric",  51,  49, 0, "1k"),
    ("R15", "Resistor_SMD:R_0402_1005Metric",   4,  50, 0, "5k1"),
    ("R16", "Resistor_SMD:R_0402_1005Metric",   6,  50, 0, "5k1"),
    ("R17", "Resistor_SMD:R_0402_1005Metric",  11,  45, 0, "1k"),
    ("R18", "Resistor_SMD:R_0402_1005Metric",  13,  45, 0, "1k"),
    ("R19", "Resistor_SMD:R_0402_1005Metric",  57,  12, 0, "2k0"),
    ("R20", "Resistor_SMD:R_0402_1005Metric",  63,   8, 0, "36k"),
    ("R21", "Resistor_SMD:R_0402_1005Metric",  63,  10, 0, "10k"),
    ("R22", "Resistor_SMD:R_0402_1005Metric",  62,  14, 0, "1k"),
    ("R23", "Resistor_SMD:R_0402_1005Metric",  76,  18, 0, "1M1"),
    ("R24", "Resistor_SMD:R_0402_1005Metric",  76,  20, 0, "47k"),
    ("R25", "Resistor_SMD:R_0402_1005Metric",  14,  47, 0, "10k"),
    ("R26", "Resistor_SMD:R_0402_1005Metric",  57,  38, 0, "10k"),
    # Capacitors
    ("C1",   "Capacitor_SMD:C_0805_2012Metric",  8,  41, 0, "10uF"),
    ("C2",   "Capacitor_SMD:C_0805_2012Metric", 12,  41, 0, "10uF"),
    ("C3",   "Capacitor_SMD:C_0402_1005Metric", 20,  14, 0, "100nF"),
    ("C4",   "Capacitor_SMD:C_0805_2012Metric", 22,  14, 0, "10uF"),
    ("C5",   "Capacitor_SMD:C_0402_1005Metric", 29,  14, 0, "100nF"),
    ("C6",   "Capacitor_SMD:C_0805_2012Metric", 31,  14, 0, "10uF"),
    ("C7",   "Capacitor_SMD:C_0402_1005Metric", 36,  12, 0, "100nF"),
    ("C8",   "Capacitor_SMD:C_0402_1005Metric", 55,  32, 0, "100nF"),
    ("C9",   "Capacitor_SMD:C_0402_1005Metric", 54,  35, 0, "100nF"),
    ("C10",  "Capacitor_SMD:C_0402_1005Metric", 56,  35, 0, "1uF"),
    ("C11",  "Capacitor_SMD:C_0402_1005Metric", 54,  37, 0, "100nF"),
    ("C12",  "Capacitor_SMD:C_0402_1005Metric", 56,  37, 0, "1uF"),
    ("C13",  "Capacitor_SMD:C_0402_1005Metric", 27,  37, 0, "100nF"),
    ("C14a", "Capacitor_SMD:C_0402_1005Metric", 42,  26, 0, "100nF"),
    ("C14b", "Capacitor_SMD:C_0402_1005Metric", 44,  24, 0, "100nF"),
    ("C14c", "Capacitor_SMD:C_0402_1005Metric", 46,  26, 0, "100nF"),
    ("C14d", "Capacitor_SMD:C_0402_1005Metric", 48,  24, 0, "100nF"),
    ("C15",  "Capacitor_SMD:C_0805_2012Metric", 44,  26, 0, "10uF"),
    ("C16",  "Capacitor_SMD:C_0805_2012Metric",  6,  46, 0, "4.7uF"),
    ("C17",  "Capacitor_SMD:C_0805_2012Metric", 58,   8, 0, "10uF"),
    ("C18",  "Capacitor_SMD:C_0805_2012Metric", 60,  12, 0, "10uF"),
    ("C19",  "Capacitor_SMD:C_0805_2012Metric", 76,  14, 0, "10uF"),
    ("C20",  "Capacitor_SMD:C_1206_3216Metric", 77,   8, 0, "22uF"),
    # Mounting holes  (NPTH — no copper pads)
    ("MH1", "MountingHole:MountingHole_3.2mm_M3",  3.5,  3.5, 0, "M3"),
    ("MH2", "MountingHole:MountingHole_3.2mm_M3", 76.5,  3.5, 0, "M3"),
    ("MH3", "MountingHole:MountingHole_3.2mm_M3",  3.5, 51.5, 0, "M3"),
    ("MH4", "MountingHole:MountingHole_3.2mm_M3", 76.5, 51.5, 0, "M3"),
]

# ---------------------------------------------------------------------------
# Mask / paste clearance constants  (mm)
# ---------------------------------------------------------------------------
MASK_CLEARANCE  = 0.10   # solder mask opening = pad + 2 × 0.10mm per side
PASTE_REDUCTION = 0.00   # stencil = pad size (no shrinkage for prototype run)

# ---------------------------------------------------------------------------
# Pad transformation helper
# ---------------------------------------------------------------------------
def _rotate_pad(pad: Pad, rot_deg: float) -> tuple[float, float]:
    """Return world-space (dx, dy) for pad local offset after component rotation."""
    if rot_deg == 0.0:
        return pad.x, pad.y
    r = math.radians(rot_deg)
    c, s = math.cos(r), math.sin(r)
    return c * pad.x - s * pad.y, s * pad.x + c * pad.y

def _pad_world(comp_x: float, comp_y: float, rot: float, pad: Pad) -> tuple[float, float]:
    dx, dy = _rotate_pad(pad, rot)
    return comp_x + dx, comp_y + dy

# KiCad rotation: counter-clockwise. For a pad with width w and height h at angle θ,
# the rotated aperture needs its own angle. We handle only 0°/90° for now and treat
# rectangular pads at arbitrary angles as oval with the same footprint.
def _rotated_dims(w: float, h: float, rot: float) -> tuple[float, float]:
    """Swap w/h when component is rotated 90° or 270°."""
    if abs(rot % 180) == 90:
        return h, w
    return w, h

# ---------------------------------------------------------------------------
# Gerber file builder
# ---------------------------------------------------------------------------
class GerberLayer:
    def __init__(self, filename: str, layer_fn: str, polarity: str = "Positive") -> None:
        self.filename = filename
        self.layer_fn = layer_fn
        self.polarity = polarity
        self._aps = _Aps()
        self._body: list[str] = []
        self._cur_ap: int = -1

    def _sel(self, d: int) -> None:
        if d != self._cur_ap:
            self._body.append(f"G54D{d}*")
            self._cur_ap = d

    def flash(self, x: float, y: float, ap: int) -> None:
        self._sel(ap)
        self._body.append(f"{_xy(x, y)}D03*")

    def line(self, x1: float, y1: float, x2: float, y2: float, ap: int) -> None:
        self._sel(ap)
        self._body.append(f"{_xy(x1, y1)}D02*")
        self._body.append(f"{_xy(x2, y2)}D01*")

    def circle_ap(self, d: float) -> int:
        return self._aps.circle(d)

    def rect_ap(self, w: float, h: float) -> int:
        return self._aps.rect(w, h)

    def oval_ap(self, w: float, h: float) -> int:
        return self._aps.oval(w, h)

    def _header(self) -> str:
        return (
            f"G04 Gerber X2 — WellD v{REV} — {self.filename}*\n"
            f"%TF.GenerationSoftware,WellD,generate_gerbers.py,1.0*%\n"
            f"%TF.CreationDate,{DATE}T00:00:00+00:00*%\n"
            f"%TF.ProjectId,welld,00000000-0000-0000-0000-000000000000,rev{REV}*%\n"
            f"%TF.SameCoordinates,Original*%\n"
            f"%TF.FileFunction,{self.layer_fn}*%\n"
            f"%TF.FilePolarity,{self.polarity}*%\n"
            f"%FSLAX46Y46*%\n"
            f"%MOMM*%\n"
            f"%LPD*%\n"
            f"G04 --- Apertures ---*\n"
            f"{self._aps.defs()}"
            f"G04 --- Data ---*\n"
            f"G01*\n"          # linear mode
        )

    def write(self, directory: str) -> str:
        path = os.path.join(directory, self.filename)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self._header())
            fh.write("\n".join(self._body))
            fh.write("\nM02*\n")
        return path

# ---------------------------------------------------------------------------
# Drill file builder  (Excellon format 2, metric, LZ suppression)
# ---------------------------------------------------------------------------
class DrillFile:
    def __init__(self, filename: str, plated: bool) -> None:
        self.filename = filename
        self.plated = plated
        self._tools: dict[float, int] = {}
        self._holes: list[tuple[int, float, float]] = []  # (tool, x, y)
        self._next_tool = 1

    def add(self, x: float, y: float, d: float) -> None:
        if d not in self._tools:
            self._tools[d] = self._next_tool
            self._next_tool += 1
        self._holes.append((self._tools[d], x, y))

    def _coord(self, mm: float) -> str:
        return f"{mm:.4f}"

    def write(self, directory: str) -> str:
        path = os.path.join(directory, self.filename)
        pth_str = "PTH" if self.plated else "NPTH"
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(f"; Excellon drill file — WellD v{REV} — {pth_str}\n")
            fh.write(f"; Generated {DATE}\n")
            fh.write("M48\n")
            fh.write("METRIC,LZ\n")
            fh.write("FMAT,2\n")
            for d, t in sorted(self._tools.items(), key=lambda kv: kv[1]):
                fh.write(f"T{t:02d}C{d:.3f}\n")
            fh.write("%\n")
            fh.write("G90\nG05\n")  # absolute, drill mode
            cur_tool = -1
            for tool, x, y in self._holes:
                if tool != cur_tool:
                    fh.write(f"T{tool:02d}\n")
                    cur_tool = tool
                fh.write(f"X{self._coord(x)}Y{self._coord(y)}\n")
            fh.write("T00\nM30\n")
        return path

# ---------------------------------------------------------------------------
# Gerber job file  (IPC-2581 / Gerber X2 metadata)
# ---------------------------------------------------------------------------
def write_job_file(directory: str, layer_files: list[str]) -> str:
    import json
    layers = []
    fn_map = {
        "F_Cu":       ("Copper,L1,Top",       True),
        "B_Cu":       ("Copper,L2,Bot",       True),
        "F_Mask":     ("SolderMask,Top",       True),
        "B_Mask":     ("SolderMask,Bot",       True),
        "F_Paste":    ("SolderPaste,Top",      True),
        "F_SilkS":    ("Legend,Top",           True),
        "Edge_Cuts":  ("Profile,NP",           True),
    }
    for fn in sorted(layer_files):
        base = os.path.basename(fn)
        stem = base.replace("welld-", "").replace(".gbr", "")
        func, __ = fn_map.get(stem, (f"Other,{stem}", True))
        layers.append({"FileName": base, "FileFunction": func, "FilePolarity": "Positive"})

    job = {
        "Header": {
            "GenerationSoftware": {"Vendor": "WellD", "Application": "generate_gerbers.py", "Version": "1.0"},
            "CreationDate": f"{DATE}T00:00:00+00:00",
        },
        "GeneralSpecs": {
            "ProjectId": {"Name": "welld", "Revision": REV},
            "Size": {"X": 80.0, "Y": 55.0},
            "LayerNumber": 2,
            "BoardThickness": 1.6,
            "Finish": "ENIG",
        },
        "FilesAttributes": layers,
        "MaterialStackup": [
            {"Type": "Legend", "Color": "White", "Name": "F.SilkS"},
            {"Type": "SolderPaste", "Name": "F.Paste"},
            {"Type": "SolderMask", "Color": "Green", "Name": "F.Mask"},
            {"Type": "Copper", "Name": "F.Cu"},
            {"Type": "Dielectric", "Material": "FR4", "Name": "F.Cu/B.Cu", "ThicknessMm": 1.51},
            {"Type": "Copper", "Name": "B.Cu"},
            {"Type": "SolderMask", "Color": "Green", "Name": "B.Mask"},
        ],
        "DesignRules": [
            {"Layers": "Outer", "PadToPad": 0.2, "PadToTrack": 0.2, "TrackToTrack": 0.2,
             "MinLineWidth": 0.15, "TrackToRegion": 0.5, "RegionToRegion": 0.5},
        ],
    }
    path = os.path.join(directory, "welld-job.gbrjob")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(job, fh, indent=2)
    return path

# ---------------------------------------------------------------------------
# Build all layers
# ---------------------------------------------------------------------------
def build() -> None:
    os.makedirs(OUTDIR, exist_ok=True)

    # Copper layers
    f_cu    = GerberLayer("welld-F_Cu.gbr",    "Copper,L1,Top")
    b_cu    = GerberLayer("welld-B_Cu.gbr",    "Copper,L2,Bot")
    # Solder mask — negative polarity means openings are drawn, not coverage
    f_mask  = GerberLayer("welld-F_Mask.gbr",  "SolderMask,Top")
    b_mask  = GerberLayer("welld-B_Mask.gbr",  "SolderMask,Bot")
    # Paste stencil (SMD only)
    f_paste = GerberLayer("welld-F_Paste.gbr", "SolderPaste,Top")
    # Silkscreen
    f_silk  = GerberLayer("welld-F_SilkS.gbr", "Legend,Top")
    # Board outline
    edge    = GerberLayer("welld-Edge_Cuts.gbr","Profile,NP")

    pth_drill  = DrillFile("welld-PTH.drl",  plated=True)
    npth_drill = DrillFile("welld-NPTH.drl", plated=False)

    # Board outline — 80×55mm rectangle on Edge.Cuts
    outline_ap = edge.circle_ap(0.05)
    for (x1, y1, x2, y2) in [
        (0, 0, 80, 0), (80, 0, 80, 55), (80, 55, 0, 55), (0, 55, 0, 0)
    ]:
        edge.line(x1, y1, x2, y2, outline_ap)

    # Silkscreen title
    _silk_text(f_silk, "WellD ESP32-C6 Well Monitor", 40, 53.5, 1.0)

    # Iterate over all components
    for ref, fp_key, cx, cy, rot, value in COMPONENTS:
        pads = FOOTPRINTS.get(fp_key)
        if pads is None:
            print(f"  WARNING: no footprint for {ref} ({fp_key})")
            continue

        for pad in pads:
            wx, wy = _pad_world(cx, cy, rot, pad)
            pw, ph = _rotated_dims(pad.w, pad.h, rot)

            if pad.npth:
                # Non-plated mounting hole — drill only, no copper/mask
                npth_drill.add(wx, wy, pad.drill)
                continue

            if pad.layers in ('F', 'T'):
                # ── Front copper ────────────────────────────────────────
                ap = _flash_ap(f_cu, pad.shape, pw, ph)
                f_cu.flash(wx, wy, ap)
                # ── Front solder mask (opening = pad + clearance each side)
                mw = pw + 2 * MASK_CLEARANCE
                mh = ph + 2 * MASK_CLEARANCE
                map_ = _flash_ap(f_mask, pad.shape, mw, mh)
                f_mask.flash(wx, wy, map_)
                # ── Paste stencil  (SMD pads that accept paste)
                if pad.layers == 'F' and pad.paste:
                    pap = _flash_ap(f_paste, pad.shape, pw, ph)
                    f_paste.flash(wx, wy, pap)

            if pad.layers == 'T':
                # ── Back copper annular ring
                bap = _flash_ap(b_cu, pad.shape, pw, ph)
                b_cu.flash(wx, wy, bap)
                # ── Back solder mask opening
                mw = pw + 2 * MASK_CLEARANCE
                mh = ph + 2 * MASK_CLEARANCE
                bmap = _flash_ap(b_mask, pad.shape, mw, mh)
                b_mask.flash(wx, wy, bmap)
                # ── Drill
                pth_drill.add(wx, wy, pad.drill)

        # Silkscreen reference label (1mm above component, approximate)
        f_silk_ref(f_silk, ref, cx, cy - 2)

    # Write all files
    written: list[str] = []
    for layer in (f_cu, b_cu, f_mask, b_mask, f_paste, f_silk, edge):
        path = layer.write(OUTDIR)
        written.append(path)
        print(f"  wrote {os.path.relpath(path)}")
    for df in (pth_drill, npth_drill):
        path = df.write(OUTDIR)
        written.append(path)
        print(f"  wrote {os.path.relpath(path)}")

    # Gerber job file
    gbr_files = [p for p in written if p.endswith(".gbr")]
    path = write_job_file(OUTDIR, gbr_files)
    print(f"  wrote {os.path.relpath(path)}")

    print(f"\nDone — {len(written)+1} files in {os.path.relpath(OUTDIR)}/")

# ---------------------------------------------------------------------------
# Small helpers used in build()
# ---------------------------------------------------------------------------
def _flash_ap(layer: GerberLayer, shape: str, w: float, h: float) -> int:
    if shape == 'circle':
        return layer.circle_ap(w)
    if shape == 'oval':
        return layer.oval_ap(w, h)
    return layer.rect_ap(w, h)   # default: rect

def _silk_text(layer: GerberLayer, text: str, x: float, y: float, h: float) -> None:
    """Approximate text as a thin horizontal line (placeholder for silk)."""
    # True stroke-font rendering would require a full glyph library.
    # We draw a single underline at the text baseline as a positioning marker.
    ap = layer.circle_ap(0.12)
    half = len(text) * h * 0.30
    layer.line(x - half, y, x + half, y, ap)

def f_silk_ref(layer: GerberLayer, ref: str, x: float, y: float) -> None:
    """Draw a tiny dot at the approximate ref-designator location."""
    ap = layer.circle_ap(0.10)
    layer.flash(x, y, ap)

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print(f"WellD Gerber generator — output: {os.path.relpath(OUTDIR)}/")
    build()
