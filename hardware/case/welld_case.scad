// WellD Well-Level Monitor — Parametric Enclosure
// Target printer: FDM, PETG or ASA recommended (outdoor/IP67 use)
// ESP32-C6-MINI-1U based PCB, 80×55 mm
//
// Two-part design:
//   base()  — bottom shell with PCB standoffs, 2S1P battery bay, and wall cutouts
//   lid()   — flat plate with inner lip, screw counterbores, RF-thinned zone
//
// 2S1P 18650 battery bay (Sinowatt GR 3350 mAh, from Arizer Solo II):
//   Pack spec: ~40×70×21 mm, 7.2 V nominal (8.4 V full, 6.0 V discharged)
//   JST PH 2.0 mm 2-pin connector — pigtail exits via slot at X+ end of bay
//   Bay: 41 mm wide (Y) × 71 mm long (X) × 22 mm deep (Z)
//   Orientation: along X axis, centred in Y, below the PCB standoff zone.
//   CN3722 (2S MPPT solar charger) and AP63205 (buck converter) on PCB rated for 2S.
//
// To print: render and export each module separately.
//   F6 to render, then File → Export → Export as STL.
//   Use the SHOW_BASE / SHOW_LID flags below, or call each module from a
//   separate file that does:  use <welld_case.scad>  base();  (or lid();)

SHOW_BASE            = true;
SHOW_LID             = true;
SHOW_DRILL_TEMPLATE  = false;  // set true to export the 1:1 concrete drill guide
SHOW_GASKET          = false;  // set true to export the TPU lid-sealing gasket STL

// Render colour — grey-blue, ~RAL 5014 "Pigeon Blue"
CASE_COLOR = [0.47, 0.58, 0.68];

// ─────────────────────────────────────────────
// --- Parameters ---
// ─────────────────────────────────────────────

// PCB
pcb_w       = 80;    // PCB width  — long axis (X), mm
pcb_d       = 55;    // PCB depth  — short axis (Y), mm
pcb_t       = 1.6;   // PCB thickness, mm

// ── 2S1P 18650 battery bay ────────────────────────────────────────────────
//   Pack spec: Sinowatt GR 3350 mAh, ~40×70×21 mm, 7.4 V nominal (8.4 V full / 6.0 V empty)
//   JST PH 2.0 mm 2-pin connector — pigtail exits via slot at X+ end of bay.
//   Charged by CN3722 (2S MPPT solar charger) on the PCB; no USB charging path.
//   The pack lives in a rectangular pocket in the base floor, below the PCB.
//   Orientation: along X axis (longest PCB dimension), centred in Y.
batt2s_w    = 41;   // bay width:  pack 40 mm + 1.0 mm clearance, mm (Y axis)
batt2s_l    = 71;   // bay length: pack 70 mm + 1.0 mm clearance, mm (X axis)
batt2s_h    = 22;   // bay depth:  pack 21 mm + 1.0 mm clearance, mm (Z axis) = floor_h

// Wire-channel slot at X+ end of bay (JST PH 2.0 mm pigtail to J1 on PCB)
batt_wire_slot_w = 6.0;   // slot width  (X), mm
batt_wire_slot_d = 6.0;   // slot depth  (Y), mm

// Walls / floors
wall        = 2.5;   // nominal wall thickness, mm
// floor_h: PCB underside clearance / standoff height.
//   = 2S1P pack height (21 mm) + 1.0 mm clearance = 22 mm.
//   Equals batt2s_h.  The 2.5 mm floor slab below adds to absolute height.
floor_h     = 22;    // mm

// Internal air gap above PCB top surface (components + service loop)
top_clear   = 10;    // mm  (spec says ≥6; 10 gives comfortable margin)

// Lid
lid_t       = 3;     // lid plate thickness, mm
// Concrete mounting wings need extra Z to seat an M6 nut (5 mm) with ≥1 mm base.
// wing_t is independent of lid_t so the lid plate stays thin.
wing_t      = 8;     // concrete-mount wing tab thickness, mm  (must be > mount_cbore_h)
lid_lip     = 2;     // lid inner lip depth (fits inside base top opening), mm
lid_lip_t   = 1.5;   // lip wall thickness, mm (≤ wall)
lip_clearance = 0.3; // radial clearance between lip OD and base interior, mm

// Fastener geometry
m3_hole     = 3.4;   // M3 clearance hole diameter, mm
m3_cbore_d  = 6.5;   // M3 counterbore diameter (hex-head / washer face), mm
m3_cbore_h  = 2.5;   // M3 counterbore depth, mm  (must be < lid_t=3 to avoid breakthrough)
m3_insert_d = 4.5;   // M3 heat-set insert OD — wall boss inner diameter, mm
boss_d      = 8.0;   // corner boss outer diameter, mm

// Standoffs (PCB mounting pillars)
standoff_h  = floor_h;  // always equals floor_h so PCB sits flush on standoff tops
standoff_d  = 5;     // outer diameter, mm
standoff_id = 3.2;   // inner bore (tap to M3, or press-fit brass insert), mm

// Cable glands
m16_hole    = 20.5;  // M16 cable gland thread OD → drill/cut this diameter, mm
// Four M16 glands: three on bottom wall, one on back wall (solar)

// USB-C connector slot (J13, USB4135-GF-A) on left wall — 5 V charging / programming input.
// Slot is centred in Y on the PCB edge and placed at PCB surface level (Z = pcb_z).
// The USB4135-GF-A body is ~3.3 mm tall above PCB; 5 mm slot gives 1.7 mm clearance.
usbc_w     = 10;   // slot width,  mm  (USB-C receptacle opening ≈ 9 mm; +1 mm clearance)
usbc_h     = 5;    // slot height, mm  (connector body ~3.3 mm + 1.7 mm margin)
usbc_z_pcb = 0;    // slot bottom flush with PCB bottom face (Z offset from pcb_z)

// Programming header cutout (left wall, optional gland)
// Placed at Y = 80 % of pcb_d to keep it clear of the USB-C slot (Y centre = 30 mm).
// Minimum centre-to-centre distance from USB-C: |46.5 - 30| = 16.5 mm > gland radius 8 mm.
prog_gland   = true;   // include gland hole for programming cable
prog_gland_d = 16.0;   // M16 gland hole Ø — fits FTDI/SWD cables, mm

// Antenna / RF zone (lid)
rf_zone_x   = 5;     // X offset of RF-thinned zone from lid left edge, mm
                     // (antenna is near PCB left edge on ESP32-C6-MINI-1U)
rf_zone_w   = 20;    // width of thinned zone, mm
rf_zone_d   = 20;    // depth of thinned zone, mm
rf_wall_t   = 0.5;   // thinned wall thickness over antenna, mm

// Mounting tabs (left external wall)
tab_t       = 5;     // tab thickness (Y extent), mm
tab_w       = 8;     // tab Z extent, mm — halved so both tabs stay inside ext_h_base
tab_hole_d  = 5;     // hole through tab for M5 screw or cable tie, mm
tab_offset  = 4;     // half-gap from shell midpoint to tab centre (Z), mm

// SMA passthrough cutout — bottom wall (Y=0 face)
//   J3 (Amphenol 132289 edge-launch SMA) sits on the bottom PCB edge, centred at
//   X=40 mm from the left board edge → enclosure X = wall + 40 = 42.5 mm.
//   The SMA barrel protrudes 3.04 mm past the board bottom edge and exits through
//   the bottom wall of the enclosure.  The rubber-duck antenna screws directly onto
//   J3 from outside — no panel-mount bulkhead, no pigtail exits the case.
//   W1 (~50 mm internal pigtail, U.FL on ESP32 module → J3) is routed entirely
//   inside the enclosure within the top_clear zone.
//
//   Hole diameter 10.5 mm provides snug clearance for the Amphenol 132289 boss
//   (~9.52 mm hex, outer boss ≈ 9.5 mm).  10.5 mm gives ~0.5 mm radial clearance,
//   sufficient for clean barrel entry while maintaining wall contact for support.
//
//   Z centre aligned with PCB mid-thickness (edge-launch pin centreline):
//     sma_z = pcb_z + pcb_t/2 = 24.5 + 0.8 = 25.3 mm
//   (Inlined to avoid forward-reference of pcb_z / pcb_t which are derived below.)
sma_hole_d       = 10.5;   // SMA passthrough clearance hole diameter, mm
// sma_x and sma_z are derived in the derived-dimensions block below.

// XT30PW-F battery connector cutout — left wall (X=0 face)
//   AMASS XT30PW-F (LCSC C601498), right-angle THT female.
//   Board-relative position: X=5.6 mm, Y=33.5 mm from board top edge, rotation=180°.
//   Mating face points toward the left wall (X=0 in enclosure coords).
//
//   Connector body: ~18 mm long (along board X), ~10 mm wide (along board Y),
//   ~9 mm tall above PCB surface.
//
//   Enclosure-coordinate mapping:
//     Y_enc = wall + (pcb_d - 33.5) = 2.5 + 21.5 = 24.0 mm
//       (board Y=33.5 from top = 21.5 mm from bottom edge)
//     Z_enc = pcb_z + pcb_t/2 = 24.5 + 0.8 = 25.3 mm (PCB mid-plane)
//
//   Slot: 14 mm (Y) × 12 mm (Z), centred on (Y_enc=24.0, Z_enc=25.3).
//     Y range: 17.0 – 31.0 mm
//     Z range: 19.3 – 31.3 mm
//
//   Note: the USB-C slot (Y=25–35, Z=24.5–29.5) partially overlaps this cutout in
//   the region Y=25–31, Z=24.5–29.5.  In OpenSCAD both are boolean subtractions so
//   they simply produce a merged opening — both connectors remain accessible.
//   14 mm slot height provides ample margin for the XT30 plug body (~10 mm wide).
xt30_y_enc   = wall + (pcb_d - 33.5);  // 24.0 mm — connector Y centre in enclosure
xt30_z_enc   = pcb_z + pcb_t / 2;      // 25.3 mm — PCB mid-plane (same as sma_z)
xt30_slot_h  = 14;   // slot height along Y axis, mm
xt30_slot_v  = 12;   // slot height along Z axis, mm

// Back-wall solar cable gland X position (centred; SMA is now on bottom wall, not back wall)
solar_cg_x_frac = 0.5;    // fraction of ext_w; 0.5 × 85 = 42.5 mm from left (centred)

// ── Concrete lid underside mounting ──────────────────────────────────────────
//   When concrete_mount = true the lid grows four corner wings, each with an
//   M6 anchor-bolt clearance hole + nut counterbore.  The lid face (branding
//   side) presses against the concrete.  Sensor cables exit the base and hang
//   down into the well; the external SMA antenna faces the air column below.
//
//   Mounting hardware: 4× M6×50 stainless hex-head anchor bolts or M6 concrete
//   screws (e.g. Hilti HUS3-H 6×50, Rawlplug R-HPT6) in 6 mm pre-drilled holes,
//   minimum 30 mm embedment in sound concrete.  Apply silicone or polyurethane
//   sealant around each anchor entry point to maintain the enclosure's IP rating.
//
//   Anchor bolt pattern (centre-to-centre between opposite wings):
//     X span: ext_w + mount_wing_w = 85 + 22 = 107 mm
//     Y span: ext_d + mount_wing_d = 60 + 22 =  82 mm
//   Use drill_template() to print a 1:1 paper/card drill guide.
concrete_mount   = true;   // add corner wings to lid for concrete underside mount
mount_wing_w     = 22;     // wing extent beyond lid in X, mm
mount_wing_d     = 22;     // wing extent beyond lid in Y, mm
mount_bolt_d     = 6.6;    // M6 anchor bolt clearance hole, mm
mount_cbore_d    = 12.5;   // M6 hex-nut counterbore (AF 10 mm → 12.5 mm circle)
mount_cbore_h    = 6.0;    // counterbore depth — M6 nut thickness 5 mm + 1 mm

// Label emboss
label_depth = 1;     // emboss depth into top surface, mm
// Two-line branding: "WellD" large + "gh0stee.com" small
// Horizontal centre of text block = right 55% of lid (clear of RF zone)
// Inlined to avoid forward-reference of ext_w (defined further below)
label_cx    = (pcb_w + 2 * wall) * 0.65;

// Small epsilon for clean boolean differences
eps = 0.01;

// ─────────────────────────────────────────────
// --- Derived dimensions (do not edit) ---
// ─────────────────────────────────────────────

// Total external footprint
ext_w = pcb_w + 2 * wall;          // X:  85 mm
ext_d = pcb_d + 2 * wall;          // Y:  60 mm

// Internal height breakdown
//   floor slab  : wall (printed floor thickness, same as wall)       =  2.5 mm
//   floor_h gap : standoff height / battery bay zone                 = 22.0 mm
//   pcb_t       : PCB itself                                         =  1.6 mm
//   top_clear   : above PCB top surface                              = 10.0 mm
// External shell height (base only, no lid):
ext_h_base = wall + floor_h + pcb_t + top_clear;   // = 36.1 mm
// total with lid:
ext_h_total = ext_h_base + lid_t;                  // = 39.1 mm

// Z-coordinate of PCB bottom face (inside enclosure, above floor slab face)
pcb_z = wall + floor_h;            // 2.5 + 22 = 24.5 mm from enclosure base

// Z-coordinate of PCB top face
pcb_top_z = pcb_z + pcb_t;         // 26.1 mm

// SMA passthrough cutout position on the bottom wall (Y=0 face).
//   X: J3 is at X=40 mm from the left board edge → enclosure X = wall + 40 mm.
//   Z: edge-launch SMA pin centreline = PCB mid-thickness above the floor zone.
//      pcb_z + pcb_t/2 = 24.5 + 0.8 = 25.3 mm
sma_x = wall + 40;          // 42.5 mm from case left outer edge
sma_z = pcb_z + pcb_t / 2; // 25.3 mm — edge-launch SMA pin centreline

// Z-centre of the USB-C slot on the left wall
usbc_z_centre = pcb_z + usbc_z_pcb + usbc_h / 2;   // 24.5 + 0 + 2.5 = 27.0 mm

// Z height of top of base walls (= top of the shell opening)
shell_top_z = ext_h_base;

// PCB mounting hole positions in PCB-local coords (from lower-left corner)
mh = [[3.5, 3.5], [76.5, 3.5], [3.5, 51.5], [76.5, 51.5]];

// Same positions in enclosure coords (offset by wall in X and Y)
function mh_enc(i) = [mh[i][0] + wall, mh[i][1] + wall];

// Screw boss positions (corner bosses for lid screws) — placed at PCB hole positions
// The bosses are cylinders inside the four corners of the base.
// We reuse the four PCB mounting hole positions for the lid screws so the same
// M3 locations do double duty: standoffs below the PCB, through-bosses above.
// The lid M3 insert bores are on the top rim of the corner bosses.

// Cable-gland Z centre on bottom (Y=0) wall — mid-height of screw terminal connectors
// Terminals are 8.5 mm tall above PCB, centred vertically on PCB + 4.25 mm
cg_z_bottom = pcb_top_z + (8.5 / 2);   // ≈ 30.4 mm from enclosure floor face

// 2S1P bay position (interior coordinates) — rectangular pocket, centred in X and Y
batt_cx = wall + pcb_w / 2;    // X centre: 2.5 + 40 = 42.5 mm
batt_cy = wall + pcb_d / 2;    // Y centre: 2.5 + 27.5 = 30 mm
// Bay carved from interior floor surface (Z = wall) downward (pocket in floor zone)
batt_bay_z  = wall;             // start Z (bottom of pocket = top of floor slab)
batt_bay_h  = batt2s_h;        // 22 mm — fills full floor_h zone (0 mm gap to PCB)

// JST pigtail wire-slot — X+ end only; routes pigtail up to J1 on PCB
batt_wire_x_pos = batt_cx + batt2s_l / 2 - batt_wire_slot_w / 2;  // near X+ end of bay

// ─────────────────────────────────────────────
// --- Helper modules ---
// ─────────────────────────────────────────────

// Rounded-rectangle prism (convex hull of four cylinders)
module rounded_box(w, d, h, r) {
    hull() {
        for (x = [r, w - r], y = [r, d - r]) {
            translate([x, y, 0]) cylinder(r = r, h = h, $fn = 32);
        }
    }
}

// Single PCB standoff at enclosure-local (x, y).
// Solid pillar with central bore (tap M3 or press-fit brass insert).
module standoff(x, y) {
    translate([x, y, wall]) {
        difference() {
            cylinder(d = standoff_d, h = standoff_h, $fn = 32);
            translate([0, 0, -eps])
                cylinder(d = standoff_id, h = standoff_h + 2 * eps, $fn = 24);
        }
    }
}

// Corner boss for lid screw (above PCB level).
// A filled cylinder from pcb_z up to the shell top, with a heat-set insert bore
// drilled from the top.
module corner_boss(x, y) {
    boss_bot = wall;              // boss starts at floor inside face
    boss_top = shell_top_z;
    boss_h   = boss_top - boss_bot;

    translate([x, y, boss_bot]) {
        difference() {
            cylinder(d = boss_d, h = boss_h, $fn = 32);
            // heat-set insert bore from top (blind, 6 mm deep)
            translate([0, 0, boss_h - 6])
                cylinder(d = m3_insert_d, h = 6 + eps, $fn = 24);
        }
    }
}

// Cable gland hole — cylindrical punch through a wall.
// orient: "x" punches along X axis, "y" punches along Y axis.
// cx, cy, cz: centre of the hole in enclosure coordinates.
// d: hole diameter (defaults to m16_hole for M16 glands).
module cg_hole(cx, cy, cz, orient = "y", d = m16_hole) {
    if (orient == "y") {
        translate([cx, cy, cz])
            rotate([90, 0, 0])
                cylinder(d = d, h = wall * 4, center = true, $fn = 48);
    } else {
        translate([cx, cy, cz])
            rotate([0, 90, 0])
                cylinder(d = d, h = wall * 4, center = true, $fn = 48);
    }
}

// Programming header cable gland (M16) on left wall.
module prog_cg_hole(cy, cz) {
    cg_hole(0, cy, cz, "x");
}

// External mounting tab on left wall.
// z_centre: Z-centre of the tab, measured from enclosure base.
module mounting_tab(z_centre) {
    tab_h = tab_w;   // Z extent of the tab block
    translate([-tab_t, ext_d / 2 - tab_t / 2, z_centre - tab_h / 2]) {
        difference() {
            cube([tab_t, tab_t, tab_h]);
            // through-hole for M5 screw or cable tie
            translate([tab_t / 2, tab_t / 2, tab_h / 2])
                rotate([0, 0, 0])
                    cylinder(d = tab_hole_d, h = tab_h + 2 * eps,
                             center = true, $fn = 24);
        }
    }
}

// Corner mounting wing for concrete underside mounting.
// Placed at (cx, cy) — a corner of the lid footprint.
// sign_x / sign_y: +1 or -1, direction the wing extends from that corner.
module mount_wing_tab(cx, cy, sign_x, sign_y) {
    // Overlap into the lid corner so the wing is solidly fused when unioned.
    lap = 5;
    ox = (sign_x > 0) ? cx - lap : cx - mount_wing_w;
    oy = (sign_y > 0) ? cy - lap : cy - mount_wing_d;
    // Bolt hole centre stays at the mid-point of the outer wing span.
    hx = cx + sign_x * (mount_wing_w / 2);
    hy = cy + sign_y * (mount_wing_d / 2);

    difference() {
        translate([ox, oy, 0])
            rounded_box(mount_wing_w + lap, mount_wing_d + lap, wing_t, r = 3);

        // M6 anchor bolt clearance hole (through full wing thickness)
        translate([hx, hy, -eps])
            cylinder(d = mount_bolt_d, h = wing_t + 2 * eps, $fn = 24);

        // M6 nut counterbore on the interior face (Z = wing_t).
        // Bolt passes up through concrete anchor → wing → nut tightened from
        // inside the well.  Counterbore depth leaves ≥1 mm at concrete face.
        translate([hx, hy, wing_t - mount_cbore_h])
            cylinder(d = mount_cbore_d, h = mount_cbore_h + eps, $fn = 32);
    }
}

// 2S1P battery bay — rectangular pocket carved into the floor zone.
// Pocket dimensions: batt2s_l (X) × batt2s_w (Y) × batt2s_h (Z).
// Centred in both X and Y; carved from Z = wall (interior floor surface) upward.
// batt2s_h = floor_h = 22 mm so the pocket uses the full standoff-height zone.
module batt_bay_cutout() {
    translate([batt_cx - batt2s_l / 2, batt_cy - batt2s_w / 2, batt_bay_z])
        cube([batt2s_l, batt2s_w, batt_bay_h]);
}

// JST pigtail wire-channel slot — X+ end of the bay only.
// The JST PH 2.0 mm pigtail exits the bay at the positive X end and routes
// up through the standoff zone to J1 on the PCB.
// Slot runs from bay floor (Z = wall) up through the full floor_h zone.
module batt_wire_channels() {
    slot_h = floor_h + eps;   // spans the full standoff zone above the floor slab
    translate([batt_wire_x_pos,
               batt_cy - batt_wire_slot_d / 2,
               wall - eps])
        cube([batt_wire_slot_w, batt_wire_slot_d, slot_h + eps]);
}

// Flat 1:1 drill template — print on paper/card, tape to concrete,
// centre-punch through the holes to mark the anchor-bolt positions.
// Template outline = lid + wing footprint; bolt holes are indicated by
// 2 mm circles.  Export as a separate STL (paper template height = 0.3 mm).
module drill_template() {
    tw = ext_w + 2 * mount_wing_w;
    td = ext_d + 2 * mount_wing_d;
    th = 0.3;   // one layer — print with a coloured filament for visibility

    difference() {
        // Outer rectangle, centred on the lid footprint
        translate([-mount_wing_w, -mount_wing_d, 0])
            rounded_box(tw, td, th, r = 3);

        // Lid outline cutout (leaves a frame showing the device footprint)
        translate([0, 0, -eps])
            rounded_box(ext_w, ext_d, th + 2 * eps, r = 3);

        // Four anchor-hole markers (2 mm Ø pillars become holes in template)
        for (cx_t = [0, ext_w], cy_t = [0, ext_d]) {
            sx = (cx_t == 0) ? -1 : +1;
            sy = (cy_t == 0) ? -1 : +1;
            hx_t = cx_t + sx * (mount_wing_w / 2);
            hy_t = cy_t + sy * (mount_wing_d / 2);
            translate([hx_t, hy_t, -eps])
                cylinder(d = 2.0, h = th + 2 * eps, $fn = 16);
        }
    }
}

// ─────────────────────────────────────────────
// --- Base (bottom shell) ---
// ─────────────────────────────────────────────

module base() {
    difference() {

        // ── Solid shell body ──────────────────────────────────────────────
        union() {
            // Outer shell block (rounded corners, r=3 mm)
            rounded_box(ext_w, ext_d, ext_h_base, r = 3);

            // Corner bosses (four, at PCB mounting hole positions)
            for (i = [0:3]) {
                corner_boss(mh_enc(i)[0], mh_enc(i)[1]);
            }

            // External mounting tabs on left (X=0) wall
            mounting_tab(ext_h_base / 2 - tab_offset);
            mounting_tab(ext_h_base / 2 + tab_offset);
        }

        // ── Hollow out the interior ───────────────────────────────────────
        // Interior cavity starts above the floor (wall thickness = wall)
        // and leaves wall thickness on all four sides.
        // The top is open (no ceiling — the lid provides it).
        translate([wall, wall, wall])
            cube([pcb_w, pcb_d, ext_h_base - wall + eps]);

        // ── 2S1P battery bay ──────────────────────────────────────────────
        // Rectangular pocket in the floor zone, centred in X and Y.
        // 71 mm (X) × 41 mm (Y) × 22 mm (Z); fills the full floor_h zone.
        batt_bay_cutout();

        // ── JST pigtail wire-channel slot ────────────────────────────────
        // 6×6 mm slot at X+ end of bay, spanning the full floor_h zone.
        // JST PH 2.0 mm pigtail routes from bay up to J1 on the PCB.
        batt_wire_channels();

        // ── Bottom-wall (Y=0 face) cable gland holes ─────────────────────
        // Three M16 glands for: 4-20 mA transducer cable, DS18B20 1-wire, solar/spare.
        // The SMA passthrough cutout occupies X=42.5 mm on this same wall, so gland
        // positions are shifted left and right to clear it.
        //
        // Available X span (enclosure interior): wall=2.5 mm to ext_w-wall=82.5 mm.
        // SMA centre at X=42.5 mm with 10.5 mm hole → exclusion zone X≈37.25–47.75 mm.
        // M16 hole radius = 10.25 mm; minimum gland centre distance from SMA edge:
        //   |cg_cx - sma_x| ≥ (m16_hole/2 + sma_hole_d/2 + 1) = 10.25+5.25+1 = 16.5 mm
        //   → cg_cx ≤ 26.0 mm  or  cg_cx ≥ 59.0 mm
        //
        // Chosen positions (clear of SMA, clear of each other, within wall):
        //   Gland 0 (left):   X = 15.0 mm  (4-20 mA transducer)
        //   Gland 1 (centre-left): X = 27.5 mm  (DS18B20 1-wire + GND)
        //   Gland 2 (right):  X = 70.0 mm  (spare / future sensor)
        // Centre-to-centre check:
        //   0↔1: |27.5-15.0|=12.5 mm ≥ m16_hole+1=21.5? NO — use 3-zone split instead.
        //
        // With only 80 mm of wall width and m16_hole=20.5 mm diameter, three M16 glands
        // can fit left-of-SMA and right-of-SMA if we place two on the left side and one
        // on the right, ensuring ≥1 mm of solid wall between any two holes:
        //   Min c-to-c between two M16s: 20.5 + 1 = 21.5 mm
        //   Left zone X=2.5..26.0: can fit ONE gland at X≈14.25 (centre of left zone)
        //   Right zone X=59.0..82.5: can fit ONE gland at X≈70.75
        //   A third gland: place on the right at X≈14.25 (left zone, ONLY one fits here)
        //
        // Practical solution: two glands left-of-SMA as far left as possible, one right.
        //   Gland 0: X = wall + m16_hole/2 + 0.5 = 2.5 + 10.25 + 0.5 = 13.25 mm
        //   Gland 1: X = 13.25 + 21.5 = 34.75 mm — but 34.75 < 37.25 (SMA excl zone edge)
        //             → this still leaves only 37.25-34.75=2.5 mm gap (10.25+5.25=15.5 vs 8)
        //             — overlap! Two M16s left-of-SMA require 2×21.5=43 mm; left zone is
        //             only 23.5 mm wide. Only ONE M16 fits left of the SMA.
        //
        // Final layout — one gland each side of SMA plus one gland on the back wall:
        //   Gland 0 (bottom-wall, left):  X = 20.0 mm  (4-20 mA transducer cable)
        //   Gland 1 (bottom-wall, right): X = 65.0 mm  (DS18B20 1-wire + GND cable)
        //   Gland 2 (back-wall): already present as solar cable gland.
        // Clearance checks (gland radius 10.25 mm, SMA radius 5.25 mm):
        //   Gland 0 ↔ SMA: |42.5-20.0|=22.5 mm ≥ 10.25+5.25+1=16.5 mm ✓
        //   Gland 1 ↔ SMA: |65.0-42.5|=22.5 mm ≥ 16.5 mm ✓
        //   Gland 0 ↔ left wall: 20.0-2.5=17.5 mm from outer edge; ≥10.25 ✓
        //   Gland 1 ↔ right wall: 82.5-65.0=17.5 mm from outer edge; ≥10.25 ✓
        cg_hole(20.0, 0, cg_z_bottom, "y");   // 4-20 mA transducer cable
        cg_hole(65.0, 0, cg_z_bottom, "y");   // DS18B20 1-wire + GND cable

        // ── Left-wall: USB-C connector slot (J13, USB4135-GF-A) ─────────────────
        // Slot: 10 mm wide (Y), 5 mm tall (Z), centred on PCB Y-midline.
        // Bottom edge flush with PCB bottom face (usbc_z_centre = pcb_z + usbc_h/2 = 27.0 mm).
        // usbc_z_centre is computed in the derived-dimensions block above.
        translate([-eps, ext_d / 2 - usbc_w / 2, usbc_z_centre - usbc_h / 2])
            cube([wall + 2 * eps, usbc_w, usbc_h]);

        // ── Left-wall: XT30PW-F battery connector cutout ────────────────────────
        // AMASS XT30PW-F (LCSC C601498) right-angle THT female at board-relative
        // X=5.6 mm, Y=33.5 mm from board top, rotation=180° (mating face → left wall).
        // Enclosure Y centre: wall + (pcb_d - 33.5) = 24.0 mm
        // Enclosure Z centre: pcb_z + pcb_t/2 = 25.3 mm (PCB mid-plane)
        // Slot: 14 mm (Y) × 12 mm (Z) gives ≥2 mm margin around the 10 mm plug body.
        // See parameter block above for full derivation and USB-C overlap note.
        translate([-eps,
                   xt30_y_enc - xt30_slot_h / 2,
                   xt30_z_enc - xt30_slot_v / 2])
            cube([wall + 2 * eps, xt30_slot_h, xt30_slot_v]);

        // ── Left-wall programming header cable gland ─────────────────────────────
        // Y-offset toward the back wall to avoid merging with the USB-C slot.
        // USB-C slot: Y centre = ext_d/2 = 30 mm.
        // Gland centre: Y = wall + pcb_d*0.8 = 2.5 + 44 = 46.5 mm → 16.5 mm clear.
        // Z: upper third of the left-wall height to stay above the USB-C slot (Z ≈ 24-30 mm).
        if (prog_gland) {
            prog_cy = wall + pcb_d * 0.8;           // 46.5 mm — toward back wall
            prog_cz = pcb_top_z + top_clear * 0.55; // ≈ 31.6 mm — above USB-C zone
            cg_hole(0, prog_cy, prog_cz, "x", prog_gland_d);
        }

        // ── Back-wall (Y=ext_d face): solar cable gland ──────────────────
        // Solar gland: centred in X (SMA is now on the bottom wall, not back wall).
        cg_hole(ext_w * solar_cg_x_frac, ext_d, ext_h_base / 2, "y");

        // ── Bottom-wall (Y=0 face): SMA passthrough cutout ────────────────
        // J3 (Amphenol 132289 edge-launch SMA) is centred at X=40 mm from the
        // left board edge.  The SMA barrel protrudes 3.04 mm past the board
        // bottom edge and exits through this wall.  The rubber-duck antenna
        // threads directly onto J3 from outside — no bulkhead fitting, no pigtail.
        //
        // Hole: 10.5 mm Ø, punched along the Y axis through the full wall (2.5 mm).
        // Z centre: pcb_z + pcb_t/2 = 25.3 mm (edge-launch pin centreline).
        // X centre: wall + 40 = 42.5 mm (J3 X position in enclosure coords).
        //
        // cg_hole() centres the punch on (cx, cy, cz) and extends ±wall*2 each
        // side along the chosen axis, so it cleanly penetrates the 2.5 mm wall.
        cg_hole(sma_x, 0, sma_z, "y", sma_hole_d);

        // ── M3 lid screw through-holes in top rim (corner bosses) ─────────
        // These are the clearance holes through the boss top into the insert bore.
        // Drilled from above, so the screw passes through the lid and threads into
        // the insert in the boss.  (The insert bore is already carved in corner_boss.)
        // No additional cut needed here — the lid carries the clearance holes.

    } // end difference (base)

    // ── PCB standoffs (added after difference so they're not hollowed) ──
    // Standoffs are 22 mm tall (= floor_h), placing PCB tops at Z = 24.5 + 1.6 = 26.1 mm.
    // The battery bay (71×41 mm) clears the standoff columns — standoffs sit at
    // the four PCB hole corners (3.5 mm from edges) which are outside the bay footprint.
    for (i = [0:3]) {
        standoff(mh_enc(i)[0], mh_enc(i)[1]);
    }
}

// ─────────────────────────────────────────────
// --- Lid ---
// ─────────────────────────────────────────────

module lid() {
    // Lid sits on top of the base, with a 2 mm inner lip that drops into the
    // opening.  Four countersunk M3 clearance holes at the corner boss positions.
    //
    // When concrete_mount = true, four corner wings extend beyond the lid
    // footprint; each carries an M6 anchor-bolt clearance hole + nut counterbore.
    // The lid face (branding side = top when installed normally) presses against
    // the underside of the concrete well lid.
    //
    // Coordinate origin of the lid module = bottom face of lid (as printed).
    // The lid is printed upside-down (label face down) for best surface finish,
    // but the module is oriented "installed" for the preview.

    lid_w = ext_w;
    lid_d = ext_d;

    difference() {
        union() {
            // ── Main lid plate ───────────────────────────────────────────
            rounded_box(lid_w, lid_d, lid_t, r = 3);

            // ── Inner lip (fits inside base top opening) ─────────────────
            // Suppressed for concrete_mount: when the lid is flipped face-down
            // against concrete, the lip would point upward and press against the
            // ceiling.  Gasket sealing is used instead.
            //
            // Lip OD = base interior − 2×lip_clearance so it slides in without
            // binding.  The inner hollow leaves lid_lip_t wall all round.
            if (!concrete_mount) {
                lip_x  = wall + lip_clearance;
                lip_y  = wall + lip_clearance;
                lip_ow = pcb_w - 2 * lip_clearance;   // outer width of lip ring
                lip_od = pcb_d - 2 * lip_clearance;   // outer depth of lip ring
                translate([lip_x, lip_y, -lid_lip])
                    difference() {
                        rounded_box(lip_ow, lip_od, lid_lip + eps, r = 2);
                        translate([lid_lip_t, lid_lip_t, -eps])
                            cube([lip_ow - 2 * lid_lip_t, lip_od - 2 * lid_lip_t,
                                  lid_lip + 3 * eps]);
                    }
            }

            // ── Concrete-lid mounting wings (unioned here so they fuse) ──
            if (concrete_mount) {
                mount_wing_tab( 0,     0,     -1, -1);   // bottom-left
                mount_wing_tab( ext_w, 0,     +1, -1);   // bottom-right
                mount_wing_tab( 0,     ext_d, -1, +1);   // top-left
                mount_wing_tab( ext_w, ext_d, +1, +1);   // top-right
            }
        }

        // ── M3 countersunk clearance holes (one per corner boss) ─────────
        for (i = [0:3]) {
            hx = mh_enc(i)[0];
            hy = mh_enc(i)[1];
            // Clearance hole through full lid thickness
            translate([hx, hy, -eps])
                cylinder(d = m3_hole, h = lid_t + 2 * eps, $fn = 24);
            // Counterbore on top surface (screw head recessed)
            translate([hx, hy, lid_t - m3_cbore_h])
                cylinder(d = m3_cbore_d, h = m3_cbore_h + eps, $fn = 32);
        }

        // ── RF-transparent zone over ESP32-C6-MINI-1U antenna ────────────
        // The antenna is on the left side of the module which sits near PCB
        // left edge.  Thin the lid to rf_wall_t in a 20×20 mm zone.
        // rf_zone_x is offset from lid left edge; rf_zone starts 5 mm from left.
        rf_zone_y = (lid_d - rf_zone_d) / 2;   // centred in Y
        recess_depth = lid_t - rf_wall_t;
        translate([rf_zone_x, rf_zone_y, rf_wall_t])
            cube([rf_zone_w, rf_zone_d, recess_depth + eps]);

        // ── Branding — recessed into top surface (debossed) ──────────────────
        // Laid out in the right 55 % of the lid to stay clear of the RF zone.
        // Depth 1.5 mm in a 3 mm lid — leaves 1.5 mm wall, visible and printable.
        // "WellD"  — large bold product name
        translate([label_cx, lid_d * 0.63, lid_t - 1.5])
            linear_extrude(height = 1.5 + eps)
                text("WellD",
                     size   = 8,
                     halign = "center",
                     valign = "center",
                     font   = "Liberation Sans:style=Bold");
        // "gh0stee.com" — smaller domain / maker mark below
        translate([label_cx, lid_d * 0.35, lid_t - 1.5])
            linear_extrude(height = 1.5 + eps)
                text("gh0stee.com",
                     size   = 4.5,
                     halign = "center",
                     valign = "center",
                     font   = "Liberation Sans:style=Regular");
    }

}

// ─────────────────────────────────────────────
// --- TPU gasket ---
// ─────────────────────────────────────────────

// Flat lid-sealing gasket — print in TPU 95A.
// Outer footprint matches the base top rim (ext_w × ext_d, r=3).
// Inner opening matches the base interior (pcb_w × pcb_d).
// Uncompressed thickness 1.5 mm → ~1.0 mm at 33 % compression under the lid.
// The 2.5 mm wide rim provides the seating surface.
// For concrete_mount lids (no inner lip), the gasket is the only seal path.
// Print settings: 3 walls, 0 % infill (solid perimeters), 0.2 mm layers, no supports.
module gasket() {
    gasket_t = 1.5;   // uncompressed thickness, mm
    difference() {
        rounded_box(ext_w, ext_d, gasket_t, r = 3);
        translate([wall, wall, -eps])
            cube([pcb_w, pcb_d, gasket_t + 2 * eps]);
    }
}

// ─────────────────────────────────────────────
// --- Preview / export layout ---
// ─────────────────────────────────────────────

// Both parts shown slightly separated so you can inspect the assembly.
// To print: render and export each module separately.
//   • Base:           SHOW_BASE=true, others false → F6 → Export STL
//   • Lid:            SHOW_LID=true,  others false → F6 → Export STL
//     (Print lid upside-down — label face to the bed.)
//   • Drill template: SHOW_DRILL_TEMPLATE=true, others false → F6 → Export STL
//     Print at 100% scale on paper/card; tape to concrete; centre-punch holes.

if (SHOW_BASE) {
    color(CASE_COLOR) base();
}

if (SHOW_LID) {
    // Lift lid above base for assembly view (40 mm separation)
    color(CASE_COLOR) translate([0, 0, ext_h_base + 40])
        lid();
}

if (SHOW_DRILL_TEMPLATE) {
    // Shown in the XY plane beside the base for preview purposes.
    // Wings extend into negative X/Y so offset it clear of the base model.
    color(CASE_COLOR) translate([-mount_wing_w - 5, -mount_wing_d - 5, 0])
        drill_template();
}

if (SHOW_GASKET) {
    // Shown floating above the base top rim for preview.
    // For STL export: set SHOW_GASKET=true, others false → F6 → Export STL.
    // Slice in TPU 95A: 3 walls, 0 % infill, 0.2 mm layers.
    color([0.95, 0.7, 0.2]) translate([0, 0, ext_h_base + 2])
        gasket();
}

// ─────────────────────────────────────────────
// --- Bill of materials (hardware per unit) ---
// ─────────────────────────────────────────────
// 4× M3×8 button-head screws (lid)
// 4× M3 heat-set inserts (press into corner boss bores with soldering iron)
// 4× M3×6 self-tapping or machine screws (PCB standoffs — optional; brass inserts preferred)
// 4× M3 brass threaded inserts for PCB standoffs (press-fit, 3 mm OD bore)
// 1× 2S1P 18650 battery pack (Sinowatt GR 3350 mAh from Arizer Solo II,
//    ~40×70×21 mm, 7.2 V nominal, JST PH 2.0 mm 2-pin connector)
// 2× M16 cable glands (bottom wall — X=20 mm: 4-20 mA transducer cable; X=65 mm: DS18B20 1-wire + GND)
//    NOTE: third gland moved to back wall (solar) to clear the SMA cutout at X=42.5 mm
// 1× USB-C slot cutout (left wall — J13 USB4135-GF-A, 5 V charging input; no gland, connector flush)
// 1× XT30PW-F plug clearance slot (left wall — J1 battery connector, 14×12 mm slot at Y=17–31 mm, Z=19.3–31.3 mm)
// 1× M16 cable gland (left wall — programming/debug cable; offset toward back wall, Y ≈ 46.5 mm)
// 1× M16 cable gland (back wall — solar panel cable)
// 1× 2.4 GHz rubber-duck SMA antenna (screws directly onto J3 through bottom-wall cutout,
//    e.g. Taoglas FXP73 or equivalent; no bulkhead fitting required)
// 1× W1 U.FL-to-SMA internal pigtail, ~50 mm, RG178 (ESP32 U.FL → J3 on PCB, fully internal)
// 1× TPU 95A gasket (printed from SHOW_GASKET export — replaces silicone sealant bead)
// For concrete_mount variant additionally:
// 4× M6×50 stainless anchor bolts (e.g. Hilti HUS3-H 6×50 or Rawlplug R-HPT6)
// 4× M6 stainless hex nuts (tightened from inside the well against wing counterbore)
