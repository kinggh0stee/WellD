# WellD Enclosure

Parametric two-part 3-D printed enclosure for the WellD well-level monitor PCB (80 × 55 mm, ESP32-C6-MINI-1U).

Target IP rating: **IP54** (dust-protected, splash-resistant) when cable glands are fitted and the TPU gasket is compressed between the lid and base rim.

---

## Files

| File | Purpose |
|---|---|
| `welld_case.scad` | Full parametric OpenSCAD source — edit this to customise |
| `welld_gasket.stl` | Pre-exported TPU 95A lid-sealing gasket (1.5 mm uncompressed) |

---

## Software requirements

- **OpenSCAD** 2021.01 or later (2023.x recommended for `rounded_box` preview performance)
  - <https://openscad.org/downloads.html>
- Any slicer (PrusaSlicer, Bambu Studio, Cura, OrcaSlicer…)

---

## Printing the parts

### Recommended material

| Part | Material | Notes |
|---|---|---|
| Base + Lid | **PETG** | First choice — UV/chemical resistant, low moisture absorption |
| Base + Lid | **ASA** | Best UV resistance for direct sunlight |
| Gasket | **TPU 95A** | Flexible, UV-resistant, low compression-set |

ABS is acceptable for base/lid but warps; PLA is not recommended outdoors.

### Slicer settings

#### Base and lid (PETG/ASA)

| Setting | Recommended value |
|---|---|
| Layer height | 0.2 mm |
| Perimeters / walls | 4 |
| Top/bottom solid layers | 5 |
| Infill | 30 % gyroid |
| Support | None required for either part |
| Brim | 5 mm on the base (large flat print) |

The base prints flat (open face up). The three bottom-wall gland holes are horizontal cylinders through a vertical wall, which bridge cleanly at 0.2 mm layers.

The lid prints **upside-down** (label face down to the bed).

#### Gasket (TPU 95A)

| Setting | Recommended value |
|---|---|
| Layer height | 0.2 mm |
| Perimeters / walls | 3 |
| Infill | 0 % (solid perimeters only) |
| Support | None |
| Cooling | Minimal (TPU sticks better warm) |

Print the gasket flat on the bed — it is a simple flat ring, 1.5 mm thick.

---

## Exporting STLs from OpenSCAD

1. Open `welld_case.scad` in OpenSCAD.
2. To export the **base**:
   - Set `SHOW_BASE = true;` and all others `false;` near the top.
   - Press **F6** (full render).
   - File → Export → **Export as STL** → save as `welld_base.stl`.
3. To export the **lid**:
   - Set `SHOW_LID = true;`, others `false`.
   - F6 → Export as `welld_lid.stl`.
4. To export the **gasket**:
   - Set `SHOW_GASKET = true;`, others `false`.
   - F6 → Export as `welld_gasket.stl`.
5. To export the **drill template** (concrete mounting):
   - Set `SHOW_DRILL_TEMPLATE = true;`, others `false`.
   - F6 → Export as `welld_drill_template.stl`.

Alternatively, run from the command line:

```bash
openscad -D 'SHOW_BASE=true;SHOW_LID=false;'   -o welld_base.stl         welld_case.scad
openscad -D 'SHOW_BASE=false;SHOW_LID=true;'   -o welld_lid.stl           welld_case.scad
openscad -D 'SHOW_BASE=false;SHOW_LID=false;SHOW_GASKET=true;' \
                                                -o welld_gasket.stl         welld_case.scad
openscad -D 'SHOW_BASE=false;SHOW_LID=false;SHOW_DRILL_TEMPLATE=true;' \
                                                -o welld_drill_template.stl welld_case.scad
```

---

## Assembly

### Hardware required per unit

| Qty | Part |
|---|---|
| 4 | M3 × 8 mm button-head screws (lid attachment) |
| 4 | M3 heat-set threaded inserts, OD ≈ 4.5 mm (press into corner boss bores) |
| 4 | M3 × 6 mm machine screws or M3 brass PCB standoff inserts (PCB mounting) |
| 3 | M16 cable glands (bottom wall — sensor/power cables) |
| 1 | M12 cable gland (left wall — programming/debug cable) |
| 1 | M16 cable gland (right wall — LiPo battery pigtail, standard variant only) |
| 1 | M16 cable gland (back wall — solar panel cable) |
| 1 | TPU 95A gasket (printed from `welld_gasket.stl`) |
| 1 | SMA female bulkhead connector, IP67, e.g. Amphenol RF 132289 (back wall) |
| 1 | U.FL to SMA female pigtail, ~100 mm, RG178, e.g. Taoglas CAB.100.07.0100B |

**Additional for concrete underside mounting (`concrete_mount = true`):**

| Qty | Part |
|---|---|
| 4 | M6 × 50 mm stainless anchor bolts (e.g. Hilti HUS3-H 6×50 or Rawlplug R-HPT6) |
| 4 | M6 stainless hex nuts (tightened from inside the well against wing counterbore) |

### Step-by-step

1. **Heat-set inserts** — press four M3 heat-set inserts into the corner boss bores at the top of the base using a soldering iron at ~200 °C (PETG) or ~240 °C (ASA). Flush or 0.2 mm below the rim.

2. **PCB standoffs** — press M3 brass threaded inserts into the four standoff bores (3.2 mm bore, 3 mm tall) or run an M3 tap through them. Alternatively use self-tapping M3 × 6 screws directly into the PETG bore.

3. **Cable glands** — thread M16 glands into the three bottom-wall holes and the right/back-wall holes. Thread the M12 gland into the left-wall programming hole. Tighten finger-tight; route cables before fully tightening.

4. **USB-C** — the left-wall slot is open (no gland). For a better IP rating, fit a short rubber grommet or add a thin bead of silicone around the USB-C receptacle flange once the PCB is installed.

5. **PCB installation** — lower the PCB onto the four standoffs, connectors toward the bottom wall, USB-C toward the left wall. Fasten with M3 × 6 screws.

6. **Gasket placement** — lay the TPU gasket flat onto the base top rim. No adhesive needed — the lid's weight and clamping load hold it in place. For concrete-mount lids (no inner lip), the gasket is the only seal path.

7. **Lid screws** — insert four M3 × 8 button-head screws through the counterbored holes in the lid and thread into the heat-set inserts in the corner bosses. Torque lightly (~0.5 N·m) — PETG boss walls will crack if over-torqued. The gasket compresses from 1.5 mm to ~1.0 mm (33 %) at this torque.

---

## Concrete underside mounting

When `concrete_mount = true` the lid grows four corner wings, each with an M6 anchor-bolt clearance hole and nut counterbore (8 mm thick wing, 6 mm counterbore leaving 2 mm face material).

**Orientation:** the lid is installed **face-down** against the concrete well cover. The wings point downward into the well. Anchor bolts pass up through the concrete and through the wings; M6 nuts are tightened from inside the well.

**No inner lip:** the inner lip is suppressed in concrete-mount mode — a lip pointing upward would press against the concrete ceiling. The TPU gasket seats directly on the base rim and is clamped by the flat lid face.

**Anchor bolt pattern (centre-to-centre):**
- X span: 85 + 22 = 107 mm (lid width + wing extent)
- Y span: 60 + 22 = 82 mm (lid depth + wing extent)

Use the drill template (`SHOW_DRILL_TEMPLATE = true`) to print a 1:1 paper/card guide. Minimum 30 mm embedment in sound concrete; apply sealant around each anchor entry point.

---

## Enclosure dimensions

| Dimension | Value |
|---|---|
| External width (X, long axis) | 85 mm |
| External depth (Y, short axis) | 60 mm |
| External height (base + lid) | ~41 mm (wall + floor\_h + pcb\_t + top\_clear + lid\_t) |
| PCB to floor (standoff height) | 3 mm |
| Internal clearance above PCB | 10 mm |
| Wall thickness | 2.5 mm |
| Lid thickness | 3 mm |
| Gasket thickness (uncompressed) | 1.5 mm |
| Gasket width (rim seating surface) | 2.5 mm |

All values are driven by the parameters at the top of `welld_case.scad`.

---

## Customising the design

The parameters section at the top of `welld_case.scad` is the only place you should normally need to edit:

```openscad
pcb_w         = 80;    // PCB width (X), mm
pcb_d         = 55;    // PCB depth (Y), mm
wall          = 2.5;   // wall thickness, mm
top_clear     = 10;    // clearance above PCB top, mm
m16_hole      = 20.5;  // M16 cable gland hole diameter, mm
prog_gland_d  = 16.0;  // M12 programming gland hole diameter, mm
lip_clearance = 0.3;   // radial clearance between lid lip OD and base interior, mm
```

Common changes:

- **Different PCB size** — adjust `pcb_w` and `pcb_d`; update the `mh` mounting hole array to match.
- **More internal height** — increase `top_clear` (e.g. to 14 for tall through-hole components).
- **Thicker walls** — increase `wall` for more mechanical robustness (adds weight and print time).
- **Fewer/more bottom cable glands** — change the loop `for (i = [0:2])` (3 glands) to your count; maximum 3× M16 in 85 mm without overlap. For 4 glands switch to M12 (16 mm) holes and set `m16_hole = 16.0` in the gland loop only.
- **Remove programming header gland** — set `prog_gland = false;`.
- **RF zone position** — adjust `rf_zone_x` and `rf_zone_y` if you move the ESP32 module.
- **Disable concrete mount** — set `concrete_mount = false;` to get a plain flat lid with inner sealing lip.
- **2S 18650 battery variant** — set `USE_2S_BATTERY = true;` (see electrical warnings in the SCAD file).

---

## Wall cutout reference

| Wall | Cutouts |
|---|---|
| Bottom (Y=0, sensor connectors) | 3× M16 cable glands (20.5 mm Ø), evenly spaced at ~26.7 mm centres |
| Left (X=0, USB-C side) | 1× USB-C slot (10 × 5 mm) + 1× M12 gland (16 mm Ø, programming cable) |
| Right (X=ext\_w, battery side) | 1× M16 cable gland (LiPo/battery cable) |
| Back (Y=ext\_d, opposite sensors) | 1× M16 cable gland (solar cable) + 1× SMA bulkhead hole (6.5 mm Ø) |
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

The tabs are 5 mm thick (Y) and 8 mm tall (Z), positioned within the shell height — no overhang past the base footprint.
