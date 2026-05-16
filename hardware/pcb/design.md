# WellD Custom PCB — Design Reference

## Overview

| Parameter | Value |
|-----------|-------|
| Module | ESP32-C6-MINI-1U (external antenna, U.FL) |
| Form factor | 80 × 55 mm, 2-layer, 1 oz Cu |
| Target enclosure | Hammond 1551K (83 × 58 × 35 mm) or equiv. IP65 ABS |
| MCU supply | 3.3 V from TPS7A0533 LDO (1 µA Iq), fed from LiPo |
| Loop supply | Independent VLOOP input for 4–20 mA sensors (8–24 V DC) |
| Sensor interfaces | 2× 4–20 mA (screw terminals), 1× DS18B20 (screw terminal), 1× spare 3-pin |
| Expansion | I²C header, 6-pin GPIO header, 4 spare ADC channels |
| Programming | 6-pin 1.27 mm UART header; no USB bridge on board |

---

## GPIO Assignments

All ADC1 channels (GPIO0–GPIO6) are preserved for analog use. DS18B20 is assigned
to GPIO7 (non-ADC) so no ADC channel is sacrificed to a digital sensor.

| GPIO | ADC ch | Function | Connected to |
|------|--------|----------|--------------|
| 0 | CH0 | 4–20 mA sensor 1 | Shunt → ADC via R3/D1 |
| 1 | CH1 | Battery voltage | Onboard divider R7/R8 |
| 2 | CH2 | 4–20 mA sensor 2 | Shunt → ADC via R5/D1 |
| 3 | CH3 | Spare ADC | J9 expansion header |
| 4 | CH4 | Spare ADC | J9 expansion header |
| 5 | CH5 | Spare ADC | J9 expansion header |
| 6 | CH6 | Spare ADC | J9 expansion header |
| 7 | — | DS18B20 1-Wire data | J6 screw terminal |
| 8 | — | Strapping (pull-up) | 10 kΩ to 3.3 V, test pad |
| 9 | — | BOOT strapping | 10 kΩ pull-up; SW2 to GND |
| 10 | — | I²C SDA | J8 header, 4.7 kΩ pull-up |
| 11 | — | I²C SCL | J8 header, 4.7 kΩ pull-up |
| 12 | — | Spare digital | J9 expansion header |
| 13 | — | Status LED | 1 kΩ → D4 → GND; SJ3 to disconnect |
| 14 | — | Spare digital | J9 expansion header |
| 15 | — | Spare digital | J9 expansion header |
| 16 | — | UART0 TX | J10 programming header |
| 17 | — | UART0 RX | J10 programming header |
| 18 | — | USB D− | J2 USB-C (power only) |
| 19 | — | USB D+ | J2 USB-C (power only) |
| 20 | — | Spare digital | J9 expansion header |
| 21 | — | Spare digital | J9 expansion header |

---

## Block Descriptions

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

### Power — LiPo Protection (U3: DW01A + U4: FS8205A)

DW01A (SOT-23-6) monitors cell voltage and current; drives two FS8205A (SOT-23-6)
MOSFETs in back-to-back configuration for over-discharge (< 2.5 V), over-charge
(> 4.35 V), and over-current protection. Standard jellybean combination, widely
stocked on JLCPCB/LCSC. Place as close to the JST-PH battery connector (J1) as
possible.

### Power — 3.3 V LDO (U1: TPS7A0533)

1 µA quiescent current LDO, SC70-5 package, 1 A output. Input from the battery
(after protection circuit). Enables deep-sleep current dominated by the ESP32-C6
module, not the regulator.

Input: 0.1 µF + 1 µF ceramic.
Output: 0.1 µF + 1 µF ceramic.
ENABLE pin: tie high (10 kΩ to VIN) for always-on. Can be driven from a GPIO if
controlled power-down is needed in future.

### ESP32-C6-MINI-1U Module (U6)

Mount on 1.5 mm edge clearance for hand soldering. U.FL antenna connector (J11) on
the short edge nearest the module; route a 50 Ω coplanar waveguide trace from the
module U.FL pad to J11 — keep it under 20 mm with no layer transitions or vias.

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
| 1 | VLOOP | Loop supply input. Connect external 8–24 V DC. |
| 2 | SIG | Transducer return (−) wire. Connects to shunt side. |
| 3 | GND | System ground. |

On-PCB:
- R2 (100 Ω ±0.1%, 0805) is the current shunt, from SIG to GND.
- R3 (100 Ω, 0402) is a series input limiter between SIG and the ADC tap.
- D1 CH1 (PRTR5V0U2X, SOT-363, one device covers both channels 1 and 2) clamps the
  ADC tap to the 3.3 V rail and GND against transients.
- C3 (100 nF) + C4 (10 µF, 0805) on the ADC tap provide a 10 µs RC low-pass filter
  in combination with R3.
- ADC tap → GPIO0.

SJ1 (solder jumper, 2-pad, normally open): closes to connect 3.3 V to the VLOOP pin.
Allows low-voltage (3.3 V-powered) sensors without an external supply. Open by default.

SJ2 (solder jumper, 2-pad, normally closed): bridges J4_VLOOP to J5_VLOOP so both
sensors share a single external supply. Cut to give channels independent supplies.

### 4–20 mA Sensor Interface — Channel 2 (J5)

Identical circuit to Channel 1. Shunt R4 (100 Ω ±0.1%), limiter R5 (100 Ω), ADC
tap protected by D1 CH2. ADC tap → GPIO2.

Intended for a second submersible transducer (e.g. redundancy or separate measurement
point). Firmware support not yet implemented; GPIO2/ADC1_CH2 is exposed and
CONFIG_WELLD_SENSOR_ADC_CHANNEL can be overridden to 2 to switch between channels.

### DS18B20 1-Wire Interface (J6)

3-position pluggable screw terminal, 3.5 mm pitch:

| Pin | Label | Description |
|-----|-------|-------------|
| 1 | VCC | 3.3 V. Must be connected — parasite-power not supported. |
| 2 | DATA | 1-Wire bus. R6 (4.7 kΩ) pull-up to 3.3 V on PCB. |
| 3 | GND | System ground. |

C5 (100 nF) on VCC at the connector provides local decoupling. Multiple DS18B20s can
be bussed on DATA; the firmware locks onto one ROM address after first discovery.

### Spare Sensor (J7)

3-position pluggable screw terminal, 3.5 mm pitch:

| Pin | Label | Description |
|-----|-------|-------------|
| 1 | 3V3 | 3.3 V supply. |
| 2 | IO | GPIO3 / ADC1_CH3. Also connected to J9 header pin. |
| 3 | GND | System ground. |

Populated as a placeholder for a third sensor (flow pulse, analog 0–3 V output,
single-wire protocol, etc.).

### Battery Voltage Divider

Onboard resistor divider from VBAT (after protection circuit, before LDO):
- R7: 100 kΩ (high side)
- R8: 100 kΩ (low side)
- Ratio: 2:1 → CONFIG_WELLD_BATT_DIVIDER_RATIO = 200
- C6: 100 nF across R8 for noise immunity
- ADC tap → GPIO1

The 10 MΩ combined impedance minimises quiescent draw (~0.4 µA at 4.2 V).

### I²C Expansion Header (J8)

4-pin 2.54 mm single-row header:

| Pin | Signal |
|-----|--------|
| 1 | 3.3 V |
| 2 | GND |
| 3 | SDA (GPIO10) |
| 4 | SCL (GPIO11) |

R9 and R10 (4.7 kΩ each) pull SDA and SCL to 3.3 V on the PCB. Suited for I²C
sensors: pressure (e.g. MS5837), conductivity, turbidity, RTC module.

### GPIO Expansion Header (J9)

8-pin 2.54 mm single-row header:

| Pin | Signal |
|-----|--------|
| 1 | 3.3 V |
| 2 | GND |
| 3 | GPIO3 / ADC1_CH3 |
| 4 | GPIO4 / ADC1_CH4 |
| 5 | GPIO5 / ADC1_CH5 |
| 6 | GPIO12 |
| 7 | GPIO14 |
| 8 | GPIO20 |

Spare ADC channels (3–5) are suitable for additional analog sensors (0–3 V output),
pH probes via amplifier, or turbidity sensor output. Digital pins suit pulse
counting, additional 1-Wire sensors, or UART to an RS-485 transceiver.

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
- **ADC traces:** route GPIO0–GPIO2 shunt taps away from switching nodes (LDO,
  USB); ground-plane stitching vias around the shunt resistors
- **50 Ω trace:** module U.FL pad to J11; calculate width for your specific
  stackup (typically 2.9–3.2 mm on standard 1.6 mm FR4 with 35 µm Cu)
- **Test points:** expose VBAT, 3V3, GND, GPIO8, and each ADC tap as 1 mm SMD
  test pads
