# WellD Schematic — Net Connectivity Reference

The schematic files contain component symbol placements but **no wire connections**. This document is the authoritative wiring reference. Use it alongside the schematic editor to draw all nets manually (see `kicad_guide_eli5.md`).

**Convention:** connections below are given by **pin name** (as printed on the symbol), not pin number. Several custom symbols have unverified pin *numbers* — see [Symbol pin-number verification](#symbol-pin-number-verification) before assigning footprints.

---

## Design changes — 2026-07-05 electrical review

| # | Change | Reason |
|---|--------|--------|
| 1 | **U1 changed AP63205WU → AP63203WU** (fixed 3.3 V); R_FBH/R_FBL marked **DNP** | AP63205 is the **5 V fixed** variant of the Diodes AP6320x family; AP63203 is the 3.3 V fixed variant. The previously specified divider math (0.6 V ref) matches no part in this family (adjustable AP63200 uses a 0.8 V reference). Any of the previous combinations would have put 4.4–8 V on the 3V3 rail and destroyed the ESP32. **Verify against the Diodes datasheet before ordering** (see verification blockers). |
| 2 | **MT3608B topology corrected** (boost: VBAT→L1→SW, not SW→L1→VOUT) and **D15 rectifier + Q3/Q4 load-disconnect added** | The MT3608 family is an async boost: the inductor goes from VIN to SW and an external Schottky (D15) carries SW→VLOOP. Without a disconnect switch, VBAT−0.4 V leaks through L1+D15 to the loop terminals permanently, powering the transmitter during deep sleep and killing the battery. |
| 3 | **Status LED moved GPIO13 → GPIO14** (net renamed `GPIO14_LED`) | Firmware uses GPIO13 as the factory-reset strap (hold LOW at boot → NVS erase). A green LED + 1 kΩ to GND holds the pin below V_IH at boot → factory reset on **every** boot. GPIO14 was spare. TP13 added as the factory-reset pad. |
| 4 | **Battery divider switched to high-side disconnect** (Q5 P-FET added, Q2 becomes its gate driver); **C8 100 nF → 1 nF** | With the old low-side Q2, the mid node was pulled to VBAT through R7 when disabled, biasing ADS1115 AIN2 above VDD via its ESD diode (~14 µA continuous sleep drain — defeating the purpose of the switch). C8 at 100 nF gave τ ≈ 7.7 ms, far too slow for the firmware's ≥1 ms enable window; 1 nF settles in <1 ms. |
| 5 | **R25 pull-up added on /CHRG_SOLAR** | Gate rule: open-drain outputs need external pull-ups; GPIO6 previously relied on the ESP32 internal ~45 kΩ pull-up only. |
| 6 | **R27 pull-down added on VBOOST_EN** | GPIO5 is isolated (floats) in deep sleep; a floating MT3608B EN (and Q4 gate) could randomly enable the 12 V boost while asleep. |
| 7 | **R15 + C36 added on ESP32 EN** | ESP32-C6-MINI-1U requires an external RC on EN (10 kΩ to 3V3, 1 µF to GND) for a clean power-on reset; only SW1 was present. |
| 8 | **D8/D14 changed SMAJ28CA → SMAJ24CA; C17 uprated to 35 V** | SMAJ28CA standoff equals the CN3722 28 V abs max — zero clamp margin (senior review warning #5). Consequence: max permitted panel Voc is now **24 V** (12 V-nominal panels, Voc ≈ 21–22 V, still fine). C17 at 25 V had no margin over a 24 V standoff rail. |
| 9 | **C25 deleted from power.kicad_sch** (duplicate of C_BST); **C16 assigned as U1 VIN bulk 10 µF** | Resolves senior review warnings #8 and #9; the AP6320x datasheet input cap is 10 µF, previously only 100 nF + 1 µF were fitted. |
| 10 | Refdes reconciliation: `R_CC1/R_CC2` → **R50/R51**, `C14a–C14d` → **C13, C30–C33**, `C_SH1/C_SH2` → **C34/C35**; **R38 is the TP5100 /CHRG pull-up** (the solar /CHRG pull-up is new R25); TP1=VBAT, TP3=+3V3, TP4=GND | Docs referred to symbols that do not exist in the schematics under those names. |
| 11 | **TP5100 USB charge path flagged NON-FUNCTIONAL as designed** | TP5100 is a switching **step-down** (buck) 2S/1S charger. It cannot charge an 8.4 V pack from 5 V USB — VIN must exceed the pack voltage. Superseded by change #12. |
| 12 | **U12 replaced TP5100 → Injoinic IP2326** (5 V→2S synchronous **boost** charger, ESOP-8); **L3 boost inductor added**; R35 repurposed as ISET (value TBD); **R36/R37 deleted — GPIO4/USB_CE freed**; R38 reassigned to the IP2326 status pin; NTC strap placeholder added; **F2 uprated 1.1 A → 2 A hold** (boost input ≈1.9 A at 1 A charge) | Component-selection review 2026-07-05 (`component_selection_review.md` §1). Resolves change #11. IP2326 auto-runs on VBUS — no charge-enable GPIO (⚠️ verify EN absence, plus full pinout/CV/ISET/mid-cell-balance behaviour: blocker #2). Firmware must be told GPIO4 is no longer USB_CE. |

---

## Net Inventory

| Net name | Voltage | Description |
|----------|---------|-------------|
| GND | 0V | Ground plane |
| +3V3 | 3.3V | Main logic rail (U1 buck output) |
| VBAT | 6.0–8.4V | 2S Li-ion battery (raw, after D5 load-switch) |
| VBAT_RAW | 6.0–8.4V | Battery positive before D5 (J1 BAT+, D13, D5 drain) |
| VUSB | 5V | USB-C VBUS after F2 polyfuse |
| VUSB_IN | 5V | USB-C VBUS raw (J13 VBUS pins, before F2) |
| VSOLAR | ≤24V (Voc) | Solar input after D6 diode = CN3722 VIN node |
| VSOLAR_IN | ≤24V (Voc) | Solar panel raw (J12 terminal, before D6) |
| VLOOP | 12V ±5% | Boost output (MT3608B + D15), loop power |
| VLOOP_SW | switching | MT3608B SW node (L1 / D15 anode / C_BST) |
| VLOOP_L | 6.0–8.4V gated | Q3 drain → L1 input (boost disconnect branch) |
| +3V3_ADS | 3.3V filtered | ADS1115 VDD (after FB1 ferrite bead) |
| AP_FB | 3.3V (sense) | U1 FB/VOUT sense pin tie to +3V3 (fixed-output part) |
| MT_FB | 0.6V | MT3608B feedback divider mid-point (R23/R24) |
| MPPT_REF | 1.205V | CN3722 MPPT pin divider mid-point (R20/R21) |
| CN_FB | 1.205V | CN3722 CV feedback divider mid-point (R33/R34) |
| ADS_DRDY | signal | ADS1115 ALERT/RDY open-drain → GPIO12 (R_DRDY pull-up) |
| I2C_SDA | signal | I²C SDA → GPIO10 (R9 pull-up) |
| I2C_SCL | signal | I²C SCL → GPIO11 (R10 pull-up) |
| ADC_CH0 | 0–2.0V | ADS1115 AIN0 (CH1 4-20mA after protection chain) |
| ADC_CH1 | 0–2.0V | ADS1115 AIN1 (CH2 4-20mA after protection chain) |
| ADC_CH2 | 0–1.95V | ADS1115 AIN2 (battery divider mid-point) |
| VBAT_SW | 6.0–8.4V gated | Q5 drain → R7 top (battery divider, gated) |
| Q3_GATE / Q5_GATE | analog | P-FET gate nodes (level-shifted from GPIO5 / GPIO15) |
| 1WIRE | signal | DS18B20 data → GPIO7 (R6 pull-up) |
| LOOP_TERM_CH1/2 | signal | 4-20mA SIG inputs from J4/J5 |
| SHUNT_IN_1/2, SHUNT_OUT_1/2 | analog | Shunt chain intermediate nets (see ADC_CH0/1) |
| /CHRG_SOLAR | signal | CN3722 /CHRG (open-drain, active-low) → GPIO6, R25 pull-up |
| /CHRG_USB | signal | IP2326 charge-status pin (⚠️ verify pin/polarity) → R38 pull-up → TP15 only |
| ~~USB_CE~~ | — | **DELETED 2026-07-05** — IP2326 auto-charges on VBUS; R36/R37 removed, GPIO4 freed (spare — coordinate with firmware) |
| USBCHG_SW | switching | IP2326 boost switch node (VUSB → L3 → SW, internal sync FETs) — ⚠️ pin per datasheet |
| BATT_DIV_EN | signal | GPIO15 → Q2 gate (HIGH enables battery divider via Q5) |
| VBOOST_EN | signal | GPIO5 → MT3608B EN + Q4 gate (HIGH = 12V loop on); R27 pull-down |
| GPIO14_LED | signal | Status LED (GPIO14 → R14 → D4 → SJ3 → GND) |
| FACTORY_RESET | signal | GPIO13 → TP13 pad (hold LOW at boot = NVS erase) |
| UART_TX / UART_RX | signal | Debug UART GPIO16/GPIO17 → SJ4/SJ5 → J10 |
| EN | signal | ESP32-C6 EN (R15 pull-up, C36, SW1, J10) |
| BOOT | signal | ESP32-C6 GPIO9 (R12 pull-up, SW2, J10) |

---

## Net-by-Net Pin Connections

### GND

| Component | Pin | Note |
|-----------|-----|------|
| U1 AP63203WU | GND | Buck GND |
| U7 CN3722 | GND | Solar charger GND |
| U8 MT3608B | GND | Boost GND |
| U9 ADS1115 | GND **and ADDR** | ADDR→GND sets I²C address 0x48 |
| U6 ESP32-C6-MINI-1U | GND (all) | Module GND + thermal pad |
| U11 USBLC6-2SC6 | GND | USB ESD clamp |
| U12 IP2326 | GND (+ exposed pad) | |
| D1, D12 PRTR5V0U2X | GND | Rail clamps |
| R_FBL | pin 2 | **DNP** (only fitted with adjustable AP63200 option) |
| R24 | pin 2 | MT3608B FB divider low side |
| R21 | pin 2 | MPPT divider low side |
| R34 | pin 2 | CN3722 CV divider low side |
| R35 | pin 2 | IP2326 ISET resistor (value TBD ⚠️) |
| R26 | pin 2 | Q2 gate pull-down |
| R27 | pin 2 | VBOOST_EN pull-down |
| R31 | pin 2 | D5 gate pull-down (turns load switch ON) |
| R8 | pin 2 | Battery divider low side (direct to GND — Q2 no longer in this leg) |
| R50, R51 | pin 2 | USB-C CC pull-downs |
| C8 | pin 2 | 1 nF across R8 |
| C9, C10, C16 | pin 2 | U1 VIN decoupling |
| C11, C12, C_BUCK | pin 2 | +3V3 output decoupling |
| C17, C21 | pin 2 | CN3722 VIN filters |
| C18 | pin 2 | CN3722 VBAT cap |
| C19 | pin 2 | MT3608B VIN bypass |
| C20, C22 | pin 2 | VLOOP output caps |
| C23, C24 | pin 2 | ADS1115 VDD decoupling (+3V3_ADS side) |
| C13, C30–C33 | pin 2 | ESP32-C6 VCC3V3 decoupling (5 × 100 nF) |
| C15 | pin 2 | ESP32-C6 bulk |
| C36 | pin 2 | ESP32 EN reset-delay cap |
| C27, C28 | pin 2 | VUSB filters |
| C29 | pin 2 | IP2326 BAT-side bypass |
| C3–C6, C34, C35 | pin 2 | 4-20mA filter/bypass caps |
| C7 | pin 2 | J6 VCC bypass |
| R2, R4 | pin 2 (shunt low side) | 4-20mA shunt return |
| D9, D10, D11, D13, D14, D8 | one terminal | TVS clamps (bidirectional except D11 = unidirectional, cathode to VLOOP) |
| Q2 | S | BSS123 source |
| SW1 | pin 2 | Reset to GND |
| SW2 | pin 2 | Boot to GND |
| D4 | cathode via SJ3 | Status LED return |
| J1 | BAT− | Battery return |
| J4, J5 | pin 3 | Loop GND return |
| J6 | pin 3 | DS18B20 GND |
| J7 | pin 3 | Spare GND |
| J8 | GND pin | I²C header |
| J9 | GND pin | GPIO header |
| J10 | GND pin | Programming header |
| J12 | SOLAR− | Solar return |
| J13 | GND (A1/B1 etc.) | USB-C shield/GND |
| J3 | ground ring | SMA GND |
| TP4 | pad | GND test point |

### +3V3

| Component | Pin | Note |
|-----------|-----|------|
| U1 AP63203WU | FB/VOUT sense pin | **Fixed-output part: tie the FB pin directly to the +3V3 output rail** (no divider). If the adjustable AP63200WU option is chosen instead, wire +3V3→R_FBH→FB and FB→R_FBL→GND with R_FBH=390k / R_FBL=124k (VFB=0.8 V → 3.32 V) and fit both resistors. |
| L2 | pin 2 | Buck output inductor (SW→L2→+3V3) |
| C_BUCK, C11, C12 | pin 1 | Output caps at L2 |
| FB1 | pin 1 | Ferrite feed to +3V3_ADS |
| R9, R10 | pin 1 | I²C pull-ups |
| R_DRDY | pin 1 | ADS_DRDY pull-up |
| R25 | pin 1 | /CHRG_SOLAR pull-up |
| R38 | pin 1 | /CHRG_USB pull-up (to TP15) |
| R6 | pin 1 | 1-Wire pull-up |
| R28 | pin 1 | Feed to J6 VCC (100 Ω series) |
| R12, R13 | pin 1 | BOOT / GPIO8 strapping pull-ups |
| R15 | pin 1 | ESP32 EN pull-up |
| R22 | pin 1 | Solar-charge LED feed (DNF) |
| U6 ESP32-C6-MINI-1U | 3V3 (all) | Module supply |
| C13, C30–C33, C15 | pin 1 | Module decoupling/bulk |
| J7 | pin 1 | Spare sensor supply |
| J8, J9, J10 | 3V3 pin | Headers |
| D1 PRTR5V0U2X | VCC | ADC clamp rail |
| D12 PRTR5V0U2X | VCC | 1-Wire clamp rail |
| TP3 | pad | +3V3 test point |

> **CE network removed (2026-07-05):** R36/R37 belonged to the TP5100 CE pin. The IP2326 replacement auto-charges whenever VBUS is present (⚠️ verify no EN pin exists — blocker #2). **GPIO4 is freed**; firmware's USB_CHG drive becomes a no-op (harmless against an unconnected pad) until firmware is updated.

### +3V3_ADS

| Component | Pin | Note |
|-----------|-----|------|
| FB1 | pin 2 | Ferrite output |
| U9 ADS1115 | VDD | |
| C23 (100nF), C24 (1µF) | pin 1 | On U9 side of FB1, within 1 mm of VDD |

### VBAT

| Component | Pin | Note |
|-----------|-----|------|
| D5 AO3407 | S (source) | Load-switch output |
| U1 | VIN | Buck input |
| U7 CN3722 | VBAT (both pins if present) | Charger output |
| U8 MT3608B | IN | Boost controller supply (stays connected; <1 µA when EN low) |
| Q3 AO3407 | S (source) | Boost inductor disconnect switch input |
| Q5 AO3407 | S (source) | Battery divider disconnect switch input |
| R29 | pin 1 | Q3 gate pull-up |
| R16 | pin 1 | Q5 gate pull-up |
| R11 | pin 1 | U1 EN pull-up (always-on buck); pin 2 → U1 EN |
| R33 | pin 1 | CN3722 CV divider high side |
| C9, C10, C16 | pin 1 | U1 VIN decoupling (100n / 1µ / 10µ) |
| C18 | pin 1 | CN3722 VBAT cap |
| C19 | pin 1 | MT3608B VIN bypass |
| U12 IP2326 | BAT/VOUT (⚠️ pin per datasheet) | Boost charger output; C29 pin 1 here. ⚠️ Verify BAT-pin quiescent < 10 µA with USB absent |
| TP1 | pad | VBAT test point (after D5) |
| J9 | VBAT pin (optional) | — only if the header carries VBAT; otherwise omit |

### VBAT_RAW

| Component | Pin | Note |
|-----------|-----|------|
| J1 XT30 | BAT+ (pin 1) | Battery positive input |
| D13 SMAJ10CA | terminal 1 | Battery TVS (other terminal GND) |
| D5 AO3407 | D (drain) | Load-switch input (body diode conducts drain→source at first connect, then channel enhances: gate held at GND by R31, Vgs = −VBAT) |
| D5 AO3407 | G (gate) | → R31 pin 1 (R31 pin 2 → GND) |
| TP11 | pad | Before D5 |

### VLOOP (12 V boost — corrected topology)

Current path: `VBAT → Q3 (P-FET switch) → L1 → SW node → D15 (Schottky) → VLOOP`

| Component | Pin | Net segment | Note |
|-----------|-----|-------------|------|
| Q3 AO3407 | S | VBAT | Disconnect switch |
| Q3 AO3407 | D | VLOOP_L | To inductor |
| Q3 AO3407 | G | Q3_GATE | R29 (100k) to VBAT; Q4 drain pulls low to turn on |
| Q4 BSS123 | D | Q3_GATE | Level shifter |
| Q4 BSS123 | G | VBOOST_EN | With R27 pull-down |
| Q4 BSS123 | S | GND | |
| L1 | pin 1 | VLOOP_L | Inductor input |
| L1 | pin 2 | VLOOP_SW | Switch node |
| U8 MT3608B | SW | VLOOP_SW | Internal low-side switch |
| C_BST | pin 1 / pin 2 | BST ↔ VLOOP_SW | 100 nF; **verify BST pin exists** — classic MT3608 pin 6 is NC (harmless if fitted to an NC pin) |
| D15 SS34 | anode | VLOOP_SW | Boost rectifier |
| D15 SS34 | cathode | VLOOP | |
| C20 (22µF 25V), C22 (10µF 25V) | pin 1 | VLOOP | Output filter |
| R23 (1.91M) | pin 1 | VLOOP | FB divider high side; pin 2 → MT_FB |
| R24 (100k) | pin 1 | MT_FB | pin 2 → GND. VOUT = 0.6 × (1 + 1910/100) = 12.06 V |
| U8 MT3608B | FB | MT_FB | |
| D11 SMAJ13A | cathode | VLOOP | Unidirectional TVS, anode → GND |
| J4 | LOOP+ (pin 1) | VLOOP | CH1 loop power |
| SJ2 | A/B | VLOOP ↔ J5 LOOP+ | Bridged by default; open to isolate CH2 |
| J5 | LOOP+ (pin 1) | via SJ2 | CH2 loop power |
| TP2 | pad | VLOOP | Test point |

### VBOOST_EN

| Component | Pin | Note |
|-----------|-----|------|
| U6 ESP32-C6 | GPIO5 | Drives HIGH ≥5 ms before a loop read (recommend 10 ms now that C20/C22 charge through Q3) |
| U8 MT3608B | EN | HIGH = boost active |
| Q4 BSS123 | G | Enables Q3 simultaneously |
| R27 (100k) | pin 1 | Pull-down to GND — holds boost + Q3 off while GPIO5 is isolated in deep sleep |
| SJ1 | A/B | Open by default; bridging ties EN permanently to VBAT for bench debug (jumper from EN to VBAT side) |

### VSOLAR / VSOLAR_IN

| Component | Pin | Note |
|-----------|-----|------|
| J12 | SOLAR+ | Panel input (max Voc **24 V** with SMAJ24CA) |
| D14 SMAJ24CA | terminal 1 | First TVS at terminal (other terminal GND) |
| D6 MBRS140 | anode | VSOLAR_IN — backfeed block |
| D6 MBRS140 | cathode | VSOLAR (CN3722 VIN node) |
| D8 SMAJ24CA | terminal 1 | Second-stage TVS at CN3722 VIN (other terminal GND) |
| U7 CN3722 | VIN (both pins if present) | |
| C17 (10µF **35V**), C21 (100nF 50V) | pin 1 | VIN filters |
| R20 | pin 1 | MPPT divider high side (senses CN3722 VIN) |
| TP10 | pad | VSOLAR_IN test point at J12 |

### MPPT_REF

| Component | Pin | Note |
|-----------|-----|------|
| U7 CN3722 | MPPT | Regulates panel to VMPPT when divider mid = 1.205 V |
| R20 (36k) | pin 2 | High side from VSOLAR; V_MPPT = 1.205 × (36+10)/10 ≈ 5.54 V |
| R21 (10k) | pin 1 | Low side to GND |

### CN3722 CV feedback (CN_FB)

| Component | Pin | Note |
|-----------|-----|------|
| U7 CN3722 | FB (CV sense) | Regulates VBAT so that mid = 1.205 V |
| R33 (590k) | pin 2 | High side from VBAT → Vchg = 1.205 × (1 + 590/100) = **8.31 V** ✓ (≤8.40 V for 2S) |
| R34 (100k) | pin 1 | Low side to GND |

> **R19 (2.0 kΩ)** sets the 500 mA charge current per the original design ("CN3722 PROG pin"). The current 8-pin symbol has a `VPROG` pin — wire R19 from VPROG to GND. **Verify against the CN3722 datasheet**: Consonance chargers in this family normally set current with a CSP/CSN sense resistor, and the package is likely SSOP-10, not SOP-8. Blocking item — see verification blockers.

### /CHRG_SOLAR

| Component | Pin | Note |
|-----------|-----|------|
| U7 CN3722 | /CHRG | Open-drain, LOW = charging |
| R25 (4.7k) | pin 2 | Pull-up to +3V3 (**new** — was internal-pull-up only) |
| U6 ESP32-C6 | GPIO6 | Input; firmware reads LOW = charging |
| D7 LED | cathode | Solar-charge indicator (green): +3V3 → R22 (1k, **DNF**) → D7 anode; D7 cathode → /CHRG_SOLAR. Lights while charging. DNF by default to save power. |
| TP14 | pad | CHRG_SOL test point |

### VUSB / VUSB_IN / USB-C

| Component | Pin | Note |
|-----------|-----|------|
| J13 USB-C | VBUS (A4/B4/A9/B9) | VUSB_IN |
| U11 USBLC6-2SC6 | VBUS | ESD clamp on VUSB_IN |
| U11 | IO1/IO2 pairs | To J13 D+/D− stubs (power-only port; D± go nowhere else) |
| F2 polyfuse (2A hold) | pin 1 / pin 2 | VUSB_IN → VUSB (uprated — boost input ≈1.9 A at 1 A charge) |
| C27 (4.7µF) | pin 1 | VUSB after F2 |
| U12 IP2326 | VIN (⚠️ pin per datasheet) | VUSB; C28 (10µF) pin 1 at pin |
| L3 | pin 1 / pin 2 | VUSB → USBCHG_SW (⚠️ topology/pin per IP2326 datasheet — internal sync FETs, no external rectifier) |
| J13 | CC1 → R50 (5.1k) → GND; CC2 → R51 (5.1k) → GND | Sink advertising 5 V |

### ~~USB_CE~~ — deleted 2026-07-05

R36/R37 removed with the TP5100. IP2326 auto-runs on VBUS presence (⚠️ verify no EN/CE pin — blocker #2). **GPIO4 is spare**; coordinate with the firmware agent before re-tasking it.

### /CHRG_USB

| Component | Pin | Note |
|-----------|-----|------|
| U12 IP2326 | charge-status pin (⚠️ verify name, polarity, open-drain vs push-pull LED driver) | |
| R38 (4.7k) | pin 2 | Pull-up to +3V3 (fit only if the status pin is open-drain) |
| TP15 | pad | Hardware-only test point (no GPIO) |

### IP2326 ISET / NTC

| Component | Pin | Note |
|-----------|-----|------|
| U12 IP2326 | ISET | R35 → GND, **value TBD ⚠️** for ~1 A charge current (was TP5100 PROG 1.2 k) |
| U12 IP2326 | NTC | RT1 strap **TBD ⚠️** — strongly prefer a real 10 k NTC thermally coupled to the pack (cold-charge cutoff, `component_selection_review.md` O-1) over a fixed disable strap |

> **2026-07-05:** the TP5100 CRITICAL flag is resolved by the IP2326 replacement (design change #12). Remaining risk: IP2326's 2S **mid-cell/balance pin** vs our 2-pin XT30 pack — if the pin cannot be left unconnected, the charger choice reopens (blocker #2a).

### AP63203WU buck (U1)

| Component | Pin | Note |
|-----------|-----|------|
| U1 | VIN | VBAT; C9/C10/C16 at pin |
| U1 | EN | R11 (10k) to VBAT — always on |
| U1 | SW | → L2 pin 1 |
| L2 | pin 2 | +3V3 rail (C_BUCK/C11/C12 here) |
| U1 | FB | **Tie directly to +3V3** (fixed 3.3 V part). R_FBH/R_FBL are DNP. |
| U1 | BST | Left as symbol pin; original design leaves it unconnected (bootstrap integrated per AP6320x family). **Verify against datasheet** — if an external 100 nF BST–SW cap is required, add one. |

### ADS_DRDY

| Component | Pin | Note |
|-----------|-----|------|
| U9 ADS1115 | ALERT (pin 2) | Open-drain conversion-ready |
| R_DRDY (4.7k) | pin 2 | Pull-up to +3V3 |
| U6 ESP32-C6 | GPIO12 | Falling-edge interrupt |
| TP12 | pad | Test point |

### I2C_SDA / I2C_SCL

| Component | Pin | Note |
|-----------|-----|------|
| U9 ADS1115 | SDA (pin 9) / SCL (pin 10) | True TI MSOP-10 numbering: ADDR=1, ALERT=2, GND=3, AIN0=4, AIN1=5, AIN2=6, AIN3=7, VDD=8, SDA=9, SCL=10 |
| U6 ESP32-C6 | GPIO10 (SDA) / GPIO11 (SCL) | |
| R9 / R10 (4.7k) | pin 2 | Pull-ups to +3V3 |
| J8 | SDA/SCL pins | I²C header (DNF): 3V3 / GND / SDA / SCL |
| TP8 / TP9 | pads | Test points |

### ADC_CH0 / ADC_CH1 (4-20 mA inputs)

CH1 path: `J4 SIG → D9 clamp → R2 shunt (‖ C34) → R3 → ADC_CH0 (C3, C4, D1 ch.1) → U9 AIN0`

| Component | Pin | Net segment | Note |
|-----------|-----|-------------|------|
| J4 | SIG (pin 2) | LOOP_TERM_CH1 | Loop return from transmitter |
| D9 SMAJ3.3CA | terminal 1 | LOOP_TERM_CH1 | Clamp to GND |
| R2 (100Ω 0.1%) | pin 1 | LOOP_TERM_CH1 | Shunt top; **pin 2 → GND** (loop current returns through R2) |
| C34 (10nF) | pins 1–2 | across R2 | HF bypass, within 1 mm |
| R3 (100Ω) | pin 1 | LOOP_TERM_CH1 (shunt top) | Series limiter |
| R3 | pin 2 | ADC_CH0 | |
| C3 (1µF), C4 (10µF) | pin 1 | ADC_CH0 | RC filter / bulk |
| D1 PRTR5V0U2X | IO1 | ADC_CH0 | Clamp to +3V3/GND |
| U9 ADS1115 | AIN0 | ADC_CH0 | 20 mA × 100 Ω = 2.0 V max, PGA ±2.048 V |
| TP5 | pad | LOOP_TERM_CH1 | At shunt top |

CH2 identical: `J5 SIG → D10 → R4 (‖ C35) → R5 → ADC_CH1 (C5, C6, D1 IO2) → U9 AIN1`, TP6 at shunt top.

### ADC_CH2 (battery divider — corrected high-side gating)

Path: `VBAT → Q5 (P-FET) → R7 (330k) → mid (ADC_CH2) → R8 (100k) → GND`

| Component | Pin | Note |
|-----------|-----|------|
| Q5 AO3407 | S | VBAT |
| Q5 AO3407 | D | VBAT_SW → R7 pin 1 |
| Q5 AO3407 | G | Q5_GATE: R16 (100k) to VBAT; Q2 drain pulls low to enable |
| Q2 BSS123 | D | Q5_GATE |
| Q2 BSS123 | G | BATT_DIV_EN (GPIO15), R26 (4.7k) pull-down |
| Q2 BSS123 | S | GND |
| R7 | pin 2 | ADC_CH2 (mid) |
| R8 | pin 1 / pin 2 | mid / GND |
| C8 (**1 nF**) | pins 1–2 | across R8 — τ ≈ 77 µs, settles well inside the 1 ms firmware enable window |
| U9 ADS1115 | AIN2 | 8.4 V × 100/430 = 1.95 V max |

> With Q5 off, the divider is fully dead: AIN2 rests at 0 V through R8 and there is no sneak path into the ADS1115 ESD diodes (the old low-side switch leaked ~14 µA into AIN2 during sleep).

### 1WIRE

| Component | Pin | Note |
|-----------|-----|------|
| J6 | DATA (pin 2) | DS18B20 data |
| D12 PRTR5V0U2X | IO1 | Clamp at terminal (IO2 = NC) |
| R6 (4.7k) | pin 2 | Pull-up to +3V3 |
| R32 (33Ω, **populate**) | pin 1 / pin 2 | Terminal side / GPIO side series resistor |
| U6 ESP32-C6 | GPIO7 | 1-Wire master |
| TP7 | pad | GPIO7 side of R32 |
| J6 VCC (pin 1) | ← R28 (100Ω) ← +3V3 | C7 (100nF) at J6 pin 1. External power mode only |

### EN (ESP32 reset)

| Component | Pin | Note |
|-----------|-----|------|
| U6 ESP32-C6 | EN | |
| R15 (10k, **new**) | pin 2 | Pull-up to +3V3 |
| C36 (1µF, **new**) | pin 1 | To GND — 10 ms power-on delay |
| SW1 | pin 1 | Push to GND = reset |
| J10 | EN pin | Programming header |

### BOOT

| Component | Pin | Note |
|-----------|-----|------|
| U6 ESP32-C6 | GPIO9 | Strapping (LOW = download mode) |
| R12 (10k) | pin 2 | Pull-up to +3V3 |
| SW2 | pin 1 | Push to GND |
| J10 | GPIO9 pin | |

GPIO8 strapping: R13 (10k) pull-up to +3V3, no other connection.

### GPIO14_LED (status LED — moved off GPIO13)

| Component | Pin | Note |
|-----------|-----|------|
| U6 ESP32-C6 | **GPIO14** | LED drive (was GPIO13 — conflicted with factory-reset strap) |
| R14 (1k) | pin 1 / pin 2 | GPIO14 / D4 anode |
| D4 green | cathode | → SJ3 → GND (SJ3 bridged; open to save current) |

### FACTORY_RESET

| Component | Pin | Note |
|-----------|-----|------|
| U6 ESP32-C6 | GPIO13 | Internal pull-up at boot; hold LOW ≥ boot = NVS erase + rejoin |
| TP13 (**new**) | pad | Field-accessible pad — short to TP4/GND while powering on |

### UART_TX / UART_RX

| Component | Pin | Note |
|-----------|-----|------|
| U6 ESP32-C6 | GPIO16 (TX) / GPIO17 (RX) | UART0 default pins |
| SJ4 / SJ5 | A→B | In series to J10 (bridged by default — see resolution table on jumper variant) |
| J10 | TX/RX pins | Programming header: TX / RX / GND / 3V3 / GPIO9 / EN |

### J7 spare sensor / J9 GPIO header

- J7: pin 1 = +3V3, pin 2 = GPIO3 (spare ADC), pin 3 = GND.
- J9 (8-pin, DNF): +3V3, GND, GPIO0, GPIO1, GPIO2, GPIO3, GPIO20, GPIO21.

### RF

`U6 U.FL pad → W1 pigtail (hand-fitted) → J3 SMA`. J3 RF pin has no PCB trace; GND ring to plane.

---

## Power-On Sequence Reference

1. Battery connects → VBAT_RAW → D5 body diode conducts, then channel enhances (gate at GND via R31) → VBAT.
2. U1 (fixed 3.3 V) starts (EN via R11) → +3V3 → C36/R15 delay → ESP32 boots.
3. Boost idles: R27 holds MT3608B EN + Q4 low. Both chargers are autonomous — CN3722 charges whenever panel power is present, IP2326 whenever VBUS is present (no enable GPIOs).
4. Firmware: GPIO5 HIGH → U8 EN + Q4 → Q3 closes → VLOOP = 12 V (allow ≥5 ms, recommend 10 ms for C20/C22 charge through Q3) → loop read → GPIO5 LOW.
5. Firmware: GPIO15 HIGH → Q2 → Q5 closes → divider live (settles < 1 ms with C8 = 1 nF) → AIN2 read → GPIO15 LOW.
6. Deep sleep: all control GPIOs driven LOW then isolated; R27/R26/R37/R31 define every switch state passively. No DC path from VBAT except U1, R11, and IC quiescents.

---

## Symbol pin-number verification

Wiring above uses **pin names**. Before assigning footprints / generating a netlist, verify these symbol pin **numbers** against datasheets — several are known or suspected wrong:

| Symbol | Status |
|--------|--------|
| welld:ADS1115 | ✅ matches TI MSOP-10 (ADDR=1 … SCL=10) |
| welld:AO3407 | ✅ G=1, S=2, D=3 (SOT-23) |
| welld:AP63205WU (used for U1) | ⚠️ numbering EN=1, GND=2, FB=3, VIN=4, SW=5, BST=6 — **verify against Diodes TSOT-26 datasheet**; also rename to AP63203WU |
| welld:MT3608B | ❌ suspect — classic MT3608 SOT-23-6 is SW=1, GND=2, FB=3, EN=4, IN=5, NC=6. Symbol has IN=1, SW=5, BST=6. Fix numbering (or the footprint mapping) before layout |
| welld:USBLC6_2SC6 | ❌ suspect — real part: IO1=1, GND=2, IO2=3, IO2'=4, VBUS=5, IO1'=6. Symbol has VBUS=1, GND=4 |
| welld:TP5100 | ❌ obsolete — TP5100 replaced by IP2326 (design change #12). Delete this symbol and draw a new **welld:IP2326** (ESOP-8) from the Injoinic datasheet |
| welld:CN3722 | ⚠️ 8-pin symbol; part is likely SSOP-10 (with /DONE pin). Verify pinout + package |
| welld:PRTR5V0U2X | ⚠️ 6-pin symbol / SOT-363 footprint; real PRTR5V0U2X is SOT-143B (4 pins: I/O1, I/O2, VCC, GND) |
| welld:ESP32_C6_MINI_1U | ⚠️ custom numbering — replace with the official Espressif KiCad symbol/footprint before layout |

---

## Datasheet verification blockers (resolve before tape-out)

1. **U1 identity**: confirm AP63203WU = 3.3 V fixed / AP63205WU = 5 V fixed / AP63200WU = adjustable (VFB 0.8 V), and whether the BST pin needs an external cap. Pick AP63203WU (preferred, R_FBH/R_FBL stay DNP) or AP63200WU (fit R_FBH=390k, R_FBL=124k). Also confirm the ~22 µA no-load Iq figure used in the sleep budget (`component_selection_review.md` §3).
2. **U12 IP2326** (replaced TP5100, design change #12) — verify against the Injoinic datasheet:
   - **2a. Mid-cell/balance pin — ✅ RESOLVED 2026-07-06**: VBATM (pin 23) and VBAT_GND (pin 24) "should be left floating when doesn't use" per the IP2326 V1.2 datasheet. The 2-pin XT30 pack works unchanged with balancing disabled. Charger choice stands.
   - 2b. Package = ESOP-8 and exposed-pad size; full pinout for a new `welld:IP2326` symbol.
   - 2c. CV = 8.40 V fixed for 2S (or how it is set).
   - 2d. R35 ISET value for ~1 A charge current.
   - 2e. EN/CE pin — ✅ RESOLVED 2026-07-06: **EN exists (pin 12)**, pull-low-to-disable, float = enabled. Decision: leave floating (auto-charge on VBUS), GPIO4 stays freed. Polarity matches the old TP5100 CE drive, so GPIO4→EN is a zero-firmware-change option later. Package is **24-pin + EPAD, not ESOP-8** — see component_selection_review.md 2026-07-06 addendum for the full verified pin map, RVSET=120k CV correction (NC strap maxes at 8.5 V — unsafe for 2S), RISET=90k (1 A), and the NTC pin path to the sub-zero cutoff.
   - 2f. NTC pin function and strap; wire a real pack NTC if feasible (blocker #7 / review O-1).
   - 2g. BAT-pin quiescent with USB absent — must be < 10 µA (nightly battery drain).
   - 2h. Input-adaptive current limiting behaviour on weak 5 V sources (we advertise only default USB via 5.1 k CC sinks).
   - 2i. L3 inductor value/Isat and input/output cap values (C28/C29); status-pin type for R38.
   - 2j. LCSC part number and stock.
3. **U8 MT3608B**: confirm pinout, whether pin 6 is BST or NC (C_BST fitted either way — harmless on NC), switch-current/sync-rectifier details, and EN-low shutdown current (<1 µA assumed in the sleep budget). D15 + Q3/Q4 disconnect are required regardless unless the chosen part has true load disconnect.
4. **U7 CN3722**: confirm package (SSOP-10?), current-set mechanism (VPROG resistor vs CSP/CSN sense resistor), /DONE pin, and MPPT/FB pin numbering. **Added 2026-07-05**: (a) BAT-pin quiescent in the dark — this sits on the pack every night, expect low single-digit µA; (b) whether a TEMP/NTC pin exists — if so, wire it for cold-charge cutoff (blocker #7).
5. **ESP32-C6-MINI-1U**: replace custom symbol with the Espressif library part.
6. **D9/D10 SMAJ3.3CA leakage** (added 2026-07-05): confirm reverse leakage at 2.0 V working voltage / 60 °C is ≤ 1 µA — the leakage path parallels the 100 Ω shunt and reads as loop current. If it fails, substitute a 5 V-standoff low-leakage clamp (R3/R5 + D1 still protect the ADS1115 pins).
7. **Charge-temperature and pack-current limits** (added 2026-07-05): (a) confirm the pack PCM continuous charge rating ≥ 2 A (solar 0.5 A + USB 1 A co-charge, review §2); (b) decide the below-0 °C charging strategy — Li-ion must not be charged below 0 °C, and this is an outdoor device. Preferred: real NTC to both chargers' temperature pins (review O-1).
8. **F2 replacement PTC** (added 2026-07-05): exact MPN for a 2 A-hold / ≥6 V / 1206 part (MF-MSMF200/16X class — verify suffix and voltage rating), sized for the IP2326's ≈1.9 A input current at 1 A charge.

---

## Components Still Needing Resolution in KiCad

| Symbol | Issue | Action in KiCad |
|--------|-------|-----------------|
| R_FBH / R_FBL | Marked DNP in schematic (fixed-3.3 V U1 needs no divider) | Leave DNP for AP63203WU; if AP63200WU chosen, set values 390k/124k and clear DNP |
| Q3, Q4, R29, D15 | VLOOP disconnect + rectifier — **not yet placed as symbols** | Add to power sheet per the VLOOP section above (Q3=AO3407, Q4=BSS123, R29=100k 0402, D15=SS34 SMA) |
| R25, R27 | New pull-up/pull-down — **not yet placed** | Add to power sheet (R25 4.7k 0402, R27 100k 0402) |
| Q5, R16 | Battery divider high-side switch — **not yet placed** | Add to sensors sheet (Q5=AO3407, R16=100k 0402); rewire Q2 as its gate driver per ADC_CH2 section |
| R15, C36 | ESP32 EN RC — **not yet placed** | Add to mcu sheet (10k 0402, 1µF 0402) |
| TP13 | Factory-reset pad — **not yet placed** | Add to interfaces sheet (TestPoint_Pad, net GPIO13) |
| C8 | Value change 100nF → 1nF | Edit value in sensors sheet |
| D8, D14 | SMAJ28CA → SMAJ24CA | Edit values in power sheet |
| C17 | 25 V → 35 V rating (footprint 0805 → 1206) | Edit value/footprint in power sheet |
| SJ2/SJ3 (and new SJ4/SJ5) | All five SJ symbols use the *Open* variant; SJ2/SJ3/SJ4/SJ5 should default **bridged** | Swap symbol/footprint variant |
| U12 | TP5100 symbol obsolete | Delete; draw `welld:IP2326` (ESOP-8) from datasheet after blocker #2 is resolved; rewire USB section per the VUSB, /CHRG_USB, and ISET/NTC tables above |
| L3, RT1 | New IP2326 support parts — **not yet placed** | Add to power sheet once blocker #2 fixes values (L3 boost inductor, RT1 NTC strap) |
| R36, R37 | Deleted with TP5100 CE network | Remove symbols from power sheet; GPIO4 net becomes spare (tell firmware agent) |
| F2 | 1.1 A → 2 A hold PTC | Edit value/MPN in power sheet (blocker #8) |
| U6 | Custom symbol | Replace with Espressif official symbol + footprint |
| C25 | ~~Duplicate of C_BST~~ | ✅ Deleted 2026-07-05 |
| C16 | ~~Unidentified~~ | ✅ Assigned: U1 VIN bulk 10 µF 16 V 0805 |
