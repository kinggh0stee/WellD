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
C_PWR   = '#b71c1c'   # +3.3 V  (dark red)
C_GND   = '#1a237e'   # ground  (dark navy)
C_SIG   = '#0277bd'   # ADC / 1-Wire signal  (blue)
C_LOOP  = '#bf360c'   # loop supply  (dark orange-red)
C_BATT  = '#1b5e20'   # battery ADC  (dark green)
C_PCB   = '#2e7d32'   # board fill
C_ANN   = '#546e7a'   # annotation text
C_FADE  = '#b0bec5'   # unused-pin label colour
C_USED  = '#212121'   # used-pin label colour

LW   = 2.2
STUB = 0.45   # pin stub beyond board edge

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

def dot(x, y, c, sz=72, zo=6):
    ax.scatter([x], [y], s=sz, color=c, zorder=zo)

def t(x, y, s, ha='center', va='center', sz=9, c='#212121',
      bold=False, italic=False, zo=8):
    ax.text(x, y, s, ha=ha, va=va, fontsize=sz, color=c, zorder=zo,
            fontweight='bold' if bold else 'normal',
            fontstyle='italic'  if italic else 'normal')

def ann(x, y, s, ha='center'):
    t(x, y, s, ha=ha, sz=7.5, c=C_ANN, italic=True)

def resistor_v(cx, cy, val, zo=5):
    W, H = 0.42, 0.90
    box(cx - W/2, cy - H/2, W, H, fc='#fff9c4', ec='#f57f17', lw=1.5, zo=zo)
    t(cx + W/2 + 0.12, cy, val, ha='left', sz=8, c='#4e342e', bold=True, zo=zo+1)

def resistor_h(cx, cy, val, zo=5):
    W, H = 0.90, 0.42
    box(cx - W/2, cy - H/2, W, H, fc='#fff9c4', ec='#f57f17', lw=1.5, zo=zo)
    t(cx, cy + H/2 + 0.17, val, ha='center', sz=8, c='#4e342e', bold=True, zo=zo+1)

def gnd_sym(x, y, zo=5):
    for i, hw in enumerate([0.28, 0.18, 0.09]):
        ax.plot([x - hw, x + hw], [y - i*0.13, y - i*0.13],
                color=C_GND, lw=2.0, zorder=zo)

def vcc_sym(x, y, lbl='+3.3V', zo=5):
    ax.annotate('', xy=(x, y + 0.38), xytext=(x, y),
                arrowprops=dict(arrowstyle='->', color=C_PWR, lw=2.0), zorder=zo)
    t(x, y + 0.62, lbl, sz=8, c=C_PWR, bold=True, zo=zo+1)

# ─────────────────────────────────────────────────────────────────────────────
#  ESP32-C6-DevKitC-1  actual pinout
#
#  Left header J1 (top → bottom, USB connector at board bottom):
#    GND, 3V3, EN, GPIO4, GPIO5, GPIO6, GPIO7,
#    GPIO0, GPIO1, GPIO2, GPIO3, GPIO8, GPIO9, GPIO10, GPIO11, GND
#
#  Right header J3 (top → bottom):
#    GND, 5V, GPIO23, GPIO22, GPIO21, GPIO20, GPIO19, GPIO18,
#    GPIO17/RX, GPIO16/TX, GPIO15, GPIO14, GPIO13, GPIO12, GND
# ─────────────────────────────────────────────────────────────────────────────
BX, BY, BW, BH = 10.8, 2.2, 3.6, 10.8
BTOP = BY + BH    # 13.0
BBOT = BY         # 2.2
LPX  = BX         # left edge  10.8
RPX  = BX + BW    # right edge 14.4

# Pin definitions: (label, colour-if-used, used?, side-annotation)
# colour=None for unused pins
L_PINS = [
    ('GND',    C_GND,   True,  ''),
    ('3V3',    C_PWR,   True,  '→ pull-up, DS18B20 VCC'),
    ('EN',     None,    False, ''),
    ('GPIO4',  C_SIG,   True,  '→ DS18B20 DATA  (1-Wire)'),
    ('GPIO5',  None,    False, ''),
    ('GPIO6',  None,    False, ''),
    ('GPIO7',  None,    False, ''),
    ('GPIO0',  C_SIG,   True,  '→ shunt (ADC1_CH0)'),
    ('GPIO1',  C_BATT,  True,  '→ battery divider (ADC1_CH1)'),
    ('GPIO2',  None,    False, ''),
    ('GPIO3',  None,    False, ''),
    ('GPIO8',  None,    False, ''),
    ('GPIO9',  None,    False, ''),
    ('GPIO10', None,    False, ''),
    ('GPIO11', None,    False, ''),
    ('GND',    C_GND,   True,  '→ shunt / bat GND'),
]

R_PINS = [
    ('GND',       C_GND,  True,  '→ DS18B20 GND'),
    ('5V',        None,   False, ''),
    ('GPIO23',    None,   False, ''),
    ('GPIO22',    None,   False, ''),
    ('GPIO21',    None,   False, ''),
    ('GPIO20',    None,   False, ''),
    ('GPIO19',    None,   False, ''),
    ('GPIO18',    None,   False, ''),
    ('GPIO17/RX', None,   False, ''),
    ('GPIO16/TX', None,   False, ''),
    ('GPIO15',    None,   False, ''),
    ('GPIO14',    None,   False, ''),
    ('GPIO13',    None,   False, ''),
    ('GPIO12',    None,   False, ''),
    ('GND',       C_GND,  False, ''),
]

NL = len(L_PINS)   # 16
NR = len(R_PINS)   # 15

# Compute y positions so first pin is near top, last near bottom
L_TOP_Y = BTOP - 0.55
L_BOT_Y = BBOT + 0.55
L_STEP  = (L_TOP_Y - L_BOT_Y) / (NL - 1)
L_YS    = [L_TOP_Y - i * L_STEP for i in range(NL)]

R_TOP_Y = BTOP - 0.55
R_BOT_Y = BBOT + 0.55
R_STEP  = (R_TOP_Y - R_BOT_Y) / (NR - 1)
R_YS    = [R_TOP_Y - i * R_STEP for i in range(NR)]

# ── Draw board body ───────────────────────────────────────────────────────────
ax.add_patch(mpatches.FancyBboxPatch((BX, BY), BW, BH,
    boxstyle='round,pad=0.18', lw=3.0, ec='#1b5e20', fc=C_PCB, zorder=3))

# USB connector stub at board bottom
USB_W, USB_H = 1.0, 0.45
ax.add_patch(mpatches.FancyBboxPatch(
    (BX + BW/2 - USB_W/2, BBOT - USB_H), USB_W, USB_H,
    boxstyle='round,pad=0.05', lw=1.5, ec='#78909c', fc='#eceff1', zorder=4))
t(BX + BW/2, BBOT - USB_H/2, 'USB', sz=7, c='#607d8b')

# Module outline (ESP32-C6 module on PCB)
MX = BX + BW*0.25
MY = BY + BH*0.52
MW, MH = BW * 0.50, BH * 0.28
box(MX, MY, MW, MH, fc='#1c1c1c', ec='#424242', lw=1.2, zo=4)
t(BX + BW/2, MY + MH*0.62, 'ESP32-C6', sz=8.5, c='white', bold=True, zo=5)
t(BX + BW/2, MY + MH*0.25, 'module',   sz=7,   c='#9e9e9e',            zo=5)

# Board label
t(BX + BW/2, BY + BH*0.18, 'DevKitC-1', sz=9,  c='#a5d6a7')
t(BX + BW/2, BY + BH*0.09, 'J1 ← left  |  right → J3', sz=6.5, c='#66bb6a', italic=True)

# ── Draw all pins ─────────────────────────────────────────────────────────────
PAD = 0.065   # pad half-size

def draw_left_pin(idx):
    lbl, col, used, _ = L_PINS[idx]
    y = L_YS[idx]
    c = col if used else C_FADE
    lw_pin = 2.4 if used else 1.2
    # stub
    ax.plot([LPX - STUB, LPX], [y, y], color=c, lw=lw_pin, zorder=4)
    # pad square
    sz_pad = PAD if used else PAD * 0.7
    fc_pad = c if used else '#cfd8dc'
    ax.add_patch(mpatches.Rectangle(
        (LPX - STUB - sz_pad, y - sz_pad), sz_pad*2, sz_pad*2,
        fc=fc_pad, ec='white', lw=0.6, zorder=5))
    # label
    t(LPX - STUB - 0.14, y, lbl,
      ha='right', sz=8 if used else 7, c=c,
      bold=used, zo=8)

def draw_right_pin(idx):
    lbl, col, used, _ = R_PINS[idx]
    y = R_YS[idx]
    c = col if used else C_FADE
    lw_pin = 2.4 if used else 1.2
    ax.plot([RPX, RPX + STUB], [y, y], color=c, lw=lw_pin, zorder=4)
    sz_pad = PAD if used else PAD * 0.7
    fc_pad = c if used else '#cfd8dc'
    ax.add_patch(mpatches.Rectangle(
        (RPX + STUB - sz_pad, y - sz_pad), sz_pad*2, sz_pad*2,
        fc=fc_pad, ec='white', lw=0.6, zorder=5))
    t(RPX + STUB + 0.14, y, lbl,
      ha='left', sz=8 if used else 7, c=c,
      bold=used, zo=8)

for i in range(NL): draw_left_pin(i)
for i in range(NR): draw_right_pin(i)

# Handy aliases — pin stub endpoints (outer edge)
Y_GND_L_TOP = L_YS[0]   # left GND top
Y_3V3       = L_YS[1]
Y_GPIO4     = L_YS[3]
Y_GPIO0     = L_YS[7]
Y_GPIO1     = L_YS[8]
Y_GND_L_BOT = L_YS[15]

Y_GND_R_TOP = R_YS[0]   # right GND top

LSTUB_END = LPX - STUB   # left pad x  (wires connect here)
RSTUB_END = RPX + STUB   # right pad x

# ─────────────────────────────────────────────────────────────────────────────
#  ① Pressure transducer (4–20 mA)
# ─────────────────────────────────────────────────────────────────────────────
TX, TY, TW, TH = 0.6, 8.8, 2.8, 2.0
box(TX, TY, TW, TH, fc='#e3f2fd', ec='#0d47a1', lw=2.2, zo=3)
t(TX+TW/2, TY+TH/2+0.30, 'Pressure',   sz=10, c='#0d47a1', bold=True)
t(TX+TW/2, TY+TH/2-0.13, 'Transducer', sz=10, c='#0d47a1', bold=True)
t(TX+TW/2, TY+TH/2-0.55, '(4–20 mA)', sz=8.5, c='#1565c0')
t(TX+0.18, TY+TH-0.30, '(+)', ha='left', sz=9, c=C_LOOP, bold=True)
t(TX+0.18, TY+0.30,    '(−)', ha='left', sz=9, c='#37474f', bold=True)

# Loop supply box
LS_CX  = TX + TW/2
LS_BOT = TY + TH + 0.18
rbox(LS_CX-1.0, LS_BOT, 2.0, 0.85, fc='#fff3e0', ec=C_LOOP, lw=1.8, zo=3, r=0.07)
t(LS_CX, LS_BOT+0.54, 'Loop Supply',    sz=8.5, c=C_LOOP, bold=True)
t(LS_CX, LS_BOT+0.20, '(9 – 36 V DC)', sz=8,   c=C_LOOP)

TRANS_POS_Y = TY + TH - 0.30
wire([(TX+0.36, TRANS_POS_Y),
      (TX+0.36, TY+TH),
      (LS_CX,   TY+TH),
      (LS_CX,   LS_BOT)], C_LOOP)

t(TX+TW/2, TY+TH+1.25, '① Pressure Transducer', sz=9.5, c='#0d47a1', bold=True)

# Signal junction (transducer −, shunt top, GPIO0 wire)
JX = 8.0
JY = TY + 0.30   # ≈ 9.10

wire([(TX+TW, JY), (JX, JY)], C_SIG)
dot(JX, JY, C_SIG)

# Shunt 100 Ω → GND
SHUNT_GND_Y = JY - 2.4
wire([(JX, JY), (JX, JY-0.52)], C_GND)
resistor_v(JX, JY-1.02, '100 Ω  ±1 %')
wire([(JX, JY-1.52), (JX, SHUNT_GND_Y)], C_GND)
gnd_sym(JX, SHUNT_GND_Y)

# GPIO0 route: junction → left border of board at GPIO0 row
wire([(JX, JY),
      (JX, Y_GPIO0),
      (LSTUB_END, Y_GPIO0)], C_SIG)
ann((JX + LSTUB_END)/2, Y_GPIO0 + 0.32, '0.4 – 2.0 V  (shunt voltage → ADC)')

# ─────────────────────────────────────────────────────────────────────────────
#  ② DS18B20 Temperature Probe
#
#  GPIO4 is on the LEFT side of the board.
#  Wire routes: left stub end → left → UP along routing channel → OVER board top
#  → RIGHT → DOWN to DS18B20 DATA on the right.
# ─────────────────────────────────────────────────────────────────────────────
DSX, DSY, DSW, DSH = 18.5, 8.0, 3.4, 2.8
box(DSX, DSY, DSW, DSH, fc='#e8f5e9', ec='#1b5e20', lw=2.2, zo=3)
t(DSX+DSW/2, DSY+DSH/2+0.52, 'DS18B20',      sz=10, c='#1b5e20', bold=True)
t(DSX+DSW/2, DSY+DSH/2+0.10, 'Temperature',  sz=9,  c='#2e7d32')
t(DSX+DSW/2, DSY+DSH/2-0.32, 'Probe',        sz=9,  c='#2e7d32')

DS_VCC_Y  = DSY + DSH - 0.40
DS_DATA_Y = DSY + DSH/2
DS_GND_Y  = DSY + 0.40

t(DSX+0.20, DS_VCC_Y,  'VCC',  ha='left', sz=9, c=C_PWR, bold=True)
t(DSX+0.20, DS_DATA_Y, 'DATA', ha='left', sz=9, c=C_SIG, bold=True)
t(DSX+0.20, DS_GND_Y,  'GND',  ha='left', sz=9, c=C_GND, bold=True)

# GPIO4 routing over board top.
# Wire drops at PU_JX so the pull-up branches off cleanly, then continues to DS18B20.
ROUTE_X = 8.8           # vertical routing channel (left side of board)
OVER_Y  = BTOP + 0.95   # horizontal channel above board top
PU_JX   = DSX - 1.25    # pull-up junction x — between channel drop and DS18B20 box

wire([(LSTUB_END, Y_GPIO4),
      (ROUTE_X,   Y_GPIO4),
      (ROUTE_X,   OVER_Y),
      (PU_JX,     OVER_Y),       # stop above pull-up junction
      (PU_JX,     DS_DATA_Y),    # drop down to DATA level
      (DSX,       DS_DATA_Y)], C_SIG, lw=2.4)
ann((ROUTE_X + PU_JX)/2, OVER_Y + 0.30,
    'GPIO4  /  1-Wire data  (routed over board top)')

# Pull-up: junction on DATA wire (where wire drops from OVER_Y) → 4.7 kΩ → +3.3V
PU_JY = DS_DATA_Y
dot(PU_JX, PU_JY, C_SIG)
wire([(PU_JX, PU_JY + 0.52), (PU_JX, PU_JY)], C_PWR)
resistor_v(PU_JX, PU_JY + 1.05, '4.7 kΩ')
wire([(PU_JX, PU_JY + 1.58), (PU_JX, PU_JY + 1.90)], C_PWR)
vcc_sym(PU_JX, PU_JY + 1.90, '+3.3V')

# DS18B20 VCC: independent +3.3V symbol above box
VCC_DS_X   = DSX + DSW * 0.65
VCC_DS_BOT = DSY + DSH + 0.20
vcc_sym(VCC_DS_X, VCC_DS_BOT, '+3.3V')
wire([(VCC_DS_X, VCC_DS_BOT),
      (VCC_DS_X, DS_VCC_Y),
      (DSX,      DS_VCC_Y)], C_PWR)

# DS18B20 GND: route from right board GND_R_TOP → right of DS18B20 → down → into GND pin
GND_RAIL_X = DSX + DSW + 0.55
wire([(RSTUB_END,  Y_GND_R_TOP),
      (GND_RAIL_X, Y_GND_R_TOP),
      (GND_RAIL_X, DS_GND_Y),
      (DSX,        DS_GND_Y)], C_GND)

t(DSX+DSW/2, DSY+DSH+1.25, '② DS18B20 Temperature Probe',
  sz=9.5, c='#1b5e20', bold=True)

# ─────────────────────────────────────────────────────────────────────────────
#  ③ Battery Voltage Divider  (optional)
# ─────────────────────────────────────────────────────────────────────────────
BAT_X, BAT_Y, BAT_W, BAT_H = 0.6, 4.0, 2.6, 1.55
box(BAT_X, BAT_Y, BAT_W, BAT_H, fc='#fafafa', ec='#607d8b', lw=2.0, zo=3)
t(BAT_X+BAT_W/2, BAT_Y+BAT_H/2+0.22, 'Battery',     sz=9.5, c='#37474f', bold=True)
t(BAT_X+BAT_W/2, BAT_Y+BAT_H/2-0.24, '(LiPo / AA)', sz=8,   c='#546e7a')

BAT_POS_Y = BAT_Y + BAT_H - 0.30
BAT_NEG_Y = BAT_Y + 0.30
BAT_RX    = BAT_X + BAT_W

t(BAT_RX-0.16, BAT_POS_Y, '(+)', ha='right', sz=9, c=C_LOOP,    bold=True)
t(BAT_RX-0.16, BAT_NEG_Y, '(−)', ha='right', sz=9, c='#37474f', bold=True)

R1_CX     = 4.55
MID_X     = 5.60
MID_Y     = BAT_POS_Y
DIV_GND_Y = BAT_NEG_Y - 0.50

wire([(BAT_RX, BAT_POS_Y), (R1_CX-0.48, BAT_POS_Y)], C_LOOP)
resistor_h(R1_CX, BAT_POS_Y, 'R1  100 kΩ')
wire([(R1_CX+0.48, BAT_POS_Y), (MID_X, MID_Y)], C_LOOP)
dot(MID_X, MID_Y, C_BATT)

wire([(MID_X, MID_Y), (MID_X, MID_Y-0.50)], C_GND)
resistor_v(MID_X, MID_Y-1.0, 'R2  100 kΩ')
wire([(MID_X, MID_Y-1.50), (MID_X, DIV_GND_Y)], C_GND)
gnd_sym(MID_X, DIV_GND_Y)

BAT_GND_X = BAT_RX + 0.30
wire([(BAT_RX,    BAT_NEG_Y),
      (BAT_GND_X, BAT_NEG_Y),
      (BAT_GND_X, DIV_GND_Y-0.05)], C_GND)
gnd_sym(BAT_GND_X, DIV_GND_Y-0.05)

# Mid-point → GPIO1 on left board pin
GPIO1_STUB_END = LSTUB_END
wire([(MID_X,           MID_Y),
      (GPIO1_STUB_END,  MID_Y),
      (GPIO1_STUB_END,  Y_GPIO1)], C_BATT)
ann((MID_X + GPIO1_STUB_END)/2, MID_Y + 0.32,
    '~2.1 V at full charge  (divided battery → ADC)')

rbox(BAT_X-0.06, BAT_Y-0.54, 2.72, 0.38,
     fc='#fff8e1', ec='#f9a825', lw=1.5, zo=4, r=0.06)
t(BAT_X+BAT_W/2, BAT_Y-0.35, 'OPTIONAL', sz=8.5, c='#e65100', bold=True)
t(BAT_X+BAT_W/2, BAT_Y+BAT_H+0.32, '③ Battery Divider',
  sz=9.5, c='#37474f', bold=True)

# ─────────────────────────────────────────────────────────────────────────────
#  Title
# ─────────────────────────────────────────────────────────────────────────────
t(FIG_W/2, FIG_H-0.50,
  'WellD — Sensor Wiring Diagram',
  sz=17, c='#0d1b4b', bold=True)
t(FIG_W/2, FIG_H-1.05,
  'ESP32-C6-DevKitC-1  ·  4–20 mA Pressure Transducer  ·'
  '  DS18B20 Temperature Probe  ·  Battery Monitor (optional)',
  sz=9, c='#546e7a')

# ─────────────────────────────────────────────────────────────────────────────
#  Colour key
# ─────────────────────────────────────────────────────────────────────────────
KX, KY = 18.5, 2.2
rbox(KX-0.25, KY-0.25, 7.0, 4.5, fc='#fafafa', ec='#b0bec5', lw=1.4, zo=3, r=0.14)
t(KX+3.25, KY+4.0, 'Colour Key', sz=11, c='#0d1b4b', bold=True)

KEY_ITEMS = [
    (C_PWR,  '+3.3 V power rail'),
    (C_LOOP, 'Loop supply  (9–36 V)'),
    (C_SIG,  'Signal / 1-Wire / ADC node'),
    (C_GND,  'Ground  (GND symbols)'),
    (C_BATT, 'Battery ADC  (optional)'),
    (C_FADE, 'Unused board pin'),
]
for i, (c, lbl) in enumerate(KEY_ITEMS):
    ky = KY + 3.42 - i * 0.62
    ax.plot([KX+0.12, KX+1.05], [ky, ky],
            color=c, lw=3.0, solid_capstyle='round', zorder=5)
    dot(KX+1.05, ky, c, sz=40, zo=6)
    t(KX+1.22, ky, lbl, ha='left', sz=9, c='#212121')

# ─────────────────────────────────────────────────────────────────────────────
#  Footer
# ─────────────────────────────────────────────────────────────────────────────
t(FIG_W/2, 0.40,
  'GND symbols are all one net — connect each to a board GND pin.  '
  '+3.3V symbols connect to the board 3V3 pin.  '
  'GPIO assignments are defaults; override in sdkconfig.defaults.local.',
  sz=7.5, c='#90a4ae', italic=True)

# ─────────────────────────────────────────────────────────────────────────────
out = os.path.join(os.path.dirname(__file__), 'wiring_diagram.png')
plt.savefig(out, dpi=150, bbox_inches='tight', facecolor='white')
print(f'Saved → {out}')
