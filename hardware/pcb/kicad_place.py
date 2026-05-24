"""
Place all PCB components at their designed coordinates.

Usage — KiCad scripting console (Tools > Scripting Console):
    exec(open("/path/to/hardware/pcb/kicad_place.py").read())

Or with auto-path resolution (board file must be saved first):
    import pcbnew, os
    exec(open(os.path.join(os.path.dirname(pcbnew.GetBoard().GetFileName()), "kicad_place.py")).read())

Run AFTER pressing F8 (Update PCB from Schematic) to snap all footprints
to the positions defined in generate_kicad.py's PCB_COMPONENTS list.
generate_kicad.py is imported read-only (main() is guarded by __name__).
"""

import sys
import os
import pcbnew

board = pcbnew.GetBoard()

# Resolve generate_kicad.py relative to the board file
_pcb_dir = os.path.dirname(os.path.abspath(board.GetFileName()))
if _pcb_dir not in sys.path:
    sys.path.insert(0, _pcb_dir)

from generate_kicad import PCB_COMPONENTS, PCB_X_OFFSET, PCB_Y_OFFSET


def _set_orientation(fp, deg):
    """Set footprint orientation, compatible with KiCad 8+ (EDA_ANGLE) and older."""
    try:
        fp.SetOrientation(pcbnew.EDA_ANGLE(deg, pcbnew.DEGREES_T))
    except AttributeError:
        # KiCad < 8 used 0.1-degree integer units
        fp.SetOrientation(int(deg * 10))


def place_all():
    # ref → (pcb_abs_x_mm, pcb_abs_y_mm, rot_deg)
    targets = {
        ref: (bx + PCB_X_OFFSET, by + PCB_Y_OFFSET, rot)
        for ref, _fp, bx, by, rot, _val in PCB_COMPONENTS
    }

    placed, missing = [], []
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref not in targets:
            missing.append(ref)
            continue
        ax, ay, rot = targets[ref]
        fp.SetPosition(pcbnew.VECTOR2I_MM(ax, ay))
        _set_orientation(fp, rot)
        placed.append(ref)

    pcbnew.Refresh()
    print(f"[kicad_place] placed {len(placed)}: {sorted(placed)}")
    if missing:
        not_in_script = sorted(set(missing))
        print(f"[kicad_place] not in PCB_COMPONENTS (position unchanged): {not_in_script}")


place_all()
