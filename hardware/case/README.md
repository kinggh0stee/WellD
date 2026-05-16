# WellD Enclosure

Parametric two-part 3-D printed enclosure for the WellD well-level monitor PCB (80 × 55 mm, ESP32-C6-MINI-1U).

Target IP rating: **IP54** (dust-protected, splash-resistant) when cable glands are fitted and the lid lip is sealed with silicone.

---

## Files

| File | Purpose |
|---|---|
| `welld_case.scad` | Full parametric OpenSCAD source — edit this to customise |

---

## Software requirements

- **OpenSCAD** 2021.01 or later (2023.x recommended for `rounded_box` preview performance)
  - <https://openscad.org/downloads.html>
- Any slicer (PrusaSlicer, Bambu Studio, Cura, OrcaSlicer…)

---

## Printing the parts

### Recommended material

| Material | Notes |
|---|---|
| **PETG** | First choice — UV/chemical resistant, low moisture absorption, good layer adhesion |
| **ASA** | Best UV resistance if the enclosure will be in direct sunlight |
| ABS | Acceptable, but warps and needs an enclosure |
| PLA | Not recommended outdoors — creep and UV degradation |

### Slicer settings

| Setting | Recommended value |
|---|---|
| Layer height | 0.2 mm |
| Perimeters / walls | 4 |
| Top/bottom solid layers | 5 |
| Infill | 30 % gyroid |
| Support | None required for either part |
| Brim | 5 mm on the base (large flat print) |

The base prints flat (open face up). No supports are needed — the cable gland holes are horizontal cylinders through vertical walls, which bridge cleanly at 0.2 mm layers.

The lid prints **upside-down** (label face down to the bed). The inner lip overhangs slightly, but at 2 mm depth and 1.5 mm wall they print without support on any reasonably calibrated printer.

---

## Exporting STLs from OpenSCAD

1. Open `welld_case.scad` in OpenSCAD.
2. To export the **base**:
   - Set `SHOW_BASE = true;` and `SHOW_LID = false;` near the top of the file.
   - Press **F6** (full render).
   - File → Export → **Export as STL** → save as `welld_base.stl`.
3. To export the **lid**:
   - Set `SHOW_BASE = false;` and `SHOW_LID = true;`.
   - Press **F6**.
   - Export as `welld_lid.stl`.

Alternatively, run from the command line:

```bash
openscad -D 'SHOW_BASE=true;SHOW_LID=false;'  -o welld_base.stl welld_case.scad
openscad -D 'SHOW_BASE=false;SHOW_LID=true;'  -o welld_lid.stl  welld_case.scad
```

---

## Assembly

### Hardware required per unit

| Qty | Part |
|---|---|
| 4 | M3 × 8 mm button-head screws (lid attachment) |
| 4 | M3 heat-set threaded inserts, OD ≈ 4.5 mm (press into corner boss bores) |
| 4 | M3 × 6 mm machine screws or M3 brass PCB standoff inserts (PCB mounting) |
| 8 | M16 cable glands (5 × bottom wall, 1 × left, 1 × right, 1 × back) |
| 1 | Tube of silicone sealant (lid lip seal) |

### Step-by-step

1. **Heat-set inserts** — press four M3 heat-set inserts into the corner boss bores at the top of the base using a soldering iron at ~200 °C (PETG) or ~240 °C (ASA). Flush or 0.2 mm below the rim.

2. **PCB standoffs** — press M3 brass threaded inserts into the four standoff bores (3.2 mm bore, 3 mm tall) or run an M3 tap through them. Alternatively use self-tapping M3 × 6 screws directly into the PETG bore.

3. **Cable glands** — thread M16 cable glands into all eight wall holes. Tighten finger-tight plus a quarter turn with a wrench. Route cables before tightening fully.

4. **USB-C** — the left-wall slot is open (no gland). For a better IP rating, fit a short rubber grommet or add a thin bead of silicone around the USB-C receptacle flange once the PCB is installed.

5. **PCB installation** — lower the PCB onto the four standoffs, connectors toward the bottom wall, USB-C toward the left wall. Fasten with M3 × 6 screws.

6. **Lid sealing** — run a thin bead of silicone around the inner lip of the lid before pressing it down onto the base. Wipe away squeeze-out. Let cure for 1–2 hours before fully torquing the four M3 lid screws.

7. **Lid screws** — insert four M3 × 8 button-head screws through the counterbored holes in the lid and thread into the heat-set inserts in the corner bosses. Torque lightly (~0.5 N·m) — PETG boss walls will crack if over-torqued.

---

## Enclosure dimensions

| Dimension | Value |
|---|---|
| External width (X, long axis) | 85 mm |
| External depth (Y, short axis) | 60 mm |
| External height (base + lid) | ~41 mm (wall + floor\_h + pcb\_t + top\_clear + lid\_t + wall) |
| PCB to floor (standoff height) | 3 mm |
| Internal clearance above PCB | 10 mm |
| Wall thickness | 2.5 mm |
| Lid thickness | 3 mm |

All values are driven by the parameters at the top of `welld_case.scad`. Edit them to suit a revised PCB or different wall thickness preference.

---

## Customising the design

The parameters section at the top of `welld_case.scad` is the only place you should normally need to edit:

```openscad
pcb_w       = 80;    // PCB width (X), mm
pcb_d       = 55;    // PCB depth (Y), mm
wall        = 2.5;   // wall thickness, mm
top_clear   = 10;    // clearance above PCB top, mm
m16_hole    = 20.5;  // M16 cable gland hole diameter, mm
```

Common changes:

- **Different PCB size** — adjust `pcb_w` and `pcb_d`; the mounting hole positions array `mh` at the top of the derived-dimensions block must also be updated.
- **More internal height** — increase `top_clear` (e.g. to 14 for tall through-hole components).
- **Thicker walls** — increase `wall` for more mechanical robustness (adds weight and print time).
- **Fewer cable glands** — the bottom-wall gland loop count (`for (i = [0:4])`) can be changed from 5 to the number you need.
- **Remove programming header gland** — set `prog_gland = false;`.
- **RF zone position** — adjust `rf_zone_x` and `rf_zone_y` if you move the ESP32 module.

---

## Wall cutout reference

| Wall | Cutouts |
|---|---|
| Bottom (Y=0, sensor connectors) | 5× M16 cable glands, evenly spaced |
| Left (X=0, USB-C side) | 1× USB-C slot (10 × 5 mm) + 1× M16 gland (programming cable) |
| Right (X=ext\_w, battery side) | 1× M16 cable gland (LiPo/battery cable) |
| Back (Y=ext\_d, opposite sensors) | 1× M16 cable gland (solar panel cable) |
| Top (lid) | RF-thinned zone (20 × 20 mm, 0.5 mm wall) over ESP32 antenna |

---

## Zigbee / RF note

The lid has a 20 × 20 mm zone thinned to 0.5 mm directly above the ESP32-C6-MINI-1U antenna. PETG at 0.5 mm has negligible impact on 2.4 GHz signal. Do not use metal-flake or carbon-filled filament in this zone. The zone position is controlled by `rf_zone_x` (default 5 mm from lid left edge, centred in Y) — verify it aligns with your module placement before printing.

---

## Mounting

Two external tabs are printed on the left (X=0) wall of the base, one near each end of the enclosure. Each tab has a 5 mm through-hole suitable for:

- An M5 screw into a wall or post
- A large cable tie for pipe/conduit mounting
- A 5 mm stainless snap-hook for hanging

The tabs are 5 mm thick (Y) and 12 mm tall (Z) and are integral to the base print — no separate hardware needed.
