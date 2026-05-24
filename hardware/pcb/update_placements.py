#!/usr/bin/env python3
"""
update_placements.py — applies the new PCB_COMPONENTS placement to welld.kicad_pcb
by finding each footprint block by its reference property and rewriting the (at X Y rot) line.

PCB absolute = board-relative + (PCB_X_OFFSET=65, PCB_Y_OFFSET=46.5)

Run from hardware/pcb/:
    python3 update_placements.py
"""

import re

PCB_X_OFFSET = 65.0
PCB_Y_OFFSET = 46.5

# New board-relative positions: (ref, x, y, rot)
# Locked: J1(5.6,33.5,180), J3(40.0,55.0,270), R9(44.0,43.5,0), R10(53.0,45.0,0)
# MH1-4 are not in this table (handled separately as mounting holes with no ref change needed).
# J8 and J9 are DNF — park them far off-board (they remain in the PCB file but moved out of the way).
NEW_POSITIONS = {
    # Zone 1 — Solar charging
    "U7":    ( 9.0,   8.0,   0.0),
    "C17":   (16.0,   5.0,   0.0),
    "D6":    (22.0,   5.0,   0.0),
    "D8":    (28.0,   5.0,   0.0),
    "C18":   (16.0,  13.0,   0.0),
    "R19":   (22.0,  10.0,   0.0),
    "R20":   (22.0,  14.0,   0.0),
    "R21":   (27.0,  10.0,   0.0),
    "R33":   (27.0,  14.0,   0.0),
    "R34":   (27.0,  18.0,   0.0),
    "D7":    ( 9.0,  18.0,   0.0),
    "R22":   (14.0,  18.0,   0.0),
    # USB-C sub-group
    "J13":   ( 5.0,  25.0,   0.0),
    "R_CC1": (13.0,  23.0,   0.0),
    "R_CC2": (13.0,  26.0,   0.0),
    "U11":   (19.0,  24.0,   0.0),
    "F2":    (25.0,  24.0,   0.0),
    "C27":   (25.0,  28.0,   0.0),
    # TP5100 USB charger
    "U12":   (21.0,  43.0,   0.0),
    "C28":   (28.0,  40.0,   0.0),
    "C29":   (28.0,  44.0,   0.0),
    "R35":   (16.0,  40.0,   0.0),
    "R36":   (16.0,  44.0,   0.0),
    "R37":   (16.0,  48.0,   0.0),
    "R38":   (21.0,  48.0,   0.0),
    # Battery protection
    "D13":   ( 6.0,  40.0,   0.0),
    "D5":    ( 6.0,  45.0,   0.0),
    "R31":   ( 6.0,  49.0,   0.0),
    # 3.3V Buck converter
    "U1":    (10.0,  34.0,   0.0),
    "L2":    (17.0,  34.0,   0.0),
    "C9":    ( 7.0,  36.5,   0.0),
    "C10":   (10.0,  36.5,   0.0),
    "C11":   (20.0,  34.0,   0.0),
    "C12":   (20.0,  36.5,   0.0),
    "C_BUCK":(25.0,  35.0,   0.0),
    "R11":   (13.0,  36.5,   0.0),
    # LOCKED
    "J1":    ( 5.6,  33.5, 180.0),
    # Zone 2 — MCU
    "U6":    (50.0,  17.0,   0.0),
    "C14a":  (36.0,   7.0,   0.0),
    "C14b":  (39.0,   7.0,   0.0),
    "C14c":  (36.0,  10.0,   0.0),
    "C14d":  (39.0,  10.0,   0.0),
    "C15":   (42.0,   8.0,   0.0),
    "R12":   (36.0,  14.0,   0.0),
    "R13":   (39.0,  14.0,   0.0),
    "C13":   (42.0,  14.0,   0.0),
    "SW1":   (42.0,   4.0,   0.0),
    "SW2":   (48.0,   4.0,   0.0),
    "D4":    (62.0,  28.0,   0.0),
    "R14":   (58.0,  28.0,   0.0),
    # Zone 3 — Analog / Sensors
    "U9":    (62.0,  20.0,   0.0),
    "FB1":   (57.0,  17.0,   0.0),
    "C23":   (57.0,  20.0,   0.0),
    "C24":   (57.0,  23.0,   0.0),
    "R28":   (62.0,  25.0,   0.0),
    "Q2":    (57.0,   8.0,   0.0),
    "R7":    (62.0,   6.0,   0.0),
    "R8":    (62.0,   9.0,   0.0),
    "C8":    (57.0,  12.0,   0.0),
    "R26":   (62.0,  12.0,   0.0),
    "D9":    (58.0,  30.0,   0.0),
    "R2":    (64.0,  33.0,   0.0),
    "R3":    (58.0,  33.0,   0.0),
    "C3":    (60.0,  36.0,   0.0),
    "C4":    (64.0,  36.0,   0.0),
    "C_SH1": (64.0,  30.0,   0.0),
    "D10":   (58.0,  38.0,   0.0),
    "R4":    (64.0,  41.0,   0.0),
    "R5":    (58.0,  41.0,   0.0),
    "C5":    (60.0,  44.0,   0.0),
    "C6":    (64.0,  44.0,   0.0),
    "C_SH2": (64.0,  38.0,   0.0),
    "D1":    (57.0,  27.0,   0.0),
    "D12":   (57.0,  36.0,   0.0),
    "C7":    (57.0,  44.0,   0.0),
    "R6":    (57.0,  47.0,   0.0),
    "R32":   (57.0,  50.0,   0.0),
    # Zone 4 — Connectors (right edge)
    "J12":   (73.0,   6.0, 180.0),
    "D14":   (65.0,   6.0,   0.0),
    "J4":    (73.0,  18.0, 180.0),
    "J5":    (73.0,  30.0, 180.0),
    "J6":    (73.0,  42.0, 180.0),
    "J7":    (73.0,  50.0, 180.0),
    # Zone 5 — VLOOP boost + support
    "U8":    (33.0,  42.0,   0.0),
    "L1":    (33.0,  47.0,   0.0),
    "C_BST": (36.0,  39.0,   0.0),
    "C20":   (33.0,  52.0,   0.0),
    "C22":   (38.0,  52.0,   0.0),
    "C19":   (38.0,  47.0,   0.0),
    "D11":   (38.0,  42.0,   0.0),
    "R23":   (33.0,  38.0,   0.0),
    "R24":   (38.0,  38.0,   0.0),
    "C21":   (43.0,  39.0,   0.0),
    "J10":   (30.0,  47.0,   0.0),
    "SJ1":   (48.0,  44.0,   0.0),
    "SJ2":   (48.0,  48.0,   0.0),
    "SJ3":   (48.0,  52.0,   0.0),
    "SJ4":   (53.0,  44.0,   0.0),
    "SJ5":   (53.0,  48.0,   0.0),
    # Test points — bottom strip Y=52
    "TP1":   ( 3.0,  52.0,   0.0),
    "TP2":   ( 7.0,  52.0,   0.0),
    "TP3":   (11.0,  52.0,   0.0),
    "TP4":   (15.0,  52.0,   0.0),
    "TP5":   (19.0,  52.0,   0.0),
    "TP6":   (23.0,  52.0,   0.0),
    "TP7":   (27.0,  52.0,   0.0),
    "TP8":   (31.0,  52.0,   0.0),
    "TP9":   (47.0,  52.0,   0.0),
    "TP10":  (51.0,  52.0,   0.0),
    "TP11":  (55.0,  52.0,   0.0),
    "TP12":  (59.0,  52.0,   0.0),
    "TP14":  (63.0,  52.0,   0.0),
    "TP15":  (67.0,  52.0,   0.0),
    # LOCKED
    "J3":    (40.0,  55.0, 270.0),
    "R9":    (44.0,  43.5,   0.0),
    "R10":   (53.0,  45.0,   0.0),
    # DNF — park off-board at a safe position (200,200 board-relative = well outside)
    "J8":    (200.0, 200.0,  0.0),
    "J9":    (200.0, 210.0,  0.0),
}


def apply_placements(pcb_path: str) -> None:
    with open(pcb_path, "r") as f:
        content = f.read()

    # Split into lines for processing
    lines = content.split("\n")
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Detect start of a footprint block: line contains '(footprint' and '(at '
        fp_match = re.match(r'^(\s*\(footprint\s+"[^"]*"\s+\(layer\s+"[^"]*"\)\s+)\(at\s+([\d.\-]+)\s+([\d.\-]+)(?:\s+([\d.\-]+))?\)', line)
        if fp_match:
            prefix = fp_match.group(1)
            old_x = float(fp_match.group(2))
            old_y = float(fp_match.group(3))
            old_rot_str = fp_match.group(4)
            old_rot = float(old_rot_str) if old_rot_str else 0.0
            rest_of_line = line[fp_match.end():]

            # Peek ahead to find the Reference property to identify the component
            ref = None
            j = i + 1
            # Look up to 5 lines ahead for the Reference property
            while j < min(i + 8, len(lines)):
                ref_match = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', lines[j])
                if ref_match:
                    ref = ref_match.group(1)
                    break
                j += 1

            if ref and ref in NEW_POSITIONS:
                bx, by, brot = NEW_POSITIONS[ref]
                new_x = bx + PCB_X_OFFSET
                new_y = by + PCB_Y_OFFSET
                new_rot = brot
                new_line = f"{prefix}(at {new_x:.3f} {new_y:.3f} {new_rot:.1f}){rest_of_line}"
                result.append(new_line)
                print(f"  {ref:8s}: ({old_x:.3f}, {old_y:.3f}, {old_rot:.1f}) -> ({new_x:.3f}, {new_y:.3f}, {new_rot:.1f})")
            else:
                # Keep unchanged (mounting holes, or ref not in our map)
                if ref:
                    print(f"  {ref:8s}: UNCHANGED at ({old_x:.3f}, {old_y:.3f})")
                result.append(line)
        else:
            result.append(line)
        i += 1

    new_content = "\n".join(result)
    with open(pcb_path, "w") as f:
        f.write(new_content)
    print(f"\nWrote updated {pcb_path}")


if __name__ == "__main__":
    import os
    pcb = os.path.join(os.path.dirname(__file__), "welld.kicad_pcb")
    print(f"Updating placements in {pcb} ...")
    apply_placements(pcb)
