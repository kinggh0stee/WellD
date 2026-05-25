# WellD PCB — BOM with KiCad 10 Footprints

**Board:** 80 × 55 mm (or your chosen size), 2-layer, 1.6 mm FR4, 1 oz Cu  
**Assembler:** PCBWay PCBA  
**Sourcing key:** ✅ LCSC (direct PCBWay) · ⚠️ PCBWay global sourcing · 📦 Customer-supply to PCBWay

---

## Power — Battery Input

| Ref | Value | Package | KiCad 10 Footprint | MPN | LCSC | Notes |
|-----|-------|---------|-------------------|-----|------|-------|
| J1 | XT30PW-F right-angle | THT | `WellD:XT30PW-F_RightAngle` (custom, in WellD.pretty) | XT30PW-F | C601498 ✅ | Pin 1=BAT+, Pin 2=BAT− |
| D5 | AO3407 P-ch MOSFET | SOT-23 | `Package_TO_SOT_SMD:SOT-23` | AO3407 | C31417 ✅ | Reverse-polarity protection |
| R31 | 10kΩ 1% | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | C25741 ✅ | D5 gate pull-down to GND |
| D13 | SMAJ10CA TVS 10V bidi | DO-214AC | `Diode_SMD:D_SMA` | SMAJ10CA | C2836474 ✅ | Battery terminal TVS |

---

## Power — USB-C Charging (TP5100 path)

| Ref | Value | Package | KiCad 10 Footprint | MPN | LCSC | Notes |
|-----|-------|---------|-------------------|-----|------|-------|
| J13 | USB-C 2.0 power-only | 16-pin SMD | `Connector_USB:USB_C_Receptacle_GCT_USB4135` ⚠️ or use GCT KiCad file | USB4135-GF-A | — ⚠️ | GCT publishes KiCad footprint; check PCBWay global sourcing |
| U11 | USBLC6-2SC6 ESD | SOT-23-6 | `Package_TO_SOT_SMD:SOT-23-6` | USBLC6-2SC6 | C7519 ✅ | VBUS + D+/D− clamp |
| F2 | 1A hold PTC fuse | 1206 | `Fuse:Fuse_1206_3216Metric` | MF-MSMF110/16X | — ⚠️ | Series with J13 VBUS |
| U12 | TP5100 2S boost charger | SOP-8 | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` | TP5100 | C841540 ✅ | 5V→8.4V, 1A |
| R35 | 1.2kΩ 1% | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | TP5100 PROG: sets 1A charge current |
| R36 | 100kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | CE pull-up to VUSB |
| R37 | 4.7kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | CE pull-down to GND (fail-safe off) |
| R38 | 4.7kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | /CHRG pull-up to +3V3 |
| R_CC1 | 5.1kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | J13 CC1 → GND |
| R_CC2 | 5.1kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | J13 CC2 → GND |
| C27 | 4.7µF 10V X5R | 0805 | `Capacitor_SMD:C_0805_2012Metric` | — | ✅ | VUSB input filter after F2 |
| C28 | 10µF 10V X5R | 0805 | `Capacitor_SMD:C_0805_2012Metric` | — | ✅ | U12 VIN bypass |
| C29 | 10µF 16V X5R | 0805 | `Capacitor_SMD:C_0805_2012Metric` | — | ✅ | U12 VBAT bypass |

---

## Power — Solar MPPT Charging (CN3722 path)

| Ref | Value | Package | KiCad 10 Footprint | MPN | LCSC | Notes |
|-----|-------|---------|-------------------|-----|------|-------|
| U7 | CN3722 2S MPPT charger | SOP-8 | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` | CN3722 | C2690716 ✅ | 5–25V in, 8.4V out |
| D6 | MBRS140 Schottky 1A 40V | SOD-123 | `Diode_SMD:D_SOD-123` | MBRS140T3G | — ✅ | Solar backfeed block |
| D8 | SMAJ28CA TVS 28V bidi | DO-214AC | `Diode_SMD:D_SMA` | SMAJ28CA | — ⚠️ | At CN3722 VIN; same reel as D14 |
| R19 | 2.0kΩ 1% | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | Sets 500mA charge current |
| R20 | 36kΩ 1% | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | MPPT divider high-side (Vmppt=5.5V) |
| R21 | 10kΩ 1% | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | MPPT divider low-side |
| R33 | **590kΩ 1% E96** | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | CV high-side → Vchg=8.31V ✓ (was 604kΩ→8.48V, fixed) |
| R34 | 100kΩ 1% | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | CV low-side |
| C17 | 10µF 25V | 0805 | `Capacitor_SMD:C_0805_2012Metric` | — | ✅ | CN3722 VIN filter |
| C18 | 10µF 16V | 0805 | `Capacitor_SMD:C_0805_2012Metric` | — | ✅ | CN3722 VBAT filter |
| C21 | 100nF | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | Bypass across D8 |

---

## Power — 3.3V Buck (AP63205)

| Ref | Value | Package | KiCad 10 Footprint | MPN | LCSC | Notes |
|-----|-------|---------|-------------------|-----|------|-------|
| U1 | AP63205WU buck 3.3V | SOT-23-6 | `Package_TO_SOT_SMD:SOT-23-6` | AP63205WU | C2862534 ✅ | 22µA Iq, 2A, VIN 3.8–32V |
| L2 | 4.7µH 1A shielded | 4×4mm SMD | `Inductor_SMD:L_4.0x4.0mm_H2.6mm` ⚠️verify name | CDRH4D22NP-4R7NC | C376098 ✅ | Same part as L1 |
| **R_FBH** | **560kΩ 1%** | **0402** | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | **ADD TO SCHEMATIC** — VOUT→FB divider high-side → VOUT=3.31V |
| **R_FBL** | **124kΩ 1%** | **0402** | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | **ADD TO SCHEMATIC** — FB→GND divider low-side |
| R11 | 10kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | EN pull-up to VIN (always-on) |
| C9 | 100nF 16V | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | VIN bypass |
| C10 | 1µF 16V | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | VIN bulk |
| C11 | 100nF | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | VOUT bypass |
| C12 | 1µF | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | VOUT bulk |
| **C_BUCK** | **10µF 10V X5R** | **0805** | `Capacitor_SMD:C_0805_2012Metric` | — | ✅ | **ADD TO SCHEMATIC** — primary output filter cap after L2 |

---

## Power — 12V VLOOP Boost (MT3608B)

| Ref | Value | Package | KiCad 10 Footprint | MPN | LCSC | Notes |
|-----|-------|---------|-------------------|-----|------|-------|
| U8 | MT3608B boost 12V | SOT-23-6 | `Package_TO_SOT_SMD:SOT-23-6` | MT3608B | C84005 ✅ | GPIO5-gated, EN=HIGH during 4-20mA reads |
| L1 | 4.7µH 1A shielded | 4×4mm SMD | `Inductor_SMD:L_4.0x4.0mm_H2.6mm` ⚠️verify name | CDRH4D22NP-4R7NC | C376098 ✅ | Same part as L2 |
| R23 | 1.9MΩ 1% | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | VOUT divider high-side → VOUT=12V |
| R24 | 100kΩ 1% | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | VOUT divider low-side |
| **C_BST** | **100nF 16V** | **0402** | `Capacitor_SMD:C_0402_1005Metric` | — | C14663 ✅ | **VERIFY IN SCHEMATIC** — BST pin (pin 6) to SW node; mandatory |
| C19 | 10µF 16V | 0805 | `Capacitor_SMD:C_0805_2012Metric` | — | ✅ | VIN bypass |
| C20 | 22µF 25V X5R | 1206 | `Capacitor_SMD:C_1206_3216Metric` | — | ✅ | VOUT filter |
| C22 | 10µF 25V X5R | 0805 | `Capacitor_SMD:C_0805_2012Metric` | — | ✅ | VOUT parallel with C20 |
| D11 | SMAJ13A TVS 13V uni | DO-214AC | `Diode_SMD:D_SMA` | SMAJ13A | C8057 ✅ | VLOOP terminal clamp |
| SJ1 | Solder jumper NO | — | `Jumper:SolderJumper-2_P1.3mm_Open_TrianglePad1.0x1.5mm` | — | — | MT3608B EN permanent tie, DNF |
| SJ2 | Solder jumper NC | — | `Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm` | — | — | J4/J5 VLOOP bus share |

---

## Battery Divider

| Ref | Value | Package | KiCad 10 Footprint | MPN | LCSC | Notes |
|-----|-------|---------|-------------------|-----|------|-------|
| Q2 | BSS123 N-ch MOSFET | SOT-23 | `Package_TO_SOT_SMD:SOT-23` | BSS123 | — ✅ | Gate=GPIO15; enables divider during measurement |
| R7 | 330kΩ 1% | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | Divider high-side (VBAT→midpoint) |
| R8 | 100kΩ 1% | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | Divider low-side (midpoint→Q2→GND) |
| R26 | 4.7kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | Q2 gate pull-down |
| C8 | 100nF | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | Across R8; settles after Q2 enables |

---

## MCU — ESP32-C6

| Ref | Value | Package | KiCad 10 Footprint | MPN | LCSC | Notes |
|-----|-------|---------|-------------------|-----|------|-------|
| U6 | ESP32-C6-MINI-1U-H4 | Module | `RF_Module:ESP32-C6-MINI-1` 📦 or Espressif KiCad lib | ESP32-C6-MINI-1U-H4 | C2913202 ✅ | Download Espressif KiCad libraries from github.com/espressif/kicad-libraries |
| C14a–C14d | 100nF ×4 | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | VCC3V3 decoupling, within 2mm of module pads |
| C15 | 10µF 10V | 0805 | `Capacitor_SMD:C_0805_2012Metric` | — | ✅ | VCC3V3 bulk |
| R12 | 10kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | GPIO9 BOOT pull-up |
| R13 | 10kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | GPIO8 strapping pull-up |
| SW1 | Reset tactile 6×6mm | SMD | `Button_Switch_SMD:SW_Push_6mm_H4.3mm` | — | ✅ | Pulls ESP32 EN to GND |
| SW2 | Boot tactile 6×6mm | SMD | `Button_Switch_SMD:SW_Push_6mm_H4.3mm` | — | ✅ | Pulls GPIO9 to GND |
| D4 | Status LED green | 0603 | `LED_SMD:LED_0603_1608Metric` | — | ✅ | GPIO13 → R14 → D4 → GND |
| R14 | 1.0kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | LED current limit |
| SJ3 | Solder jumper NC | — | `Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm` | — | — | LED disconnect to save current |

---

## ADC — ADS1115

| Ref | Value | Package | KiCad 10 Footprint | MPN | LCSC | Notes |
|-----|-------|---------|-------------------|-----|------|-------|
| U9 | ADS1115IDGST 16-bit I²C | MSOP-10 | `Package_SO:MSOP-10_3x3mm_P0.5mm` | ADS1115IDGST | C37593 ✅ | Addr 0x48 (ADDR→GND) |
| FB1 | 600Ω@100MHz ferrite | 0402 | `Inductor_SMD:L_0402_1005Metric` | BLM18KG601SN1D | C76537 ✅ | In +3V3 feed to U9 VDD |
| C23 | 100nF | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | U9 VDD bypass, U9 side of FB1 |
| C24 | 1µF | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | U9 VDD bulk |
| R9 | 4.7kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | I²C SDA pull-up (GPIO10) |
| R10 | 4.7kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | I²C SCL pull-up (GPIO11) |
| **R_DRDY** | **4.7kΩ** | **0402** | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | **ADD TO SCHEMATIC** — ADS_DRDY to +3V3; required open-drain pull-up |

---

## Sensors — 4-20mA Channels

| Ref | Value | Package | KiCad 10 Footprint | MPN | LCSC | Notes |
|-----|-------|---------|-------------------|-----|------|-------|
| D9 | SMAJ3.3CA TVS 3.3V bidi | DO-214AC | `Diode_SMD:D_SMA` | SMAJ3.3CA | C2836497 ✅ | J4 SIG surge clamp |
| D10 | SMAJ3.3CA TVS 3.3V bidi | DO-214AC | `Diode_SMD:D_SMA` | SMAJ3.3CA | C2836497 ✅ | J5 SIG surge clamp |
| D1 | PRTR5V0U2X dual ESD | SOT-363 | `Package_TO_SOT_SMD:SOT-363` | PRTR5V0U2X | C2687116 ✅ | ADS1115 AIN0/AIN1 input clamp |
| R2 | 100Ω ±0.1% 0.25W | 0805 | `Resistor_SMD:R_0805_2012Metric` | RG2012N-101-W-T1 | — ⚠️ | CH1 shunt (AIN0 reads across this) |
| R4 | 100Ω ±0.1% 0.25W | 0805 | `Resistor_SMD:R_0805_2012Metric` | RG2012N-101-W-T1 | — ⚠️ | CH2 shunt |
| C_SH1 | 10nF X7R 25V | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | HF bypass directly across R2 |
| C_SH2 | 10nF X7R 25V | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | HF bypass directly across R4 |
| R3 | 100Ω | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | CH1 series limiter to AIN0 |
| R5 | 100Ω | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | CH2 series limiter to AIN1 |
| C3 | 1µF X5R | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | CH1 RC filter with R3 (fc≈1.6kHz) |
| C5 | 1µF X5R | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | CH2 RC filter with R5 |
| C4 | 10µF 10V | 0805 | `Capacitor_SMD:C_0805_2012Metric` | — | ✅ | CH1 bulk |
| C6 | 10µF 10V | 0805 | `Capacitor_SMD:C_0805_2012Metric` | — | ✅ | CH2 bulk |

---

## Sensors — DS18B20 1-Wire

| Ref | Value | Package | KiCad 10 Footprint | MPN | LCSC | Notes |
|-----|-------|---------|-------------------|-----|------|-------|
| D12 | PRTR5V0U2X dual ESD | SOT-363 | `Package_TO_SOT_SMD:SOT-363` | PRTR5V0U2X | C2687116 ✅ | Same part as D1; 1-Wire DATA ESD clamp |
| R6 | 4.7kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | 1-Wire pull-up to +3V3 |
| R28 | 100Ω | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | VCC series protection |
| R32 | 33Ω | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | **Change from DNF to POPULATE** — GPIO abs-max protection; see reviewer note |
| C7 | 100nF | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | J6 VCC bypass |

---

## Solar Input Protection

| Ref | Value | Package | KiCad 10 Footprint | MPN | LCSC | Notes |
|-----|-------|---------|-------------------|-----|------|-------|
| D14 | SMAJ28CA TVS 28V bidi | DO-214AC | `Diode_SMD:D_SMA` | SMAJ28CA | — ⚠️ | At J12 SOLAR+ terminal; same reel as D8 |

---

## Connectors — Field Side

> **Connector strategy:** PCB headers (G series, screw-clamp side that stays on the board) are LCSC-available and wave-soldered by PCBWay. Field plugs have been upgraded to **spring-cage** (STF series) — no screws to strip. Order field plugs from Mouser/Digi-Key and include them in the box with the product; they do not go to PCBWay.

| Ref | PCB Header (PCBWay assembles) | KiCad 10 Footprint | LCSC | Field Plug (ship separately) | MPN |
|-----|------------------------------|-------------------|------|------------------------------|-----|
| J4 | Phoenix MC 1.5/3-G-3.5 | `Connector_Phoenix_MC:PhoenixContact_MC_1,5_3-G-3,5_1x03_P3.50mm_Horizontal` | ✅ | **MC 1.5/3-STF-3.5** (spring-cage, no screws) | 1827755 |
| J5 | Phoenix MC 1.5/3-G-3.5 | same as J4 | ✅ | **MC 1.5/3-STF-3.5** | 1827755 |
| J6 | Phoenix MC 1.5/3-G-3.5 | same as J4 | ✅ | **MC 1.5/3-STF-3.5** | 1827755 |
| J7 | Phoenix MC 1.5/3-G-3.5 | same as J4 | ✅ | **MC 1.5/3-STF-3.5** | 1827755 |
| J12 | Phoenix MC 1.5/2-G-3.5 | `Connector_Phoenix_MC:PhoenixContact_MC_1,5_2-G-3,5_1x02_P3.50mm_Horizontal` | ✅ | **MC 1.5/2-STF-3.5** (spring-cage, 2-pos) | 1827742 |

> **Why spring-cage works with the same PCB header:** Phoenix Contact's MC 1.5 G-series headers accept both ST (screw) and STF (spring-cage) plugs of the same pitch. No board change needed — just swap the plug type.

---

## Connectors — Programming & Expansion

| Ref | Value | Package | KiCad 10 Footprint | Notes |
|-----|-------|---------|-------------------|-------|
| J10 | 6-pin 1.27mm prog header | THT | `Connector_PinHeader_1.27mm:PinHeader_1x06_P1.27mm_Vertical` | UART TX/RX/GND/3V3/GPIO9/EN |
| J3 | SMA edge-launch (Amphenol 132289) | SMD edge | `Connector_Coaxial:SMA_Amphenol_132289_EdgeMount` | ✅ in KiCad standard lib |
| J8 | I²C header 4-pin 2.54mm | THT DNF | `Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical` | DNF |
| J9 | GPIO header 8-pin 2.54mm | THT DNF | `Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical` | DNF |

---

## ESD / Reverse Polarity

| Ref | Value | Package | KiCad 10 Footprint | MPN | LCSC |
|-----|-------|---------|-------------------|-----|------|
| D8 | SMAJ28CA 28V bidi | DO-214AC | `Diode_SMD:D_SMA` | SMAJ28CA | — ⚠️ |

---

## Test Points (all DNF — pads only)

All test points use: `TestPoint:TestPoint_Pad_1.0x1.0mm`

| Ref | Net | Notes |
|-----|-----|-------|
| TP1 | VBAT | After D5 |
| TP2 | VLOOP | After U8 VOUT |
| TP3 | +3V3 | After U1 |
| TP4 | GND | Reference |
| TP5 | LOOP_TERM_CH1 | Between R2 and R3 |
| TP6 | LOOP_TERM_CH2 | Between R4 and R5 |
| TP7 | 1WIRE | At J6 DATA |
| TP8 | I2C_SDA | GPIO10 |
| TP9 | I2C_SCL | GPIO11 |
| TP10 | VSOLAR_IN | At J12 |
| TP11 | VBAT_RAW | At J1 BAT+, before D5 |
| TP12 | ADS_DRDY | GPIO12 interrupt line |
| TP15 | /CHRG_USB | TP5100 charge status |

---

## Solder Jumpers

| Ref | Type | KiCad 10 Footprint | Default |
|-----|------|-------------------|---------|
| SJ1 | 2-pad open | `Jumper:SolderJumper-2_P1.3mm_Open_TrianglePad1.0x1.5mm` | Open (DNF) |
| SJ2 | 2-pad bridged | `Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm` | Closed |
| SJ3 | 2-pad bridged | `Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm` | Closed |

---

## Custom Footprints Needed (not in KiCad standard library)

| Component | Status | Action |
|-----------|--------|--------|
| ESP32-C6-MINI-1U | In `WellD.pretty/` already, verify | Download Espressif KiCad libs as backup |
| XT30PW-F right-angle | In `WellD.pretty/` already | Verify pad dimensions against AMASS datasheet |
| USB4135-GF-A (J13) | Not in standard lib | Download from GCT website (they provide KiCad files) |
| CDRH4D22 inductors (L1, L2) | May need verification | Check `Inductor_SMD:L_4.0x4.0mm_H2.6mm` exists; if not, use KiCad footprint editor to create 4.0×4.0mm SMD pad |
