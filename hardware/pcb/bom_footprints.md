# WellD PCB — Bill of Materials

**Board:** 2-layer, 1.6 mm FR-4, 1 oz copper; outline set at layout (working target ≈100 × 60 mm, driven by the top-side 18650 carrier).
**Assembly:** PCBWay PCBA, parts ordered by the LCSC numbers below. Single-sided (top) SMT plus THT connectors.
**Source of truth:** the Value / Footprint / LCSC fields in the schematic. This document mirrors them one row per reference (163 parts) and adds the MPN and the reason for each choice. Every LCSC number was looked up in LCSC's catalogue on **2026-11-28** (several older numbers pointed at unrelated parts — pin headers, a 10 kV diode — and were replaced); "generic" means any LCSC part of that value, tolerance and size.

**Fit legend:** **DNF** = footprint placed, part not fitted (schematic DNP flag). *Footprint only* = bare pads with no part (test points, solder jumpers) — excluded from the BOM and placement files.

## Not on the board

| Item | Qty | Part | Notes |
|------|-----|------|-------|
| Field plugs, 3-pos | 4 | Phoenix MC 1,5/3-STF-3,5 (1827755), spring-cage | Mate with the J4–J7 MC 1,5 G headers; ship with the device |
| Field plug, 2-pos | 1 | Phoenix MC 1,5/2-STF-3,5 (1827742), spring-cage | Mates with J12 |
| 18650 cell | 1 | generic quality 18650, ≈3–3.4 Ah | Worst-case co-charge ≈2.2 A (TP4056 1 A + CN3791 1.2 A) ≈ 0.65C — use a high-rate cell, or R_PROG = 2.4 kΩ |
| RF pigtail W1 | 1 | Taoglas CAB.100.07.0050B (U.FL → SMA plug, 50 mm) — *pending* | Depends on the RF decision in README.md (decision 1) |
| Antenna | 1 | 2.4 GHz SMA, e.g. Taoglas FXP73 | — |

## Project library parts (`WellD.pretty`, `welld.kicad_sym`)

| Item | Source |
|------|--------|
| `WellD:ESP32-C6-MINI-1U` footprint + `welld:ESP32-C6-MINI-1U` symbol | Copied unchanged from Espressif's kicad-libraries (CC-BY-SA 4.0 with the KiCad design exception); the 3D model needs the Espressif PCM package |
| `WellD:GDT_Littelfuse_GTCS23` | Drawn 2026-11-28 from the Littelfuse GTCS23 datasheet land pattern (pads 2.0 × 3.0 mm, 2.0 mm gap) |
| Other `welld:` symbols (charger, regulator, protection, ADC, transistors) | Drawn for this project; pinouts and sources in `schematic_connections.md` → *Symbol pin-number verification* |

Every other footprint is from the KiCad 10 standard library; `footprint_check.py` confirms each exists and matches its symbol's pins.

## Battery and protection

| Ref | Value | Footprint | MPN | LCSC | Notes |
|-----|-------|-----------|-----|------|-------|
| BT1 | 18650 holder | `Battery:BatteryHolder_Keystone_1042_1x18650` | Keystone 1042 | — | Single generic 18650 (≈3–3.4 Ah). Keystone 1042 = off-LCSC (Digi-Key/Mouser, customer-supplied). The LCSC MYOUNG BH-18650-B1BA002 (C2988620) does **not** fit this land: its pads sit 82.6 mm apart vs 79.4 mm — see README decision 2 |
| U13 | DW01A | `Package_TO_SOT_SMD:SOT-23-6` | DW01A (PUOLOP) | C351410 | 1S protection supervisor: over-discharge 2.40 V (release 3.0), over-charge 4.30 V (release 4.1). R_DW1 + C_DW + R_CS_DW = datasheet typical application |
| Q6 | FS8205A | `Package_SO:TSSOP-8_4.4x3mm_P0.65mm` | FS8205A (Fortune) | C14212 | Dual N-FET in the cell− path, 20 V. ⚠️ LCSC stock was 0 on 2026-11-28 (also C16052) — order early or source globally; the common SOT-23-6 FS8205A has a different pinout and footprint |
| R_DW1 | 100R | `Resistor_SMD:R_0402_1005Metric` | — | generic | DW01A VCC filter |
| C_DW | 100nF | `Capacitor_SMD:C_0402_1005Metric` | — | generic | DW01A VCC filter (to BATT_N) |
| R_CS_DW | 1k | `Resistor_SMD:R_0402_1005Metric` | — | generic | DW01A CS series resistor to system GND |
| D5 | AO3407A | `Package_TO_SOT_SMD:SOT-23` | AO3407A (AOS) | C15155 | Reverse-polarity P-FET on cell+ (gate held low by R31) — blocks a reversed cell |
| R31 | 10k | `Resistor_SMD:R_0402_1005Metric` | — | generic | D5 gate pull-down |
| D13 | SMAJ5.0A | `Diode_SMD:D_SMA` | SMAJ5.0A-TR (ST) | C98802 | Cell+ TVS: 5 V standoff clears 4.2 V; forward diode clamps negative transients |

## USB-C charging (TP4056)

| Ref | Value | Footprint | MPN | LCSC | Notes |
|-----|-------|-----------|-----|------|-------|
| J13 | USB-C | `Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12` | TYPE-C-31-M-12 (HRO) | C165948 | USB-C (power + native-USB console). Both pad rows wired (D± on A6/B6, A7/B7) so either plug orientation works |
| U11 | USBLC6-2SC6 | `Package_TO_SOT_SMD:SOT-23-6` | USBLC6-2SC6 (ST) | C7519 | VBUS + D± ESD clamp (flow-through: 1/6 and 3/4 are the same line) |
| F2 | PTC 2.5A hold | `Fuse:Fuse_1812_4532Metric` | MF-MSMF250/16X-2 (Bourns) | C210838 | 2.5 A hold / 5 A trip, 16 V; derates to ≈1.75–2 A hold at 60 °C — fine for the 1 A linear charge |
| C27 | 4.7uF | `Capacitor_SMD:C_0805_2012Metric` | — | generic | VUSB input filter after F2 |
| U12 | TP4056 | `Package_SO:SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.3mm` | TP4056-42-ESOP8 (Top Power) | C16581 | 1 A linear charger. EPAD to a GND pour with thermal vias (≈1.3 W at mid-charge; thermal regulation folds back at ≈120 °C die). Land = LCSC/JLC pattern (EP 2.40 × 3.30 mm) |
| C28 | 10uF 25V | `Capacitor_SMD:C_0805_2012Metric` | — | generic | TP4056 VCC bypass |
| C29 | 10uF 25V | `Capacitor_SMD:C_0805_2012Metric` | — | generic | TP4056 BAT bypass |
| R_PROG | 1k2 | `Resistor_SMD:R_0402_1005Metric` | — | generic | I_CH = 1200 V / R_PROG = 1 A (0.9 A on datasheet rev 2.3); 2.4 kΩ → 0.5 A if the enclosure runs hot |
| R_NTC | 5k6 | `Resistor_SMD:R_0402_1005Metric` | — | generic | TEMP divider top; with RT1 → charge window +8…+44 °C (computed) |
| RT1 | NTC 10k B3950 | `Resistor_SMD:R_0603_1608Metric` | SDNT1608X103F3950FTF (Sunlord) | C279936 | Thermally couple to the cell — USB-path charge-temperature cutoff |
| R38 | 4k7 | `Resistor_SMD:R_0402_1005Metric` | — | generic | /CHRG_USB pull-up (to TP15 only) |
| R50 | 5k1 | `Resistor_SMD:R_0402_1005Metric` | — | generic | CC1 sink 5.1 kΩ |
| R51 | 5k1 | `Resistor_SMD:R_0402_1005Metric` | — | generic | CC2 sink 5.1 kΩ |

## Solar charging (CN3791)

| Ref | Value | Footprint | MPN | LCSC | Notes |
|-----|-------|-----------|-----|------|-------|
| J12 | Solar | `Connector_Phoenix_MC:PhoenixContact_MC_1,5_2-G-3.5_1x02_P3.50mm_Horizontal` | MC 1,5/2-G-3,5 (Phoenix 1844210) | C3584780 | 2-pos pluggable header; panel ≤ 10 V Voc (6 V-nominal panel) |
| D14 | SMAJ10CA | `Diode_SMD:D_SMA` | SMAJ10CA (LGE) | C320526 | First TVS at the solar terminal (10 V bidirectional) |
| D6 | MBRS140 | `Diode_SMD:D_SMB` | MBRS140T3G (onsemi) | C133091 | Solar back-feed block |
| D8 | SMAJ10CA | `Diode_SMD:D_SMA` | SMAJ10CA (LGE) | C320526 | Second-stage TVS at CN3791 VCC |
| C17 | 10uF 35V | `Capacitor_SMD:C_1206_3216Metric` | — | generic | CN3791 VCC filter |
| C21 | 100nF | `Capacitor_SMD:C_0402_1005Metric` | — | generic | HF bypass at CN3791 VCC |
| U7 | CN3791 | `Package_SO:SSOP-10_3.9x4.9mm_P1.00mm` | CN3791 (Consonance) | C154992 | 1S MPPT buck charge **controller** (external P-FET), fixed 4.2 V CV, MPPT ref 1.205 V, 300 kHz |
| M_SOLAR | SI2319CDS | `Package_TO_SOT_SMD:SOT-23` | SI2319CDS-T1-GE3 (Vishay) | C146287 | Buck high-side P-FET (VBsemi clone C558254 is 30 V — still fine at ≤ 10 V) |
| R_DRV | 300k | `Resistor_SMD:R_0402_1005Metric` | — | generic | M_SOLAR gate–source pull-off |
| D16 | SS34 | `Diode_SMD:D_SMA` | SS34 (MDD) | C8678 | Series diode after M_SOLAR — blocks night back-feed |
| D_SOLAR | SS34 | `Diode_SMD:D_SMA` | SS34 (MDD) | C8678 | Freewheel diode (GND → SOLAR_FW) |
| L_SOLAR | 22uH | `Inductor_SMD:L_Bourns_SRN6045TA` | SRN6045TA-220M (Bourns) | C2044314 | 22 µH, Isat 3.3 A (peak ≈1.24 A). ⚠️ LCSC stock 22 on 2026-11-28 |
| R19 | 0R1 | `Resistor_SMD:R_1206_3216Metric` | — | generic | R_CS: I_CH = 120 mV / 0.1 Ω = 1.2 A (≈0.14 W) |
| C18 | 10uF | `Capacitor_SMD:C_0805_2012Metric` | — | generic | CN3791 BAT filter |
| R20 | 316k | `Resistor_SMD:R_0402_1005Metric` | — | generic | MPPT divider top → V_MP = 1.205 × (1 + 316/100) ≈ 5.0 V — recompute for the actual panel |
| R21 | 100k | `Resistor_SMD:R_0402_1005Metric` | — | generic | MPPT divider bottom |
| C_VG | 100nF | `Capacitor_SMD:C_0402_1005Metric` | — | generic | VG → VCC (not GND) |
| C_COM | 220nF | `Capacitor_SMD:C_0402_1005Metric` | — | generic | COM compensation (series with R_COM) |
| R_COM | 120R | `Resistor_SMD:R_0402_1005Metric` | — | generic | COM compensation |
| R25 | 4k7 | `Resistor_SMD:R_0402_1005Metric` | — | generic | /CHRG_SOLAR pull-up (GPIO6) |
| D7 | LED | `LED_SMD:LED_0603_1608Metric` | — | generic | Solar-charging LED (+3V3 → R22 → D7 → /CHRG_SOLAR) |
| R22 | 1k DNF **DNF** | `Resistor_SMD:R_0402_1005Metric` | — | generic | D7 series resistor — DNF by default (fit for bench debug) |

## Solar cold-charge cutoff (LM393)

| Ref | Value | Footprint | MPN | LCSC | Notes |
|-----|-------|-----------|-----|------|-------|
| U14 | LM393 | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` | LM393DR2G (onsemi) | C7955 | Solar cold-charge cutoff, powered from VSOLAR (zero draw at night) |
| RT_SOLAR | NTC 10k B3950 | `Resistor_SMD:R_0603_1608Metric` | SDNT1608X103F3950FTF (Sunlord) | C279936 | Thermally couple to the cell; trip ≈ +2 °C falling, release ≈ +4 °C |
| R_NT1 | 30k | `Resistor_SMD:R_0402_1005Metric` | — | generic | Cutoff temperature divider top (≈ NTC at +2 °C) |
| R_NT2 | 100k | `Resistor_SMD:R_0402_1005Metric` | — | generic | Reference divider (½·VSOLAR) |
| R_NT3 | 100k | `Resistor_SMD:R_0402_1005Metric` | — | generic | Reference divider (½·VSOLAR) |
| R_PU | 100k | `Resistor_SMD:R_0402_1005Metric` | — | generic | OUT1 pull-up to VSOLAR |
| R_HYS | 330k | `Resistor_SMD:R_0402_1005Metric` | — | generic | ≈2 °C hysteresis |
| C_NTC | 100nF | `Capacitor_SMD:C_0402_1005Metric` | — | generic | U14 supply bypass |
| Q7 | AO3400A | `Package_TO_SOT_SMD:SOT-23` | AO3400A (AOS) | C20917 | Clamps the CN3791 MPPT pin when cold |

## 3.3 V LDO (HT7333-A)

| Ref | Value | Footprint | MPN | LCSC | Notes |
|-----|-------|-----------|-----|------|-------|
| U1 | HT7333-A | `Package_TO_SOT_SMD:SOT-89-3` | HT7333-A (Holtek) | C21583 | 3.3 V LDO, 250 mA, ≈4 µA Iq. **SOT-89-3: GND=1, VIN=2 (tab), VOUT=3** — Wi-Fi must stay disabled (250 mA ceiling) |
| C9 | 100nF | `Capacitor_SMD:C_0402_1005Metric` | — | generic | U1 VIN bypass |
| C10 | 1uF | `Capacitor_SMD:C_0402_1005Metric` | — | generic | U1 VIN |
| C16 | 10uF | `Capacitor_SMD:C_0805_2012Metric` | — | generic | U1 VIN bulk |
| C11 | 100nF | `Capacitor_SMD:C_0402_1005Metric` | — | generic | +3V3 bypass |
| C12 | 1uF | `Capacitor_SMD:C_0402_1005Metric` | — | generic | +3V3 |
| C_BUCK | 10uF | `Capacitor_SMD:C_0805_2012Metric` | — | generic | +3V3 output cap at U1 (name kept from the buck era) |

## 16 V loop boost (MT3608B)

| Ref | Value | Footprint | MPN | LCSC | Notes |
|-----|-------|-----------|-----|------|-------|
| U8 | MT3608B | `Package_TO_SOT_SMD:SOT-23-6` | MT3608B (Aerosemi) | C19189893 | 16 V async boost, GPIO5-gated; FB 0.6 V, 4 A switch limit |
| L1 | 4.7uH | `Inductor_SMD:L_Vishay_IFSC-1515AH_4x4x1.8mm` | IFSC1515AHER4R7M01 (Vishay) | C844955 | 4.7 µH, Isat ≈2 A (≥ 1 A required: ≈0.8 A peak with both loops in current limit), DCR 90 mΩ |
| D15 | SS34 | `Diode_SMD:D_SMA` | SS34 (MDD) | C8678 | Boost rectifier SW → VLOOP |
| Q3 | AO3407A | `Package_TO_SOT_SMD:SOT-23` | AO3407A (AOS) | C15155 | VLOOP input disconnect (VBAT → L1) — stops sleep leakage into the loop terminals |
| Q4 | AO3400A | `Package_TO_SOT_SMD:SOT-23` | AO3400A (AOS) | C20917 | Q3 gate driver (VBOOST_EN) |
| R29 | 100k | `Resistor_SMD:R_0402_1005Metric` | — | generic | Q3 gate pull-up (off by default) |
| R27 | 100k | `Resistor_SMD:R_0402_1005Metric` | — | generic | VBOOST_EN pull-down (GPIO5 floats in deep sleep) |
| R23 | 1.91M | `Resistor_SMD:R_0402_1005Metric` | — | generic | FB top: VLOOP = 0.6 × (1 + 1910/75) = 15.88 V |
| R24 | 75k | `Resistor_SMD:R_0402_1005Metric` | — | generic | FB bottom (design change #21: was 100 k → 12 V) |
| C19 | 10uF | `Capacitor_SMD:C_0805_2012Metric` | — | generic | U8 VIN bypass |
| C20 | 22uF 25V | `Capacitor_SMD:C_1206_3216Metric` | — | generic | VLOOP output (25 V ≥ 1.2 × 16.7 V) |
| C22 | 10uF 25V | `Capacitor_SMD:C_0805_2012Metric` | — | generic | VLOOP output |
| C_BST | 100nF DNF **DNF** | `Capacitor_SMD:C_0402_1005Metric` | — | generic | DNF — U8 pin 6 is NC, the cap does nothing; footprint kept |
| D11 | SMAJ18A | `Diode_SMD:D_SMA` | SMAJ18A-13-F (Diodes) | C134965 | VLOOP clamp (VWM 18 V ≥ 16.7 V); also takes LOOP+ surges steered in by D17/D19 |
| SJ1 | VBOOST *(footprint only, not in BOM)* | `Jumper:SolderJumper-2_P1.3mm_Open_TrianglePad1.0x1.5mm` | — | generic | Open: bridge to tie U8 EN to VBAT for bench debug |
| SJ2 | VLOOP *(footprint only, not in BOM)* | `Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm` | — | generic | Bridged: VLOOP → VLOOP_CH2 (open to isolate channel 2 — then leave J5 LOOP+ unconnected) |

## 4–20 mA channels

| Ref | Value | Footprint | MPN | LCSC | Notes |
|-----|-------|-----------|-----|------|-------|
| J4 | 4-20mA_1 | `Connector_Phoenix_MC:PhoenixContact_MC_1,5_3-G-3.5_1x03_P3.50mm_Horizontal` | MC 1,5/3-G-3,5 (Phoenix 1844223) | C3580576 | CH1 loop: LOOP+ / SIG / GND |
| J5 | 4-20mA_2 | `Connector_Phoenix_MC:PhoenixContact_MC_1,5_3-G-3.5_1x03_P3.50mm_Horizontal` | MC 1,5/3-G-3,5 (Phoenix 1844223) | C3580576 | CH2 loop (not read by firmware yet) |
| D9 | SMAJ5.0A | `Diode_SMD:D_SMA` | SMAJ5.0A-TR (ST) | C98802 | CH1 SIG clamp |
| D10 | SMAJ5.0A | `Diode_SMD:D_SMA` | SMAJ5.0A-TR (ST) | C98802 | CH2 SIG clamp |
| GDT1 | GDT 90V DNF **DNF** | `WellD:GDT_Littelfuse_GTCS23` | GTCS23-900M-R01-2 (Littelfuse) | C3659812 | DNF — fit only for long/buried/aerial cable runs. ⚠️ LCSC stock 0 |
| GDT2 | GDT 90V DNF **DNF** | `WellD:GDT_Littelfuse_GTCS23` | GTCS23-900M-R01-2 (Littelfuse) | C3659812 | DNF — as GDT1 |
| R2 | 100R 0.1% | `Resistor_SMD:R_0805_2012Metric` | RT0805BRD07100RL (Yageo) | C110773 | CH1 shunt, 0.1 %, 25 ppm/°C, 125 mW (0.12 W in a limited short, 10–15 ms per wake) |
| R4 | 100R 0.1% | `Resistor_SMD:R_0805_2012Metric` | RT0805BRD07100RL (Yageo) | C110773 | CH2 shunt (as R2) |
| C34 | 10nF | `Capacitor_SMD:C_0402_1005Metric` | — | generic | HF bypass across R2 |
| C35 | 10nF | `Capacitor_SMD:C_0402_1005Metric` | — | generic | HF bypass across R4 |
| R3 | 1k | `Resistor_SMD:R_0402_1005Metric` | — | generic | CH1 series limiter (≈3.5 mA into D1 on a fault) |
| R5 | 1k | `Resistor_SMD:R_0402_1005Metric` | — | generic | CH2 series limiter |
| C3 | 100nF | `Capacitor_SMD:C_0402_1005Metric` | — | generic | AIN0 filter: τ = (R2 + R3)·C3 ≈ 110 µs |
| C5 | 100nF | `Capacitor_SMD:C_0402_1005Metric` | — | generic | AIN1 filter |
| C4 | 10uF DNF **DNF** | `Capacitor_SMD:C_0805_2012Metric` | — | generic | DNF — would make τ ≈ 11 ms (level reads 10–40 % low at the 10 ms warm-up) |
| C6 | 10uF DNF **DNF** | `Capacitor_SMD:C_0805_2012Metric` | — | generic | DNF — as C4 |
| D1 | PRTR5V0U2X | `Package_TO_SOT_SMD:SOT-143` | PRTR5V0U2X,215 (Nexperia) | C12333 | ADS1115 AIN0/AIN1 rail clamp |

## Loop current limiters (design change #21)

| Ref | Value | Footprint | MPN | LCSC | Notes |
|-----|-------|-----------|-----|------|-------|
| R52 | 22R | `Resistor_SMD:R_0603_1608Metric` | — | generic | CH1 limiter sense (≈20 mW at the limit) |
| R54 | 22R | `Resistor_SMD:R_0603_1608Metric` | — | generic | CH2 limiter sense |
| Q8 | BCP53-16 | `Package_TO_SOT_SMD:SOT-223-3_TabPin2` | BCP53-16,115 (Nexperia) | C85085 | CH1 pass transistor: ≤ ≈0.56 W into a dead short — ≥ 1 cm² collector copper. Never substitute an SOT-89 BCX53 |
| Q10 | BCP53-16 | `Package_TO_SOT_SMD:SOT-223-3_TabPin2` | BCP53-16,115 (Nexperia) | C85085 | CH2 pass (as Q8) |
| Q9 | MMBT3906 | `Package_TO_SOT_SMD:SOT-23` | MMBT3906LT1G (onsemi) | C53444 | CH1 clamp (E on VLOOP, B on the sense node) |
| Q11 | MMBT3906 | `Package_TO_SOT_SMD:SOT-23` | MMBT3906LT1G (onsemi) | C53444 | CH2 clamp |
| R53 | 15k | `Resistor_SMD:R_0402_1005Metric` | — | generic | CH1 pass base drive (≈1 mA) |
| R55 | 15k | `Resistor_SMD:R_0402_1005Metric` | — | generic | CH2 pass base drive |
| D17 | SS34 | `Diode_SMD:D_SMA` | SS34 (MDD) | C8678 | CH1 LOOP+ surge steering → VLOOP/D11 |
| D19 | SS34 | `Diode_SMD:D_SMA` | SS34 (MDD) | C8678 | CH2 LOOP+ surge steering → VLOOP_CH2 (after SJ2) |
| D18 | SMAJ18A | `Diode_SMD:D_SMA` | SMAJ18A-13-F (Diodes) | C134965 | CH1 LOOP+ terminal clamp (cathode LOOP+) |
| D20 | SMAJ18A | `Diode_SMD:D_SMA` | SMAJ18A-13-F (Diodes) | C134965 | CH2 LOOP+ terminal clamp |

## Battery divider

| Ref | Value | Footprint | MPN | LCSC | Notes |
|-----|-------|-----------|-----|------|-------|
| Q5 | AO3407A | `Package_TO_SOT_SMD:SOT-23` | AO3407A (AOS) | C15155 | High-side divider switch (dead divider in sleep) |
| R16 | 100k | `Resistor_SMD:R_0402_1005Metric` | — | generic | Q5 gate pull-up |
| Q2 | AO3400A | `Package_TO_SOT_SMD:SOT-23` | AO3400A (AOS) | C20917 | Q5 gate driver (GPIO15) |
| R26 | 4k7 | `Resistor_SMD:R_0402_1005Metric` | — | generic | Q2 gate pull-down |
| R7 | 100k | `Resistor_SMD:R_0402_1005Metric` | — | generic | Divider top (÷2: 4.2 V → 2.1 V on AIN2, read on the ±4.096 V range) |
| R8 | 100k | `Resistor_SMD:R_0402_1005Metric` | — | generic | Divider bottom |
| C8 | 1nF | `Capacitor_SMD:C_0402_1005Metric` | — | generic | Across R8 — settles in < 1 ms |

## ADC (ADS1115)

| Ref | Value | Footprint | MPN | LCSC | Notes |
|-----|-------|-----------|-----|------|-------|
| U9 | ADS1115 | `Package_SO:MSOP-10_3x3mm_P0.5mm` | ADS1115IDGSR (TI) | C37593 | 16-bit I²C ADC, address 0x48 (ADDR → GND) |
| FB1 | 600R@100MHz | `Inductor_SMD:L_0603_1608Metric` | BLM18KG601SN1D (Murata) | C85833 | Ferrite in the +3V3 feed to U9 VDD (0603) |
| C23 | 100nF | `Capacitor_SMD:C_0402_1005Metric` | — | generic | U9 VDD bypass (U9 side of FB1) |
| C24 | 1uF | `Capacitor_SMD:C_0402_1005Metric` | — | generic | U9 VDD |
| R9 | 4k7 | `Resistor_SMD:R_0402_1005Metric` | — | generic | SDA pull-up (GPIO18) |
| R10 | 4k7 | `Resistor_SMD:R_0402_1005Metric` | — | generic | SCL pull-up (GPIO19) |
| R_DRDY | 4.7k | `Resistor_SMD:R_0402_1005Metric` | — | generic | ALERT/RDY open-drain pull-up (GPIO22) |

## MCU (ESP32-C6-MINI-1U)

| Ref | Value | Footprint | MPN | LCSC | Notes |
|-----|-------|-----------|-----|------|-------|
| U6 | ESP32-C6-MINI-1U-H4 | `WellD:ESP32-C6-MINI-1U` | ESP32-C6-MINI-1U-H4 (Espressif) | C20627095 | U.FL antenna port, no on-board antenna. Footprint vendored from Espressif kicad-libraries |
| C13 | 100nF | `Capacitor_SMD:C_0402_1005Metric` | — | generic | Module decoupling |
| C30 | 100nF | `Capacitor_SMD:C_0402_1005Metric` | — | generic | Module decoupling |
| C31 | 100nF | `Capacitor_SMD:C_0402_1005Metric` | — | generic | Module decoupling |
| C32 | 100nF | `Capacitor_SMD:C_0402_1005Metric` | — | generic | Module decoupling |
| C33 | 100nF | `Capacitor_SMD:C_0402_1005Metric` | — | generic | Module decoupling |
| C15 | 10uF | `Capacitor_SMD:C_0805_2012Metric` | — | generic | Module bulk |
| R15 | 10k | `Resistor_SMD:R_0402_1005Metric` | — | generic | EN pull-up |
| C36 | 1uF | `Capacitor_SMD:C_0402_1005Metric` | — | generic | EN power-on delay (≈10 ms with R15) |
| R12 | 10k | `Resistor_SMD:R_0402_1005Metric` | — | generic | GPIO9 / BOOT strap pull-up |
| R13 | 10k | `Resistor_SMD:R_0402_1005Metric` | — | generic | GPIO8 strap pull-up |
| SW1 | RESET | `Button_Switch_SMD:SW_Push_1P1T_NO_CK_KSC6xxJ` | KSC641JLFS (C&K) | C226344 | Reset (EN → GND), 6.2 mm IP67, J-lead |
| SW2 | BOOT | `Button_Switch_SMD:SW_Push_1P1T_NO_CK_KSC6xxJ` | KSC641JLFS (C&K) | C226344 | Boot (GPIO9 → GND) |
| D4 | Green | `LED_SMD:LED_0603_1608Metric` | — | generic | Status LED (GPIO14 → R14 → D4 → SJ3 → GND) — no firmware support yet |
| R14 | 1k | `Resistor_SMD:R_0402_1005Metric` | — | generic | LED current limit |
| SJ3 | LED_DIS *(footprint only, not in BOM)* | `Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm` | — | generic | Bridged: open to disconnect the LED |

## DS18B20 1-Wire

| Ref | Value | Footprint | MPN | LCSC | Notes |
|-----|-------|-----------|-----|------|-------|
| J6 | DS18B20 | `Connector_Phoenix_MC:PhoenixContact_MC_1,5_3-G-3.5_1x03_P3.50mm_Horizontal` | MC 1,5/3-G-3,5 (Phoenix 1844223) | C3580576 | DS18B20: VCC / DATA / GND |
| D12 | PRTR5V0U2X | `Package_TO_SOT_SMD:SOT-143` | PRTR5V0U2X,215 (Nexperia) | C12333 | 1-Wire DATA clamp (I/O2 unused) |
| R6 | 4k7 | `Resistor_SMD:R_0402_1005Metric` | — | generic | 1-Wire pull-up |
| R28 | 100R | `Resistor_SMD:R_0402_1005Metric` | — | generic | J6 VCC series |
| R32 | 33R | `Resistor_SMD:R_0402_1005Metric` | — | generic | GPIO7 series protection — populate |
| C7 | 100nF | `Capacitor_SMD:C_0402_1005Metric` | — | generic | J6 VCC bypass |

## Expansion, programming and RF

| Ref | Value | Footprint | MPN | LCSC | Notes |
|-----|-------|-----------|-----|------|-------|
| J7 | Spare | `Connector_Phoenix_MC:PhoenixContact_MC_1,5_3-G-3.5_1x03_P3.50mm_Horizontal` | MC 1,5/3-G-3,5 (Phoenix 1844223) | C3580576 | Spare: +3V3 / GPIO3 / GND |
| J8 | I2C **DNF** | `Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical` | — | generic | DNF I²C header |
| J9 | GPIO **DNF** | `Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical` | — | generic | DNF GPIO header |
| J10 | PROG | `Connector_PinHeader_1.27mm:PinHeader_1x06_P1.27mm_Vertical` | 1×6 1.27 mm header | C22438103 | TX / RX / GND / 3V3 / GPIO9 / EN |
| SJ4 | UART_TX *(footprint only, not in BOM)* | `Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm` | — | generic | Bridged: UART_TX to J10 |
| SJ5 | UART_RX *(footprint only, not in BOM)* | `Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm` | — | generic | Bridged: UART_RX to J10 |
| J3 | 132289 | `Connector_Coaxial:SMA_Amphenol_132289_EdgeMount` | 132289 (Amphenol) | generic | SMA edge-launch. ⚠️ RF path is an open decision (README decision 1); LCSC stock 0 |

## Test points

TP1–TP15: `TestPoint:TestPoint_Pad_1.0x1.0mm`, bare pads — **footprint only, excluded from the BOM and placement files**. Nets: TP1 VBAT · TP2 VLOOP · TP3 +3V3 · TP4 GND · TP5 LOOP_TERM_CH1 (CH1 shunt top) · TP6 LOOP_TERM_CH2 · TP7 1WIRE · TP8 I2C_SDA · TP9 I2C_SCL · TP10 VSOLAR_IN · TP11 VBAT_RAW · TP12 ADS_DRDY · TP13 FACTORY_RESET (keep reachable with the lid off) · TP14 /CHRG_SOLAR · TP15 /CHRG_USB.

## Sourcing risks found on 2026-11-28

| Part | Issue | Options |
|------|-------|---------|
| Q6 FS8205A (TSSOP-8) | LCSC stock 0 (C14212 and C16052) | Order early / global sourcing, or redraw for an in-stock 8205A in TSSOP-8 from another vendor (check its pinout) |
| J4–J7 Phoenix 1844223 | LCSC stock 5 (C3580576); four needed per board | PCBWay global sourcing, Digi-Key/Mouser, or an MC 1,5 G-compatible 3.5 mm pluggable header with the same land pattern |
| L_SOLAR SRN6045TA-220M | LCSC stock 22 (C2044314) | Any 22 µH 6 × 6 mm shielded inductor with Isat ≥ 2 A on the same land |
| J3 Amphenol 132289 | LCSC stock 0 | Depends on the RF decision |
| GDT1/GDT2 | LCSC stock 0 (C3659812) | DNF by default — only needed for site-specific fitting |
| BT1 Keystone 1042 | Not on LCSC | Customer-supplied to the assembler, or hand-fitted |

Parts removed over the design's history (IP2326, CN3722 buck stage, AP63203WU, XT30 pack connector, …) are listed in `history/design_history.md` and the CHANGELOG.
