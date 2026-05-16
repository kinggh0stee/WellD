#!/usr/bin/env python3
"""
generate_kicad.py
-----------------
Generates KiCad 7 project files for WellD well-level monitor.

Outputs (all in the same directory as this script):
  welld.kicad_pro  — project JSON
  welld.kicad_sch  — schematic (KiCad 7 s-expression)
  welld.kicad_pcb  — PCB layout (KiCad 7 s-expression)

Run:
  python3 generate_kicad.py
"""

import json
import os
import uuid

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

HERE = os.path.dirname(os.path.abspath(__file__))

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

# Component data: (ref, description, lib_id, x, y, rotation, value)
# Schematic coordinates are in mm on KiCad A2 sheet (594×420 mm)
# We place functional blocks as described in the spec.

COMPONENTS = [
    # ref,   value,            lib_id,                      x,     y
    # ----- Block A: Solar input -----
    ("J12",  "SolarPanel",     "Connector:Conn_01x02_Pin",  20,    30),
    ("D6",   "MBRS140",        "Device:D_Schottky",         50,    30),
    ("C17",  "10uF",           "Device:C",                  80,    30),
    ("R20",  "36k",            "Device:R",                  50,    50),
    ("R21",  "10k",            "Device:R",                  50,    65),
    ("U7",   "CN3791",         "welld:CN3791",               100,   45),
    ("C18",  "10uF",           "Device:C",                  130,   45),
    ("R19",  "2k",             "Device:R",                  100,   65),
    ("R22",  "1k DNF",         "Device:R",                  130,   65),

    # ----- Block B: USB input -----
    ("J2",   "USB-C",          "welld:USB_C_Power",         20,   130),
    ("R15",  "5.1k",           "Device:R",                  20,   155),
    ("R16",  "5.1k",           "Device:R",                  35,   155),
    ("F1",   "PTC 1A",         "Device:Polyfuse",           60,   130),
    ("C16",  "4.7uF",          "Device:C",                  45,   140),
    ("U5",   "USBLC6-2SC6",    "welld:USBLC6_2SC6",         90,   130),
    ("U2",   "TP4056",         "welld:TP4056",               150,  130),
    ("R1",   "2.0k",           "Device:R",                  130,  155),
    ("C1",   "10uF",           "Device:C",                  135,  130),
    ("C2",   "10uF",           "Device:C",                  165,  130),
    ("D2",   "LED DNF",        "Device:LED",                155,  155),
    ("D3",   "LED DNF",        "Device:LED",                170,  155),
    ("R17",  "1k DNF",         "Device:R",                  155,  165),
    ("R18",  "1k DNF",         "Device:R",                  170,  165),

    # ----- Block C: Battery / Protection -----
    ("J1",   "LiPo",           "Connector:Conn_01x02_Pin",  220,   80),
    ("D5",   "AO3407",         "welld:AO3407",               250,   80),
    ("U3",   "DW01A",          "welld:DW01A",                280,   70),
    ("U4",   "FS8205A",        "welld:FS8205A",              280,   95),

    # ----- Block D: LDO -----
    ("U1",   "TPS7A0533",      "welld:TPS7A0533",            340,   80),
    ("C9",   "100nF",          "Device:C",                  370,   65),
    ("C10",  "1uF",            "Device:C",                  385,   65),
    ("C11",  "100nF",          "Device:C",                  370,   95),
    ("C12",  "1uF",            "Device:C",                  385,   95),

    # ----- Block E: ESP32-C6 -----
    ("U6",   "ESP32-C6-MINI",  "welld:ESP32_C6_MINI_1U",    430,   80),
    ("R11",  "10k",            "Device:R",                  490,   60),
    ("R12",  "10k",            "Device:R",                  490,   70),
    ("R13",  "10k",            "Device:R",                  490,   80),
    ("SW1",  "RESET",          "Device:SW_Push",             410,   50),
    ("SW2",  "BOOT",           "Device:SW_Push",             410,   65),
    ("C13",  "100nF",          "Device:C",                  410,   75),
    ("C14a", "100nF",          "Device:C",                  400,   95),
    ("C14b", "100nF",          "Device:C",                  410,   95),
    ("C14c", "100nF",          "Device:C",                  420,   95),
    ("C14d", "100nF",          "Device:C",                  430,   95),
    ("C15",  "10uF",           "Device:C",                  445,   95),
    ("R7",   "100k",           "Device:R",                  490,   90),
    ("R8",   "100k",           "Device:R",                  490,  100),
    ("C8",   "100nF",          "Device:C",                  510,   95),

    # ----- Block F: Sensor interfaces -----
    ("J4",   "4-20mA_CH1",     "Connector:Conn_01x03_Pin",  420,  200),
    ("J5",   "4-20mA_CH2",     "Connector:Conn_01x03_Pin",  450,  200),
    ("J6",   "DS18B20",        "Connector:Conn_01x03_Pin",  480,  200),
    ("J7",   "Spare",          "Connector:Conn_01x03_Pin",  510,  200),
    ("D1",   "PRTR5V0U2X",     "welld:PRTR5V0U2X",           420,  230),
    ("R2",   "100R 0.1%",      "Device:R",                  440,  215),
    ("R3",   "100R",           "Device:R",                  460,  215),
    ("C3",   "100nF",          "Device:C",                  460,  225),
    ("C4",   "10uF",           "Device:C",                  470,  225),
    ("R4",   "100R 0.1%",      "Device:R",                  480,  215),
    ("R5",   "100R",           "Device:R",                  500,  215),
    ("C5",   "100nF",          "Device:C",                  500,  225),
    ("C6",   "10uF",           "Device:C",                  510,  225),
    ("R6",   "4.7k",           "Device:R",                  490,  250),
    ("C7",   "100nF",          "Device:C",                  510,  250),

    # ----- Block G: Expansion headers -----
    ("J8",   "I2C_4pin",       "Connector:Conn_01x04_Pin",  530,   80),
    ("J9",   "GPIO_8pin",      "Connector:Conn_01x08_Pin",  530,  110),
    ("J10",  "PROG_6pin",      "Connector:Conn_01x06_Pin",  530,  160),
    ("J3",   "U.FL_Antenna",   "welld:U_FL_Antenna",         530,  190),
    ("R9",   "4.7k",           "Device:R",                  555,   75),
    ("R10",  "4.7k",           "Device:R",                  565,   75),

    # ----- Block H: LED indicators -----
    ("D4",   "Status_LED",     "Device:LED",                330,  200),
    ("R14",  "1k",             "Device:R",                  330,  215),
]


def sch_global_label(net: str, x: float, y: float, shape: str = "passive") -> str:
    """Emit a global_label s-expression."""
    return f"""
  (global_label "{net}" (shape {shape}) (at {x:.2f} {y:.2f} 0) (fields_autoplaced)
    (effects (font (size 1.27 1.27)) (justify left))
    (uuid "{uid()}")
    (property "Intersheets" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
  )"""


def sch_power_symbol(net: str, x: float, y: float) -> str:
    """Emit a power symbol (power port / PWR_FLAG)."""
    return f"""
  (power "{net}" (at {x:.2f} {y:.2f} 0) (fields_autoplaced)
    (uuid "{uid()}")
    (property "Reference" "#PWR" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
    (property "Value" "{net}" (at 0 -3.81 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
    (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
    (pin "1" (at 0 0 270))
  )"""


def sch_component(ref: str, value: str, lib_id: str, x: float, y: float) -> str:
    """Emit a symbol instance s-expression for the schematic."""
    footprint = ""
    return f"""
  (symbol (lib_id "{lib_id}") (at {x:.2f} {y:.2f} 0) (unit 1)
    (in_bom yes) (on_board yes) (dnp no) (fields_autoplaced)
    (uuid "{uid()}")
    (property "Reference" "{ref}" (at {x:.2f} {y - 3.81:.2f} 0)
      (effects (font (size 1.27 1.27))))
    (property "Value" "{value}" (at {x:.2f} {y + 3.81:.2f} 0)
      (effects (font (size 1.27 1.27))))
    (property "Footprint" "{footprint}" (at 0 0 0)
      (effects (font (size 1.27 1.27)) (hide yes)))
    (property "Datasheet" "~" (at 0 0 0)
      (effects (font (size 1.27 1.27)) (hide yes)))
  )"""


def make_sch_lib_symbols() -> str:
    """
    Define all custom IC symbols inline.
    Each symbol follows KiCad 7 s-expression format.
    Pin format: (pin <type> <direction> (at x y angle) (length l) (name "n" ...) (number "n" ...))
    """

    def pin(ptype: str, pdir: str, x: float, y: float, angle: int, name: str, num: str, length: float = 2.54) -> str:
        return (
            f'      (pin {ptype} {pdir} (at {x:.2f} {y:.2f} {angle}) (length {length:.2f})\n'
            f'        (name "{name}" (effects (font (size 1.27 1.27))))\n'
            f'        (number "{num}" (effects (font (size 1.27 1.27))))\n'
            f'      )'
        )

    # ---- CN3791 solar MPPT charger (SOIC-8) --------------------------------
    cn3791 = f"""
    (symbol "CN3791" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 10.16 0) (effects (font (size 1.27 1.27))))
      (property "Value" "CN3791" (at 0 -10.16 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (symbol "CN3791_0_1"
        (rectangle (start -3.81 -8.89) (end 3.81 8.89)
          (stroke (width 0) (type default)) (fill (type background)))
      )
      (symbol "CN3791_1_1"
{pin("passive",       "right",  -6.35, 6.35,  0,   "VBAT",  "1")}
{pin("power_in",      "right",  -6.35, 3.81,  0,   "GND",   "2")}
{pin("input",         "left",    6.35, 3.81,  180, "MPPT",  "3")}
{pin("power_in",      "left",    6.35, 6.35,  180, "VIN",   "4")}
{pin("passive",       "left",    6.35, -3.81, 180, "PROG",  "5")}
{pin("open_collector","right",  -6.35, -3.81, 0,   "/CHRG", "6")}
{pin("open_collector","right",  -6.35, -6.35, 0,   "/DONE", "7")}
{pin("no_connect",    "left",    6.35, -6.35, 180, "VIN2",  "8")}
      )
    )"""

    # ---- TP4056 USB charger (SOIC-8) ----------------------------------------
    tp4056 = f"""
    (symbol "TP4056" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 10.16 0) (effects (font (size 1.27 1.27))))
      (property "Value" "TP4056" (at 0 -10.16 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (symbol "TP4056_0_1"
        (rectangle (start -3.81 -8.89) (end 3.81 8.89)
          (stroke (width 0) (type default)) (fill (type background)))
      )
      (symbol "TP4056_1_1"
{pin("passive",  "left",    6.35,  6.35,  180, "PROG",  "1")}
{pin("power_in", "left",    6.35,  3.81,  180, "GND",   "2")}
{pin("power_in", "left",    6.35,  1.27,  180, "VCC",   "3")}
{pin("output",   "right",  -6.35,  3.81,    0, "STDBY", "4")}
{pin("output",   "right",  -6.35,  1.27,    0, "CHRG",  "5")}
{pin("passive",  "right",  -6.35, -1.27,    0, "BAT",   "6")}
{pin("input",    "left",    6.35, -1.27,  180, "TE",    "7")}
{pin("input",    "left",    6.35, -3.81,  180, "CE",    "8")}
      )
    )"""

    # ---- TPS7A0533 LDO (SC70-5) ---------------------------------------------
    tps = f"""
    (symbol "TPS7A0533" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 7.62 0) (effects (font (size 1.27 1.27))))
      (property "Value" "TPS7A0533" (at 0 -7.62 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "Package_TO_SOT_SMD:SC-70-5" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (symbol "TPS7A0533_0_1"
        (rectangle (start -3.81 -6.35) (end 3.81 6.35)
          (stroke (width 0) (type default)) (fill (type background)))
      )
      (symbol "TPS7A0533_1_1"
{pin("power_in",  "left",  6.35,  3.81, 180, "IN",  "1")}
{pin("power_in",  "left",  6.35,  1.27, 180, "GND", "2")}
{pin("input",     "left",  6.35, -1.27, 180, "EN",  "3")}
{pin("no_connect","left",  6.35, -3.81, 180, "NC",  "4")}
{pin("power_out", "right",-6.35,  1.27,   0, "OUT", "5")}
      )
    )"""

    # ---- DW01A LiPo protection (SOT-23-6) -----------------------------------
    dw01a = f"""
    (symbol "DW01A" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 7.62 0) (effects (font (size 1.27 1.27))))
      (property "Value" "DW01A" (at 0 -7.62 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "Package_TO_SOT_SMD:SOT-23-6" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (symbol "DW01A_0_1"
        (rectangle (start -3.81 -6.35) (end 3.81 6.35)
          (stroke (width 0) (type default)) (fill (type background)))
      )
      (symbol "DW01A_1_1"
{pin("power_in", "left",   6.35,  3.81, 180, "GND", "1")}
{pin("input",    "left",   6.35,  1.27, 180, "CS",  "2")}
{pin("output",   "right", -6.35,  3.81,   0, "DO",  "3")}
{pin("output",   "right", -6.35,  1.27,   0, "CO",  "4")}
{pin("power_in", "left",   6.35, -1.27, 180, "VCC", "5")}
{pin("passive",  "right", -6.35, -1.27,   0, "VDD", "6")}
      )
    )"""

    # ---- FS8205A dual P-ch MOSFET (SOT-23-6) --------------------------------
    fs8205a = f"""
    (symbol "FS8205A" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 7.62 0) (effects (font (size 1.27 1.27))))
      (property "Value" "FS8205A" (at 0 -7.62 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "Package_TO_SOT_SMD:SOT-23-6" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (symbol "FS8205A_0_1"
        (rectangle (start -3.81 -6.35) (end 3.81 6.35)
          (stroke (width 0) (type default)) (fill (type background)))
      )
      (symbol "FS8205A_1_1"
{pin("passive", "left",   6.35,  3.81, 180, "S1",   "1")}
{pin("input",   "left",   6.35,  1.27, 180, "G1",   "2")}
{pin("passive", "left",   6.35, -1.27, 180, "S2",   "3")}
{pin("passive", "right", -6.35,  1.27,   0, "D1D2", "4")}
{pin("input",   "right", -6.35, -1.27,   0, "G2",   "5")}
{pin("passive", "right", -6.35, -3.81,   0, "S2b",  "6")}
      )
    )"""

    # ---- USBLC6-2SC6 USB ESD (SOT-23-6) ------------------------------------
    usblc6 = f"""
    (symbol "USBLC6_2SC6" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 7.62 0) (effects (font (size 1.27 1.27))))
      (property "Value" "USBLC6-2SC6" (at 0 -7.62 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "Package_TO_SOT_SMD:SOT-23-6" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
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
    )"""

    # ---- PRTR5V0U2X dual TVS (SOT-363 / SC-70-6) ---------------------------
    prtr = f"""
    (symbol "PRTR5V0U2X" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
      (property "Reference" "D" (at 0 7.62 0) (effects (font (size 1.27 1.27))))
      (property "Value" "PRTR5V0U2X" (at 0 -7.62 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "Package_TO_SOT_SMD:SOT-363_SC-70-6" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
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
    )"""

    # ---- AO3407 P-channel MOSFET (SOT-23) -----------------------------------
    ao3407 = f"""
    (symbol "AO3407" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
      (property "Reference" "D" (at 0 5.08 0) (effects (font (size 1.27 1.27))))
      (property "Value" "AO3407" (at 0 -5.08 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "Package_TO_SOT_SMD:SOT-23" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (symbol "AO3407_0_1"
        (rectangle (start -2.54 -3.81) (end 2.54 3.81)
          (stroke (width 0) (type default)) (fill (type background)))
      )
      (symbol "AO3407_1_1"
{pin("input",   "left",  5.08,  1.27, 180, "G", "1")}
{pin("passive", "left",  5.08, -1.27, 180, "S", "2")}
{pin("passive", "right",-5.08,  0,      0, "D", "3")}
      )
    )"""

    # ---- USB-C power connector (stub) --------------------------------------
    usbcpwr = f"""
    (symbol "USB_C_Power" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
      (property "Reference" "J" (at 0 7.62 0) (effects (font (size 1.27 1.27))))
      (property "Value" "USB_C_Power" (at 0 -7.62 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "welld:USB_C_9x3.2mm" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
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
    )"""

    # ---- U.FL antenna stub -------------------------------------------------
    ufl = f"""
    (symbol "U_FL_Antenna" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
      (property "Reference" "J" (at 0 3.81 0) (effects (font (size 1.27 1.27))))
      (property "Value" "U.FL" (at 0 -3.81 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (symbol "U_FL_Antenna_0_1"
        (rectangle (start -2.54 -2.54) (end 2.54 2.54)
          (stroke (width 0) (type default)) (fill (type background)))
      )
      (symbol "U_FL_Antenna_1_1"
{pin("passive",  "right", -5.08, 1.27,   0, "RF",  "1")}
{pin("power_in", "left",   5.08, -1.27, 180, "GND", "2")}
      )
    )"""

    # ---- ESP32-C6-MINI-1U (large custom) ------------------------------------
    # Left side: power + strapping; Right side: GPIO
    esp_pins_left = [
        pin("power_in",  "left",  -12.7,  10.16, 180, "3V3",    "2"),
        pin("power_in",  "left",  -12.7,   7.62, 180, "3V3_b",  "3"),
        pin("power_in",  "left",  -12.7,  -7.62, 180, "GND",    "1"),
        pin("power_in",  "left",  -12.7,  -10.16,180, "GND_b",  "40"),
        pin("input",     "left",  -12.7,   5.08, 180, "EN",     "3"),
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
        pin("passive", "right",  12.7, -20.32, 0, "GPIO15", "30"),
        pin("passive", "right",  12.7, -22.86, 0, "GPIO16", "31"),
        pin("passive", "right",  12.7, -25.4,  0, "GPIO17", "32"),
        pin("passive", "right",  12.7, -27.94, 0, "GPIO20", "33"),
        pin("passive", "right",  12.7, -30.48, 0, "GPIO21", "34"),
    ]
    esp_all_pins = "\n".join(esp_pins_left + esp_pins_right)

    esp32 = f"""
    (symbol "ESP32_C6_MINI_1U" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 35.56 0) (effects (font (size 1.27 1.27))))
      (property "Value" "ESP32-C6-MINI-1U" (at 0 -35.56 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "welld:ESP32_C6_MINI_1U" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (symbol "ESP32_C6_MINI_1U_0_1"
        (rectangle (start -10.16 -33.02) (end 10.16 12.7)
          (stroke (width 0) (type default)) (fill (type background)))
      )
      (symbol "ESP32_C6_MINI_1U_1_1"
{esp_all_pins}
      )
    )"""

    return "\n".join([cn3791, tp4056, tps, dw01a, fs8205a, usblc6, prtr, ao3407, usbcpwr, ufl, esp32])


def make_sch() -> str:
    """Build the complete welld.kicad_sch s-expression string."""

    lib_symbols = make_sch_lib_symbols()

    # Global labels for all key nets
    nets = [
        ("VSOLAR_IN",    30,   15, "passive"),
        ("VSOLAR",       70,   15, "passive"),
        ("VUSB_IN",      30,  120, "passive"),
        ("VUSB",         80,  120, "passive"),
        ("VBAT",        210,   70, "passive"),
        ("+3V3",        330,   70, "passive"),
        ("GND",          30,  280, "passive"),
        ("ADC_CH0",     415,  195, "input"),
        ("ADC_CH1",     485,  195, "input"),
        ("ADC_CH2",     470,  195, "input"),
        ("1WIRE",       490,  195, "input"),
        ("I2C_SDA",     545,   70, "passive"),
        ("I2C_SCL",     555,   70, "passive"),
        ("GPIO13_LED",  320,  190, "passive"),
        ("UART_TX",     545,  100, "passive"),
        ("UART_RX",     545,  110, "passive"),
        ("EN",          405,   45, "input"),
        ("BOOT",        405,   60, "input"),
        ("MPPT_REF",     50,   60, "passive"),
        ("/CHRG_USB",   180,  120, "passive"),
        ("/DONE_USB",   180,  130, "passive"),
        ("/CHRG_SOLAR", 120,   45, "passive"),
        ("/DONE_SOLAR", 120,   55, "passive"),
    ]

    global_labels_str = ""
    for net, x, y, shape in nets:
        global_labels_str += sch_global_label(net, x, y, shape)

    # Power symbols (PWR_FLAG at rail entry points)
    power_flags = [
        ("+3V3",    335,  65),
        ("GND",      35, 285),
        ("VBAT",    215,  65),
    ]
    power_str = ""
    for net, x, y in power_flags:
        power_str += sch_power_symbol(net, x, y)

    # All component symbol instances
    comps_str = ""
    for ref, value, lib_id, x, y in COMPONENTS:
        comps_str += sch_component(ref, value, lib_id, x, y)

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
        wire(20, 30, 45, 30),
        wire(55, 30, 70, 30),
        # USB path: J2 -> F1
        wire(20, 130, 55, 130),
        wire(65, 130, 90, 130),
        # TP4056 output -> VBAT
        wire(170, 128, 210, 128),
        # LDO input <- VBAT
        wire(320, 80, 335, 80),
        # LDO output -> +3V3
        wire(360, 80, 375, 80),
        # ESP32 VCC
        wire(420, 60, 420, 80),
        # Batt divider
        wire(490, 90, 490, 100),
        # MPPT divider
        wire(50, 50, 50, 65),
        # Battery protection chain
        wire(260, 80, 275, 80),
        wire(295, 80, 335, 80),
        # LED path
        wire(330, 200, 330, 215),
    ]

    wires_str = "".join(wires)

    # No-connect markers on un-used pins (representative set)
    def noconn(x, y):
        return f"""
  (no_connect (at {x:.2f} {y:.2f}) (uuid "{uid()}"))"""

    noconns_str = noconn(535, 190)  # J3 shield

    sch = f"""(kicad_sch (version 20230121) (generator "welld_generate_kicad")

  (lib_symbols
{lib_symbols}
  )

  (paper "A2")

  (title_block
    (title "WellD Well-Level Monitor")
    (date "2026-05-16")
    (rev "1.0")
    (company "WellD Project")
    (comment 1 "ESP32-C6-MINI-1U + TP4056 + CN3791 + TPS7A0533")
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
# Footprints use standard KiCad 7 library paths.
PCB_COMPONENTS = [
    # ICs
    ("U1",   "Package_TO_SOT_SMD:SC-70-5",                               56,   34,   0, "TPS7A0533"),
    ("U2",   "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",                     10,   41,   0, "TP4056"),
    ("U3",   "Package_TO_SOT_SMD:SOT-23-6",                              68,   21,   0, "DW01A"),
    ("U4",   "Package_TO_SOT_SMD:SOT-23-6",                              68,   14,   0, "FS8205A"),
    ("U5",   "Package_TO_SOT_SMD:SOT-23-6",                              10,   48,   0, "USBLC6"),
    ("U6",   "welld:ESP32_C6_MINI_1U",                                   31,   26,   0, "ESP32-C6"),
    ("U7",   "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",                     60,   10,   0, "CN3791"),

    # Diodes
    ("D1",   "Package_TO_SOT_SMD:SOT-363_SC-70-6",                      15,   14,   0, "PRTR5V0U2X"),
    ("D2",   "LED_SMD:LED_0603_1608Metric",                              12,   47,   0, "LED_CHRG"),
    ("D3",   "LED_SMD:LED_0603_1608Metric",                              14,   47,   0, "LED_STBY"),
    ("D4",   "LED_SMD:LED_0603_1608Metric",                              50,   51,   0, "LED_STATUS"),
    ("D5",   "Package_TO_SOT_SMD:SOT-23",                                65,   42,   0, "AO3407"),
    ("D6",   "Diode_SMD:D_SOD-123",                                      56,    7,   0, "MBRS140"),

    # Fuse
    ("F1",   "Fuse:Fuse_1206_3216Metric",                                 6,   44,   0, "PTC_1A"),

    # Connectors
    ("J1",   "Connector_JST:JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal",  74,   40,   0, "LiPo"),
    ("J2",   "welld:USB_C_9x3.2mm",                                       2,   47,   0, "USB-C"),
    ("J3",   "Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical",     40,   53,   0, "U.FL"),
    ("J4",   "Connector_Phoenix_MC:PhoenixContact_MC_1,5_3-G-3,5_1x03_P3.50mm_Horizontal", 12, 2, 0, "4-20mA_1"),
    ("J5",   "Connector_Phoenix_MC:PhoenixContact_MC_1,5_3-G-3,5_1x03_P3.50mm_Horizontal", 23, 2, 0, "4-20mA_2"),
    ("J6",   "Connector_Phoenix_MC:PhoenixContact_MC_1,5_3-G-3,5_1x03_P3.50mm_Horizontal", 34, 2, 0, "DS18B20"),
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
    ("C3",   "Capacitor_SMD:C_0402_1005Metric",  20,   14,  0, "100nF"),
    ("C4",   "Capacitor_SMD:C_0805_2012Metric",  22,   14,  0, "10uF"),
    ("C5",   "Capacitor_SMD:C_0402_1005Metric",  29,   14,  0, "100nF"),
    ("C6",   "Capacitor_SMD:C_0805_2012Metric",  31,   14,  0, "10uF"),
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
]


def pcb_net_declarations() -> str:
    lines = []
    for i, net in enumerate(NETS, start=1):
        lines.append(f'  (net {i} "{net}")')
    return "\n".join(lines)


def pcb_footprint(ref: str, fp: str, x: float, y: float, rot: float, value: str) -> str:
    """
    Generate a minimal KiCad 7 footprint placement s-expression.
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

    # Board title graphic text
    title_text = f"""
  (gr_text "WellD v1.0  ESP32-C6 Well Monitor" (at 40 53.5 0) (layer "F.SilkS")
    (uuid "{uid()}")
    (effects (font (size 1.0 1.0) (thickness 0.15)))
  )"""

    pcb = f"""(kicad_pcb (version 20221018) (generator "welld_generate_kicad")

  (general
    (thickness 1.6)
    (legacy_teardrops no)
  )

  (paper "A3")

  (title_block
    (title "WellD Well-Level Monitor PCB")
    (date "2026-05-16")
    (rev "1.0")
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

)
"""
    return pcb


# ===========================================================================
# Entry point
# ===========================================================================

def main():
    print("Generating KiCad 7 project files …")

    print("\n[1/3] welld.kicad_pro")
    write("welld.kicad_pro", make_pro())

    print("\n[2/3] welld.kicad_sch")
    write("welld.kicad_sch", make_sch())

    print("\n[3/3] welld.kicad_pcb")
    write("welld.kicad_pcb", make_pcb())

    print("\nDone.  Files written to:", HERE)


if __name__ == "__main__":
    main()
