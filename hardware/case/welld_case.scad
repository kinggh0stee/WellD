// WellD Well-Level Monitor — Parametric Enclosure
// Target printer: FDM, PETG or ASA recommended (outdoor/IP54 use)
// ESP32-C6-MINI-1U based PCB, 80×55 mm
//
// Two-part design:
//   base()  — bottom shell with PCB standoffs and wall cutouts
//   lid()   — flat plate with inner lip, screw counterbores, RF-thinned zone
//
// To print: render and export each module separately.
//   F6 to render, then File → Export → Export as STL.
//   Use the SHOW_BASE / SHOW_LID flags below, or call each module from a
//   separate file that does:  use <welld_case.scad>  base();  (or lid();)

SHOW_BASE            = true;
SHOW_LID             = true;
SHOW_DRILL_TEMPLATE  = false;  // set true to export the 1:1 concrete drill guide

// ─────────────────────────────────────────────
// --- Parameters ---
// ─────────────────────────────────────────────

// PCB
pcb_w       = 80;    // PCB width  — long axis (X), mm
pcb_d       = 55;    // PCB depth  — short axis (Y), mm
pcb_t       = 1.6;   // PCB thickness, mm

// ── 2S 18650 battery pack variant ─────────────────────────────────────────────
//   Set USE_2S_BATTERY = true to generate the taller-base variant sized for a
//   side-by-side 2S1P 18650 pack (e.g. CS-ARS200SL, 7.4 V 3400 mAh) that sits
//   directly on the enclosure floor below the PCB.
//
//   ⚠ ELECTRICAL WARNING — PCB IS NOT COMPATIBLE WITH A 2S PACK WITHOUT REWORK:
//     • U1 TPS7A0533 LDO: abs-max input 6.5 V — 8.4 V (charged 2S) destroys it.
//     • U2 TP4056 / U7 CN3791: both rated to 6.5 V input — same issue.
//     • U3 S-8261AAYFT: single-cell protection (2.9 V cutoff) — replace with a
//       2S-rated IC (e.g. S-8232) or discrete 2S BMS (cutoff ≈ 6.0 V).
//     Required PCB changes before connecting the 2S pack:
//       1. Replace U1 with a wide-input buck converter (e.g. TPS54331, 4.5–28 V in).
//       2. Replace U2/U7 with a 2S charger (e.g. MCP73213 or BQ25606).
//       3. Replace U3 with a 2S protection IC.
//     The change here is enclosure geometry only.
USE_2S_BATTERY = false;

BATT_2S_L   = 73;    // pack length  (along case X axis), mm  ← 18650×2 + wrap
BATT_2S_W   = 40;    // pack width   (along case Y axis), mm  ← cell OD + wrap
BATT_2S_H   = 22;    // pack height  (along case Z axis), mm  ← cell OD + wrap
BATT_2S_TOL =  1.0;  // clearance each side of locating posts, mm

// Walls / floors
wall        = 2.5;   // nominal wall thickness, mm
// floor_h: PCB underside clearance.  For the 2S variant the battery (BATT_2S_H)
// plus a 3 mm service gap determines the standoff height.
floor_h     = USE_2S_BATTERY ? (BATT_2S_H + 3) : 3;

// Internal air gap above PCB top surface (components + service loop)
top_clear   = 10;    // mm  (spec says ≥6; 10 gives comfortable margin)

// Lid
lid_t       = 3;     // lid plate thickness, mm
lid_lip     = 2;     // lid inner lip depth (fits inside base top opening), mm
lid_lip_t   = 1.5;   // lip wall thickness, mm (≤ wall)

// Fastener geometry
m3_hole     = 3.4;   // M3 clearance hole diameter, mm
m3_cbore_d  = 6.5;   // M3 counterbore diameter (hex-head / washer face), mm
m3_cbore_h  = 3.5;   // M3 counterbore depth, mm
m3_insert_d = 4.5;   // M3 heat-set insert OD — wall boss inner diameter, mm
boss_d      = 8.0;   // corner boss outer diameter, mm

// Standoffs (PCB mounting pillars)
standoff_h  = floor_h;  // always equals floor_h so PCB sits flush on standoff tops
standoff_d  = 5;     // outer diameter, mm
standoff_id = 3.2;   // inner bore (tap to M3, or press-fit brass insert), mm

// Cable glands
m16_hole    = 20.5;  // M16 cable gland thread OD → drill/cut this diameter, mm
// Five M16 glands on bottom wall, one each on left/right/back walls

// USB-C cutout (left wall)
usbc_w      = 10;    // slot width,  mm
usbc_h      = 5;     // slot height, mm
usbc_z_pcb  = 0;     // USB-C connector sits at PCB surface level (bottom of slot
                     // is at floor_h + 0; top at floor_h + usbc_h)

// Programming header cutout (left wall, optional gland)
prog_gland  = true;  // include M16 gland hole for programming cable

// Antenna / RF zone (lid)
rf_zone_x   = 5;     // X offset of RF-thinned zone from lid left edge, mm
                     // (antenna is near PCB left edge on ESP32-C6-MINI-1U)
rf_zone_w   = 20;    // width of thinned zone, mm
rf_zone_d   = 20;    // depth of thinned zone, mm
rf_wall_t   = 0.5;   // thinned wall thickness over antenna, mm

// Mounting tabs (left external wall)
tab_t       = 5;     // tab thickness (Y extent), mm
tab_w       = 12;    // tab width (Z extent), mm
tab_hole_d  = 5;     // hole through tab for M5 screw or cable tie, mm
tab_offset  = 8;     // distance from each outer edge to tab centre (Z), mm

// External antenna (SMA female bulkhead on back wall)
//   The back wall (Y = ext_d face) is closest to the ESP32 U.FL connector.
//   A U.FL-to-SMA pigtail (~100 mm RG178) runs from J3 on the PCB to the bulkhead.
//   Set ext_antenna = false to omit the hole and use the on-module chip antenna instead.
ext_antenna      = true;   // include SMA bulkhead hole on back wall
sma_hole_d       = 6.5;    // SMA panel-mount thread clearance hole, mm
                            // (SMA thread OD = 6.35 mm = 1/4-36 UNS; 6.5 mm is snug clearance)
// Horizontal position of the SMA hole on the back wall (from left outer edge)
// U.FL (J3) is at PCB x=40, which is case-internal x=42.5.  Centre the bulkhead there.
sma_x           = 42.5;    // mm from case left outer edge
// Vertical position of the SMA hole — mid-height of the base shell
// Inlined to avoid forward-reference of ext_h_base (defined further below)
sma_z           = (wall + floor_h + pcb_t + top_clear) / 2;

// Back-wall solar cable gland X position (moved left to make room for SMA)
solar_cg_x_frac = 0.25;   // fraction of ext_w; 0.25 × 85 = ~21 mm from left

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
//   floor slab  : wall (printed floor thickness, same as wall)
//   floor_h gap : clearance between floor face and PCB underside
//   pcb_t       : PCB itself
//   top_clear   : above PCB top surface
// External shell height (base only, no lid):
ext_h_base = wall + floor_h + pcb_t + top_clear;
// total with lid:
ext_h_total = ext_h_base + lid_t;

// Z-coordinate of PCB bottom face (inside enclosure, above floor face)
pcb_z = wall + floor_h;            // 3 + 2.5 = 5.5 mm from enclosure base

// Z-coordinate of PCB top face
pcb_top_z = pcb_z + pcb_t;         // 7.1 mm

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
cg_z_bottom = pcb_top_z + (8.5 / 2);   // ≈ 11.4 mm from enclosure floor face

// USB-C Z centre — connector sits at PCB surface, opening centred on connector body
usbc_z_centre = pcb_z + pcb_t / 2 + usbc_h / 2;

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

// Four corner locating posts for the 2S 18650 pack.
// The pack slots in between them; BATT_2S_TOL clearance each side.
// Posts height = BATT_2S_H so the PCB standoffs clear the pack by ~3 mm.
module battery_locators_2s() {
    cx = wall + pcb_w / 2;
    cy = wall + pcb_d / 2;
    hl = (BATT_2S_L / 2) + BATT_2S_TOL;   // half-span X, to post inner edge
    hw = (BATT_2S_W / 2) + BATT_2S_TOL;   // half-span Y, to post inner edge
    post_d = 5;
    for (sx = [-1, 1], sy = [-1, 1]) {
        translate([cx + sx * hl - (sx > 0 ? post_d : 0),
                   cy + sy * hw - (sy > 0 ? post_d : 0),
                   wall])
            cube([post_d, post_d, BATT_2S_H]);
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

// M16 cable gland hole — cylindrical punch through a wall.
// orient: "x" punches along X axis, "y" punches along Y axis.
// cx, cy, cz: centre of the hole in enclosure coordinates.
module cg_hole(cx, cy, cz, orient = "y") {
    if (orient == "y") {
        translate([cx, cy, cz])
            rotate([90, 0, 0])
                cylinder(d = m16_hole, h = wall * 4, center = true, $fn = 48);
    } else {
        translate([cx, cy, cz])
            rotate([0, 90, 0])
                cylinder(d = m16_hole, h = wall * 4, center = true, $fn = 48);
    }
}

// USB-C rectangular slot — punches through left wall (at x=0 face).
// Centred at (0, usbc_cy, usbc_cz) in enclosure coords.
module usbc_slot(cy, cz) {
    translate([-eps, cy - usbc_w / 2, cz - usbc_h / 2])
        cube([wall + 2 * eps, usbc_w, usbc_h]);
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
    // Wing body origin (lower-left of its bounding box)
    ox = (sign_x > 0) ? cx : cx - mount_wing_w;
    oy = (sign_y > 0) ? cy : cy - mount_wing_d;
    // Bolt hole centre inside the wing
    hx = cx + sign_x * (mount_wing_w / 2);
    hy = cy + sign_y * (mount_wing_d / 2);

    difference() {
        translate([ox, oy, 0])
            rounded_box(mount_wing_w, mount_wing_d, lid_t, r = 3);

        // M6 anchor bolt clearance hole (through full thickness)
        translate([hx, hy, -eps])
            cylinder(d = mount_bolt_d, h = lid_t + 2 * eps, $fn = 24);

        // Nut counterbore on the top face (the face that presses against
        // concrete).  Bolt head / nut sits here; depth = mount_cbore_h.
        translate([hx, hy, lid_t - mount_cbore_h])
            cylinder(d = mount_cbore_d, h = mount_cbore_h + eps, $fn = 32);
    }
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

        // Carve out boss interiors that overlap the hollow (keep boss walls)
        // — already handled: bosses are solid cylinders, hull subtracted above
        // carves only the rectangular main body; cylindrical bosses stand proud.
        // (No extra subtraction needed — the boss OD fits within the wall zone.)

        // ── Bottom-wall (Y=0 face) cable gland holes ─────────────────────
        // Five M16 glands evenly spaced across pcb_w, centred on terminal height
        // Spacing: divide pcb_w into 6 equal zones, place glands at zone centres
        cg_spacing = pcb_w / 5;   // ~16 mm between centres across the 80 mm span
        for (i = [0:4]) {
            cg_cx = wall + cg_spacing * i + cg_spacing / 2;
            cg_hole(cg_cx, 0, cg_z_bottom, "y");
        }

        // ── Left-wall (X=0 face) USB-C slot ──────────────────────────────
        // USB-C is at x≈2 mm on PCB, centred roughly at Y mid of left short edge.
        // We centre the slot at the mid-depth of the left wall face.
        usbc_cy = ext_d / 2;      // centred on the short wall
        usbc_cz = pcb_z + pcb_t / 2;
        usbc_slot(usbc_cy, usbc_cz);

        // ── Left-wall programming header cable gland ─────────────────────
        if (prog_gland) {
            // Place it above the USB-C slot, centred in upper half of left wall
            prog_cy = ext_d / 2;
            prog_cz = pcb_top_z + top_clear * 0.55;
            cg_hole(0, prog_cy, prog_cz, "x");
        }

        // ── Right-wall (X=ext_w face) battery cable gland ─────────────────
        // External battery only (single-cell LiPo pigtail).  Omitted for the
        // 2S variant because the pack lives inside the case.
        if (!USE_2S_BATTERY) {
            cg_hole(ext_w, ext_d / 2, ext_h_base / 2, "x");
        }

        // ── 2S battery strap slots ─────────────────────────────────────────
        // Two horizontal slots through the left (X=0) and right (X=ext_w) walls,
        // sized for a 16 mm wide × 3 mm thick nylon strap or velcro band.
        // Centred on the battery mid-height; keeps pack secure when lid is off.
        if (USE_2S_BATTERY) {
            strap_w   = 18;   // slot width  (slightly wider than 16 mm strap)
            strap_h   =  4;   // slot height (slightly taller than 3 mm strap)
            strap_cx  = wall + pcb_w / 2;
            strap_cz  = wall + BATT_2S_H / 2;
            // Left wall (X = 0)
            translate([         -eps, strap_cx - strap_w / 2, strap_cz - strap_h / 2])
                cube([wall + 2 * eps, strap_w, strap_h]);
            // Right wall (X = ext_w)
            translate([ext_w - wall - eps, strap_cx - strap_w / 2, strap_cz - strap_h / 2])
                cube([wall + 2 * eps, strap_w, strap_h]);
        }

        // ── Back-wall (Y=ext_d face): solar cable gland + SMA antenna ────
        // Solar gland: offset left (quarter-width) to leave room for SMA.
        cg_hole(ext_w * solar_cg_x_frac, ext_d, ext_h_base / 2, "y");

        // SMA female bulkhead hole: centred on J3 (U.FL) X position.
        // The U.FL-to-SMA RG178 pigtail (~100 mm) runs from J3 on the PCB
        // to this bulkhead.  An external rubber-duck or whip antenna threads
        // onto the SMA from outside the enclosure.
        if (ext_antenna) {
            translate([sma_x, ext_d, ext_h_base / 2])
                rotate([90, 0, 0])
                    cylinder(d = sma_hole_d, h = wall * 4, center = true, $fn = 48);
        }

        // ── M3 lid screw through-holes in top rim (corner bosses) ─────────
        // These are the clearance holes through the boss top into the insert bore.
        // Drilled from above, so the screw passes through the lid and threads into
        // the insert in the boss.  (The insert bore is already carved in corner_boss.)
        // No additional cut needed here — the lid carries the clearance holes.

    } // end difference (base)

    // ── PCB standoffs (added after difference so they're not hollowed) ──
    for (i = [0:3]) {
        standoff(mh_enc(i)[0], mh_enc(i)[1]);
    }

    // ── 2S battery locating posts ──────────────────────────────────────────
    if (USE_2S_BATTERY) {
        battery_locators_2s();
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
            // Lip inner dimensions match the base interior (pcb_w × pcb_d),
            // outer dimensions = inner + 2*lid_lip_t.
            lip_x = wall - lid_lip_t;
            lip_y = wall - lid_lip_t;
            lip_ow = pcb_w + 2 * lid_lip_t;   // outer width of lip ring
            lip_od = pcb_d + 2 * lid_lip_t;   // outer depth of lip ring
            translate([lip_x, lip_y, -lid_lip])
                difference() {
                    rounded_box(lip_ow, lip_od, lid_lip + eps, r = 2);
                    translate([lid_lip_t, lid_lip_t, -eps])
                        cube([pcb_w, pcb_d, lid_lip + 3 * eps]);
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

    // ── Concrete-lid mounting wings ────────────────────────────────────────
    // Four corner tabs extend beyond the lid footprint; each has an M6
    // anchor-bolt hole and nut counterbore.  The wings sit flush with the
    // top (branding) face and share the same Z origin as the lid plate.
    // Anchor bolt centres (relative to lid corner at 0,0):
    //   BL: (−wing_w/2, −wing_d/2)   BR: (ext_w + wing_w/2, −wing_d/2)
    //   TL: (−wing_w/2, ext_d+wing_d/2)   TR: (ext_w+wing_w/2, ext_d+wing_d/2)
    // → bolt pattern span: (ext_w + mount_wing_w) × (ext_d + mount_wing_d)
    //                     =  107 mm × 82 mm
    if (concrete_mount) {
        mount_wing_tab( 0,     0,     -1, -1);   // bottom-left
        mount_wing_tab( ext_w, 0,     +1, -1);   // bottom-right
        mount_wing_tab( 0,     ext_d, -1, +1);   // top-left
        mount_wing_tab( ext_w, ext_d, +1, +1);   // top-right
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
    base();
}

if (SHOW_LID) {
    // Lift lid above base for assembly view (40 mm separation)
    translate([0, 0, ext_h_base + 40])
        lid();
}

if (SHOW_DRILL_TEMPLATE) {
    // Shown in the XY plane beside the base for preview purposes.
    // Wings extend into negative X/Y so offset it clear of the base model.
    translate([-mount_wing_w - 5, -mount_wing_d - 5, 0])
        drill_template();
}

// ─────────────────────────────────────────────
// --- Bill of materials (hardware per unit) ---
// ─────────────────────────────────────────────
// 4× M3×8 button-head screws (lid)
// 4× M3 heat-set inserts (press into corner boss bores with soldering iron)
// 4× M3×6 self-tapping or machine screws (PCB standoffs — optional; brass inserts preferred)
// 4× M3 brass threaded inserts for PCB standoffs (press-fit, 3 mm OD bore)
// 5× M16 cable glands (bottom wall — sensor/power cables)
// 3× M16 cable glands (left, right, back walls — battery, solar, debug)
// 1× USB-C panel slot (open cutout — add a short rubber grommet for better IP rating)
// 1× SMA female bulkhead connector (back wall, IP67 rated; e.g. Amphenol RF 132289)
// 1× U.FL to SMA female pigtail, ~100 mm, RG178 (e.g. Taoglas CAB.100.07.0100B)
// 1× 2.4 GHz omnidirectional SMA antenna (rubber duck, 2 dBi, e.g. Taoglas FXP73)
// Silicone sealant bead between lid lip and base top rim for IP54 sealing
//
// Additional hardware for USE_2S_BATTERY variant only:
// 1× 2S1P 18650 pack (e.g. CS-ARS200SL, 7.4 V 3400 mAh, ~73×40×22 mm)
// 1× nylon strap or velcro band, 16 mm wide × ≥ 200 mm long (battery retention)
// ⚠ PCB requires charger and LDO rework before connecting 2S pack — see SCAD comments
