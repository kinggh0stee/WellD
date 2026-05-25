# WellD Custom PCB — Design Reference

## Overview

| Parameter | Value |
|-----------|-------|
| Module | ESP32-C6-MINI-1U (external antenna, U.FL) |
| Form factor | 80 × 55 mm, 2-layer, 1 oz Cu |
| Target enclosure | Custom 3D-printed parametric case (`hardware/case/welld_case.scad`) |
| MCU supply | 3.3 V from AP63205 synchronous buck (22 µA Iq), fed from 2S LiPo |
| Battery | 2S1P 18650 LiPo — 6.0 V (discharged) to 8.4 V (full); AMASS XT30PW-F right-angle THT (J1, LCSC C601498), Pin 1=BAT+, Pin 2=BAT− |
| Solar charging | CN3722 2S MPPT solar charger (U7), 5–25 V input, 8.4 V CV target, 500 mA |
| Solar input | 5–25 V (Vmp 5.5 V target for 6 V panel), ≤ 28 V Voc; J12 screw terminal |
| USB-C charging | TP5100 boost charger (U12), 5 V USB-C in → 8.4 V / 1 A out; J13 USB-C connector |
| Loop supply | 12 V boost (MT3608B, U8) from VBAT, GPIO5-gated; powers 2-wire 4–20 mA transmitters |
| Sensor interfaces | 2× 4–20 mA (screw terminals), 1× DS18B20, 1× spare 3-pin, 1× solar 2-pin |
| External ADC | ADS1115 16-bit I²C (U9, 0.1% non-linearity) replaces ESP32 ADC for depth/battery channels |
| Battery voltage | Resistor divider R7/R8 (330 kΩ / 100 kΩ) on ADS1115 AIN2; Q2-gated to save sleep current |
| Expansion | I²C header, 6-pin GPIO header, 4 spare ADC channels |
| Programming | 6-pin 1.27 mm UART header; no USB bridge on board |
| On-board cell protection | **OMITTED** — Sinowatt 2S1P pack contains integrated PCM |

---

## GPIO Assignments

All ADC1 channels (GPIO0–GPIO3) are available for analog backup use. Primary depth and
battery voltage measurements are handled by U9 (ADS1115) over I²C. GPIO5 gates the 12 V
VLOOP boost converter (U8). GPIO6 monitors CN3722 solar charge status. GPIO10/11 are the
shared I²C bus for ADS1115 (U9 only — MAX17048 has been removed). GPIO4 now controls the
TP5100 USB-C charger CE (charge enable) pin. GPIO14 remains spare.

| GPIO | ADC ch | Function | Connected to |
|------|--------|----------|--------------|
| 0 | CH0 | 4–20 mA CH1 (backup) | Shunt R2 → limiter R3 → GPIO0; primary reading via U9 ADS1115 |
| 1 | CH1 | Battery voltage (backup) | Divider R7/R8 → GPIO1 when Q2 enabled; primary via U9 AIN2 |
| 2 | CH2 | 4–20 mA CH2 (backup) | Shunt R4 → limiter R5 → GPIO2; primary reading via U9 ADS1115 |
| 3 | CH3 | Spare ADC | J9 expansion header |
| 4 | — | USB_CHG_DIS | TP5100 CE pin (active-HIGH = charging enabled); R36 100 kΩ pull-up to VUSB; R37 4.7 kΩ bleed to GND holds CE LOW (charger off) at reset/boot and during deep-sleep |
| 5 | — | VBOOST_EN | MT3608B EN pin; firmware drives HIGH only during 4–20 mA measurement window |
| 6 | — | Solar CHRG detect | CN3722 open-drain /CHRG output (active-LOW = charging in progress); GPIO6 configured as input with internal pull-up; read LOW = solar charging active |
| 7 | — | DS18B20 1-Wire | J6 screw terminal |
| 8 | — | Strapping pull-up | 10 kΩ to 3.3 V, test pad |
| 9 | — | BOOT strapping | 10 kΩ pull-up; SW2 to GND |
| 10 | — | I²C SDA | J8 header, ADS1115 only; 4.7 kΩ pull-up R9 |
| 11 | — | I²C SCL | J8 header, ADS1115 only; 4.7 kΩ pull-up R10 |
| 12 | — | ADS1115_ALERT / DRDY | ALERT/RDY pin of U9; interrupt-driven conversion ready |
| 13 | — | Status LED | 1 kΩ → D4 → GND; SJ3 to disconnect |
| 14 | — | **SPARE** | Available for user functions |
| 15 | — | BATT_DIV_EN | Gate of Q2 (N-MOSFET); enables battery voltage divider only during measurement |
| 16 | — | UART0 TX | J10 programming header |
| 17 | — | UART0 RX | J10 programming header |
| 18 | — | Spare | Unused |
| 19 | — | Spare | Unused |
| 20 | — | Spare digital | J9 expansion header |
| 21 | — | Spare digital | J9 expansion header |

> **USB note:** GPIO12/GPIO13 are the ESP32-C6 on-chip USB-Serial-JTAG D−/D+
> lines. This board repurposes them (GPIO12 → ADS1115 DRDY, GPIO13 → status LED)
> so the native USB-Serial-JTAG interface is not available. All flashing and debug
> is over the J10 UART header. J13 is the USB-C power-only charging input (TP5100,
> U12); it carries only VBUS and CC resistors — no USB data path.

---

> **Firmware requirements:**
> 1. GPIO5 HIGH before any 4–20 mA reading; LOW after. Allow 5 ms for MT3608B soft-start.
> 2. GPIO15 HIGH for 1 ms before battery ADC read via U9 AIN2; LOW after.
> 3. GPIO4 is USB_CHG_DIS — TP5100 CE (active-HIGH = charging enabled). Drive GPIO4 HIGH on wake to enable USB charging; R37 (4.7 kΩ to GND) holds CE LOW during reset/boot (charger off at power-on until firmware explicitly enables). Include GPIO4 in `esp_sleep_gpio_isolate()` coverage so it floats during deep-sleep; R37 bleed then holds CE LOW passively.
> 4. GPIO6 solar-detect remains active-LOW input with internal pull-up; no action needed.
> 5. Read U9 ADS1115 via I²C for all depth and battery voltage measurements; keep GPIO0/1/2 reads as fallback.
> 6. Battery SOC is now estimated from ADS1115 AIN2 using resistor divider R7/R8 (330 kΩ / 100 kΩ); CONFIG_WELLD_BATT_DIVIDER_RATIO = 430. VBAT range: 6.0–8.4 V. Update battery_full_mv = 8400, battery_empty_mv = 6000 in Z2M converter options.
> 7. Implement GPIO12 DRDY interrupt for ADS1115 single-shot completion signalling.
> 8. GPIO14 is spare — no MAX17048 ALRT handling needed.
> 9. No /CHRG GPIO monitoring for U12 — TP15 is a hardware-only test point; firmware does not need to read it.

---

## Block Descriptions

## Solar Charging

A solar panel connects via a 2-pin pluggable screw terminal (J12, Phoenix MC
1.5/2-ST-3.5) on the bottom edge. The solar path uses a dedicated MPPT charger
(U7: CN3722) that maximises charge current under partially-shaded or early-morning
conditions where panel voltage sags below Vmp. The CN3722 targets 8.4 V CV for the
2S Li-ion pack.

GPIO6 is the CN3722 /CHRG status input (active-LOW = charging in progress).

### Solar panel selection

| Panel spec | Requirement |
|------------|-------------|
| Vmp | 4.5–20 V (CN3722 MPPT input range 5–25 V with D6 drop) |
| Voc | ≤ 28 V (CN3722 VIN absolute max 28 V) |
| Isc | ≤ 1.5 A (CN3722 max charge current) |
| Typical match | 5–10 W / 6 V rigid or flexible panel; Vmp ≈ 5.5 V |

12 V panels (Vmp ≈ 17–18 V) are now compatible — CN3722 accepts up to 25 V MPPT
operating voltage and 28 V absolute max. A 10 W / 12 V panel works; recalculate
R20/R21 divider for the panel's Vmp.

### MPPT setting (R20/R21)

CN3722 regulates its VIN to maintain VMPPT = 1.205 V at the MPPT pin. The
resistor divider R20/R21 (from VIN to GND, midpoint to MPPT pin) sets the target
operating point:

    Vmppt_target = 1.205 × (R20 + R21) / R21

Default values: R20 = 36 kΩ, R21 = 10 kΩ → Vmppt = 1.205 × 46/10 = **5.5 V**
(correct for a 6 V nominal panel with Vmp ≈ 5.5 V).

For a 12 V nominal panel (Vmp ≈ 17 V): R20 = 130 kΩ, R21 = 10 kΩ →
Vmppt = 1.205 × 14 = 16.9 V.

The divider senses the CN3722 VIN pin, which sits one Schottky drop below the
panel terminal (D6 is in series ahead of VIN). The panel therefore operates at
roughly Vmppt + Vf(D6) ≈ Vmppt + 0.4 V. Account for this when matching the divider
to a panel's true Vmp — drop R20 slightly if the panel should sit exactly at Vmp.

### Charge voltage (2S CV target, R_CV divider)

CN3722 uses a feedback resistor divider (R_CVH / R_CVL from VBAT to GND,
midpoint to FB pin at 1.205 V) to set the constant-voltage (CV) charge threshold.
For 2S target of 8.4 V:

    8.4 = 1.205 × (R_CVH + R_CVL) / R_CVL
    R_CVH / R_CVL = (8.4 / 1.205) − 1 = 5.972

Standard values: R_CVH = 560 kΩ, R_CVL = 100 kΩ → ratio = 5.6 → Vchg = 1.205 × 6.6 = 7.95 V.
Better: R_CVH = 620 kΩ, R_CVL = 100 kΩ → ratio = 6.2 → Vchg = 1.205 × 7.2 = 8.68 V (slightly high).
Use **R_CVH = 590 kΩ (use 560 kΩ + 30 kΩ or 604 kΩ E96), R_CVL = 100 kΩ** →
Vchg = 1.205 × 7.04 = 8.48 V ≈ 8.4 V. Practical nearest standard: **R_CVH = 604 kΩ
(E96 1%, LCSC available), R_CVL = 100 kΩ** → 8.48 V. Populates as R33 and R34
(new references, 0402 1%).

Alternatively, for tighter accuracy use **R_CVH = 560 kΩ + 39 kΩ in series (bridge
with 0402 footprint) = 599 kΩ, R_CVL = 100 kΩ** → 8.42 V. The BOM lists R33 = 604 kΩ
(E96) and R34 = 100 kΩ as the default selection.

### Charge current (R19)

CN3722 PROG pin: R19 = 2 kΩ → 500 mA charge current.
This draws ≈ 600 mA from a 6 V panel at the MPPT point (accounting for ~85 %
conversion efficiency) — well within a 5 W panel's Isc. For smaller panels,
raise R19: 3.3 kΩ → 300 mA.

### Solar terminal ESD protection (D14)

D14 (SMAJ28CA, DO-214AC/SMA, **bidirectional** TVS, 28 V standoff, 400 W peak)
replaces the former SMAJ7.0A now that the CN3722 accepts up to 28 V Voc. It is
placed from J12 SOLAR+ (pin 1) to GND, before D6 (the Schottky input diode).
The two-stage protection chain is:

    J12 SOLAR+ → D14 (SMAJ28CA, first-stage, at terminal)
               → D6 (MBRS140 Schottky, backfeed block)
               → D8 (SMAJ28CA, second-stage, at CN3722 VIN)
               → CN3722 VIN (abs max 28 V)

Standoff selection rationale:
- Normal MPPT operating range: 5 V to 25 V. The 28 V standoff is above the 25 V
  maximum MPPT operating point, so D14 does not conduct during MPPT regulation.
- CN3722 VIN absolute max: 28 V. At Voc = 28 V (worst-case no-load), D14 begins to
  clamp, preventing the full Voc from reaching D6 and CN3722. This is the intended
  behaviour for panel disconnect/reconnect transients.
- Bidirectional: changed from unidirectional SMAJ7.0A to bidirectional SMAJ28CA
  because the higher standoff requires the bidirectional variant to be available in
  this voltage class. A bidirectional TVS on a single-polarity rail is acceptable
  (only the positive standoff direction is active in normal operation).
- D14 and D8 now use the same MPN (SMAJ28CA) — consolidate on one tape reel.
- LCSC: verify SMAJ28CA availability; SMAJ26CA (26 V) is an acceptable substitute.

Place D14 within 3 mm of J12 pin 1, on the terminal side of D6.

### Input protection (D6)

A Schottky diode (D6: MBRS140, SOD-123) in series with J12 pin 1 prevents backfeed
from the battery through U7 when the panel is dark or disconnected, and provides
reverse-polarity protection for miswired panels. D6 rating (40 V reverse, 1 A)
is adequate for the expanded input voltage range.

### CN3722 charging operation

Solar via CN3722 is one of two charging sources; the other is the TP5100 USB-C
charger (U12). GPIO6 monitors the CN3722 /CHRG open-drain output (active-LOW =
charging in progress) and may be used by firmware to log charging status or reduce
transmission interval. The CN3722 also has a /DONE output on a separate pin (if
available — verify pinout against CN3722 datasheet and connect to a test point or
leave no-connect). For dual-charger coexistence details, see **Power — USB-C
Charging (U12: TP5100)**.

---

### Power — Input & Reverse Polarity (D5 + R31)

D5 (AO3407, SOT-23, P-channel MOSFET) provides reverse-polarity protection in series
with the BAT+ rail, downstream of D13 (the battery terminal TVS). It is placed between
J1 BAT+ and the VBAT system rail:

    J1 BAT+ → D13 (SMAJ10CA TVS, across terminal) → D5 source → D5 drain → VBAT rail

D5 wiring:
- Source: J1 BAT+ terminal (VBAT_RAW node, after D13 TVS)
- Drain: VBAT system rail (feeds U1 buck converter, U7 CN3722)
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

AO3407 electrical justification (voltage range 6.0–8.4 V):
- Vgs(th) max: −1.5 V. At minimum battery voltage 6.0 V (discharged), Vgs = −6.0 V,
  giving 4.5 V margin above |Vgs(th)| max — D5 is deeply saturated.
- RDS(on) max: 55 mΩ @ Vgs = −4.5 V. At Vgs = −8.4 V (2S full charge) RDS(on) is
  well below 55 mΩ → drop at 1 A continuous ≤ 55 mV. Peak current ≤ 2 A → worst-case
  drop ≤ 110 mV, well within acceptable limits.
- Vgs absolute maximum: ±12 V. Maximum Vgs magnitude = 8.4 V (2S full charge battery
  on source, gate at 0 V) — 30 % below the ±12 V abs max. No gate-drain clamp required.
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
at 1 A would offset the battery voltage measurement seen by U9 ADS1115 AIN2 via the
R7/R8 divider, introducing a systematic SOC estimation error. The MOSFET solution
has ≤ 55 mV drop, which is within the measurement uncertainty of the voltage divider.

### Power — USB-C Charging (U12: TP5100)

The TP5100 (SOP-8) is a 2S Li-ion boost charger that accepts 4.5–7 V input and
charges a 2S pack to the hardcoded 8.4 V CV target. It is driven by a regulated
5 V / 2 A USB-C panel or wall adapter connected to J13.

#### Input path (VUSB rail)

J13 (USB4135-GF-A, 16-pin USB-C SMD, left short edge — same footprint position
as the former J2) carries VBUS power only:
- D+ and D− are left no-connect (power-only application).
- CC1 and CC2 each have a 5.1 kΩ pull-down to GND (R_CC1, R_CC2, 0402). These
  resistors identify the device as a USB sink requesting 5 V/2 A from any USB-C
  source compliant with the USB Power Delivery Type-C current advertisement
  specification. A 10 W / 5 V / 2 A USB-C solar panel or charger will see this
  as a 1.5 A or 3.0 A current capability advertisement and supply up to 2 A.
- VBUS is routed through F2 (1 A PTC resettable fuse, 1206) to the VUSB net.
- U11 (USBLC6-2SC6, SOT-23-6) provides TVS ESD protection on VBUS and the
  D+/D− stubs. Same part as the former U5 (reintroduced to BOM). Place between
  J13 and F2.
- C27 (4.7 µF, 10 V, 0805) on VUSB after F2 for input filtering.

#### TP5100 charge path

| Pin | Net | Component |
|-----|-----|-----------|
| VIN | VUSB | C28 (10 µF, 10 V, 0805) bypass within 2 mm of VIN pin |
| GND | GND | — |
| VBAT | VBAT | C29 (10 µF, 16 V, 0805) bypass within 3 mm of VBAT pin; shared VBAT rail with CN3722 output |
| PROG | R35→GND | R35 (1.2 kΩ, 1%, 0402): Icharge = 1200 / 1.2 = 1000 mA = 1 A; place within 3 mm of PROG pin |
| CE | GPIO4 via R36/R37 | R36 (100 kΩ, 0402) pull-up from CE to VUSB; R37 (4.7 kΩ, 0402) from CE to GND. GPIO4 driven HIGH enables charging; R37 holds CE LOW when GPIO4 floats (reset, boot, deep-sleep) — charger is off by default |
| /CHRG | TP15 via R38 | R38 (4.7 kΩ, 0402) pull-up from /CHRG to +3V3; /CHRG net routed to TP15 only (no GPIO monitoring needed) |

Charge current: Icharge = 1200 / Rprog(kΩ) mA → R35 = 1.2 kΩ → 1 A.
At 5 V in, 8.4 V out, 1 A: efficiency ~85%; Pdiss ≈ (8.4 − 5) × 1 / 0.85 × (1 − 0.85) ≈ 1.5 W.
SOP-8 θJA ≈ 150 °C/W → ΔTj ≈ 22 °C above ambient. Acceptable without a heatsink.
Add an 8 × 8 mm solid GND copper pour on F.Cu under and around U12 for thermal relief.

#### /CHRG status: TP15

TP15 (1.0 mm SMD pad, TestPoint:TestPoint_Pad_1.0x1.0mm, DNF) is placed on the
/CHRG net with R38 (4.7 kΩ) pull-up to +3V3. Active-LOW: pad is LOW when U12 is
actively charging, pulled HIGH (3.3 V) by R38 when idle or no VUSB present. Used
for field debug with a meter or logic probe; no firmware GPIO connection required.

#### Dual-charger coexistence

Both U12 (TP5100, USB-C) and U7 (CN3722, solar J12) share the VBAT rail. Both
charge to 8.4 V as their CV target. Coexistence is safe because:

- Both regulators operate in constant-voltage mode at 8.4 V; the battery terminal
  voltage simultaneously clamps both outputs. Neither charger can overcharge the
  other.
- Combined maximum charge current: CN3722 500 mA + TP5100 1000 mA = 1500 mA.
  For a 2S1P Sinowatt 3350 mAh pack: 1500 / 3350 = 0.45 C — well within the
  standard 0.5 C safe charge rate for 18650 cells. The pack's internal PCM will
  cut off before thermal limits are reached.
- No hardware interlock between U7 and U12 is required. GPIO4 CE control gives
  firmware optional supervisory control over U12 if desired (e.g. suppress USB
  charging when solar alone is sufficient).

> **Combined charge current warning:** If both sources are simultaneously active and
> the battery is deeply discharged, peak combined current into the pack can reach
> 1.5 A. Verify the target pack's PCM is rated for at least 2 A charge current to
> provide margin. The Sinowatt 2S1P (Arizer Solo II) PCM is rated for ≥ 2 A charge.

#### Placement notes for U12 / J13 subcircuit

- J13: left PCB edge, same X-position as former J2. The case left-wall USB-C
  slot cutout must be re-added (case agent constraint — see below).
- U12: bottom-left quadrant, near J13; keep VIN trace from F2 to U12 VIN under 10 mm.
- R_CC1, R_CC2: within 3 mm of J13 CC1/CC2 pins.
- F2 and U11: between J13 VBUS pin and U12 VIN; keep VUSB trace under 15 mm total.
- C28 within 2 mm of U12 VIN pin; C29 within 3 mm of U12 VBAT pin.
- R35 within 3 mm of U12 PROG pin.
- R36 and R37 near U12 CE pin (R36 to VUSB net, R37 to GND).
- TP15 near U12 /CHRG pin.
- GND copper pour 8 × 8 mm under U12 on F.Cu for thermal relief.

> **Case-engineer constraint:** J13 USB-C connector is on the left short PCB edge.
> The enclosure left wall requires a USB-C slot cutout: 10 mm wide, 5 mm tall,
> at PCB surface level.

### Power — Solar MPPT Charging (U7: CN3722)

MPPT solar charger, SOP-8. Accepts 5–25 V from J12 (via D6 Schottky protection).
Charges VBAT to 8.4 V with constant-current / constant-voltage profile. MPPT
regulation reference: 1.205 V.

Key passives:
- R19 (2.0 kΩ, PROG pin to GND): sets charge current to ~500 mA.
- R20 (36 kΩ) + R21 (10 kΩ) divider from VIN to GND, midpoint to MPPT pin: targets
  Vmppt = 5.5 V (optimal for a 6 V nominal / Vmp 5.5 V panel).
- R33 (604 kΩ, E96 1%) + R34 (100 kΩ) from VBAT to GND, midpoint to FB pin:
  sets CV charge voltage to 8.4 V.
- C17 (10 µF, 25 V, 0805) on VIN: input filter.
- C18 (10 µF, 16 V, 0805) on VBAT: output filter (16 V rating required for 8.4 V output).
- D7 (green LED, DNF) with R22 (1 kΩ) on /CHRG pin: solar charge indicator.

The CN3722 /CHRG open-drain output is connected to GPIO6 (active-LOW = charging in
progress). GPIO6 is configured as input with internal pull-up — no EN/shutdown pin
is involved (the CN3722 has no EN pin — it runs continuously whenever VIN is present).

### Power — Battery Terminal ESD Protection (D13)

D13 (SMAJ10CA, DO-214AC/SMA, bidirectional TVS, 10 V standoff, 200 W peak pulse
power) replaces the former SMAJ5.0CA. It is placed across J1 BAT+ and BAT- (the
system GND side of the battery connector, before D5 the reverse-polarity P-MOSFET).
It absorbs ESD and inductive cable transients on the battery wiring in both polarities.

Standoff selection rationale (updated for 2S battery, 6.0–8.4 V range):
- Normal battery voltage range: 6.0 V (2S discharged) to 8.4 V (2S full charge).
  The SMAJ5.0CA (5.0 V standoff) would conduct continuously at any normal battery
  voltage — it was completely wrong for this application and **must** be replaced.
- SMAJ10CA standoff: 10 V — 19 % above the 8.4 V maximum 2S charge voltage, so it
  does not conduct during normal charge/discharge cycles.
- Clamp voltage at 10 A pulse (SMAJ10CA): approximately 16.7 V. This absorbs
  ESD (sub-microsecond) energy that otherwise arrives as a much higher uncontrolled
  voltage spike. The AP63205 buck converter has a VIN absolute maximum of typically
  18–24 V (verify datasheet); the 16.7 V clamp is within this range for transient
  energy absorption only.
- Bidirectional: required because charge current flows into BAT+ and discharge
  current flows out of BAT+. Both polarities of transient must be clamped.
- DO NOT substitute a unidirectional TVS on a bidirectional power rail.
- LCSC: SMAJ10CA — verify current availability; C2836474 or equivalent DO-214AC.

Place D13 within 5 mm of J1 AMASS XT30PW-F battery connector. Anode/cathode
orientation is symmetric for bidirectional TVS — either orientation is correct.

### Power — Battery Protection (U3, U4: REMOVED)

The S-8261AAYFT (U3) and FS8205A (U4) single-cell protection ICs and their
associated bypass capacitors (C26 for U3 VCC, previously missing) have been
**removed** from this design. These ICs have per-cell voltage thresholds (2.9 V
over-discharge, 4.28 V over-charge) calibrated for a single 18650 cell and are
incompatible with a 2S pack.

The Sinowatt 2S1P 18650 pack (from Arizer Solo II) is assumed to contain an
integrated PCM (protection circuit module) that protects both cells against
over-charge, over-discharge, and over-current. On-board single-cell protection
ICs are therefore redundant and omitted.

> **Field installer warning:** Verify that the replacement Sinowatt 2S1P pack has
> an integrated PCM before deployment. A pack without internal protection connected
> to this board has no over-charge/over-discharge cutoff. Do not deploy unprotected
> bare cells.

The battery connector J1 has been changed from JST XH 2.5 mm (B2B-XH-AM) to
**AMASS XT30PW-F right-angle THT** (LCSC C601498) to match the 2S1P 18650 pack
current capacity. Polarity: pin 1 = BAT+ (positive), pin 2 = BAT− (negative).
Verify polarity before connecting the pack — XT30 connectors are physically
keyed (male/female) but verify wire colours against the pack's own PCM labels.

> **Note on C26:** C26 (100 nF, previously added as S-8261AAYFT VCC bypass — listed
> as "previously missing" in an earlier revision) is removed along with U3.

### Power — VLOOP 12 V Boost (U8: MT3608B)

The VLOOP rail supplies 2-wire 4–20 mA pressure transmitters, which require ≥ 10 V
to operate their internal electronics. U8 (MT3608B, SOT-23-6, synchronous boost,
Vin 2–24 V) converts VBAT (6.0–8.4 V) to 12 V when the EN pin is driven HIGH by
GPIO5. The output voltage is set by a resistor divider from VOUT to the
FB pin (0.6 V reference):

    VOUT = 0.6 × (1 + R23/R24) = 0.6 × (1 + 1.9 MΩ / 100 kΩ) = 12.0 V

R23 = 1.9 MΩ (E96 1%, 0402), R24 = 100 kΩ (1%, 0402). VOUT = 0.6 × (1 + 19) =
12.0 V. The high divider impedance keeps the FB leg current to ≈ 6 µA while the
boost is enabled. The MT3608B FB bias current is < 100 nA — negligible at this
impedance.

R23 = 1.9 MΩ, R24 = 100 kΩ for the MT3608B's 0.6 V reference.

L1 (4.7 µH, 1.0 A, CDRH4D22NP-4R7NC or equivalent 4×4 mm shielded) is retained
and placed within 3 mm of U8 SW pin. The MT3608B has a peak switch current of 4 A
and the inductor's 1 A saturation current rating is adequate for 12 V at 20 mA
load (typical). C19 (10 µF, 16 V, 0805 — voltage rating increased from 10 V to
accommodate up to 8.4 V VIN), C20 (22 µF 16 V, 1206), and C22 (10 µF 16 V, 0805)
provide filtering. GPIO5 drives EN HIGH only during the 4–20 mA measurement window
(typically 50–100 ms); at all other times EN=LOW and U8 draws < 1 µA.

C22 (10 µF, 0805, X5R, ≥16 V rating) is placed in parallel with C20 at the
MT3608B VOUT pin. X5R capacitors at 12 V DC bias derate significantly — a nominal
22 µF 1206 X5R may present only 6–8 µF effective capacitance at 12 V. C22 ensures
≥10 µF effective output capacitance is maintained. Place C22 adjacent to C20,
within 3 mm of U8 VOUT pin.

D11 (SMAJ13A, DO-214AC/SMA, unidirectional TVS, 13 V standoff, ≈21.5 V clamp
@ 10 A) is retained — standoff 13 V is above VLOOP nominal (12.0 V) so D11 does
not conduct in steady state. Place within 5 mm of C20/C22 on the J4/J5 side of SJ2.

MT3608B switching frequency: ~1.2 MHz. SW node layout: keep hot-loop trace
(SW → L1 → C20/C22) under 10 mm, ≥ 0.5 mm wide; no pour under L1; GND
via-stitch perimeter. Package: SOT-23-6.


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
the MT3608B VOUT rail and J4/J5 — see **Power — VLOOP 12 V Boost (U8: MT3608B)**
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
panel disconnection. D8 (SMAJ28CA, DO-214AC/SMA, bidirectional TVS, 28 V standoff)
replaces the former SMAJ7.0A (7 V standoff) which was incompatible with the CN3722's
wider input range. D8 is placed across the CN3722 VIN pin and GND after D6 (the
Schottky input diode). D8 absorbs inductive surges from the panel cable before they
reach the CN3722 VIN pin. Standoff voltage 28 V is above the 25 V maximum MPPT
operating voltage, so normal MPPT operation never triggers the TVS. The CN3722 VIN
absolute maximum is 28 V — D8 clamps at that boundary for fast transient energy only;
sustained overvoltage protection relies on selecting a panel whose Voc stays within
the CN3722 abs max. Same MPN as D14 — consolidate on one tape reel. Place D8 within
5 mm of C17.

C21 (100 nF, 0402) is placed directly across D8 (TVS clamp) to absorb the L×dI/dt
inductive transient from panel cable inductance before D8 clamps it. The RC formed
with the cable series resistance (typically 1–5 Ω) limits the peak voltage seen by
D8 during fast-edge events. Place C21 within 3 mm of D8.

### Power — 3.3 V Buck Converter (U1: AP63205)

22 µA quiescent current synchronous buck, SOT-23-6 package, 2 A output. Accepts
VIN 3.8–32 V — compatible with the 2S battery range (6.0–8.4 V).

The synchronous buck topology converts 7.2 V nominal → 3.3 V at ~80 % efficiency.
At 50 mA typical active current (ESP32-C6 active transmit), the buck dissipates
roughly 50 mW.

Quiescent current: 22 µA. At deep-sleep quiescent loads (~20 µA), the 22 µA Iq is
acceptable given the efficiency gain during active wake cycles.

Output voltage: set by an external resistor divider on the FB pin (Vref = 0.6 V):

    VOUT = 0.6 × (1 + R_FBH / R_FBL)

For VOUT = 3.3 V: R_FBH / R_FBL = (3.3 / 0.6) − 1 = 4.5.
Standard values: R_FBH = 470 kΩ, R_FBL = 100 kΩ → VOUT = 0.6 × 5.7 = 3.42 V.
Better: R_FBH = 402 kΩ (E96), R_FBL = 91 kΩ → 0.6 × 5.418 = 3.25 V.
Or: **R_FBH = 330 kΩ, R_FBL = 68 kΩ** → 0.6 × (1 + 4.853) = 3.51 V — slightly
high. Use **R_FBH = 330 kΩ, R_FBL = 75 kΩ** (E96 standard) → 0.6 × 5.4 = 3.24 V.
Recommended: **R_FBH = 560 kΩ, R_FBL = 124 kΩ (E96, or use 120 kΩ + 4.7 kΩ)**
→ 0.6 × (1 + 4.524) = 3.31 V. Practical nearest E24 pair: **R_FBH = 220 kΩ,
R_FBL = 47 kΩ** → 0.6 × 5.681 = 3.41 V. Final selection (BOM R_FBH / R_FBL):
these two resistors replace the former EN pull-up R11 function. The AP63205 has an
internal EN pull-up; tie EN directly to VIN for always-on operation.

The AP63205 switching frequency is 1.5 MHz. An output inductor of 4.7 µH is
recommended (same value as L1 but a different inductor instance — share footprint
if space allows). Output capacitor 10 µF 10 V X5R (0805) in addition to the
existing C11/C12 bypass caps on the regulated output.

Decoupling: C9 (100 nF 0402) + C10 (1 µF 0402) on VIN remain adequate (now rated
for up to 10 V, check existing capacitor ratings are sufficient — 10 V rating is
adequate for 8.4 V VIN with 20 % margin; upgrade to 16 V if available same size).
C11 (100 nF 0402) + C12 (1 µF 0402) on VOUT remain. Add L_BUCK (4.7 µH, 1 A,
0402 or 2520 package — separate inductor, ref L2) and C_BUCK_OUT (10 µF 10 V 0805,
ref C_BUCK) as new BOM items. Note: R35, C27 are now assigned to the TP5100 USB-C
charger subcircuit — do not reuse these designators for AP63205 passives.

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
   from MT3608B switching noise (~1.2 MHz), AP63205 buck noise (~1.5 MHz), and
   Zigbee radio interference on the shared 3.3 V rail. FB1 (BLM18KG601SN1D,
   600 Ω @ 100 MHz, 0402) attenuates high-frequency supply ripple; C23 and C24
   decouple the U9 VDD pin locally.

Target measurement bandwidth: DC to ~5 Hz, set by the SPS = 8 or SPS = 16 ADS1115
operating mode. At SPS = 128, the digital filter corner is ~36 Hz — well below stage 2
anti-aliasing corner of 1.6 kHz, so no aliasing of 50/60 Hz mains.

U9 supply filtering: FB1 (BLM18KG601SN1D, 600 Ω @ 100 MHz, 500 mA, 0402) is
placed in series with the +3V3 feed to U9 VDD, isolating the ADC from switching
noise from U8 (MT3608B, ~1.2 MHz), U1 (AP63205, ~1.5 MHz), and the Zigbee radio.
C23 (100 nF, 0402) and C24 (1 µF, 0402) are placed on the U9 side of FB1, within
1 mm of U9 VDD pin, per ADS1115 datasheet requirements.

### Battery State-of-Charge

SOC estimation is performed using a simple resistor divider measurement:
- ADS1115 AIN2 reads the midpoint of R7 (330 kΩ) + R8 (100 kΩ) from VBAT to GND
  (Q2-gated during measurement).
- CONFIG_WELLD_BATT_DIVIDER_RATIO = 430 → VBAT = AIN2_mV × 430 / 100
- Firmware computes SOC by linear interpolation between battery_empty_mv = 6000
  and battery_full_mv = 8400 (Z2M converter device options).
- The I²C bus now has only one device: ADS1115 at address 0x48. The I2C_SDA /
  I2C_SCL pull-up resistors R9/R10 (4.7 kΩ) remain in place.
- GPIO14 is now spare.
- The I²C header comment in J8 description should be updated to remove MAX17048.

---

## Thermal Review: MT3608B Boost + CN3722 MPPT Simultaneous Operation

Both U8 (MT3608B, 12 V VLOOP boost) and U7 (CN3722, solar MPPT charger) can operate
concurrently during a wake cycle — firmware enables U8 (GPIO5 HIGH) while the solar
charger runs continuously whenever the panel is illuminated.

### MT3608B (U8, SOT-23-6)

- **Package:** SOT-23-6 — no exposed thermal pad; heat exits through the six leads.
- **Switching frequency:** ~1.2 MHz (fixed, internal oscillator).
- **SW node:** transitions between VBAT and GND at ~1.2 MHz. The hot-loop is SW → L1 → VOUT.
- **Power dissipation during active measurement window:** at 12 V output and 20 mA
  maximum loop current, output power ≈ 240 mW. At 90 % conversion efficiency (VIN
  8.4 V), Pdiss ≈ 27 mW. At 85 % (VIN 6.0 V, worst case duty cycle ~69 %), Pdiss
  ≈ 42 mW. SOT-23-6 θJA ≈ 250 °C/W. ΔTj = 42 mW × 250 = 10.5 °C — negligible.
- **Duty cycle:** 50–100 ms per wake cycle (GPIO5 gating), so average Pdiss is
  effectively < 1 mW. U8 thermal management is a non-issue in this duty-cycle regime.
- **SW node copper pour recommendation:** the hot-loop trace (U8 SW pin → L1 → C20/C22)
  must be kept short (< 10 mm) and wide (≥ 0.5 mm). Do NOT pour copper under L1 on
  either layer. Fill the U8/L1/C20 island on F.Cu with a GND via-stitch perimeter
  to provide a low-inductance GND return path for the SW node return current.

### CN3722 (U7, SOP-8)

- **Package:** SOP-8 — no exposed thermal pad; heat exits through leads and pad
  contact on the PCB land pattern.
- **Maximum power dissipation:** at Vin = 6.5 V (MPPT operating point) and
  Vbat = 6.0 V (2S discharged), the internal pass element dissipates approximately:
  Pdiss = (Vin − Vbat) × Ichg = (6.5 − 6.0) × 0.5 A = **0.25 W** (2S minimum case).
  At Vbat = 8.0 V approaching CV, Vin ≤ 6.5 V, IC enters CV/taper — no dissipation
  concern. The worst case with a higher-voltage panel (e.g. 12 V panel, Vin = 17 V)
  and a fully discharged 2S pack (6.0 V): Pdiss = (17 − 6) × 0.5 = **5.5 W** —
  the CN3722 internal thermal fold-back will limit current well before this.
  For a 6 V panel (Vmp ≈ 5.5 V) the worst case is far lower. Copper pour on U7 is
  recommended regardless.
- **Copper pour recommendation:** place a 10 × 10 mm solid copper pour on F.Cu
  under and around U7 (SOP-8 land area), connected to GND via ≥ 4 thermal-relief
  vias (0.6 mm drill, 1.0 mm pad) underneath the IC body. Mirror the pour on B.Cu
  and connect with the same vias. Label `GND_THERMAL_U7` on silkscreen.
- **Placement constraint:** U7 must be placed away from U6 (ESP32-C6 module) and
  U9 (ADS1115). Recommended position: bottom-left quadrant, ≥ 15 mm from U6 and
  ≥ 20 mm from U9. Keep U7 and U8 ≥ 8 mm apart.

### Simultaneous Operation Thermal Budget (2S, 6 V panel)

| Condition | U7 Pdiss | U8 Pdiss | Combined | Est. PCB ΔT |
|-----------|----------|----------|----------|-------------|
| Vin=5.5V, Vbat=7.2V (nominal), Ichg=500mA, Iloop=10mA | 0.35 W | 17 mW | ~0.37 W | ~7 °C |
| Vin=6.5V, Vbat=6.0V (discharged), Ichg=500mA, Iloop=20mA | 0.25 W | 42 mW | ~0.29 W | ~6 °C |
| Deep-sleep (GPIO5=LOW) | < 1 µA × Vin | < 1 µW | negligible | — |

With a 6 V panel, U7 dissipates ~0.35 W typical. If a 12 V panel is used, Pdiss
increases and the copper pour on U7 becomes critical.

---

## Test Points (TP1–TP12)

Solderable test point pads for production testing, ICT fixtures, and field debugging.
All are SMD pads, 1.0 mm diameter copper with solder mask opening. Fit as DNF
(do-not-fit) by default — pads are present on the PCB but no component is required;
a bare pad or a press-fit test nail is used in-fixture.

TP13 (MAX_ALRT) and TP14 (/CHRG_SOLAR) have been **removed**: TP13 because the
MAX17048 is removed and GPIO14 is spare; TP14 because the /CHRG_SOLAR net has been
renamed /CHRG_CN3722 and the TP footprint can be reused for GPIO6 monitoring if
desired (use the spare footprint location as TP14_GPIO6 DNF if needed).

TP15 has been **added** for the TP5100 /CHRG status output (see USB-C charging section).

| Ref | Net | Description |
|-----|-----|-------------|
| TP1 | VBAT | Battery rail (after D5 reverse-polarity MOSFET, before AP63205 buck; range 6.0–8.4 V) |
| TP2 | VLOOP | 12 V boost output rail (after U8 MT3608B VOUT, before J4/J5 VLOOP terminal) |
| TP3 | +3V3 | 3.3 V regulated supply (after AP63205 U1 output) |
| TP4 | GND | System ground reference |
| TP5 | LOOP_TERM_CH1 | CH1 current loop signal: J4 SIG → D9 → R2 shunt; tap is node between R2 and R3 (before ADS1115 AIN0 input limiter) |
| TP6 | LOOP_TERM_CH2 | CH2 current loop signal: J5 SIG → D10 → R4 shunt; tap is node between R4 and R5 (before ADS1115 AIN1 input limiter) |
| TP7 | 1WIRE | DS18B20 1-Wire data bus (J6 DATA line, after R6 pull-up, before D12 ESD clamp) |
| TP8 | I2C_SDA | I²C SDA (GPIO10; ADS1115 only) |
| TP9 | I2C_SCL | I²C SCL (GPIO11; ADS1115 only) |
| TP10 | VSOLAR_IN | Solar panel input at J12 pin 1 (before D14 TVS and D6 Schottky; raw panel voltage) |
| TP11 | VBAT_RAW | Battery terminal before D5 (at J1 BAT+, after D13 TVS; 2S raw battery voltage 6.0–8.4 V) |
| TP12 | ADS_DRDY | ADS1115 ALERT/RDY → GPIO12 (interrupt signal for single-shot conversion complete) |
| TP15 | /CHRG_USB | TP5100 U12 /CHRG open-drain output with R38 (4.7 kΩ) pull-up to +3V3; LOW = USB charging in progress; HIGH (3.3 V) = idle or VUSB absent; field debug only, no GPIO connection |

### Test point placement notes

- TP1/TP3/TP4: place in a row near the AP63205 buck (U1) output, accessible from the top edge.
- TP2: place near C20/C22 on the VLOOP rail.
- TP5/TP6: place within 3 mm of R2/R4 shunt pads, on the ADC-tap (R3/R5) side.
- TP7: place near J6 DATA terminal, on the GPIO7 side of D12.
- TP8/TP9: place near J8 I²C header.
- TP10/TP11: place near J12 and J1 respectively.
- TP12: place near the edge of U6 (ESP32-C6) where GPIO12 routes.
- TP15: place near U12 /CHRG pin (bottom-left quadrant, within 3 mm of U12).
- All TPs must have a 0.2 mm annular ring minimum and be clear of any keep-out zone.
- SMD pad footprint: `TestPoint:TestPoint_Pad_1.0x1.0mm` (KiCad standard library).
- **Case-engineer note:** TP pad height above PCB surface ≈ 0.1 mm (pad only, no
  component body). No keep-out height constraint imposed. A test-nail ICT fixture
  accessing all 13 TPs from the top side requires a 1.27 mm minimum nail-to-nail pitch
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

### MAX17048 (U10) — REMOVED

U10, R27 (ALRT pull-up), and C25 (VDD bypass, formerly noted as missing) have been
removed along with the MAX17048. No decoupling review items apply.

### MT3608B (U8)

- **Present:** C19 (10 µF, 16 V, 0805) on VIN — voltage rating increased to 16 V
  (was 10 V) to accommodate VIN up to 8.4 V with margin; C20 (22 µF 16 V, 1206) +
  C22 (10 µF 16 V, 0805) in parallel on VOUT.
- **Datasheet requirement:** MT3608B datasheet recommends ≥ 10 µF on VIN and ≥ 22 µF
  effective on VOUT. Bootstrap capacitor: MT3608B (SOT-23-6) uses an internal BST pin
  (pin 6) — a 100 nF BST capacitor from BST to SW is required per datasheet. Add
  **C_BST (100 nF 0402, ≥ 16 V)** from MT3608B pin 6 (BST) to SW node. New BOM item.
- **Status:** C19 voltage rating updated; C_BST added as new component.

### CN3722 (U7)

- **Present:** C17 (10 µF, 25 V, 0805) on VIN — 25 V rating required for CN3722
  input range; C18 (10 µF, 16 V, 0805) on VBAT output — 16 V rating required for
  8.4 V output with margin. R19 sets PROG current; C21 (100 nF) across D8 TVS.
- **Datasheet requirement:** CN3722 datasheet recommends 10 µF on VIN and 10 µF on
  VBAT. A 100 nF bypass on the FB/PROG pins is not required. Verify CN3722 pinout
  against datasheet — CN3722 has an additional FB pin for CV voltage set (R33/R34
  divider to GND) for the CV voltage set.
- **Status:** Capacitor voltage ratings updated; R33/R34 added for CV set.

### AP63205 (U1 / 3.3 V Buck)

- **Present:** C9 (100 nF, 0402) + C10 (1 µF, 0402) on VIN; C11 (100 nF, 0402)
  + C12 (1 µF, 0402) on VOUT; C13 (100 nF, 0402) on EN reset (retained from LDO
  design — tie EN to VIN for always-on; C13 can be omitted or kept as VIN bypass).
- **Datasheet requirement:** AP63205 datasheet recommends 10 µF on VIN and a dedicated
  output inductor + output capacitor. Add **L2 (4.7 µH, 1 A, 2520 or 3015 SMD)** and
  **C_BUCK (10 µF 10 V, 0805)** as the primary output filter for U1. The C11/C12
  bypass caps on +3V3 remain for the module and downstream decoupling.
  R11 (10 kΩ EN pull-up) is retained but now connects EN to VIN (VBAT) rather than to
  +3V3, since the AP63205 EN threshold is referenced to VIN. Alternatively, connect
  EN directly to VIN without R11 — both are acceptable.
- **Status:** L2 and C_BUCK are new BOM items. Capacitor voltage rating check: C9/C10
  are on the VIN side (up to 8.4 V) — upgrade to ≥ 16 V rated 0402 ceramics.

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
permanently holds MT3608B EN HIGH (VLOOP always-on). **DNF in production** — lab/debug use
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

D6 (MBRS140, SOD-123) sits in series between J12 pin 1 and CN3722 VIN. It is
oriented with the cathode toward U7 — current flows from the panel into the charger;
the diode blocks reverse current when the panel is dark.

### Battery Voltage Divider

Onboard resistor divider from VBAT (after D5 reverse-polarity MOSFET, before buck):
- R7: **330 kΩ** (high side) — changed from 100 kΩ to scale 8.4 V down into the
  ADS1115 ±2.048 V PGA range
- R8: 100 kΩ (low side), with Q2 (BSS123) in series to GND — gate driven by GPIO15
- Ratio: (330 + 100) / 100 = 4.3 → CONFIG_WELLD_BATT_DIVIDER_RATIO = 430
- ADC tap voltage at full charge: 8.4 × 100 / 430 = 1.953 V ✓ (within ±2.048 V PGA)
- ADC tap voltage at discharged: 6.0 × 100 / 430 = 1.395 V ✓
- C6: 100 nF across R8/Q2 drain for noise immunity (unchanged)
- ADC tap → U9 ADS1115 AIN2 (primary) and GPIO1 (backup, when Q2 enabled)

Q2 (BATT_DIV_EN, GPIO15) gates the lower leg of the divider. During deep sleep
GPIO15 is LOW and Q2 is off, eliminating the divider standby draw. At VBAT = 7.2 V
(nominal 2S), the ungateed divider would draw 7.2 V / 430 kΩ ≈ 16.7 µA — Q2
eliminates this. See **Power — Battery Divider Enable (Q2)** for switching timing.

> **Firmware agent note:** Update CONFIG_WELLD_BATT_DIVIDER_RATIO to 430.
> Update battery_full_mv = 8400 and battery_empty_mv = 6000 in the Z2M converter
> device options. The R7/R8 resistor ratio change is load-bearing for SOC accuracy.

### I²C Expansion Header (J8)

4-pin 2.54 mm single-row header:

| Pin | Signal |
|-----|--------|
| 1 | 3.3 V |
| 2 | GND |
| 3 | SDA (GPIO10) |
| 4 | SCL (GPIO11) |

R9 and R10 (4.7 kΩ each) pull SDA and SCL to 3.3 V on the PCB. The I²C bus now
has a single on-board device: U9 (ADS1115, addr 0x48). The MAX17048 (addr 0x36)
has been removed. Suited for additional I²C sensors: pressure (e.g. MS5837),
conductivity, turbidity, RTC module.

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

GPIO4, GPIO5, GPIO6, GPIO12, and GPIO15 are dedicated to on-board functions (TP5100
CE, boost enable, CN3722 /CHRG status, ADS1115 DRDY, battery divider enable
respectively). GPIO14 is spare. GPIO20 and GPIO21 on J9 are available for user
expansion.

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
- **Connector placement:** screw terminals on the bottom long edge; programming
  header (J10) and USB-C charging connector (J13) on the left short edge; battery
  connector J1 (AMASS XT30PW-F) on the right short edge; U.FL and status LED on the
  top long edge
- **Antenna keep-out:** 15 mm clear area around the module antenna region on both
  sides; no copper pour in this zone
- **ADC traces:** route GPIO0–GPIO2 shunt taps and ADS1115 AIN lines away from
  switching nodes (VLOOP boost L1/U8, LDO, USB); ground-plane stitching vias
  around the shunt resistors; keep ADS1115 (U9) within 20 mm of the shunt taps
- **VLOOP boost placement:** U8 (MT3608B) and L1 should be placed together on the
  bottom-right quadrant, away from the RF keep-out zone and ADC signal traces;
  C19/C20 within 3 mm of U8 pins; ensure 12 V trace to J4/J5 VLOOP pins is rated
  for 500 mA (≥ 0.5 mm trace width)
- **I²C routing:** ADS1115 (U9) is the only I²C device; route the I²C bus with
  4.7 kΩ pull-ups (R9, R10) close to U6; keep bus traces under 50 mm to avoid
  capacitive loading at 400 kHz Fast-mode.
- **Q2 placement:** Q2 (battery divider enable) near R8 lower leg; R26 gate bleed
  for Q2 within 2 mm of Q2 gate.
- **D8 TVS placement:** within 5 mm of C17 (CN3722 VIN filter cap) for effective
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
- **D13 battery TVS placement:** within 5 mm of J1 AMASS XT30PW-F battery connector;
  DO-214AC SMA footprint; across VBAT_RAW (J1 BAT+ pin) and GND; bidirectional —
  either orientation correct; SMAJ10CA (10 V standoff) replaces former SMAJ5.0CA
- **D5/R31 reverse-polarity MOSFET placement:** D5 (AO3407 SOT-23) in series on
  BAT+ rail, source toward J1 BAT+ and D13, drain toward VBAT system rail; R31
  (10 kΩ, 0402) from D5 gate pin to GND; place R31 within 2 mm of D5 gate pin; D5
  sits between J1 and the AP63205 buck (U1) input; protection chain order on PCB
  copper: J1 BAT+ → D13 (TVS, at terminal) → D5 S→D → VBAT rail → U1/U7
- **FB1/C23/C24 ADS1115 supply filter:** FB1 in series with +3V3 to U9 VDD; C23 and
  C24 on the U9 side of FB1, within 1 mm of U9 VDD pin
- **Q3/R30 hardware interlock:** REMOVED (Q3, R29, R30, R25 removed with TP4056)
- **50 Ω trace:** module U.FL pad to J3; calculate width for your specific
  stackup (typically 2.9–3.2 mm on standard 1.6 mm FR4 with 35 µm Cu)
- **Test points:** TP1–TP12, 1.0 mm SMD pads (TestPoint:TestPoint_Pad_1.0x1.0mm),
  DNF by default; see **Test Points** section above for full net-to-TP mapping and
  placement notes. TP13 (MAX_ALRT) and TP14 (/CHRG_SOLAR) removed.
- **MT3608B BST bypass (C_BST):** 100 nF 0402, ≥ 16 V, from MT3608B BST pin (pin 6)
  to SW node; required by MT3608B datasheet; place within 1 mm of U8 BST pin.
- **AP63205 output inductor (L2):** 4.7 µH, 1 A, 2520 or 3015 SMD shielded;
  in series between U1 SW pin and the +3V3 rail output node; place within 5 mm of U1.
- **AP63205 output cap (C_BUCK):** 10 µF 10 V X5R 0805; on +3V3 output after L2;
  in addition to existing C11/C12.
- **AP63205 FB divider:** Two 0402 resistors (R_FBH and R_FBL) connected from
  +3V3 → FB → GND; sets output voltage. Recommended values to be confirmed against
  final AP63205 variant datasheet.
- **CN3722 thermal copper pour (U7):** 10 × 10 mm solid GND pour on F.Cu under
  U7 SOP-8, connected to B.Cu via ≥ 4 thermal vias (0.6 mm drill, 1.0 mm pad);
  see **Thermal Review** section above for full rationale.
- **MT3608B SW-node copper (U8):** keep hot-loop trace (SW → L1 → C20/C22) under
  10 mm, ≥ 0.5 mm wide; no solid copper pour under L1; GND via-stitch perimeter
  around the U8/L1 island; see **Thermal Review** section for details.
- **KiCad files:** `welld.kicad_sch` / `welld.kicad_pcb` (generated by
  `generate_kicad.py`) contain all component placements and net labels. Board
  outline and footprints are placed; no traces routed — use the KiCad autorouter
  or route manually after running DRC on the net list.
- **Case:** `hardware/case/welld_case.scad` — parametric 3D-printed enclosure with
  M16 cable gland cutouts and SMA bulkhead hole on back wall for external antenna.
- **Power & measurement BOM summary:**
  U1 AP63205WU (SOT-23-6, 3.3 V synchronous buck),
  U7 CN3722 (SOP-8, MPPT solar charger, 8.4 V CV),
  U8 MT3608B (SOT-23-6, 12 V VLOOP boost),
  U12 TP5100 (SOP-8, USB-C 2S boost charger),
  L1 4.7 µH shielded CDRH4D22NP-4R7NC (VLOOP boost),
  L2 4.7 µH 1 A SMD shielded (AP63205 output inductor),
  C19 10 µF 16 V 0805 (MT3608B VIN),
  C20 22 µF 16 V 1206 (VBOOST output),
  C22 10 µF 16 V 0805 (VBOOST parallel),
  C17 10 µF 25 V 0805 (CN3722 VIN),
  C18 10 µF 16 V 0805 (CN3722 VBAT output),
  C_BST 100 nF 16 V 0402 (MT3608B BST pin),
  C_BUCK 10 µF 10 V 0805 (AP63205 output),
  R7 330 kΩ 1% 0402 (battery divider high-side),
  R8 100 kΩ 1% 0402 (battery divider low-side),
  R23 1.9 MΩ 1% 0402 (MT3608B FB high-side),
  R24 100 kΩ 1% 0402 (MT3608B FB low-side),
  R33 604 kΩ E96 1% 0402 (CN3722 CV set high-side),
  R34 100 kΩ 1% 0402 (CN3722 CV set low-side),
  R26 4.7 kΩ 0402 (Q2 gate pull-down),
  R28 100 Ω 0402 (DS18B20 VCC series),
  C21 100 nF 0402 (TVS bypass),
  C23 100 nF 0402 (ADS1115 VDD bypass),
  C24 1 µF 0402 (ADS1115 VDD bulk),
  FB1 BLM18KG601SN1D 0402 (ADS1115 supply filter),
  C_SH1 10 nF 0402, C_SH2 10 nF 0402 (shunt HF bypass),
  D5 AO3407 SOT-23 (reverse-polarity MOSFET; Vgs abs max ±12 V adequate for 8.4 V),
  R31 10 kΩ 0402 (D5 gate pull-down),
  D13 SMAJ10CA DO-214AC (battery TVS, 10 V standoff > 8.4 V),
  D14 SMAJ28CA DO-214AC (solar terminal TVS, 28 V standoff),
  D8 SMAJ28CA DO-214AC (solar inline TVS),
  D9 SMAJ3.3CA DO-214AC (loop ch1 TVS),
  D10 SMAJ3.3CA DO-214AC (loop ch2 TVS),
  D11 SMAJ13A DO-214AC (VLOOP TVS),
  D12 PRTR5V0U2X SOT-363 (1-Wire ESD),
  J1 AMASS XT30PW-F right-angle THT LCSC C601498 (battery connector),
  J13 USB4135-GF-A USB-C (USB-C charging input),
  U9 ADS1115IDGST MSOP-10,
  Q2 BSS123 SOT-23 (battery divider gate),
  TP1–TP12 SMD test point pads 1.0 mm (TestPoint:TestPoint_Pad_1.0x1.0mm; DNF).
