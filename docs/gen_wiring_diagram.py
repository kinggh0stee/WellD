#!/usr/bin/env python3
"""Generate WellD wiring diagram as a PNG."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os

# ── Palette ──────────────────────────────────────────────────────────────────
C_RED    = '#c0392b'   # 3.3 V power
C_GND    = '#1a1a2e'   # ground
C_BLUE   = '#1a6fa8'   # ADC / digital signal
C_ORANGE = '#c87722'   # loop supply (separate domain)
C_GREEN  = '#1e8449'   # battery ADC (optional)
C_PCB    = '#1a472a'   # ESP32 board green
C_RES    = '#c9a84c'   # resistor body
C_SENS1  = '#1a5276'   # pressure transducer border
C_SENS2  = '#1e6b40'   # DS18B20 border
C_BAT    = '#626567'   # battery border

# ── Canvas ────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(17, 11))
ax.set_xlim(0, 17)
ax.set_ylim(0, 11)
ax.set_aspect('equal')
ax.axis('off')
fig.patch.set_facecolor('#fafafa')
ax.set_facecolor('#fafafa')

# ── Helpers ───────────────────────────────────────────────────────────────────
def rect(x, y, w, h, fc='white', ec='black', lw=1.5, zo=3, alpha=1.0):
    ax.add_patch(mpatches.Rectangle(
        (x, y), w, h, linewidth=lw, edgecolor=ec,
        facecolor=fc, zorder=zo, alpha=alpha))

def rrect(x, y, w, h, fc='white', ec='black', lw=1.5, zo=3, pad=0.08):
    ax.add_patch(mpatches.FancyBboxPatch(
        (x, y), w, h, boxstyle=f'round,pad={pad}',
        linewidth=lw, edgecolor=ec, facecolor=fc, zorder=zo))

def wire(pts, color, lw=2.0, zo=2, style='-'):
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color=color, lw=lw, ls=style,
            solid_capstyle='round', solid_joinstyle='round', zorder=zo)

def dot(x, y, color, sz=55, zo=6):
    ax.scatter([x], [y], s=sz, color=color, zorder=zo)

def txt(x, y, s, ha='center', va='center', sz=8, color='black',
        bold=False, italic=False, zo=7):
    ax.text(x, y, s, ha=ha, va=va, fontsize=sz, color=color, zorder=zo,
            fontweight='bold' if bold else 'normal',
            fontstyle='italic' if italic else 'normal')

def resistor_v(cx, cy, label, color=C_RES):
    """Vertical resistor: wire stubs above/below a labelled rectangle."""
    w, h = 0.38, 0.82
    rect(cx - w/2, cy - h/2, w, h, fc='#fef9e7', ec=color, lw=1.4, zo=5)
    txt(cx, cy, label, sz=6.2, color=color, bold=True, zo=6)

def resistor_h(cx, cy, label, color=C_RES):
    """Horizontal resistor."""
    w, h = 0.82, 0.32
    rect(cx - w/2, cy - h/2, w, h, fc='#fef9e7', ec=color, lw=1.4, zo=5)
    txt(cx, cy, label, sz=6.2, color=color, bold=True, zo=6)

def gnd(x, y):
    """IEC ground symbol."""
    for i, hw in enumerate([0.24, 0.15, 0.07]):
        yy = y - i * 0.11
        ax.plot([x - hw, x + hw], [yy, yy], color=C_GND, lw=1.8, zorder=5)

def vcc_arrow(x, y, label='+3.3V'):
    ax.annotate('', xy=(x, y + 0.38), xytext=(x, y),
                arrowprops=dict(arrowstyle='->', color=C_RED, lw=1.6), zorder=5)
    txt(x, y + 0.58, label, sz=7, color=C_RED, bold=True)

# ─────────────────────────────────────────────────────────────────────────────
#  ESP32-C6 Board
# ─────────────────────────────────────────────────────────────────────────────
BX, BY, BW, BH = 6.8, 1.6, 3.0, 7.4
rect(BX, BY, BW, BH, fc=C_PCB, ec='#0d2614', lw=3, zo=3)
# Silk-screen text
txt(BX + BW/2, BY + BH/2 + 0.5, 'ESP32-C6', sz=12.5, color='white', bold=True)
txt(BX + BW/2, BY + BH/2 - 0.1, 'Dev Board', sz=8.5, color='#88cc88')
# Small chip rectangle
rect(BX + BW/2 - 0.5, BY + BH/2 - 1.3, 1.0, 0.9, fc='#2e2e2e', ec='#555', lw=1, zo=4)
txt(BX + BW/2, BY + BH/2 - 0.85, 'C6', sz=7, color='#aaa', zo=5)

# ── Left pins ────────────────────────────────────────────────────────────────
STUB = 0.45   # pin stub length
LPX  = BX     # left board edge

pin_y = {
    '3V3':   8.35,
    'GND_L': 7.45,
    'GPIO0': 6.15,
    'GPIO1': 4.85,
}

pin_color = {
    '3V3':   C_RED,
    'GND_L': C_GND,
    'GPIO0': C_BLUE,
    'GPIO1': C_GREEN,
}

pin_label = {
    '3V3':   '3V3',
    'GND_L': 'GND',
    'GPIO0': 'GPIO0\n(ADC CH0)',
    'GPIO1': 'GPIO1\n(ADC CH1)',
}

for key, y in pin_y.items():
    c = pin_color[key]
    ax.plot([LPX - STUB, LPX], [y, y], color=c, lw=2.5, zorder=4)
    dot(LPX - STUB, y, c, sz=28)
    txt(LPX - STUB - 0.08, y, pin_label[key], ha='right', sz=7, color=c, bold=True)

# ── Right pins ────────────────────────────────────────────────────────────────
RPX = BX + BW

pin_y_r = {
    'GPIO4': 7.9,
    'GND_R': 6.95,
}
pin_color_r = {
    'GPIO4': C_BLUE,
    'GND_R': C_GND,
}
pin_label_r = {
    'GPIO4': 'GPIO4\n(1-Wire)',
    'GND_R': 'GND',
}

for key, y in pin_y_r.items():
    c = pin_color_r[key]
    ax.plot([RPX, RPX + STUB], [y, y], color=c, lw=2.5, zorder=4)
    dot(RPX + STUB, y, c, sz=28)
    txt(RPX + STUB + 0.08, y, pin_label_r[key], ha='left', sz=7, color=c, bold=True)

# ─────────────────────────────────────────────────────────────────────────────
#  ① Pressure Transducer
# ─────────────────────────────────────────────────────────────────────────────
TX, TY, TW, TH = 0.6, 5.2, 2.3, 2.2
rect(TX, TY, TW, TH, fc='#d6eaf8', ec=C_SENS1, lw=2.2, zo=3)
txt(TX + TW/2, TY + TH/2 + 0.25, 'Pressure', sz=9, color=C_SENS1, bold=True)
txt(TX + TW/2, TY + TH/2 - 0.2, 'Transducer', sz=9, color=C_SENS1, bold=True)
txt(TX + TW/2, TY + TH/2 - 0.58, '(4–20 mA)', sz=7.5, color=C_SENS1)
# (+) and (–) terminal labels
txt(TX + 0.18, TY + TH - 0.28, '(+)', ha='left', sz=8, color=C_ORANGE, bold=True)
txt(TX + 0.18, TY + 0.28,       '(−)', ha='left', sz=8, color=C_GND,    bold=True)

# Loop supply box above the transducer
LS_CX = TX + TW/2
LS_BY = TY + TH + 0.15
rrect(LS_CX - 0.72, LS_BY, 1.44, 0.68, fc='#fef9e7', ec=C_ORANGE, lw=1.6, zo=3, pad=0.06)
txt(LS_CX, LS_BY + 0.38, 'Loop Supply', sz=7.5, color=C_ORANGE, bold=True)
txt(LS_CX, LS_BY + 0.15, '(9 – 36 V)', sz=7,   color=C_ORANGE)

# Transducer (+) up to loop supply
wire([(TX + 0.32, TY + TH - 0.28),
      (TX + 0.32, TY + TH),
      (LS_CX,     TY + TH),
      (LS_CX,     LS_BY)], C_ORANGE, lw=2)

# Junction node: transducer (−) → shunt top + GPIO0 wire
JX = 4.85
JY = TY + 0.28

# Transducer (–) wire right to junction
wire([(TX + TW, JY), (JX, JY)], C_GND, lw=2)
dot(JX, JY, C_BLUE, sz=55)

# Shunt resistor: junction → GND (vertical)
SHUNT_R_BOT = JY - 1.9
wire([(JX, JY),         (JX, JY - 0.52)],     C_GND, lw=2)
resistor_v(JX, JY - 0.93, '100 Ω\n±1%')
wire([(JX, JY - 1.34),  (JX, SHUNT_R_BOT)],  C_GND, lw=2)
gnd(JX, SHUNT_R_BOT)

# GPIO0 wire: junction up to GPIO0 y, then right to board left pin
GPIO0_Y = pin_y['GPIO0']
wire([(JX, JY),
      (JX, GPIO0_Y),
      (LPX - STUB, GPIO0_Y)], C_BLUE, lw=2)
txt(JX + 0.18, (JY + GPIO0_Y) / 2,
    '0.4 – 2.0 V\n(ADC signal)', ha='left', sz=6.5, color=C_BLUE, italic=True)

# Section label
txt(TX + TW/2, TY + TH + 1.1, '① Pressure Transducer', sz=8.5, color=C_SENS1, bold=True)

# ─────────────────────────────────────────────────────────────────────────────
#  ② DS18B20 Temperature Probe
# ─────────────────────────────────────────────────────────────────────────────
DSX, DSY, DSW, DSH = 12.8, 5.5, 2.4, 2.6
rect(DSX, DSY, DSW, DSH, fc='#d5f5e3', ec=C_SENS2, lw=2.2, zo=3)
txt(DSX + DSW/2, DSY + DSH/2 + 0.5,  'DS18B20',      sz=9,   color=C_SENS2, bold=True)
txt(DSX + DSW/2, DSY + DSH/2 + 0.1,  'Temperature',  sz=8.5, color=C_SENS2)
txt(DSX + DSW/2, DSY + DSH/2 - 0.3,  'Probe',        sz=8.5, color=C_SENS2)

# Pin label stubs on the left side of the DS18B20 box
DS_VCC_Y  = DSY + DSH - 0.35
DS_DATA_Y = DSY + DSH / 2 - 0.1
DS_GND_Y  = DSY + 0.35
DS_LEFT_X = DSX

txt(DS_LEFT_X + 0.15, DS_VCC_Y,  'VCC',  ha='left', sz=7.5, color=C_RED,  bold=True)
txt(DS_LEFT_X + 0.15, DS_DATA_Y, 'DATA', ha='left', sz=7.5, color=C_BLUE, bold=True)
txt(DS_LEFT_X + 0.15, DS_GND_Y,  'GND',  ha='left', sz=7.5, color=C_GND,  bold=True)

# 4.7 kΩ pull-up: VCC symbol → resistor → DATA junction
PU_X    = RPX + STUB + 1.0          # x of pull-up column
PU_VCC_Y = DS_VCC_Y + 0.3
vcc_arrow(PU_X, PU_VCC_Y, '+3.3V')  # arrow points up to VCC label

PU_BOT_Y = DS_DATA_Y               # bottom of pull-up = DATA wire y
wire([(PU_X, PU_VCC_Y),       (PU_X, DS_DATA_Y + 0.62)], C_RED, lw=2)
resistor_v(PU_X, DS_DATA_Y + 0.22, '4.7kΩ')
wire([(PU_X, DS_DATA_Y - 0.18), (PU_X, DS_DATA_Y)],       C_RED, lw=2)

# Junction where pull-up meets DATA wire
dot(PU_X, DS_DATA_Y, C_BLUE, sz=55)

# DATA wire: board GPIO4 → right → pull-up junction → DS18B20
GPIO4_Y = pin_y_r['GPIO4']
wire([(RPX + STUB, GPIO4_Y),
      (PU_X,       GPIO4_Y),
      (PU_X,       DS_DATA_Y),
      (DS_LEFT_X,  DS_DATA_Y)], C_BLUE, lw=2)

# VCC to DS18B20 VCC
VCC_JUNC_X = PU_X + 0.3
wire([(PU_X,        PU_VCC_Y),
      (VCC_JUNC_X,  PU_VCC_Y),
      (VCC_JUNC_X,  DS_VCC_Y),
      (DS_LEFT_X,   DS_VCC_Y)], C_RED, lw=2)
dot(PU_X, PU_VCC_Y, C_RED, sz=40)

# DS18B20 GND
DS_GND_TERM_X = PU_X
DS_GND_TERM_Y = DS_GND_Y - 0.75
wire([(DS_LEFT_X,      DS_GND_Y),
      (DS_GND_TERM_X,  DS_GND_Y),
      (DS_GND_TERM_X,  DS_GND_TERM_Y)], C_GND, lw=2)
gnd(DS_GND_TERM_X, DS_GND_TERM_Y)

# Board GND_R → DS GND
GND_R_Y = pin_y_r['GND_R']
wire([(RPX + STUB,     GND_R_Y),
      (DS_GND_TERM_X + 0.4, GND_R_Y),
      (DS_GND_TERM_X + 0.4, DS_GND_TERM_Y),
      (DS_GND_TERM_X,  DS_GND_TERM_Y)], C_GND, lw=2)
dot(DS_GND_TERM_X, DS_GND_TERM_Y, C_GND, sz=40)

# Section label
txt(DSX + DSW/2, DSY + DSH + 0.42, '② DS18B20 Probe', sz=8.5, color=C_SENS2, bold=True)

# ─────────────────────────────────────────────────────────────────────────────
#  ③ Battery Voltage Divider  (optional)
# ─────────────────────────────────────────────────────────────────────────────
BAT_X, BAT_Y, BAT_W, BAT_H = 0.6, 0.9, 1.8, 1.2
rect(BAT_X, BAT_Y, BAT_W, BAT_H, fc='#fdfefe', ec=C_BAT, lw=1.8, zo=3)
txt(BAT_X + BAT_W/2, BAT_Y + BAT_H/2 + 0.18, 'Battery', sz=8.5, color=C_BAT, bold=True)
txt(BAT_X + BAT_W/2, BAT_Y + BAT_H/2 - 0.22, '(LiPo / AA)', sz=7, color=C_BAT)

BAT_POS_Y = BAT_Y + BAT_H - 0.25
BAT_NEG_Y = BAT_Y + 0.25
BAT_R_X   = BAT_X + BAT_W
txt(BAT_R_X - 0.15, BAT_POS_Y, '(+)', ha='right', sz=7.5, color=C_ORANGE, bold=True)
txt(BAT_R_X - 0.15, BAT_NEG_Y, '(−)', ha='right', sz=7.5, color=C_GND,    bold=True)

# Divider: R1 → junction → R2 → GND
DIV_X       = 3.5      # x of resistor chain right side
R1_CX       = DIV_X - 0.55
JUNC_DIV_X  = DIV_X
JUNC_DIV_Y  = BAT_POS_Y
DIV_GND_Y   = BAT_NEG_Y - 0.45

# Battery (+) → R1 (horizontal)
wire([(BAT_R_X, BAT_POS_Y), (R1_CX - 0.45, BAT_POS_Y)], C_ORANGE, lw=2)
resistor_h(R1_CX, BAT_POS_Y, 'R1\n100kΩ')
wire([(R1_CX + 0.45, BAT_POS_Y), (JUNC_DIV_X, JUNC_DIV_Y)], C_ORANGE, lw=2)
dot(JUNC_DIV_X, JUNC_DIV_Y, C_GREEN, sz=55)

# Junction → R2 → GND (vertical down)
wire([(JUNC_DIV_X, JUNC_DIV_Y),  (JUNC_DIV_X, JUNC_DIV_Y - 0.38)], C_GND, lw=2)
resistor_v(JUNC_DIV_X, JUNC_DIV_Y - 0.79, 'R2\n100kΩ')
wire([(JUNC_DIV_X, JUNC_DIV_Y - 1.2), (JUNC_DIV_X, DIV_GND_Y)], C_GND, lw=2)
gnd(JUNC_DIV_X, DIV_GND_Y)

# Battery (–) → GND
BAT_GND_X = BAT_R_X + 0.3
wire([(BAT_R_X, BAT_NEG_Y), (BAT_GND_X, BAT_NEG_Y), (BAT_GND_X, DIV_GND_Y - 0.05)], C_GND, lw=2)
gnd(BAT_GND_X, DIV_GND_Y - 0.05)

# Junction → GPIO1 (right to board)
GPIO1_Y = pin_y['GPIO1']
wire([(JUNC_DIV_X, JUNC_DIV_Y),
      (LPX - STUB, JUNC_DIV_Y),
      (LPX - STUB, GPIO1_Y)], C_GREEN, lw=2)
txt(JUNC_DIV_X + 0.15, JUNC_DIV_Y + 0.2,
    '~2.1 V\nat full', ha='left', sz=6.5, color=C_GREEN, italic=True)

# Optional badge
rrect(BAT_X - 0.05, BAT_Y - 0.42, 1.9, 0.34, fc='#fef9e7', ec='#e59866', lw=1.3, zo=4, pad=0.05)
txt(BAT_X + BAT_W/2, BAT_Y - 0.25, 'OPTIONAL', sz=7.5, color='#ca6f1e', bold=True)

txt(BAT_X + BAT_W/2 + 0.4, BAT_Y + BAT_H + 0.28,
    '③ Battery Divider', sz=8.5, color=C_BAT, bold=True)

# ─────────────────────────────────────────────────────────────────────────────
#  Title & Legend
# ─────────────────────────────────────────────────────────────────────────────
txt(8.3, 10.65, 'WellD — Sensor Wiring Diagram', sz=15, bold=True, color='#1a252f')
txt(8.3, 10.3,
    'ESP32-C6  ·  4–20 mA Pressure Transducer  ·  DS18B20 Temperature Probe  ·  Battery Monitor (optional)',
    sz=8, color='#5d6d7e')

# Legend box
LEG_X, LEG_Y = 13.4, 1.0
rrect(LEG_X - 0.2, LEG_Y - 0.15, 3.5, 3.0, fc='white', ec='#aaa', lw=1.2, zo=3, pad=0.1)
txt(LEG_X + 1.5, LEG_Y + 2.65, 'Colour Key', sz=8.5, bold=True, color='#2c3e50')
legend = [
    (C_RED,    '3.3 V power rail'),
    (C_ORANGE, 'Loop supply  (9–36 V)'),
    (C_BLUE,   'Data / ADC signal'),
    (C_GND,    'Ground return'),
    (C_GREEN,  'Battery ADC  (optional)'),
]
for i, (c, lbl) in enumerate(legend):
    y = LEG_Y + 2.25 - i * 0.48
    ax.plot([LEG_X, LEG_X + 0.55], [y, y], color=c, lw=2.8, solid_capstyle='round', zorder=5)
    dot(LEG_X + 0.55, y, c, sz=35, zo=6)
    txt(LEG_X + 0.72, y, lbl, ha='left', sz=7.5, color='#2c3e50')

# Note at the bottom
txt(8.3, 0.35,
    'Default GPIO assignments shown. Change via sdkconfig.defaults.local before building.',
    sz=7.5, color='#888', italic=True)

# ─────────────────────────────────────────────────────────────────────────────
out = os.path.join(os.path.dirname(__file__), 'wiring_diagram.png')
plt.savefig(out, dpi=150, bbox_inches='tight', facecolor='#fafafa')
print(f'Saved → {out}')
