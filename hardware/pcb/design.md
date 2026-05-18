# WellD Custom PCB — Design Reference

## Overview

| Parameter | Value |
|-----------|-------|
| Module | ESP32-C6-MINI-1U (external antenna, U.FL) |
| Form factor | 80 × 55 mm, 2-layer, 1 oz Cu |
| Target enclosure | Custom 3D-printed case (`hardware/case/`) or Hammond 1551K equiv. |
| MCU supply | 3.3 V from TPS7A0533 LDO (1 µA Iq), fed from LiPo |
| LiPo charging | USB-C via TP4056 (580 mA, GPIO4-interlocked) + solar via CN3791 MPPT (500 mA) |
| Solar input | 5–6.5 V, ≤ 7.5 V Voc (5 W / 6 V panel); J12 screw terminal |
| Loop supply | 12 V boost (TPS61023, U8) from VBAT, GPIO5-gated; powers 2-wire 4–20 mA transmitters |
| Sensor interfaces | 2× 4–20 mA (screw terminals), 1× DS18B20, 1× spare 3-pin, 1× solar 2-pin |
| External ADC | ADS1115 16-bit I²C (U9, 0.1% non-linearity) replaces ESP32 ADC for depth/battery channels |
| Fuel gauge | MAX17048 coulomb-counting I²C SoC (U10) on shared I²C bus |
| Expansion | I²C header, 6-pin GPIO header, 4 spare ADC channels |
| Programming | 6-pin 1.27 mm UART header; no USB bridge on board |

---

## GPIO Assignments

All ADC1 channels (GPIO0–GPIO3) are available for analog backup use. Primary depth and
battery voltage measurements are handled by U9 (ADS1115) over I²C. GPIO4 controls the
TP4056 charger interlock (Q1). GPIO5 gates the 12 V VLOOP boost converter (U8). GPIO6
disables CN3791 solar charging. GPIO10/11 are the shared I²C bus for ADS1115 and MAX17048.

| GPIO | ADC ch | Function | Connected to |
|------|--------|----------|--------------|
| 0 | CH0 | 4–20 mA CH1 (backup) | Shunt R2 → limiter R3 → GPIO0; primary reading via U9 ADS1115 |
| 1 | CH1 | Battery voltage (backup) | Divider R7/R8 → GPIO1 when Q2 enabled; primary via U9 AIN2 |
| 2 | CH2 | 4–20 mA CH2 (backup) | Shunt R4 → limiter R5 → GPIO2; primary reading via U9 ADS1115 |
| 3 | CH3 | Spare ADC | J9 expansion header |
| 4 | — | CHRG_USB_DIS | Gate of Q1 (N-MOSFET); pulls TP4056 CE low to inhibit USB charging when solar is active |
| 5 | — | VBOOST_EN | TPS61023 EN pin; firmware drives HIGH only during 4–20 mA measurement window |
| 6 | — | Solar CHRG detect | CN3791 open-drain /CHRG output (active-LOW = charging in progress); GPIO6 configured as input with internal pull-up; read LOW = solar charging active |
| 7 | — | DS18B20 1-Wire | J6 screw terminal |
| 8 | — | Strapping pull-up | 10 kΩ to 3.3 V, test pad |
| 9 | — | BOOT strapping | 10 kΩ pull-up; SW2 to GND |
| 10 | — | I²C SDA | J8 header, ADS1115, MAX17048; 4.7 kΩ pull-up R9 |
| 11 | — | I²C SCL | J8 header, ADS1115, MAX17048; 4.7 kΩ pull-up R10 |
| 12 | — | ADS1115_ALERT / DRDY | ALERT/RDY pin of U9; interrupt-driven conversion ready |
| 13 | — | Status LED | 1 kΩ → D4 → GND; SJ3 to disconnect |
| 14 | — | MAX17048_ALRT | ALRT pin of U10; low-battery interrupt; external pull-up R27 (4.7 kΩ to 3.3V) |
| 15 | — | BATT_DIV_EN | Gate of Q2 (N-MOSFET); enables battery voltage divider only during measurement |
| 16 | — | UART0 TX | J10 programming header |
| 17 | — | UART0 RX | J10 programming header |
| 18 | — | Spare | Unused — USB-C is power-only, no USB data path |
| 19 | — | Spare | Unused — USB-C is power-only, no USB data path |
| 20 | — | Spare digital | J9 expansion header |
| 21 | — | Spare digital | J9 expansion header |

> **USB note:** GPIO12/GPIO13 are the ESP32-C6 on-chip USB-Serial-JTAG D−/D+
> lines. This board repurposes them (GPIO12 → ADS1115 DRDY, GPIO13 → status LED)
> and the USB-C connector carries power only, so the native USB-Serial-JTAG
> interface is not available. All flashing and debug is over the J10 UART header.

---

> **Firmware requirements:**
> 1. GPIO5 HIGH before any 4–20 mA reading; LOW after. Allow 5 ms for TPS61023 soft-start.
> 2. GPIO15 HIGH for 1 ms before battery ADC read via U9 AIN2; LOW after.
> 3. GPIO4 HIGH when GPIO6 reads LOW (/CHRG_SOLAR active-LOW — LOW = solar is charging in progress). GPIO6 uses internal pull-up.
> 4. Read U9 ADS1115 via I²C for all depth and battery voltage measurements; keep GPIO0/1/2 reads as fallback.
> 5. Read U10 MAX17048 via I²C for SOC%; report via Zigbee EP2 (battery voltage) using the calibrated SOC value.
> 6. Implement GPIO12 DRDY interrupt for ADS1115 single-shot completion signalling.

---

## Block Descriptions

## Solar Charging

A 5 W solar panel connects via a 2-pin pluggable screw terminal (J12, Phoenix MC
1.5/2-ST-3.5) on the bottom edge. The solar path uses a dedicated MPPT charger
(U7: CN3791) that maximises charge current under partially-shaded or early-morning
conditions where panel voltage sags below Vmp.

### Solar panel selection

| Panel spec | Requirement |
|------------|-------------|
| Vmp | 5.0–6.5 V (CN3791 input range) |
| Voc | ≤ 7.5 V (CN3791 absolute max) |
| Isc | ≤ 1.5 A (CN3791 max charge current) |
| Typical match | 5 W / 6 V rigid or flexible panel, or USB 5 V regulated panel output |

12 V panels are **not** compatible — the CN3791 will be damaged. Use a buck
pre-regulator if a 12 V panel is required.

### MPPT setting (R20/R21)

CN3791 regulates its VIN to maintain VMPPT = 1.205 V at the MPPT pin. The
resistor divider R20/R21 (from VIN to GND, midpoint to MPPT) sets the target
operating point:

    Vmppt_target = 1.205 × (R20 + R21) / R21

Default values: R20 = 36 kΩ, R21 = 10 kΩ → Vmppt = 1.205 × 46/10 = **5.5 V**
(correct for a 6 V nominal panel with Vmp ≈ 5.5 V).

For a regulated 5 V USB panel output, change R20 to 30 kΩ → Vmppt ≈ 4.8 V.

The divider senses the CN3791 VIN pin, which sits one Schottky drop below the
panel terminal (D6 is in series ahead of VIN). The panel therefore operates at
roughly Vmppt + Vf(D6) ≈ Vmppt + 0.4 V. Account for this when matching the divider
to a panel's true Vmp — drop R20 slightly if the panel should sit exactly at Vmp.

### Charge current (R19)

CN3791 PROG pin: R19 = 2 kΩ → 500 mA charge current. This draws ≈ 600 mA from
a 6 V panel at the MPPT point (accounting for ~85 % conversion efficiency) — well
within a 5 W panel's Isc. For smaller panels or higher battery capacity, raise R19:
3.3 kΩ → 300 mA.

### Solar terminal ESD protection (D14)

D14 (SMAJ7.0A, DO-214AC/SMA, unidirectional TVS, 7.0 V standoff, 400 W peak)
is placed from J12 SOLAR+ (pin 1) to GND, **before** D6 (the Schottky input diode).
It provides the first stage of a two-stage solar transient protection chain:

    J12 SOLAR+ → D14 (SMAJ7.0A, first-stage, at terminal)
               → D6 (MBRS140 Schottky, backfeed block)
               → D8 (SMAJ7.0A, second-stage, at CN3791 VIN)
               → CN3791 VIN (abs max 7.5 V)

Standoff selection rationale:
- Normal MPPT operating range: 4.5 V to 6.5 V. The 7.0 V standoff is 7.7 % above
  the 6.5 V maximum, so D14 does not conduct during MPPT regulation.
- Panel Voc constraint: ≤ 7.5 V per design requirement. At Voc = 7.5 V (no-load),
  D14 begins to conduct slightly, clamping the terminal and preventing the full
  open-circuit voltage from reaching D6 and CN3791. This is the intended behaviour.
- Unidirectional: the solar input is a single-polarity power rail; reverse polarity
  is handled by D6. A unidirectional TVS from rail to GND is correct here.
- Same MPN as D8 (SMAJ7.0A, LCSC C78310) — consolidate on one tape reel.

Place D14 within 3 mm of J12 pin 1, on the terminal side of D6.

### Input protection (D6)

A Schottky diode (D6: MBRS140, SOD-123) in series with J12 pin 1 prevents backfeed
from the battery through U7 when the panel is dark or disconnected, and provides
reverse-polarity protection for miswired panels.

### USB + solar coexistence

Both TP4056 (USB, U2) and CN3791 (solar, U7) share the VBAT rail directly. Each IC
has its own CC/CV termination; the battery voltage clamps both simultaneously. Total
charge current when both inputs are active = IUSB + ISOLAR — ensure the combined
current stays within the battery's max charge rate (typically 1 C). Separating the
charge sources with Schottky diodes is **not** recommended here — it would prevent
each IC from accurately sensing the battery terminal voltage and would degrade
termination accuracy. If simultaneous operation is a concern, drive the CN3791
PROG pin high-Z via GPIO6 (currently spare ADC, can be repurposed as a digital
output) to disable solar charging when USB is detected on VUSB.

---

### Power — Input & Reverse Polarity (D5 + R31)

D5 (AO3407, SOT-23, P-channel MOSFET) provides reverse-polarity protection in series
with the BAT+ rail, downstream of D13 (the battery terminal TVS). It is placed between
J1 BAT+ and the VBAT system rail:

    J1 BAT+ → D13 (SMAJ5.0CA TVS, across terminal) → D5 source → D5 drain → VBAT rail

D5 wiring:
- Source: J1 BAT+ terminal (VBAT_RAW node, after D13 TVS)
- Drain: VBAT system rail (feeds U3 S-8261AAYFT, U4 FS8205A, U10 MAX17048, U1 LDO)
- Gate: GND (through R31 — see below)

R31 (10 kΩ, 0402) connects D5 gate to GND. This resistor is mandatory:
- Holds gate at 0 V so Vgs = 0 − Vbat = −Vbat, keeping D5 fully saturated during
  normal operation.
- Defines the off-state (gate floating HIGH if battery disconnected would leave D5 off
  and prevent body-diode-mediated inrush — the pull-down ensures gate = 0 V so
  D5 turns on immediately when a good battery is connected).
- Limits gate capacitance charge current on hot-plug events.
- RC time constant with gate capacitance (~50 pF typical): τ = 10 kΩ × 50 pF = 500 ns;
  MOSFET reaches full enhancement in < 3 µs — not perceptible at the system level.

AO3407 electrical justification:
- Vgs(th) max: −1.5 V. At minimum battery voltage 3.0 V, Vgs = −3.0 V, giving 1.5 V
  margin above |Vgs(th)| max — D5 is fully saturated at the lowest expected battery
  voltage. The DMG2305UX (|Vgs(th)| max 2.0 V) has only 1.0 V margin at 3.0 V and is
  a worse fit for this battery voltage range.
- RDS(on) max: 55 mΩ @ Vgs = −4.5 V. At Vgs = −4.2 V (full charge), RDS(on) is ≤
  55 mΩ → drop at 1 A continuous ≤ 55 mV. Peak charge + discharge current ≤ 2 A →
  worst-case drop ≤ 110 mV, well within acceptable limits.
- Vgs absolute maximum: ±12 V. Maximum Vgs magnitude = 4.2 V (full charge battery
  on source, gate at 0 V) — 65 % below the abs max. No gate-drain voltage clamp is
  required.
- ID max: 3 A continuous, 20 A pulsed. Continuous 1 A and peak 2 A are well within
  the SOT-23 package thermal limits at ambient temperature.

Operation with reversed battery:
- Battery − connected to J1 BAT+, battery + to J1 BAT−: source is driven negative,
  gate remains at 0 V (pulled down by R31), Vgs = 0 − (negative voltage) = positive.
  A positive Vgs does not turn on a P-channel MOSFET; D5 stays off.
- The body diode is forward-biased from drain to source in this reversed condition,
  but the drain (VBAT rail) is at 0 V (system unpowered), so no significant current
  flows. The D13 TVS at the terminal absorbs transient energy from a hot-plug event.

A diode alternative (e.g. MBR0530) is explicitly rejected: the ~300 mV forward drop
at 1 A shifts the voltage seen by MAX17048 (VCELL pin, connected to VBAT rail) and
the S-8261AAYFT (VCC pin) by 300 mV, corrupting the 2.9 V over-discharge threshold
and the MAX17048 SOC model calibration. The MOSFET solution has ≤ 55 mV drop which
is within the measurement uncertainty of the MAX17048 model and below the S-8261AAYFT
threshold hysteresis band of 100 mV.

### Power — LiPo Charging (U2: TP4056)

Single-cell LiPo charger, SOP-8. Charge current set by R1 (RPROG pin to GND):
- 2 kΩ → ~580 mA (for 500–1000 mAh cells, USB 500 mA limit safe)

Charge and standby status LEDs (D2, D3) are optional populate — omit in production
to eliminate their draw. USB-C input (J2) feeds VBUS through a 1 A fuse (F1) to the
TP4056 VCC pin.

USB-C CC resistors: two 5.1 kΩ to GND on CC1 and CC2 (R15, R16) present the device
as a USB sink to any USB-C charger. No USB data path on this connector.

ESD protection on USB lines: U5 (USBLC6-2SC6, SOT-23-6) clamps D+ and D− to VBUS
and GND during ESD events.

### Power — Solar MPPT Charging (U7: CN3791)

MPPT solar charger, SOP-8. Accepts 4.5–6.5 V from J12 (via D6 Schottky protection).
Charges the shared VBAT rail to 4.2 V with constant-current / constant-voltage profile.

Key passives:
- R19 (2.0 kΩ, PROG pin to GND): sets charge current to ~500 mA.
- R20 (36 kΩ) + R21 (10 kΩ) divider from VIN to GND, midpoint to MPPT pin: targets
  Vmppt = 5.5 V (optimal for a 6 V nominal / Vmp 5.5 V panel).
- C17 (10 µF, 0805) on VIN: input filter.
- C18 (10 µF, 0805) on VBAT: output filter.
- D7 (green LED, DNF) with R22 (1 kΩ) on CHRG pin: solar charge indicator.

The CN3791 EN/shutdown pin is connected to GPIO6 via a 10 kΩ pull-up to +3V3 —
pull LOW from firmware to disable solar charging when USB is detected.

### Power — Battery Terminal ESD Protection (D13)

D13 (SMAJ5.0CA, DO-214AC/SMA, bidirectional TVS, 5.0 V standoff, 200 W peak pulse
power) is placed across J1 BAT+ and BAT- (the system GND side of the battery
connector, before D5 the reverse-polarity P-MOSFET). It absorbs ESD and inductive
cable transients on the battery wiring in both polarities.

Standoff selection rationale:
- Normal battery voltage range: 3.0 V (over-discharge cutoff per S-8261AAYFT) to
  4.2 V (full charge). The SMAJ5.0CA standoff is 5.0 V — 19 % above the 4.2 V
  maximum, so it does not conduct during normal charge/discharge cycles.
- Clamp voltage at 10 A pulse: 9.2 V. The S-8261AAYFT VCC absolute maximum is
  ~6.5 V; the FS8205A gate-source absolute maximum is ±20 V. The 9.2 V clamp
  voltage during a transient is above the S-8261AAYFT abs max — D13 is intended
  to absorb ESD (sub-microsecond) energy that otherwise arrives as a much higher
  uncontrolled voltage spike. For sustained overvoltage beyond 6.5 V, the
  S-8261AAYFT over-charge protection is the active limit.
- Bidirectional: required because charge current flows into BAT+ and discharge
  current flows out of BAT+. Both polarities of transient must be clamped.
- DO NOT substitute a unidirectional TVS on a bidirectional power rail.

Place D13 within 5 mm of J1, on the same side of the PCB as U3/U4. Anode/cathode
orientation is symmetric for bidirectional TVS — either orientation is correct.

### Power — LiPo Protection (U3: S-8261AAYFT + U4: FS8205A)

U3 is the **S-8261AAYFT** (Seiko Instruments, SOT-23-6). It trips at 2.9 V
over-discharge (with 0.1 V hysteresis, i.e. recovery at 3.0 V) and 4.28 V
over-charge. The 2.9 V cutoff keeps the cell above the LiPo safe floor of 3.0 V;
a lower cutoff would degrade cell capacity by ≈ 30 % per 100 cycles. SOT-23-6
pinout: OD, OC, CS, NC/TM, GND, VCC.

U4 (FS8205A, SOT-23-6) provides the dual back-to-back MOSFET switch driven by U3
for over-discharge, over-charge, and over-current protection. J1 is a JST XH
connector (2.5 mm pitch, B2B-XH-AM) — JST XH has high retention force and is robust
for field battery connector use. Place U3 and U4 as close to J1 as possible.

### Power — VLOOP 12 V Boost (U8: TPS61023)

The VLOOP rail supplies 2-wire 4–20 mA pressure transmitters, which require ≥ 10 V
to operate their internal electronics. U8 (TPS61023DCKR, SOT-23-5, synchronous
boost) converts VBAT (3.0–4.2 V) to 12 V when the EN pin is driven HIGH by GPIO5.
The output voltage is set by a resistor divider from VOUT to the FB pin (0.5 V
reference):

    VOUT = 0.5 × (1 + R23/R24) = 0.5 × (1 + 1.1 MΩ / 47 kΩ) ≈ 12.2 V

The high divider impedance keeps the FB leg current to ≈ 10 µA while the boost is
enabled. The TPS61023 FB bias current is small but non-zero — if VOUT accuracy is
critical, verify the divider against the device datasheet for the production lot.

L1 (4.7 µH, 1.0 A, CDRH4D22NP-4R7NC or equivalent 4×4 mm shielded) is placed
within 3 mm of U8 SW pin. C19 (10 µF, input) and C20 (22 µF 16 V, output — rated
above 12 V) provide filtering. GPIO5 drives EN HIGH only during the 4–20 mA
measurement window (typically 50–100 ms); at all other times EN=LOW and U8 draws
< 1 µA.

C22 (10 µF, 0805, X5R, ≥16 V rating) is placed in parallel with C20 at the
TPS61023 VOUT pin. X5R capacitors at 12 V DC bias derate significantly — a nominal
22 µF 1206 X5R may present only 6–8 µF effective capacitance at 12 V. C22 ensures
≥10 µF effective output capacitance is maintained across the operating voltage range.
Place C22 adjacent to C20, within 3 mm of U8 VOUT pin.

D11 (SMAJ13A, DO-214AC/SMA, unidirectional TVS, 13 V standoff, ≈21.5 V clamp
@ 10 A) is placed from the VLOOP rail to GND between U8 VOUT and J4/J5 pin 1
(VLOOP terminal). Clamps cable-induced transients (back-EMF on cable disconnect,
lightning induction) before they reach U8. Standoff 13 V is above VLOOP nominal
(12.2 V) so D11 does not conduct in steady state. Place within 5 mm of C20/C22
on the J4/J5 side of SJ2.

### Power — Charger Interlock (Q1 + Q3)

TP4056 and CN3791 both target the same 4.20 V CV threshold. When both chargers are
simultaneously active and approaching termination, their CC→CV transition currents
can interact and prevent either from reaching proper termination.

**Software interlock (Q1 / GPIO4):** Q1 (BSS123, SOT-23, N-ch, Vgs(th) max 1.5 V)
has its drain tied to the TP4056 CE pin (active-HIGH enable) through R29 (4.7 kΩ
pull-up to 3.3 V), and its source to GND. When GPIO4 is driven HIGH, Q1 pulls CE
LOW, disabling USB charging. Firmware reads GPIO6 (CN3791 open-drain /CHRG output,
active-LOW = charging in progress, internal pull-up) and asserts GPIO4 HIGH when
GPIO6 reads LOW.

**Hardware interlock (Q3):** To eliminate the boot-window race where both chargers
are simultaneously active before firmware asserts GPIO4, Q3 (BSS84, SOT-23, P-ch,
Vgs(th) max −1.5 V) directly monitors the /CHRG_SOLAR signal and pulls TP4056 CE
LOW without firmware involvement.

Q3 wiring:
- Source: TP4056 CE node (between R29 and TP4056 CE pin)
- Gate: /CHRG_SOLAR net (CN3791 CHRG pin, active-LOW)
- Drain: GND
- R30 (10 kΩ, 0402): pull-up from gate to +3V3, ensuring Q3 gate is defined if
  /CHRG_SOLAR floats during boot

Operation:
- Solar charging active (/CHRG_SOLAR = 0 V): Vgs = 0 − 3.3 = −3.3 V → Q3 ON →
  CE pulled LOW through Q3 drain → TP4056 disabled (no firmware required)
- Solar idle (/CHRG_SOLAR = 3.3 V via pull-up): Vgs ≈ 0 V → Q3 OFF → CE held HIGH
  by R29 → TP4056 enabled

Q1 and Q3 both pull the CE node LOW in parallel; they do not interfere.
R25 (4.7 kΩ to GND) holds Q1 gate LOW when GPIO4 floats (reset/deep-sleep), which
is the correct fail-safe state (USB charging enabled when radio is silent).

### Power — Battery Divider Enable (Q2)

R7 and R8 (100 kΩ each) form the battery voltage divider. At VBAT = 3.7 V this
draws 18.5 µA continuously — roughly doubling deep-sleep current. Q2 (BSS123,
SOT-23, N-ch, Vgs(th) max 1.5 V) is inserted in series with R8 to GND. When
GPIO15 is LOW (default during sleep), Q2 is off and the divider draws 0 µA.
Firmware pulses GPIO15 HIGH for 1 ms before taking the ADC sample (allowing the
RC filter C8 to settle), then returns GPIO15 LOW. R26 (4.7 kΩ) to GND keeps Q2
gate defined when the GPIO is floating during reset.

GPIO15 is an ESP32-C6 strapping pin (it selects the JTAG signal source at boot).
R26 holds it LOW at reset, which is a defined and harmless strap state — the board
uses UART programming via J10, so the JTAG strap is irrelevant. Driving GPIO15 as
an output after boot does not affect the strap, which is sampled only at reset.

### Transient Protection — 4–20 mA LOOP Terminals (D9, D10, D1, R3, R5)

The LOOP+ and LOOP− terminals are exposed to field wiring and can carry inductive
transients, cable-coupled lightning surges (IEC 61000-4-5), and electrostatic
discharge. A two-stage protection chain is used on each channel to safely clamp
transients while satisfying the ADS1115 absolute-maximum input rating (VDD + 0.3 V =
3.6 V at VDD = 3.3 V):

**Stage 1 — High-energy clamp at the terminal (D9 / D10):**
D9 and D10 (SMAJ3.3CA, DO-214AC/SMA, bidirectional TVS, 3.3 V standoff, 200 W
peak pulse power) are placed at the J4/J5 SIG (LOOP−) terminal, between the
field connector and the shunt resistor. They absorb the bulk of a cable-induced
surge before it reaches R2/R4 and the ADC chain.

Standoff selection rationale: the SMAJ3.3CA has a 3.3 V standoff voltage. The
maximum SIG terminal voltage during normal 4–20 mA operation is 20 mA × 100 Ω =
2.0 V, which is comfortably below 3.3 V, so D9/D10 remain non-conducting in steady
state. The SMAJ3.3CA clamp voltage at 10 A is approximately 5.3 V — substantially
tighter than the previous SMAJ5.0CA (9.2 V at 10 A), which reduces the peak voltage
stress passed through to R3/R5 and D1 during a surge event. The 200 W peak rating
is adequate for IEC 61000-4-5 Class 2 (1 kV) at the series impedances typical of a
current-loop cable. If the installation has very long cable runs (>100 m) or
exposure to direct lightning, an external surge arrester at the cable entry gland is
recommended ahead of D9/D10.

LOOP+ (VLOOP, J4/J5 pin 1) protection: VLOOP transients are clamped by D11
(SMAJ13A, DO-214AC, 13 V standoff unidirectional TVS, 400 W) placed between
the TPS61023 VOUT rail and J4/J5 — see **Power — VLOOP 12 V Boost (U8: TPS61023)**
for details.

**Stage 2 — ADS1115 input clamp (R3/R5 + D1):**
R3 and R5 (100 Ω each, 0402) sit in series between the shunt voltage tap and
the ADS1115 AIN0/AIN1 inputs (and the GPIO0/GPIO2 backup inputs). They limit
fault current into the downstream clamp diodes. D1 (PRTR5V0U2X, SOT-363)
provides dual-channel ESD/EFT clamping at the ADS1115 input nodes, with clamp
voltage tied to VDD (3.3 V) and GND. At maximum residual transient current
through R3/R5, D1 clamp voltage stays below VDD + 0.3 V = 3.6 V, satisfying the
ADS1115 absolute maximum.

With R3 = 100 Ω in series and D1 clamping at ~3.3 V, the worst-case current into
D1 from a 5.3 V post-D9 residual is (5.3 − 3.3) / 100 = 20 mA — well within
PRTR5V0U2X continuous clamp ratings.

**Protection chain summary per channel:**

    Field terminal → D9/D10 (SMAJ3.3CA, 3.3V standoff)
                  → R2/R4 (100Ω shunt) ‖ C_SH1/C_SH2 (10nF HF bypass)
                  → R3/R5 (100Ω series limiter)
                  → D1 (PRTR5V0U2X, clamp to 3.3V/GND)
                  → ADS1115 AIN0/AIN1 (abs max 3.6V)

### Power — Solar Input TVS Protection (D8)

Solar panel cables can carry inductive voltage spikes when partially shaded panels
switch bypass diodes, or when long cable inductance is energised/de-energised by
panel disconnection. D8 (SMAJ7.0A, DO-214AC/SMA, unidirectional TVS, 7.0 V
standoff, 11.2 V clamp @ 10 A) is placed across the CN3791 VIN pin and GND after
D6 (the Schottky input diode). D8 absorbs the high-energy inductive surge and
clamps it to ≈ 11 V for the duration of the transient — far below the
multi-hundred-volt spikes long panel cables can otherwise deliver, though above
the CN3791 7.5 V recommended maximum. D8 therefore protects against fast transient
energy only; sustained-overvoltage protection relies on selecting a panel whose
Voc stays ≤ 7.5 V. Standoff voltage 7.0 V is above the 6.5 V maximum MPPT operating
point, so normal MPPT operation never triggers the TVS. Place D8 within 5 mm of C17.

C21 (100 nF, 0402) is placed directly across D8 (TVS clamp) to absorb the L×dI/dt
inductive transient from panel cable inductance before D8 clamps it. The RC formed
with the cable series resistance (typically 1–5 Ω) limits the peak voltage seen by
D8 during fast-edge events. Place C21 within 3 mm of D8.

### Power — 3.3 V LDO (U1: TPS7A0533)

1 µA quiescent current LDO, SC70-5 package, 1 A output. Input from the battery
(after protection circuit). Enables deep-sleep current dominated by the ESP32-C6
module, not the regulator.

Input: 0.1 µF + 1 µF ceramic.
Output: 0.1 µF + 1 µF ceramic.
ENABLE pin: tie high (10 kΩ to VIN) for always-on. Can be driven from a GPIO if
controlled power-down is needed in future.

### Measurement Accuracy — ADS1115 External ADC (U9)

The ESP32-C6 ADC has ±5 % non-linearity even after efuse two-point calibration.
Across the 4–20 mA measurement span (0.4–2.0 V on the shunt), this translates to
≈ ±80 mV ≈ ±10 % span error — equivalent to ±600 mm depth error on a 10 m
transducer range. U9 (ADS1115IDGST, MSOP-10, 16-bit, I²C addr 0x48 via ADDR→GND)
replaces the onboard ADC for all precision measurements:

- AIN0 (single-ended, referenced to GND): 4–20 mA CH1 shunt voltage (from node between R3 and GPIO0)
- AIN1 (single-ended, referenced to GND): 4–20 mA CH2 shunt voltage (from node between R5 and GPIO2)
- AIN2 (single-ended, referenced to GND): battery voltage divider output (midpoint of R7/R8, same node as GPIO1)
- AIN3: spare

PGA set to ±2.048 V (LSB = 62.5 µV, non-linearity ±0.01 % FS). The 100 Ω shunt
develops 0.4–2.0 V across the 4–20 mA span; the ±2.048 V range fully covers the
normal operating range. Transmitters emitting 21–24 mA fault-signalling currents
will clip at ±2.048 V; firmware detects this as a saturated reading and reports a
sensor fault. SPS = 128 for fast single-shot reads compatible with deep-sleep
wakeup cycles. ALERT/DRDY tied to GPIO12 as an interrupt; firmware waits for DRDY
rather than polling. GPIO backup readings on GPIO0/1/2 remain available for
diagnostics.

#### Analog front-end noise filtering (three-stage chain)

Each 4–20 mA channel has three cascaded filter/protection stages:

1. **C_SH1 / C_SH2 (10 nF across R2 / R4):** HF bypass directly across the shunt
   resistor. Corner frequency fc = 1/(2π × 100 Ω × 10 nF) ≈ 160 kHz. Absorbs
   RF pickup and motor PWM harmonics coupled onto the loop cable before they enter
   the measurement chain. Does not affect the 0–10 Hz measurement band.

2. **R3 / R5 (100 Ω) + C3 / C5 (1 µF):** Anti-aliasing low-pass filter at the ADC
   input tap. fc ≈ 1.6 kHz. Rejects motor-drive switching frequencies, 50/60 Hz
   harmonics beyond the first, and RF pickup from the Zigbee 2.4 GHz radio.

3. **FB1 + C23 (100 nF) + C24 (1 µF) on U9 VDD:** Isolates the ADS1115 supply rail
   from TPS61023 switching noise (~1.5 MHz) and Zigbee radio interference on the
   shared 3.3 V rail. FB1 (BLM18KG601SN1D, 600 Ω @ 100 MHz, 0402) attenuates
   high-frequency supply ripple; C23 and C24 decouple the U9 VDD pin locally.

Target measurement bandwidth: DC to ~5 Hz, set by the SPS = 8 or SPS = 16 ADS1115
operating mode. At SPS = 128, the digital filter corner is ~36 Hz — well below stage 2
anti-aliasing corner of 1.6 kHz, so no aliasing of 50/60 Hz mains.

U9 supply filtering: FB1 (BLM18KG601SN1D, 600 Ω @ 100 MHz, 500 mA, 0402) is
placed in series with the +3V3 feed to U9 VDD, isolating the ADC from switching
noise from U8 (TPS61023, ~1.5 MHz) and the Zigbee radio. C23 (100 nF, 0402) and
C24 (1 µF, 0402) are placed on the U9 side of FB1, within 1 mm of U9 VDD pin,
per ADS1115 datasheet requirements.

### Battery State-of-Charge — MAX17048 Fuel Gauge (U10)

A voltage-only SOC estimate from R7/R8 has ≈ 10 % error due to LiPo open-circuit
voltage curve non-linearity and temperature dependence. U10 (MAX17048G+T10,
SOT-23-6, I²C addr 0x36) uses a model-based algorithm with continuous voltage
measurement to produce a calibrated SOC percentage. VCELL pin connects directly to
VBAT (before the FS8205A protection FETs). ALRT open-drain output to GPIO14 signals
when SOC falls below the firmware-configured threshold (default 15 %). VDD is 3.3 V;
GND to system GND. No RSET resistor required (internal default). U10 draws 23 µA
active, 3 µA sleep; it runs continuously (no GPIO gate needed — 3 µA is within sleep
budget). Place within 5 mm of J1 battery connector for shortest VBAT trace.

R27 (4.7 kΩ, 0402) provides an external pull-up from GPIO14 to 3.3 V for the
MAX17048 ALRT open-drain output. The internal weak pull-up (~50 kΩ) in the boost
converter neighbourhood is insufficient — R27 replaces it with a dedicated low-impedance
pull-up near U10. Place R27 within 3 mm of U10.

---

## Thermal Review: TPS61023 Boost + CN3791 MPPT Simultaneous Operation

Both U8 (TPS61023, 12 V VLOOP boost) and U7 (CN3791, solar MPPT charger) can operate
concurrently during a wake cycle — firmware enables U8 (GPIO5 HIGH) while the solar
charger runs continuously whenever the panel is illuminated.

### TPS61023 (U8, SOT-23-5)

- **Package:** SOT-23-5 — no exposed thermal pad; heat exits through the five leads.
- **Switching frequency:** ~1.5 MHz (fixed, internal oscillator).
- **SW node:** the source/drain of the internal synchronous switch. This node
  transitions between VBAT and GND at 1.5 MHz. The hot-loop is SW → L1 → VOUT.
- **Power dissipation during active measurement window:** at 12 V output and 20 mA
  maximum loop current, output power ≈ 240 mW. At 90 % conversion efficiency,
  Pdiss ≈ 27 mW. At 85 % (worst case with 3.0 V input), Pdiss ≈ 42 mW. SOT-23-5
  θJA ≈ 250 °C/W (TI datasheet, worst case). ΔTj = 42 mW × 250 = 10.5 °C — negligible.
- **Duty cycle:** 50–100 ms per wake cycle (GPIO5 gating), so average Pdiss is
  effectively < 1 mW. U8 thermal management is a non-issue in this duty-cycle regime.
- **SW node copper pour recommendation:** the hot-loop trace (U8 SW pin → L1 → C20/C22)
  must be kept short (< 10 mm) and wide (≥ 0.5 mm). Do NOT pour copper under L1 on
  either layer — the shielded CDRH4D22NP-4R7NC has its own magnetic shield, but stray
  currents in a solid pour would add core losses. Fill the U8/L1/C20 island on F.Cu
  with a GND via stitch perimeter to provide a low-inductance GND return path for the
  SW node's return current, but keep the island itself clear of large fills.

### CN3791 (U7, SOIC-8)

- **Package:** SOIC-8 — no exposed thermal pad; heat exits through leads and pad
  contact on the PCB land pattern.
- **Maximum power dissipation:** at Vin = 6.5 V (maximum MPPT operating point) and
  Vbat = 3.0 V (discharged cell), the linear pass element dissipates approximately:
  Pdiss_max = (Vin − Vbat) × Ichg = (6.5 − 3.0) × 0.5 A = **1.75 W**.
  This exceeds the SOIC-8 θJA-limited capability (~800 mW at 25 °C ambient for a
  standard SOIC-8 with minimal PCB copper). The CN3791 has an internal thermal
  fold-back that limits output current when the die temperature approaches 140 °C —
  the actual delivered charge current will throttle below 500 mA under worst-case
  conditions. This is the intended operating mode; the MPPT algorithm naturally
  reduces input current when the panel sags, moderating dissipation.
- **Copper pour recommendation:** place a 10 × 10 mm solid copper pour on F.Cu
  under and around U7 (SOIC-8 land area), connected to GND via ≥ 4 thermal-relief
  vias (0.6 mm drill, 1.0 mm pad) underneath the IC body. Mirror the pour on B.Cu
  and connect with the same vias to form a thermal via array. This reduces effective
  θJA to ~50–60 °C/W, keeping junction temperature below 125 °C at 1.75 W worst-case
  (ΔTj ≈ 105 °C above 25 °C ambient = 130 °C junction — borderline; thermal fold-back
  remains the safety net). Label this copper island `GND_THERMAL_U7` on the silkscreen.
- **Placement constraint:** U7 must be placed away from U6 (ESP32-C6 module) and
  U9 (ADS1115). Recommended position: bottom-left quadrant of the board, with at
  least 15 mm clearance from U6 and 20 mm from U9. U7 and U8 may be in the same
  quadrant (bottom-right) since both are power ICs, but place them ≥ 8 mm apart
  to avoid mutual heating — combined worst-case Pdiss ≈ 1.8 W (U7 + U8) in the
  same region would raise local PCB temperature by ~15–20 °C.

### Simultaneous Operation Thermal Budget

| Condition | U7 Pdiss | U8 Pdiss | Combined | Est. PCB ΔT |
|-----------|----------|----------|----------|-------------|
| Vin=5.5V, Vbat=3.7V, Ichg=500mA, Iloop=10mA | 0.9 W | 17 mW | ~0.92 W | ~18 °C |
| Vin=6.5V, Vbat=3.0V, Ichg=500mA, Iloop=20mA | 1.75 W | 42 mW | ~1.79 W | ~36 °C |
| Deep-sleep (GPIO5=LOW) | 3 µA × Vin | < 1 µW | negligible | — |

The worst case (1.79 W combined) is thermally benign for U8 but causes U7 to
enter thermal fold-back. The copper pour on U7 and physical separation between
the two ICs are the critical mitigations. No component value changes are required.

---

## Test Points (TP1–TP14)

Solderable test point pads for production testing, ICT fixtures, and field debugging.
All are SMD pads, 1.0 mm diameter copper with solder mask opening. Fit as DNF
(do-not-fit) by default — pads are present on the PCB but no component is required;
a bare pad or a press-fit test nail is used in-fixture.

| Ref | Net | Description |
|-----|-----|-------------|
| TP1 | VBAT | Battery rail (after D5 reverse-polarity MOSFET, before LDO/protection ICs) |
| TP2 | VLOOP | 12 V boost output rail (after U8 TPS61023 VOUT, before J4/J5 VLOOP terminal) |
| TP3 | +3V3 | 3.3 V regulated supply (after TPS7A0533 U1 output) |
| TP4 | GND | System ground reference |
| TP5 | LOOP_TERM_CH1 | CH1 current loop signal: J4 SIG → D9 → R2 shunt; tap is node between R2 and R3 (before ADS1115 AIN0 input limiter) |
| TP6 | LOOP_TERM_CH2 | CH2 current loop signal: J5 SIG → D10 → R4 shunt; tap is node between R4 and R5 (before ADS1115 AIN1 input limiter) |
| TP7 | 1WIRE | DS18B20 1-Wire data bus (J6 DATA line, after R6 pull-up, before D12 ESD clamp) |
| TP8 | I2C_SDA | I²C SDA (GPIO10; shared ADS1115 + MAX17048 bus) |
| TP9 | I2C_SCL | I²C SCL (GPIO11; shared ADS1115 + MAX17048 bus) |
| TP10 | VSOLAR_IN | Solar panel input at J12 pin 1 (before D14 TVS and D6 Schottky; raw panel voltage) |
| TP11 | VBAT_RAW | Battery terminal before D5 (at J1 BAT+, after D13 TVS; raw battery voltage pre-protection-MOSFET) |
| TP12 | ADS_DRDY | ADS1115 ALERT/RDY → GPIO12 (interrupt signal for single-shot conversion complete) |
| TP13 | MAX_ALRT | MAX17048 ALRT → GPIO14 (low-battery interrupt; active-low open-drain with R27 pull-up) |
| TP14 | /CHRG_SOLAR | CN3791 /CHRG open-drain output (active-LOW = solar charging; also drives Q3 hardware interlock) |

### Test point placement notes

- TP1/TP3/TP4: place in a row near the LDO (U1) output, accessible from the top edge.
- TP2: place near C20/C22 on the VLOOP rail.
- TP5/TP6: place within 3 mm of R2/R4 shunt pads, on the ADC-tap (R3/R5) side.
- TP7: place near J6 DATA terminal, on the GPIO7 side of D12.
- TP8/TP9: place near J8 I²C header.
- TP10/TP11: place near J12 and J1 respectively.
- TP12/TP13/TP14: place near the edge of U6 (ESP32-C6) where GPIO12/14 route.
- All TPs must have a 0.2 mm annular ring minimum and be clear of any keep-out zone.
- SMD pad footprint: `TestPoint:TestPoint_Pad_1.0x1.0mm` (KiCad standard library).
- **Case-engineer note:** TP pad height above PCB surface ≈ 0.1 mm (pad only, no
  component body). No keep-out height constraint imposed. A test-nail ICT fixture
  accessing all 14 TPs from the top side requires a 1.27 mm minimum nail-to-nail pitch
  (all TPs are 1.0 mm pads; 0.27 mm clearance is sufficient for standard ICT probes).

---

## Decoupling Review

### ESP32-C6 Module (U6)

- **Present:** C14a–C14d (4× 100 nF, 0402) + C15 (10 µF, 0805) on VCC3V3 pads.
- **Datasheet requirement:** Espressif ESP32-C6-MINI-1U hardware design guide
  recommends 100 nF per VDD pin (4 pins require 4× 100 nF) plus one 10 µF bulk cap.
- **Status:** Adequate. No change needed.

### ADS1115 (U9)

- **Present:** FB1 (600 Ω ferrite bead) in series with +3V3 to VDD; C23 (100 nF, 0402)
  + C24 (1 µF, 0402) on U9 side of FB1.
- **Datasheet requirement:** ADS1115 datasheet recommends 100 nF + 1 µF decoupling
  on VDD, placed as close as possible to the VDD pin. The ferrite bead is additional
  isolation added by this design.
- **Status:** Adequate. No change needed.

### MAX17048 (U10)

- **Present:** R27 (4.7 kΩ pull-up on ALRT pin). No VDD bypass capacitor.
- **Datasheet requirement:** MAX17048 datasheet (Maxim DS3739 rev 2) recommends a
  100 nF ceramic decoupling capacitor on VDD pin, placed as close as possible to U10.
- **Status:** MISSING. Added **C25** (100 nF, 0402, X7R, ≥ 6.3 V) from U10 VDD to GND.
  Place within 1 mm of U10 VDD pin (pin 1). LCSC C14663 or equivalent.

### TPS61023 (U8)

- **Present:** C19 (10 µF, 0805) on VIN; C20 (22 µF 16 V, 1206) + C22 (10 µF 16 V,
  0805) in parallel on VOUT.
- **Datasheet requirement:** TPS61023 datasheet recommends ≥ 4.7 µF on VIN and ≥ 10 µF
  effective on VOUT (the X5R derating note explains why C20 + C22 are both populated).
  A bootstrap cap is not required — TPS61023 is a SOT-23-5 that does not expose a
  BST pin; bootstrap is internal.
- **Status:** Adequate. No change needed.

### CN3791 (U7)

- **Present:** C17 (10 µF, 0805) on VIN; C18 (10 µF, 0805) on BAT/VBAT output.
  R19 sets PROG current; C21 (100 nF) across D8 TVS.
- **Datasheet requirement:** CN3791 datasheet recommends 10 µF on VIN and 10 µF on
  BAT. The PROG pin requires no capacitor. No additional decoupling pin exists.
- **Status:** Adequate. No change needed.

### S-8261AAYFT (U3)

- **Present:** No dedicated VCC bypass capacitor in the BOM.
- **Datasheet requirement:** Seiko S-8261A datasheet recommends a 0.1 µF (100 nF)
  ceramic capacitor on VCC (pin 5) to GND (pin 1), placed as close as possible to U3.
  This stabilises the internal reference and prevents oscillation in the protection
  comparator during fast transients on the VBAT rail.
- **Status:** MISSING. Added **C26** (100 nF, 0402, X7R, ≥ 6.3 V) from U3 VCC (pin 5)
  to GND. Place within 1 mm of U3 VCC pin. LCSC C14663 or equivalent (same part as C25).

### TP4056 (U2)

- **Present:** C1 (10 µF, 0805) on VCC input; C2 (10 µF, 0805) on BAT output.
- **Datasheet requirement:** TP4056 datasheet recommends 10 µF on VCC and 10 µF on
  BAT. PROG pin needs no capacitor.
- **Status:** Adequate. No change needed.

### TPS7A0533 (U1 / 3.3 V LDO)

- **Present:** C9 (100 nF, 0402) + C10 (1 µF, 0402) on VIN; C11 (100 nF, 0402)
  + C12 (1 µF, 0402) on VOUT.
- **Datasheet requirement:** TPS7A0533 datasheet (TI SBVS301) recommends 100 nF
  input bypass + 1 µF minimum output for stability. Additional bulk on input reduces
  dropout transients. ENABLE pin pull-up via R11 + C13 (100 nF) on EN for clean
  power-on reset.
- **Status:** Adequate. No change needed.

---

### External Antenna (J3 → SMA bulkhead)

The ESP32-C6-MINI-1U module has a U.FL pad for an external antenna. J3 (U.FL
receptacle, Hirose U.FL-R-SMT-1) connects to an SMA female bulkhead mounted in
the enclosure back wall via a U.FL→SMA RG178 pigtail (~100 mm, Taoglas
CAB.100.07.0100B or equivalent).

A 2.4 GHz omnidirectional SMA rubber-duck antenna (e.g. Taoglas FXP73, 2 dBi)
threads onto the bulkhead from outside the enclosure. This is the default
configuration — the antenna protrudes from the back wall, pointing up, giving
clear line-of-sight to the Zigbee coordinator.

**RF layout constraints:**
- Route a 50 Ω coplanar waveguide from the module U.FL pad to J3 — keep it under
  20 mm, no layer transitions or vias.
- 50 Ω CPW trace width on standard 1.6 mm FR4 with 35 µm Cu: typically 2.9–3.2 mm
  with 0.15 mm gap to adjacent ground pour. Calculate precisely for your stackup.
- Maintain a 15 mm no-copper keep-out around the module's on-chip antenna area on
  both layers. J3 and the trace exit from the opposite (U.FL) side of the module.
- The enclosure back wall's RF-thinned zone in `welld_case.scad` reduces plastic
  thickness to 0.5 mm above the J3/U.FL area for minimal insertion loss.

**Alternative — chip antenna:** Leave J3 unpopulated and set `ext_antenna = false`
in `welld_case.scad`. The module's internal chip antenna is adequate for indoor
ranges up to ~30 m. For a well in a metal housing or a long yard run, the external
antenna is strongly recommended.

### ESP32-C6-MINI-1U Module (U6)

Mount on 1.5 mm edge clearance for hand soldering. U.FL connector (J3) is on the
top PCB edge nearest the back wall; route a 50 Ω CPW trace from the module U.FL
pad to J3 — keep it under 20 mm with no layer transitions or vias.

Strapping resistors:
- GPIO8: 10 kΩ to 3.3 V (normal boot)
- GPIO9: 10 kΩ to 3.3 V; SW2 (BOOT) pulls to GND for download mode
- EN: 10 kΩ to 3.3 V + 100 nF to GND for clean power-on reset; SW1 (RESET) pulls EN to GND

All module VCC3V3 and GND pads must be decoupled. Minimum: four 100 nF 0402 ceramics
placed within 2 mm of the module pads, plus one 10 µF 0805 bulk cap.

### 4–20 mA Sensor Interface — Channel 1 (J4)

3-position pluggable screw terminal, 3.5 mm pitch (Phoenix Contact MC 1.5/3-ST-3.5 +
MC 1.5/3-G-3.5 PCB header):

| Pin | Label | Description |
|-----|-------|-------------|
| 1 | VLOOP | Loop supply input. Connected to VLOOP 12 V boost rail (U8). |
| 2 | SIG | Transducer return (−) wire. Connects to shunt side. |
| 3 | GND | System ground. |

On-PCB:
- D9 (SMAJ3.3CA, DO-214AC, bidirectional TVS, 3.3 V standoff, 200 W peak) is placed
  from the SIG terminal (J4 pin 2) to GND **before** R2. Provides IEC 61000-4-5
  surge protection at the field terminal. Changed from SMAJ5.0CA (5 V standoff) to
  SMAJ3.3CA (3.3 V standoff): the 3.3 V standoff is above the 2.0 V maximum shunt
  voltage during normal 4–20 mA operation so D9 does not conduct in steady state, yet
  clamps transients to ~5.3 V at 10 A — well below the 9.2 V clamp of SMAJ5.0CA.
  This lower clamp voltage substantially reduces the residual stress seen by R3 and
  D1 during a surge event. Place within 3 mm of J4 SIG terminal.
- R2 (100 Ω ±0.1%, 0805) is the current shunt, from SIG to GND.
- **C_SH1 (10 nF, X7R, 25 V, 0402)** is placed directly across R2. This small cap
  bypasses HF pickup (RF, motor PWM) on the loop cable before it reaches the ADC
  measurement chain. The –3 dB corner with R2 is 1/(2π × 100 × 10 nF) ≈ 160 kHz,
  well above the measurement bandwidth (<10 Hz) and well below the 1.6 kHz R3+C3
  anti-aliasing corner. The 10 nF value is small enough to leave ADS1115 SPS
  settling unaffected. Place C_SH1 within 1 mm of R2 pads.
- R3 (100 Ω, 0402) is a series input limiter between SIG and the ADC tap. Together
  with C3, R3 limits fault current into D1 and the ADS1115 AIN0 pin to safe levels.
- D1 CH1 (PRTR5V0U2X, SOT-363, one device covers both channels 1 and 2) clamps the
  ADC tap to the 3.3 V rail and GND against ESD transients (IEC 61000-4-2 / 4-4).
  This is the last-line clamp protecting the ADS1115 AIN0 pin; with R3 (100 Ω) in
  series, fault current into D1 is limited to (Vclamp – Vsig) / R3 < 33 mA.
- C3 (1 µF, X5R, 0402) + C4 (10 µF, 0805) on the ADC tap provide a 1.6 kHz RC
  low-pass filter in combination with R3, rejecting motor-drive harmonics and
  2.4 GHz pickup from the Zigbee radio.
- ADC tap routed to U9 ADS1115 AIN0 (primary) and GPIO0 (backup).

SJ1 (solder jumper, 2-pad, normally open): 2-pad solder jumper, normally open. When closed,
permanently holds TPS61023 EN HIGH (VLOOP always-on). **DNF in production** — lab/debug use
only. Closing in the field will drain the battery continuously as the 12V boost runs during
deep-sleep.

SJ2 (solder jumper, 2-pad, normally closed): bridges J4_VLOOP to J5_VLOOP so both
sensors share a single external supply. Cut to give channels independent supplies.

### 4–20 mA Sensor Interface — Channel 2 (J5)

Identical circuit to Channel 1. D10 (SMAJ3.3CA, DO-214AC, bidirectional TVS,
3.3 V standoff, 200 W) placed at J5 SIG terminal before R4 — same function and
same SMAJ5.0CA→SMAJ3.3CA change as D9 on Channel 1. Shunt R4 (100 Ω ±0.1%),
**C_SH2 (10 nF, X7R, 25 V, 0402) directly across R4** (same HF bypass function as
C_SH1 on ch1), limiter R5 (100 Ω), ADC tap protected by D1 CH2. C5 (1 µF,
X5R, 0402) forms the RC filter with R5 (fc = 1.6 kHz). ADC tap routed to U9
ADS1115 AIN1 (primary) and GPIO2 (backup). Place C_SH2 within 1 mm of R4 pads.

Intended for a second submersible transducer (e.g. redundancy or separate measurement
point). Firmware support not yet implemented; GPIO2/ADC1_CH2 and ADS1115 AIN1 are
exposed and CONFIG_WELLD_SENSOR_ADC_CHANNEL can be overridden to 2 to switch between
channels.

### DS18B20 1-Wire Interface (J6)

3-position pluggable screw terminal, 3.5 mm pitch:

| Pin | Label | Description |
|-----|-------|-------------|
| 1 | VCC | 3.3 V. Must be connected — parasite-power not supported. |
| 2 | DATA | 1-Wire bus. R6 (4.7 kΩ) pull-up to 3.3 V on PCB. |
| 3 | GND | System ground. |

C5 (100 nF) on VCC at the connector provides local decoupling. Multiple DS18B20s can
be bussed on DATA; the firmware locks onto one ROM address after first discovery.

R28 (100 Ω, 0402) is placed in the VCC line between the 3.3 V rail and J6 pin 1.
It limits fault current to ~33 mA in the event a misconnected probe cable short-circuits
the VCC pin to GND, protecting the 3.3 V rail.

**1-Wire DATA ESD protection (D12):**
D12 (PRTR5V0U2X, SOT-363) provides ESD rail-clamp protection on the 1-Wire DATA line
(J6 pin 2 → GPIO7). Long cable runs to field sensors are exposed to ESD (IEC 61000-4-2)
and electrical fast transients (IEC 61000-4-4). D12 IO1 connects to the 1WIRE net; IO2
is left no-connect. VCC pins connect to +3V3; GND pins to system GND.

Protection characteristics:
- Clamped voltage during ESD: VCC + 0.5 V = 3.8 V (sub-nanosecond transient).
  This is 0.2 V above the ESP32-C6 GPIO7 absolute maximum of 3.6 V (= VDD + 0.3 V).
  This brief overshoot is consistent with standard IEC 61000-4-2 level-4 GPIO
  protection practice using rail-clamp devices on 3.3 V systems. If strict abs-max
  compliance is required, add a 33 Ω series resistor (R32, DNF by default) between
  J6 pin 2 and the D12 IO1 / 1WIRE junction.
- Capacitance: 0.5 pF per IO pin, well below the DS18B20 spec's 800 pF maximum line
  capacitance and the 100 pF target for added protection components. 1-Wire timing
  is unaffected.
- Same part as D1 (PRTR5V0U2X) — no new component introduced to the BOM.

Place D12 within 3 mm of J6 DATA terminal (pin 2), on the terminal side of R6.

### Spare Sensor (J7)

3-position pluggable screw terminal, 3.5 mm pitch:

| Pin | Label | Description |
|-----|-------|-------------|
| 1 | 3V3 | 3.3 V supply. |
| 2 | IO | GPIO3 / ADC1_CH3. Also connected to J9 header pin. |
| 3 | GND | System ground. |

Populated as a placeholder for a third sensor (flow pulse, analog 0–3 V output,
single-wire protocol, etc.).

### Solar Panel Input (J12)

2-position pluggable screw terminal, 3.5 mm pitch (Phoenix Contact MC 1.5/2-ST-3.5
+ MC 1.5/2-G-3.5 PCB header) on the bottom edge, right of the sensor connectors:

| Pin | Label | Description |
|-----|-------|-------------|
| 1 | SOLAR+ | Solar panel positive. 5–6.5 V nominal (Voc ≤ 7.5 V). |
| 2 | GND | Common ground. |

D6 (MBRS140, SOD-123) sits in series between J12 pin 1 and CN3791 VIN. It is
oriented with the cathode toward U7 — current flows from the panel into the charger;
the diode blocks reverse current when the panel is dark.

### Battery Voltage Divider

Onboard resistor divider from VBAT (after protection circuit, before LDO):
- R7: 100 kΩ (high side)
- R8: 100 kΩ (low side), with Q2 (BSS123) in series to GND — gate driven by GPIO15
- Ratio: 2:1 → CONFIG_WELLD_BATT_DIVIDER_RATIO = 200
- C6: 100 nF across R8/Q2 drain for noise immunity
- ADC tap → U9 ADS1115 AIN2 (primary) and GPIO1 (backup, when Q2 enabled)

Q2 (BATT_DIV_EN, GPIO15) gates the lower leg of the divider. During deep sleep
GPIO15 is LOW and Q2 is off, eliminating the 18.5 µA standby draw. See
**Power — Battery Divider Enable (Q2)** for switching timing.

### I²C Expansion Header (J8)

4-pin 2.54 mm single-row header:

| Pin | Signal |
|-----|--------|
| 1 | 3.3 V |
| 2 | GND |
| 3 | SDA (GPIO10) |
| 4 | SCL (GPIO11) |

R9 and R10 (4.7 kΩ each) pull SDA and SCL to 3.3 V on the PCB. The I²C bus is
shared with U9 (ADS1115, addr 0x48) and U10 (MAX17048, addr 0x36). Suited for
additional I²C sensors: pressure (e.g. MS5837), conductivity, turbidity, RTC module.

### GPIO Expansion Header (J9)

8-pin 2.54 mm single-row header:

| Pin | Signal |
|-----|--------|
| 1 | 3.3 V |
| 2 | GND |
| 3 | GPIO3 / ADC1_CH3 |
| 4 | (spare) |
| 5 | (spare) |
| 6 | (spare) |
| 7 | GPIO20 |
| 8 | GPIO21 |

GPIO4, GPIO5, GPIO6, GPIO12, GPIO14, and GPIO15 are now dedicated to on-board
functions (charger interlock, boost enable, CN3791 disable, ADS1115 DRDY,
MAX17048 ALRT, battery divider enable respectively). Spare digital pins GPIO20 and
GPIO21 remain on J9 for user expansion.

### Programming Header (J10)

6-pin 1.27 mm SMD header (no USB bridge chip on board):

| Pin | Signal |
|-----|--------|
| 1 | 3.3 V |
| 2 | GND |
| 3 | TX (GPIO16) |
| 4 | RX (GPIO17) |
| 5 | EN |
| 6 | BOOT (GPIO9) |

Use any USB-UART adapter supporting 3.3 V logic. Hold BOOT low (SW2) and pulse EN
(SW1) to enter download mode, or use the adapter's DTR/RTS auto-reset circuit.

Pads for an optional CH343G (or CH340C) USB-UART bridge are included on the PCB
(DNF in production). Two solder jumpers (SJ4, SJ5) bridge CH343 TX/RX to the
ESP32-C6 UART lines; cutting them isolates the bridge chip completely.

### Status LED (D4)

Green LED on GPIO13, series 1 kΩ (R14) to GND. SJ3 (solder jumper, normally closed)
disconnects the LED. Cut SJ3 on production/field units to eliminate the parasitic
draw during active phase.

---

## PCB Physical Notes

- **Layers:** 2-layer, 1 oz Cu each side
- **Dimensions:** 80 × 55 mm
- **Mounting holes:** M3, on 70 × 45 mm grid (4 corners, 1.5 mm from edge)
- **Min trace / space:** 0.15 mm / 0.15 mm (achievable on standard FR4 process)
- **Min via drill:** 0.3 mm (0.6 mm pad)
- **Connector placement:** screw terminals on the bottom long edge; USB-C and
  programming header on the left short edge; battery connector on the right short
  edge; U.FL and status LED on the top long edge
- **Antenna keep-out:** 15 mm clear area around the module antenna region on both
  sides; no copper pour in this zone
- **ADC traces:** route GPIO0–GPIO2 shunt taps and ADS1115 AIN lines away from
  switching nodes (VLOOP boost L1/U8, LDO, USB); ground-plane stitching vias
  around the shunt resistors; keep ADS1115 (U9) within 20 mm of the shunt taps
- **VLOOP boost placement:** U8 (TPS61023) and L1 should be placed together on the
  bottom-right quadrant, away from the RF keep-out zone and ADC signal traces;
  C19/C20 within 3 mm of U8 pins; ensure 12 V trace to J4/J5 VLOOP pins is rated
  for 500 mA (≥ 0.5 mm trace width)
- **I²C routing:** ADS1115 (U9) and MAX17048 (U10) share GPIO10/GPIO11; route the
  I²C bus with 4.7 kΩ pull-ups (R9, R10) close to U6; keep bus traces under 50 mm
  to avoid capacitive loading at 400 kHz Fast-mode
- **MAX17048 placement:** U10 within 5 mm of J1 (JST XH battery connector) for
  shortest VBAT trace; VCELL line should be as short as possible and away from
  switching nodes
- **Q1/Q2 placement:** Q1 (charger interlock) near TP4056 CE pin; Q2 (battery
  divider enable) near R8 lower leg; R26 gate bleed for Q2 within 2 mm of Q2 gate
- **D8 TVS placement:** within 5 mm of C17 (CN3791 VIN filter cap) for effective
  transient clamping
- **D14 solar terminal TVS placement:** within 3 mm of J12 SOLAR+ terminal (pin 1);
  on the terminal side of D6 — D14 must be between J12 and D6; same footprint as
  D8 (DO-214AC/SMA); cathode toward SOLAR+ rail, anode to GND
- **D9/D10 loop TVS placement:** within 3 mm of J4/J5 SIG terminal (pin 2); on the
  terminal side of R2/R4 — D9/D10 must be between the field connector and the shunt;
  D9 and D10 are now SMAJ3.3CA (3.3 V standoff) — verify silkscreen if a 5.0 V
  variant was previously stuffed on any prototype
- **C_SH1/C_SH2 shunt bypass cap placement:** 10 nF 0402 placed directly across R2
  and R4 respectively; within 1 mm of the shunt resistor pads; on the shunt (not
  ADC-tap) side of R3/R5
- **D11 VLOOP TVS placement:** within 5 mm of C20/C22 on the J4/J5 side of SJ2;
  clamps VLOOP cable transients before they reach U8
- **D12 1-Wire ESD clamp placement:** within 3 mm of J6 DATA terminal (pin 2);
  SOT-363 footprint; VCC pins to +3V3, GND pins to GND, IO1 to 1WIRE, IO2 no-connect
- **D13 battery TVS placement:** within 5 mm of J1 JST XH battery connector; DO-214AC
  SMA footprint; across VBAT_RAW (J1 BAT+ pin) and GND; bidirectional — either
  orientation correct; place near U3/U4 LiPo protection circuit
- **D5/R31 reverse-polarity MOSFET placement:** D5 (AO3407 SOT-23) in series on
  BAT+ rail, source toward J1 BAT+ and D13, drain toward VBAT system rail; R31
  (10 kΩ, 0402) from D5 gate pin to GND; place R31 within 2 mm of D5 gate pin; D5
  sits between J1 and U3/U4 LiPo protection IC cluster; protection chain order on
  PCB copper: J1 BAT+ → D13 (TVS, at terminal) → D5 S→D → VBAT rail → U3/U4/U10
- **FB1/C23/C24 ADS1115 supply filter:** FB1 in series with +3V3 to U9 VDD; C23 and
  C24 on the U9 side of FB1, within 1 mm of U9 VDD pin
- **Q3/R30 hardware interlock:** Q3 (BSS84 P-ch SOT-23) near TP4056 CE node, source
  to CE, gate to /CHRG_SOLAR, drain to GND; R30 (10 kΩ) within 2 mm of Q3 gate
- **50 Ω trace:** module U.FL pad to J3; calculate width for your specific
  stackup (typically 2.9–3.2 mm on standard 1.6 mm FR4 with 35 µm Cu)
- **Test points:** TP1–TP14, 1.0 mm SMD pads (TestPoint:TestPoint_Pad_1.0x1.0mm),
  DNF by default; see **Test Points** section above for full net-to-TP mapping and
  placement notes. Verified footprints added to schematic and BOM as DNF entries.
- **MAX17048 VDD bypass (C25):** 100 nF 0402 from U10 VDD (pin 1) to GND; within
  1 mm of U10 VDD pin; required by MAX17048 datasheet; previously missing from BOM.
- **S-8261A VCC bypass (C26):** 100 nF 0402 from U3 VCC (pin 5) to GND; within
  1 mm of U3; required by S-8261AAYFT datasheet; previously missing from BOM.
- **CN3791 thermal copper pour (U7):** 10 × 10 mm solid GND pour on F.Cu under
  U7 SOIC-8, connected to B.Cu via ≥ 4 thermal vias (0.6 mm drill, 1.0 mm pad);
  see **Thermal Review** section above for full rationale.
- **TPS61023 SW-node copper (U8):** keep hot-loop trace (SW → L1 → C20/C22) under
  10 mm, ≥ 0.5 mm wide; no solid copper pour under L1; GND via-stitch perimeter
  around the U8/L1 island; see **Thermal Review** section for details.
- **KiCad files:** `welld.kicad_sch` / `welld.kicad_pcb` (generated by
  `generate_kicad.py`) contain all component placements and net labels. Board
  outline and footprints are placed; no traces routed — use the KiCad autorouter
  or route manually after running DRC on the net list.
- **Case:** `hardware/case/welld_case.scad` — parametric 3D-printed enclosure with
  M16 cable gland cutouts and SMA bulkhead hole on back wall for external antenna.
- **Power & measurement BOM summary:** U8 TPS61023DCKR (SOT-23-5), L1 4.7 µH
  shielded inductor (CDRH4D22NP-4R7NC), C19 10 µF 0805, C20 22 µF 16 V 1206,
  R23 1.1 MΩ 0402, R24 47 kΩ 0402, Q1 BSS123 SOT-23 (software USB interlock),
  Q2 BSS123 SOT-23 (battery divider gate), Q3 BSS84 SOT-23 (hardware USB interlock),
  R25 4.7 kΩ 0402, R26 4.7 kΩ 0402, R27 4.7 kΩ 0402 (MAX17048 ALRT pull-up),
  R28 100 Ω 0402 (DS18B20 VCC series), R29 4.7 kΩ 0402 (TP4056 CE pull-up),
  R30 10 kΩ 0402 (Q3 gate pull-up), C21 100 nF 0402 (TVS bypass),
  C22 10 µF 0805 (VBOOST parallel), C23 100 nF 0402 (ADS1115 VDD bypass),
  C24 1 µF 0402 (ADS1115 VDD bulk), FB1 BLM18KG601SN1D 0402 (ADS1115 supply filter),
  C_SH1 10 nF 0402 (shunt ch1 HF bypass across R2),
  C_SH2 10 nF 0402 (shunt ch2 HF bypass across R4),
  D9 SMAJ3.3CA DO-214AC (loop ch1 terminal surge TVS — changed from SMAJ5.0CA),
  D10 SMAJ3.3CA DO-214AC (loop ch2 terminal surge TVS — changed from SMAJ5.0CA),
  D11 SMAJ13A DO-214AC (VLOOP terminal surge TVS),
  D12 PRTR5V0U2X SOT-363 (1-Wire DATA ESD rail clamp at J6; same part as D1),
  D5 AO3407 SOT-23 (reverse-polarity P-ch MOSFET, BAT+ series; source→J1 drain→VBAT; LCSC C31417),
  R31 10kΩ 0402 (D5 gate pull-down to GND; holds Vgs=−Vbat for full enhancement; mandatory),
  D13 SMAJ5.0CA DO-214AC (battery terminal bidirectional TVS at J1),
  D14 SMAJ7.0A DO-214AC (solar terminal TVS at J12 before D6; same part as D8),
  U9 ADS1115IDGST MSOP-10, U10 MAX17048G+T10 SOT-23-6, D8 SMAJ7.0A DO-214AC,
  U3 S-8261AAYFT (SOT-23-6), J1 JST XH 2.5 mm (B2B-XH-AM),
  C25 100 nF 0402 (MAX17048 VDD bypass — new; previously missing),
  C26 100 nF 0402 (S-8261AAYFT VCC bypass — new; previously missing),
  TP1–TP14 SMD test point pads 1.0 mm (TestPoint:TestPoint_Pad_1.0x1.0mm; DNF).
