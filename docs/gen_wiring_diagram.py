#!/usr/bin/env python3
"""WellD dev-board wiring diagram (ADS1115 path) -> docs/wiring_diagram.png.

Draws the hand-wired build described in docs/wiring.md: an ESP32-C6
development board, an ADS1115 breakout on I2C (GPIO18/19, ALERT on GPIO22),
the 4-20 mA transducer loop into ADS1115 A0, an optional battery divider into
A2 and a DS18B20 on GPIO7. Pin names are the silkscreen labels; header order
differs between boards, so the board is drawn generically.

Regenerate after editing:  python3 docs/gen_wiring_diagram.py
"""

import os

import matplotlib

matplotlib.use('Agg')
import matplotlib.patches as mpatches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

# ── Canvas ────────────────────────────────────────────────────────────────────
FIG_W, FIG_H = 24, 17
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(0, FIG_W)
ax.set_ylim(0, FIG_H)
ax.set_aspect('equal')
ax.axis('off')
fig.patch.set_facecolor('#ffffff')
ax.set_facecolor('#ffffff')

# ── Palette ───────────────────────────────────────────────────────────────────
C_PWR = '#b71c1c'    # +3.3 V
C_GND = '#1a237e'    # ground
C_I2C = '#6a1b9a'    # I2C bus + ALERT
C_SIG = '#0277bd'    # analog / 1-Wire signal
C_LOOP = '#bf360c'   # loop supply (12-24 V) — never reaches the ADC side
C_BATT = '#1b5e20'   # battery divider (optional)
C_ANN = '#546e7a'    # annotation text
C_FADE = '#b0bec5'   # unused / leave-open pin

LW = 2.2
STUB = 0.45          # pin stub length outside a box


# ── Helpers ───────────────────────────────────────────────────────────────────
def box(x, y, w, h, fc='#fafafa', ec='#455a64', lw=1.8, zo=3):
    ax.add_patch(mpatches.Rectangle((x, y), w, h, lw=lw, ec=ec, fc=fc, zorder=zo))


def rbox(x, y, w, h, fc='#fafafa', ec='#455a64', lw=1.8, zo=3, r=0.1):
    ax.add_patch(mpatches.FancyBboxPatch((x, y), w, h, boxstyle=f'round,pad={r}',
                                         lw=lw, ec=ec, fc=fc, zorder=zo))


def wire(pts, c, lw=LW, zo=2):
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color=c, lw=lw, solid_capstyle='round',
            solid_joinstyle='round', zorder=zo)


def dot(x, y, c, sz=80, zo=6):
    ax.scatter([x], [y], s=sz, color=c, zorder=zo)


def t(x, y, s, ha='center', va='center', sz=9, c='#212121', bold=False,
      italic=False, zo=8):
    ax.text(x, y, s, ha=ha, va=va, fontsize=sz, color=c, zorder=zo,
            fontweight='bold' if bold else 'normal',
            fontstyle='italic' if italic else 'normal')


def ann(x, y, s, ha='center', c=C_ANN, sz=8):
    """Annotation on a white background so it reads over any wire beneath."""
    ax.text(x, y, s, ha=ha, va='center', fontsize=sz, color=c,
            fontstyle='italic', zorder=9,
            bbox=dict(fc='white', ec='none', alpha=0.92, pad=2.0))


def resistor_v(cx, cy, val, zo=5, side='right'):
    """Vertical resistor body (0.9 tall) with its value beside it."""
    w, h = 0.42, 0.90
    box(cx - w / 2, cy - h / 2, w, h, fc='#fff9c4', ec='#f57f17', lw=1.5, zo=zo)
    if side == 'right':
        t(cx + w / 2 + 0.14, cy, val, ha='left', sz=8, c='#4e342e', bold=True, zo=zo + 1)
    else:
        t(cx - w / 2 - 0.14, cy, val, ha='right', sz=8, c='#4e342e', bold=True, zo=zo + 1)


def resistor_h(cx, cy, val, zo=5):
    """Horizontal resistor body (0.9 wide) with its value above it."""
    w, h = 0.90, 0.42
    box(cx - w / 2, cy - h / 2, w, h, fc='#fff9c4', ec='#f57f17', lw=1.5, zo=zo)
    t(cx, cy + h / 2 + 0.2, val, ha='center', sz=8, c='#4e342e', bold=True, zo=zo + 1)


def cap_v(cx, cy, val, c=C_SIG, zo=5):
    """Vertical capacitor: two plates centred on (cx, cy), leads 0.45 each way."""
    gap, pw = 0.09, 0.30
    wire([(cx, cy + 0.45), (cx, cy + gap)], c, zo=zo)
    wire([(cx, cy - gap), (cx, cy - 0.45)], C_GND, zo=zo)
    for yy in (cy + gap, cy - gap):
        ax.plot([cx - pw, cx + pw], [yy, yy], color='#37474f', lw=2.6, zorder=zo + 1)
    t(cx + pw + 0.12, cy, val, ha='left', sz=8, c='#4e342e', bold=True, zo=zo + 1)


def gnd_sym(x, y, zo=5):
    """Ground symbol hanging below (x, y): three shrinking bars."""
    for i, hw in enumerate([0.28, 0.18, 0.09]):
        ax.plot([x - hw, x + hw], [y - i * 0.13, y - i * 0.13], color=C_GND,
                lw=2.0, zorder=zo)


def vcc_sym(x, y, lbl='+3.3V', zo=5):
    """+3.3 V rail arrow pointing up from (x, y)."""
    ax.annotate('', xy=(x, y + 0.40), xytext=(x, y),
                arrowprops=dict(arrowstyle='->', color=C_PWR, lw=2.1), zorder=zo)
    t(x, y + 0.62, lbl, sz=8.5, c=C_PWR, bold=True, zo=zo + 1)


def pin_right(x_edge, y, lbl, c, used=True, lc=None):
    """Stub leaving a box's right edge; label inside the box (colour lc)."""
    cc = c if used else C_FADE
    ax.plot([x_edge, x_edge + STUB], [y, y], color=cc, lw=2.4 if used else 1.2, zorder=4)
    t(x_edge - 0.12, y, lbl, ha='right', sz=8.5 if used else 7.5,
      c=lc or cc, bold=used)


def pin_left(x_edge, y, lbl, c, used=True):
    """Stub leaving a box's left edge; label inside the box."""
    cc = c if used else C_FADE
    ax.plot([x_edge - STUB, x_edge], [y, y], color=cc, lw=2.4 if used else 1.2, zorder=4)
    t(x_edge + 0.12, y, lbl, ha='left', sz=8.5 if used else 7.5, c=cc, bold=used)


# ── Title ─────────────────────────────────────────────────────────────────────
t(FIG_W / 2, FIG_H - 0.45, 'WellD — Dev-Board Wiring (ADS1115)', sz=17,
  c='#0d1b4b', bold=True)
t(FIG_W / 2, FIG_H - 0.98,
  'ESP32-C6 dev board  ·  ADS1115 16-bit ADC on I²C (0x48)  ·  4–20 mA transducer '
  'on A0  ·  battery divider on A2 (optional)  ·  DS18B20 on GPIO7',
  sz=9.5, c=C_ANN)

# ─────────────────────────────────────────────────────────────────────────────
#  Pin rows shared by the board's right edge and the ADS1115's left edge, so
#  every board-to-ADS1115 wire is a straight horizontal line.
# ─────────────────────────────────────────────────────────────────────────────
Y_VDD, Y_GND, Y_SCL, Y_SDA, Y_ADDR, Y_ALRT = 11.9, 11.2, 10.5, 9.8, 9.1, 8.4
Y_GPIO7 = 6.0

# ── ESP32-C6 development board ────────────────────────────────────────────────
BX, BY, BW, BH = 2.2, 3.3, 3.8, 9.6
BR = BX + BW                     # right edge
rbox(BX, BY, BW, BH, fc='#2e7d32', ec='#1b5e20', lw=3.0, zo=3, r=0.18)
box(BX + 0.9, BY + BH - 3.0, 2.0, 2.2, fc='#1c1c1c', ec='#424242', lw=1.2, zo=4)
t(BX + 1.9, BY + BH - 1.55, 'ESP32-C6', sz=9, c='white', bold=True, zo=5)
t(BX + 1.9, BY + BH - 2.05, 'module', sz=7, c='#9e9e9e', zo=5)
t(BX + 1.6, BY + 2.25, 'ESP32-C6', sz=10, c='#e8f5e9', bold=True)
t(BX + 1.6, BY + 1.8, 'dev board', sz=10, c='#e8f5e9', bold=True)
t(BX + 1.6, BY + 1.25, 'pins as printed on\nthe board (header\norder varies)',
  sz=6.8, c='#a5d6a7', italic=True)

# USB connector on the bottom edge
ax.add_patch(mpatches.FancyBboxPatch((BX + 1.2, BY - 0.45), 1.0, 0.45,
                                     boxstyle='round,pad=0.05', lw=1.5,
                                     ec='#78909c', fc='#eceff1', zorder=4))
t(BX + 1.7, BY - 0.22, 'USB', sz=7, c='#607d8b')
ann(BX + 1.7, BY - 0.85, 'power + serial monitor')

# Used pins (right edge)
pin_right(BR, Y_VDD, '3V3', C_PWR, lc='white')
pin_right(BR, Y_GND, 'GND', C_GND, lc='white')
pin_right(BR, Y_SCL, 'GPIO19', C_I2C, lc='white')
pin_right(BR, Y_SDA, 'GPIO18', C_I2C, lc='white')
pin_right(BR, Y_ALRT, 'GPIO22', C_I2C, lc='white')
pin_right(BR, Y_GPIO7, 'GPIO7', C_SIG, lc='white')

# Firmware-owned PCB pins (left edge) — leave unconnected on a dev board
LEAVE = [('GPIO5', 'loop-boost enable (output)'),
         ('GPIO15', 'divider enable (output)'),
         ('GPIO6', 'solar status (pull-up)'),
         ('GPIO23', 'factory reset (pull-up)')]
for i, (lbl, why) in enumerate(LEAVE):
    y = 11.3 - i * 0.75
    ax.plot([BX - STUB, BX], [y, y], color=C_FADE, lw=1.4, zorder=4)
    t(BX + 0.12, y, lbl, ha='left', sz=7.5, c='#c8e6c9', bold=True)
    t(BX - STUB - 0.1, y, why, ha='right', sz=7, c=C_ANN, italic=True)
t(BX - 1.55, 12.05, 'leave unconnected', sz=8, c='#78909c', bold=True)
t(BX - 1.55, 11.75, '(PCB-only functions)', sz=7, c='#78909c', italic=True)

# ── ① ADS1115 breakout ────────────────────────────────────────────────────────
AX, AY, AW, AH = 9.4, 7.8, 3.0, 4.75
AR = AX + AW
box(AX, AY, AW, AH, fc='#ede7f6', ec='#4527a0', lw=2.2, zo=3)
t(AX + AW / 2, AY + AH - 0.35, 'ADS1115', sz=10.5, c='#4527a0', bold=True)
t(AX + AW / 2, AY + 0.32, '16-bit ADC breakout', sz=7.5, c='#5e35b1', italic=True)
t(AX + AW / 2, AY + AH + 0.55, '① ADS1115 ADC module', sz=10, c='#4527a0', bold=True)

for y, lbl, c in [(Y_VDD, 'VDD', C_PWR), (Y_GND, 'GND', C_GND), (Y_SCL, 'SCL', C_I2C),
                  (Y_SDA, 'SDA', C_I2C), (Y_ADDR, 'ADDR', C_GND), (Y_ALRT, 'ALRT', C_I2C)]:
    pin_left(AX, y, lbl, c)

Y_A0, Y_A1, Y_A2, Y_A3 = 11.5, 10.7, 9.9, 9.1
pin_right(AR, Y_A0, 'A0', C_SIG)
pin_right(AR, Y_A1, 'A1', C_FADE, used=False)
pin_right(AR, Y_A2, 'A2', C_BATT)
pin_right(AR, Y_A3, 'A3', C_FADE, used=False)

# Board → ADS1115: straight wires
for y, c in [(Y_VDD, C_PWR), (Y_GND, C_GND), (Y_SCL, C_I2C), (Y_SDA, C_I2C),
             (Y_ALRT, C_I2C)]:
    wire([(BR + STUB, y), (AX - STUB, y)], c)
ann((BR + AX) / 2, Y_SCL + 0.33, 'SCL')
ann((BR + AX) / 2, Y_SDA + 0.33, 'SDA')
ann((BR + AX) / 2, Y_ALRT + 0.33, 'ALERT / data-ready (recommended)')

# ADDR → GND selects address 0x48
wire([(AX - STUB, Y_ADDR), (AX - 0.95, Y_ADDR), (AX - 0.95, Y_ADDR - 0.15)], C_GND)
gnd_sym(AX - 0.95, Y_ADDR - 0.15)
t(AX - 1.35, Y_ADDR + 0.02, '0x48', ha='right', sz=7.5, c=C_GND, bold=True)

# ── ② Pressure transducer loop → A0 ─────────────────────────────────────────
CAP_X = 13.75          # 100 nF filter cap (A0 side of the series resistor)
RS_X = 15.15           # 4.7 kΩ series resistor centre
SH_X = 16.75           # shunt node
TRX, TRY, TRW, TRH = 18.6, 10.4, 2.9, 2.1     # transducer box
LSX, LSY, LSW, LSH = 18.6, 13.35, 2.9, 1.15   # loop supply box

wire([(AR + STUB, Y_A0), (RS_X - 0.45, Y_A0)], C_SIG)
dot(CAP_X, Y_A0, C_SIG)
cap_v(CAP_X, Y_A0 - 0.75, '100 nF')
gnd_sym(CAP_X, Y_A0 - 1.20)
resistor_h(RS_X, Y_A0, '4.7 kΩ')
ann(RS_X, Y_A0 + 0.8, 'protects A0 if the cable shorts', sz=7.3)
wire([(RS_X + 0.45, Y_A0), (TRX, Y_A0)], C_SIG)
dot(SH_X, Y_A0, C_SIG)
wire([(SH_X, Y_A0), (SH_X, Y_A0 - 0.55)], C_SIG)
resistor_v(SH_X, Y_A0 - 1.0, '100 Ω shunt\n0.1–1 %')
wire([(SH_X, Y_A0 - 1.45), (SH_X, Y_A0 - 1.85)], C_GND)
gnd_sym(SH_X, Y_A0 - 1.85)
ann(SH_X + 0.05, Y_A0 + 0.42, 'shunt node 0.4–2.0 V')

box(TRX, TRY, TRW, TRH, fc='#e3f2fd', ec='#0d47a1', lw=2.2, zo=3)
t(TRX + TRW / 2 + 0.2, TRY + TRH / 2 + 0.2, 'Pressure', sz=10, c='#0d47a1', bold=True)
t(TRX + TRW / 2 + 0.2, TRY + TRH / 2 - 0.2, 'transducer', sz=10, c='#0d47a1', bold=True)
t(TRX + TRW / 2 + 0.2, TRY + TRH / 2 - 0.6, '4–20 mA, 2-wire', sz=8, c='#1565c0')
t(TRX + 0.15, Y_A0, '(−)', ha='left', sz=9, c='#37474f', bold=True)
PLUS_X = TRX + TRW - 0.55
t(PLUS_X, TRY + TRH - 0.25, '(+)', sz=9, c=C_LOOP, bold=True)

rbox(LSX, LSY, LSW, LSH, fc='#fff3e0', ec=C_LOOP, lw=1.8, zo=3, r=0.07)
t(LSX + LSW / 2, LSY + 0.78, 'Loop supply', sz=9, c=C_LOOP, bold=True)
t(LSX + LSW / 2, LSY + 0.38, '12–24 V DC, current-limited', sz=7.5, c=C_LOOP)
t(PLUS_X, LSY + 0.13, '+', sz=9, c=C_LOOP, bold=True)
t(LSX + 0.2, LSY + LSH / 2 - 0.02, '−', ha='left', sz=10, c=C_GND, bold=True)
wire([(PLUS_X, LSY), (PLUS_X, TRY + TRH)], C_LOOP, zo=4)
LSG_X = LSX - 0.8
wire([(LSX, LSY + LSH / 2), (LSG_X, LSY + LSH / 2), (LSG_X, LSY - 0.05)], C_GND)
gnd_sym(LSG_X, LSY - 0.05)
ann(LSG_X - 0.15, LSY + LSH / 2 + 0.38, '(−) to board GND!', ha='right', c=C_GND)
t(LSX + LSW / 2, LSY + LSH + 0.5, '② 4–20 mA pressure transducer', sz=10,
  c='#0d47a1', bold=True)

# ── ④ Battery divider (optional) → A2 ───────────────────────────────────────
BAX, BAY, BAW, BAH = 19.8, 4.5, 2.4, 1.6
BAT_P_Y = BAY + BAH - 0.4
BAT_N_Y = BAY + 0.4
MID_X = 16.9
R1_X = 18.45
A2_RISE_X = 13.25

box(BAX, BAY, BAW, BAH, fc='#fafafa', ec='#607d8b', lw=2.0, zo=3)
t(BAX + BAW / 2 + 0.15, BAY + BAH / 2 + 0.2, 'Battery', sz=9.5, c='#37474f', bold=True)
t(BAX + BAW / 2 + 0.15, BAY + BAH / 2 - 0.22, '1S Li-ion', sz=8, c='#546e7a')
t(BAX + 0.15, BAT_P_Y, '(+)', ha='left', sz=9, c=C_LOOP, bold=True)
t(BAX + 0.15, BAT_N_Y, '(−)', ha='left', sz=9, c='#37474f', bold=True)

wire([(BAX, BAT_P_Y), (R1_X + 0.45, BAT_P_Y)], C_LOOP)
resistor_h(R1_X, BAT_P_Y, 'R1 100 kΩ')
wire([(R1_X - 0.45, BAT_P_Y), (MID_X, BAT_P_Y)], C_BATT)
dot(MID_X, BAT_P_Y, C_BATT)
wire([(MID_X, BAT_P_Y), (MID_X, BAT_P_Y - 0.5)], C_BATT)
resistor_v(MID_X, BAT_P_Y - 0.95, 'R2 100 kΩ', side='left')
wire([(MID_X, BAT_P_Y - 1.4), (MID_X, BAT_P_Y - 1.75)], C_GND)
gnd_sym(MID_X, BAT_P_Y - 1.75)
BN_X = BAX - 0.45
wire([(BAX, BAT_N_Y), (BN_X, BAT_N_Y), (BN_X, BAT_N_Y - 0.35)], C_GND)
gnd_sym(BN_X, BAT_N_Y - 0.35)

wire([(MID_X, BAT_P_Y), (A2_RISE_X, BAT_P_Y), (A2_RISE_X, Y_A2),
      (AR + STUB, Y_A2)], C_BATT)
ann((A2_RISE_X + MID_X) / 2, BAT_P_Y + 0.36, '≈2.1 V at 4.2 V (half the cell)')

rbox(BAX - 0.6, BAY - 1.55, 3.6, 0.95, fc='#fff8e1', ec='#f9a825', lw=1.5, zo=4, r=0.06)
t(BAX + 1.2, BAY - 0.85, 'OPTIONAL', sz=8.5, c='#e65100', bold=True)
t(BAX + 1.2, BAY - 1.22, 'No battery? Wire A2 straight to GND', sz=7.5, c='#e65100')
t(BAX + 1.2, BAY + BAH + 0.45, '④ Battery divider', sz=10, c='#37474f', bold=True)

# ── ③ DS18B20 on GPIO7 ───────────────────────────────────────────────────────
DSX, DSY, DSW, DSH = 9.4, 2.6, 3.0, 2.5
DS_VCC_Y, DS_DATA_Y, DS_GND_Y = DSY + DSH - 0.5, DSY + DSH / 2, DSY + 0.5
DS_CONN_X = DSX - 0.65
PU_X = 8.1
DROP_X = 7.2

box(DSX, DSY, DSW, DSH, fc='#e8f5e9', ec='#1b5e20', lw=2.2, zo=3)
t(DSX + DSW / 2 + 0.35, DSY + DSH * 0.66, 'DS18B20', sz=10, c='#1b5e20', bold=True)
t(DSX + DSW / 2 + 0.35, DSY + DSH * 0.42, 'temperature', sz=8.5, c='#2e7d32')
t(DSX + DSW / 2 + 0.35, DSY + DSH * 0.24, 'probe', sz=8.5, c='#2e7d32')
t(DSX + 0.15, DS_VCC_Y, 'VCC (red)', ha='left', sz=8, c=C_PWR, bold=True)
t(DSX + 0.15, DS_DATA_Y, 'DATA', ha='left', sz=8, c=C_SIG, bold=True)
t(DSX + 0.15, DS_GND_Y, 'GND (black)', ha='left', sz=8, c=C_GND, bold=True)
t(DSX + DSW / 2, DSY - 0.4, '③ DS18B20 temperature probe', sz=10, c='#1b5e20', bold=True)

wire([(DS_CONN_X, DS_VCC_Y), (DSX, DS_VCC_Y)], C_PWR, zo=4)
wire([(DS_CONN_X, DS_DATA_Y), (DSX, DS_DATA_Y)], C_SIG, zo=4)
wire([(DS_CONN_X, DS_GND_Y), (DSX, DS_GND_Y)], C_GND, zo=4)
vcc_sym(DS_CONN_X, DS_VCC_Y)
gnd_sym(DS_CONN_X, DS_GND_Y - 0.05)

# GPIO7 → drop → DATA; 4.7 kΩ pull-up from the DATA line to +3.3 V
wire([(BR + STUB, Y_GPIO7), (DROP_X, Y_GPIO7), (DROP_X, DS_DATA_Y),
      (DS_CONN_X, DS_DATA_Y)], C_SIG)
ann((BR + STUB + DROP_X) / 2 + 0.05, Y_GPIO7 + 0.33, '1-Wire data')
dot(PU_X, DS_DATA_Y, C_SIG)
wire([(PU_X, DS_DATA_Y), (PU_X, DS_DATA_Y + 0.5)], C_PWR)
resistor_v(PU_X, DS_DATA_Y + 0.95, '4.7 kΩ', side='left')
wire([(PU_X, DS_DATA_Y + 1.4), (PU_X, DS_DATA_Y + 1.6)], C_PWR)
vcc_sym(PU_X, DS_DATA_Y + 1.6)

# ── Colour key ────────────────────────────────────────────────────────────────
KX, KY = 0.5, 0.2
KEY = [(C_PWR, '+3.3 V (board 3V3 pin)'),
       (C_GND, 'Ground — all GND symbols are one net'),
       (C_I2C, 'I²C bus + ALERT'),
       (C_SIG, 'Signal: shunt → A0, 1-Wire'),
       (C_LOOP, 'Loop supply / battery (+)'),
       (C_BATT, 'Divided battery → A2'),
       (C_FADE, 'Unused / leave open')]
rbox(KX, KY, 6.9, 1.85, fc='#fafafa', ec='#b0bec5', lw=1.4, zo=3, r=0.12)
for i, (c, lbl) in enumerate(KEY):
    col, row = divmod(i, 4)
    kx = KX + 0.2 + col * 3.55
    ky = KY + 1.6 - row * 0.42
    ax.plot([kx, kx + 0.55], [ky, ky], color=c, lw=3.0, solid_capstyle='round', zorder=5)
    t(kx + 0.7, ky, lbl, ha='left', sz=7.3, c='#212121')

# ── Footer ────────────────────────────────────────────────────────────────────
t(FIG_W / 2 + 2.5, 0.75,
  '+3.3V arrows and GND symbols are the board 3V3 / GND pins — connect each to the '
  'nearest one.  Default GPIOs shown; change them in sdkconfig.defaults.local '
  '(see docs/wiring.md).', sz=7.8, c='#78909c', italic=True)
t(FIG_W / 2 + 2.5, 0.38,
  'The WellD PCB has all of this on board — this drawing is for hand-wired '
  'dev-board builds only.', sz=7.8, c='#78909c', italic=True)

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wiring_diagram.png')
plt.savefig(out, dpi=150, bbox_inches='tight', facecolor='white')
print(f'Saved → {out}')
