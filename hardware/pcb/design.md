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
| 6 | — | CN3791 disable | 10 kΩ pull-up to CN3791 PROG; pull GPIO6 LOW to halt solar charging |
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
| 18 | — | USB D− | J2 USB-C (power only) |
| 19 | — | USB D+ | J2 USB-C (power only) |
| 20 | — | Spare digital | J9 expansion header |
| 21 | — | Spare digital | J9 expansion header |

---

> **Firmware changes required for rev-2 hardware:**
> 1. GPIO5 HIGH before any 4–20 mA reading; LOW after. Allow 5 ms for TPS61023 soft-start.
> 2. GPIO15 HIGH for 1 ms before battery ADC read via U9 AIN2; LOW after.
> 3. GPIO4 HIGH when /CHRG_SOLAR (GPIO6 read with pull-up) indicates solar charging active.
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

### Charge current (R19)

CN3791 PROG pin: R19 = 2 kΩ → 500 mA charge current. This draws ≈ 600 mA from
a 6 V panel at the MPPT point (accounting for ~85 % conversion efficiency) — well
within a 5 W panel's Isc. For smaller panels or higher battery capacity, raise R19:
3.3 kΩ → 300 mA.

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

### Power — Input & Reverse Polarity (D5)

A P-channel MOSFET (e.g., AO3407, SOT-23) with gate pulled to VBAT and source at
VBAT provides reverse-polarity protection with <150 mV drop at full load.
Alternative: series Schottky (MBR0530, SOD-323) for simplicity at the cost of ~0.3 V
drop and 300 mW dissipation at 1 A — acceptable for a battery-powered device.

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

### Power — LiPo Protection (U3: S-8261AAYFT + U4: FS8205A)

U3 has been changed from DW01A (over-discharge cutoff 2.4 V) to **S-8261AAYFT**
(Seiko Instruments, SOT-23-6, pin-compatible). The DW01A 2.4 V cutoff is below the
LiPo safe floor of 3.0 V; repeated discharge to 2.4 V degrades cell capacity by
≈ 30 % per 100 cycles. The S-8261A trips at 2.9 V over-discharge (with 0.1 V
hysteresis, i.e. recovery at 3.0 V) and 4.28 V over-charge, which is identical to
the DW01A over-charge threshold. The SOT-23-6 pinout is identical (OD, OC, CS,
NC/TM, GND, VCC) so no PCB change is required — only a BOM substitution.

U4 (FS8205A, SOT-23-6) provides the dual back-to-back MOSFET switch driven by U3
for over-discharge, over-charge, and over-current protection. **J1 changed from JST
PH (2.0 mm) to JST XH (2.5 mm, B2B-XH-AM). JST XH has higher retention force and
is more robust for field battery connector use.** Place U3 and U4 as close to J1 as
possible.

### Power — VLOOP 12 V Boost (U8: TPS61023)

The VLOOP rail supplies 2-wire 4–20 mA pressure transmitters, which require ≥ 10 V
to operate their internal electronics. U8 (TPS61023DCKR, SOT-23-5, synchronous
boost) converts VBAT (3.0–4.2 V) to 12 V when the EN pin is driven HIGH by GPIO5.
The output voltage is set by a resistor divider from VOUT to the FB pin (0.5 V
reference):

    VOUT = 0.5 × (1 + R23/R24) = 0.5 × (1 + 1100/47) ≈ 12.2 V

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

### Power — Charger Interlock (Q1)

TP4056 and CN3791 both target the same 4.20 V CV threshold. When both chargers are
simultaneously active and approaching termination, their CC→CV transition currents
can interact and prevent either from reaching proper termination. Q1 (BSS123,
SOT-23, N-ch, Vgs(th) max 1.5 V) has its drain tied to the TP4056 CE pin
(active-HIGH enable) through a 4.7 kΩ pull-up to 3.3 V, and its source to GND.
When GPIO4 is driven HIGH, Q1 pulls CE LOW, disabling USB charging. Firmware reads
the /CHRG_SOLAR signal (from CN3791 open-drain CHRG pin, connected to GPIO6 internal
pull-up) to determine whether solar charging is active, and then asserts GPIO4 HIGH
to park the TP4056 until solar charging completes or USB is the only source present.

### Power — Battery Divider Enable (Q2)

R7 and R8 (100 kΩ each) form the battery voltage divider. At VBAT = 3.7 V this
draws 18.5 µA continuously — roughly doubling deep-sleep current. Q2 (BSS123,
SOT-23, N-ch, Vgs(th) max 1.5 V) is inserted in series with R8 to GND. When
GPIO15 is LOW (default during sleep), Q2 is off and the divider draws 0 µA.
Firmware pulses GPIO15 HIGH for 1 ms before taking the ADC sample (allowing the
RC filter C8 to settle), then returns GPIO15 LOW. R26 (4.7 kΩ) to GND keeps Q2
gate defined when the GPIO is floating during reset.

### Power — Solar Input TVS Protection (D8)

Solar panel cables can carry inductive voltage spikes when partially shaded panels
switch bypass diodes, or when long cable inductance is energised/de-energised by
panel disconnection. D8 (SMAJ7.0A, DO-214AC/SMA, unidirectional TVS, 7.0 V
standoff, 11.2 V clamp @ 10 A) is placed across the CN3791 VIN pin and GND after
D6 (the Schottky input diode). This clamps transients below the CN3791 absolute
maximum of 7.5 V. Standoff voltage 7.0 V is above the 6.5 V maximum MPPT operating
point, preventing normal MPPT operation from triggering the TVS. Place D8 within
5 mm of C17.

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
transducer range. U9 (ADS1115IDGST, SOIC-8, 16-bit, I²C addr 0x48 via ADDR→GND)
replaces the onboard ADC for all precision measurements:

- AIN0 (differential with AIN1 GND): 4–20 mA CH1 shunt voltage (from node between R3 and GPIO0)
- AIN1 (single-ended): 4–20 mA CH2 shunt voltage (from node between R5 and GPIO2)
- AIN2 (single-ended): battery voltage divider output (midpoint of R7/R8, same node as GPIO1)
- AIN3: spare

PGA set to ±2.048 V (LSB = 62.5 µV, non-linearity ±0.01 % FS). SPS = 128 for fast
single-shot reads compatible with deep-sleep wakeup cycles. ALERT/DRDY tied to
GPIO12 as an interrupt; firmware waits for DRDY rather than polling. GPIO backup
readings on GPIO0/1/2 remain available for diagnostics.

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
- R2 (100 Ω ±0.1%, 0805) is the current shunt, from SIG to GND.
- R3 (100 Ω, 0402) is a series input limiter between SIG and the ADC tap.
- D1 CH1 (PRTR5V0U2X, SOT-363, one device covers both channels 1 and 2) clamps the
  ADC tap to the 3.3 V rail and GND against transients.
- C3 (100 nF) + C4 (10 µF, 0805) on the ADC tap provide a 10 µs RC low-pass filter
  in combination with R3.
- ADC tap routed to U9 ADS1115 AIN0 (primary) and GPIO0 (backup).

SJ1 (solder jumper, 2-pad, normally open): 2-pad solder jumper, normally open. When closed,
permanently holds TPS61023 EN HIGH (VLOOP always-on). **DNF in production** — lab/debug use
only. Closing in the field will drain the battery continuously as the 12V boost runs during
deep-sleep.

SJ2 (solder jumper, 2-pad, normally closed): bridges J4_VLOOP to J5_VLOOP so both
sensors share a single external supply. Cut to give channels independent supplies.

### 4–20 mA Sensor Interface — Channel 2 (J5)

Identical circuit to Channel 1. Shunt R4 (100 Ω ±0.1%), limiter R5 (100 Ω), ADC
tap protected by D1 CH2. ADC tap routed to U9 ADS1115 AIN1 (primary) and GPIO2
(backup).

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
- **50 Ω trace:** module U.FL pad to J3; calculate width for your specific
  stackup (typically 2.9–3.2 mm on standard 1.6 mm FR4 with 35 µm Cu)
- **Test points:** expose VBAT, 3V3, GND, VLOOP, GPIO8, each ADC tap (GPIO0–GPIO2),
  I²C SDA/SCL, GPIO12 (DRDY), and GPIO14 (MAX17048 ALRT) as 1 mm SMD test pads
- **KiCad files:** `welld.kicad_sch` / `welld.kicad_pcb` (generated by
  `generate_kicad.py`) contain all component placements and net labels. Board
  outline and footprints are placed; no traces routed — use the KiCad autorouter
  or route manually after running DRC on the net list.
- **Case:** `hardware/case/welld_case.scad` — parametric 3D-printed enclosure with
  M16 cable gland cutouts and SMA bulkhead hole on back wall for external antenna.
- **Rev-2 BOM additions:** U8 TPS61023DCKR (SOT-23-5), L1 4.7 µH shielded inductor
  (CDRH4D22NP-4R7NC), C19 10 µF 0402, C20 22 µF 16 V 0805, R23 1100 Ω 0402,
  R24 47 Ω 0402, Q1 BSS123 SOT-23, Q2 BSS123 SOT-23, R25 4.7 kΩ 0402,
  R26 4.7 kΩ 0402, R27 4.7 kΩ 0402 (GPIO14 ALRT pull-up), R28 100 Ω 0402
  (DS18B20 VCC series), C21 100 nF 0402 (TVS bypass), C22 10 µF 0805 (VBOOST
  parallel), U9 ADS1115IDGST SOIC-8, U10 MAX17048G+T10 SOT-23-6, D8 SMAJ7.0A
  DO-214AC, U3 changed from DW01A to S-8261AAYFT (SOT-23-6, drop-in), J1 changed
  from JST PH 2.0 mm to JST XH 2.5 mm (B2B-XH-AM).
