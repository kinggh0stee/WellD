#!/usr/bin/env python3
"""WellD footprint check: every symbol's pin numbers must match its footprint's pads.

"Update PCB from Schematic" connects nets to pads by *number*. A symbol pin with
no pad of the same number silently loses its net, and a pad with no pin stays
unconnected. This script catches both before the board is imported, plus any
footprint name that does not exist in the library.

For every placed symbol on the four sub-sheets it compares the pin numbers of
the embedded library symbol with the pad numbers of the footprint named in its
Footprint field:

  * WellD:*   -> hardware/pcb/WellD.pretty (project library, in the repo)
  * others    -> the KiCad 10 standard library: a local install given with
                 --kicad-footprints DIR (or $KICAD10_FOOTPRINT_DIR), otherwise
                 downloaded once from the kicad-footprints 10.0.0 tag into
                 ~/.cache/welld-kicad-footprints/

Unnamed pads (mounting/NPTH holes) are ignored. Pins of electrical type
no_connect may lack a pad. Exit code 0 = every symbol matches.

Run:  python3 hardware/pcb/footprint_check.py [--kicad-footprints DIR]
"""

import argparse
import os
import re
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SHEETS = ["power", "mcu", "sensors", "interfaces"]
KICAD_TAG = "10.0.0"
RAW = "https://gitlab.com/kicad/libraries/kicad-footprints/-/raw/{tag}/{lib}.pretty/{name}.kicad_mod"
CACHE = os.path.join(os.path.expanduser("~"), ".cache", "welld-kicad-footprints", KICAD_TAG)


def tokens(s):
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c in " \t\r\n":
            i += 1
        elif c in "()":
            yield c
            i += 1
        elif c == '"':
            j, buf = i + 1, []
            while s[j] != '"':
                if s[j] == "\\":
                    buf.append(s[j + 1])
                    j += 2
                else:
                    buf.append(s[j])
                    j += 1
            yield ("S", "".join(buf))
            i = j + 1
        else:
            j = i
            while j < n and s[j] not in " \t\r\n()":
                j += 1
            yield ("A", s[i:j])
            i = j


def parse(s):
    stack = [[]]
    for t in tokens(s):
        if t == "(":
            stack.append([])
        elif t == ")":
            x = stack.pop()
            stack[-1].append(x)
        else:
            stack[-1].append(t[1])
    return stack[0][0]


def kids(node, head):
    return [c for c in node if isinstance(c, list) and c and c[0] == head]


def prop(sym, name):
    for p in kids(sym, "property"):
        if p[1] == name:
            return p[2]
    return None


def lib_pins(tree):
    """lib_id -> {pin number: electrical type} for every embedded library symbol."""
    out = {}
    for sym in kids(kids(tree, "lib_symbols")[0], "symbol"):
        pins = {}
        for unit in kids(sym, "symbol"):
            for pin in kids(unit, "pin"):
                pins[kids(pin, "number")[0][1]] = pin[1]
        out[sym[1]] = pins
    return out


def footprint_file(fp, kicad_dir):
    lib, name = fp.split(":", 1)
    if lib == "WellD":
        return os.path.join(HERE, "WellD.pretty", name + ".kicad_mod")
    if kicad_dir:
        return os.path.join(kicad_dir, lib + ".pretty", name + ".kicad_mod")
    path = os.path.join(CACHE, lib + ".pretty", name + ".kicad_mod")
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        url = RAW.format(tag=KICAD_TAG, lib=urllib.request.quote(lib), name=urllib.request.quote(name, safe=",.-_"))
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                data = r.read()
        except Exception as e:  # 404 = not in the library
            return f"download failed ({e})"
        with open(path, "wb") as f:
            f.write(data)
    return path


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--kicad-footprints", default=os.environ.get("KICAD10_FOOTPRINT_DIR"),
                    help="local KiCad 10 footprint library directory (the folder holding *.pretty)")
    args = ap.parse_args()

    problems, checked = [], 0
    for sheet in SHEETS:
        with open(os.path.join(HERE, sheet + ".kicad_sch")) as f:
            tree = parse(f.read())
        libs = lib_pins(tree)
        for sym in kids(tree, "symbol"):
            lid = kids(sym, "lib_id")
            ref = prop(sym, "Reference")
            if not lid or ref.startswith("#"):
                continue
            fp = prop(sym, "Footprint")
            if not fp:
                problems.append(f"{ref}: no footprint assigned")
                continue
            path = footprint_file(fp, args.kicad_footprints)
            if not os.path.exists(path):
                problems.append(f"{ref}: footprint {fp} not found ({path})")
                continue
            with open(path) as f:
                pads = set(re.findall(r'\(pad\s+"([^"]*)"', f.read())) - {""}
            pins = libs[lid[0][1]]
            no_pad = sorted(p for p, et in pins.items() if p not in pads and et != "no_connect")
            no_pin = sorted(pads - set(pins))
            checked += 1
            if no_pad:
                problems.append(f"{ref} ({fp}): symbol pins without a pad: {no_pad}")
            if no_pin:
                problems.append(f"{ref} ({fp}): pads without a symbol pin: {no_pin}")

    print(f"symbols checked : {checked}")
    for p in problems:
        print("PROBLEM:", p)
    if problems:
        print(f"\nRESULT: {len(problems)} problem(s)")
        sys.exit(1)
    print("\nRESULT: every symbol's pins match its footprint's pads.")


if __name__ == "__main__":
    main()
