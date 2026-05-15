#!/usr/bin/env python3
"""WellD wiring diagram — ESP32-C6-DevKitC-1 actual pinout."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os

# ── Canvas ────────────────────────────────────────────────────────────────────
FIG_W, FIG_H = 26, 16
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(0, FIG_W)
ax.set_ylim(0, FIG_H)
ax.set_aspect('equal')
ax.axis('off')
fig.patch.set_facecolor('#ffffff')
ax.set_facecolor('#ffffff')

# ── Palette ───────────────────────────────────────────────────────────────────
C_PWR   = '#b71c1c'   # +3.3 V
C_GND   = '#1a237e'   # ground
C_SIG   = '#0277bd'   # ADC / 1-Wire signal
C_LOOP  = '#bf360c'   # raw/unregulated voltage (battery input to divider)
C_BATT  = '#1b5e20'   # battery ADC (optional)
C_PCB   = '#2e7d32'   # board fill
C_ANN   = '#546e7a'   # annotation text
C_FADE  = '#b0bec5'   # unused-pin colour

LW   = 2.2
STUB = 0.45   # board pin stub beyond edge

# ── Helpers ───────────────────────────────────────────────────────────────────
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

def dot(x, y, c, sz=80, zo=6):
    ax.scatter([x], [y], s=sz, color=c, zorder=zo)

def t(x, y, s, ha='center', va='center', sz=9, c='#212121',
      bold=False, italic=False, zo=8):
    ax.text(x, y, s, ha=ha, va=va, fontsize=sz, color=c, zorder=zo,
            fontweight='bold' if bold else 'normal',
            fontstyle='italic'  if italic else 'normal')

def ann(x, y, s, ha='center'):
    """Annotation with white background so it reads over any wire beneath."""
    ax.text(x, y, s, ha=ha, va='center', fontsize=8, color=C_ANN,
            fontstyle='italic', zorder=9,
            bbox=dict(fc='white', ec='none', alpha=0.90, pad=2.0))

def resistor_v(cx, cy, val, zo=5):
    """Vertical resistor body; value label to the right, clear of body."""
    W, H = 0.42, 0.90
    box(cx - W/2, cy - H/2, W, H, fc='#fff9c4', ec='#f57f17', lw=1.5, zo=zo)
    t(cx + W/2 + 0.14, cy, val, ha='left', sz=8, c='#4e342e', bold=True, zo=zo+1)

def resistor_h(cx, cy, val, zo=5):
    """Horizontal resistor body; value label above, clear of body."""
    W, H = 0.90, 0.42
    box(cx - W/2, cy - H/2, W, H, fc='#fff9c4', ec='#f57f17', lw=1.5, zo=zo)
    t(cx, cy + H/2 + 0.18, val, ha='center', sz=8, c='#4e342e', bold=True, zo=zo+1)

def gnd_sym(x, y, zo=5):
    """IEC earth symbol: three decreasing horizontal bars."""
    for i, hw in enumerate([0.28, 0.18, 0.09]):
        ax.plot([x - hw, x + hw], [y - i*0.13, y - i*0.13],
                color=C_GND, lw=2.0, zorder=zo)

def vcc_sym(x, y, lbl='+3.3V', zo=5):
    """VCC rail symbol: upward arrow + label.  Connection point is at (x, y)."""
    ax.annotate('', xy=(x, y + 0.40), xytext=(x, y),
                arrowprops=dict(arrowstyle='->', color=C_PWR, lw=2.1), zorder=zo)
    t(x, y + 0.65, lbl, sz=8.5, c=C_PWR, bold=True, zo=zo+1)

# ─────────────────────────────────────────────────────────────────────────────
#  ESP32-C6-DevKitC-1  pinout
#
#  J1 (left, top → bottom, USB at board bottom):
#    GND, 3V3, EN, GPIO4, GPIO5, GPIO6, GPIO7,
#    GPIO0, GPIO1, GPIO2, GPIO3, GPIO8–GPIO11, GND
#
#  J3 (right, top → bottom):
#    GND, 5V, GPIO23–GPIO12, GND
# ─────────────────────────────────────────────────────────────────────────────
BX, BY, BW, BH = 10.8, 2.2, 3.6, 10.8
BTOP = BY + BH    # 13.0
BBOT = BY         # 2.2
LPX  = BX         # left  edge  10.8
RPX  = BX + BW    # right edge  14.4

# (label, highlight-colour or None, used-bool)
L_PINS = [
    ('GND',    C_GND,  True ),   # 0  — shunt / battery ground
    ('3V3',    C_PWR,  True ),   # 1  — +3.3 V rail (shown via rail symbols)
    ('EN',     None,   False),
    ('GPIO4',  C_SIG,  True ),   # 3  — DS18B20 1-Wire data
    ('GPIO5',  None,   False),
    ('GPIO6',  None,   False),
    ('GPIO7',  None,   False),
    ('GPIO0',  C_SIG,  True ),   # 7  — pressure ADC  (ADC1_CH0)
    ('GPIO1',  C_BATT, True ),   # 8  — battery ADC   (ADC1_CH1, optional)
    ('GPIO2',  None,   False),
    ('GPIO3',  None,   False),
    ('GPIO8',  None,   False),
    ('GPIO9',  None,   False),
    ('GPIO10', None,   False),
    ('GPIO11', None,   False),
    ('GND',    C_GND,  True ),   # 15 — shunt / battery ground
]

R_PINS = [
    ('GND',       None,  False),   # 0  — shown via GND symbol at DS18B20
    ('5V',        None,  False),
    ('GPIO23',    None,  False),
    ('GPIO22',    None,  False),
    ('GPIO21',    None,  False),
    ('GPIO20',    None,  False),
    ('GPIO19',    None,  False),
    ('GPIO18',    None,  False),
    ('GPIO17/RX', None,  False),
    ('GPIO16/TX', None,  False),
    ('GPIO15',    None,  False),
    ('GPIO14',    None,  False),
    ('GPIO13',    None,  False),
    ('GPIO12',    None,  False),
    ('GND',       None,  False),
]

NL = len(L_PINS)   # 16
NR = len(R_PINS)   # 15

L_TOP_Y = BTOP - 0.55   # 12.45
L_BOT_Y = BBOT + 0.55   # 2.75
L_STEP  = (L_TOP_Y - L_BOT_Y) / (NL - 1)   # 0.647
L_YS    = [L_TOP_Y - i * L_STEP for i in range(NL)]

R_TOP_Y = BTOP - 0.55
R_BOT_Y = BBOT + 0.55
R_STEP  = (R_TOP_Y - R_BOT_Y) / (NR - 1)
R_YS    = [R_TOP_Y - i * R_STEP for i in range(NR)]

# ── Board body ────────────────────────────────────────────────────────────────
ax.add_patch(mpatches.FancyBboxPatch((BX, BY), BW, BH,
    boxstyle='round,pad=0.18', lw=3.0, ec='#1b5e20', fc=C_PCB, zorder=3))

# USB connector
USB_W, USB_H = 1.0, 0.45
ax.add_patch(mpatches.FancyBboxPatch(
    (BX + BW/2 - USB_W/2, BBOT - USB_H), USB_W, USB_H,
    boxstyle='round,pad=0.05', lw=1.5, ec='#78909c', fc='#eceff1', zorder=4))
t(BX + BW/2, BBOT - USB_H/2, 'USB', sz=7, c='#607d8b')

# Module silkscreen
MX = BX + BW*0.25
MY = BY + BH*0.52
MW, MH = BW*0.50, BH*0.28
box(MX, MY, MW, MH, fc='#1c1c1c', ec='#424242', lw=1.2, zo=4)
t(BX + BW/2, MY + MH*0.62, 'ESP32-C6', sz=8.5, c='white', bold=True, zo=5)
t(BX + BW/2, MY + MH*0.25, 'module',   sz=7,   c='#9e9e9e',           zo=5)

t(BX + BW/2, BY + BH*0.18, 'DevKitC-1', sz=9, c='#a5d6a7')
t(BX + BW/2, BY + BH*0.10,
  'J1 ← left  |  right → J3', sz=6.5, c='#66bb6a', italic=True)

# ── Pin stubs ─────────────────────────────────────────────────────────────────
PAD = 0.065

def draw_left_pin(idx):
    lbl, col, used = L_PINS[idx]
    y  = L_YS[idx]
    c  = col if used else C_FADE
    lw_pin = 2.4 if used else 1.2
    ax.plot([LPX - STUB, LPX], [y, y], color=c, lw=lw_pin, zorder=4)
    sp = PAD if used else PAD*0.7
    ax.add_patch(mpatches.Rectangle(
        (LPX - STUB - sp, y - sp), sp*2, sp*2,
        fc=c, ec='white', lw=0.6, zorder=5))
    t(LPX - STUB - 0.14, y, lbl,
      ha='right', sz=8 if used else 7, c=c, bold=used, zo=8)

def draw_right_pin(idx):
    lbl, col, used = R_PINS[idx]
    y  = R_YS[idx]
    c  = col if used else C_FADE
    lw_pin = 2.4 if used else 1.2
    ax.plot([RPX, RPX + STUB], [y, y], color=c, lw=lw_pin, zorder=4)
    sp = PAD if used else PAD*0.7
    ax.add_patch(mpatches.Rectangle(
        (RPX + STUB - sp, y - sp), sp*2, sp*2,
        fc=c, ec='white', lw=0.6, zorder=5))
    t(RPX + STUB + 0.14, y, lbl,
      ha='left', sz=8 if used else 7, c=c, bold=used, zo=8)

for i in range(NL): draw_left_pin(i)
for i in range(NR): draw_right_pin(i)

# Named y-coords for wired pins
Y_GND_L_TOP = L_YS[0]    # 12.45
Y_3V3       = L_YS[1]    # 11.80
Y_GPIO4     = L_YS[3]    # 10.51
Y_GPIO0     = L_YS[7]    #  7.92
Y_GPIO1     = L_YS[8]    #  7.28
Y_GND_L_BOT = L_YS[15]   #  2.75

LSTUB_END = LPX - STUB   # 10.35  — outer end of left  stubs
RSTUB_END = RPX + STUB   # 14.85  — outer end of right stubs

# 3V3 annotation: rail symbol represents this board pin
ann(LPX - STUB - 1.18, Y_3V3,
    '+3.3V rail symbols', ha='right')

# ─────────────────────────────────────────────────────────────────────────────
#  ① Pressure transducer (4–20 mA current loop)
# ─────────────────────────────────────────────────────────────────────────────
TX, TY, TW, TH = 0.6, 8.8, 2.8, 2.0
box(TX, TY, TW, TH, fc='#e3f2fd', ec='#0d47a1', lw=2.2, zo=3)
t(TX+TW/2, TY+TH/2+0.30, 'Pressure',   sz=10, c='#0d47a1', bold=True)
t(TX+TW/2, TY+TH/2-0.12, 'Transducer', sz=10, c='#0d47a1', bold=True)
t(TX+TW/2, TY+TH/2-0.54, '(4–20 mA)', sz=8.5, c='#1565c0')
t(TX+0.18, TY+TH-0.30,   '(+)', ha='left', sz=9, c=C_PWR, bold=True)
t(TX+0.18, TY+0.30,       '(−)', ha='left', sz=9, c='#37474f', bold=True)

# (+) terminal: stub exits box right wall → +3.3V rail symbol.
# Wire starts AT the right wall so it never enters the box interior.
TRANS_POS_Y  = TY + TH - 0.30          # 10.50
TRANS_STUB_X = TX + TW + 0.55          # 3.95 — stub end outside box
wire([(TX + TW, TRANS_POS_Y), (TRANS_STUB_X, TRANS_POS_Y)], C_PWR, zo=4)
vcc_sym(TRANS_STUB_X, TRANS_POS_Y, '+3.3V')

t(TX+TW/2, TY+TH+1.05, '① Pressure Transducer', sz=10, c='#0d47a1', bold=True)

# ── Signal junction: transducer −, shunt top, GPIO0 ──────────────────────────
# This node sits at 0.4–2.0 V (loop current × 100 Ω). It is NOT ground.
JX = 8.0
JY = TY + 0.30   # 9.10

wire([(TX+TW, JY), (JX, JY)], C_SIG)   # transducer − → junction (left to right)
dot(JX, JY, C_SIG)

# Shunt 100 Ω → GND — goes STRAIGHT DOWN from junction at x=JX
SHUNT_GND_Y = JY - 2.4   # 6.70
wire([(JX, JY),       (JX, JY - 0.52)], C_GND)
resistor_v(JX, JY - 1.02, '100 Ω  ±1 %')
wire([(JX, JY - 1.52), (JX, SHUNT_GND_Y)], C_GND)
gnd_sym(JX, SHUNT_GND_Y)

# GPIO0 route: junction → RIGHT at JY level → down → right to board stub.
# Exits right so it never overlaps the vertical shunt wire.
GPIO0_TURN_X = 9.4   # between JX (8.0) and board stub (10.35)
wire([(JX,           JY),
      (GPIO0_TURN_X, JY),
      (GPIO0_TURN_X, Y_GPIO0),
      (LSTUB_END,    Y_GPIO0)], C_SIG)
ann((GPIO0_TURN_X + LSTUB_END)/2, Y_GPIO0 + 0.48,
    '0.4 – 2.0 V  (shunt voltage → ADC)')

# ─────────────────────────────────────────────────────────────────────────────
#  ② DS18B20 Temperature Probe
#
#  Pin connections are on the LEFT side via short external stubs.
#  No wire ever enters the DS18B20 box interior — all wires terminate
#  at the stub endpoints which sit just outside the box left edge.
#
#  Pull-up topology (correct):
#       +3.3V        +3.3V
#         │            │
#       4.7 kΩ       (stub)
#         │            │
#  GPIO4 ─┤── DATA stub ── VCC stub
#     junction             │
#         │               DS18B20
#        GND stub
#         │
#        GND
# ─────────────────────────────────────────────────────────────────────────────
DSX, DSY, DSW, DSH = 18.5, 8.0, 3.4, 2.8

# Pin y-levels (where each signal enters/exits the component left edge)
DS_VCC_Y  = DSY + DSH - 0.45   # 10.35
DS_DATA_Y = DSY + DSH / 2       # 9.40
DS_GND_Y  = DSY + 0.45          # 8.45

DS_STUB   = 0.65                          # stub length beyond box left wall
DS_CONN_X = DSX - DS_STUB                # 17.85 — external connection x

# DS18B20 box
box(DSX, DSY, DSW, DSH, fc='#e8f5e9', ec='#1b5e20', lw=2.2, zo=3)
t(DSX+DSW/2, DSY+DSH*0.72, 'DS18B20',      sz=10, c='#1b5e20', bold=True)
t(DSX+DSW/2, DSY+DSH*0.50, 'Temperature',  sz=9,  c='#2e7d32')
t(DSX+DSW/2, DSY+DSH*0.30, 'Probe',        sz=9,  c='#2e7d32')

# Pin labels inside box, flush left
t(DSX+0.22, DS_VCC_Y,  'VCC',  ha='left', sz=9, c=C_PWR, bold=True)
t(DSX+0.22, DS_DATA_Y, 'DATA', ha='left', sz=9, c=C_SIG, bold=True)
t(DSX+0.22, DS_GND_Y,  'GND',  ha='left', sz=9, c=C_GND, bold=True)

# External stubs: connection point → box left wall.
# zo=4 so stubs are visible over the box border line.
wire([(DS_CONN_X, DS_VCC_Y),  (DSX, DS_VCC_Y)],  C_PWR, zo=4)
wire([(DS_CONN_X, DS_DATA_Y), (DSX, DS_DATA_Y)],  C_SIG, zo=4)
wire([(DS_CONN_X, DS_GND_Y),  (DSX, DS_GND_Y)],   C_GND, zo=4)

# VCC: +3.3V rail symbol directly at the VCC stub connection point.
# Arrow points UP from DS_CONN_X; stub wire goes RIGHT into box.
vcc_sym(DS_CONN_X, DS_VCC_Y)

# GND: earth symbol directly at the GND stub connection point, pointing DOWN.
gnd_sym(DS_CONN_X, DS_GND_Y - 0.08)

# Pull-up resistor: sits on the DATA wire between GPIO4 drop and DS18B20 DATA stub.
# Junction at (PU_JX, DS_DATA_Y); pull-up branch goes UP to +3.3V.
PU_JX = 16.8   # between GPIO4 drop column and DS_CONN_X (17.85)
PU_JY = DS_DATA_Y

dot(PU_JX, PU_JY, C_SIG)
wire([(PU_JX, PU_JY), (PU_JX, PU_JY + 0.52)], C_PWR)
resistor_v(PU_JX, PU_JY + 1.05, '4.7 kΩ')
wire([(PU_JX, PU_JY + 1.58), (PU_JX, PU_JY + 1.95)], C_PWR)
vcc_sym(PU_JX, PU_JY + 1.95, '+3.3V')

# GPIO4 wire:
#   board left stub (10.35, Y_GPIO4)
#   → left to routing channel at x=ROUTE_X
#   → UP to above-board channel at OVER_Y
#   → RIGHT across top of board
#   → DROP at PU_JX down to DATA level
#   → RIGHT along DATA wire to DS18B20 DATA stub connection
ROUTE_X = 8.8
OVER_Y  = BTOP + 1.2   # 14.2

wire([(LSTUB_END, Y_GPIO4),
      (ROUTE_X,   Y_GPIO4),
      (ROUTE_X,   OVER_Y),
      (PU_JX,     OVER_Y),
      (PU_JX,     DS_DATA_Y),
      (DS_CONN_X, DS_DATA_Y)], C_SIG, lw=2.5)
ann((ROUTE_X + PU_JX)/2, OVER_Y + 0.35,
    'GPIO4  /  1-Wire data  (routed over board top)')

t(DSX+DSW/2, DSY+DSH+1.25, '② DS18B20 Temperature Probe',
  sz=10, c='#1b5e20', bold=True)

# ─────────────────────────────────────────────────────────────────────────────
#  ③ Battery Voltage Divider  (optional)
# ─────────────────────────────────────────────────────────────────────────────
BAT_X, BAT_Y, BAT_W, BAT_H = 0.6, 4.0, 2.6, 1.55
box(BAT_X, BAT_Y, BAT_W, BAT_H, fc='#fafafa', ec='#607d8b', lw=2.0, zo=3)
t(BAT_X+BAT_W/2, BAT_Y+BAT_H/2+0.22, 'Battery',     sz=9.5, c='#37474f', bold=True)
t(BAT_X+BAT_W/2, BAT_Y+BAT_H/2-0.24, '(LiPo / AA)', sz=8,   c='#546e7a')

BAT_POS_Y = BAT_Y + BAT_H - 0.30   # 5.25
BAT_NEG_Y = BAT_Y + 0.30           # 4.30
BAT_RX    = BAT_X + BAT_W          # 3.20

t(BAT_RX-0.16, BAT_POS_Y, '(+)', ha='right', sz=9, c=C_LOOP,    bold=True)
t(BAT_RX-0.16, BAT_NEG_Y, '(−)', ha='right', sz=9, c='#37474f', bold=True)

# Battery (+) → R1 → midpoint
R1_CX  = 4.55
MID_X  = 5.60
MID_Y  = BAT_POS_Y   # 5.25

wire([(BAT_RX, BAT_POS_Y), (R1_CX-0.48, BAT_POS_Y)], C_LOOP)
resistor_h(R1_CX, BAT_POS_Y, 'R1  100 kΩ')
wire([(R1_CX+0.48, BAT_POS_Y), (MID_X, MID_Y)], C_LOOP)
dot(MID_X, MID_Y, C_BATT)

# Midpoint → R2 → GND
DIV_GND_Y = BAT_NEG_Y - 0.50   # 3.80
wire([(MID_X, MID_Y), (MID_X, MID_Y - 0.50)], C_GND)
resistor_v(MID_X, MID_Y - 1.00, 'R2  100 kΩ')
wire([(MID_X, MID_Y - 1.50), (MID_X, DIV_GND_Y)], C_GND)
gnd_sym(MID_X, DIV_GND_Y)

# Battery (−) → GND
BAT_GND_X = BAT_RX + 0.30
wire([(BAT_RX,    BAT_NEG_Y),
      (BAT_GND_X, BAT_NEG_Y),
      (BAT_GND_X, DIV_GND_Y - 0.05)], C_GND)
gnd_sym(BAT_GND_X, DIV_GND_Y - 0.05)

# Midpoint → GPIO1:  RIGHT at MID_Y, then UP to GPIO1 row, then RIGHT to board stub
GPIO1_TURN_X = LSTUB_END   # 10.35
wire([(MID_X,        MID_Y),
      (GPIO1_TURN_X, MID_Y),
      (GPIO1_TURN_X, Y_GPIO1)], C_BATT)
ann((MID_X + GPIO1_TURN_X)/2, MID_Y + 0.48,
    '~2.1 V at full charge  (divided battery → ADC)')

rbox(BAT_X-0.06, BAT_Y-0.54, 2.72, 0.38,
     fc='#fff8e1', ec='#f9a825', lw=1.5, zo=4, r=0.06)
t(BAT_X+BAT_W/2, BAT_Y-0.35,      'OPTIONAL',         sz=8.5, c='#e65100', bold=True)
t(BAT_X+BAT_W/2, BAT_Y+BAT_H+0.32, '③ Battery Divider', sz=10, c='#37474f', bold=True)

# ─────────────────────────────────────────────────────────────────────────────
#  Title
# ─────────────────────────────────────────────────────────────────────────────
t(FIG_W/2, FIG_H-0.50,
  'WellD — Sensor Wiring Diagram', sz=17, c='#0d1b4b', bold=True)
t(FIG_W/2, FIG_H-1.05,
  'ESP32-C6-DevKitC-1  ·  4–20 mA Pressure Transducer  ·'
  '  DS18B20 Temperature Probe  ·  Battery Monitor (optional)',
  sz=9, c='#546e7a')

# ─────────────────────────────────────────────────────────────────────────────
#  Colour key
# ─────────────────────────────────────────────────────────────────────────────
KX, KY = 18.6, 2.0
rbox(KX-0.3, KY-0.3, 7.3, 5.6, fc='#fafafa', ec='#b0bec5', lw=1.4, zo=3, r=0.15)
t(KX+3.35, KY+5.1, 'Colour Key', sz=11, c='#0d1b4b', bold=True)

KEY_ITEMS = [
    (C_PWR,  '+3.3 V power rail  (ESP32 3V3 pin)'),
    (C_SIG,  'Signal / 1-Wire / ADC node'),
    (C_GND,  'Ground  (all GND symbols = same net)'),
    (C_LOOP, 'Battery voltage  (raw, into divider)'),
    (C_BATT, 'Battery ADC signal  (optional)'),
    (C_FADE, 'Unused board pin'),
]
for i, (c, lbl) in enumerate(KEY_ITEMS):
    ky = KY + 4.52 - i * 0.72
    ax.plot([KX+0.12, KX+1.10], [ky, ky],
            color=c, lw=3.0, solid_capstyle='round', zorder=5)
    dot(KX+1.10, ky, c, sz=40, zo=6)
    t(KX+1.28, ky, lbl, ha='left', sz=8.5, c='#212121')

# ─────────────────────────────────────────────────────────────────────────────
#  Footer
# ─────────────────────────────────────────────────────────────────────────────
t(FIG_W/2, 0.40,
  '+3.3V / GND symbols represent the board 3V3 and GND pins respectively — '
  'connect each symbol to the nearest available board pin.  '
  'Default GPIO assignments; override in sdkconfig.defaults.local.',
  sz=7.5, c='#90a4ae', italic=True)

# ─────────────────────────────────────────────────────────────────────────────
out = os.path.join(os.path.dirname(__file__), 'wiring_diagram.png')
plt.savefig(out, dpi=150, bbox_inches='tight', facecolor='white')
print(f'Saved → {out}')
