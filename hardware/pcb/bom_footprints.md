# WellD PCB — BOM with KiCad 10 Footprints

**Board:** 80 × 55 mm (or your chosen size), 2-layer, 1.6 mm FR4, 1 oz Cu  
**Assembler:** PCBWay PCBA  
**Sourcing key:** ✅ LCSC (direct PCBWay) · ⚠️ PCBWay global sourcing · 📦 Customer-supply to PCBWay

> **2026-07-05 electrical review:** several parts changed (U1, D8/D14, C8, C17, LED GPIO) and new components were added (D15, Q3–Q5, R15/R16/R25/R27/R29, C36, TP13). See `schematic_connections.md` → "Design changes" and "Datasheet verification blockers" before ordering. **The TP5100 USB charge path is non-functional as designed (buck charger cannot make 8.4 V from 5 V USB) — do not order U12 until the charger architecture is resolved.**

---

## Power — Battery Input

| Ref | Value | Package | KiCad 10 Footprint | MPN | LCSC | Notes |
|-----|-------|---------|-------------------|-----|------|-------|
| J1 | XT30PW-F right-angle | THT | `WellD:XT30PW-F_RightAngle` (custom, in WellD.pretty) | XT30PW-F | C601498 ✅ | Pin 1=BAT+, Pin 2=BAT− |
| D5 | AO3407 P-ch MOSFET | SOT-23 | `Package_TO_SOT_SMD:SOT-23` | AO3407 | C31417 ✅ | Reverse-polarity protection |
| R31 | 10kΩ 1% | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | C25741 ✅ | D5 gate pull-down to GND (holds load switch ON) |
| D13 | SMAJ10CA TVS 10V bidi | DO-214AC | `Diode_SMD:D_SMA` | SMAJ10CA | C2836474 ✅ | Battery terminal TVS |

---

## Power — USB-C Charging (TP5100 path)

| Ref | Value | Package | KiCad 10 Footprint | MPN | LCSC | Notes |
|-----|-------|---------|-------------------|-----|------|-------|
| J13 | USB-C 2.0 power-only | 16-pin SMD | `Connector_USB:USB_C_Receptacle_GCT_USB4135` ⚠️ or use GCT KiCad file | USB4135-GF-A | — ⚠️ | GCT publishes KiCad footprint; check PCBWay global sourcing |
| U11 | USBLC6-2SC6 ESD | SOT-23-6 | `Package_TO_SOT_SMD:SOT-23-6` | USBLC6-2SC6 | C7519 ✅ | VBUS + D+/D− clamp |
| F2 | 1A hold PTC fuse | 1206 | `Fuse:Fuse_1206_3216Metric` | MF-MSMF110/16X | — ⚠️ | Series with J13 VBUS |
| U12 | TP5100 2S charger | SOP-8 (⚠️ verify — likely QFN-16) | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` ❌ | TP5100 | C841540 | ⚠️ **CRITICAL: TP5100 is a step-DOWN charger — it cannot charge 2S (8.4V) from 5V USB. Replace (e.g. IP2326-class 5V→2S boost charger) or add a 5V→12V pre-boost. Do not order as-is.** |
| R35 | 1.2kΩ 1% | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | TP5100 PROG: sets 1A charge current |
| R36 | 100kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | CE pull-up to VUSB (dominated by R37 — electrically ineffective, candidate DNP) |
| R37 | 4.7kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | CE pull-down to GND (fail-safe off) |
| R38 | 4.7kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | TP5100 /CHRG pull-up to +3V3 (routes to TP15 only) |
| R50 | 5.1kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | J13 CC1 → GND (was "R_CC1") |
| R51 | 5.1kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | J13 CC2 → GND (was "R_CC2") |
| C27 | 4.7µF 10V X5R | 0805 | `Capacitor_SMD:C_0805_2012Metric` | — | ✅ | VUSB input filter after F2 |
| C28 | 10µF 10V X5R | 0805 | `Capacitor_SMD:C_0805_2012Metric` | — | ✅ | U12 VIN bypass |
| C29 | 10µF 16V X5R | 0805 | `Capacitor_SMD:C_0805_2012Metric` | — | ✅ | U12 VBAT bypass |

---

## Power — Solar MPPT Charging (CN3722 path)

| Ref | Value | Package | KiCad 10 Footprint | MPN | LCSC | Notes |
|-----|-------|---------|-------------------|-----|------|-------|
| U7 | CN3722 2S MPPT charger | SOP-8 | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` | CN3722 | C2690716 ✅ | 5–25V in, 8.4V out |
| D6 | MBRS140 Schottky 1A 40V | SMB | `Diode_SMD:D_SMB` | MBRS140T3G | — ✅ | Solar backfeed block (MBRS140T3G is SMB, not SOD-123) |
| D8 | **SMAJ24CA TVS 24V bidi** | DO-214AC | `Diode_SMD:D_SMA` | SMAJ24CA | — ⚠️ | At CN3722 VIN; same reel as D14. Was SMAJ28CA (zero margin vs CN3722 28V abs max). Panel Voc limit now **24V** |
| R19 | 2.0kΩ 1% | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | VPROG → GND, sets 500mA charge current (⚠️ verify vs CN3722 datasheet) |
| R20 | 36kΩ 1% | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | MPPT divider high-side (VSOLAR→MPPT pin; Vmppt≈5.54V) |
| R21 | 10kΩ 1% | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | MPPT divider low-side (MPPT pin→GND) |
| R33 | **590kΩ 1% E96** | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | CV FB divider high-side (VBAT→FB) → Vchg=1.205×(1+590/100)=8.31V ✓ (was 604kΩ→8.48V, fixed) |
| R34 | 100kΩ 1% | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | CV FB divider low-side (FB→GND) |
| C17 | 10µF **35V** X5R | **1206** | `Capacitor_SMD:C_1206_3216Metric` | — | ✅ | CN3722 VIN filter (rail can sit at panel Voc up to 24V; 25V rating had no margin) |
| C18 | 10µF 16V | 0805 | `Capacitor_SMD:C_0805_2012Metric` | — | ✅ | CN3722 VBAT filter |
| C21 | 100nF **50V** | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | HF bypass at CN3722 VIN (across D8) |
| R25 | 4.7kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | **NEW** — /CHRG_SOLAR pull-up to +3V3 (GPIO6; was internal pull-up only) |
| D7 | Green LED | 0603 | `LED_SMD:LED_0603_1608Metric` | — | ✅ | Solar-charging indicator: +3V3→R22→D7→/CHRG_SOLAR |
| R22 | 1kΩ **DNF** | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | D7 series resistor — DNF by default (fit for bench debug) |

---

## Power — 3.3V Buck (AP63203)

| Ref | Value | Package | KiCad 10 Footprint | MPN | LCSC | Notes |
|-----|-------|---------|-------------------|-----|------|-------|
| U1 | **AP63203WU buck 3.3V fixed** | TSOT-26 | `Package_TO_SOT_SMD:SOT-23-6` | AP63203WU-7 | — ⚠️ look up | 22µA Iq, 2A, VIN 3.8–32V. **Changed from AP63205WU, which is the 5V-fixed variant** — it would have destroyed the 3V3 rail. ⚠️ Verify variant table + pinout in Diodes datasheet before ordering |
| L2 | 4.7µH 1A shielded | 4×4mm SMD | `Inductor_SMD:L_4.0x4.0mm_H2.6mm` ⚠️verify name | CDRH4D22NP-4R7NC | C376098 ✅ | Same part as L1 |
| R_FBH | **DNP** (390kΩ 1% if AP63200WU alt) | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | DNP for fixed-3.3V AP63203WU (FB ties to +3V3). Only for adjustable AP63200WU: 390k/124k → 0.8×(1+390/124)=3.32V. The old 560k/124k assumed a 0.6V ref that no AP6320x part has |
| R_FBL | **DNP** (124kΩ 1% if AP63200WU alt) | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | See R_FBH |
| R11 | 10kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | EN pull-up to VIN (always-on) |
| C16 | 10µF 16V X5R | 0805 | `Capacitor_SMD:C_0805_2012Metric` | — | ✅ | U1 VIN bulk (AP6320x datasheet CIN = 10µF; was an orphan symbol, now assigned) |
| C9 | 100nF 16V | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | VIN bypass |
| C10 | 1µF 16V | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | VIN bulk |
| C11 | 100nF | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | VOUT bypass |
| C12 | 1µF | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | VOUT bulk |
| C_BUCK | 10µF 10V X5R | 0805 | `Capacitor_SMD:C_0805_2012Metric` | — | ✅ | Primary output filter cap after L2 (symbol present, needs wiring) |

---

## Power — 12V VLOOP Boost (MT3608B)

| Ref | Value | Package | KiCad 10 Footprint | MPN | LCSC | Notes |
|-----|-------|---------|-------------------|-----|------|-------|
| U8 | MT3608B boost 12V | SOT-23-6 | `Package_TO_SOT_SMD:SOT-23-6` | MT3608B | C84005 ✅ | GPIO5-gated, EN=HIGH during 4-20mA reads |
| L1 | 4.7µH 1A shielded | 4×4mm SMD | `Inductor_SMD:L_4.0x4.0mm_H2.6mm` ⚠️verify name | CDRH4D22NP-4R7NC | C376098 ✅ | Same part as L2 |
| R23 | 1.91MΩ 1% E96 | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | VOUT divider high-side → VOUT=0.6×(1+1910/100)=12.06V (matches schematic value) |
| R24 | 100kΩ 1% | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | VOUT divider low-side |
| C_BST | 100nF 16V | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | C14663 ✅ | BST↔SW. ⚠️ Classic MT3608 has pin 6 = NC (no BST); harmless if fitted to NC — verify datasheet |
| **D15** | **SS34 Schottky 3A 40V** | DO-214AC | `Diode_SMD:D_SMA` | SS34 | C8678 ✅ | **NEW** — boost rectifier SW→VLOOP (MT3608 is an async boost; there was no rectifier in the BOM) |
| **Q3** | **AO3407 P-ch MOSFET** | SOT-23 | `Package_TO_SOT_SMD:SOT-23` | AO3407 | C31417 ✅ | **NEW** — VLOOP input disconnect (VBAT→Q3→L1); kills the permanent VBAT−0.4V leak through L1+D15 to the loop terminals during sleep |
| **Q4** | **BSS123 N-ch MOSFET** | SOT-23 | `Package_TO_SOT_SMD:SOT-23` | BSS123 | — ✅ | **NEW** — Q3 gate driver, gate on VBOOST_EN (GPIO5) |
| **R29** | **100kΩ** | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | **NEW** — Q3 gate pull-up to VBAT (off by default) |
| **R27** | **100kΩ** | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | **NEW** — VBOOST_EN pull-down (GPIO5 floats in deep sleep) |
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
| Q2 | BSS123 N-ch MOSFET | SOT-23 | `Package_TO_SOT_SMD:SOT-23` | BSS123 | — ✅ | Gate=GPIO15; now drives Q5's gate (level shifter) |
| **Q5** | **AO3407 P-ch MOSFET** | SOT-23 | `Package_TO_SOT_SMD:SOT-23` | AO3407 | C31417 ✅ | **NEW** — high-side divider disconnect (old low-side switch leaked ~14µA into ADS1115 AIN2 during sleep) |
| **R16** | **100kΩ** | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | **NEW** — Q5 gate pull-up to VBAT |
| R7 | 330kΩ 1% | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | Divider high-side (VBAT→midpoint) |
| R8 | 100kΩ 1% | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | Divider low-side (midpoint→GND, direct) |
| R26 | 4.7kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | Q2 gate pull-down |
| C8 | **1nF** X7R | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | Across R8. Was 100nF → τ≈7.7ms, too slow for the firmware's ≥1ms enable window; 1nF settles in <1ms |

---

## MCU — ESP32-C6

| Ref | Value | Package | KiCad 10 Footprint | MPN | LCSC | Notes |
|-----|-------|---------|-------------------|-----|------|-------|
| U6 | ESP32-C6-MINI-1U-H4 | Module | `RF_Module:ESP32-C6-MINI-1` 📦 or Espressif KiCad lib | ESP32-C6-MINI-1U-H4 | C2913202 ✅ | Download Espressif KiCad libraries from github.com/espressif/kicad-libraries |
| C13, C30–C33 | 100nF ×5 | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | VCC3V3 decoupling, within 2mm of module pads (schematic refs; were documented as "C14a–C14d") |
| **R15** | **10kΩ** | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | **NEW** — ESP32 EN pull-up to +3V3 |
| **C36** | **1µF** | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | **NEW** — ESP32 EN→GND reset-delay cap (10ms RC with R15) |
| C15 | 10µF 10V | 0805 | `Capacitor_SMD:C_0805_2012Metric` | — | ✅ | VCC3V3 bulk |
| R12 | 10kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | GPIO9 BOOT pull-up |
| R13 | 10kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | GPIO8 strapping pull-up |
| SW1 | Reset tactile 6×6mm | SMD | `Button_Switch_SMD:SW_Push_6mm_H4.3mm` | — | ✅ | Pulls ESP32 EN to GND |
| SW2 | Boot tactile 6×6mm | SMD | `Button_Switch_SMD:SW_Push_6mm_H4.3mm` | — | ✅ | Pulls GPIO9 to GND |
| D4 | Status LED green | 0603 | `LED_SMD:LED_0603_1608Metric` | — | ✅ | **GPIO14** → R14 → D4 → SJ3 → GND (moved off GPIO13: a green LED + 1k to GND held the factory-reset strap below V_IH → NVS wipe every boot) |
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
| D1 | PRTR5V0U2X dual ESD | SOT-143B | `Package_TO_SOT_SMD:SOT-143` ⚠️ | PRTR5V0U2X | C2687116 ✅ | ADS1115 AIN0/AIN1 input clamp (real part is SOT-143B 4-pin, not SOT-363 — fix symbol/footprint) |
| R2 | 100Ω ±0.1% 0.25W | 0805 | `Resistor_SMD:R_0805_2012Metric` | RG2012N-101-W-T1 | — ⚠️ | CH1 shunt (AIN0 reads across this) |
| R4 | 100Ω ±0.1% 0.25W | 0805 | `Resistor_SMD:R_0805_2012Metric` | RG2012N-101-W-T1 | — ⚠️ | CH2 shunt |
| C34 | 10nF X7R 25V | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | HF bypass directly across R2 (was "C_SH1") |
| C35 | 10nF X7R 25V | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | HF bypass directly across R4 (was "C_SH2") |
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
| D12 | PRTR5V0U2X dual ESD | SOT-143B | `Package_TO_SOT_SMD:SOT-143` ⚠️ | PRTR5V0U2X | C2687116 ✅ | Same part as D1; 1-Wire DATA ESD clamp (IO2 channel NC) |
| R6 | 4.7kΩ | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | 1-Wire pull-up to +3V3 |
| R28 | 100Ω | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | VCC series protection |
| R32 | 33Ω | 0402 | `Resistor_SMD:R_0402_1005Metric` | — | ✅ | **POPULATE** (was DNF) — GPIO abs-max protection for cable runs; resolves review warning #15 |
| C7 | 100nF | 0402 | `Capacitor_SMD:C_0402_1005Metric` | — | ✅ | J6 VCC bypass |

---

## Solar Input Protection

| Ref | Value | Package | KiCad 10 Footprint | MPN | LCSC | Notes |
|-----|-------|---------|-------------------|-----|------|-------|
| D14 | **SMAJ24CA TVS 24V bidi** | DO-214AC | `Diode_SMD:D_SMA` | SMAJ24CA | — ⚠️ | At J12 SOLAR+ terminal; same reel as D8 (was SMAJ28CA — see D8 note) |

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
| D8 | SMAJ24CA 24V bidi | DO-214AC | `Diode_SMD:D_SMA` | SMAJ24CA | — ⚠️ |

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
| TP13 | FACTORY_RESET | **NEW** — GPIO13; short to GND at power-on for NVS erase + rejoin |
| TP14 | /CHRG_SOLAR | Solar charge status (present in interfaces sheet, was missing here) |
| TP15 | /CHRG_USB | TP5100 charge status |

---

## Solder Jumpers

| Ref | Type | KiCad 10 Footprint | Default |
|-----|------|-------------------|---------|
| SJ1 | 2-pad open | `Jumper:SolderJumper-2_P1.3mm_Open_TrianglePad1.0x1.5mm` | Open (DNF) |
| SJ2 | 2-pad bridged | `Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm` | Closed |
| SJ3 | 2-pad bridged | `Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm` | Closed |
| SJ4 | 2-pad bridged | `Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm` | Closed — UART_TX to J10 (was missing here; symbol exists in interfaces sheet) |
| SJ5 | 2-pad bridged | `Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm` | Closed — UART_RX to J10 (was missing here) |

---

## Custom Footprints Needed (not in KiCad standard library)

| Component | Status | Action |
|-----------|--------|--------|
| ESP32-C6-MINI-1U | In `WellD.pretty/` already, verify | Download Espressif KiCad libs as backup |
| XT30PW-F right-angle | In `WellD.pretty/` already | Verify pad dimensions against AMASS datasheet |
| USB4135-GF-A (J13) | Not in standard lib | Download from GCT website (they provide KiCad files) |
| CDRH4D22 inductors (L1, L2) | May need verification | Check `Inductor_SMD:L_4.0x4.0mm_H2.6mm` exists; if not, use KiCad footprint editor to create 4.0×4.0mm SMD pad |
