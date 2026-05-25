# WellD Schematic — Net Connectivity Reference

The schematic files contain component symbol placements but **no wire connections**. This document is the authoritative wiring reference. Use it alongside the schematic editor to draw all nets manually, or run `kicad_wire_script.py` in the KiCad scripting console (see `kicad_guide_eli5.md`).

---

## Net Inventory

| Net name | Voltage | Description |
|----------|---------|-------------|
| GND | 0V | Ground plane |
| +3V3 | 3.31V | Main logic rail (AP63205WU output) |
| VBAT | 6.0–8.4V | 2S Li-ion battery (raw, after D5 load-switch) |
| VBAT_RAW | 6.0–8.4V | Battery positive before D5 (connects J1 BAT+, D5 drain, D13 anode) |
| VUSB | 5V | USB-C VBUS after F2 polyfuse |
| VUSB_IN | 5V | USB-C VBUS raw (J13 VBUS pins) |
| VSOLAR | Open-circuit PV | Solar panel after D6 diode |
| VSOLAR_IN | Open-circuit PV | Solar panel raw (J12 terminal, before D14/D6) |
| VLOOP | 12V ±5% | Boost output (MT3608B, loop power) |
| +3V3_ADS | 3.3V filtered | ADS1115 VDD (after FB1 ferrite bead, isolated from digital) |
| MPPT_REF | ~1.25V | CN3722 MPPT voltage reference divider mid-point |
| ADS_DRDY | signal | ADS1115 ALERT/DRDY open-drain → GPIO12 |
| ADS_SDA | signal | I²C SDA → GPIO10 |
| ADS_SCL | signal | I²C SCL → GPIO11 |
| ADC_CH0 | 0–2.048V | ADS1115 AIN0 (CH1 4-20mA after protection chain) |
| ADC_CH1 | 0–2.048V | ADS1115 AIN1 (CH2 4-20mA after protection chain) |
| ADC_CH2 | 0–2.048V | ADS1115 AIN2 (battery voltage divider output) |
| 1WIRE | signal | DS18B20 one-wire bus → GPIO7 |
| LOOP_TERM_CH1 | signal | CH1 4-20mA input from J4 |
| LOOP_TERM_CH2 | signal | CH2 4-20mA input from J5 |
| /CHRG_SOLAR | signal | CN3722 /CHRG status (active-low) → GPIO6 |
| /CHRG_USB | signal | TP5100 /CHRG open-drain status |
| CHRG_USB_DIS | signal | TP5100 CE enable (HIGH = charge enabled via VUSB pull-up) |
| BATT_DIV_EN | signal | Q2 gate = GPIO15; HIGH enables battery divider read |
| VBOOST_EN | signal | MT3608B EN pin = GPIO5; HIGH enables 12V boost |
| SOLAR_DET | signal | CN3722 /DONE or solar detect |
| GPIO13_LED | signal | Status LED (GPIO13) |
| UART_TX | signal | Debug UART TX (GPIO16 or via header) |
| UART_RX | signal | Debug UART RX |
| EN | signal | ESP32-C6 EN (reset) |
| BOOT | signal | ESP32-C6 BOOT/GPIO9 (low = download mode) |

---

## Net-by-Net Pin Connections

### GND

| Component | Pin | Note |
|-----------|-----|------|
| U1 AP63205WU | GND (pin 2) | Buck converter GND |
| U7 CN3722 | GND (pin 4) | Solar charger GND |
| U8 MT3608B | GND (pin 2) | Boost converter GND |
| U9 ADS1115 | GND (pin 1) | ADC GND |
| U6 ESP32-C6-MINI-1U | GND (multiple) | Module GND |
| U11 USBLC6-2SC6 | GND | USB ESD clamp GND |
| U12 TP5100 | GND (exposed pad) | USB charger thermal/GND pad |
| R_FBL | pin 2 | AP63205WU feedback divider low-side |
| C9, C10 | pin 2 | AP63205WU VIN decoupling |
| C11, C12 | pin 2 | +3V3 output decoupling near L2 |
| C16 | pin 2 | +3V3 (verify = C_BUCK or remove) |
| C17, C18 | pin 2 | CN3722 VIN/VBAT decoupling |
| C19 | pin 2 | MT3608B VIN bypass |
| C20, C22 | pin 2 | MT3608B VOUT decoupling |
| C_BUCK | pin 2 | AP63205WU primary output filter |
| C23, C24 | pin 2 | ADS1115 VDD decoupling (on +3V3_ADS side of FB1) |
| C14a–C14d | pin 2 | ESP32-C6 VCC3V3 decoupling |
| C15 | pin 2 | ESP32-C6 VCC3V3 bulk |
| C27, C28 | pin 2 | TP5100 VIN bypass |
| C29 | pin 2 | TP5100 VBAT bypass |
| R3, R5 | pin 2 (shunt low-side) | 4-20mA shunt return |
| R7, R8 | pin 2 (divider) | VBAT voltage divider GND side |
| D1, D9, D10 | cathode groups | TVS clamps |
| D6 | anode | Solar backfeed Schottky |
| D8 SMAJ28CA | one end | Solar TVS at CN3722 VIN |
| D13 SMAJ10CA | one end | Battery TVS at J1 |
| F1, F2 | — | Polyfuses (no direct GND pin) |
| J3 SMA | ground ring | Antenna connector GND |
| TP1, TP3, TP4 (GND TPs) | — | Near buck output |

### +3V3

| Component | Pin | Note |
|-----------|-----|------|
| U1 AP63205WU | SW (pin 4) via L2 | Buck output (SW→L2→+3V3) |
| L2 | pin 2 (output) | Buck output inductor |
| R_FBH | pin 1 (top) | Feedback high-side; pin 2 connects to FB |
| C_BUCK | pin 1 | Primary output filter cap (10µF 0805) — ADD THIS |
| C11, C12 | pin 1 | Output rail decoupling near L2 |
| C16 | pin 1 | If C16 = C_BUCK; otherwise resolve |
| FB1 | pin 1 (input) | Ferrite bead feeding +3V3_ADS |
| R9 | pin 1 | I²C SDA pull-up |
| R10 | pin 1 | I²C SCL pull-up |
| R_DRDY | pin 1 | ADS1115 DRDY pull-up — ADD THIS |
| R38 | pin 1 | /CHRG_SOLAR pull-up |
| R37 | connects to VUSB | CE pull-up (R37 goes to VUSB not +3V3 — see note) |
| U6 ESP32-C6-MINI-1U | VCC3V3 (multiple) | Module supply |
| C14a–C14d | pin 1 | Module decoupling |
| C15 | pin 1 | Module bulk cap |
| TP1 | pad | +3V3 test point |

> **R37 note**: R37 pulls the TP5100 CE pin to VUSB (5V), not +3V3. GPIO4 asserts CE LOW to disable charging; the 5V pull-up auto-enables when VUSB present. See Warning #12 in senior_review_2026-05-25.md.

### +3V3_ADS

| Component | Pin | Note |
|-----------|-----|------|
| FB1 | pin 2 (output) | Ferrite bead isolates ADS supply from digital noise |
| U9 ADS1115 | VDD (pin 4) | ADS1115 supply |
| C23 | pin 1 | 100nF decoupling (on ADS side of FB1) |
| C24 | pin 1 | 1µF decoupling (on ADS side of FB1) |

### VBAT

| Component | Pin | Note |
|-----------|-----|------|
| D5 AO3407 | source | Load-switch output (switches VBAT from battery) |
| U1 AP63205WU | VIN (pin 1) | Buck input |
| U7 CN3722 | VBAT (pin 3) | Charger output |
| U8 MT3608B | VIN (pin 1) | Boost input |
| C9, C10 | pin 1 | AP63205WU VIN decoupling |
| C17 | pin 1 (also CN3722 VIN net) | Filter cap |
| C18 | pin 1 | CN3722 VBAT cap |
| C19 | pin 1 | MT3608B VIN bypass |
| TP11 | pad | VBAT test point after D5 |
| R7 | pin 1 (divider top) | VBAT→R7→VBAT_DIV_MID→R8→GND divider |

### VBAT_RAW

| Component | Pin | Note |
|-----------|-----|------|
| J1 XT30 | BAT+ | Battery positive input |
| D13 SMAJ10CA | anode | Battery TVS protection |
| D5 AO3407 | drain | Load-switch input |
| R31 | pin 2 (to gate?) | R31 in D5/R31 protection group — see placement_constraints.md Group H |

### VLOOP

| Component | Pin | Note |
|-----------|-----|------|
| U8 MT3608B | VOUT (pin 5) via L1 | Boost output |
| L1 | pin 2 (output) | Boost output inductor |
| C20 | pin 1 | VOUT decoupling |
| C22 | pin 1 | VOUT parallel cap |
| J4 | LOOP+ (pin 1) | CH1 4-20mA loop power |
| J5 | LOOP+ (pin 1) | CH2 4-20mA loop power |
| TP2 | pad | VLOOP test point |

### VSOLAR / VSOLAR_IN

| Component | Pin | Note |
|-----------|-----|------|
| J12 | SOLAR+ | Solar terminal input |
| D14 | anode | First TVS clamp (J12→D14→D6) |
| D14 | cathode | Connects to D6 anode and D8 |
| D6 | cathode | VSOLAR (solar after Schottky, goes to U7 VIN) |
| D8 SMAJ28CA | anode | Second-stage TVS at CN3722 VIN |
| U7 CN3722 | VIN (pin 1) | Solar charger input |
| C17 | pin 1 | CN3722 VIN filter |
| C21 | pin 1 | CN3722 VIN second filter |
| TP10 | pad | Solar input test point |

### VUSB / VUSB_IN

| Component | Pin | Note |
|-----------|-----|------|
| J13 USB-C | VBUS pins | USB-C VBUS input |
| U11 USBLC6-2SC6 | VBUS pin | USB ESD protection |
| F2 | pin 1 | Polyfuse input |
| F2 | pin 2 | VUSB output (to U12 VIN and R37) |
| C27 | pin 1 | VUSB input filter after F2 |
| U12 TP5100 | VIN | USB charger input |
| R37 | pin 1 | CE pull-up (other end to U12 CE pin) |

### AP63205WU Feedback Net (FB)

| Component | Pin | Note |
|-----------|-----|------|
| U1 AP63205WU | FB (pin 3) | Feedback input; sets VOUT |
| R_FBH | pin 2 (bottom) | High-side top at +3V3, bottom at FB |
| R_FBL | pin 1 (top) | Low-side top at FB, bottom at GND |

> This net has no name yet. Name it `AP_FB` in KiCad. VOUT = 0.6 × (1 + 560k/124k) = 3.31V.

### MT3608B Bootstrap (BST→SW)

| Component | Pin | Note |
|-----------|-----|------|
| U8 MT3608B | BST (pin 6) | Bootstrap supply input |
| C_BST | pin 1 | 100nF cap; other end to SW node |
| U8 MT3608B | SW (pin 3) | Switching node |
| C_BST | pin 2 | SW side of bootstrap cap |
| L1 | pin 1 | Also connects to SW node |

### ADS_DRDY

| Component | Pin | Note |
|-----------|-----|------|
| U9 ADS1115 | ALERT/DRDY (pin 7) | Open-drain output |
| R_DRDY | pin 2 (bottom) | Pull-up; pin 1 connects to +3V3 |
| U6 ESP32-C6-MINI-1U | GPIO12 | Interrupt input |
| TP12 | pad | DRDY test point |

### ADS_SDA / ADS_SCL

| Component | Pin | Note |
|-----------|-----|------|
| U9 ADS1115 | SDA (pin 6) | I²C data |
| U6 ESP32-C6 | GPIO10 | SDA |
| R9 | pin 2 (bottom) | Pull-up (top to +3V3) |
| J8 | SDA pin | I²C header |
| TP8 | pad | SDA test point |
| U9 ADS1115 | SCL (pin 5) | I²C clock |
| U6 ESP32-C6 | GPIO11 | SCL |
| R10 | pin 2 (bottom) | Pull-up (top to +3V3) |
| J8 | SCL pin | I²C header |
| TP9 | pad | SCL test point |

### ADC_CH0, ADC_CH1 (4-20mA inputs)

CH1 signal path: J4 SIG → D9 (TVS) → R2 (100Ω shunt) → TP5 → R3 → D1 → C3 (bypass) → C4 (bypass) → U9 AIN0

| Component | Pin | Net segment | Note |
|-----------|-----|-------------|------|
| J4 | SIG (pin 2) | LOOP_TERM_CH1 | CH1 current input |
| D9 SMAJ3.3CA | anode | LOOP_TERM_CH1 | First protection TVS |
| D9 | cathode | shunt_in_1 | After TVS |
| R2 | pin 1 | shunt_in_1 | Shunt top |
| R2 | pin 2 | shunt_out_1 | Shunt bottom (AIN0 side) |
| R3 | pin 1 | shunt_out_1 | Series protection |
| R3 | pin 2 | ADC_CH0 | To ADS1115 |
| C3 | pin 1 | ADC_CH0 | Bypass cap |
| C4 | pin 1 | ADC_CH0 | Bypass cap |
| D1 PRTR5V0U2X | one channel | ADC_CH0 | Rail clamp protection |
| U9 ADS1115 | AIN0 (pin 8) | ADC_CH0 | ADC input |
| TP5 | pad | Between R2 and R3 | Test point |

CH2 is identical: J5 → D10 → R4 → R5 → D1 channel 2 → C5/C6 → U9 AIN1

### ADC_CH2 (Battery voltage divider)

| Component | Pin | Note |
|-----------|-----|------|
| R7 | pin 1 | Top — connects to VBAT (8.4V max) |
| R7 | pin 2 | Mid — connects to R8 pin 1 |
| R8 | pin 2 | Bottom — connects to GND |
| R7/R8 mid | — | Divider output (named ADC_CH2) |
| C_SH | pin 1 | Filter cap across divider (if present) |
| Q2 | drain | Q2 gate-controlled switch in divider enable path |
| U9 ADS1115 | AIN2 (pin 10) | ADC input |
| U6 ESP32-C6 | GPIO15 (BATT_DIV_EN) | Enables Q2 before read |

### 1WIRE

| Component | Pin | Note |
|-----------|-----|------|
| J6 | DATA (pin 2) | DS18B20 data line |
| D12 PRTR5V0U2X | data channel | ESD protection |
| R6 | pin 2 | Pull-up (pin 1 to +3V3) |
| R32 | pin 1 | 33Ω series resistor (populate — see warning #15) |
| R32 | pin 2 | After series R, to GPIO7 |
| U6 ESP32-C6 | GPIO7 | 1-Wire GPIO |
| TP7 | pad | On GPIO7 side of D12 |

### /CHRG_SOLAR

| Component | Pin | Note |
|-----------|-----|------|
| U7 CN3722 | /CHRG (pin 5) | Open-drain active-low charging indicator |
| R38 | pin 2 | Pull-up to +3V3 |
| U6 ESP32-C6 | GPIO6 | Firmware reads LOW = charging |

### CHRG_USB_DIS / CE

| Component | Pin | Note |
|-----------|-----|------|
| R37 | pin 2 | Pull-up to VUSB (5V) |
| U12 TP5100 | CE (enable pin) | HIGH = charge enabled |
| U6 ESP32-C6 | GPIO4 | LOW asserted by firmware disables charging |

### VBOOST_EN

| Component | Pin | Note |
|-----------|-----|------|
| U8 MT3608B | EN (pin 4) | Enable; HIGH = boost active |
| U6 ESP32-C6 | GPIO5 | Firmware drives HIGH to power loop |

### MPPT_REF

| Component | Pin | Note |
|-----------|-----|------|
| U7 CN3722 | MPPT (pin 6) | Voltage reference input |
| R19 | pin 2 | Divider mid-point (R19 top to VSOLAR, R20 bottom to GND) |
| R20 | pin 1 | MPPT divider low-side |

### CN3722 CV Setpoint (PROG)

| Component | Pin | Note |
|-----------|-----|------|
| U7 CN3722 | PROG (pin 7) | CV voltage set |
| R33 | pin 2 | 590kΩ (was 604kΩ) — sets Vchg = 8.31V |
| R34 | pin 2 | Sets charge termination (parallel with R33 per CN3722 app note?) |
| R21 | pin 2 | Possible CC current set resistor |

> Verify exact PROG pin connections against CN3722 datasheet Fig.8. R33=590kΩ sets Vchg=8.31V. R34=100kΩ may set another parameter.

### TP5100 USB Charge Current (PROG)

| Component | Pin | Note |
|-----------|-----|------|
| U12 TP5100 | PROG (pin 5) | Charge current set |
| R35 | pin 1 | PROG → GND; current = 1200/R35 [mA] |

### USB-C CC Resistors

| Component | Pin | Note |
|-----------|-----|------|
| J13 | CC1 | USB-C CC1 |
| R_CC1 | pin 1 | 5.1kΩ CC1 pull-down to GND |
| J13 | CC2 | USB-C CC2 |
| R_CC2 | pin 1 | 5.1kΩ CC2 pull-down to GND |

### GPIO13_LED

| Component | Pin | Note |
|-----------|-----|------|
| U6 ESP32-C6 | GPIO13 | LED drive |
| R (LED series) | pin 1 | Current limit |
| LED | anode | Status LED |

---

## Power-On Sequence Reference

1. Battery connects → VBAT_RAW present → D5 auto-on (or R31/firmware-controlled) → VBAT available
2. AP63205WU starts → +3V3 rail up (R_FBH/R_FBL set to 3.31V) → ESP32 boots
3. Firmware: GPIO5 HIGH → MT3608B enables → VLOOP = 12V → 4-20mA transducer powered
4. Firmware: GPIO15 HIGH → Q2 on → battery divider active → ADS1115 reads AIN2
5. Firmware: GPIO15 LOW, GPIO5 LOW → everything off before deep sleep

---

## Components Still Needing Resolution in KiCad

| Symbol | Issue | Action in KiCad |
|--------|-------|-----------------|
| C25 (100nF, at 66.04,185.42 in power.kicad_sch) | Documented as removed but present in schematic | Either wire it as C_BST (BST→SW) and delete new C_BST symbol, or delete C25 |
| C16 (10µF, at 96.52,90.17 in power.kicad_sch) | No BOM row — may be C_BUCK | If it is C_BUCK: rename to C_BUCK and delete new C_BUCK symbol; otherwise delete |
| R_FBH / R_FBL | Added as symbols with no wires | Wire: +3V3 → R_FBH pin1 → R_FBH pin2 → (FB net) → R_FBL pin1 → R_FBL pin2 → GND |
| R_DRDY | Added as symbol with no wires | Wire: +3V3 → R_DRDY pin1 → R_DRDY pin2 → ADS_DRDY net |
| C_BST | Added as symbol with no wires | Wire: U8 BST(pin6) → C_BST pin1 → C_BST pin2 → U8 SW(pin3) node |
| C_BUCK | Added as symbol with no wires | Wire: +3V3 → C_BUCK pin1 → C_BUCK pin2 → GND; place after L2 output |
