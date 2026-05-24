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
    """Locate KiCad symbol libraries across platforms.

    Priority:
      1. System-installed KiCad libraries (fastest, preferred)
      2. Previously cloned local copy in project dir
      3. None — caller will clone from GitLab
    """
    # 1. System-installed libraries
    system_candidates = [
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
    for path in system_candidates:
        if os.path.isdir(path):
            return path

    # 2. Previously cloned local copy
    local_clone = os.path.join(HERE, "kicad-libs", "symbols")
    if os.path.isdir(local_clone):
        return local_clone

    return None


def clone_kicad_libs() -> str:
    """Clone KiCad official libraries from GitLab as a last resort."""
    libs_dir = os.path.join(HERE, "kicad-libs")
    sym_dir = os.path.join(libs_dir, "symbols")

    if os.path.isdir(sym_dir):
        print(f"  Using cached KiCad libraries in {sym_dir}")
        return sym_dir

    print("  No system KiCad libraries found.")
    print("  Cloning from GitLab: https://gitlab.com/kicad/libraries/kicad-symbols")
    print("  This may take a minute...")

    result = subprocess.run(
        ["git", "clone", "--depth", "1",
         "https://gitlab.com/kicad/libraries/kicad-symbols.git",
         sym_dir],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        print(f"  WARNING: Failed to clone KiCad libraries: {result.stderr}")
        print("  Will use fallback inline symbols instead.")
        return ""

    print(f"  Successfully cloned KiCad libraries to {sym_dir}")
    return sym_dir


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
    "U6":    "PCM_Espressif:ESP32-C6-MINI-1U",
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
    "L1":    "Inductor_SMD:L_Vishay_IFSC-1515AH_4x4x1.8mm",
    "L2":    "Inductor_SMD:L_Vishay_IFSC-1515AH_4x4x1.8mm",
    "FB1":   "Inductor_SMD:L_0402_1005Metric",
    "F2":    "Fuse:Fuse_1206_3216Metric",
    "Q2":    "Package_TO_SOT_SMD:SOT-23",
    "J1":    "WellD:XT30PW-F_RightAngle",
    "J3":    "Connector_Coaxial:SMA_Amphenol_132289_EdgeMount",
    "J4":    "TerminalBlock_Phoenix:TerminalBlock_Phoenix_PT-1,5-3-3.5-H_1x03_P3.50mm_Horizontal",
    "J5":    "TerminalBlock_Phoenix:TerminalBlock_Phoenix_PT-1,5-3-3.5-H_1x03_P3.50mm_Horizontal",
    "J6":    "TerminalBlock_Phoenix:TerminalBlock_Phoenix_PT-1,5-3-3.5-H_1x03_P3.50mm_Horizontal",
    "J7":    "TerminalBlock_Phoenix:TerminalBlock_Phoenix_PT-1,5-3-3.5-H_1x03_P3.50mm_Horizontal",
    "J8":    "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
    "J9":    "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical",
    "J10":   "Connector_PinHeader_1.27mm:PinHeader_1x06_P1.27mm_Vertical",
    "J12":   "TerminalBlock_Phoenix:TerminalBlock_Phoenix_PT-1,5-2-3.5-H_1x02_P3.50mm_Horizontal",
    "J13":   "Connector_USB:USB_C_Receptacle_GCT_USB4135-GF-A_6P_TopMnt_Horizontal",
    "SW1":   "Button_Switch_SMD:SW_Push_1P1T_NO_CK_KSC6xxG",
    "SW2":   "Button_Switch_SMD:SW_Push_1P1T_NO_CK_KSC6xxG",
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
        return "Jumper:SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm"
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
    "J1":    "C601498",
    "L1":    "C376098",
    "L2":    "C376098",
    "C_BST": "C14663",
}

COMPONENTS = [
    # ref,      value,               lib_id,                          x,     y
    # ── Row 1: Power Inputs (y=25-65) ─────────────────────────────────────────
    # Solar input (left)
    ("J12",  "Solar",            "Connector:Conn_01x02_Pin",       25,    30),
    ("D14",  "SMAJ28CA",         "Device:D_TVS",                   25,    55),
    ("D6",   "MBRS140",          "Device:D_Schottky",              55,    30),
    ("D8",   "SMAJ28CA",         "Device:D_TVS",                   55,    55),
    ("C17",  "10uF",             "Device:C",                       85,    30),
    ("U7",   "CN3722",           "welld:CN3722",                   85,    55),
    ("C18",  "10uF",             "Device:C",                      115,    30),
    ("R19",  "2k0",              "Device:R",                       25,    80),
    ("R20",  "36k",              "Device:R",                       45,    80),
    ("R21",  "10k",              "Device:R",                       65,    80),
    ("R33",  "604k",             "Device:R",                       85,    80),
    ("R34",  "100k",             "Device:R",                      105,    80),
    ("R22",  "1k DNF",           "Device:R",                      125,    80),
    ("D7",   "LED",              "Device:LED",                     25,   105),

    # USB-C input (center)
    ("J13",  "USB-C",            "welld:USB_C_Power",             165,    30),
    ("R_CC1","5k1",              "Device:R",                      165,    55),
    ("R_CC2","5k1",              "Device:R",                      165,    80),
    ("U11",  "USBLC6",           "welld:USBLC6_2SC6",             195,    30),
    ("F2",   "Polyfuse",         "Device:Polyfuse",               195,    55),
    ("C27",  "4.7uF",            "Device:C",                      195,    80),
    ("U12",  "TP5100",           "welld:TP5100",                  225,    30),
    ("C28",  "10uF",             "Device:C",                      225,    55),
    ("C29",  "10uF",             "Device:C",                      225,    80),
    ("R35",  "1k2",              "Device:R",                      255,    30),
    ("R36",  "100k",             "Device:R",                      255,    55),
    ("R37",  "4k7",              "Device:R",                      255,    80),
    ("R38",  "4k7",              "Device:R",                      255,   105),

    # Battery + protection (right)
    ("J1",   "XT30PW-F",         "Connector:Conn_01x02_Pin",      300,    30),
    ("D13",  "SMAJ10CA",         "Device:D_TVS",                  300,    55),
    ("D5",   "AO3407",           "welld:AO3407",                  300,    80),
    ("R31",  "10k",              "Device:R",                      300,   105),

    # ── Row 2: Main Circuitry (y=125-185) ─────────────────────────────────────
    # 3.3V Buck (left)
    ("U1",   "AP63205",          "welld:AP63205WU",                25,   140),
    ("L2",   "4.7uH",            "Device:L",                       25,   165),
    ("C9",   "100nF",            "Device:C",                       25,   190),
    ("C10",  "1uF",              "Device:C",                       50,   140),
    ("C11",  "100nF",            "Device:C",                       50,   165),
    ("C12",  "1uF",              "Device:C",                       50,   190),
    ("C_BUCK","10uF",            "Device:C",                       75,   140),
    ("R11",  "10k",              "Device:R",                       75,   165),

    # ESP32-C6 (center)
    ("U6",   "ESP32-C6",         "welld:ESP32_C6_MINI_1U",        115,   140),
    ("SW1",  "RESET",            "Switch:SW_Push",                115,   115),
    ("SW2",  "BOOT",             "Switch:SW_Push",                140,   115),
    ("R12",  "10k",              "Device:R",                      115,   190),
    ("R13",  "10k",              "Device:R",                      140,   190),
    ("C13",  "100nF",            "Device:C",                      165,   140),
    ("C14a", "100nF",            "Device:C",                      165,   165),
    ("C14b", "100nF",            "Device:C",                      165,   190),
    ("C14c", "100nF",            "Device:C",                      190,   140),
    ("C14d", "100nF",            "Device:C",                      190,   165),
    ("C15",  "10uF",             "Device:C",                      190,   190),

    # Status LED
    ("D4",   "Status",           "Device:LED",                    115,   215),
    ("R14",  "1k",               "Device:R",                      140,   215),

    # Sensor interfaces (right)
    ("J4",   "4-20mA_1",         "Connector:Conn_01x03_Pin",      230,   125),
    ("J5",   "4-20mA_2",         "Connector:Conn_01x03_Pin",      260,   125),
    ("J6",   "DS18B20",          "Connector:Conn_01x03_Pin",      290,   125),
    ("J7",   "Spare",            "Connector:Conn_01x03_Pin",      320,   125),
    ("R32",  "33R",              "Device:R",                      230,   150),
    ("D1",   "PRTR5V",           "welld:PRTR5V0U2X",              230,   175),
    ("D12",  "PRTR5V",           "welld:PRTR5V0U2X",              260,   175),
    ("R2",   "100R",             "Device:R",                      230,   200),
    ("R3",   "100R",             "Device:R",                      260,   200),
    ("D9",   "SMAJ3.3",          "Device:D_TVS",                  290,   150),
    ("D10",  "SMAJ3.3",          "Device:D_TVS",                  320,   150),
    ("C3",   "1uF",              "Device:C",                      290,   175),
    ("C4",   "10uF",             "Device:C",                      320,   175),
    ("C_SH1","10nF",             "Device:C",                      290,   200),
    ("R4",   "100R",             "Device:R",                      350,   125),
    ("R5",   "100R",             "Device:R",                      350,   150),
    ("C5",   "1uF",              "Device:C",                      350,   175),
    ("C6",   "10uF",             "Device:C",                      350,   200),
    ("C_SH2","10nF",             "Device:C",                      380,   125),
    ("R6",   "4k7",              "Device:R",                      380,   150),
    ("C7",   "100nF",            "Device:C",                      380,   175),

    # Expansion headers (far right)
    ("J8",   "I2C",              "Connector:Conn_01x04_Pin",      230,   230),
    ("J9",   "GPIO",             "Connector:Conn_01x08_Pin",      260,   230),
    ("J10",  "PROG",             "Connector:Conn_01x06_Pin",      290,   230),
    ("J3",   "132289",           "welld:U_FL_Antenna",            320,   230),
    ("R9",   "4k7",              "Device:R",                      350,   230),
    ("R10",  "4k7",              "Device:R",                      380,   230),

    # ── Row 3: Support Circuits (y=245-305) ───────────────────────────────────
    # VLOOP boost (left)
    ("U8",   "MT3608",           "welld:MT3608B",                  25,   250),
    ("L1",   "4.7uH",            "Device:L",                       25,   275),
    ("C_BST","100nF",            "Device:C",                       25,   300),
    ("C22",  "10uF 25V",         "Device:C",                       50,   250),
    ("R23",  "1.91M",            "Device:R",                       50,   275),
    ("R24",  "100k",             "Device:R",                       50,   300),
    ("C19",  "10uF",             "Device:C",                       75,   250),
    ("C20",  "22uF 25V",         "Device:C",                       75,   275),
    ("D11",  "SMAJ13",           "Device:D_TVS",                   75,   300),
    ("C21",  "100nF",            "Device:C",                      100,   250),

    # Precision ADC (center-left)
    ("FB1",  "Ferrite",          "Device:L",                      125,   250),
    ("C23",  "100nF",            "Device:C",                      125,   275),
    ("C24",  "1uF",              "Device:C",                      125,   300),
    ("U9",   "ADS1115",          "welld:ADS1115",                 150,   250),
    ("R28",  "100R",             "Device:R",                      150,   275),

    # Battery divider (center)
    ("Q2",   "BSS123",           "Device:Q_NMOS",                 190,   250),
    ("R7",   "330k",             "Device:R",                      190,   275),
    ("R8",   "100k",             "Device:R",                      190,   300),
    ("C8",   "100nF",            "Device:C",                      215,   250),
    ("R26",  "4k7",              "Device:R",                      215,   275),

    # Solder jumpers (right)
    ("SJ1",  "VBOOST",           "Jumper:SolderJumper_2_Open",    255,   250),
    ("SJ2",  "VLOOP",            "Jumper:SolderJumper_2_Open",    255,   275),
    ("SJ3",  "LED_DIS",          "Jumper:SolderJumper_2_Open",    255,   300),
    ("SJ4",  "UART_TX",          "Jumper:SolderJumper_2_Open",    280,   250),
    ("SJ5",  "UART_RX",          "Jumper:SolderJumper_2_Open",    280,   275),

    # ── Row 4: Test Points (y=330) ────────────────────────────────────────────
    ("TP1",  "VBAT",             "welld:TestPoint_Pad",            25,   330),
    ("TP2",  "VLOOP",            "welld:TestPoint_Pad",            50,   330),
    ("TP3",  "+3V3",             "welld:TestPoint_Pad",            75,   330),
    ("TP4",  "GND",              "welld:TestPoint_Pad",           100,   330),
    ("TP5",  "LOOP1",            "welld:TestPoint_Pad",           125,   330),
    ("TP6",  "LOOP2",            "welld:TestPoint_Pad",           150,   330),
    ("TP7",  "1WIRE",            "welld:TestPoint_Pad",           175,   330),
    ("TP8",  "SDA",              "welld:TestPoint_Pad",           200,   330),
    ("TP9",  "SCL",              "welld:TestPoint_Pad",           225,   330),
    ("TP10", "VSOLAR",           "welld:TestPoint_Pad",           250,   330),
    ("TP11", "VBAT_RAW",         "welld:TestPoint_Pad",           275,   330),
    ("TP12", "ADS_DRDY",         "welld:TestPoint_Pad",           300,   330),
    ("TP14", "CHRG_SOL",         "welld:TestPoint_Pad",           325,   330),
    ("TP15", "CHRG_USB",         "welld:TestPoint_Pad",           350,   330),
]


# ── Hierarchical sheet component assignments ───────────────────────────────
# Each sheet gets its own .kicad_sch file with a tighter layout.

SHEET_ASSIGNMENTS: dict[str, list[str]] = {
    "power": [
        "J12", "D14", "D6", "D8", "C17", "U7", "C18",
        "R19", "R20", "R21", "R33", "R34", "R22", "D7",
        "J13", "R_CC1", "R_CC2", "U11", "F2", "C27",
        "U12", "C28", "C29", "R35", "R36", "R37", "R38",
        "J1", "D13", "D5", "R31",
        "U1", "L2", "C9", "C10", "C11", "C12", "C_BUCK", "R11",
        "U8", "L1", "C_BST", "C22", "R23", "R24", "C19", "C20", "D11", "C21",
    ],
    "mcu": [
        "U6", "SW1", "SW2", "R12", "R13",
        "C13", "C14a", "C14b", "C14c", "C14d", "C15",
        "D4", "R14",
    ],
    "sensors": [
        "J4", "J5", "J6", "J7",
        "R32", "D1", "D12", "R2", "R3",
        "D9", "D10", "C3", "C4", "C_SH1",
        "R4", "R5", "C5", "C6", "C_SH2", "R6", "C7",
        "FB1", "C23", "C24", "U9", "R28",
        "Q2", "R7", "R8", "C8", "R26",
    ],
    "interfaces": [
        "J8", "J9", "J10", "J3", "R9", "R10",
        "SJ1", "SJ2", "SJ3", "SJ4", "SJ5",
        "TP1", "TP2", "TP3", "TP4", "TP5", "TP6", "TP7",
        "TP8", "TP9", "TP10", "TP11", "TP12", "TP14", "TP15",
    ],
}


def _filter_components(refs: list[str]) -> list[tuple]:
    """Return (ref, value, lib_id, x, y) tuples matching the given ref list."""
    comps = []
    for ref, value, lib_id, x, y in COMPONENTS:
        if ref in refs:
            comps.append((ref, value, lib_id, x, y))
    return comps


def _remap_positions(comps: list[tuple], x0: float, y0: float,
                     scale: float = 0.5) -> list[tuple]:
    """Remap component positions to a tighter grid centred on (x0, y0)."""
    if not comps:
        return []
    xs = [c[3] for c in comps]
    ys = [c[4] for c in comps]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    cx = (min_x + max_x) / 2
    cy = (min_y + max_y) / 2
    remapped = []
    for ref, value, lib_id, x, y in comps:
        nx = x0 + (x - cx) * scale
        ny = y0 + (y - cy) * scale
        remapped.append((ref, value, lib_id, nx, ny))
    return remapped


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


def hierarchical_label(net: str, x: float, y: float, shape: str = "bidirectional") -> str:
    """Generate a KiCad hierarchical label for subsheets."""
    return f"""  (hierarchical_label "{net}"
    (shape {shape})
    (at {x:.2f} {y:.2f} 0)
    (fields_autoplaced yes)
    (effects (font (size 1.27 1.27)) (justify left))
    (uuid "{uid()}")
  )"""


def sheet_symbol(name: str, filename: str, x: float, y: float,
                 width: float, height: float, pins: list[tuple]) -> str:
    """Generate a KiCad sheet symbol (hierarchical block) on the parent sheet.

    pins: list of (pin_name, direction, offset_x, offset_y)
        direction: input, output, bidirectional
        offset is relative to the sheet origin (x, y)
    """
    sx, sy = x, y
    pin_strs = ""
    for pname, pdir, px, py in pins:
        pin_strs += f"""
    (pin "{pname}" {pdir} (at {sx + px:.2f} {sy + py:.2f} 0)
      (effects (font (size 1.27 1.27)) (justify left))
      (uuid "{uid()}")
    )"""

    return f"""  (sheet
    (at {sx:.2f} {sy:.2f})
    (size {width:.2f} {height:.2f})
    (fields_autoplaced yes)
    (stroke (width 0.1524) (type solid) (color 0 0 0 0))
    (fill (color 0 0 0 0.0000))
    (uuid "{uid()}")
    (property "Sheet name" "{name}"
      (at {sx:.2f} {sy - 1.27:.2f} 0)
      (do_not_autoplace no)
      (effects (font (size 1.27 1.27)) (justify left bottom))
    )
    (property "Sheet file" "{filename}"
      (at {sx:.2f} {sy + height + 1.27:.2f} 0)
      (do_not_autoplace no)
      (effects (font (size 1.27 1.27)) (justify left top))
    )
{pin_strs}
  )"""


KICAD_SYM_DIR = find_kicad_sym_dir() or clone_kicad_libs() or "/usr/share/kicad/symbols"

def _extract_sym(lib: str, name: str) -> str:
    """Extract a single top-level symbol block from a .kicad_sym library file
    or a .kicad_symdir directory.

    Returns the raw s-expression text (unindented) suitable for embedding
    directly inside a (lib_symbols ...) block, or '' if not found.
    """
    # Try old flat format first: LibraryName.kicad_sym
    path = os.path.join(KICAD_SYM_DIR, f"{lib}.kicad_sym")
    if os.path.isfile(path):
        try:
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
        except OSError:
            return ""
    else:
        # Try new directory format: LibraryName.kicad_symdir/SymbolName.kicad_sym
        symdir = os.path.join(KICAD_SYM_DIR, f"{lib}.kicad_symdir")
        path = os.path.join(symdir, f"{name}.kicad_sym")
        if os.path.isfile(path):
            try:
                with open(path, encoding="utf-8") as fh:
                    text = fh.read()
            except OSError:
                return ""
        else:
            return ""

    # Match the opening of a top-level symbol with exactly this name.
    # Accept tabs or spaces for indentation.
    pattern = re.compile(r'(?m)^[ \t]*\(symbol "' + re.escape(name) + r'"(?:\s|\))')
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

    # ---- SMA edge-launch antenna stub (Amphenol 132289) --------------------
    ufl = hdr("U_FL_Antenna", "J", 3.81, "132289", -3.81,
              "Connector_Coaxial:SMA_Amphenol_132289_EdgeMount") + f"""
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


def make_subsheet_sch(sheet_name: str, sheet_uuid: str, page: str = "A4") -> str:
    """Generate a sub-sheet .kicad_sch file for one functional block."""
    refs = SHEET_ASSIGNMENTS[sheet_name]
    comps = _filter_components(refs)
    
    # Tighter layout: remap to A4 page with 0.5x scale
    cx, cy = 148.5, 105.0  # A4 landscape centre
    remapped = _remap_positions(comps, cx, cy, scale=0.6)
    
    # Build component strings
    comps_str = ""
    for ref, value, lib_id, x, y in remapped:
        comps_str += sch_component(ref, value, lib_id, x, y, sheet_uuid)
    
    # Power symbols for each sheet
    power_str = ""
    if sheet_name in ("power", "mcu", "sensors", "interfaces"):
        power_str += sch_power_symbol("+3V3", 20, 20, sheet_uuid)
        power_str += sch_power_symbol("GND", 20, 190, sheet_uuid)
    if sheet_name in ("power", "sensors", "interfaces"):
        power_str += sch_power_symbol("VBAT", 270, 20, sheet_uuid)
    
    # Hierarchical labels (cross-sheet connections)
    sheet_labels = {
        "power": [
            ("VSOLAR_IN", 20, 50, "input"),
            ("VUSB_IN", 20, 70, "input"),
            ("VBAT", 270, 80, "output"),
            ("+3V3", 270, 100, "output"),
            ("VLOOP", 270, 120, "output"),
            ("/CHRG_SOLAR", 20, 90, "output"),
            ("/CHRG_USB", 20, 110, "output"),
        ],
        "mcu": [
            ("+3V3", 20, 50, "input"),
            ("VBAT", 270, 50, "input"),
            ("EN", 270, 70, "output"),
            ("BOOT", 270, 90, "output"),
            ("GPIO13_LED", 270, 110, "output"),
            ("UART_TX", 270, 130, "output"),
            ("UART_RX", 270, 150, "output"),
            ("I2C_SDA", 270, 170, "bidirectional"),
            ("I2C_SCL", 270, 190, "bidirectional"),
            ("1WIRE", 270, 210, "bidirectional"),
            ("ADS_DRDY", 270, 230, "input"),
            ("BATT_DIV_EN", 270, 250, "output"),
            ("VBOOST_EN", 270, 270, "output"),
        ],
        "sensors": [
            ("+3V3", 20, 50, "input"),
            ("VBAT", 20, 70, "input"),
            ("VLOOP", 20, 90, "input"),
            ("ADC_CH0", 270, 50, "output"),
            ("ADC_CH1", 270, 70, "output"),
            ("ADC_CH2", 270, 90, "output"),
            ("1WIRE", 270, 110, "bidirectional"),
            ("I2C_SDA", 270, 130, "bidirectional"),
            ("I2C_SCL", 270, 150, "bidirectional"),
            ("ADS_DRDY", 270, 170, "output"),
            ("BATT_DIV_EN", 20, 110, "input"),
            ("VBAT_RAW", 270, 190, "output"),
        ],
        "interfaces": [
            ("+3V3", 20, 50, "input"),
            ("VBAT", 20, 70, "input"),
            ("UART_TX", 20, 90, "input"),
            ("UART_RX", 20, 110, "input"),
            ("I2C_SDA", 20, 130, "input"),
            ("I2C_SCL", 20, 150, "input"),
            ("1WIRE", 20, 170, "input"),
            ("EN", 20, 190, "input"),
            ("BOOT", 20, 210, "input"),
            ("GPIO13_LED", 20, 230, "input"),
            ("ADS_DRDY", 20, 250, "input"),
        ],
    }
    
    labels_str = ""
    for net, x, y, shape in sheet_labels.get(sheet_name, []):
        labels_str += hierarchical_label(net, x, y, shape)
    
    # Local wires (simplified)
    def wire(x1, y1, x2, y2):
        return f"""
  (wire (pts (xy {x1:.2f} {y1:.2f}) (xy {x2:.2f} {y2:.2f}))
    (stroke (width 0) (type default))
    (uuid "{uid()}")
  )"""
    
    wires_str = ""
    # Add a few structural wires per sheet
    if sheet_name == "power":
        wires_str += wire(30, 60, 50, 60)  # solar path
        wires_str += wire(160, 60, 180, 60)  # USB path
        wires_str += wire(30, 120, 50, 120)  # battery path
        wires_str += wire(160, 120, 180, 120)  # buck path
    elif sheet_name == "mcu":
        wires_str += wire(120, 100, 120, 120)  # ESP32 power
        wires_str += wire(120, 140, 120, 160)  # decoupling
    elif sheet_name == "sensors":
        wires_str += wire(40, 80, 60, 80)  # sensor net
        wires_str += wire(40, 100, 60, 100)  # sensor net
    
    lib_symbols = make_sch_lib_symbols()
    
    sch = f"""(kicad_sch
  (version 20260306)
  (generator "eeschema")
  (generator_version "10.0")
  (uuid "{sheet_uuid}")
  (paper "{page}")
  (title_block
    (title "WellD – {sheet_name.capitalize()}")
    (date "2026-05-18")
    (company "WellD Project")
  )
  (lib_symbols
{lib_symbols}
  )

{labels_str}

{power_str}

{comps_str}

{wires_str}

)
"""
    return sch


def make_sch() -> str:
    """Build the main welld.kicad_sch with 4 hierarchical sheet symbols."""
    root_uuid = uid()
    
    # Sheet layout on A3 parent page
    # Power  top-left,  MCU     top-right
    # Sensors bottom-left, Interfaces bottom-right
    SHEETS = [
        ("power",      "power.kicad_sch",      25.4,  25.4,  120, 100, [
            ("VSOLAR_IN",   "input",  0, 30),
            ("VUSB_IN",     "input",  0, 50),
            ("VBAT",        "output", 120, 40),
            ("+3V3",        "output", 120, 60),
            ("VLOOP",       "output", 120, 80),
            ("/CHRG_SOLAR", "output", 0, 70),
            ("/CHRG_USB",   "output", 0, 90),
        ]),
        ("mcu",        "mcu.kicad_sch",        165.1, 25.4,  120, 100, [
            ("+3V3",        "input",  0, 30),
            ("VBAT",        "input",  0, 50),
            ("EN",          "output", 120, 30),
            ("BOOT",        "output", 120, 45),
            ("GPIO13_LED",  "output", 120, 60),
            ("UART_TX",     "output", 120, 75),
            ("UART_RX",     "output", 120, 90),
            ("I2C_SDA",     "bidirectional", 120, 105),
            ("I2C_SCL",     "bidirectional", 120, 120),
            ("1WIRE",       "bidirectional", 120, 135),
            ("ADS_DRDY",    "input", 120, 150),
            ("BATT_DIV_EN", "output", 120, 165),
            ("VBOOST_EN",   "output", 120, 180),
        ]),
        ("sensors",    "sensors.kicad_sch",    25.4,  152.4, 120, 100, [
            ("+3V3",        "input",  0, 30),
            ("VBAT",        "input",  0, 50),
            ("VLOOP",       "input",  0, 70),
            ("ADC_CH0",     "output", 120, 30),
            ("ADC_CH1",     "output", 120, 50),
            ("ADC_CH2",     "output", 120, 70),
            ("1WIRE",       "bidirectional", 120, 90),
            ("I2C_SDA",     "bidirectional", 120, 110),
            ("I2C_SCL",     "bidirectional", 120, 130),
            ("ADS_DRDY",    "output", 120, 150),
            ("BATT_DIV_EN", "input",  0, 90),
            ("VBAT_RAW",    "output", 120, 170),
        ]),
        ("interfaces", "interfaces.kicad_sch", 165.1, 152.4, 120, 100, [
            ("+3V3",        "input",  0, 30),
            ("VBAT",        "input",  0, 50),
            ("UART_TX",     "input",  0, 70),
            ("UART_RX",     "input",  0, 85),
            ("I2C_SDA",     "input",  0, 100),
            ("I2C_SCL",     "input",  0, 115),
            ("1WIRE",       "input",  0, 130),
            ("EN",          "input",  0, 145),
            ("BOOT",        "input",  0, 160),
            ("GPIO13_LED",  "input",  0, 175),
            ("ADS_DRDY",    "input",  0, 190),
        ]),
    ]
    
    sheets_str = ""
    for name, filename, x, y, w, h, pins in SHEETS:
        sheets_str += sheet_symbol(name, filename, x, y, w, h, pins)
    
    # Main sheet wires: connect Power outputs to MCU/Sensors inputs
    def wire(x1, y1, x2, y2):
        return f"""
  (wire (pts (xy {x1:.2f} {y1:.2f}) (xy {x2:.2f} {y2:.2f}))
    (stroke (width 0) (type default))
    (uuid "{uid()}")
  )"""
    
    wires = [
        # +3V3: Power right -> MCU left, Sensors left
        wire(145.4, 85.4, 165.1, 55.4),
        wire(145.4, 85.4, 25.4, 182.4),
        # VBAT: Power right -> MCU left, Sensors left, Interfaces left
        wire(145.4, 65.4, 165.1, 75.4),
        wire(145.4, 65.4, 25.4, 202.4),
        wire(145.4, 65.4, 165.1, 202.4),
        # VLOOP: Power right -> Sensors left
        wire(145.4, 105.4, 25.4, 222.4),
        # UART: MCU right -> Interfaces left
        wire(285.1, 100.4, 165.1, 227.4),
        wire(285.1, 115.4, 165.1, 242.4),
        # I2C: MCU right -> Sensors right, Interfaces left
        wire(285.1, 130.4, 145.4, 262.4),
        wire(285.1, 145.4, 145.4, 282.4),
        wire(285.1, 130.4, 165.1, 257.4),
        wire(285.1, 145.4, 165.1, 272.4),
        # 1WIRE: MCU right -> Sensors right, Interfaces left
        wire(285.1, 160.4, 145.4, 242.4),
        wire(285.1, 160.4, 165.1, 287.4),
    ]
    wires_str = "".join(wires)
    
    # Global labels on main sheet for key nets
    global_labels = [
        ("VSOLAR_IN", 20, 20, "input"),
        ("VUSB_IN", 20, 40, "input"),
        ("GND", 297, 380, "passive"),
    ]
    global_labels_str = ""
    for net, x, y, shape in global_labels:
        global_labels_str += sch_global_label(net, x, y, shape)
    
    sch = f"""(kicad_sch
  (version 20260306)
  (generator "eeschema")
  (generator_version "10.0")
  (uuid "{root_uuid}")
  (paper "A3")
  (title_block
    (title "WellD Well-Level Monitor")
    (date "2026-05-18")
    (company "WellD Project")
    (comment 1 "Hierarchical schematic – 4 sheets")
  )
  (lib_symbols
  )

{global_labels_str}

{sheets_str}

{wires_str}

)
"""
    return sch


# ===========================================================================
# 3.  welld.kicad_pcb
# ===========================================================================

# Board dimensions (mm)
BOARD_W = 80.0
BOARD_H = 55.0

# Center the PCB on the A5 landscape page (210x148mm)
# Board is 80x55mm, so offset = (page - board) / 2
PCB_X_OFFSET = 65.0
PCB_Y_OFFSET = 46.5

# Mounting hole positions (mm from lower-left = PCB origin)
MOUNTING_HOLES = [
    (3.5,  3.5),
    (76.5, 3.5),
    (3.5,  51.5),
    (76.5, 51.5),
]

# PCB component placement: (ref, footprint, x, y, rotation, description)
# Footprints use standard KiCad 10 library paths.
# All positions are board-relative (0,0 = top-left of 80x55 mm board).
# PCB absolute = board-relative + (PCB_X_OFFSET, PCB_Y_OFFSET).
# Usable area: X=2..78, Y=2..53 (2 mm edge clearance).
# Keepouts:
#   J3 courtyard: X=34.24-45.76, Y=40.53-55 (no components)
#   J1 courtyard: X=-1.2-13.5, Y=26.6-40.4 (XT30 body at 270°; pins at board x=12)
#   Antenna keepout: X=0-30, Y=0-20 (no copper-bearing components)
#   MH exclusion: 4 mm radius around each mounting hole corner
# J1, J3, R9, R10, MH1-4 positions are LOCKED — do not move.
PCB_COMPONENTS = [

    # -------------------------------------------------------------------------
    # Zone 1 — Power (left strip, X=2..31)
    # -------------------------------------------------------------------------

    # --- Solar sub-group (top-left, Y=2..25) ---
    # J12 is in Zone 4 (connector strip); solar group clusters around U7
    # D14: 28V TVS at J12 input terminal (placed near Zone 4 — see Zone 4 entry)
    # U7 (CN3722 SOIC-8) — MPPT solar charger IC
    # Note: thermal zone in pcb_thermal_zone_u7() is centred on (60,10) board-rel;
    # we move U7 here and the zone will be updated in a follow-up pass.
    ("U7",    "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",      9.0,   8.0,    0, "CN3722"),
    # Input filter cap across U7 VIN
    ("C17",   "Capacitor_SMD:C_0805_2012Metric",          16.0,   5.0,    0, "10uF"),
    # Input protection Schottky (after D14 TVS)
    ("D6",    "Diode_SMD:D_SOD-123",                      22.0,   5.0,    0, "MBRS140"),
    # VIN TVS clamp across CN3722 VIN/GND (after D6)
    ("D8",    "Diode_SMD:D_SMA",                          28.0,   5.0,    0, "SMAJ28CA"),
    # CN3722 output / VBAT filter cap
    ("C18",   "Capacitor_SMD:C_0805_2012Metric",          16.0,  13.0,    0, "10uF"),
    # MPPT divider
    ("R19",   "Resistor_SMD:R_0402_1005Metric",           22.0,  10.0,    0, "2k0"),
    ("R20",   "Resistor_SMD:R_0402_1005Metric",           22.0,  14.0,    0, "36k"),
    ("R21",   "Resistor_SMD:R_0402_1005Metric",           27.0,  10.0,    0, "10k"),
    # CV divider (new for CN3722)
    ("R33",   "Resistor_SMD:R_0402_1005Metric",           27.0,  14.0,    0, "604k"),
    ("R34",   "Resistor_SMD:R_0402_1005Metric",           27.0,  18.0,    0, "100k"),
    # Solar charge LED + series resistor (DNF in production)
    ("D7",    "LED_SMD:LED_0603_1608Metric",               9.0,  18.0,    0, "LED"),
    ("R22",   "Resistor_SMD:R_0402_1005Metric",           14.0,  18.0,    0, "1k DNF"),

    # --- USB-C sub-group (mid-left, Y=22..36, clear of J1 courtyard) ---
    # J1 courtyard is X=0-13.6, Y=29-38; avoid with USB-C ICs
    # J13 goes on left edge, body inside board
    ("J13",   "Connector_USB:USB_C_Receptacle_GCT_USB4135-GF-A_6P_TopMnt_Horizontal",
                                                           5.0,  25.0,    0, "USB-C"),
    # CC pull-downs — within 3 mm of J13
    ("R_CC1", "Resistor_SMD:R_0402_1005Metric",          13.0,  23.0,    0, "5k1"),
    ("R_CC2", "Resistor_SMD:R_0402_1005Metric",          13.0,  26.0,    0, "5k1"),
    # VBUS ESD clamp
    ("U11",   "Package_TO_SOT_SMD:SOT-23-6",             19.0,  24.0,    0, "USBLC6"),
    # PTC fuse in series with VBUS
    ("F2",    "Fuse:Fuse_1206_3216Metric",                25.0,  24.0,    0, "Polyfuse"),
    # VUSB filter cap (after F2)
    ("C27",   "Capacitor_SMD:C_0805_2012Metric",          25.0,  28.0,    0, "4.7uF"),

    # --- TP5100 USB charger sub-group (Y=39..52, X=14..31) ---
    # Kept right of battery protection (D13/D5/R31) to avoid J1 courtyard
    ("U12",   "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",     21.0,  43.0,    0, "TP5100"),
    # U12 VIN bypass — within 2 mm
    ("C28",   "Capacitor_SMD:C_0805_2012Metric",          28.0,  40.0,    0, "10uF"),
    # U12 VBAT output bypass — within 3 mm
    ("C29",   "Capacitor_SMD:C_0805_2012Metric",          28.0,  44.0,    0, "10uF"),
    # PROG resistor (charge current set)
    ("R35",   "Resistor_SMD:R_0402_1005Metric",           16.0,  40.0,    0, "1k2"),
    # CE pull-up
    ("R36",   "Resistor_SMD:R_0402_1005Metric",           16.0,  44.0,    0, "100k"),
    # CE bleed to GND (fail-safe disable)
    ("R37",   "Resistor_SMD:R_0402_1005Metric",           16.0,  48.0,    0, "4k7"),
    # /CHRG pull-up to 3V3
    ("R38",   "Resistor_SMD:R_0402_1005Metric",           21.0,  48.0,    0, "4k7"),

    # --- Battery protection (X=2..12, Y=39..52) ---
    # D13: 10V TVS across battery terminals (J1)
    ("D13",   "Diode_SMD:D_SMA",                          6.0,  40.0,    0, "SMAJ10CA"),
    # D5: P-ch MOSFET reverse-polarity protection
    ("D5",    "Package_TO_SOT_SMD:SOT-23",                6.0,  45.0,    0, "AO3407"),
    # R31: D5 gate pull-down — within 2 mm of D5
    ("R31",   "Resistor_SMD:R_0402_1005Metric",           6.0,  49.0,    0, "10k"),

    # --- 3.3V Buck converter (X=2..16, Y=34..38, between J1 and TP5100) ---
    # Placed below USB-C group, above TP5100 group, tight to left edge
    ("U1",    "Package_TO_SOT_SMD:SOT-23-6",             10.0,  34.0,    0, "AP63205"),
    ("L2",    "Inductor_SMD:L_Vishay_IFSC-1515AH_4x4x1.8mm", 17.0,  34.0,    0, "4.7uH"),
    # VIN bypass caps — within 2 mm of U1
    ("C9",    "Capacitor_SMD:C_0402_1005Metric",          7.0,  36.5,    0, "100nF"),
    ("C10",   "Capacitor_SMD:C_0402_1005Metric",         10.0,  36.5,    0, "100nF"),
    # Output bypass caps — on +3V3 side of L2
    ("C11",   "Capacitor_SMD:C_0402_1005Metric",         20.0,  34.0,    0, "100nF"),
    ("C12",   "Capacitor_SMD:C_0402_1005Metric",         20.0,  36.5,    0, "1uF"),
    ("C_BUCK","Capacitor_SMD:C_0805_2012Metric",         25.0,  35.0,    0, "10uF"),
    # EN pull-up
    ("R11",   "Resistor_SMD:R_0402_1005Metric",         13.0,  36.5,    0, "10k"),

    # -------------------------------------------------------------------------
    # LOCKED — J1 (XT30PW-F battery connector, left side)
    # -------------------------------------------------------------------------
    ("J1",    "WellD:XT30PW-F_RightAngle",                2.0,  33.5,  270, "XT30PW-F"),

    # -------------------------------------------------------------------------
    # Zone 2 — MCU (center, X=32..66, Y=2..38)
    # Antenna keepout: X<30, Y<20 — U6 module is clear (center ~50,18)
    # -------------------------------------------------------------------------
    # U6: ESP32-C6-MINI-1U module (~16x14 mm body)
    ("U6",    "PCM_Espressif:ESP32-C6-MINI-1U",          50.0,  17.0,    0, "ESP32-C6"),
    # Module VCC3V3 decoupling — within 3 mm of module pads
    ("C14a",  "Capacitor_SMD:C_0402_1005Metric",         36.0,   7.0,    0, "100nF"),
    ("C14b",  "Capacitor_SMD:C_0402_1005Metric",         39.0,   7.0,    0, "100nF"),
    ("C14c",  "Capacitor_SMD:C_0402_1005Metric",         36.0,  10.0,    0, "100nF"),
    ("C14d",  "Capacitor_SMD:C_0402_1005Metric",         39.0,  10.0,    0, "100nF"),
    # Module VCC3V3 bulk
    ("C15",   "Capacitor_SMD:C_0805_2012Metric",         42.0,   8.0,    0, "10uF"),
    # Strapping resistors
    ("R12",   "Resistor_SMD:R_0402_1005Metric",          36.0,  14.0,    0, "10k"),
    ("R13",   "Resistor_SMD:R_0402_1005Metric",          39.0,  14.0,    0, "10k"),
    # EN reset cap
    ("C13",   "Capacitor_SMD:C_0402_1005Metric",         42.0,  14.0,    0, "100nF"),
    # Buttons — top edge of module, accessible for hand-press
    ("SW1",   "Button_Switch_SMD:SW_Push_1P1T_NO_CK_KSC6xxG",
                                                          42.0,   4.0,    0, "RESET"),
    ("SW2",   "Button_Switch_SMD:SW_Push_1P1T_NO_CK_KSC6xxG",
                                                          48.0,   4.0,    0, "BOOT"),
    # Status LED + current limit resistor — right of module
    ("D4",    "LED_SMD:LED_0603_1608Metric",              62.0,  28.0,    0, "Status"),
    ("R14",   "Resistor_SMD:R_0402_1005Metric",          58.0,  28.0,    0, "1k"),

    # -------------------------------------------------------------------------
    # Zone 3 — Analog / Sensors (X=56..66, Y=2..38)
    # ADS1115 kept away from MT3608B boost noise (Zone 5, bottom-center)
    # -------------------------------------------------------------------------
    # ADS1115 cluster — U9 MSOP-10 at center ~(62,20)
    ("U9",    "Package_SO:MSOP-10_3x3mm_P0.5mm",         62.0,  20.0,    0, "ADS1115"),
    # ADS1115 VDD ferrite bead (in 3V3 supply line to U9)
    ("FB1",   "Inductor_SMD:L_0402_1005Metric",          57.0,  17.0,    0, "Ferrite"),
    # ADS1115 VDD bypass caps — on U9 side of FB1, within 1 mm of U9
    ("C23",   "Capacitor_SMD:C_0402_1005Metric",         57.0,  20.0,    0, "100nF"),
    ("C24",   "Capacitor_SMD:C_0402_1005Metric",         57.0,  23.0,    0, "1uF"),
    # ALERT/DRDY series protection
    ("R28",   "Resistor_SMD:R_0402_1005Metric",          62.0,  25.0,    0, "100R"),

    # Battery divider — near U9 AIN2 input
    ("Q2",    "Package_TO_SOT_SMD:SOT-23",                57.0,   8.0,    0, "BSS123"),
    ("R7",    "Resistor_SMD:R_0402_1005Metric",           62.0,   6.0,    0, "330k"),
    ("R8",    "Resistor_SMD:R_0402_1005Metric",           62.0,   9.0,    0, "100k"),
    ("C8",    "Capacitor_SMD:C_0402_1005Metric",          57.0,  12.0,    0, "100nF"),
    ("R26",   "Resistor_SMD:R_0402_1005Metric",           62.0,  12.0,    0, "4k7"),

    # 4-20mA ch1 circuit — below U9
    ("D9",    "Diode_SMD:D_SMA",                          58.0,  30.0,    0, "SMAJ3.3"),
    ("R2",    "Resistor_SMD:R_0805_2012Metric",           64.0,  33.0,    0, "100R"),
    ("R3",    "Resistor_SMD:R_0402_1005Metric",           58.0,  33.0,    0, "100R"),
    ("C3",    "Capacitor_SMD:C_0402_1005Metric",          60.0,  36.0,    0, "1uF"),
    ("C4",    "Capacitor_SMD:C_0805_2012Metric",          64.0,  36.0,    0, "10uF"),
    ("C_SH1", "Capacitor_SMD:C_0402_1005Metric",          64.0,  30.0,    0, "10nF"),

    # 4-20mA ch2 circuit — alongside ch1
    ("D10",   "Diode_SMD:D_SMA",                          58.0,  38.0,    0, "SMAJ3.3"),
    ("R4",    "Resistor_SMD:R_0805_2012Metric",           64.0,  41.0,    0, "100R"),
    ("R5",    "Resistor_SMD:R_0402_1005Metric",           58.0,  41.0,    0, "100R"),
    ("C5",    "Capacitor_SMD:C_0402_1005Metric",          60.0,  44.0,    0, "1uF"),
    ("C6",    "Capacitor_SMD:C_0805_2012Metric",          64.0,  44.0,    0, "10uF"),
    ("C_SH2", "Capacitor_SMD:C_0402_1005Metric",          64.0,  38.0,    0, "10nF"),

    # ESD protection — dual PRTR5V, one per channel + DS18B20
    ("D1",    "Package_TO_SOT_SMD:SOT-363_SC-70-6",       57.0,  27.0,    0, "PRTR5V"),
    ("D12",   "Package_TO_SOT_SMD:SOT-363_SC-70-6",       57.0,  36.0,    0, "PRTR5V"),

    # DS18B20 pullup + bypass
    ("C7",    "Capacitor_SMD:C_0402_1005Metric",          57.0,  44.0,    0, "100nF"),
    ("R6",    "Resistor_SMD:R_0402_1005Metric",           57.0,  47.0,    0, "4k7"),

    # DS18B20 1-Wire series protection resistor (DNF by default)
    ("R32",   "Resistor_SMD:R_0402_1005Metric",           57.0,  50.0,    0, "33R"),

    # -------------------------------------------------------------------------
    # Zone 4 — Connectors strip (right edge, X=68..78, rot=180 → wires exit right)
    # Phoenix PT-1,5/3 body: ~10.5 mm wide, ~8 mm deep
    # Stacked vertically: J4 Y=6, J5 Y=18, J6 Y=30, J7 Y=42
    # J12 (2-pos, ~7 mm wide): top-right corner
    # -------------------------------------------------------------------------
    ("J12",   "TerminalBlock_Phoenix:TerminalBlock_Phoenix_PT-1,5-2-3.5-H_1x02_P3.50mm_Horizontal",
                                                          73.0,   6.0,  180, "Solar"),
    # Solar TVS at J12 terminal
    ("D14",   "Diode_SMD:D_SMA",                          65.0,   6.0,    0, "SMAJ28CA"),
    # 4-20mA channel 1
    ("J4",    "TerminalBlock_Phoenix:TerminalBlock_Phoenix_PT-1,5-3-3.5-H_1x03_P3.50mm_Horizontal",
                                                          73.0,  18.0,  180, "4-20mA_1"),
    # 4-20mA channel 2
    ("J5",    "TerminalBlock_Phoenix:TerminalBlock_Phoenix_PT-1,5-3-3.5-H_1x03_P3.50mm_Horizontal",
                                                          73.0,  30.0,  180, "4-20mA_2"),
    # DS18B20 sensor
    ("J6",    "TerminalBlock_Phoenix:TerminalBlock_Phoenix_PT-1,5-3-3.5-H_1x03_P3.50mm_Horizontal",
                                                          73.0,  42.0,  180, "DS18B20"),
    # Spare sensor
    ("J7",    "TerminalBlock_Phoenix:TerminalBlock_Phoenix_PT-1,5-3-3.5-H_1x03_P3.50mm_Horizontal",
                                                          73.0,  50.0,  180, "Spare"),

    # -------------------------------------------------------------------------
    # Zone 5 — Support / Interfaces (bottom center, X=32..66, Y=38..53)
    # Outside J3 courtyard (X=34.24-45.76, Y=40.53-55) — place VLOOP west of it
    # -------------------------------------------------------------------------
    # VLOOP boost cluster — MT3608B (U8) SOT-23-6 + hot-loop: SW→L1→C20/C22
    # Place at X=33..48, Y=38..52, west of J3 courtyard
    ("U8",    "Package_TO_SOT_SMD:SOT-23-6",             33.0,  42.0,    0, "MT3608B"),
    ("L1",    "Inductor_SMD:L_Vishay_IFSC-1515AH_4x4x1.8mm",
                                                          33.0,  47.0,    0, "4.7uH"),
    # Bootstrap cap on BST pin (pin 6) — within 1 mm of U8
    ("C_BST", "Capacitor_SMD:C_0402_1005Metric",         36.0,  39.0,    0, "100nF"),
    # VOUT output caps (high-ripple; keep short to L1 output)
    ("C20",   "Capacitor_SMD:C_1206_3216Metric",         33.0,  52.0,    0, "22uF 25V"),
    ("C22",   "Capacitor_SMD:C_0805_2012Metric",         38.0,  52.0,    0, "10uF 25V"),
    # Input bypass to U8 VIN — within 2 mm
    ("C19",   "Capacitor_SMD:C_0805_2012Metric",         38.0,  47.0,    0, "10uF"),
    # VLOOP TVS (at VOUT terminal, before J4/J5 VLOOP pin)
    ("D11",   "Diode_SMD:D_SMA",                         38.0,  42.0,    0, "SMAJ13"),
    # Feedback divider (R23 high-side, R24 low-side)
    ("R23",   "Resistor_SMD:R_0402_1005Metric",          33.0,  38.0,    0, "1.91M"),
    ("R24",   "Resistor_SMD:R_0402_1005Metric",          38.0,  38.0,    0, "100k"),
    # Bypass cap on TVS (D8 area) — absorbs inductive transients
    ("C21",   "Capacitor_SMD:C_0402_1005Metric",         43.0,  39.0,    0, "100nF"),

    # Programming header — accessible top of bottom strip
    ("J10",   "Connector_PinHeader_1.27mm:PinHeader_1x06_P1.27mm_Vertical",
                                                          30.0,  47.0,    0, "PROG"),

    # Solder jumpers
    ("SJ1",   "Jumper:SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm",
                                                          48.0,  44.0,    0, "VBOOST"),
    ("SJ2",   "Jumper:SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm",
                                                          48.0,  48.0,    0, "VLOOP"),
    ("SJ3",   "Jumper:SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm",
                                                          48.0,  52.0,    0, "LED_DIS"),
    ("SJ4",   "Jumper:SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm",
                                                          53.0,  44.0,    0, "UART_TX"),
    ("SJ5",   "Jumper:SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm",
                                                          53.0,  48.0,    0, "UART_RX"),

    # Test points — scattered along bottom strip Y=50..53, X=2..55
    # (avoid J3 courtyard X=34.24-45.76, and J7 at Y=50)
    ("TP1",   "TestPoint:TestPoint_Pad_1.0x1.0mm",        3.0,  52.0,    0, "VBAT"),
    ("TP2",   "TestPoint:TestPoint_Pad_1.0x1.0mm",        7.0,  52.0,    0, "VLOOP"),
    ("TP3",   "TestPoint:TestPoint_Pad_1.0x1.0mm",       11.0,  52.0,    0, "+3V3"),
    ("TP4",   "TestPoint:TestPoint_Pad_1.0x1.0mm",       15.0,  52.0,    0, "GND"),
    ("TP5",   "TestPoint:TestPoint_Pad_1.0x1.0mm",       19.0,  52.0,    0, "LOOP1"),
    ("TP6",   "TestPoint:TestPoint_Pad_1.0x1.0mm",       23.0,  52.0,    0, "LOOP2"),
    ("TP7",   "TestPoint:TestPoint_Pad_1.0x1.0mm",       27.0,  52.0,    0, "1WIRE"),
    ("TP8",   "TestPoint:TestPoint_Pad_1.0x1.0mm",       31.0,  52.0,    0, "SDA"),
    ("TP9",   "TestPoint:TestPoint_Pad_1.0x1.0mm",       47.0,  52.0,    0, "SCL"),
    ("TP10",  "TestPoint:TestPoint_Pad_1.0x1.0mm",       51.0,  52.0,    0, "VSOLAR"),
    ("TP11",  "TestPoint:TestPoint_Pad_1.0x1.0mm",       55.0,  52.0,    0, "VBAT_RAW"),
    ("TP12",  "TestPoint:TestPoint_Pad_1.0x1.0mm",       59.0,  52.0,    0, "ADS_DRDY"),
    ("TP14",  "TestPoint:TestPoint_Pad_1.0x1.0mm",       63.0,  52.0,    0, "CHRG_SOL"),
    ("TP15",  "TestPoint:TestPoint_Pad_1.0x1.0mm",       67.0,  52.0,    0, "CHRG_USB"),

    # -------------------------------------------------------------------------
    # LOCKED — J3, R9, R10 (do not move)
    # -------------------------------------------------------------------------
    ("J3",    "Connector_Coaxial:SMA_Amphenol_132289_EdgeMount",
                                                          40.0,  55.0,  270, "132289"),
    ("R9",    "Resistor_SMD:R_0402_1005Metric",           44.0,  43.5,    0, "4k7"),  # shifted north to clear J3 courtyard
    ("R10",   "Resistor_SMD:R_0402_1005Metric",           53.0,  45.0,    0, "4k7"),
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
    (property "Reference" "{ref}" (at 0 -1.5 0) (layer "F.SilkS")
      (uuid "{uid()}")
      (effects (font (size 0.8 0.8) (thickness 0.12)))
    )
    (property "Value" "{value}" (at 0 1.5 0) (layer "F.Fab")
      (uuid "{uid()}")
      (effects (font (size 0.8 0.8) (thickness 0.12)))
    )
  )"""


def pcb_mounting_hole(x: float, y: float) -> str:
    """Generate a mounting hole footprint (M3, 3.2mm drill)."""
    return f"""
  (footprint "MountingHole:MountingHole_3.2mm_M3" (layer "F.Cu") (at {x:.3f} {y:.3f} 0)
    (uuid "{uid()}")
    (property "Reference" "MH" (at 0 -3 0) (layer "F.SilkS")
      (uuid "{uid()}")
      (effects (font (size 0.8 0.8) (thickness 0.12)))
    )
    (property "Value" "MountingHole_3.2mm_M3" (at 0 3 0) (layer "F.Fab")
      (uuid "{uid()}")
      (effects (font (size 0.8 0.8) (thickness 0.12)))
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
    ox, oy = PCB_X_OFFSET, PCB_Y_OFFSET
    lines = []
    corners = [
        ((ox, oy),       (ox + w, oy)),
        ((ox + w, oy),   (ox + w, oy + h)),
        ((ox + w, oy + h), (ox, oy + h)),
        ((ox, oy + h),   (ox, oy)),
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
    ox, oy = PCB_X_OFFSET, PCB_Y_OFFSET
    # F.Cu zone (GND, solid fill, no thermal relief on zone connection)
    zone_fcu = f"""
  (zone (net 1) (net_name "GND") (layer "F.Cu") (uuid "{uid()}")
    (name "GND_THERMAL_U7")
    (hatch edge 0.508)
    (connect_pads thru_hole_only (clearance 0.2))
    (min_thickness 0.25)
    (fill yes (thermal_gap 0.3) (thermal_bridge_width 0.3))
    (polygon
      (pts (xy {55.0+ox} {5.0+oy}) (xy {65.0+ox} {5.0+oy}) (xy {65.0+ox} {15.0+oy}) (xy {55.0+ox} {15.0+oy}))
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
      (pts (xy {55.0+ox} {5.0+oy}) (xy {65.0+ox} {5.0+oy}) (xy {65.0+ox} {15.0+oy}) (xy {55.0+ox} {15.0+oy}))
    )
  )"""

    # Four thermal vias connecting F.Cu to B.Cu through U7 body area
    # Placed at 2mm spacing inside the 10x10 zone centred on (60,10)
    # Pattern: (58,8), (62,8), (58,12), (62,12)
    via_positions = [(58.0+ox, 8.0+oy), (62.0+ox, 8.0+oy), (58.0+ox, 12.0+oy), (62.0+ox, 12.0+oy)]
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
  (gr_text "GND_THERMAL_U7" (at {60+ox} {16.5+oy} 0) (layer "F.SilkS")
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
    ox, oy = PCB_X_OFFSET, PCB_Y_OFFSET
    # Perimeter coordinates (rectangular ring, clockwise, corners at each corner
    # plus intermediate points every ~2.5 mm)

    # Keep ring inside board boundary (board right edge = 80 mm; leave 1mm margin)
    x0, y0 = 68.0 + ox, 7.0 + oy
    x1, y1 = 79.0 + ox, 25.0 + oy

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
  (gr_text "SW_ISLAND_U8" (at {74+ox} {26.5+oy} 0) (layer "F.SilkS")
    (uuid "{uid()}")
    (effects (font (size 0.6 0.6) (thickness 0.1)))
  )"""

    return vias_str + silk_label


def make_pcb() -> str:
    """Build the complete welld.kicad_pcb s-expression string."""

    net_decls = pcb_net_declarations()

    # Board outline
    outline = pcb_board_outline()

    ox, oy = PCB_X_OFFSET, PCB_Y_OFFSET

    # Mounting holes
    mholes = ""
    for x, y in MOUNTING_HOLES:
        mholes += pcb_mounting_hole(x + ox, y + oy)

    # Component footprints
    footprints = ""
    for ref, fp, x, y, rot, value in PCB_COMPONENTS:
        footprints += pcb_footprint(ref, fp, x + ox, y + oy, rot, value)

    # Thermal copper pours and via stitching
    thermal_u7 = pcb_thermal_zone_u7()
    u8_viastitch = pcb_u8_gnd_viastitch()

    # Board title graphic text
    title_text = f"""
  (gr_text "WellD  ESP32-C6 Well Monitor" (at {40 + ox} {53.5 + oy} 0) (layer "F.SilkS")
    (uuid "{uid()}")
    (effects (font (size 0.8 0.8) (thickness 0.12)))
  )"""

    pcb = f"""(kicad_pcb (version 20260206) (generator "pcbnew") (generator_version "10.0")

  (general
    (thickness 1.6)
    (legacy_teardrops no)
  )

  (paper "User" 210 148)

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


def make_fp_lib_table() -> str:
    """Project-level fp-lib-table."""
    libs = [
        ("WellD", "KiCad", "${KIPRJMOD}/WellD.pretty", "WellD custom footprints"),
    ]
    entries = "\n".join(
        f'\t(lib (name "{n}") (type "{t}") (uri "{u}") (options "") (descr "{d}"))'
        for n, t, u, d in libs
    )
    return f"(fp_lib_table\n\t(version 7)\n{entries}\n)\n"


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

    print("\n[1/4] welld.kicad_pro")
    write("welld.kicad_pro", make_pro())

    print("\n[2/4] Hierarchical schematics")
    # Main sheet
    write("welld.kicad_sch", make_sch())
    sch_path = os.path.join(HERE, "welld.kicad_sch")
    result = subprocess.run(
        ["kicad-cli", "sch", "upgrade", "--force", sch_path],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print("  main sheet normalised")
    else:
        print(f"  WARNING: kicad-cli upgrade failed: {result.stderr.strip()}")
    
    # Sub-sheets
    for sheet_name in ["power", "mcu", "sensors", "interfaces"]:
        sheet_uuid = uid()
        fname = f"{sheet_name}.kicad_sch"
        write(fname, make_subsheet_sch(sheet_name, sheet_uuid))
        spath = os.path.join(HERE, fname)
        subprocess.run(
            ["kicad-cli", "sch", "upgrade", "--force", spath],
            capture_output=True, text=True
        )
        print(f"  {fname} generated")

    print("\n[3/4] welld.kicad_pcb")
    write("welld.kicad_pcb", make_pcb())

    print("\n[4/4] Symbol library")
    write("welld.kicad_sym", make_sym_lib())
    sym_path = os.path.join(HERE, "welld.kicad_sym")
    subprocess.run(["kicad-cli", "sym", "upgrade", "--force", sym_path],
                   capture_output=True)

    print("[+] sym-lib-table  (project library paths)")
    write("sym-lib-table", make_sym_lib_table())

    print("[+] fp-lib-table  (project footprint libraries)")
    write("fp-lib-table", make_fp_lib_table())

    print("\nDone.  Files written to:", HERE)


if __name__ == "__main__":
    main()
