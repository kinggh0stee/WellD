#!/usr/bin/env python3
"""Generate WellD wiring diagram as a PNG."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os

# ── Palette ───────────────────────────────────────────────────────────────────
C_RED    = '#c0392b'   # 3.3 V power
C_GND    = '#1a1a2e'   # ground
C_BLUE   = '#1a6fa8'   # ADC / digital signal
C_ORANGE = '#c87722'   # loop supply (separate high-voltage domain)
C_GREEN  = '#1e8449'   # battery ADC (optional)
C_PCB    = '#1a472a'   # ESP32 board green
C_RES    = '#c9a84c'   # resistor body
C_SENS1  = '#1a5276'   # pressure transducer
C_SENS2  = '#1e6b40'   # DS18B20
C_BAT    = '#626567'   # battery

# ── Canvas ────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(17, 11))
ax.set_xlim(0, 17)
ax.set_ylim(0, 11)
ax.set_aspect('equal')
ax.axis('off')
fig.patch.set_facecolor('#fafafa')
ax.set_facecolor('#fafafa')

# ── Helpers ───────────────────────────────────────────────────────────────────
def rect(x, y, w, h, fc='white', ec='black', lw=1.5, zo=3):
    ax.add_patch(mpatches.Rectangle(
        (x, y), w, h, linewidth=lw, edgecolor=ec, facecolor=fc, zorder=zo))

def rrect(x, y, w, h, fc='white', ec='black', lw=1.5, zo=3, pad=0.08):
    ax.add_patch(mpatches.FancyBboxPatch(
        (x, y), w, h, boxstyle=f'round,pad={pad}',
        linewidth=lw, edgecolor=ec, facecolor=fc, zorder=zo))

def wire(pts, color, lw=2.0, zo=2):
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color=color, lw=lw,
            solid_capstyle='round', solid_joinstyle='round', zorder=zo)

def dot(x, y, color, sz=55, zo=6):
    ax.scatter([x], [y], s=sz, color=color, zorder=zo)

def txt(x, y, s, ha='center', va='center', sz=8, color='black',
        bold=False, italic=False, zo=7):
    ax.text(x, y, s, ha=ha, va=va, fontsize=sz, color=color, zorder=zo,
            fontweight='bold' if bold else 'normal',
            fontstyle='italic' if italic else 'normal')

def resistor_v(cx, cy, label):
    w, h = 0.38, 0.82
    rect(cx - w/2, cy - h/2, w, h, fc='#fef9e7', ec=C_RES, lw=1.4, zo=5)
    txt(cx, cy, label, sz=6.2, color=C_RES, bold=True, zo=6)

def resistor_h(cx, cy, label):
    w, h = 0.82, 0.32
    rect(cx - w/2, cy - h/2, w, h, fc='#fef9e7', ec=C_RES, lw=1.4, zo=5)
    txt(cx, cy, label, sz=6.2, color=C_RES, bold=True, zo=6)

def gnd(x, y):
    """IEC earth symbol — three decreasing horizontal bars."""
    for i, hw in enumerate([0.24, 0.15, 0.07]):
        ax.plot([x - hw, x + hw], [y - i * 0.11, y - i * 0.11],
                color=C_GND, lw=1.8, zorder=5)

def vcc(x, y, label='+3.3V'):
    """VCC power symbol: upward arrow + label above tip.
    The wire connection point is at (x, y) — the arrow base."""
    ax.annotate('', xy=(x, y + 0.35), xytext=(x, y),
                arrowprops=dict(arrowstyle='->', color=C_RED, lw=1.8), zorder=5)
    txt(x, y + 0.56, label, sz=7, color=C_RED, bold=True)

# ─────────────────────────────────────────────────────────────────────────────
#  ESP32-C6 board
# ─────────────────────────────────────────────────────────────────────────────
BX, BY, BW, BH = 6.8, 1.6, 3.0, 7.4
rect(BX, BY, BW, BH, fc=C_PCB, ec='#0d2614', lw=3, zo=3)
txt(BX + BW/2, BY + BH/2 + 0.5, 'ESP32-C6', sz=12.5, color='white', bold=True)
txt(BX + BW/2, BY + BH/2 - 0.1, 'Dev Board', sz=8.5, color='#88cc88')
rect(BX + BW/2 - 0.5, BY + BH/2 - 1.3, 1.0, 0.9, fc='#2e2e2e', ec='#555', lw=1, zo=4)
txt(BX + BW/2, BY + BH/2 - 0.85, 'C6', sz=7, color='#aaa', zo=5)

STUB = 0.45
LPX  = BX          # left board edge
RPX  = BX + BW     # right board edge

# Left pins: only the two that are actually wired in this diagram.
# 3V3 and GND are supplied via the board but shown with power symbols (VCC/GND)
# throughout the diagram rather than as routed wires — standard schematic practice.
Y_GPIO0 = 6.15
Y_GPIO1 = 4.85

for y, lbl, c in [(Y_GPIO0, 'GPIO0\n(ADC CH0)', C_BLUE),
                   (Y_GPIO1, 'GPIO1\n(ADC CH1)', C_GREEN)]:
    ax.plot([LPX - STUB, LPX], [y, y], color=c, lw=2.5, zorder=4)
    dot(LPX - STUB, y, c, sz=28)
    txt(LPX - STUB - 0.08, y, lbl, ha='right', sz=7, color=c, bold=True)

# Right pins
Y_GPIO4 = 7.9
Y_GND_R = 6.95

for y, lbl, c in [(Y_GPIO4, 'GPIO4\n(1-Wire)', C_BLUE),
                   (Y_GND_R, 'GND', C_GND)]:
    ax.plot([RPX, RPX + STUB], [y, y], color=c, lw=2.5, zorder=4)
    dot(RPX + STUB, y, c, sz=28)
    txt(RPX + STUB + 0.08, y, lbl, ha='left', sz=7, color=c, bold=True)

# ─────────────────────────────────────────────────────────────────────────────
#  ① Pressure transducer  (4–20 mA current loop)
# ─────────────────────────────────────────────────────────────────────────────
TX, TY, TW, TH = 0.6, 5.2, 2.3, 2.2
rect(TX, TY, TW, TH, fc='#d6eaf8', ec=C_SENS1, lw=2.2, zo=3)
txt(TX + TW/2, TY + TH/2 + 0.25, 'Pressure',   sz=9,   color=C_SENS1, bold=True)
txt(TX + TW/2, TY + TH/2 - 0.2,  'Transducer', sz=9,   color=C_SENS1, bold=True)
txt(TX + TW/2, TY + TH/2 - 0.58, '(4–20 mA)',  sz=7.5, color=C_SENS1)
txt(TX + 0.18, TY + TH - 0.28, '(+)', ha='left', sz=8, color=C_ORANGE, bold=True)
txt(TX + 0.18, TY + 0.28,       '(−)', ha='left', sz=8, color=C_GND,    bold=True)

# Loop supply box (separate supply rail — never touches ESP32 pins)
LS_CX = TX + TW/2
LS_BY = TY + TH + 0.15
rrect(LS_CX - 0.72, LS_BY, 1.44, 0.68, fc='#fef9e7', ec=C_ORANGE, lw=1.6, zo=3, pad=0.06)
txt(LS_CX, LS_BY + 0.38, 'Loop Supply', sz=7.5, color=C_ORANGE, bold=True)
txt(LS_CX, LS_BY + 0.15, '(9 – 36 V)',  sz=7,   color=C_ORANGE)

# Transducer (+) wire up to loop supply
wire([(TX + 0.32, TY + TH - 0.28),
      (TX + 0.32, TY + TH),
      (LS_CX,     TY + TH),
      (LS_CX,     LS_BY)], C_ORANGE, lw=2)

# Junction node — where transducer (−), shunt top, and GPIO0 all meet.
# This node sits at 0.4–2.0 V (I × R), NOT at ground.
JX = 4.85
JY = TY + 0.28   # = 5.48

# FIX: wire from transducer (−) to junction is BLUE — it is a signal node,
# not ground. Drawing it black (GND colour) was misleading.
wire([(TX + TW, JY), (JX, JY)], C_BLUE, lw=2)
dot(JX, JY, C_BLUE, sz=55)

# Shunt resistor: junction → 100 Ω → GND  (current flows to ground here)
SHUNT_BOT = JY - 1.9
wire([(JX, JY),        (JX, JY - 0.52)],   C_GND, lw=2)
resistor_v(JX, JY - 0.93, '100 Ω\n±1%')
wire([(JX, JY - 1.34), (JX, SHUNT_BOT)],   C_GND, lw=2)
gnd(JX, SHUNT_BOT)

# GPIO0 wire: junction → up → right → board pin
wire([(JX, JY), (JX, Y_GPIO0), (LPX - STUB, Y_GPIO0)], C_BLUE, lw=2)
txt(JX + 0.18, (JY + Y_GPIO0) / 2,
    '0.4–2.0 V\n(ADC signal)', ha='left', sz=6.5, color=C_BLUE, italic=True)

txt(TX + TW/2, TY + TH + 1.05, '① Pressure Transducer', sz=8.5, color=C_SENS1, bold=True)

# ─────────────────────────────────────────────────────────────────────────────
#  ② DS18B20 temperature probe
#
#  Correct pull-up topology:
#    +3.3V ──── 4.7 kΩ ──┬──── DS18B20 DATA
#                         │
#                       GPIO4 ──────────────── (same node, direct)
#
#  The GPIO4 path and the pull-up resistor must be at DIFFERENT x positions
#  so they are visually distinct branches — not one series path.
# ─────────────────────────────────────────────────────────────────────────────
DSX, DSY, DSW, DSH = 12.8, 5.5, 2.4, 2.6
rect(DSX, DSY, DSW, DSH, fc='#d5f5e3', ec=C_SENS2, lw=2.2, zo=3)
txt(DSX + DSW/2, DSY + DSH/2 + 0.5,  'DS18B20',      sz=9,   color=C_SENS2, bold=True)
txt(DSX + DSW/2, DSY + DSH/2 + 0.1,  'Temperature',  sz=8.5, color=C_SENS2)
txt(DSX + DSW/2, DSY + DSH/2 - 0.3,  'Probe',        sz=8.5, color=C_SENS2)

DS_VCC_Y  = DSY + DSH - 0.35   # = 7.75
DS_DATA_Y = DSY + DSH / 2 - 0.1  # = 6.7
DS_GND_Y  = DSY + 0.35         # = 5.85

txt(DSX + 0.15, DS_VCC_Y,  'VCC',  ha='left', sz=7.5, color=C_RED,  bold=True)
txt(DSX + 0.15, DS_DATA_Y, 'DATA', ha='left', sz=7.5, color=C_BLUE, bold=True)
txt(DSX + 0.15, DS_GND_Y,  'GND',  ha='left', sz=7.5, color=C_GND,  bold=True)

# GPIO4 route: right stub → turn down at x=10.65 → horizontal to DS18B20 DATA.
# This path has NO resistor in it — GPIO4 connects directly to the DATA line.
GPIO4_TURN_X = RPX + STUB + 0.4   # = 10.65
wire([(RPX + STUB,    Y_GPIO4),
      (GPIO4_TURN_X,  Y_GPIO4),
      (GPIO4_TURN_X,  DS_DATA_Y),
      (DSX,           DS_DATA_Y)], C_BLUE, lw=2)

# Pull-up: +3.3V → 4.7 kΩ → junction on DATA wire.
# The junction is on the HORIZONTAL segment (between the turn and the DS18B20),
# at a different x than the GPIO4 turn so the two branches are visually separate.
PU_JX = 11.5          # x of pull-up column — distinct from GPIO4_TURN_X
PU_JY = DS_DATA_Y     # = 6.7, sits on the horizontal DATA wire

dot(PU_JX, PU_JY, C_BLUE, sz=55)             # junction dot on DATA wire

# Vertical pull-up branch: DATA wire → resistor → +3.3V symbol (upward)
wire([(PU_JX, PU_JY),      (PU_JX, PU_JY + 0.45)], C_RED, lw=2)
resistor_v(PU_JX, PU_JY + 0.86, '4.7 kΩ')
wire([(PU_JX, PU_JY + 1.27), (PU_JX, PU_JY + 1.55)], C_RED, lw=2)
vcc(PU_JX, PU_JY + 1.55, '+3.3V')            # vcc() arrow base = wire end

# DS18B20 VCC: separate +3.3V symbol above the box top, short wire in.
VCC_DS_X   = DSX + 0.7
VCC_DS_BASE = DSY + DSH + 0.18               # = 8.28, just above box top (8.1)
vcc(VCC_DS_X, VCC_DS_BASE, '+3.3V')
wire([(VCC_DS_X, VCC_DS_BASE),
      (VCC_DS_X, DS_VCC_Y),
      (DSX,      DS_VCC_Y)], C_RED, lw=2)

# DS18B20 GND: short wire left to a GND symbol.
# The board GND_R stub (already labelled "GND") is the source; GND symbols
# throughout the diagram share the same net by convention.
DS_GND_OUT_X = DSX - 0.5
wire([(DSX,          DS_GND_Y),
      (DS_GND_OUT_X, DS_GND_Y),
      (DS_GND_OUT_X, DS_GND_Y - 0.35)], C_GND, lw=2)
gnd(DS_GND_OUT_X, DS_GND_Y - 0.35)

txt(DSX + DSW/2, DSY + DSH + 0.95, '② DS18B20 Probe', sz=8.5, color=C_SENS2, bold=True)

# ─────────────────────────────────────────────────────────────────────────────
#  ③ Battery voltage divider  (optional)
#
#  Correct voltage divider topology:
#    Battery (+) ──── R1 ──┬──── GPIO1 (ADC reads mid-point)
#                          │
#                          R2
#                          │
#                         GND
# ─────────────────────────────────────────────────────────────────────────────
BAT_X, BAT_Y, BAT_W, BAT_H = 0.6, 0.9, 1.8, 1.2
rect(BAT_X, BAT_Y, BAT_W, BAT_H, fc='#fdfefe', ec=C_BAT, lw=1.8, zo=3)
txt(BAT_X + BAT_W/2, BAT_Y + BAT_H/2 + 0.18, 'Battery',     sz=8.5, color=C_BAT, bold=True)
txt(BAT_X + BAT_W/2, BAT_Y + BAT_H/2 - 0.22, '(LiPo / AA)', sz=7,   color=C_BAT)

BAT_POS_Y = BAT_Y + BAT_H - 0.25   # = 1.85
BAT_NEG_Y = BAT_Y + 0.25           # = 1.15
BAT_R_X   = BAT_X + BAT_W          # = 2.4
txt(BAT_R_X - 0.15, BAT_POS_Y, '(+)', ha='right', sz=7.5, color=C_ORANGE, bold=True)
txt(BAT_R_X - 0.15, BAT_NEG_Y, '(−)', ha='right', sz=7.5, color=C_GND,    bold=True)

R1_CX      = 3.15   # centre of R1
JUNC_DIV_X = 3.7    # mid-point node (between R1 and R2)
JUNC_DIV_Y = BAT_POS_Y

# Battery (+) → R1 (horizontal) → mid-point junction
wire([(BAT_R_X, BAT_POS_Y), (R1_CX - 0.45, BAT_POS_Y)], C_ORANGE, lw=2)
resistor_h(R1_CX, BAT_POS_Y, 'R1\n100kΩ')
wire([(R1_CX + 0.45, BAT_POS_Y), (JUNC_DIV_X, JUNC_DIV_Y)], C_ORANGE, lw=2)
dot(JUNC_DIV_X, JUNC_DIV_Y, C_GREEN, sz=55)

# Mid-point → R2 (vertical) → GND
DIV_GND_Y = BAT_NEG_Y - 0.45
wire([(JUNC_DIV_X, JUNC_DIV_Y),        (JUNC_DIV_X, JUNC_DIV_Y - 0.38)], C_GND, lw=2)
resistor_v(JUNC_DIV_X, JUNC_DIV_Y - 0.79, 'R2\n100kΩ')
wire([(JUNC_DIV_X, JUNC_DIV_Y - 1.20), (JUNC_DIV_X, DIV_GND_Y)],         C_GND, lw=2)
gnd(JUNC_DIV_X, DIV_GND_Y)

# Battery (−) → GND
BAT_GND_X = BAT_R_X + 0.28
wire([(BAT_R_X, BAT_NEG_Y), (BAT_GND_X, BAT_NEG_Y), (BAT_GND_X, DIV_GND_Y - 0.05)], C_GND, lw=2)
gnd(BAT_GND_X, DIV_GND_Y - 0.05)

# Mid-point → GPIO1  (green = ADC reading of scaled battery voltage)
wire([(JUNC_DIV_X, JUNC_DIV_Y),
      (LPX - STUB,  JUNC_DIV_Y),
      (LPX - STUB,  Y_GPIO1)], C_GREEN, lw=2)
txt(JUNC_DIV_X + 0.15, JUNC_DIV_Y + 0.2,
    '~2.1 V at full', ha='left', sz=6.5, color=C_GREEN, italic=True)

rrect(BAT_X - 0.05, BAT_Y - 0.42, 1.9, 0.34, fc='#fef9e7', ec='#e59866', lw=1.3, zo=4, pad=0.05)
txt(BAT_X + BAT_W/2, BAT_Y - 0.25, 'OPTIONAL', sz=7.5, color='#ca6f1e', bold=True)
txt(BAT_X + BAT_W/2, BAT_Y + BAT_H + 0.28, '③ Battery Divider', sz=8.5, color=C_BAT, bold=True)

# ─────────────────────────────────────────────────────────────────────────────
#  Title, note, and legend
# ─────────────────────────────────────────────────────────────────────────────
txt(8.3, 10.65, 'WellD — Sensor Wiring Diagram', sz=15, bold=True, color='#1a252f')
txt(8.3, 10.3,
    'ESP32-C6  ·  4–20 mA Pressure Transducer  ·  DS18B20 Temperature Probe  ·  Battery Monitor (optional)',
    sz=8, color='#5d6d7e')
txt(8.3, 0.35,
    'GND symbols share one net — connect all to the board GND pin. '
    'VCC symbols (+3.3V) connect to the board 3V3 pin.',
    sz=7, color='#888', italic=True)

LEG_X, LEG_Y = 13.5, 1.0
rrect(LEG_X - 0.2, LEG_Y - 0.15, 3.3, 3.1, fc='white', ec='#aaa', lw=1.2, zo=3, pad=0.1)
txt(LEG_X + 1.4, LEG_Y + 2.75, 'Colour Key', sz=8.5, bold=True, color='#2c3e50')
for i, (c, lbl) in enumerate([
    (C_RED,    '3.3 V power  (+3.3V symbols)'),
    (C_ORANGE, 'Loop supply  (9–36 V)'),
    (C_BLUE,   'Signal / ADC node'),
    (C_GND,    'Ground  (GND symbols)'),
    (C_GREEN,  'Battery ADC  (optional)'),
]):
    y = LEG_Y + 2.28 - i * 0.50
    ax.plot([LEG_X, LEG_X + 0.5], [y, y], color=c, lw=2.8,
            solid_capstyle='round', zorder=5)
    dot(LEG_X + 0.5, y, c, sz=32, zo=6)
    txt(LEG_X + 0.68, y, lbl, ha='left', sz=7.2, color='#2c3e50')

# ─────────────────────────────────────────────────────────────────────────────
out = os.path.join(os.path.dirname(__file__), 'wiring_diagram.png')
plt.savefig(out, dpi=150, bbox_inches='tight', facecolor='#fafafa')
print(f'Saved → {out}')
