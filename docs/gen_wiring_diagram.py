#!/usr/bin/env python3
"""WellD wiring diagram — professional redesign."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os

# ── Canvas ────────────────────────────────────────────────────────────────────
FIG_W, FIG_H = 22, 14
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(0, FIG_W)
ax.set_ylim(0, FIG_H)
ax.set_aspect('equal')
ax.axis('off')
fig.patch.set_facecolor('#ffffff')
ax.set_facecolor('#ffffff')

# ── Palette ───────────────────────────────────────────────────────────────────
C_PWR  = '#b71c1c'   # +3.3 V  (dark red)
C_GND  = '#1a237e'   # ground  (dark navy)
C_SIG  = '#0277bd'   # signal / ADC node  (blue)
C_LOOP = '#bf360c'   # loop supply — separate high-voltage domain  (dark orange-red)
C_BATT = '#1b5e20'   # battery ADC (optional)  (dark green)
C_PCB  = '#2e7d32'   # board fill
C_ANN  = '#546e7a'   # annotation text  (steel grey)

LW   = 2.2   # standard wire width
STUB = 0.55  # board pin stub length

# ── Drawing helpers ───────────────────────────────────────────────────────────
def box(x, y, w, h, fc='#fafafa', ec='#455a64', lw=1.8, zo=3):
    ax.add_patch(mpatches.Rectangle((x, y), w, h,
        lw=lw, ec=ec, fc=fc, zorder=zo))

def rbox(x, y, w, h, fc='#fafafa', ec='#455a64', lw=1.8, zo=3, r=0.1):
    ax.add_patch(mpatches.FancyBboxPatch((x, y), w, h,
        boxstyle=f'round,pad={r}', lw=lw, ec=ec, fc=fc, zorder=zo))

def wire(pts, c, lw=LW, zo=2):
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color=c, lw=lw,
            solid_capstyle='round', solid_joinstyle='round', zorder=zo)

def dot(x, y, c, sz=72, zo=6):
    ax.scatter([x], [y], s=sz, color=c, zorder=zo)

def t(x, y, s, ha='center', va='center', sz=9, c='#212121',
      bold=False, italic=False, zo=8):
    ax.text(x, y, s, ha=ha, va=va, fontsize=sz, color=c, zorder=zo,
            fontweight='bold' if bold else 'normal',
            fontstyle='italic' if italic else 'normal')

def ann(x, y, s, ha='center', c=C_ANN):
    """Annotation label — italic, grey, never placed on a wire path."""
    t(x, y, s, ha=ha, sz=8, c=c, italic=True)

def resistor_v(cx, cy, val):
    """Vertical IEC resistor. Value label sits to the right, clear of wire paths."""
    W, H = 0.44, 0.95
    box(cx - W/2, cy - H/2, W, H, fc='#fff9c4', ec='#f57f17', lw=1.6, zo=5)
    t(cx + W/2 + 0.12, cy, val, ha='left', sz=8.5, c='#4e342e', bold=True, zo=6)

def resistor_h(cx, cy, val):
    """Horizontal IEC resistor. Value label sits above, clear of wire paths."""
    W, H = 0.95, 0.44
    box(cx - W/2, cy - H/2, W, H, fc='#fff9c4', ec='#f57f17', lw=1.6, zo=5)
    t(cx, cy + H/2 + 0.18, val, ha='center', sz=8.5, c='#4e342e', bold=True, zo=6)

def gnd_sym(x, y):
    """IEC earth/ground symbol — three decreasing horizontal bars."""
    for i, hw in enumerate([0.30, 0.19, 0.09]):
        ax.plot([x - hw, x + hw], [y - i * 0.14, y - i * 0.14],
                color=C_GND, lw=2.1, zorder=5)

def vcc_sym(x, y, lbl='+3.3V'):
    """VCC symbol: upward-pointing arrow + label above tip.
    Wire connection point is at the arrow BASE (x, y)."""
    ax.annotate('', xy=(x, y + 0.42), xytext=(x, y),
                arrowprops=dict(arrowstyle='->', color=C_PWR, lw=2.2), zorder=5)
    t(x, y + 0.68, lbl, sz=8.5, c=C_PWR, bold=True)

def pin_L(bx, y, lbl, c):
    """Left-side board pin stub with label to the left."""
    ax.plot([bx - STUB, bx], [y, y], color=c, lw=2.8, zorder=4)
    ax.add_patch(mpatches.Rectangle((bx - STUB - 0.07, y - 0.07), 0.14, 0.14,
        fc=c, ec='white', lw=0.8, zorder=5))
    t(bx - STUB - 0.15, y, lbl, ha='right', sz=8.5, c=c, bold=True)

def pin_R(bx, y, lbl, c):
    """Right-side board pin stub with label to the right."""
    ax.plot([bx, bx + STUB], [y, y], color=c, lw=2.8, zorder=4)
    ax.add_patch(mpatches.Rectangle((bx + STUB - 0.07, y - 0.07), 0.14, 0.14,
        fc=c, ec='white', lw=0.8, zorder=5))
    t(bx + STUB + 0.15, y, lbl, ha='left', sz=8.5, c=c, bold=True)

# ─────────────────────────────────────────────────────────────────────────────
#  ESP32-C6 Dev Board
# ─────────────────────────────────────────────────────────────────────────────
BX, BY, BW, BH = 9.0, 2.5, 3.2, 9.0
box(BX, BY, BW, BH, fc=C_PCB, ec='#1b5e20', lw=3.2, zo=3)
t(BX + BW/2, BY + BH * 0.64, 'ESP32-C6',  sz=14, c='white', bold=True)
t(BX + BW/2, BY + BH * 0.54, 'Dev Board', sz=9.5, c='#a5d6a7')
# Chip silkscreen
box(BX + BW/2 - 0.6, BY + BH * 0.25, 1.2, 1.0, fc='#1c1c1c', ec='#555', lw=1, zo=4)
t(BX + BW/2, BY + BH * 0.33, 'C6', sz=8.5, c='#9e9e9e', zo=5)

LPX = BX            # left board edge
RPX = BX + BW       # right board edge

# Left pins — only those wired in this diagram
Y_GPIO0 = 9.5        # pressure transducer ADC
Y_GPIO1 = 5.5        # battery ADC (optional)
pin_L(LPX, Y_GPIO0, 'GPIO0  (ADC CH0)', C_SIG)
pin_L(LPX, Y_GPIO1, 'GPIO1  (ADC CH1)', C_BATT)

# Right pins
Y_GPIO4 = 9.8        # DS18B20 1-Wire data
Y_GND_R = 8.5        # DS18B20 GND supply
pin_R(RPX, Y_GPIO4, 'GPIO4  (1-Wire)', C_SIG)
pin_R(RPX, Y_GND_R, 'GND',             C_GND)

# ─────────────────────────────────────────────────────────────────────────────
#  ① Pressure Transducer  (4–20 mA current loop)
# ─────────────────────────────────────────────────────────────────────────────
TX, TY, TW, TH = 0.7, 8.0, 2.9, 2.1
box(TX, TY, TW, TH, fc='#e3f2fd', ec='#0d47a1', lw=2.4, zo=3)
t(TX + TW/2, TY + TH/2 + 0.32, 'Pressure',   sz=10.5, c='#0d47a1', bold=True)
t(TX + TW/2, TY + TH/2 - 0.13, 'Transducer', sz=10.5, c='#0d47a1', bold=True)
t(TX + TW/2, TY + TH/2 - 0.60, '(4–20 mA)', sz=8.5,  c='#1565c0')
# Terminal markers on the component box edges
t(TX + 0.20, TY + TH - 0.32, '(+)', ha='left', sz=9.5, c=C_LOOP, bold=True)
t(TX + 0.20, TY +       0.32, '(−)', ha='left', sz=9.5, c='#37474f', bold=True)

# Loop supply — separate power domain, different colour
LS_CX  = TX + TW / 2
LS_BOT = TY + TH + 0.22
rbox(LS_CX - 1.0, LS_BOT, 2.0, 0.90,
     fc='#fff3e0', ec=C_LOOP, lw=2.0, zo=3, r=0.08)
t(LS_CX, LS_BOT + 0.57, 'Loop Supply',   sz=9,   c=C_LOOP, bold=True)
t(LS_CX, LS_BOT + 0.22, '(9 – 36 V DC)', sz=8.5, c=C_LOOP)

# Transducer (+) → loop supply
TRANS_POS_Y = TY + TH - 0.32
wire([(TX + 0.38, TRANS_POS_Y),
      (TX + 0.38, TY + TH),
      (LS_CX,     TY + TH),
      (LS_CX,     LS_BOT)], C_LOOP)

# ── Signal junction node: transducer (−), shunt top, GPIO0 wire ──────────────
# This node sits at 0.4–2.0 V (= I × R_shunt). It is NOT ground.
JX = 6.5
JY = TY + 0.32   # = 8.32

# Transducer (−) → junction.  BLUE because this is the ADC signal node.
wire([(TX + TW, JY), (JX, JY)], C_SIG)
dot(JX, JY, C_SIG)

# Shunt: junction → 100 Ω → GND  (black — current returns to ground here)
SHUNT_GND_Y = JY - 2.6
wire([(JX, JY),          (JX, JY - 0.58)],        C_GND)
resistor_v(JX, JY - 1.08, '100 Ω  ±1 %')
wire([(JX, JY - 1.58),   (JX, SHUNT_GND_Y)],      C_GND)
gnd_sym(JX, SHUNT_GND_Y)

# GPIO0 wire: junction → up to GPIO0 row → right to board pin stub end
#   Route goes UP first, then RIGHT — label sits above the horizontal segment.
GPIO0_STUB_END = LPX - STUB   # = 8.45
wire([(JX, JY),
      (JX, Y_GPIO0),
      (GPIO0_STUB_END, Y_GPIO0)], C_SIG)

# Annotation above the horizontal wire — no overlap with wire path
ann((JX + GPIO0_STUB_END) / 2, Y_GPIO0 + 0.35,
    '0.4 – 2.0 V   (ADC reads voltage across shunt)')

t(TX + TW/2, TY + TH + 1.42, '① Pressure Transducer', sz=10, c='#0d47a1', bold=True)

# ─────────────────────────────────────────────────────────────────────────────
#  ② DS18B20 Temperature Probe
#
#  Pull-up topology (correct):
#
#          +3.3V
#            │
#          4.7 kΩ          ← pull-up: separate branch from VCC to DATA
#            │
#  GPIO4 ───┬──── DS18B20 DATA     ← GPIO4 connects directly, no resistor
#        junction dot
# ─────────────────────────────────────────────────────────────────────────────
DSX, DSY, DSW, DSH = 15.5, 7.6, 3.5, 2.7
box(DSX, DSY, DSW, DSH, fc='#e8f5e9', ec='#1b5e20', lw=2.4, zo=3)
t(DSX + DSW/2, DSY + DSH/2 + 0.52, 'DS18B20',      sz=10.5, c='#1b5e20', bold=True)
t(DSX + DSW/2, DSY + DSH/2 + 0.10, 'Temperature',  sz=9.5,  c='#2e7d32')
t(DSX + DSW/2, DSY + DSH/2 - 0.32, 'Probe',        sz=9.5,  c='#2e7d32')

DS_VCC_Y  = DSY + DSH - 0.40   # = 9.90
DS_DATA_Y = DSY + DSH / 2      # = 8.95
DS_GND_Y  = DSY + 0.40         # = 8.00

# Pin labels inside the box, flush to the left edge
t(DSX + 0.22, DS_VCC_Y,  'VCC',  ha='left', sz=9, c=C_PWR, bold=True)
t(DSX + 0.22, DS_DATA_Y, 'DATA', ha='left', sz=9, c=C_SIG, bold=True)
t(DSX + 0.22, DS_GND_Y,  'GND',  ha='left', sz=9, c=C_GND, bold=True)

# GPIO4 route: stub end → right (short) → turn down → right to DS18B20 DATA
# The turn is placed well to the right of the board so wires don't crowd the
# board edge.  GPIO4 connects DIRECTLY to DATA — no resistor in this path.
GPIO4_TURN_X = RPX + STUB + 0.65   # = 13.25
wire([(RPX + STUB,   Y_GPIO4),
      (GPIO4_TURN_X, Y_GPIO4),
      (GPIO4_TURN_X, DS_DATA_Y),
      (DSX,          DS_DATA_Y)], C_SIG)

# Pull-up: junction on the DATA wire → 4.7 kΩ → +3.3V
# Junction at a DIFFERENT x than the GPIO4 turn so it reads as a distinct
# branch, not as a resistor in series with GPIO4.
PU_JX = 14.5   # between GPIO4_TURN_X (13.25) and DSX (15.5)
PU_JY = DS_DATA_Y

dot(PU_JX, PU_JY, C_SIG)   # junction dot on DATA wire

wire([(PU_JX, PU_JY),        (PU_JX, PU_JY + 0.55)], C_PWR)
resistor_v(PU_JX, PU_JY + 1.08, '4.7 kΩ')
wire([(PU_JX, PU_JY + 1.60), (PU_JX, PU_JY + 1.95)], C_PWR)
vcc_sym(PU_JX, PU_JY + 1.95, '+3.3V')

# DS18B20 VCC: independent +3.3V symbol, short wire into box
VCC_DS_X   = DSX + DSW * 0.38   # = 16.83
VCC_DS_BOT = DSY + DSH + 0.22   # just above box top = 10.52
vcc_sym(VCC_DS_X, VCC_DS_BOT, '+3.3V')
wire([(VCC_DS_X, VCC_DS_BOT),
      (VCC_DS_X, DS_VCC_Y),
      (DSX,      DS_VCC_Y)], C_PWR)

# DS18B20 GND + board GND_R: both meet at a junction node to the left of the box.
# Route board GND_R down and across — chosen to avoid crossing the signal wires.
GND_JUNC_X = 14.3
GND_JUNC_Y = DS_GND_Y   # = 8.00

wire([(DSX,        DS_GND_Y),
      (GND_JUNC_X, DS_GND_Y),
      (GND_JUNC_X, DS_GND_Y - 0.48)], C_GND)
gnd_sym(GND_JUNC_X, DS_GND_Y - 0.48)

# Board GND_R wire to DS18B20 GND junction
# Route: right from stub → down below DATA wire → left to junction
GND_R_TURN_X = RPX + STUB + 0.28   # = 13.03  (to the right of board edge)
wire([(RPX + STUB,   Y_GND_R),       # (13.03–, 8.5)
      (GND_R_TURN_X, Y_GND_R),       # go right a bit
      (GND_R_TURN_X, GND_JUNC_Y),    # turn down to GND_JUNC_Y
      (GND_JUNC_X,   GND_JUNC_Y)], C_GND)  # go right to junction
dot(GND_JUNC_X, GND_JUNC_Y, C_GND)

t(DSX + DSW/2, DSY + DSH + 1.32, '② DS18B20 Temperature Probe',
  sz=10, c='#1b5e20', bold=True)

# ─────────────────────────────────────────────────────────────────────────────
#  ③ Battery Voltage Divider  (optional)
# ─────────────────────────────────────────────────────────────────────────────
BAT_X, BAT_Y, BAT_W, BAT_H = 0.7, 3.2, 2.7, 1.6
box(BAT_X, BAT_Y, BAT_W, BAT_H, fc='#fafafa', ec='#607d8b', lw=2.2, zo=3)
t(BAT_X + BAT_W/2, BAT_Y + BAT_H/2 + 0.22, 'Battery',     sz=10,  c='#37474f', bold=True)
t(BAT_X + BAT_W/2, BAT_Y + BAT_H/2 - 0.26, '(LiPo / AA)', sz=8.5, c='#546e7a')

BAT_POS_Y = BAT_Y + BAT_H - 0.32   # = 4.48
BAT_NEG_Y = BAT_Y + 0.32           # = 3.52
BAT_RX    = BAT_X + BAT_W          # = 3.40

t(BAT_RX - 0.18, BAT_POS_Y, '(+)', ha='right', sz=9.5, c=C_LOOP,   bold=True)
t(BAT_RX - 0.18, BAT_NEG_Y, '(−)', ha='right', sz=9.5, c='#37474f', bold=True)

# Voltage divider: Battery (+) → R1 → mid-point → R2 → GND
R1_CX     = 4.80   # R1 centre
MID_X     = 5.90   # mid-point (junction between R1 and R2)
MID_Y     = BAT_POS_Y
DIV_GND_Y = BAT_NEG_Y - 0.55   # = 2.97

# Battery (+) → R1 → mid-point
wire([(BAT_RX, BAT_POS_Y), (R1_CX - 0.50, BAT_POS_Y)], C_LOOP)
resistor_h(R1_CX, BAT_POS_Y, 'R1  100 kΩ')
wire([(R1_CX + 0.50, BAT_POS_Y), (MID_X, MID_Y)], C_LOOP)
dot(MID_X, MID_Y, C_BATT)

# Mid-point → R2 (vertical) → GND
wire([(MID_X, MID_Y),        (MID_X, MID_Y - 0.52)],  C_GND)
resistor_v(MID_X, MID_Y - 1.02, 'R2  100 kΩ')
wire([(MID_X, MID_Y - 1.52), (MID_X, DIV_GND_Y)],     C_GND)
gnd_sym(MID_X, DIV_GND_Y)

# Battery (−) → GND (short stub down)
BAT_GND_X = BAT_RX + 0.35
wire([(BAT_RX,    BAT_NEG_Y),
      (BAT_GND_X, BAT_NEG_Y),
      (BAT_GND_X, DIV_GND_Y - 0.06)], C_GND)
gnd_sym(BAT_GND_X, DIV_GND_Y - 0.06)

# Mid-point → GPIO1  (scaled voltage the ADC reads)
GPIO1_STUB_END = LPX - STUB   # = 8.45
wire([(MID_X,          MID_Y),
      (GPIO1_STUB_END,  MID_Y),
      (GPIO1_STUB_END,  Y_GPIO1)], C_BATT)

# Annotation above the horizontal segment — clear of the wire path
ann((MID_X + GPIO1_STUB_END) / 2, MID_Y + 0.38,
    '~2.1 V at full charge   (ADC reads divided battery voltage)')

# OPTIONAL badge
rbox(BAT_X - 0.06, BAT_Y - 0.56, 2.82, 0.40,
     fc='#fff8e1', ec='#f9a825', lw=1.6, zo=4, r=0.07)
t(BAT_X + BAT_W/2, BAT_Y - 0.36, 'OPTIONAL', sz=9, c='#e65100', bold=True)

t(BAT_X + BAT_W/2, BAT_Y + BAT_H + 0.36, '③ Battery Divider',
  sz=10, c='#37474f', bold=True)

# ─────────────────────────────────────────────────────────────────────────────
#  Title block
# ─────────────────────────────────────────────────────────────────────────────
t(FIG_W / 2, FIG_H - 0.52,
  'WellD — Sensor Wiring Diagram',
  sz=17, c='#0d1b4b', bold=True)
t(FIG_W / 2, FIG_H - 1.08,
  'ESP32-C6  ·  4–20 mA Pressure Transducer  ·  DS18B20 Temperature Probe'
  '  ·  Battery Monitor (optional)',
  sz=9, c='#546e7a')

# ─────────────────────────────────────────────────────────────────────────────
#  Colour key
# ─────────────────────────────────────────────────────────────────────────────
KX, KY = 15.5, 2.5
rbox(KX - 0.25, KY - 0.25, 6.2, 4.2,
     fc='#fafafa', ec='#b0bec5', lw=1.5, zo=3, r=0.15)
t(KX + 2.85, KY + 3.72, 'Colour Key', sz=11, c='#0d1b4b', bold=True)

KEY_ITEMS = [
    (C_PWR,  '+3.3 V power rail'),
    (C_LOOP, 'Loop supply  (9–36 V)'),
    (C_SIG,  'Signal / ADC node'),
    (C_GND,  'Ground  (GND symbols)'),
    (C_BATT, 'Battery ADC  (optional)'),
]
for i, (c, lbl) in enumerate(KEY_ITEMS):
    ky = KY + 3.18 - i * 0.62
    ax.plot([KX + 0.12, KX + 1.05], [ky, ky],
            color=c, lw=3.2, solid_capstyle='round', zorder=5)
    dot(KX + 1.05, ky, c, sz=45, zo=6)
    t(KX + 1.22, ky, lbl, ha='left', sz=9.5, c='#212121')

# ─────────────────────────────────────────────────────────────────────────────
#  Footer note
# ─────────────────────────────────────────────────────────────────────────────
t(FIG_W / 2, 0.42,
  'GND symbols are all one net — connect each to the board GND pin.  '
  '+3.3V symbols connect to the board 3V3 pin.  '
  'Default GPIO assignments; change in sdkconfig.defaults.local.',
  sz=7.5, c='#90a4ae', italic=True)

# ─────────────────────────────────────────────────────────────────────────────
out = os.path.join(os.path.dirname(__file__), 'wiring_diagram.png')
plt.savefig(out, dpi=150, bbox_inches='tight', facecolor='white')
print(f'Saved → {out}')
