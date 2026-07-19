#!/usr/bin/env python3
"""WellD schematic wiring generator (2026-07-13 wiring pass).

Gives every symbol pin in power/mcu/sensors/interfaces.kicad_sch its electrical
connectivity using *stub + label* connectivity (a 2.54 mm grid-aligned wire stub
from each pin endpoint plus a net label on the stub), which is electrically
identical to point-to-point wiring for netlisting/ERC purposes.

Authoritative source for the net table below: schematic_connections.md.

Connectivity scheme
-------------------
* Power rails  -> global labels on every stub  (GLOBAL_NETS)
* Cross-sheet signals -> hierarchical labels on every stub + matching sheet
  pins on welld.kicad_sch, joined at the root by short stubs + local labels
  (computed automatically: any non-global net used in >1 sheet)
* Sheet-local nets -> local labels
* Unused pins -> explicit (no_connect) markers  (NC_PINS)

The script is idempotent: it first strips every top-level wire / label /
no_connect / junction element (and the decorative #PWR power symbols) from the
four sub-sheets, and rebuilds the sheet-pin lists on welld.kicad_sch, then
regenerates everything from the table.

Run:  python3 hardware/pcb/kicad_wire_script.py
Then: python3 hardware/pcb/netlist_check.py   (verifies files vs the table)
"""

import math
import os
import re
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
SHEETS = ["power", "mcu", "sensors", "interfaces"]
TOP = "welld"
STUB = 2.54  # mm

# ---------------------------------------------------------------------------
# NET TABLE  (sheet -> net -> ["REF.PIN", ...])  — from schematic_connections.md
# ---------------------------------------------------------------------------

GLOBAL_NETS = {
    "GND", "+3V3", "+3V3_ADS", "VBAT", "VBAT_RAW", "VLOOP",
    "VUSB", "VUSB_IN", "VSOLAR", "VSOLAR_IN",
}

NETS = {
    # =====================================================================
    "power": {
        "GND": [
            "U1.1", "U7.2", "U8.2", "U12.3", "U12.9",
            "RT1.2", "R_PROG.2", "R_COM.2",
            "D_SOLAR.2",           # catch Schottky anode
            "R24.2", "R21.2", "R27.2", "R31.2",
            "R50.2", "R51.2",
            "C9.2", "C10.2", "C16.2", "C11.2", "C12.2", "C_BUCK.2",
            "C17.2", "C21.2", "C18.2", "C19.2", "C20.2", "C22.2",
            "C27.2", "C28.2", "C29.2",
            "D11.2", "D13.2", "D14.2", "D8.2",
            "Q4.S", "Q6.6", "Q6.7", "R_CS_DW.2", "J12.2", "J13.A1", "U11.2",
        ],
        "+3V3": [
            "U1.2",                # HT7333-A VOUT
            "C_BUCK.1", "C11.1", "C12.1",
            "R25.1", "R38.1", "R22.1",
        ],
        "VBAT": [
            "U1.3", "C9.1", "C10.1", "C16.1",
            "U7.7", "R19.2", "C18.1",
            "U8.5", "C19.1",
            "Q3.2", "Q5.2", "R29.1", "R16.1",
            "U12.5", "C29.1",
            "D5.2",
        ],
        "VBAT_RAW": ["BT1.1", "D13.1", "D5.3", "R_DW1.1"],
        # --- 1S protection (DW01A + FS8205A) between cell- and system GND ---
        "BATT_N": ["BT1.2", "Q6.2", "Q6.3", "U13.6", "C_DW.2"],
        "DW_VCC": ["R_DW1.2", "U13.5", "C_DW.1"],
        "DW_OD": ["U13.1", "Q6.4"],
        "DW_OC": ["U13.3", "Q6.5"],
        "DW_CS": ["U13.2", "R_CS_DW.1"],
        "DW_D": ["Q6.1", "Q6.8"],
        "D5_GATE": ["D5.1", "R31.1"],
        # --- MT3608B boost + Q3/Q4 disconnect ---
        "VLOOP_L": ["Q3.3", "L1.1"],
        "Q3_GATE": ["Q3.1", "R29.2", "Q4.D"],
        "VBOOST_EN": ["U8.4", "Q4.G", "R27.1"],
        "VLOOP_SW": ["U8.1", "L1.2", "D15.2", "C_BST.2"],
        "MT_BST": ["U8.6", "C_BST.1"],   # pin 6 possibly NC — see report
        "MT_FB": ["U8.3", "R23.2", "R24.1"],
        "VLOOP": ["D15.1", "C20.1", "C22.1", "R23.1", "D11.1"],
        # --- CN3791 solar charger (integrated buck switch, 1S 4.2 V CV) ---
        "VSOLAR_IN": ["J12.1", "D14.1", "D6.2"],
        "VSOLAR": [
            "D6.1", "D8.1", "U7.9", "C17.1", "C21.1", "R20.1",
            "C_VG.2", "M_SOLAR.2", "R_DRV.1",
        ],
        "MPPT_REF": ["R20.2", "R21.1", "U7.6"],
        "CN_VG": ["U7.1", "C_VG.1"],
        "CN_DRV": ["U7.10", "M_SOLAR.1", "R_DRV.2"],
        "SOLAR_SW": ["M_SOLAR.3", "D16.2"],
        "SOLAR_FW": ["D16.1", "D_SOLAR.1", "L_SOLAR.1"],
        "CN_CS": ["L_SOLAR.2", "R19.1", "U7.8"],
        "CN_COM": ["U7.5", "C_COM.1"],
        "COM_RC": ["C_COM.2", "R_COM.1"],
        "/CHRG_SOLAR": ["U7.3", "R25.2", "D7.1"],
        "D7_A": ["D7.2", "R22.2"],
        # --- USB input + TP4056 linear charger ---
        "VUSB_IN": ["J13.A4", "U11.5", "F2.1"],
        "USB_DP": ["J13.A6", "U11.3"],
        "USB_DM": ["J13.A7", "U11.1"],
        "CC1": ["J13.A5", "R50.1"],
        "CC2": ["J13.B5", "R51.1"],
        "VUSB": ["F2.2", "C27.1", "C28.1", "U12.4",
                 "U12.8",           # CE strapped high = charge whenever VBUS
                 "R_NTC.1"],
        "USB_NTC": ["U12.1", "RT1.1", "R_NTC.2"],
        "USB_PROG": ["U12.2", "R_PROG.1"],
        "/CHRG_USB": ["U12.7", "R38.2"],
        # --- battery divider high-side switch (rest of chain in sensors) ---
        "Q5_GATE": ["Q5.1", "R16.2"],
        "VBAT_SW": ["Q5.3"],
    },
    # =====================================================================
    "mcu": {
        "GND": [
            "U6.1", "U6.40",
            "C13.2", "C30.2", "C31.2", "C32.2", "C33.2", "C15.2",
            "C36.2", "SW1.2", "SW2.2",
        ],
        "+3V3": [
            "U6.2", "U6.3",
            "C13.1", "C30.1", "C31.1", "C32.1", "C33.1", "C15.1",
            "R12.1", "R13.1", "R15.1",
        ],
        "EN": ["U6.5", "R15.2", "C36.1", "SW1.1"],
        "BOOT": ["U6.14", "R12.2", "SW2.1"],
        "GPIO8": ["U6.13", "R13.2"],
        "GPIO0": ["U6.15"],
        "GPIO1": ["U6.16"],
        "GPIO2": ["U6.17"],
        "GPIO3": ["U6.18"],
        "GPIO20": ["U6.33"],
        "GPIO21": ["U6.34"],
        "VBOOST_EN": ["U6.20"],
        "/CHRG_SOLAR": ["U6.21"],
        "1WIRE": ["U6.22"],
        "I2C_SDA": ["U6.23"],
        "I2C_SCL": ["U6.24"],
        "ADS_DRDY": ["U6.25"],
        "BATT_DIV_EN": ["U6.30"],
        "UART_TX": ["U6.31"],
        "UART_RX": ["U6.32"],
        "FACTORY_RESET": ["U6.28", "TP13.1"],
        "GPIO14_LED": ["U6.29", "R14.1"],
        "LED_A": ["R14.2", "D4.2"],
        "LED_K": ["D4.1"],
    },
    # =====================================================================
    "sensors": {
        "GND": [
            "U9.3", "U9.1",        # ADDR -> GND = I2C addr 0x48
            "C23.2", "C24.2",
            "C3.2", "C4.2", "C5.2", "C6.2", "C7.2", "C8.2",
            "C34.2", "C35.2",
            "D1.1", "D12.1",
            "D9.2", "D10.2",
            "R2.2", "R4.2", "R8.2", "R26.2",
            "Q2.S", "J4.3", "J5.3", "J6.3", "J7.3",
            "GDT1.2", "GDT2.2",   # GDT coarse surge stage returns (DNF)
        ],
        "+3V3": [
            "FB1.1", "R_DRDY.1", "R6.1", "R28.1",
            "D1.4", "D12.4",
            "J7.1",
        ],
        "+3V3_ADS": ["FB1.2", "U9.8", "C23.1", "C24.1"],
        "I2C_SDA": ["U9.9"],
        "I2C_SCL": ["U9.10"],
        "ADS_DRDY": ["U9.2", "R_DRDY.2"],
        # CH1 4-20 mA chain
        "VLOOP": ["J4.1"],
        "LOOP_TERM_CH1": ["J4.2", "D9.1", "R2.1", "C34.1", "R3.1", "GDT1.1"],
        "ADC_CH0": ["U9.4", "R3.2", "C3.1", "C4.1", "D1.2"],
        # CH2 4-20 mA chain (loop power gated by SJ2 on interfaces sheet)
        "VLOOP_CH2": ["J5.1"],
        "LOOP_TERM_CH2": ["J5.2", "D10.1", "R4.1", "C35.1", "R5.1", "GDT2.1"],
        "ADC_CH1": ["U9.5", "R5.2", "C5.1", "C6.1", "D1.3"],
        # battery divider (high-side switch Q5/R16 on power sheet)
        "VBAT_SW": ["R7.1"],
        "ADC_CH2": ["U9.6", "R7.2", "R8.1", "C8.1"],
        "Q5_GATE": ["Q2.D"],
        "BATT_DIV_EN": ["Q2.G", "R26.1"],
        # DS18B20
        "J6_VCC": ["J6.1", "R28.2", "C7.1"],
        "1WIRE_TERM": ["J6.2", "D12.2", "R6.2", "R32.1"],
        "1WIRE": ["R32.2"],
        # spare sensor header
        "GPIO3": ["J7.2"],
    },
    # =====================================================================
    "interfaces": {
        "GND": ["J10.3", "J8.2", "J9.2", "J3.2", "SJ3.2", "TP4.1"],
        "+3V3": ["J10.4", "J8.1", "J9.1", "R9.1", "R10.1", "TP3.1"],
        "VBAT": ["TP1.1", "SJ1.2"],
        "VLOOP": ["TP2.1", "SJ2.1"],
        "VLOOP_CH2": ["SJ2.2"],
        "VBAT_RAW": ["TP11.1"],
        "VSOLAR_IN": ["TP10.1"],
        "UART_TX": ["SJ4.1"],
        "UART_TX_HDR": ["SJ4.2", "J10.1"],
        "UART_RX": ["SJ5.1"],
        "UART_RX_HDR": ["SJ5.2", "J10.2"],
        "BOOT": ["J10.5"],
        "EN": ["J10.6"],
        "I2C_SDA": ["R9.2", "J8.3", "TP8.1"],
        "I2C_SCL": ["R10.2", "J8.4", "TP9.1"],
        "1WIRE": ["TP7.1"],
        "ADS_DRDY": ["TP12.1"],
        "VBOOST_EN": ["SJ1.1"],
        "LED_K": ["SJ3.1"],
        "LOOP_TERM_CH1": ["TP5.1"],
        "LOOP_TERM_CH2": ["TP6.1"],
        "/CHRG_SOLAR": ["TP14.1"],
        "/CHRG_USB": ["TP15.1"],
        "GPIO0": ["J9.3"],
        "GPIO1": ["J9.4"],
        "GPIO2": ["J9.5"],
        "GPIO3": ["J9.6"],
        "GPIO20": ["J9.7"],
        "GPIO21": ["J9.8"],
    },
}

# Explicit no-connects (see schematic_connections.md + wiring-pass decisions)
NC_PINS = {
    "power": [
        "U7.4",    # CN3791 /DONE — no spare GPIO (pad available for a TP)
        "U11.6", "U11.4",   # USBLC6 device-side line ends (DM/DP float)
        "U12.6",   # TP4056 /STDBY — unused (only /CHRG is monitored)
        "U13.4",   # DW01A TD (test/delay pin — float per every reference design)
    ],
    "mcu": [
        "U6.19",   # GPIO4 — spare (TP4056 CE strapped high in hardware, no charger GPIO)
        "U6.26",   # GPIO18 — unused
        "U6.27",   # GPIO19 — unused
    ],
    "sensors": [
        "U9.7",    # ADS1115 AIN3 unused
        "D12.3",   # PRTR5V0U2X IO2 unused on 1-Wire clamp
    ],
    "interfaces": [
        "J3.1",    # SMA RF pin — no PCB trace (W1 pigtail carries RF)
    ],
}

# Sheet-pin sides on the top sheet (cosmetic): pins face the sheet's neighbour
SHEET_PIN_SIDE = {"power": "right", "mcu": "left",
                  "sensors": "right", "interfaces": "left"}

# PWR_FLAG placement: rails that carry power_in pins but no power_out driver
# (KiCad ERC "power input not driven" would fire otherwise).  One flag per
# rail, on the sheet that sources the rail.  (x, y) are free sheet areas.
PWR_FLAGS = {
    "power": [("GND", 40.64, 205.74), ("+3V3", 60.96, 205.74),
              ("VUSB", 81.28, 205.74), ("VSOLAR", 101.6, 205.74)],
    "sensors": [("+3V3_ADS", 40.64, 205.74)],
}

ROOT_UUID = "58c9365f-ec30-52a7-98fc-0e15b15bee29"
SHEET_UUIDS = {
    "power": "64fba67a-e021-5c3c-b6fb-14c5c55ee35f",
    "mcu": "2b6726ca-47e0-5ff0-b8ba-45087cce0cf4",
    "sensors": "0c45da4f-3a65-5906-aac7-f973a0770f80",
    "interfaces": "605e54e1-9b70-5889-bd12-97a0469e9e42",
}

PWR_FLAG_LIB = '''\t\t(symbol "power:PWR_FLAG"
\t\t\t(power global)
\t\t\t(pin_numbers
\t\t\t\t(hide yes)
\t\t\t)
\t\t\t(pin_names
\t\t\t\t(offset 0)
\t\t\t\t(hide yes)
\t\t\t)
\t\t\t(exclude_from_sim no)
\t\t\t(in_bom yes)
\t\t\t(on_board yes)
\t\t\t(in_pos_files yes)
\t\t\t(duplicate_pin_numbers_are_jumpers no)
\t\t\t(property "Reference" "#FLG"
\t\t\t\t(at 0 1.905 0)
\t\t\t\t(show_name no)
\t\t\t\t(do_not_autoplace no)
\t\t\t\t(hide yes)
\t\t\t\t(effects
\t\t\t\t\t(font
\t\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t\t)
\t\t\t\t)
\t\t\t)
\t\t\t(property "Value" "PWR_FLAG"
\t\t\t\t(at 0 3.81 0)
\t\t\t\t(show_name no)
\t\t\t\t(do_not_autoplace no)
\t\t\t\t(effects
\t\t\t\t\t(font
\t\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t\t)
\t\t\t\t)
\t\t\t)
\t\t\t(property "Footprint" ""
\t\t\t\t(at 0 0 0)
\t\t\t\t(show_name no)
\t\t\t\t(do_not_autoplace no)
\t\t\t\t(hide yes)
\t\t\t\t(effects
\t\t\t\t\t(font
\t\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t\t)
\t\t\t\t)
\t\t\t)
\t\t\t(property "Datasheet" ""
\t\t\t\t(at 0 0 0)
\t\t\t\t(show_name no)
\t\t\t\t(do_not_autoplace no)
\t\t\t\t(hide yes)
\t\t\t\t(effects
\t\t\t\t\t(font
\t\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t\t)
\t\t\t\t)
\t\t\t)
\t\t\t(property "Description" "Special symbol for telling ERC where power comes from"
\t\t\t\t(at 0 0 0)
\t\t\t\t(show_name no)
\t\t\t\t(do_not_autoplace no)
\t\t\t\t(hide yes)
\t\t\t\t(effects
\t\t\t\t\t(font
\t\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t\t)
\t\t\t\t)
\t\t\t)
\t\t\t(property "ki_keywords" "flag power"
\t\t\t\t(at 0 0 0)
\t\t\t\t(show_name no)
\t\t\t\t(do_not_autoplace no)
\t\t\t\t(hide yes)
\t\t\t\t(effects
\t\t\t\t\t(font
\t\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t\t)
\t\t\t\t)
\t\t\t)
\t\t\t(symbol "PWR_FLAG_0_0"
\t\t\t\t(pin power_out line
\t\t\t\t\t(at 0 0 90)
\t\t\t\t\t(length 0)
\t\t\t\t\t(name ""
\t\t\t\t\t\t(effects
\t\t\t\t\t\t\t(font
\t\t\t\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t\t\t\t)
\t\t\t\t\t\t)
\t\t\t\t\t)
\t\t\t\t\t(number "1"
\t\t\t\t\t\t(effects
\t\t\t\t\t\t\t(font
\t\t\t\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t\t\t\t)
\t\t\t\t\t\t)
\t\t\t\t\t)
\t\t\t\t)
\t\t\t)
\t\t\t(symbol "PWR_FLAG_1_1"
\t\t\t\t(polyline
\t\t\t\t\t(pts
\t\t\t\t\t\t(xy 0 0) (xy 0 1.27) (xy -1.016 1.905) (xy 0 2.54) (xy 1.016 1.905) (xy 0 1.27)
\t\t\t\t\t)
\t\t\t\t\t(stroke
\t\t\t\t\t\t(width 0)
\t\t\t\t\t\t(type default)
\t\t\t\t\t)
\t\t\t\t\t(fill
\t\t\t\t\t\t(type none)
\t\t\t\t\t)
\t\t\t\t)
\t\t\t)
\t\t\t(embedded_fonts no)
\t\t)
'''


def emit_pwr_flag(ref, x, y, sheet_uuid):
    return (
        '(symbol\n'
        '\t\t(lib_id "power:PWR_FLAG")\n'
        '\t\t(at %s %s 0)\n'
        '\t\t(unit 1)\n'
        '\t\t(body_style 1)\n'
        '\t\t(exclude_from_sim no)\n'
        '\t\t(in_bom yes)\n'
        '\t\t(on_board yes)\n'
        '\t\t(in_pos_files yes)\n'
        '\t\t(dnp no)\n'
        '\t\t(fields_autoplaced yes)\n'
        '\t\t(uuid "%s")\n'
        '\t\t(property "Reference" "%s"\n'
        '\t\t\t(at %s %s 0)\n'
        '\t\t\t(show_name no)\n'
        '\t\t\t(do_not_autoplace no)\n'
        '\t\t\t(hide yes)\n'
        '\t\t\t(effects\n'
        '\t\t\t\t(font\n'
        '\t\t\t\t\t(size 1.27 1.27)\n'
        '\t\t\t\t)\n'
        '\t\t\t)\n'
        '\t\t)\n'
        '\t\t(property "Value" "PWR_FLAG"\n'
        '\t\t\t(at %s %s 0)\n'
        '\t\t\t(show_name no)\n'
        '\t\t\t(do_not_autoplace no)\n'
        '\t\t\t(effects\n'
        '\t\t\t\t(font\n'
        '\t\t\t\t\t(size 1.27 1.27)\n'
        '\t\t\t\t)\n'
        '\t\t\t)\n'
        '\t\t)\n'
        '\t\t(property "Footprint" ""\n'
        '\t\t\t(at 0 0 0)\n'
        '\t\t\t(hide yes)\n'
        '\t\t\t(show_name no)\n'
        '\t\t\t(do_not_autoplace no)\n'
        '\t\t\t(effects\n'
        '\t\t\t\t(font\n'
        '\t\t\t\t\t(size 1.27 1.27)\n'
        '\t\t\t\t)\n'
        '\t\t\t)\n'
        '\t\t)\n'
        '\t\t(property "Datasheet" ""\n'
        '\t\t\t(at 0 0 0)\n'
        '\t\t\t(hide yes)\n'
        '\t\t\t(show_name no)\n'
        '\t\t\t(do_not_autoplace no)\n'
        '\t\t\t(effects\n'
        '\t\t\t\t(font\n'
        '\t\t\t\t\t(size 1.27 1.27)\n'
        '\t\t\t\t)\n'
        '\t\t\t)\n'
        '\t\t)\n'
        '\t\t(property "Description" ""\n'
        '\t\t\t(at 0 0 0)\n'
        '\t\t\t(hide yes)\n'
        '\t\t\t(show_name no)\n'
        '\t\t\t(do_not_autoplace no)\n'
        '\t\t\t(effects\n'
        '\t\t\t\t(font\n'
        '\t\t\t\t\t(size 1.27 1.27)\n'
        '\t\t\t\t)\n'
        '\t\t\t)\n'
        '\t\t)\n'
        '\t\t(pin "1"\n'
        '\t\t\t(uuid "%s")\n'
        '\t\t)\n'
        '\t\t(instances\n'
        '\t\t\t(project "welld"\n'
        '\t\t\t\t(path "/%s/%s"\n'
        '\t\t\t\t\t(reference "%s")\n'
        '\t\t\t\t\t(unit 1)\n'
        '\t\t\t\t)\n'
        '\t\t\t)\n'
        '\t\t)\n'
        '\t)'
        % (fmt(x), fmt(y), uid(), ref, fmt(x), fmt(y - 4), fmt(x), fmt(y - 6),
           uid(), ROOT_UUID, sheet_uuid, ref)
    )

# ---------------------------------------------------------------------------
# s-expression helpers (self-contained, quote-aware)
# ---------------------------------------------------------------------------


def scan_children(text, start, end):
    """Yield (tag, s, e) spans of the direct children of the element whose
    opening '(' is at `start` (span exclusive of the outer parens)."""
    i = start + 1
    depth = 0
    in_str = False
    child_start = None
    while i < end:
        c = text[i]
        if in_str:
            if c == "\\":
                i += 1
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == "(":
            if depth == 0:
                child_start = i
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0 and child_start is not None:
                m = re.match(r"\(\s*([A-Za-z_0-9]+)", text[child_start:i + 1])
                yield (m.group(1) if m else "", child_start, i + 1)
                child_start = None
        i += 1


def root_span(text):
    s = text.index("(")
    e = text.rindex(")")
    return s, e + 1


def balanced(text):
    depth = 0
    in_str = False
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if in_str:
            if c == "\\":
                i += 1
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth < 0:
                return False
        i += 1
    return depth == 0 and not in_str


def get_str(chunk, key):
    m = re.search(r'\(%s\s+"((?:[^"\\]|\\.)*)"' % key, chunk)
    return m.group(1) if m else None


def get_at(chunk):
    m = re.search(r"\(at\s+([-\d.]+)\s+([-\d.]+)(?:\s+([-\d.]+))?\)", chunk)
    if not m:
        return None
    return float(m.group(1)), float(m.group(2)), int(float(m.group(3) or 0))


# ---------------------------------------------------------------------------
# geometry
# ---------------------------------------------------------------------------

ROT = {0: (1, 0, 0, -1), 90: (0, -1, -1, 0), 180: (-1, 0, 0, 1), 270: (0, 1, 1, 0)}


def xform(ax, ay, rot, px, py):
    a, b, c, d = ROT[rot % 360]
    return (round(ax + a * px + b * py, 4), round(ay + c * px + d * py, 4))


def out_dir(rot, pin_angle):
    """Unit vector pointing away from the symbol body, in schematic coords."""
    ang = (pin_angle + 180) % 360
    vx = round(math.cos(math.radians(ang)))
    vy = round(math.sin(math.radians(ang)))
    a, b, c, d = ROT[rot % 360]
    return (a * vx + b * vy, c * vx + d * vy)


# ---------------------------------------------------------------------------
# sheet model
# ---------------------------------------------------------------------------


class Sheet:
    def __init__(self, name):
        self.name = name
        self.path = os.path.join(HERE, f"{name}.kicad_sch")
        with open(self.path) as f:
            self.text = f.read()
        self.libs = {}       # lib_id -> [ {num,name,x,y,angle,etype} ]
        self.pins = {}       # "REF.PIN" -> dict(x, y, dir, etype)
        self._parse()

    def _parse(self):
        text = self.text
        rs, re_ = root_span(text)
        self.keep = []       # spans to keep verbatim
        self.symbol_spans = []
        strip_tags = {"wire", "label", "global_label", "hierarchical_label",
                      "no_connect", "junction", "bus", "bus_entry"}
        for tag, s, e in scan_children(text, rs, re_ - 1):
            chunk = text[s:e]
            if tag == "lib_symbols":
                self._parse_libs(chunk, s)
                self.keep.append((s, e))
            elif tag == "symbol":
                lib_id = get_str(chunk, "lib_id")
                if lib_id and lib_id.startswith("power:"):
                    continue  # drop decorative #PWR symbols
                self.symbol_spans.append((s, e))
                self.keep.append((s, e))
            elif tag in strip_tags:
                continue
            else:
                self.keep.append((s, e))

    def _parse_libs(self, chunk, offs):
        rs, re_ = root_span(chunk)
        for tag, s, e in scan_children(chunk, rs, re_ - 1):
            if tag != "symbol":
                continue
            sub = chunk[s:e]
            m = re.match(r'\(symbol\s+"((?:[^"\\]|\\.)*)"', sub)
            name = m.group(1)
            pins = []
            srs, sre = root_span(sub)
            for t2, s2, e2 in scan_children(sub, srs, sre - 1):
                if t2 != "symbol":
                    continue
                unit = sub[s2:e2]
                urs, ure = root_span(unit)
                for t3, s3, e3 in scan_children(unit, urs, ure - 1):
                    if t3 != "pin":
                        continue
                    p = unit[s3:e3]
                    at = get_at(p)
                    num = get_str(p, "number")
                    etype = re.match(r"\(pin\s+(\w+)", p).group(1)
                    pins.append(dict(num=num, x=at[0], y=at[1],
                                     angle=at[2], etype=etype))
            self.libs[name] = pins

    def resolve_pins(self):
        for s, e in self.symbol_spans:
            chunk = self.text[s:e]
            lib_id = get_str(chunk, "lib_id")
            m = re.search(r'\(property\s+"Reference"\s+"((?:[^"\\]|\\.)*)"', chunk)
            ref = m.group(1)
            at = get_at(chunk)
            ax, ay, rot = at
            for p in self.libs[lib_id]:
                x, y = xform(ax, ay, rot, p["x"], p["y"])
                d = out_dir(rot, p["angle"])
                self.pins[f"{ref}.{p['num']}"] = dict(x=x, y=y, dir=d,
                                                      etype=p["etype"])

    def rebuild(self, new_elements):
        """Rewrite file: kept children + new elements, inside original root."""
        text = self.text
        rs, re_ = root_span(text)
        gen = list(scan_children(text, rs, re_ - 1))
        first_any = gen[0][1]
        parts = [text[:first_any]]
        for s, e in self.keep:
            parts.append(text[s:e])
            parts.append("\n\t")
        for el in new_elements:
            parts.append(el)
            parts.append("\n\t")
        out = "".join(parts).rstrip() + "\n)\n"
        return out


# ---------------------------------------------------------------------------
# element emitters
# ---------------------------------------------------------------------------


def uid():
    return str(uuid.uuid4())


def fmt(v):
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return s if s else "0"


def emit_wire(x1, y1, x2, y2):
    return ("(wire\n\t\t(pts\n\t\t\t(xy %s %s) (xy %s %s)\n\t\t)\n"
            "\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n"
            "\t\t(uuid \"%s\")\n\t)" % (fmt(x1), fmt(y1), fmt(x2), fmt(y2), uid()))


def _justify(rot):
    return {0: "left", 90: "left", 180: "right", 270: "right"}[rot]


def emit_local_label(name, x, y, rot):
    return ("(label \"%s\"\n\t\t(at %s %s %d)\n\t\t(effects\n"
            "\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n"
            "\t\t\t(justify %s bottom)\n\t\t)\n\t\t(uuid \"%s\")\n\t)"
            % (name, fmt(x), fmt(y), rot, _justify(rot), uid()))


def emit_global_label(name, x, y, rot):
    return ("(global_label \"%s\"\n\t\t(shape passive)\n\t\t(at %s %s %d)\n"
            "\t\t(fields_autoplaced yes)\n\t\t(effects\n"
            "\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n"
            "\t\t\t(justify %s)\n\t\t)\n\t\t(uuid \"%s\")\n"
            "\t\t(property \"Intersheetrefs\" \"${INTERSHEET_REFS}\"\n"
            "\t\t\t(at %s %s 0)\n\t\t\t(hide yes)\n\t\t\t(show_name no)\n"
            "\t\t\t(do_not_autoplace no)\n\t\t\t(effects\n"
            "\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n"
            "\t\t)\n\t)"
            % (name, fmt(x), fmt(y), rot, _justify(rot), uid(), fmt(x), fmt(y)))


def emit_hier_label(name, x, y, rot):
    return ("(hierarchical_label \"%s\"\n\t\t(shape bidirectional)\n"
            "\t\t(at %s %s %d)\n\t\t(effects\n"
            "\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n"
            "\t\t\t(justify %s)\n\t\t)\n\t\t(uuid \"%s\")\n\t)"
            % (name, fmt(x), fmt(y), rot, _justify(rot), uid()))


def emit_no_connect(x, y):
    return "(no_connect\n\t\t(at %s %s)\n\t\t(uuid \"%s\")\n\t)" % (fmt(x), fmt(y), uid())


def dir_rot(d):
    return {(1, 0): 0, (-1, 0): 180, (0, -1): 90, (0, 1): 270}[d]


# ---------------------------------------------------------------------------
# collision guard: no cross-net stub/label contact
# ---------------------------------------------------------------------------


def seg_contains(p, a, b):
    (px, py), (ax, ay), (bx, by) = p, a, b
    if min(ax, bx) - 1e-6 <= px <= max(ax, bx) + 1e-6 and \
       min(ay, by) - 1e-6 <= py <= max(ay, by) + 1e-6:
        cross = (bx - ax) * (py - ay) - (by - ay) * (px - ax)
        return abs(cross) < 1e-6
    return False


class Islands:
    """Track per-net stub geometry and all pin endpoints for collision checks."""

    def __init__(self):
        self.segs = []    # (net, a, b)
        self.points = []  # (net, p)  — pin endpoints and stub ends

    def ok(self, net, a, b):
        for n2, p in self.points:
            if n2 != net and (seg_contains(p, a, b)):
                return False
        for n2, a2, b2 in self.segs:
            if n2 == net:
                continue
            if seg_contains(a, a2, b2) or seg_contains(b, a2, b2) or \
               seg_contains(a2, a, b) or seg_contains(b2, a, b):
                return False
        return True

    def add_seg(self, net, a, b):
        self.segs.append((net, a, b))
        self.points.append((net, a))
        self.points.append((net, b))

    def add_point(self, net, p):
        self.points.append((net, p))


# ---------------------------------------------------------------------------
# main generation
# ---------------------------------------------------------------------------


def cross_sheet_nets():
    seen = {}
    for sheet, nets in NETS.items():
        for net in nets:
            seen.setdefault(net, set()).add(sheet)
    return {n: s for n, s in seen.items() if len(s) > 1 and n not in GLOBAL_NETS}


def generate():
    hier = cross_sheet_nets()
    report = {}
    for name in SHEETS:
        sh = Sheet(name)
        sh.resolve_pins()

        # sanity: full pin coverage, no unknown pins in the table
        table_pins = set()
        for net, plist in NETS[name].items():
            for p in plist:
                if p in table_pins:
                    raise SystemExit(f"{name}: duplicate table entry {p}")
                table_pins.add(p)
        nc = set(NC_PINS.get(name, []))
        overlap = table_pins & nc
        if overlap:
            raise SystemExit(f"{name}: pins both wired and NC: {overlap}")
        missing = set(sh.pins) - table_pins - nc
        unknown = (table_pins | nc) - set(sh.pins)
        if missing:
            raise SystemExit(f"{name}: pins with no net assignment: {sorted(missing)}")
        if unknown:
            raise SystemExit(f"{name}: table references unknown pins: {sorted(unknown)}")

        isl = Islands()
        # register every pin endpoint first (so stubs can't cross foreign pins)
        pin_net = {}
        for net, plist in NETS[name].items():
            for p in plist:
                pin_net[p] = net
        for p in nc:
            pin_net[p] = f"__NC_{p}"
        for p, info in sh.pins.items():
            isl.add_point(pin_net[p], (info["x"], info["y"]))

        els = []
        counts = dict(wire=0, label=0, glabel=0, hlabel=0, nc=0)
        for net, plist in sorted(NETS[name].items()):
            for p in plist:
                info = sh.pins[p]
                x, y, d = info["x"], info["y"], info["dir"]
                ln = STUB
                ex, ey = x + d[0] * ln, y + d[1] * ln
                while ln > 0 and not isl.ok(net, (x, y), (ex, ey)):
                    ln -= 1.27
                    ex, ey = x + d[0] * ln, y + d[1] * ln
                if ln > 0:
                    els.append(emit_wire(x, y, ex, ey))
                    isl.add_seg(net, (x, y), (ex, ey))
                    counts["wire"] += 1
                else:
                    ex, ey = x, y
                rot = dir_rot(d)
                if net in GLOBAL_NETS:
                    els.append(emit_global_label(net, ex, ey, rot))
                    counts["glabel"] += 1
                elif net in hier:
                    els.append(emit_hier_label(net, ex, ey, rot))
                    counts["hlabel"] += 1
                else:
                    els.append(emit_local_label(net, ex, ey, rot))
                    counts["label"] += 1
        for p in sorted(nc):
            info = sh.pins[p]
            els.append(emit_no_connect(info["x"], info["y"]))
            counts["nc"] += 1

        # PWR_FLAG drivers for otherwise-undriven power rails
        counts["flag"] = 0
        for fnet, fx, fy in PWR_FLAGS.get(name, []):
            flag_n = sum(len(v) for k, v in PWR_FLAGS.items()
                         if SHEETS.index(k) < SHEETS.index(name))
            ref = f"#FLG0{flag_n + counts['flag'] + 1}"
            els.append(emit_pwr_flag(ref, fx, fy, SHEET_UUIDS[name]))
            els.append(emit_wire(fx, fy, fx, fy + STUB))
            els.append(emit_global_label(fnet, fx, fy + STUB, 270))
            counts["flag"] += 1

        out = sh.rebuild(els)
        if PWR_FLAGS.get(name) and '(symbol "power:PWR_FLAG"' not in out:
            out = out.replace("\t(lib_symbols\n", "\t(lib_symbols\n" + PWR_FLAG_LIB, 1)
        if not balanced(out):
            raise SystemExit(f"{name}: generated file unbalanced")
        with open(sh.path, "w") as f:
            f.write(out)
        report[name] = counts

    rebuild_top(hier)
    return report, hier


# ---------------------------------------------------------------------------
# top sheet: sheet pins + root-level stub/label joins
# ---------------------------------------------------------------------------

SHEET_GEOM = {}  # filled from file


def emit_sheet_pin(name, x, y, rot):
    just = "right" if rot == 180 else "left"
    return ("\t(pin \"%s\" bidirectional\n\t\t\t(at %s %s %d)\n"
            "\t\t\t(uuid \"%s\")\n\t\t\t(effects\n"
            "\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n"
            "\t\t\t\t(justify %s)\n\t\t\t)\n\t\t)"
            % (name, fmt(x), fmt(y), rot, uid(), just))


def rebuild_top(hier):
    path = os.path.join(HERE, f"{TOP}.kicad_sch")
    with open(path) as f:
        text = f.read()
    rs, re_ = root_span(text)
    kept = []
    sheets = []
    gen = list(scan_children(text, rs, re_ - 1))
    first_any = gen[0][1]
    for tag, s, e in gen:
        if tag in ("wire", "label", "global_label", "hierarchical_label",
                   "junction", "no_connect"):
            continue
        if tag == "sheet":
            sheets.append((s, e))
            continue
        kept.append((s, e))

    new_els = []
    for s, e in sheets:
        chunk = text[s:e]
        crs, cre = root_span(chunk)
        keep_children = []
        for tag, cs, ce in scan_children(chunk, crs, cre - 1):
            if tag == "pin":
                continue
            keep_children.append((cs, ce))
        m = re.search(r'\(property\s+"Sheetname"\s+"((?:[^"\\]|\\.)*)"', chunk)
        sname = m.group(1)
        at = get_at(chunk)
        msz = re.search(r"\(size\s+([-\d.]+)\s+([-\d.]+)\)", chunk)
        sx, sy = at[0], at[1]
        w, h = float(msz.group(1)), float(msz.group(2))
        side = SHEET_PIN_SIDE[sname]
        nets = sorted(n for n, sset in hier.items() if sname in sset)
        # rebuild sheet chunk
        first_c = keep_children[0][0]
        parts = [chunk[:first_c]]
        for cs, ce in keep_children:
            parts.append(chunk[cs:ce])
            parts.append("\n\t")
        px = sx + w if side == "right" else sx
        rot = 0 if side == "right" else 180
        y0 = sy + 12.7
        for i, net in enumerate(nets):
            y = y0 + i * 6.35
            parts.append(emit_sheet_pin(net, px, y, rot))
            parts.append("\n\t")
            # root-level stub + local label
            d = 1 if side == "right" else -1
            ex = px + d * STUB
            new_els.append(emit_wire(px, y, ex, y))
            new_els.append(emit_local_label(net, ex, y, 0 if d > 0 else 180))
        sheet_out = "".join(parts).rstrip() + "\n\t)"
        new_els.insert(0, sheet_out)  # sheets first, then wires/labels

    parts = [text[:first_any]]
    for s, e in kept:
        parts.append(text[s:e])
        parts.append("\n\t")
    for el in new_els:
        parts.append(el)
        parts.append("\n\t")
    out = "".join(parts).rstrip() + "\n)\n"
    if not balanced(out):
        raise SystemExit("top: generated file unbalanced")
    with open(path, "w") as f:
        f.write(out)


if __name__ == "__main__":
    report, hier = generate()
    print("cross-sheet (hierarchical) nets:")
    for n, s in sorted(hier.items()):
        print(f"  {n:16s} {sorted(s)}")
    print("\nper-sheet element counts:")
    for name, c in report.items():
        print(f"  {name:11s} wires={c['wire']:3d} global={c['glabel']:3d} "
              f"hier={c['hlabel']:3d} local={c['label']:3d} nc={c['nc']:2d} "
              f"pwr_flags={c['flag']}")
