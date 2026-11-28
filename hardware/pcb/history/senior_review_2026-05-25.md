# Senior Reviewer Report — 2026-05-25

**Verdict: BLOCKED** — 4 CRITICAL issues found. Resolve before tape-out.

---

## CRITICAL (must fix before layout)

### 1. AP63205 FB divider resistors (R_FBH / R_FBL) missing from schematic
The AP63205WU output voltage is set entirely by an external resistor divider on the FB pin. These components exist in the design notes but have no schematic symbol or BOM row. Without them, the FB pin floats, the output swings to rail, and the ESP32 and all 3.3V ICs are destroyed on first power-on.

**Fix:** Add R_FBH = 560kΩ and R_FBL = 124kΩ in the power schematic (VOUT→R_FBH→FB→R_FBL→GND). See `kicad_guide_eli5.md` Fix 1.

---

### 2. CN3722 CV setpoint overcharges 2S Li-ion pack
R33 = 604kΩ → Vchg = 8.48V, which is 80mV above the 8.40V Li-ion maximum. Every solar charge cycle terminates at an unsafe voltage.

**Fix applied in schematic:** R33 changed to **590kΩ** → Vchg = **8.31V** (safe, 90mV below limit). ✅

---

### 3. ADS1115 ALERT/DRDY has no external pull-up
DRDY is open-drain. Only the ESP32's internal ~45kΩ weak pull-up is present. The ADS1115 datasheet requires an external pull-up. This is the confirmed root cause of the DRDY edge-loss bug fixed in firmware commit `adf7101` — the hardware fault was never corrected.

**Fix:** Add R_DRDY = 4.7kΩ from ADS_DRDY net to +3V3. See `kicad_guide_eli5.md` Fix 2.

---

### 4. MT3608B C_BST bootstrap capacitor unresolved
The MT3608B datasheet mandates a 100nF cap from BST pin (pin 6) to SW node. C_BST appears in the BOM but its schematic net connection is ambiguous. C25 may be it but is documented as removed. Without C_BST, the high-side gate driver fails at low VBAT.

**Fix:** Verify or add C_BST = 100nF from U8 BST→SW. See `kicad_guide_eli5.md` Fix 3.

---

## WARNINGS (fix before production, acceptable for prototype)

| # | Issue | Recommendation |
|---|-------|----------------|
| 5 | D8 SMAJ28CA standoff equals CN3722 VIN abs max — zero clamp margin | Change to SMAJ24CA or SMAJ26CA for actual protection headroom |
| 6 | L1 saturation current 1.0A vs MT3608B 4A peak switch limit | Acceptable for 20mA load; add inrush note to assembly instructions |
| 7 | C_BUCK (AP63205 primary output cap) missing from schematic | Add 10µF 0805 on +3V3 after L2. See `kicad_guide_eli5.md` Fix 4 |
| 8 | C25 (100nF) in schematic but documented as removed | Resolve: either remove it or confirm it is C_BST with correct net connection |
| 9 | C16 (10µF) in schematic with no BOM row or documentation | Identify its net and add a BOM row, or remove it |
| 10 | C4/C6 10µF on ADC tap may slow ADS1115 settling between channels | Add inter-channel settling delay ≥5ms in firmware; or reduce to 1µF |
| 11 | CN3722 has no EN pin; co-charging with TP5100 pushes to 8.31V CV | Acceptable now that CV is fixed to 8.31V; monitor combined charge current |
| 12 | R36 (CE pull-up to VUSB 5V) — GPIO4 at 3.3V cannot assert CE HIGH against 5V pull-up | By design (VUSB presence auto-enables charging); update firmware comment to say "GPIO4 LOW disables charging" not "HIGH enables" |
| 15 | R32 (DS18B20 33Ω) is DNF — PRTR5V0U2X clamp overshoots GPIO abs max by 0.2V on ESD | Change R32 from DNF to populate for field installations with cable runs |

---

## Items Already Correct

- D13 SMAJ10CA (10V standoff) correctly replaces SMAJ5.0CA for 2S battery range ✅
- D9/D10 SMAJ3.3CA (3.3V standoff) correctly replaces SMAJ5.0CA for 4-20mA terminals ✅
- 2S battery voltage range (6.0–8.4V) correctly handled throughout ✅
- ADS1115 PGA ±2.048V correctly covers 4-20mA shunt voltage range (0.4–2.0V) ✅
- R7/R8 divider (330kΩ/100kΩ) correctly scales 8.4V to <2.0V for ADS1115 ✅
- D5 AO3407 Vgs headroom correct for 2S voltage range ✅
- Dual-charger (CN3722 + TP5100) coexistence analysis is valid at corrected CV voltage ✅
