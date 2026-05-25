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
# Locked: J1(4,46,270), J3(50,55,270)
# MH1-4 are not in this table (handled separately).
# J8 and J9 are DNF — parked off-board.
NEW_POSITIONS = {
    # Zone 1 — Solar charging
    "U7":    (10.0,   8.0,   0.0),
    "C17":   (18.0,   6.0,   0.0),
    "D6":    (24.0,   6.0,   0.0),
    "D8":    (24.0,  10.0,   0.0),
    "C18":   (18.0,  12.0,   0.0),
    "R19":   (10.0,  14.0,   0.0),
    "R20":   (14.0,  14.0,   0.0),
    "R21":   (18.0,  14.0,   0.0),
    "R33":   (22.0,  14.0,   0.0),
    "R34":   (22.0,  18.0,   0.0),
    "D7":    ( 6.0,  10.0,   0.0),
    "R22":   ( 6.0,  14.0,   0.0),
    # USB-C sub-group
    "J13":   ( 4.0,  26.0,   0.0),
    "R50":   (14.0,  24.0,   0.0),
    "R51":   (14.0,  28.0,   0.0),
    "U11":   (20.0,  24.0,   0.0),
    "F2":    (26.0,  24.0,   0.0),
    "C27":   (26.0,  28.0,   0.0),
    # TP5100 USB charger
    "U12":   (20.0,  40.0,   0.0),
    "C28":   (28.0,  38.0,   0.0),
    "C29":   (28.0,  42.0,   0.0),
    "R35":   (14.0,  38.0,   0.0),
    "R36":   (14.0,  42.0,   0.0),
    "R37":   (14.0,  46.0,   0.0),
    "R38":   (20.0,  46.0,   0.0),
    # Battery protection
    "D13":   ( 8.0,  38.0,   0.0),
    "D5":    ( 8.0,  42.0,   0.0),
    "R31":   ( 8.0,  46.0,   0.0),
    # 3.3V Buck converter
    "U1":    (14.0,  30.0,   0.0),
    "L2":    (22.0,  30.0,   0.0),
    "C9":    (10.0,  32.0,   0.0),
    "C10":   (14.0,  32.0,   0.0),
    "C11":   (22.0,  32.0,   0.0),
    "C12":   (26.0,  32.0,   0.0),
    "C16":   (26.0,  28.0,   0.0),
    "R11":   (18.0,  32.0,   0.0),
    # LOCKED
    "J1":    ( 4.0,  46.0, 270.0),
    # Zone 2 — MCU
    "U6":    (48.0,  16.0,   0.0),
    "C30":   (38.0,   6.0,   0.0),
    "C31":   (42.0,   6.0,   0.0),
    "C32":   (38.0,  10.0,   0.0),
    "C33":   (42.0,  10.0,   0.0),
    "C15":   (46.0,   6.0,   0.0),
    "R12":   (38.0,  14.0,   0.0),
    "R13":   (42.0,  14.0,   0.0),
    "C13":   (46.0,  14.0,   0.0),
    "SW1":   (40.0,   4.0,   0.0),
    "SW2":   (48.0,   4.0,   0.0),
    "D4":    (58.0,  26.0,   0.0),
    "R14":   (54.0,  26.0,   0.0),
    # Zone 3 — Analog / Sensors
    "U9":    (76.0,  14.0,   0.0),
    "FB1":   (70.0,  10.0,   0.0),
    "C23":   (70.0,  14.0,   0.0),
    "C24":   (70.0,  18.0,   0.0),
    "R28":   (76.0,  20.0,   0.0),
    "Q2":    (70.0,   6.0,   0.0),
    "R7":    (76.0,   4.0,   0.0),
    "R8":    (76.0,   8.0,   0.0),
    "C8":    (70.0,  10.0,   0.0),
    "R26":   (76.0,  10.0,   0.0),
    "D9":    (72.0,  28.0,   0.0),
    "R2":    (78.0,  32.0,   0.0),
    "R3":    (72.0,  32.0,   0.0),
    "C3":    (74.0,  36.0,   0.0),
    "C4":    (78.0,  36.0,   0.0),
    "C34":   (78.0,  28.0,   0.0),
    "D10":   (86.0,  28.0,   0.0),
    "R4":    (92.0,  32.0,   0.0),
    "R5":    (86.0,  32.0,   0.0),
    "C5":    (88.0,  36.0,   0.0),
    "C6":    (92.0,  36.0,   0.0),
    "C35":   (92.0,  28.0,   0.0),
    "D1":    (68.0,  26.0,   0.0),
    "D12":   (82.0,  34.0,   0.0),
    "C7":    (82.0,  36.0,   0.0),
    "R6":    (82.0,  32.0,   0.0),
    "R32":   (88.0,  32.0,   0.0),
    # Zone 4 — Connectors (bottom edge)
    "J12":   (10.0,  46.0, 180.0),
    "D14":   ( 6.0,  46.0,   0.0),
    "J4":    (24.0,  46.0, 180.0),
    "J5":    (40.0,  46.0, 180.0),
    "J6":    (56.0,  46.0, 180.0),
    "J7":    (72.0,  46.0, 180.0),
    "J10":   (88.0,  46.0,   0.0),
    # Zone 5 — VLOOP boost + support
    "U8":    (34.0,  40.0,   0.0),
    "L1":    (34.0,  48.0,   0.0),
    "C25":   (38.0,  38.0,   0.0),
    "C20":   (34.0,  52.0,   0.0),
    "C22":   (40.0,  52.0,   0.0),
    "C19":   (40.0,  48.0,   0.0),
    "D11":   (40.0,  40.0,   0.0),
    "R23":   (34.0,  36.0,   0.0),
    "R24":   (40.0,  36.0,   0.0),
    "C21":   (46.0,  38.0,   0.0),
    "SJ1":   (58.0,  38.0,   0.0),
    "SJ2":   (62.0,  38.0,   0.0),
    "SJ3":   (66.0,  38.0,   0.0),
    "SJ4":   (58.0,  34.0,   0.0),
    "SJ5":   (62.0,  34.0,   0.0),
    "R9":    (54.0,  36.0,   0.0),
    "R10":   (54.0,  32.0,   0.0),
    # Test points — scattered
    "TP1":   (16.0,  26.0,   0.0),
    "TP2":   (30.0,  38.0,   0.0),
    "TP3":   (20.0,  26.0,   0.0),
    "TP4":   (24.0,  26.0,   0.0),
    "TP5":   (82.0,  32.0,   0.0),
    "TP6":   (96.0,  32.0,   0.0),
    "TP7":   (66.0,  50.0,   0.0),
    "TP8":   (54.0,  20.0,   0.0),
    "TP9":   (58.0,  20.0,   0.0),
    "TP10":  (16.0,  50.0,   0.0),
    "TP11":  ( 6.0,  50.0,   0.0),
    "TP12":  (56.0,  18.0,   0.0),
    "TP14":  ( 8.0,  20.0,   0.0),
    "TP15":  (24.0,  50.0,   0.0),
    # LOCKED
    "J3":    (50.0,  55.0, 270.0),
    # DNF — park off-board
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
