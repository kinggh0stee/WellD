#!/usr/bin/env python3
"""
generate_kicad.py
-----------------
Generates KiCad 10 project files for WellD well-level monitor.

Outputs (all in the same directory as this script):
  welld.kicad_pro  — project JSON
  welld.kicad_sch  — schematic (KiCad 10 s-expression)
  welld.kicad_pcb  — PCB layout (KiCad 10 s-expression)

Run:
  python3 generate_kicad.py
"""

import json
import os
import re
import subprocess
import uuid

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

HERE = os.path.dirname(os.path.abspath(__file__))


def find_kicad_sym_dir() -> str | None:
    """Locate KiCad symbol libraries across platforms."""
    candidates = [
        "/usr/share/kicad/symbols",
        "/usr/local/share/kicad/symbols",
        os.path.expanduser("~/.local/share/kicad/8.0/symbols"),
        os.path.expanduser("~/.local/share/kicad/7.0/symbols"),
        os.path.expanduser("~/.local/share/kicad/6.0/symbols"),
        "C:/Program Files/KiCad/8.0/share/kicad/symbols",
        "C:/Program Files/KiCad/7.0/share/kicad/symbols",
        "C:/Program Files/KiCad/6.0/share/kicad/symbols",
        "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols",
    ]
    for path in candidates:
        if os.path.isdir(path):
            return path
    return None


def uid() -> str:
    """Return a fresh UUID string."""
    return str(uuid.uuid4())


def write(filename: str, content: str) -> None:
    path = os.path.join(HERE, filename)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    print(f"  wrote {path}  ({content.count(chr(10))+1} lines)")


# ===========================================================================
# 1.  welld.kicad_pro
# ===========================================================================

def make_pro() -> str:
    data = {
        "board": {
            "3dviewports": [],
            "design_settings": {
                "defaults": {
                    "board_outline_line_width": 0.05,
                    "copper_line_width": 0.2,
                    "copper_text_italic": False,
                    "copper_text_size_h": 1.5,
                    "copper_text_size_v": 1.5,
                    "copper_text_thickness": 0.3,
                    "copper_text_upright": False,
                    "courtyard_line_width": 0.05,
                    "fab_line_width": 0.1,
                    "fab_text_italic": False,
                    "fab_text_size_h": 1.0,
                    "fab_text_size_v": 1.0,
                    "fab_text_thickness": 0.15,
                    "fab_text_upright": False,
                    "other_line_width": 0.1,
                    "other_text_italic": False,
                    "other_text_size_h": 1.0,
                    "other_text_size_v": 1.0,
                    "other_text_thickness": 0.15,
                    "other_text_upright": False,
                    "pads_allowed_layers": "*.Cu *.Mask F.SilkS",
                    "silk_line_width": 0.1,
                    "silk_text_italic": False,
                    "silk_text_size_h": 1.0,
                    "silk_text_size_v": 1.0,
                    "silk_text_thickness": 0.15,
                    "silk_text_upright": False,
                },
                "diff_pair_dimensions": [],
                "drc_exclusions": [],
                "meta": {"version": 2},
                "rule_severities": {},
                "rules": {
                    "max_error": 0.005,
                    "min_clearance": 0.2,
                    "min_copper_edge_clearance": 0.5,
                    "min_hole_clearance": 0.25,
                    "min_hole_to_hole": 0.25,
                    "min_microvia_diameter": 0.2,
                    "min_microvia_drill": 0.1,
                    "min_silk_clearance": 0.0,
                    "min_through_hole_diameter": 0.3,
                    "min_track_width": 0.2,
                    "min_via_annular_width": 0.1,
                    "min_via_diameter": 0.5,
                    "solder_mask_clearance": 0.0,
                    "solder_mask_min_width": 0.0,
                    "use_height_for_length_calcs": True,
                },
                "track_widths": [0.2, 0.4, 0.8, 1.5],
                "via_dimensions": [
                    {"diameter": 0.8, "drill": 0.4},
                    {"diameter": 1.0, "drill": 0.6},
                ],
                "zones_allow_external_fillets": False,
            },
            "ipc2581": {"dist": "", "distpn": "", "internal_id": "", "mfr": "", "mpn": ""},
            "layer_presets": [],
            "viewports": [],
        },
        "boards": [],
        "cvpcb": {"equivalence_files": []},
        "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},
        "meta": {"filename": "welld.kicad_pro", "version": 1},
        "net_settings": {
            "classes": [
                {
                    "bus_width": 12,
                    "clearance": 0.2,
                    "diff_pair_gap": 0.25,
                    "diff_pair_via_gap": 0.25,
                    "diff_pair_width": 0.2,
                    "line_style": 0,
                    "microvia_diameter": 0.3,
                    "microvia_drill": 0.1,
                    "name": "Default",
                    "pcb_color": "rgba(0, 0, 0, 0.000)",
                    "schematic_color": "rgba(0, 0, 0, 0.000)",
                    "track_width": 0.25,
                    "via_diameter": 0.8,
                    "via_drill": 0.4,
                    "wire_width": 6,
                }
            ],
            "meta": {"version": 3},
            "net_colors": {},
            "netclass_assignments": {},
            "netclass_patterns": [],
        },
        "pcbnew": {
            "last_paths": {
                "gencad": "",
                "idf": "",
                "netlist": "",
                "plot": "",
                "pos_files": "",
                "specctra_dsn": "",
                "step": "",
                "vrml": "",
            },
            "page_layout_descr_file": "",
        },
        "schematic": {
            "annotate_start_num": 0,
            "drawing": {
                "dashed_lines_dash_length_ratio": 12.0,
                "dashed_lines_gap_length_ratio": 3.0,
                "default_bus_thickness": 12.0,
                "default_junction_size": 40.0,
                "default_line_thickness": 6.0,
                "default_text_size": 50.0,
                "default_wire_thickness": 6.0,
                "field_names": [],
                "intersheets_ref_own_page": False,
                "intersheets_ref_prefix": "",
                "intersheets_ref_short": False,
                "intersheets_ref_show": False,
                "intersheets_ref_suffix": "",
                "junction_size_choice": 3,
                "label_size_ratio": 0.375,
                "pin_symbol_size": 25.0,
                "text_offset_ratio": 0.15,
            },
            "legacy_lib_dir": "",
            "legacy_lib_list": [],
            "meta": {"version": 1},
            "net_format_name": "",
            "ngspice_settings": None,
            "operating_point_sim": {"enabled": False, "format": "3.2f", "threshold": 1},
            "page_layout_descr_file": "",
            "plot_directory": "",
            "spice_adjust_passive_values": False,
            "spice_external_command": "spice %I",
            "subpart_first_id": 65,
            "subpart_id_separator": 0,
        },
        "sheets": [["", ""]],
        "text_variables": {},
    }
    return json.dumps(data, indent=2)


# ===========================================================================
# 2.  welld.kicad_sch
# ===========================================================================

# Component data: (ref, value, lib_id, x, y)
# Schematic coordinates are in mm on KiCad A2 sheet (594×420 mm).

# ── KiCad footprint per reference ────────────────────────────────────────────
FOOTPRINTS: dict = {
    "U1":    "Package_TO_SOT_SMD:SOT-23-6",
    "U6":    "welld:ESP32_C6_MINI_1U",
    "U7":    "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
    "U8":    "Package_TO_SOT_SMD:SOT-23-6",
    "U9":    "Package_SO:MSOP-10_3x3mm_P0.5mm",
    "U11":   "Package_TO_SOT_SMD:SOT-23-6",
    "U12":   "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
    "D1":    "Package_TO_SOT_SMD:SOT-363_SC-70-6",
    "D4":    "LED_SMD:LED_0603_1608Metric",
    "D5":    "Package_TO_SOT_SMD:SOT-23",
    "D6":    "Diode_SMD:D_SOD-123",
    "D7":    "LED_SMD:LED_0603_1608Metric",
    "D8":    "Diode_SMD:D_SMA",
    "D9":    "Diode_SMD:D_SMA",
    "D10":   "Diode_SMD:D_SMA",
    "D11":   "Diode_SMD:D_SMA",
    "D12":   "Package_TO_SOT_SMD:SOT-363_SC-70-6",
    "D13":   "Diode_SMD:D_SMA",
    "D14":   "Diode_SMD:D_SMA",
    "L1":    "Inductor_SMD:L_4x4mm",
    "L2":    "Inductor_SMD:L_2520_6332Metric",
    "FB1":   "Inductor_SMD:L_0402_1005Metric",
    "F2":    "Fuse:Fuse_1206_3216Metric",
    "Q2":    "Package_TO_SOT_SMD:SOT-23",
    "J1":    "Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical",
    "J3":    "Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical",
    "J4":    "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MC-1.5_3pin_3.5mm",
    "J5":    "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MC-1.5_3pin_3.5mm",
    "J6":    "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MC-1.5_3pin_3.5mm",
    "J7":    "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MC-1.5_3pin_3.5mm",
    "J8":    "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
    "J9":    "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical",
    "J10":   "Connector_PinHeader_1.27mm:PinHeader_1x06_P1.27mm_Vertical",
    "J12":   "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MC-1.5_2pin_3.5mm",
    "J13":   "welld:USB_C_GCT_USB4135-GF-A",
    "SW1":   "Button_Switch_SMD:SW_SPST_PTS636",
    "SW2":   "Button_Switch_SMD:SW_SPST_PTS636",
    "R2":    "Resistor_SMD:R_0805_2012Metric",
    "R4":    "Resistor_SMD:R_0805_2012Metric",
    **{f"TP{n}": "TestPoint:TestPoint_Pad_1.0x1.0mm"
       for n in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15]},
}

_C_0805 = {"C4","C6","C15","C17","C18","C19","C22","C27","C28","C29","C_BUCK"}
_C_1206 = {"C20"}


def get_footprint(ref: str) -> str:
    if ref in FOOTPRINTS:
        return FOOTPRINTS[ref]
    if ref.startswith("R") or ref == "R_CC1" or ref == "R_CC2":
        return "Resistor_SMD:R_0402_1005Metric"
    if ref.startswith("C") or ref.startswith("C_"):
        if ref in _C_1206:
            return "Capacitor_SMD:C_1206_3216Metric"
        if ref in _C_0805:
            return "Capacitor_SMD:C_0805_2012Metric"
        return "Capacitor_SMD:C_0402_1005Metric"
    if ref.startswith("SJ"):
        return "Jumper:SolderJumper_2_Open"
    return ""


# ── LCSC part numbers (from bom.csv) ─────────────────────────────────────────
LCSC_PARTS: dict = {
    "U1":    "C2862534",
    "U7":    "C2690716",
    "U8":    "C84005",
    "U9":    "C37593",
    "U11":   "C7519",
    "U12":   "C841540",
    "D1":    "C2687116",
    "D5":    "C31417",
    "D9":    "C2836497",
    "D10":   "C2836497",
    "D11":   "C8057",
    "D12":   "C2687116",
    "D13":   "C2836474",
    "FB1":   "C76537",
    "J1":    "C457925",
    "L1":    "C376098",
    "L2":    "C376098",
    "C_BST": "C14663",
}

COMPONENTS = [
    # ref,      value,               lib_id,                          x,     y
    # ── Block A: Solar input (top-left) ───────────────────────────────────────
    ("J12",  "MC 1.5/2-G-3.5",  "Connector:Conn_01x02_Pin",       30,    40),
    ("D14",  "SMAJ28CA",         "Device:D_TVS",                   70,    40),
    ("D6",   "MBRS140T3G",       "Device:D_Schottky",             110,    40),
    ("D8",   "SMAJ28CA",         "Device:D_TVS",                  150,    40),
    ("C17",  "10uF 25V",         "Device:C",                      190,    40),
    ("U7",   "CN3722",           "welld:CN3722",                  250,    40),
    ("C18",  "10uF 16V",         "Device:C",                      310,    40),
    ("R19",  "2k0 1%",           "Device:R",                       80,    80),
    ("R20",  "36k 1%",           "Device:R",                      120,    80),
    ("R21",  "10k 1%",           "Device:R",                      160,    80),
    ("R33",  "604k 1%",          "Device:R",                      250,    80),
    ("R34",  "100k 1%",          "Device:R",                      290,    80),
    ("R22",  "1k DNF",           "Device:R",                      330,    80),
    ("D7",   "Solar_LED_DNF",    "Device:LED",                     40,    80),

    # ── Block B: USB-C input (top, next to solar) ────────────────────────────
    ("J13",  "USB4135-GF-A",     "welld:USB_C_Power",             400,    40),
    ("R_CC1","5k1",              "Device:R",                      400,    80),
    ("R_CC2","5k1",              "Device:R",                      440,    80),
    ("U11",  "USBLC6-2SC6",      "welld:USBLC6_2SC6",             490,    40),
    ("F2",   "MF-MSMF110/16X",   "Device:Polyfuse",               540,    40),
    ("C27",  "4.7uF 10V",        "Device:C",                      490,    80),
    ("U12",  "TP5100",           "welld:TP5100",                  600,    40),
    ("C28",  "10uF 10V",         "Device:C",                      660,    40),
    ("C29",  "10uF 16V",         "Device:C",                      660,    80),
    ("R35",  "1k2 1%",           "Device:R",                      600,    80),
    ("R36",  "100k",             "Device:R",                      640,    80),
    ("R37",  "4k7",              "Device:R",                      720,    40),
    ("R38",  "4k7",              "Device:R",                      720,    80),

    # ── Block C: Battery + protection (left side, middle) ─────────────────────
    ("J1",   "B2B-PH-K-S",       "Connector:Conn_01x02_Pin",       30,   150),
    ("D13",  "SMAJ10CA",         "Device:D_TVS",                   80,   150),
    ("D5",   "AO3407",           "welld:AO3407",                  140,   150),
    ("R31",  "10k",              "Device:R",                      140,   190),

    # ── Block D: 3.3 V buck converter (middle-left) ───────────────────────────
    ("U1",   "AP63205WU",        "welld:AP63205WU",               250,   150),
    ("L2",   "4.7uH",            "Device:L",                      310,   150),
    ("C9",   "100nF 16V",        "Device:C",                      370,   150),
    ("C10",  "1uF 16V",          "Device:C",                      430,   150),
    ("C11",  "100nF",            "Device:C",                      370,   190),
    ("C12",  "1uF",              "Device:C",                      430,   190),
    ("C_BUCK","10uF 10V",        "Device:C",                      490,   150),
    ("R11",  "10k",              "Device:R",                      250,   190),

    # ── Block E: ESP32-C6 module (center) ─────────────────────────────────────
    ("U6",   "ESP32-C6-MINI-1U-H4","welld:ESP32_C6_MINI_1U",     560,   150),
    ("R12",  "10k",              "Device:R",                      680,   150),
    ("R13",  "10k",              "Device:R",                      680,   190),
    ("SW1",  "RESET",            "Switch:SW_Push",                520,   120),
    ("SW2",  "BOOT",             "Switch:SW_Push",                520,   210),
    ("C13",  "100nF",            "Device:C",                      560,   230),
    ("C14a", "100nF",            "Device:C",                      600,   230),
    ("C14b", "100nF",            "Device:C",                      640,   230),
    ("C14c", "100nF",            "Device:C",                      680,   230),
    ("C14d", "100nF",            "Device:C",                      720,   230),
    ("C15",  "10uF 10V",         "Device:C",                      750,   190),

    # ── Block F: Sensor interfaces (right side, middle) ───────────────────────
    ("J4",   "4-20mA_CH1",       "Connector:Conn_01x03_Pin",      820,   150),
    ("J5",   "4-20mA_CH2",       "Connector:Conn_01x03_Pin",      880,   150),
    ("J6",   "DS18B20",          "Connector:Conn_01x03_Pin",      940,   150),
    ("R32",  "33R DNF",          "Device:R",                      980,   150),
    ("J7",   "Spare",            "Connector:Conn_01x03_Pin",     1040,   150),
    ("D1",   "PRTR5V0U2X",       "welld:PRTR5V0U2X",              820,   190),
    ("D12",  "PRTR5V0U2X",       "welld:PRTR5V0U2X",              940,   190),
    ("R2",   "100R 0.1%",        "Device:R",                      850,   230),
    ("R3",   "100R",             "Device:R",                      890,   230),
    ("D9",   "SMAJ3.3CA",        "Device:D_TVS",                  820,   110),
    ("D10",  "SMAJ3.3CA",        "Device:D_TVS",                  880,   110),
    ("C3",   "1uF",              "Device:C",                      850,   270),
    ("C4",   "10uF 10V",         "Device:C",                      890,   270),
    ("C_SH1","10nF",             "Device:C",                      850,   310),
    ("R4",   "100R 0.1%",        "Device:R",                      970,   230),
    ("R5",   "100R",             "Device:R",                     1010,   230),
    ("C5",   "1uF",              "Device:C",                      970,   270),
    ("C6",   "10uF 10V",         "Device:C",                     1010,   270),
    ("C_SH2","10nF",             "Device:C",                      970,   310),
    ("R6",   "4k7",              "Device:R",                      940,   270),
    ("C7",   "100nF",            "Device:C",                     1040,   270),

    # ── Block G: Expansion headers (right of ESP32) ──────────────────────────
    ("J8",   "I2C_4pin",         "Connector:Conn_01x04_Pin",      760,   150),
    ("J9",   "GPIO_8pin",        "Connector:Conn_01x08_Pin",      760,   200),
    ("J10",  "PROG_6pin",        "Connector:Conn_01x06_Pin",      760,   260),
    ("J3",   "U.FL",             "welld:U_FL_Antenna",            760,   310),
    ("R9",   "4k7",              "Device:R",                      800,   150),
    ("R10",  "4k7",              "Device:R",                      800,   200),

    # ── Block H: Status LED (below buck) ──────────────────────────────────────
    ("D4",   "Status_LED",       "Device:LED",                    250,   280),
    ("R14",  "1k",               "Device:R",                      290,   280),

    # ── Block I: VLOOP 12 V boost (bottom-left) ───────────────────────────────
    ("U8",   "MT3608B",          "welld:MT3608B",                  40,   350),
    ("L1",   "4.7uH",            "Device:L",                      100,   350),
    ("C_BST","100nF 16V",        "Device:C",                       70,   390),
    ("C22",  "10uF 16V",         "Device:C",                      130,   390),
    ("R23",  "1.91M 1%",         "Device:R",                      160,   350),
    ("R24",  "100k 1%",          "Device:R",                      220,   350),
    ("C19",  "10uF 16V",         "Device:C",                      280,   350),
    ("C20",  "22uF 16V",         "Device:C",                      340,   350),
    ("D11",  "SMAJ13A",          "Device:D_TVS",                  400,   350),
    ("C21",  "100nF",            "Device:C",                      400,   390),

    # ── Block J: Precision ADC (bottom, left of center) ───────────────────────
    ("FB1",  "BLM18KG601SN1D",   "Device:L",                       40,   450),
    ("C23",  "100nF",            "Device:C",                       90,   450),
    ("C24",  "1uF",              "Device:C",                      140,   450),
    ("U9",   "ADS1115IDGST",     "welld:ADS1115",                 200,   450),

    # ── Block K: Battery-voltage divider gate (bottom, center) ────────────────
    ("Q2",   "BSS123",           "Device:Q_NMOS",                 320,   450),
    ("R7",   "330k 1%",          "Device:R",                      380,   450),
    ("R8",   "100k 1%",          "Device:R",                      440,   450),
    ("C8",   "100nF",            "Device:C",                      500,   450),
    ("R26",  "4k7",              "Device:R",                      560,   450),
    ("R28",  "100R",             "Device:R",                       90,   500),

    # ── Block M: Solder jumpers (bottom, right of center) ─────────────────────
    ("SJ1",  "VBOOST_EN DNF",    "Jumper:SolderJumper_2_Open",    620,   450),
    ("SJ2",  "VLOOP_BUS",        "Jumper:SolderJumper_2_Open",    680,   450),
    ("SJ3",  "LED_DIS",          "Jumper:SolderJumper_2_Open",    740,   450),
    ("SJ4",  "UART_TX DNF",      "Jumper:SolderJumper_2_Open",    800,   450),
    ("SJ5",  "UART_RX DNF",      "Jumper:SolderJumper_2_Open",    860,   450),

    # ── Block N: Test points (bottom row) ─────────────────────────────────────
    ("TP1",  "VBAT",             "welld:TestPoint_Pad",           100,   550),
    ("TP2",  "VLOOP",            "welld:TestPoint_Pad",           160,   550),
    ("TP3",  "+3V3",             "welld:TestPoint_Pad",           220,   550),
    ("TP4",  "GND",              "welld:TestPoint_Pad",           280,   550),
    ("TP5",  "LOOP_TERM_CH1",    "welld:TestPoint_Pad",           340,   550),
    ("TP6",  "LOOP_TERM_CH2",    "welld:TestPoint_Pad",           400,   550),
    ("TP7",  "1WIRE",            "welld:TestPoint_Pad",           460,   550),
    ("TP8",  "I2C_SDA",          "welld:TestPoint_Pad",           520,   550),
    ("TP9",  "I2C_SCL",          "welld:TestPoint_Pad",           580,   550),
    ("TP10", "VSOLAR_IN",        "welld:TestPoint_Pad",           640,   550),
    ("TP11", "VBAT_RAW",         "welld:TestPoint_Pad",           700,   550),
    ("TP12", "ADS_DRDY",         "welld:TestPoint_Pad",           760,   550),
    ("TP14", "/CHRG_SOLAR",      "welld:TestPoint_Pad",           820,   550),
    ("TP15", "/CHRG_USB",        "welld:TestPoint_Pad",           880,   550),
]


def _p10(name: str, val: str, ax: float, ay: float, hidden: bool = False,
         size: float = 0.8, bold: bool = False) -> str:
    """KiCad 10 property s-expression."""
    h = '\n      (hide yes)' if hidden else ''
    bold_attr = ' (bold yes)' if bold else ''
    return (
        f'    (property "{name}" "{val}"\n'
        f'      (at {ax:.2f} {ay:.2f} 0){h}\n'
        f'      (show_name no)\n'
        f'      (do_not_autoplace no)\n'
        f'      (effects (font (size {size} {size}){bold_attr}))\n'
        f'    )'
    )


def sch_global_label(net: str, x: float, y: float, shape: str = "passive") -> str:
    return f"""
  (global_label "{net}"
    (shape {shape})
    (at {x:.2f} {y:.2f} 0)
    (fields_autoplaced yes)
    (effects (font (size 0.8 0.8)) (justify left))
    (uuid "{uid()}")
    (property "Intersheetrefs" "${{INTERSHEET_REFS}}"
      (at {x:.2f} {y:.2f} 0)
      (hide yes)
      (show_name no)
      (do_not_autoplace no)
      (effects (font (size 0.8 0.8)))
    )
    (property "Intersheets" ""
      (at 0 0 0)
      (hide yes)
      (show_name no)
      (do_not_autoplace no)
      (effects (font (size 0.8 0.8)))
    )
  )"""


def sch_power_symbol(net: str, x: float, y: float, root_uuid: str = "") -> str:
    inst = (
        f'\n    (instances\n'
        f'      (project "welld"\n'
        f'        (path "/{root_uuid}"\n'
        f'          (reference "#PWR")\n'
        f'          (unit 1)\n'
        f'        )\n'
        f'      )\n'
        f'    )'
    ) if root_uuid else ""
    return f"""
  (symbol
    (lib_id "power:{net}")
    (at {x:.2f} {y:.2f} 0)
    (unit 1)
    (body_style 1)
    (exclude_from_sim no)
    (in_bom no)
    (on_board no)
    (in_pos_files yes)
    (dnp no)
    (fields_autoplaced yes)
    (uuid "{uid()}")
{_p10("Reference", "#PWR", 0, 0, hidden=True)}
{_p10("Value", net, 0, -3.81)}
{_p10("Footprint", "", 0, 0, hidden=True)}
{_p10("Datasheet", "", 0, 0, hidden=True)}
{_p10("Description", "", x, y)}
    (pin "1" (uuid "{uid()}"))
{inst}
  )"""


def sch_component(ref: str, value: str, lib_id: str, x: float, y: float,
                  root_uuid: str = "") -> str:
    footprint = get_footprint(ref)
    lcsc = LCSC_PARTS.get(ref, "")
    lcsc_prop = (
        f'\n{_p10("LCSC", lcsc, 0, 0, hidden=True)}'
        if lcsc else ""
    )
    inst = (
        f'\n    (instances\n'
        f'      (project "welld"\n'
        f'        (path "/{root_uuid}"\n'
        f'          (reference "{ref}")\n'
        f'          (unit 1)\n'
        f'        )\n'
        f'      )\n'
        f'    )'
    ) if root_uuid else ""
    return f"""
  (symbol
    (lib_id "{lib_id}")
    (at {x:.2f} {y:.2f} 0)
    (unit 1)
    (body_style 1)
    (exclude_from_sim no)
    (in_bom yes)
    (on_board yes)
    (in_pos_files yes)
    (dnp no)
    (fields_autoplaced yes)
    (uuid "{uid()}")
{_p10("Reference", ref, x, y - 2.0, bold=True)}
{_p10("Value", value, x, y + 2.0)}
{_p10("Footprint", footprint, 0, 0, hidden=True)}
{_p10("Datasheet", "", 0, 0, hidden=True)}
{_p10("Description", "", 0, 0, hidden=True)}{lcsc_prop}
{inst}
  )"""


KICAD_SYM_DIR = find_kicad_sym_dir() or "/usr/share/kicad/symbols"

def _extract_sym(lib: str, name: str) -> str:
    """Extract a single top-level symbol block from a .kicad_sym library file.

    Returns the raw s-expression text (unindented) suitable for embedding
    directly inside a (lib_symbols ...) block, or '' if not found.
    """
    path = os.path.join(KICAD_SYM_DIR, f"{lib}.kicad_sym")
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return ""

    # Match the opening of a top-level symbol with exactly this name.
    # Accept tabs or spaces for indentation.
    pattern = re.compile(r'(?m)^[ \t]*\(symbol "' + re.escape(name) + r'"\b')
    m = pattern.search(text)
    if not m:
        return ""

    # Find the position of the opening paren
    match_text = m.group()
    paren_offset = match_text.find('(symbol')
    start = m.start() + paren_offset

    # Walk from the opening paren, counting depth to find the matching close.
    depth = 0
    i = start
    while i < len(text):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                block = text[start:i + 1]
                # Re-indent: replace leading tabs with 4 spaces per level.
                lines = []
                first_line = True
                for line in block.splitlines():
                    n = len(line) - len(line.lstrip('\t'))
                    indented = '    ' + '  ' * n + line.lstrip('\t')
                    if first_line:
                        # Add library prefix so lib_id "Device:R" resolves
                        indented = indented.replace(
                            f'(symbol "{name}"',
                            f'(symbol "{lib}:{name}"',
                            1
                        )
                        first_line = False
                    lines.append(indented)
                return '\n'.join(lines)
        i += 1
    return ""


def _fallback_symbol(lib: str, name: str) -> str:
    """Generate a minimal fallback symbol when KiCad libraries are not installed."""
    full = f"{lib}:{name}"
    
    def _prop(key: str, val: str, ax: float, ay: float, hidden: bool = False) -> str:
        h = " (hide yes)" if hidden else ""
        return (f'      (property "{key}" "{val}" (at {ax:.2f} {ay:.2f} 0)'
                f' (show_name no) (do_not_autoplace no){h}'
                f' (effects (font (size 0.8 0.8))))')
    
    def _pin(ptype: str, x: float, y: float, angle: int, pname: str, num: str) -> str:
        return (
            f'      (pin {ptype} line (at {x:.2f} {y:.2f} {angle}) (length 1.27)\n'
            f'        (name "{pname}" (effects (font (size 0.8 0.8))))\n'
            f'        (number "{num}" (effects (font (size 0.8 0.8))))\n'
            f'      )'
        )
    
    # Power symbols
    if lib == "power":
        if name == "+3V3":
            return f"""
    (symbol "{full}"
      (power global)
      (pin_numbers (hide yes))
      (pin_names (offset 0) (hide yes))
      (exclude_from_sim no)
      (in_bom no)
      (on_board no)
      (in_pos_files yes)
      (duplicate_pin_numbers_are_jumpers no)
{_prop("Reference", "#PWR", 0, -3.81, True)}
{_prop("Value", "+3V3", 0, 3.81)}
{_prop("Footprint", "", 0, 0, True)}
{_prop("Datasheet", "", 0, 0, True)}
{_prop("Description", "", 0, 0, True)}
      (symbol "+3V3_0_1"
        (polyline (pts (xy -0.762 1.27) (xy 0 2.54)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0 2.54) (xy 0.762 1.27)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0 0) (xy 0 2.54)) (stroke (width 0) (type default)) (fill (type none)))
      )
      (symbol "+3V3_1_1"
        (pin power_in line (at 0 0 90) (length 0)
          (name "" (effects (font (size 0.8 0.8))))
          (number "1" (effects (font (size 0.8 0.8))))
        )
      )
      (embedded_fonts no)
    )"""
        elif name == "GND":
            return f"""
    (symbol "{full}"
      (power global)
      (pin_numbers (hide yes))
      (pin_names (offset 0) (hide yes))
      (exclude_from_sim no)
      (in_bom no)
      (on_board no)
      (in_pos_files yes)
      (duplicate_pin_numbers_are_jumpers no)
{_prop("Reference", "#PWR", 0, -3.81, True)}
{_prop("Value", "GND", 0, 3.81)}
{_prop("Footprint", "", 0, 0, True)}
{_prop("Datasheet", "", 0, 0, True)}
{_prop("Description", "", 0, 0, True)}
      (symbol "GND_0_1"
        (polyline (pts (xy 0 0) (xy 0 -1.27)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy -1.27 -1.27) (xy 1.27 -1.27)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy -0.762 -1.778) (xy 0.762 -1.778)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy -0.254 -2.286) (xy 0.254 -2.286)) (stroke (width 0) (type default)) (fill (type none)))
      )
      (symbol "GND_1_1"
        (pin power_in line (at 0 0 270) (length 0)
          (name "" (effects (font (size 0.8 0.8))))
          (number "1" (effects (font (size 0.8 0.8))))
        )
      )
      (embedded_fonts no)
    )"""
    
    # Two-pin passives (R, C, L, LED, D_Schottky, D_TVS, Polyfuse)
    if name in ("R", "C", "L", "LED", "D_Schottky", "D_TVS", "Polyfuse"):
        ref = "R" if name == "R" else "C" if name == "C" else "L" if name == "L" else "D" if name in ("LED", "D_Schottky", "D_TVS") else "F"
        return f"""
    (symbol "{full}"
      (pin_names (offset 1.016))
      (exclude_from_sim no)
      (in_bom yes)
      (on_board yes)
      (in_pos_files yes)
      (duplicate_pin_numbers_are_jumpers no)
{_prop("Reference", ref, 0, 5.08)}
{_prop("Value", name, 0, -5.08)}
{_prop("Footprint", "", 0, 0, True)}
{_prop("Datasheet", "", 0, 0, True)}
{_prop("Description", "", 0, 0, True)}
      (symbol "{name}_0_1"
        (rectangle (start -3.81 -3.81) (end 3.81 3.81)
          (stroke (width 0) (type default)) (fill (type background)))
      )
      (symbol "{name}_1_1"
{_pin("passive", -5.08, 0, 0, "1", "1")}
{_pin("passive", 5.08, 0, 180, "2", "2")}
      )
      (embedded_fonts no)
    )"""
    
    # NMOS transistor
    if name == "Q_NMOS":
        return f"""
    (symbol "{full}"
      (pin_names (offset 1.016))
      (exclude_from_sim no)
      (in_bom yes)
      (on_board yes)
      (in_pos_files yes)
      (duplicate_pin_numbers_are_jumpers no)
{_prop("Reference", "Q", 0, 5.08)}
{_prop("Value", "Q_NMOS", 0, -5.08)}
{_prop("Footprint", "", 0, 0, True)}
{_prop("Datasheet", "", 0, 0, True)}
{_prop("Description", "", 0, 0, True)}
      (symbol "Q_NMOS_0_1"
        (circle (center 0 0) (radius 2.54)
          (stroke (width 0) (type default)) (fill (type none)))
      )
      (symbol "Q_NMOS_1_1"
{_pin("passive", -5.08, 2.54, 0, "D", "2")}
{_pin("passive", -5.08, -2.54, 0, "S", "3")}
{_pin("input", -5.08, 0, 0, "G", "1")}
      )
      (embedded_fonts no)
    )"""
    
    # Push switch
    if name == "SW_Push":
        return f"""
    (symbol "{full}"
      (pin_names (offset 1.016))
      (exclude_from_sim no)
      (in_bom yes)
      (on_board yes)
      (in_pos_files yes)
      (duplicate_pin_numbers_are_jumpers no)
{_prop("Reference", "SW", 0, 5.08)}
{_prop("Value", "SW_Push", 0, -5.08)}
{_prop("Footprint", "", 0, 0, True)}
{_prop("Datasheet", "", 0, 0, True)}
{_prop("Description", "", 0, 0, True)}
      (symbol "SW_Push_0_1"
        (circle (center -2.54 0) (radius 0.508)
          (stroke (width 0) (type default)) (fill (type none)))
        (circle (center 2.54 0) (radius 0.508)
          (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy -2.54 -2.54) (xy 2.54 -2.54)) (stroke (width 0) (type default)) (fill (type none)))
      )
      (symbol "SW_Push_1_1"
{_pin("passive", -5.08, 0, 0, "1", "1")}
{_pin("passive", 5.08, 0, 180, "2", "2")}
      )
      (embedded_fonts no)
    )"""
    
    # Connectors
    if name.startswith("Conn_01x"):
        # Parse "Conn_01x02_Pin" -> 2 pins
        dims = name.split("_")[1]  # "01x02"
        pins = int(dims.split("x")[1])  # "02" -> 2
        height = max(pins * 2.54, 5.08)
        pin_strs = []
        for i in range(pins):
            y = (pins - 1) * 1.27 - i * 2.54
            pin_strs.append(_pin("passive", 5.08, y, 180, str(i+1), str(i+1)))
        return f"""
    (symbol "{full}"
      (pin_names (offset 1.016))
      (exclude_from_sim no)
      (in_bom yes)
      (on_board yes)
      (in_pos_files yes)
      (duplicate_pin_numbers_are_jumpers no)
{_prop("Reference", "J", 0, height/2 + 2.54)}
{_prop("Value", name, 0, -height/2 - 2.54)}
{_prop("Footprint", "", 0, 0, True)}
{_prop("Datasheet", "", 0, 0, True)}
{_prop("Description", "", 0, 0, True)}
      (symbol "{name}_0_1"
        (rectangle (start -2.54 {-height/2}) (end 2.54 {height/2})
          (stroke (width 0) (type default)) (fill (type background)))
      )
      (symbol "{name}_1_1"
{"\n".join(pin_strs)}
      )
      (embedded_fonts no)
    )"""
    
    # Solder jumper
    if name == "SolderJumper_2_Open":
        return f"""
    (symbol "{full}"
      (pin_names (offset 1.016))
      (exclude_from_sim no)
      (in_bom yes)
      (on_board yes)
      (in_pos_files yes)
      (duplicate_pin_numbers_are_jumpers no)
{_prop("Reference", "JP", 0, 3.81)}
{_prop("Value", "SolderJumper_2_Open", 0, -3.81)}
{_prop("Footprint", "", 0, 0, True)}
{_prop("Datasheet", "", 0, 0, True)}
{_prop("Description", "", 0, 0, True)}
      (symbol "SolderJumper_2_Open_0_1"
        (rectangle (start -2.54 -1.27) (end 2.54 1.27)
          (stroke (width 0) (type default)) (fill (type background)))
      )
      (symbol "SolderJumper_2_Open_1_1"
{_pin("passive", -3.81, 0, 0, "1", "1")}
{_pin("passive", 3.81, 0, 180, "2", "2")}
      )
      (embedded_fonts no)
    )"""
    
    return ""


# Standard library symbols needed by the schematic.
# Format: {lib_name: [symbol_name, ...]}
_STDLIB_NEEDED: dict[str, list[str]] = {
    "Device":    ["R", "C", "L", "LED", "D_Schottky", "D_TVS",
                  "Polyfuse", "Q_NMOS"],
    "Switch":    ["SW_Push"],
    "Connector": ["Conn_01x02_Pin", "Conn_01x03_Pin", "Conn_01x04_Pin",
                  "Conn_01x06_Pin", "Conn_01x08_Pin"],
    "Jumper":    ["SolderJumper_2_Open"],
    "power":     ["+3V3", "GND"],
}


def make_sch_lib_symbols() -> str:
    """Define all custom IC symbols inline (KiCad 10 s-expression format)."""

    def pin(ptype: str, pdir: str, x: float, y: float, angle: int, name: str, num: str, length: float = 2.54) -> str:
        return (
            f'      (pin {ptype} line (at {x:.2f} {y:.2f} {angle}) (length {length:.2f})\n'
            f'        (name "{name}" (effects (font (size 0.8 0.8))))\n'
            f'        (number "{num}" (effects (font (size 0.8 0.8))))\n'
            f'      )'
        )

    def lp(name: str, val: str, ax: float, ay: float, hidden: bool = False) -> str:
        h = " (hide yes)" if hidden else ""
        return (f'      (property "{name}" "{val}" (at {ax:.2f} {ay:.2f} 0)'
                f' (show_name no) (do_not_autoplace no){h}'
                f' (effects (font (size 0.8 0.8))))')

    def hdr(sym_name: str, ref: str, ref_y: float, val: str, val_y: float, fp: str) -> str:
        full_name = f"welld:{sym_name}"
        return (
            f'\n    (symbol "{full_name}"\n'
            f'      (pin_names (offset 1.016))\n'
            f'      (exclude_from_sim no)\n'
            f'      (in_bom yes)\n'
            f'      (on_board yes)\n'
            f'      (in_pos_files yes)\n'
            f'      (duplicate_pin_numbers_are_jumpers no)\n'
            + lp("Reference", ref, 0, ref_y) + "\n"
            + lp("Value", val, 0, val_y) + "\n"
            + lp("Footprint", fp, 0, 0, hidden=True) + "\n"
            + lp("Datasheet", "", 0, 0, hidden=True) + "\n"
            + lp("Description", "", 0, 0, hidden=True)
        )

    # ---- AP63205WU 3.3V 2A synchronous buck (SOT-23-6) ----------------------
    ap63205wu = hdr("AP63205WU", "U", 7.62, "AP63205WU", -7.62,
                    "Package_TO_SOT_SMD:SOT-23-6") + f"""
      (symbol "AP63205WU_0_1"
        (rectangle (start -3.81 -6.35) (end 3.81 6.35)
          (stroke (width 0) (type default)) (fill (type background)))
      )
      (symbol "AP63205WU_1_1"
{pin("input",     "left",   6.35,  3.81, 180, "EN",  "1")}
{pin("power_in",  "left",   6.35,  1.27, 180, "GND", "2")}
{pin("input",     "left",   6.35, -1.27, 180, "FB",  "3")}
{pin("power_in",  "left",   6.35, -3.81, 180, "VIN", "4")}
{pin("power_out", "right", -6.35,  1.27,   0, "SW",  "5")}
{pin("passive",   "right", -6.35, -1.27,   0, "BST", "6")}
      )
      (embedded_fonts no)
    )"""

    # ---- MT3608B VLOOP 12V boost converter (SOT-23-6) -----------------------
    mt3608b = hdr("MT3608B", "U", 7.62, "MT3608B", -7.62,
                  "Package_TO_SOT_SMD:SOT-23-6") + f"""
      (symbol "MT3608B_0_1"
        (rectangle (start -3.81 -6.35) (end 3.81 6.35)
          (stroke (width 0) (type default)) (fill (type background)))
      )
      (symbol "MT3608B_1_1"
{pin("power_in",  "left",   6.35,  3.81, 180, "IN",  "1")}
{pin("power_in",  "left",   6.35,  1.27, 180, "GND", "2")}
{pin("input",     "left",   6.35, -1.27, 180, "FB",  "3")}
{pin("input",     "left",   6.35, -3.81, 180, "EN",  "4")}
{pin("power_out", "right", -6.35,  1.27,   0, "SW",  "5")}
{pin("passive",   "right", -6.35, -1.27,   0, "BST", "6")}
      )
      (embedded_fonts no)
    )"""

    # ---- CN3722 2S MPPT solar charger (SOP-8) --------------------------------
    cn3722 = hdr("CN3722", "U", 10.16, "CN3722", -10.16,
                 "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm") + f"""
      (symbol "CN3722_0_1"
        (rectangle (start -3.81 -8.89) (end 3.81 8.89)
          (stroke (width 0) (type default)) (fill (type background)))
      )
      (symbol "CN3722_1_1"
{pin("passive",       "left",   6.35,  6.35, 180, "VPROG", "1")}
{pin("power_in",      "left",   6.35,  3.81, 180, "GND",   "2")}
{pin("power_in",      "left",   6.35,  1.27, 180, "VIN",   "3")}
{pin("power_in",      "left",   6.35, -1.27, 180, "VIN2",  "4")}
{pin("passive",       "right", -6.35,  3.81,   0, "VBAT",  "5")}
{pin("passive",       "right", -6.35,  1.27,   0, "VBAT2", "6")}
{pin("open_collector","right", -6.35, -1.27,   0, "/CHRG", "7")}
{pin("input",         "right", -6.35, -3.81,   0, "MPPT",  "8")}
      )
      (embedded_fonts no)
    )"""

    # ---- TP5100 2S USB-C boost charger (SOP-8) --------------------------------
    tp5100 = hdr("TP5100", "U", 10.16, "TP5100", -10.16,
                 "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm") + f"""
      (symbol "TP5100_0_1"
        (rectangle (start -3.81 -8.89) (end 3.81 8.89)
          (stroke (width 0) (type default)) (fill (type background)))
      )
      (symbol "TP5100_1_1"
{pin("passive",       "left",   6.35,  6.35, 180, "PROG",  "1")}
{pin("power_in",      "left",   6.35,  3.81, 180, "VCC",   "2")}
{pin("open_collector","left",   6.35,  1.27, 180, "/CHRG", "3")}
{pin("passive",       "left",   6.35, -1.27, 180, "BAT",   "4")}
{pin("passive",       "right", -6.35, -1.27,   0, "BAT2",  "5")}
{pin("input",         "right", -6.35,  1.27,   0, "CE",    "6")}
{pin("power_in",      "right", -6.35,  3.81,   0, "GND",   "7")}
{pin("power_in",      "right", -6.35,  6.35,   0, "GND2",  "8")}
      )
      (embedded_fonts no)
    )"""

    # ---- USBLC6-2SC6 USB ESD (SOT-23-6) ------------------------------------
    usblc6 = hdr("USBLC6_2SC6", "U", 7.62, "USBLC6-2SC6", -7.62,
                 "Package_TO_SOT_SMD:SOT-23-6") + f"""
      (symbol "USBLC6_2SC6_0_1"
        (rectangle (start -3.81 -6.35) (end 3.81 6.35)
          (stroke (width 0) (type default)) (fill (type background)))
      )
      (symbol "USBLC6_2SC6_1_1"
{pin("power_in", "left",   6.35,  3.81, 180, "VBUS",    "1")}
{pin("passive",  "left",   6.35,  1.27, 180, "IO1_NEG", "2")}
{pin("passive",  "left",   6.35, -1.27, 180, "IO2_POS", "3")}
{pin("power_in", "right", -6.35, -3.81,   0, "GND",     "4")}
{pin("passive",  "right", -6.35, -1.27,   0, "IO2_NEG", "5")}
{pin("passive",  "right", -6.35,  1.27,   0, "IO1_POS", "6")}
      )
      (embedded_fonts no)
    )"""

    # ---- PRTR5V0U2X dual TVS (SOT-363 / SC-70-6) ---------------------------
    prtr = hdr("PRTR5V0U2X", "D", 7.62, "PRTR5V0U2X", -7.62,
               "Package_TO_SOT_SMD:SOT-363_SC-70-6") + f"""
      (symbol "PRTR5V0U2X_0_1"
        (rectangle (start -3.81 -6.35) (end 3.81 6.35)
          (stroke (width 0) (type default)) (fill (type background)))
      )
      (symbol "PRTR5V0U2X_1_1"
{pin("power_in",      "left",   6.35,  3.81, 180, "GND",  "1")}
{pin("bidirectional", "left",   6.35,  1.27, 180, "IO1",  "2")}
{pin("power_in",      "right", -6.35,  3.81,   0, "VCC",  "3")}
{pin("bidirectional", "right", -6.35,  1.27,   0, "IO2",  "4")}
{pin("power_in",      "right", -6.35, -1.27,   0, "VCC2", "5")}
{pin("power_in",      "left",   6.35, -1.27, 180, "GND2", "6")}
      )
      (embedded_fonts no)
    )"""

    # ---- AO3407 P-channel MOSFET (SOT-23) -----------------------------------
    ao3407 = hdr("AO3407", "D", 5.08, "AO3407", -5.08,
                 "Package_TO_SOT_SMD:SOT-23") + f"""
      (symbol "AO3407_0_1"
        (rectangle (start -2.54 -3.81) (end 2.54 3.81)
          (stroke (width 0) (type default)) (fill (type background)))
      )
      (symbol "AO3407_1_1"
{pin("input",   "left",  5.08,  1.27, 180, "G", "1")}
{pin("passive", "left",  5.08, -1.27, 180, "S", "2")}
{pin("passive", "right",-5.08,  0,      0, "D", "3")}
      )
      (embedded_fonts no)
    )"""

    # ---- USB-C power connector (stub) --------------------------------------
    usbcpwr = hdr("USB_C_Power", "J", 7.62, "USB_C_Power", -7.62,
                  "welld:USB_C_9x3.2mm") + f"""
      (symbol "USB_C_Power_0_1"
        (rectangle (start -3.81 -5.08) (end 3.81 5.08)
          (stroke (width 0) (type default)) (fill (type background)))
      )
      (symbol "USB_C_Power_1_1"
{pin("power_out", "right", -6.35,  2.54,   0, "VBUS", "A4")}
{pin("passive",   "right", -6.35,  0,      0, "D-",   "A7")}
{pin("passive",   "right", -6.35, -2.54,   0, "D+",   "A6")}
{pin("passive",   "left",   6.35,  1.27, 180, "CC1",  "A5")}
{pin("passive",   "left",   6.35, -1.27, 180, "CC2",  "B5")}
{pin("power_in",  "left",   6.35, -3.81, 180, "GND",  "A1")}
      )
      (embedded_fonts no)
    )"""

    # ---- U.FL antenna stub -------------------------------------------------
    ufl = hdr("U_FL_Antenna", "J", 3.81, "U.FL", -3.81,
              "Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical") + f"""
      (symbol "U_FL_Antenna_0_1"
        (rectangle (start -2.54 -2.54) (end 2.54 2.54)
          (stroke (width 0) (type default)) (fill (type background)))
      )
      (symbol "U_FL_Antenna_1_1"
{pin("passive",  "right", -5.08, 1.27,   0, "RF",  "1")}
{pin("power_in", "left",   5.08, -1.27, 180, "GND", "2")}
      )
      (embedded_fonts no)
    )"""

    # ---- ESP32-C6-MINI-1U (large custom) ------------------------------------
    # Left side: power + strapping; Right side: GPIO
    esp_pins_left = [
        pin("power_in",  "left",  -12.7,  10.16, 180, "3V3",    "2"),
        pin("power_in",  "left",  -12.7,   7.62, 180, "3V3_b",  "3"),
        pin("power_in",  "left",  -12.7,  -7.62, 180, "GND",    "1"),
        pin("power_in",  "left",  -12.7,  -10.16,180, "GND_b",  "40"),
        pin("input",     "left",  -12.7,   5.08, 180, "EN",     "5"),
        pin("passive",   "left",  -12.7,   2.54, 180, "GPIO9",  "14"),
        pin("passive",   "left",  -12.7,   0,    180, "GPIO8",  "13"),
        pin("passive",   "left",  -12.7,  -2.54, 180, "GPIO18", "26"),
        pin("passive",   "left",  -12.7,  -5.08, 180, "GPIO19", "27"),
    ]
    esp_pins_right = [
        pin("passive", "right",  12.7,  10.16, 0, "GPIO0",  "15"),
        pin("passive", "right",  12.7,   7.62, 0, "GPIO1",  "16"),
        pin("passive", "right",  12.7,   5.08, 0, "GPIO2",  "17"),
        pin("passive", "right",  12.7,   2.54, 0, "GPIO3",  "18"),
        pin("passive", "right",  12.7,   0,    0, "GPIO4",  "19"),
        pin("passive", "right",  12.7,  -2.54, 0, "GPIO5",  "20"),
        pin("passive", "right",  12.7,  -5.08, 0, "GPIO6",  "21"),
        pin("passive", "right",  12.7,  -7.62, 0, "GPIO7",  "22"),
        pin("passive", "right",  12.7, -10.16, 0, "GPIO10", "23"),
        pin("passive", "right",  12.7, -12.7,  0, "GPIO11", "24"),
        pin("passive", "right",  12.7, -15.24, 0, "GPIO12", "25"),
        pin("passive", "right",  12.7, -17.78, 0, "GPIO13", "28"),
        pin("passive", "right",  12.7, -20.32, 0, "GPIO14", "29"),
        pin("passive", "right",  12.7, -22.86, 0, "GPIO15", "30"),
        pin("passive", "right",  12.7, -25.4,  0, "GPIO16", "31"),
        pin("passive", "right",  12.7, -27.94, 0, "GPIO17", "32"),
        pin("passive", "right",  12.7, -30.48, 0, "GPIO20", "33"),
        pin("passive", "right",  12.7, -33.02, 0, "GPIO21", "34"),
    ]
    esp_all_pins = "\n".join(esp_pins_left + esp_pins_right)

    esp32 = hdr("ESP32_C6_MINI_1U", "U", 35.56, "ESP32-C6-MINI-1U", -38.10,
                "welld:ESP32_C6_MINI_1U") + f"""
      (symbol "ESP32_C6_MINI_1U_0_1"
        (rectangle (start -10.16 -35.56) (end 10.16 12.7)
          (stroke (width 0) (type default)) (fill (type background)))
      )
      (symbol "ESP32_C6_MINI_1U_1_1"
{esp_all_pins}
      )
      (embedded_fonts no)
    )"""

    # ---- ADS1115 16-bit I2C ADC (MSOP-10 / VSSOP-10) ------------------------
    ads1115 = hdr("ADS1115", "U", 10.16, "ADS1115", -10.16,
                  "Package_SO:MSOP-10_3x3mm_P0.5mm") + f"""
      (symbol "ADS1115_0_1"
        (rectangle (start -5.08 -8.89) (end 5.08 8.89)
          (stroke (width 0) (type default)) (fill (type background)))
      )
      (symbol "ADS1115_1_1"
{pin("power_in",      "left",   7.62,  6.35, 180, "VDD",   "8")}
{pin("power_in",      "left",   7.62,  3.81, 180, "GND",   "3")}
{pin("input",         "left",   7.62,  1.27, 180, "SCL",   "10")}
{pin("bidirectional", "left",   7.62, -1.27, 180, "SDA",   "9")}
{pin("input",         "left",   7.62, -3.81, 180, "ADDR",  "1")}
{pin("output",        "right", -7.62,  6.35,   0, "ALERT", "2")}
{pin("input",         "right", -7.62,  3.81,   0, "AIN0",  "4")}
{pin("input",         "right", -7.62,  1.27,   0, "AIN1",  "5")}
{pin("input",         "right", -7.62, -1.27,   0, "AIN2",  "6")}
{pin("input",         "right", -7.62, -3.81,   0, "AIN3",  "7")}
      )
      (embedded_fonts no)
    )"""

    # ---- TestPoint_Pad (1.0 mm SMD pad, DNF) --------------------------------
    testpoint = hdr("TestPoint_Pad", "TP", 3.81, "TestPoint", -3.81,
                    "TestPoint:TestPoint_Pad_1.0x1.0mm") + f"""
      (symbol "TestPoint_Pad_0_1"
        (circle (center 0 0) (radius 0.5)
          (stroke (width 0) (type default)) (fill (type none)))
      )
      (symbol "TestPoint_Pad_1_1"
{pin("passive", "right", -2.54, 0, 0, "1", "1")}
      )
      (embedded_fonts no)
    )"""

    # ---- VBAT power rail (not in KiCad 10 standard power library) ----------
    vbat_pwr = f"""
    (symbol "power:VBAT"
      (power global)
      (pin_numbers (hide yes))
      (pin_names (offset 0) (hide yes))
      (exclude_from_sim no)
      (in_bom yes)
      (on_board yes)
      (in_pos_files yes)
      (duplicate_pin_numbers_are_jumpers no)
      (property "Reference" "#PWR" (at 0 -3.81 0) (show_name no) (do_not_autoplace no) (hide yes) (effects (font (size 0.8 0.8))))
      (property "Value" "VBAT" (at 0 3.556 0) (show_name no) (do_not_autoplace no) (effects (font (size 0.8 0.8))))
      (property "Footprint" "" (at 0 0 0) (show_name no) (do_not_autoplace no) (hide yes) (effects (font (size 0.8 0.8))))
      (property "Datasheet" "" (at 0 0 0) (show_name no) (do_not_autoplace no) (hide yes) (effects (font (size 0.8 0.8))))
      (property "Description" "" (at 0 0 0) (show_name no) (do_not_autoplace no) (hide yes) (effects (font (size 0.8 0.8))))
      (symbol "VBAT_0_1"
        (polyline (pts (xy -0.762 1.27) (xy 0 2.54)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0 2.54) (xy 0.762 1.27)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0 0) (xy 0 2.54)) (stroke (width 0) (type default)) (fill (type none)))
      )
      (symbol "VBAT_1_1"
        (pin power_in line (at 0 0 90) (length 0)
          (name "" (effects (font (size 0.8 0.8))))
          (number "1" (effects (font (size 0.8 0.8))))
        )
      )
      (embedded_fonts no)
    )"""

    custom = "\n".join([ap63205wu, mt3608b, cn3722, tp5100, usblc6, prtr, ao3407,
                        usbcpwr, ufl, esp32, ads1115, testpoint, vbat_pwr])

    if not os.path.isdir(KICAD_SYM_DIR):
        print(f"  WARNING: KiCad symbol libraries not found at {KICAD_SYM_DIR}")
        print(f"           Standard symbols (R, C, L, GND, etc.) will show as '??'.")
        print(f"           Install KiCad libraries via Preferences → Package and Content Manager.")

    stdlib_parts = []
    missing_libs = set()
    for lib, names in _STDLIB_NEEDED.items():
        for name in names:
            sym = _extract_sym(lib, name)
            if sym:
                stdlib_parts.append(sym)
            else:
                missing_libs.add(lib)
                fallback = _fallback_symbol(lib, name)
                if fallback:
                    stdlib_parts.append(fallback)
                else:
                    print(f"  WARNING: could not extract {lib}:{name} from {KICAD_SYM_DIR}")
    
    if missing_libs:
        print(f"  INFO: Used fallback inline symbols for: {', '.join(sorted(missing_libs))}")
        print(f"        (Install KiCad libraries for prettier symbols)")

    return custom + "\n" + "\n".join(stdlib_parts)


def make_sch() -> str:
    """Build the complete welld.kicad_sch s-expression string."""

    root_uuid = uid()
    lib_symbols = make_sch_lib_symbols()

    # Global labels for all key nets
    nets = [
        ("VSOLAR_IN",    30,   20, "passive"),
        ("VSOLAR",      100,   20, "passive"),
        ("VUSB_IN",     400,   20, "passive"),
        ("VUSB",        470,   20, "passive"),
        ("VBAT",         30,  140, "passive"),
        ("+3V3",        250,  140, "passive"),
        ("GND",          30,  520, "passive"),
        ("ADC_CH0",     820,  140, "input"),
        ("ADC_CH1",     880,  140, "input"),
        ("ADC_CH2",     940,  140, "input"),
        ("1WIRE",       980,  140, "input"),
        ("I2C_SDA",     760,  140, "passive"),
        ("I2C_SCL",     760,  200, "passive"),
        ("GPIO13_LED",  250,  270, "passive"),
        ("UART_TX",     760,  280, "passive"),
        ("UART_RX",     760,  300, "passive"),
        ("EN",          520,  110, "input"),
        ("BOOT",        520,  230, "input"),
        ("MPPT_REF",     50,   70, "passive"),
        ("/CHRG_USB",   400,  100, "passive"),
        ("/DONE_USB",   400,  110, "passive"),
        ("/CHRG_SOLAR",  30,   70, "passive"),
        ("/DONE_SOLAR",  30,   80, "passive"),
        ("VLOOP",        40,  340, "passive"),
        ("VBOOST_EN",    40,  420, "input"),
        ("CHRG_USB_DIS",400,  420, "input"),
        ("SOLAR_DET",   140,  420, "input"),
        ("BATT_DIV_EN", 320,  420, "input"),
        ("ADS_DRDY",    200,  420, "input"),
        ("MAX_ALRT",    320,  520, "input"),
        ("LOOP_TERM_CH1", 820,  270, "passive"),
        ("LOOP_TERM_CH2", 880,  270, "passive"),
        ("+3V3_ADS",     40,  480, "passive"),
        ("VBAT_RAW",     80,  140, "passive"),
    ]

    global_labels_str = ""
    for net, x, y, shape in nets:
        global_labels_str += sch_global_label(net, x, y, shape)

    # Power symbols (PWR_FLAG at rail entry points)
    power_flags = [
        ("+3V3",    250,  130),
        ("GND",      30,  510),
        ("VBAT",     80,  130),
        ("GND",     140,  180),   # GND return for D5 gate pull-down R31
    ]
    power_str = ""
    for net, x, y in power_flags:
        power_str += sch_power_symbol(net, x, y, root_uuid)

    # All component symbol instances
    comps_str = ""
    for ref, value, lib_id, x, y in COMPONENTS:
        comps_str += sch_component(ref, value, lib_id, x, y, root_uuid)

    # Wire list: key structural wires to visually connect blocks
    # Format: (wire (pts (xy x1 y1) (xy x2 y2)) ...)
    def wire(x1, y1, x2, y2):
        return f"""
  (wire (pts (xy {x1:.2f} {y1:.2f}) (xy {x2:.2f} {y2:.2f}))
    (stroke (width 0) (type default))
    (uuid "{uid()}")
  )"""

    wires = [
        # Solar path: J12 -> D6 -> VSOLAR label
        wire(30, 40, 70, 40),
        wire(90, 40, 100, 40),
        # USB path: J13 -> F2
        wire(400, 40, 470, 40),
        wire(510, 40, 540, 40),
        # TP5100 output -> VBAT
        wire(630, 40, 80, 40),
        # Buck input <- VBAT
        wire(210, 150, 250, 150),
        # Buck output -> +3V3
        wire(310, 150, 330, 150),
        # ESP32 VCC
        wire(550, 150, 560, 150),
        # Batt divider
        wire(680, 150, 700, 150),
        # MPPT divider
        wire(50, 40, 50, 70),
        # Battery protection chain
        wire(140, 150, 170, 150),
        wire(190, 150, 250, 150),
        # D5 (AO3407) gate -> R31 (10k) -> GND pull-down
        wire(140, 150, 140, 190),   # gate to R31
        wire(140, 190, 140, 510),   # R31 to GND
        # LED path
        wire(250, 280, 290, 280),
        # 1-Wire series protection R32 (DNF default): J6 pin 2 -> R32 -> 1WIRE net
        wire(940, 150, 980, 150),   # J6 to 1WIRE label
    ]

    wires_str = "".join(wires)

    # No-connect markers on un-used pins (representative set)
    def noconn(x, y):
        return f"""
  (no_connect (at {x:.2f} {y:.2f}) (uuid "{uid()}"))"""

    noconns_str = noconn(760, 310)  # J3 shield

    sch = f"""(kicad_sch
  (version 20260306)
  (generator "eeschema")
  (generator_version "10.0")
  (uuid "{root_uuid}")
  (paper "A2")
  (title_block
    (title "WellD Well-Level Monitor")
    (date "2026-05-18")
    (company "WellD Project")
    (comment 1 "ESP32-C6-MINI-1U + AP63205WU + MT3608B + CN3722 + TP5100 + ADS1115")
  )
  (lib_symbols
{lib_symbols}
  )

{global_labels_str}

{power_str}

{comps_str}

{wires_str}

{noconns_str}

)
"""
    return sch


# ===========================================================================
# 3.  welld.kicad_pcb
# ===========================================================================

# Board dimensions (mm)
BOARD_W = 80.0
BOARD_H = 55.0

# Mounting hole positions (mm from lower-left = PCB origin)
MOUNTING_HOLES = [
    (3.5,  3.5),
    (76.5, 3.5),
    (3.5,  51.5),
    (76.5, 51.5),
]

# PCB component placement: (ref, footprint, x, y, rotation, description)
# Footprints use standard KiCad 10 library paths.
PCB_COMPONENTS = [
    # ICs
    ("U1",   "Package_TO_SOT_SMD:SC-70-5",                               56,   34,   0, "TPS7A0533"),
    ("U2",   "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",                     10,   41,   0, "TP4056"),
    ("U3",   "Package_TO_SOT_SMD:SOT-23-6",                              68,   21,   0, "S-8261A"),
    ("U4",   "Package_TO_SOT_SMD:SOT-23-6",                              68,   14,   0, "FS8205A"),
    ("U5",   "Package_TO_SOT_SMD:SOT-23-6",                              10,   48,   0, "USBLC6"),
    ("U6",   "welld:ESP32_C6_MINI_1U",                                   31,   26,   0, "ESP32-C6"),
    ("U7",   "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",                     60,   10,   0, "CN3791"),

    # Diodes
    ("D1",   "Package_TO_SOT_SMD:SOT-363_SC-70-6",                      15,   14,   0, "PRTR5V0U2X"),
    ("D9",   "Diode_SMD:D_SMA",                                         12,    6,   0, "SMAJ3.3CA"),  # changed from SMAJ5.0CA
    ("D10",  "Diode_SMD:D_SMA",                                         23,    6,   0, "SMAJ3.3CA"),  # changed from SMAJ5.0CA
    ("D11",  "Diode_SMD:D_SMA",                                         78,    6,   0, "SMAJ13A"),
    ("D2",   "LED_SMD:LED_0603_1608Metric",                              12,   47,   0, "LED_CHRG"),
    ("D3",   "LED_SMD:LED_0603_1608Metric",                              14,   47,   0, "LED_STBY"),
    ("D4",   "LED_SMD:LED_0603_1608Metric",                              50,   51,   0, "LED_STATUS"),
    ("D5",   "Package_TO_SOT_SMD:SOT-23",                                65,   42,   0, "AO3407"),
    ("D6",   "Diode_SMD:D_SOD-123",                                      56,    7,   0, "MBRS140"),
    ("R31",  "Resistor_SMD:R_0402_1005Metric",                           65,   44,   0, "10k"),  # D5 gate pull-down

    # Fuse
    ("F1",   "Fuse:Fuse_1206_3216Metric",                                 6,   44,   0, "PTC_1A"),

    # Connectors
    ("J1",   "Connector_JST:JST_XH_B2B-XH-AM_1x02_P2.50mm_Horizontal", 74,   40,   0, "LiPo"),
    ("J2",   "welld:USB_C_9x3.2mm",                                       2,   47,   0, "USB-C"),
    ("J3",   "Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical",     40,   53,   0, "U.FL"),
    ("J4",   "Connector_Phoenix_MC:PhoenixContact_MC_1,5_3-G-3,5_1x03_P3.50mm_Horizontal", 12, 2, 0, "4-20mA_1"),
    ("J5",   "Connector_Phoenix_MC:PhoenixContact_MC_1,5_3-G-3,5_1x03_P3.50mm_Horizontal", 23, 2, 0, "4-20mA_2"),
    ("J6",   "Connector_Phoenix_MC:PhoenixContact_MC_1,5_3-G-3,5_1x03_P3.50mm_Horizontal", 34, 2, 0, "DS18B20"),
    ("R32",  "Resistor_SMD:R_0402_1005Metric",                           36,   4,  0, "33R_DNF"),  # 1-Wire series protection (DNF default)
    ("J7",   "Connector_Phoenix_MC:PhoenixContact_MC_1,5_3-G-3,5_1x03_P3.50mm_Horizontal", 45, 2, 0, "Spare"),
    ("J8",   "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical", 70, 46,  0, "I2C"),
    ("J9",   "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical", 70, 32,  0, "GPIO"),
    ("J10",  "Connector_PinHeader_1.27mm:PinHeader_1x06_P1.27mm_Vertical",  2, 20,  0, "PROG"),
    ("J12",  "Connector_Phoenix_MC:PhoenixContact_MC_1,5_2-G-3,5_1x02_P3.50mm_Horizontal", 64, 2, 0, "Solar"),

    # Switches
    ("SW1",  "Button_Switch_SMD:SW_SPST_TL3305AF160QG",                   5,   35,   0, "RESET"),
    ("SW2",  "Button_Switch_SMD:SW_SPST_TL3305AF160QG",                   5,   28,   0, "BOOT"),

    # Resistors
    ("R1",   "Resistor_SMD:R_0402_1005Metric",   8,   38,   0, "2k0"),
    ("R2",   "Resistor_SMD:R_0805_2012Metric",   17,   10,  0, "100R_0.1%"),
    ("R3",   "Resistor_SMD:R_0402_1005Metric",   20,   12,  0, "100R"),
    ("R4",   "Resistor_SMD:R_0805_2012Metric",   26,   10,  0, "100R_0.1%"),
    ("R5",   "Resistor_SMD:R_0402_1005Metric",   29,   12,  0, "100R"),
    ("R6",   "Resistor_SMD:R_0402_1005Metric",   36,   10,  0, "4k7"),
    ("R7",   "Resistor_SMD:R_0402_1005Metric",   53,   30,  0, "100k"),
    ("R8",   "Resistor_SMD:R_0402_1005Metric",   53,   32,  0, "100k"),
    ("R9",   "Resistor_SMD:R_0402_1005Metric",   63,   46,  0, "4k7"),
    ("R10",  "Resistor_SMD:R_0402_1005Metric",   65,   46,  0, "4k7"),
    ("R11",  "Resistor_SMD:R_0402_1005Metric",   26,   36,  0, "10k"),
    ("R12",  "Resistor_SMD:R_0402_1005Metric",   26,   34,  0, "10k"),
    ("R13",  "Resistor_SMD:R_0402_1005Metric",   26,   32,  0, "10k"),
    ("R14",  "Resistor_SMD:R_0402_1005Metric",   51,   49,  0, "1k"),
    ("R15",  "Resistor_SMD:R_0402_1005Metric",    4,   50,  0, "5k1"),
    ("R16",  "Resistor_SMD:R_0402_1005Metric",    6,   50,  0, "5k1"),
    ("R17",  "Resistor_SMD:R_0402_1005Metric",   11,   45,  0, "1k_DNF"),
    ("R18",  "Resistor_SMD:R_0402_1005Metric",   13,   45,  0, "1k_DNF"),
    ("R19",  "Resistor_SMD:R_0402_1005Metric",   57,   12,  0, "2k0"),
    ("R20",  "Resistor_SMD:R_0402_1005Metric",   63,    8,  0, "36k"),
    ("R21",  "Resistor_SMD:R_0402_1005Metric",   63,   10,  0, "10k"),
    ("R22",  "Resistor_SMD:R_0402_1005Metric",   62,   14,  0, "1k_DNF"),

    # Capacitors
    ("C1",   "Capacitor_SMD:C_0805_2012Metric",   8,   41,  0, "10uF"),
    ("C2",   "Capacitor_SMD:C_0805_2012Metric",  12,   41,  0, "10uF"),
    ("C3",    "Capacitor_SMD:C_0402_1005Metric",  20,   14,  0, "1uF"),
    ("C4",    "Capacitor_SMD:C_0805_2012Metric",  22,   14,  0, "10uF"),
    ("C_SH1", "Capacitor_SMD:C_0402_1005Metric",  17,   12,  0, "10nF"),  # across R2 shunt ch1
    ("C5",    "Capacitor_SMD:C_0402_1005Metric",  29,   14,  0, "1uF"),
    ("C6",    "Capacitor_SMD:C_0805_2012Metric",  31,   14,  0, "10uF"),
    ("C_SH2", "Capacitor_SMD:C_0402_1005Metric",  26,   12,  0, "10nF"),  # across R4 shunt ch2
    ("C7",   "Capacitor_SMD:C_0402_1005Metric",  36,   12,  0, "100nF"),
    ("C8",   "Capacitor_SMD:C_0402_1005Metric",  55,   32,  0, "100nF"),
    ("C9",   "Capacitor_SMD:C_0402_1005Metric",  54,   35,  0, "100nF"),
    ("C10",  "Capacitor_SMD:C_0402_1005Metric",  56,   35,  0, "1uF"),
    ("C11",  "Capacitor_SMD:C_0402_1005Metric",  54,   37,  0, "100nF"),
    ("C12",  "Capacitor_SMD:C_0402_1005Metric",  56,   37,  0, "1uF"),
    ("C13",  "Capacitor_SMD:C_0402_1005Metric",  27,   37,  0, "100nF"),
    ("C14a", "Capacitor_SMD:C_0402_1005Metric",  42,   26,  0, "100nF"),
    ("C14b", "Capacitor_SMD:C_0402_1005Metric",  44,   24,  0, "100nF"),
    ("C14c", "Capacitor_SMD:C_0402_1005Metric",  46,   26,  0, "100nF"),
    ("C14d", "Capacitor_SMD:C_0402_1005Metric",  48,   24,  0, "100nF"),
    ("C15",  "Capacitor_SMD:C_0805_2012Metric",  44,   26,  0, "10uF"),
    ("C16",  "Capacitor_SMD:C_0805_2012Metric",   6,   46,  0, "4.7uF"),
    ("C17",  "Capacitor_SMD:C_0805_2012Metric",  58,    8,  0, "10uF"),
    ("C18",  "Capacitor_SMD:C_0805_2012Metric",  60,   12,  0, "10uF"),

    # VLOOP 12 V boost
    ("U8",   "Package_TO_SOT_SMD:SOT-23-5",      73,   20,  0, "TPS61023"),
    ("L1",   "Inductor_SMD:L_1812_4532Metric",   74,   12,  0, "4.7uH"),
    ("R23",  "Resistor_SMD:R_0402_1005Metric",   76,   18,  0, "1.1M"),
    ("R24",  "Resistor_SMD:R_0402_1005Metric",   76,   20,  0, "47k"),
    ("C19",  "Capacitor_SMD:C_0805_2012Metric",  70,   16,  0, "10uF"),
    ("C20",  "Capacitor_SMD:C_1206_3216Metric",  77,    8,  0, "22uF"),
    ("C22",  "Capacitor_SMD:C_0805_2012Metric",  72,    8,  0, "10uF"),

    # Precision ADC + fuel gauge
    ("FB1",  "Ferrite_Bead_SMD:L_0402_1005Metric", 38, 36,  0, "600R@100MHz"),
    ("C23",  "Capacitor_SMD:C_0402_1005Metric",  40,   36,  0, "100nF"),
    ("C24",  "Capacitor_SMD:C_0402_1005Metric",  42,   36,  0, "1uF"),
    ("U9",   "Package_SO:MSOP-10_3x3mm_P0.5mm",  42,   38,  0, "ADS1115"),
    ("U10",  "Package_TO_SOT_SMD:SOT-23-6",      68,   42,  0, "MAX17048"),
    ("R27",  "Resistor_SMD:R_0402_1005Metric",   62,   44,  0, "4k7"),
    ("R28",  "Resistor_SMD:R_0402_1005Metric",   50,   38,  0, "100R"),

    # Charger interlock + divider gate
    ("Q1",   "Package_TO_SOT_SMD:SOT-23",        14,   43,  0, "BSS123"),
    ("Q2",   "Package_TO_SOT_SMD:SOT-23",        56,   36,  0, "BSS123"),
    ("Q3",   "Package_TO_SOT_SMD:SOT-23",        16,   41,  0, "BSS84"),
    ("R25",  "Resistor_SMD:R_0402_1005Metric",   16,   47,  0, "4k7"),
    ("R26",  "Resistor_SMD:R_0402_1005Metric",   57,   38,  0, "4k7"),
    ("R29",  "Resistor_SMD:R_0402_1005Metric",   10,   38,  0, "4k7"),
    ("R30",  "Resistor_SMD:R_0402_1005Metric",   18,   45,  0, "10k"),

    # Solar TVS + indicator
    ("D7",   "LED_SMD:LED_0603_1608Metric",      52,    8,  0, "LED_SOLAR"),
    ("D8",   "Diode_SMD:D_SMA",                  62,   20,  0, "SMAJ7.0A"),
    ("C21",  "Capacitor_SMD:C_0402_1005Metric",  26,    8,  0, "100nF"),

    # Solder jumpers
    ("SJ1",  "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm",   70, 24, 0, "VBOOST_EN"),
    ("SJ2",  "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm",   18,  6, 0, "VLOOP_BUS"),
    ("SJ3",  "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm",   53, 49, 0, "LED_DIS"),
    ("SJ4",  "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm",    8, 16, 0, "UART_TX"),
    ("SJ5",  "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm",    8, 24, 0, "UART_RX"),

    # Missing bypass caps (decoupling review additions)
    ("C25",  "Capacitor_SMD:C_0402_1005Metric",  69, 42,  0, "100nF"),   # MAX17048 VDD bypass, within 1mm of U10
    ("C26",  "Capacitor_SMD:C_0402_1005Metric",  68, 19,  0, "100nF"),   # S-8261A VCC bypass, within 1mm of U3

    # Test points TP1-TP14 (DNF — 1.0mm SMD pads)
    # Power rails row: top edge of board
    ("TP1",  "TestPoint:TestPoint_Pad_1.0x1.0mm",  56, 50,  0, "VBAT"),
    ("TP2",  "TestPoint:TestPoint_Pad_1.0x1.0mm",  79, 18,  0, "VLOOP"),
    ("TP3",  "TestPoint:TestPoint_Pad_1.0x1.0mm",  58, 50,  0, "+3V3"),
    ("TP4",  "TestPoint:TestPoint_Pad_1.0x1.0mm",  60, 50,  0, "GND"),
    # Sensor signal taps
    ("TP5",  "TestPoint:TestPoint_Pad_1.0x1.0mm",  19, 11,  0, "LOOP_TERM_CH1"),
    ("TP6",  "TestPoint:TestPoint_Pad_1.0x1.0mm",  28, 11,  0, "LOOP_TERM_CH2"),
    ("TP7",  "TestPoint:TestPoint_Pad_1.0x1.0mm",  36,  8,  0, "1WIRE"),
    # I2C
    ("TP8",  "TestPoint:TestPoint_Pad_1.0x1.0mm",  64, 44,  0, "I2C_SDA"),
    ("TP9",  "TestPoint:TestPoint_Pad_1.0x1.0mm",  66, 44,  0, "I2C_SCL"),
    # Solar and battery raw terminals
    ("TP10", "TestPoint:TestPoint_Pad_1.0x1.0mm",  64,  4,  0, "VSOLAR_IN"),
    ("TP11", "TestPoint:TestPoint_Pad_1.0x1.0mm",  74, 38,  0, "VBAT_RAW"),
    # Interrupt signals
    ("TP12", "TestPoint:TestPoint_Pad_1.0x1.0mm",  22, 24,  0, "ADS_DRDY"),
    ("TP13", "TestPoint:TestPoint_Pad_1.0x1.0mm",  24, 24,  0, "MAX_ALRT"),
    ("TP14", "TestPoint:TestPoint_Pad_1.0x1.0mm",  64, 14,  0, "/CHRG_SOLAR"),
]

# Key nets declared in the PCB netlist
# Net id 0 = unconnected; named nets start at 1
NETS = [
    "GND",
    "+3V3",
    "VBAT",
    "VUSB",
    "VUSB_IN",
    "VSOLAR",
    "VSOLAR_IN",
    "ADC_CH0",
    "ADC_CH1",
    "ADC_CH2",
    "1WIRE",
    "I2C_SDA",
    "I2C_SCL",
    "GPIO13_LED",
    "UART_TX",
    "UART_RX",
    "EN",
    "BOOT",
    "MPPT_REF",
    "/CHRG_USB",
    "/DONE_USB",
    "/CHRG_SOLAR",
    "/DONE_SOLAR",
    "VLOOP",
    "VBOOST_EN",
    "CHRG_USB_DIS",
    "SOLAR_DET",
    "BATT_DIV_EN",
    "ADS_DRDY",
    "MAX_ALRT",
    "LOOP_TERM_CH1",
    "LOOP_TERM_CH2",
    "+3V3_ADS",
    "VBAT_RAW",
]


def pcb_net_declarations() -> str:
    lines = []
    for i, net in enumerate(NETS, start=1):
        lines.append(f'  (net {i} "{net}")')
    return "\n".join(lines)


def pcb_footprint(ref: str, fp: str, x: float, y: float, rot: float, value: str) -> str:
    """
    Generate a minimal KiCad 10 footprint placement s-expression.
    We don't embed full pad geometry (that lives in the footprint library);
    we just emit the placed instance with reference/value text.
    """
    layer = "F.Cu"
    return f"""
  (footprint "{fp}" (layer "{layer}") (at {x:.3f} {y:.3f} {rot:.1f})
    (uuid "{uid()}")
    (property "Reference" "{ref}" (at 0 -2 0) (layer "F.SilkS")
      (uuid "{uid()}")
      (effects (font (size 1 1) (thickness 0.15)))
    )
    (property "Value" "{value}" (at 0 2 0) (layer "F.Fab")
      (uuid "{uid()}")
      (effects (font (size 1 1) (thickness 0.15)))
    )
  )"""


def pcb_mounting_hole(x: float, y: float) -> str:
    """Generate a mounting hole footprint (M3, 3.2mm drill)."""
    return f"""
  (footprint "MountingHole:MountingHole_3.2mm_M3" (layer "F.Cu") (at {x:.3f} {y:.3f} 0)
    (uuid "{uid()}")
    (property "Reference" "MH" (at 0 -4 0) (layer "F.SilkS")
      (uuid "{uid()}")
      (effects (font (size 1 1) (thickness 0.15)))
    )
    (property "Value" "MountingHole_3.2mm_M3" (at 0 4 0) (layer "F.Fab")
      (uuid "{uid()}")
      (effects (font (size 1 1) (thickness 0.15)))
    )
    (pad "" np_thru_hole circle (at 0 0) (size 3.2 3.2) (drill 3.2)
      (layers "*.Cu" "*.Mask")
      (uuid "{uid()}")
    )
  )"""


def pcb_board_outline() -> str:
    """
    Board outline as gr_line elements on Edge.Cuts.
    Origin lower-left = (0,0); KiCad PCB y increases downward.
    """
    w, h = BOARD_W, BOARD_H
    lines = []
    corners = [
        ((0, 0),   (w, 0)),
        ((w, 0),   (w, h)),
        ((w, h),   (0, h)),
        ((0, h),   (0, 0)),
    ]
    for (x1, y1), (x2, y2) in corners:
        lines.append(
            f'  (gr_line (start {x1:.3f} {y1:.3f}) (end {x2:.3f} {y2:.3f})\n'
            f'    (stroke (width 0.05) (type solid)) (layer "Edge.Cuts")\n'
            f'    (uuid "{uid()}")\n'
            f'  )'
        )
    return "\n".join(lines)


def pcb_thermal_zone_u7() -> str:
    """
    GND thermal copper pour for U7 (CN3791, SOIC-8) at PCB position (60, 10).
    10x10 mm solid GND pour on F.Cu and B.Cu connected via thermal vias.
    Per design.md: reduces effective theta_JA to 50-60 C/W for CN3791.
    Zone corners: (55, 5) to (65, 15) centred on U7 at (60, 10).
    Four thermal vias: 0.6mm drill, 1.0mm pad, spaced 2mm inside the zone.
    """
    # F.Cu zone (GND, solid fill, no thermal relief on zone connection)
    zone_fcu = f"""
  (zone (net 1) (net_name "GND") (layer "F.Cu") (uuid "{uid()}")
    (name "GND_THERMAL_U7")
    (hatch edge 0.508)
    (connect_pads thru_hole_only (clearance 0.2))
    (min_thickness 0.25)
    (fill yes (thermal_gap 0.3) (thermal_bridge_width 0.3))
    (polygon
      (pts (xy 55.0 5.0) (xy 65.0 5.0) (xy 65.0 15.0) (xy 55.0 15.0))
    )
  )"""

    # B.Cu mirror zone (same net, same area, same fill)
    zone_bcu = f"""
  (zone (net 1) (net_name "GND") (layer "B.Cu") (uuid "{uid()}")
    (name "GND_THERMAL_U7_B")
    (hatch edge 0.508)
    (connect_pads thru_hole_only (clearance 0.2))
    (min_thickness 0.25)
    (fill yes (thermal_gap 0.3) (thermal_bridge_width 0.3))
    (polygon
      (pts (xy 55.0 5.0) (xy 65.0 5.0) (xy 65.0 15.0) (xy 55.0 15.0))
    )
  )"""

    # Four thermal vias connecting F.Cu to B.Cu through U7 body area
    # Placed at 2mm spacing inside the 10x10 zone centred on (60,10)
    # Pattern: (58,8), (62,8), (58,12), (62,12)
    via_positions = [(58.0, 8.0), (62.0, 8.0), (58.0, 12.0), (62.0, 12.0)]
    vias_str = ""
    for vx, vy in via_positions:
        vias_str += f"""
  (via (at {vx:.3f} {vy:.3f}) (size 1.0) (drill 0.6)
    (layers "F.Cu" "B.Cu")
    (net 1)
    (uuid "{uid()}")
  )"""

    # Silkscreen label on F.SilkS identifying the thermal island
    silk_label = f"""
  (gr_text "GND_THERMAL_U7" (at 60 16.5 0) (layer "F.SilkS")
    (uuid "{uid()}")
    (effects (font (size 0.6 0.6) (thickness 0.1)))
  )"""

    return zone_fcu + zone_bcu + vias_str + silk_label


def pcb_u8_gnd_viastitch() -> str:
    """
    GND via-stitch perimeter around U8 (TPS61023, SOT-23-5) at (73,20) and
    L1 (inductor, at 74,12).  Perimeter ring of vias at ~2mm spacing outside
    the U8/L1 cluster to provide a low-inductance GND return path for the SW
    node's return current.  No solid copper pour under L1 — only the via ring.
    Per design.md: keep hot-loop trace (SW->L1->C20/C22) short and wide;
    via-stitch perimeter around the island; no pour under L1.
    Via ring boundary: (68,7) to (80,25), one via every ~2.5mm on perimeter.
    """
    # Perimeter coordinates (rectangular ring, clockwise, corners at each corner
    # plus intermediate points every ~2.5 mm)
    import math

    # Keep ring inside board boundary (board right edge = 80 mm; leave 1mm margin)
    x0, y0 = 68.0, 7.0
    x1, y1 = 79.0, 25.0

    perimeter_vias = []
    step = 2.5

    # Top edge: left to right
    x = x0
    while x <= x1:
        perimeter_vias.append((x, y0))
        x += step

    # Right edge: top to bottom
    y = y0 + step
    while y <= y1:
        perimeter_vias.append((x1, y))
        y += step

    # Bottom edge: right to left
    x = x1 - step
    while x >= x0:
        perimeter_vias.append((x, y1))
        x -= step

    # Left edge: bottom to top
    y = y1 - step
    while y > y0:
        perimeter_vias.append((x0, y))
        y -= step

    vias_str = ""
    for vx, vy in perimeter_vias:
        vias_str += f"""
  (via (at {vx:.3f} {vy:.3f}) (size 0.8) (drill 0.4)
    (layers "F.Cu" "B.Cu")
    (net 1)
    (uuid "{uid()}")
  )"""

    # Silkscreen comment on F.SilkS marking the SW node island boundary
    silk_label = f"""
  (gr_text "SW_ISLAND_U8" (at 74 26.5 0) (layer "F.SilkS")
    (uuid "{uid()}")
    (effects (font (size 0.6 0.6) (thickness 0.1)))
  )"""

    return vias_str + silk_label


def make_pcb() -> str:
    """Build the complete welld.kicad_pcb s-expression string."""

    net_decls = pcb_net_declarations()

    # Board outline
    outline = pcb_board_outline()

    # Mounting holes
    mholes = ""
    for x, y in MOUNTING_HOLES:
        mholes += pcb_mounting_hole(x, y)

    # Component footprints
    footprints = ""
    for ref, fp, x, y, rot, value in PCB_COMPONENTS:
        footprints += pcb_footprint(ref, fp, x, y, rot, value)

    # Thermal copper pours and via stitching
    thermal_u7 = pcb_thermal_zone_u7()
    u8_viastitch = pcb_u8_gnd_viastitch()

    # Board title graphic text
    title_text = f"""
  (gr_text "WellD  ESP32-C6 Well Monitor" (at 40 53.5 0) (layer "F.SilkS")
    (uuid "{uid()}")
    (effects (font (size 1.0 1.0) (thickness 0.15)))
  )"""

    pcb = f"""(kicad_pcb (version 20260206) (generator "pcbnew") (generator_version "10.0")

  (general
    (thickness 1.6)
    (legacy_teardrops no)
  )

  (paper "A3")

  (title_block
    (title "WellD Well-Level Monitor PCB")
    (date "2026-05-18")
    (company "WellD Project")
  )

  (layers
    (0 "F.Cu" signal)
    (31 "B.Cu" signal)
    (32 "B.Adhes" user "B.Adhesive")
    (33 "F.Adhes" user "F.Adhesive")
    (34 "B.Paste" user)
    (35 "F.Paste" user)
    (36 "B.SilkS" user "B.Silkscreen")
    (37 "F.SilkS" user "F.Silkscreen")
    (38 "B.Mask" user)
    (39 "F.Mask" user)
    (40 "Dwgs.User" user "User.Drawings")
    (41 "Cmts.User" user "User.Comments")
    (42 "Eco1.User" user "User.Eco1")
    (43 "Eco2.User" user "User.Eco2")
    (44 "Edge.Cuts" user)
    (45 "Margin" user)
    (46 "B.CrtYd" user "B.Courtyard")
    (47 "F.CrtYd" user "F.Courtyard")
    (48 "B.Fab" user "B.Fabrication")
    (49 "F.Fab" user "F.Fabrication")
    (50 "User.1" user)
    (51 "User.2" user)
    (52 "User.3" user)
    (53 "User.4" user)
    (54 "User.5" user)
    (55 "User.6" user)
    (56 "User.7" user)
    (57 "User.8" user)
    (58 "User.9" user)
  )

  (setup
    (pad_to_mask_clearance 0.1)
    (solder_mask_min_width 0.05)
    (allow_soldermask_bridges_in_footprints no)
    (pcbplotparams
      (layerselection 0x00010fc_ffffffff)
      (plot_on_all_layers_selection 0x0000000_00000000)
      (disableapertmacros no)
      (usegerberextensions no)
      (usegerberattributes yes)
      (usegerberadvancedattributes yes)
      (creategerberjobfile yes)
      (dashed_line_gap_ratio 0.5)
      (svguseinch no)
      (svgprecision 6)
      (excludeedgelayer yes)
      (plotframeref no)
      (viasonmask no)
      (mode 1)
      (useauxorigin no)
      (hpglpennumber 1)
      (hpglpenspeed 20)
      (hpglpendiameter 15.0)
      (dxfpolygonmode yes)
      (dxfimperialunits yes)
      (dxfusepcbnewfont yes)
      (psnegative no)
      (psa4output no)
      (plotreference yes)
      (plotvalue yes)
      (plotinvisibletext no)
      (sketchpadsonfab no)
      (subtractmaskfromsilk yes)
      (outputformat 1)
      (mirror no)
      (drillshape 1)
      (scaleselection 1)
      (outputdirectory "gerbers/")
    )
  )

  (net 0 "")
{net_decls}

{outline}

{title_text}

{mholes}

{footprints}

{thermal_u7}

{u8_viastitch}

)
"""
    return pcb


# ===========================================================================
# Entry point
# ===========================================================================

def make_sym_lib() -> str:
    """Build welld.kicad_sym — a KiCad symbol library with all custom welld ICs.

    Extracts the welld-prefixed symbol blocks from the (lib_symbols ...) section
    of the generated schematic (after upgrade) so the library file is always in
    sync with whatever kicad-cli writes.
    """
    sch_path = os.path.join(HERE, "welld.kicad_sch")
    text = open(sch_path).read()

    # Collect every top-level symbol inside lib_symbols whose name has no
    # library prefix and is one of our custom welld symbols (identified by the
    # fact that they appear as "welld:NAME" in component instances).
    welld_names = set()
    for m in re.finditer(r'\(lib_id "welld:([^"]+)"', text):
        welld_names.add(m.group(1))

    blocks = []
    for name in sorted(welld_names):
        # Symbols inside lib_symbols are at 2-tab indent.
        # In a .kicad_sym file they must be at 1-tab indent.
        # Strategy: find the full block (including leading \t\t), extract it,
        # then replace each line's leading \t\t with \t (net: -1 tab).
        # lib_symbols stores symbols as "welld:NAME" (KiCad 10 requirement)
        pat = re.compile(r'(?m)^\t\t\(symbol "welld:' + re.escape(name) + r'"')
        m = pat.search(text)
        if not m:
            continue
        start = m.start()   # include both leading tabs
        depth = 0
        i = start
        while i < len(text):
            if text[i] == '(':
                depth += 1
            elif text[i] == ')':
                depth -= 1
                if depth == 0:
                    block_lines = text[start:i + 1].splitlines()
                    # Remove exactly one leading tab; strip "welld:" prefix from
                    # the first line so .kicad_sym stores plain names (correct
                    # sym lib format — library name is implicit from the file).
                    reindented = []
                    for idx, ln in enumerate(block_lines):
                        stripped = ln[1:] if ln.startswith('\t') else ln
                        if idx == 0:
                            stripped = stripped.replace(
                                f'(symbol "welld:{name}"', f'(symbol "{name}"', 1)
                        reindented.append(stripped)
                    blocks.append('\n'.join(reindented))
                    break
            i += 1

    symbols_text = '\n'.join(blocks)
    return f"""(kicad_symbol_lib
\t(version 20260306)
\t(generator "kicad_symbol_editor")
\t(generator_version "10.0")
{symbols_text}
)
"""


def make_sym_lib_table() -> str:
    """Project-level sym-lib-table: direct paths bypass the global Table-type wrapper
    that KiCad 10's GUI does not always expand correctly."""
    sd = "/usr/share/kicad/symbols"
    libs = [
        ("welld",     "KiCad", "${KIPRJMOD}/welld.kicad_sym",     "WellD custom symbols"),
        ("Device",    "KiCad", f"{sd}/Device.kicad_sym",          "Generic devices"),
        ("Connector", "KiCad", f"{sd}/Connector.kicad_sym",       "Connectors"),
        ("Switch",    "KiCad", f"{sd}/Switch.kicad_sym",          "Switches"),
        ("Jumper",    "KiCad", f"{sd}/Jumper.kicad_sym",          "Jumpers"),
        ("power",     "KiCad", f"{sd}/power.kicad_sym",           "Power symbols"),
    ]
    entries = "\n".join(
        f'\t(lib (name "{n}") (type "{t}") (uri "{u}") (options "") (descr "{d}"))'
        for n, t, u, d in libs
    )
    return f"(sym_lib_table\n\t(version 7)\n{entries}\n)\n"


def main():
    print("Generating KiCad 10 project files …")

    print("\n[1/3] welld.kicad_pro")
    write("welld.kicad_pro", make_pro())

    print("\n[2/3] welld.kicad_sch")
    write("welld.kicad_sch", make_sch())
    sch_path = os.path.join(HERE, "welld.kicad_sch")
    result = subprocess.run(
        ["kicad-cli", "sch", "upgrade", "--force", sch_path],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print("  normalised via kicad-cli sch upgrade")
    else:
        print(f"  WARNING: kicad-cli upgrade failed: {result.stderr.strip()}")

    print("\n[3/3] welld.kicad_pcb")
    write("welld.kicad_pcb", make_pcb())

    print("\n[+] welld.kicad_sym  (custom symbol library)")
    write("welld.kicad_sym", make_sym_lib())
    sym_path = os.path.join(HERE, "welld.kicad_sym")
    subprocess.run(["kicad-cli", "sym", "upgrade", "--force", sym_path],
                   capture_output=True)

    print("[+] sym-lib-table  (project library paths)")
    write("sym-lib-table", make_sym_lib_table())

    print("\nDone.  Files written to:", HERE)


if __name__ == "__main__":
    main()
