const test = require('node:test');
const assert = require('node:assert/strict');

const {
    convertLevel,
    convertBattery,
    convertRate,
    convertFails,
    convertLqi,
    convertSolar,
    convertAnalogInput,
    DEFAULT_BATTERY_FULL_MV,
    DEFAULT_BATTERY_EMPTY_MV,
} = require('../lib/welld_convert');

/* convertLevel ------------------------------------------------------------ */

test('water level rounds to 2 decimal places', () => {
    assert.equal(convertLevel(1.23456), 1.23);
    assert.equal(convertLevel(0), 0);
});

test('water level negative → null (open-loop transducer)', () => {
    assert.equal(convertLevel(-1), null);
    assert.equal(convertLevel(-0.0001), null);
});

test('convertLevel returns undefined for null/NaN/Infinity', () => {
    assert.equal(convertLevel(null), undefined);
    assert.equal(convertLevel(NaN), undefined);
    assert.equal(convertLevel(Infinity), undefined);
});

/* convertBattery ---------------------------------------------------------- */

test('battery percentage uses defaults when options omitted', () => {
    /* 7.2 V with default 6.0 V empty / 8.4 V full → 50 % */
    const out = convertBattery(7.2);
    assert.equal(out.battery_voltage, 7.2);
    assert.equal(out.battery, 50);
});

test('battery percentage clamps to 0 below empty threshold', () => {
    const out = convertBattery(5.5);
    assert.equal(out.battery, 0);
});

test('battery percentage clamps to 100 above full threshold', () => {
    const out = convertBattery(9.0);
    assert.equal(out.battery, 100);
});

test('battery percentage honours custom full/empty options', () => {
    /* Custom 2S range: empty 6.5 V, full 8.0 V → midpoint 7.25 V → 50 % */
    const out = convertBattery(7.25, {battery_full_mv: 8000, battery_empty_mv: 6500});
    assert.equal(out.battery, 50);
});

test('battery percentage rounds to nearest integer', () => {
    /* 7.21 V with defaults 6.0 V empty / 8.4 V full → (7.21-6.0)/(8.4-6.0)*100
       = 1.21/2.4*100 = 50.416…% → rounds to 50 */
    const out = convertBattery(7.21);
    assert.equal(out.battery, 50);
});

test('battery defaults match the firmware Kconfig defaults', () => {
    /* If these drift, the JS converter will silently misreport %. */
    assert.equal(DEFAULT_BATTERY_FULL_MV, 8400);
    assert.equal(DEFAULT_BATTERY_EMPTY_MV, 6000);
});

test('equal thresholds: voltage still reported, percentage omitted (no division by zero)', () => {
    /* The voltage reading is valid even when the % is incomputable. */
    assert.deepEqual(convertBattery(7.2, {battery_full_mv: 7200, battery_empty_mv: 7200}),
        {battery_voltage: 7.2});
});

test('inverted thresholds (full < empty): voltage still reported, percentage omitted', () => {
    assert.deepEqual(convertBattery(7.2, {battery_full_mv: 6000, battery_empty_mv: 8400}),
        {battery_voltage: 7.2});
});

test('battery options arriving as strings (YAML config) are coerced', () => {
    const out = convertBattery(7.25, {battery_full_mv: '8000', battery_empty_mv: '6500'});
    assert.equal(out.battery, 50);
});

test('non-finite battery options fall back to defaults instead of publishing NaN', () => {
    const out = convertBattery(7.2, {battery_full_mv: NaN, battery_empty_mv: 'garbage'});
    assert.equal(out.battery, 50);
    assert.ok(Number.isFinite(out.battery));
});

test('a single provided battery option combines with the other default', () => {
    /* full 8000 (custom), empty 6000 (default) → 7.0 V = 50 % */
    const out = convertBattery(7.0, {battery_full_mv: 8000});
    assert.equal(out.battery, 50);
});

test('convertBattery returns undefined for null/NaN/Infinity', () => {
    assert.equal(convertBattery(null), undefined);
    assert.equal(convertBattery(NaN), undefined);
    assert.equal(convertBattery(Infinity), undefined);
});

test('2S1P 18650 battery at full charge (8400 mV) reports 100 %', () => {
    const out = convertBattery(8.4);
    assert.equal(out.battery_voltage, 8.4);
    assert.equal(out.battery, 100);
});

test('2S1P 18650 battery at midpoint (7200 mV) reports 50 %', () => {
    /* (7200 - 6000) / (8400 - 6000) * 100 = 50 % */
    const out = convertBattery(7.2);
    assert.equal(out.battery_voltage, 7.2);
    assert.equal(out.battery, 50);
});

test('2S1P 18650 battery at minimum safe discharge (6000 mV) reports 0 %', () => {
    const out = convertBattery(6.0);
    assert.equal(out.battery_voltage, 6);
    assert.equal(out.battery, 0);
});

/* convertAnalogInput ------------------------------------------------------ */

test('endpoint 1 dispatches to water level', () => {
    const result = convertAnalogInput({
        endpoint: {ID: 1},
        data: {presentValue: 2.5},
    });
    assert.deepEqual(result, {water_level: 2.5});
});

test('endpoint 1 with negative present value reports null', () => {
    const result = convertAnalogInput({
        endpoint: {ID: 1},
        data: {presentValue: -1},
    });
    assert.deepEqual(result, {water_level: null});
});

test('endpoint 2 dispatches to battery converter', () => {
    const result = convertAnalogInput({
        endpoint: {ID: 2},
        data: {presentValue: 7.2},
    });
    assert.equal(result.battery_voltage, 7.2);
    assert.equal(result.battery, 50);
});

/* convertRate ------------------------------------------------------------- */

test('water level rate rounds to 1 decimal', () => {
    assert.equal(convertRate(12.345), 12.3);
    assert.equal(convertRate(-12.345), -12.3);
    assert.equal(convertRate(0), 0);
});

test('convertRate returns undefined for null/NaN/Infinity', () => {
    assert.equal(convertRate(null), undefined);
    assert.equal(convertRate(NaN), undefined);
    assert.equal(convertRate(Infinity), undefined);
});

test('endpoint 4 dispatches to rate converter', () => {
    const result = convertAnalogInput({
        endpoint: {ID: 4},
        data: {presentValue: 25.0},
    });
    assert.deepEqual(result, {water_level_rate: 25.0});
});

test('endpoint 4 with falling rate reports negative', () => {
    const result = convertAnalogInput({
        endpoint: {ID: 4},
        data: {presentValue: -42.5},
    });
    assert.deepEqual(result, {water_level_rate: -42.5});
});

test('missing presentValue returns undefined', () => {
    const result = convertAnalogInput({
        endpoint: {ID: 1},
        data: {},
    });
    assert.equal(result, undefined);
});

test('unknown endpoint returns undefined', () => {
    const result = convertAnalogInput({
        endpoint: {ID: 99},
        data: {presentValue: 1.0},
    });
    assert.equal(result, undefined);
});

test('endpoint 3 (temperature cluster) is not handled by convertAnalogInput', () => {
    /* EP3 uses ZCL cluster 0x0402 decoded by Z2M itself, not a custom AnalogInput path.
     * convertAnalogInput must leave it alone and return undefined. */
    const result = convertAnalogInput({
        endpoint: {ID: 3},
        data: {presentValue: 25.0},
    });
    assert.equal(result, undefined);
});

/* convertFails ------------------------------------------------------------- */

test('convertFails truncates float to integer', () => {
    assert.equal(convertFails(3.9), 3);
    assert.equal(convertFails(0.0), 0);
});

test('convertFails clamps to [0, 255]', () => {
    assert.equal(convertFails(-1), 0);
    assert.equal(convertFails(300), 255);
});

test('convertFails returns undefined for null/NaN/Infinity', () => {
    assert.equal(convertFails(null), undefined);
    assert.equal(convertFails(NaN), undefined);
    assert.equal(convertFails(Infinity), undefined);
});

test('endpoint 5 dispatches to failure counter', () => {
    const result = convertAnalogInput({
        endpoint: {ID: 5},
        data: {presentValue: 3.0},
    });
    assert.deepEqual(result, {zb_fails: 3});
});

test('endpoint 5 with zero failures reports 0', () => {
    const result = convertAnalogInput({
        endpoint: {ID: 5},
        data: {presentValue: 0.0},
    });
    assert.deepEqual(result, {zb_fails: 0});
});

/* convertLqi --------------------------------------------------------------- */

test('convertLqi rounds float to integer', () => {
    assert.equal(convertLqi(200.7), 201);
    assert.equal(convertLqi(1.0), 1);
});

test('convertLqi clamps to [1, 255]; 0 and below-zero are unknown', () => {
    assert.equal(convertLqi(300), 255);
    /* 0 = "unknown / not measured" (current firmware stub) — never published,
       so HA cannot show a permanent dead-link sensor. Negative clamps to 0
       and is likewise suppressed. */
    assert.equal(convertLqi(0.0), undefined);
    assert.equal(convertLqi(-10), undefined);
    assert.equal(convertLqi(0.4), undefined);
});

test('endpoint 6 with stub zero LQI is not published', () => {
    const result = convertAnalogInput({
        endpoint: {ID: 6},
        data: {presentValue: 0.0},
    });
    assert.equal(result, undefined);
});

test('endpoint 6 dispatches to device-side LQI', () => {
    const result = convertAnalogInput({
        endpoint: {ID: 6},
        data: {presentValue: 200.0},
    });
    assert.deepEqual(result, {device_lqi: 200});
});

test('endpoint 6 must not publish under the linkquality key (Z2M shadows it)', () => {
    /* Zigbee2MQTT overwrites `linkquality` on every message with the
       coordinator-side radio LQI, so the device-side value would be
       permanently shadowed if published under that key. */
    const result = convertAnalogInput({
        endpoint: {ID: 6},
        data: {presentValue: 180.0},
    });
    assert.ok(!('linkquality' in result));
    assert.equal(result.device_lqi, 180);
});

/* convertSolar ------------------------------------------------------------- */

test('convertSolar returns boolean', () => {
    assert.equal(convertSolar(1.0), true);
    assert.equal(convertSolar(0.0), false);
    assert.equal(convertSolar(0.5), true);
    assert.equal(convertSolar(0.4), false);
    assert.equal(convertSolar(-1.0), false);
});

test('endpoint 7 dispatches to solar charging', () => {
    const result = convertAnalogInput({
        endpoint: {ID: 7},
        data: {presentValue: 1.0},
    });
    assert.deepEqual(result, {solar_charging: true});
});

test('endpoint 7 with zero reports solar_charging false', () => {
    const result = convertAnalogInput({
        endpoint: {ID: 7},
        data: {presentValue: 0.0},
    });
    assert.deepEqual(result, {solar_charging: false});
});

/* Malformed message shapes — must never throw ----------------------------- */

test('non-numeric presentValue types are rejected without throwing', () => {
    /* The global isFinite() coerces ("2.5", true, "" all pass it); a naive
       implementation then throws in .toFixed(). Guard against regressions. */
    for (const bad of ['2.5', '', true, false, {}, [], [1]]) {
        assert.equal(convertLevel(bad), undefined);
        assert.equal(convertBattery(bad), undefined);
        assert.equal(convertRate(bad), undefined);
        assert.equal(convertFails(bad), undefined);
        assert.equal(convertLqi(bad), undefined);
        assert.equal(convertSolar(bad), undefined);
    }
});

test('convertAnalogInput tolerates malformed message shapes', () => {
    assert.equal(convertAnalogInput(undefined), undefined);
    assert.equal(convertAnalogInput(null), undefined);
    assert.equal(convertAnalogInput({}), undefined);
    assert.equal(convertAnalogInput({data: null}), undefined);
    assert.equal(convertAnalogInput({endpoint: {ID: 1}}), undefined);
    /* presentValue present but endpoint missing / malformed */
    assert.equal(convertAnalogInput({data: {presentValue: 1.0}}), undefined);
    assert.equal(convertAnalogInput({endpoint: {}, data: {presentValue: 1.0}}), undefined);
    assert.equal(convertAnalogInput({endpoint: null, data: {presentValue: 1.0}}), undefined);
});

test('convertAnalogInput rejects string presentValue without throwing', () => {
    assert.equal(convertAnalogInput({endpoint: {ID: 1}, data: {presentValue: '2.5'}}), undefined);
    assert.equal(convertAnalogInput({endpoint: {ID: 2}, data: {presentValue: '7.2'}}), undefined);
});

test('endpoint ID as string does not dispatch (strict endpoint matching)', () => {
    const result = convertAnalogInput({
        endpoint: {ID: '1'},
        data: {presentValue: 2.5},
    });
    assert.equal(result, undefined);
});

/* Store-and-forward burst -------------------------------------------------- */

test('store-and-forward burst: sequential EP1 reports convert independently', () => {
    /* After a send failure the firmware burst-reports up to 8 buffered
       readings, oldest first, as separate attribute reports on the same EP.
       Each report must convert on its own, including a -1 open-loop reading
       buffered mid-outage. */
    const burst = [3.10, 3.05, -1.0, 2.95];
    const results = burst.map((presentValue) => convertAnalogInput({
        endpoint: {ID: 1},
        data: {presentValue},
    }));
    assert.deepEqual(results, [
        {water_level: 3.1},
        {water_level: 3.05},
        {water_level: null},
        {water_level: 2.95},
    ]);
});

test('store-and-forward burst: mixed-endpoint reports stay isolated', () => {
    /* A full wakeup report is one frame per EP; converting them in sequence
       must not leak state between endpoints. */
    const frames = [
        {endpoint: {ID: 1}, data: {presentValue: 2.5}},
        {endpoint: {ID: 2}, data: {presentValue: 7.2}},
        {endpoint: {ID: 4}, data: {presentValue: -3.2}},
        {endpoint: {ID: 5}, data: {presentValue: 1.0}},
        {endpoint: {ID: 6}, data: {presentValue: 180.0}},
        {endpoint: {ID: 7}, data: {presentValue: 0.0}},
    ];
    const results = frames.map(convertAnalogInput);
    assert.deepEqual(results, [
        {water_level: 2.5},
        {battery_voltage: 7.2, battery: 50},
        {water_level_rate: -3.2},
        {zb_fails: 1},
        {device_lqi: 180},
        {solar_charging: false},
    ]);
});
