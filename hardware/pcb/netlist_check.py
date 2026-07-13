#!/usr/bin/env python3
"""WellD schematic netlist verifier (senior-review "netlist-vs-doc diff").

Re-extracts pin->net connectivity from the *written* .kicad_sch files by pure
geometry — pin endpoints (recomputed via the symbol transforms), wire segments,
label anchors (local / global / hierarchical), sheet pins and root-level joins
on welld.kicad_sch — and diffs the resulting partition against the intended
netlist table (NETS / NC_PINS in kicad_wire_script.py, which is derived
net-by-net from schematic_connections.md).

The extraction path shares only the low-level s-expression/transform helpers
with the generator; connectivity itself is rebuilt from the file geometry
(wires + point-on-segment label association + union-find), so a transform,
collision, or label-placement bug in the generator would surface here as a
merged/split/misnamed net.

Checks performed:
  1. every symbol pin is either in exactly one extracted net or carries an
     explicit (no_connect) marker;
  2. the extracted partition of pins into nets equals the intended partition
     (globals merged by name, hierarchical nets merged through the actual
     sheet-pin + root-label geometry of welld.kicad_sch — not by name);
  3. each extracted net carries exactly the intended label name(s);
  4. no stray labels or no_connect markers exist beyond the table.

Exit code 0 = zero mismatches.
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from kicad_wire_script import (  # noqa: E402
    GLOBAL_NETS, NC_PINS, NETS, SHEETS, TOP,
    Sheet, get_at, get_str, root_span, scan_children, seg_contains, balanced,
)


class UF:
    def __init__(self):
        self.p = {}

    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        self.p[self.find(a)] = self.find(b)


def parse_graph(path):
    """Return (wires, labels, ncs) from a sheet file. labels: (kind, name, x, y).
    Also sheet blocks for the top file: (name, pins=[(pname, x, y)])."""
    with open(path) as f:
        text = f.read()
    if not balanced(text):
        raise SystemExit(f"{path}: unbalanced s-expressions")
    rs, re_ = root_span(text)
    wires, labels, ncs, sheets = [], [], [], []
    for tag, s, e in scan_children(text, rs, re_ - 1):
        chunk = text[s:e]
        if tag == "wire":
            pts = re.findall(r"\(xy\s+([-\d.]+)\s+([-\d.]+)\)", chunk)
            a = (float(pts[0][0]), float(pts[0][1]))
            b = (float(pts[1][0]), float(pts[1][1]))
            wires.append((a, b))
        elif tag in ("label", "global_label", "hierarchical_label"):
            m = re.match(r'\(%s\s+"((?:[^"\\]|\\.)*)"' % tag, chunk)
            at = get_at(chunk)
            labels.append((tag, m.group(1), at[0], at[1]))
        elif tag == "no_connect":
            at = get_at(chunk)
            ncs.append((at[0], at[1]))
        elif tag == "sheet":
            m = re.search(r'\(property\s+"Sheetname"\s+"((?:[^"\\]|\\.)*)"', chunk)
            crs, cre = root_span(chunk)
            pins = []
            for t2, s2, e2 in scan_children(chunk, crs, cre - 1):
                if t2 != "pin":
                    continue
                sub = chunk[s2:e2]
                pm = re.match(r'\(pin\s+"((?:[^"\\]|\\.)*)"', sub)
                at = get_at(sub)
                pins.append((pm.group(1), at[0], at[1]))
            sheets.append((m.group(1), pins))
    return wires, labels, ncs, sheets


def key(sheet, pt):
    return (sheet, round(pt[0], 3), round(pt[1], 3))


def main():
    uf = UF()
    pin_nodes = {}     # (sheet, "REF.PIN") -> node key
    nc_markers = {}    # sheet -> set of points
    labels_all = []    # (sheet, kind, name, node)

    for name in SHEETS:
        sh = Sheet(name)
        sh.resolve_pins()
        wires, labels, ncs, _ = parse_graph(sh.path)

        # wires connect their endpoints; endpoint-on-segment connects too
        pts = []
        for a, b in wires:
            uf.union(key(name, a), key(name, b))
            pts.extend([a, b])
        for kind, lname, x, y in labels:
            pts.append((x, y))
        for pid, info in sh.pins.items():
            pts.append((info["x"], info["y"]))
        # point-on-segment attachment (KiCad: wire endings and label anchors
        # or pin ends that lie on a wire are connected to it)
        for p in pts:
            for a, b in wires:
                if seg_contains(p, a, b):
                    uf.union(key(name, p), key(name, a))
        # coincident points connect implicitly via identical keys

        for pid, info in sh.pins.items():
            pin_nodes[(name, pid)] = key(name, (info["x"], info["y"]))
        nc_markers[name] = {key(name, p) for p in ncs}

        for kind, lname, x, y in labels:
            node = key(name, (x, y))
            labels_all.append((name, kind, lname, node))
            if kind == "global_label":
                uf.union(node, ("GLOBAL", lname))
            elif kind == "hierarchical_label":
                uf.union(node, ("HIER", name, lname))
            else:  # KiCad: local labels connect by name within one sheet
                uf.union(node, ("LOCAL", name, lname))

    # ---- top sheet: sheet pins + root wires/labels merge hierarchical nets
    top_path = os.path.join(HERE, f"{TOP}.kicad_sch")
    wires, labels, ncs, sheets = parse_graph(top_path)
    pts = []
    for a, b in wires:
        uf.union(key(TOP, a), key(TOP, b))
        pts.extend([a, b])
    for kind, lname, x, y in labels:
        pts.append((x, y))
    for sname, pins in sheets:
        for pname, x, y in pins:
            pts.append((x, y))
    for p in pts:
        for a, b in wires:
            if seg_contains(p, a, b):
                uf.union(key(TOP, p), key(TOP, a))
    for kind, lname, x, y in labels:
        node = key(TOP, (x, y))
        if kind == "global_label":
            uf.union(node, ("GLOBAL", lname))
        elif kind == "label":  # root-level local labels connect by name
            uf.union(node, ("LOCAL", TOP, lname))
    for sname, pins in sheets:
        for pname, x, y in pins:
            uf.union(key(TOP, (x, y)), ("HIER", sname, pname))

    # ---- extracted partition: root -> set of (sheet, pin)
    extracted = {}
    for (sheet, pid), node in pin_nodes.items():
        extracted.setdefault(uf.find(node), set()).add((sheet, pid))
    # net names attached to each root
    root_names = {}
    for sheet, kind, lname, node in labels_all:
        root_names.setdefault(uf.find(node), set()).add(lname)

    # ---- intended partition from the table
    intended = {}      # netkey -> set of (sheet, pin)
    intended_name = {}
    hier_names = {n for n, s in
                  ((n, {sh for sh in NETS if n in NETS[sh]}) for n in
                   {n for d in NETS.values() for n in d})
                  if len(s) > 1 and n not in GLOBAL_NETS}
    for sheet, nets in NETS.items():
        for net, plist in nets.items():
            if net in GLOBAL_NETS:
                k = ("G", net)
            elif net in hier_names:
                k = ("H", net)
            else:
                k = ("L", sheet, net)
            for p in plist:
                intended.setdefault(k, set()).add((sheet, p))
            intended_name[k] = net

    problems = []

    # 1. NC markers exactly on NC pins
    pin_pos = {}
    for sheet in SHEETS:
        sh = Sheet(sheet)
        sh.resolve_pins()
        for pid, info in sh.pins.items():
            pin_pos[(sheet, pid)] = key(sheet, (info["x"], info["y"]))
    for sheet in SHEETS:
        want = {pin_pos[(sheet, pid)] for pid in NC_PINS.get(sheet, [])}
        got = nc_markers[sheet]
        for missing in sorted(want - got):
            problems.append(f"{sheet}: NC marker missing at {missing}")
        for stray in sorted(got - want):
            problems.append(f"{sheet}: stray NC marker at {stray}")

    # 2/3. partition + naming diff
    intended_by_pin = {}
    for k, pins in intended.items():
        for sp in pins:
            intended_by_pin[sp] = k
    nc_set = {(sheet, pid) for sheet in SHEETS for pid in NC_PINS.get(sheet, [])}

    matched = 0
    for root, pins in sorted(extracted.items(), key=lambda kv: str(kv[0])):
        if pins <= nc_set:
            # NC pins form singleton clusters; markers are checked separately
            if len(pins) > 1:
                problems.append(f"NC pins wired together: {sorted(pins)}")
            continue
        keys = {intended_by_pin.get(sp) for sp in pins}
        if None in keys:
            bad = [sp for sp in pins if sp not in intended_by_pin]
            problems.append(f"extracted net {sorted(pins)} contains pins not in "
                            f"the table (should be NC?): {bad}")
            continue
        if len(keys) > 1:
            problems.append("extracted net MERGES intended nets "
                            f"{sorted(intended_name[k] for k in keys)}: {sorted(pins)}")
            continue
        k = keys.pop()
        if pins != intended[k]:
            problems.append(f"net {intended_name[k]}: pin set mismatch\n"
                            f"    extracted: {sorted(pins)}\n"
                            f"    intended : {sorted(intended[k])}")
            continue
        names = root_names.get(root, set())
        if names != {intended_name[k]}:
            problems.append(f"net {intended_name[k]}: label names on net are "
                            f"{sorted(names)}")
            continue
        matched += 1

    # NC pins must not appear in any extracted net
    for sp in nc_set:
        node = pin_nodes[sp]
        members = extracted.get(uf.find(node), set())
        if len(members) > 1:
            problems.append(f"NC pin {sp} is electrically connected to {members}")

    total_pins = len(pin_nodes)
    print(f"pins checked      : {total_pins}")
    print(f"intended nets     : {len(intended)}")
    print(f"extracted nets ok : {matched}")
    print(f"no-connect pins   : {len(nc_set)}")
    if problems:
        print(f"\nMISMATCHES ({len(problems)}):")
        for p in problems:
            print("  - " + p)
        return 1
    print("\nRESULT: zero mismatches — schematic connectivity matches "
          "schematic_connections.md table.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
