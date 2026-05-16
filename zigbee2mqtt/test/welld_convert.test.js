const test = require('node:test');
const assert = require('node:assert/strict');

const {
    convertLevel,
    convertBattery,
    convertRate,
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
    /* 3.6 V with default 3.0 V empty / 4.2 V full → 50 % */
    const out = convertBattery(3.6);
    assert.equal(out.battery_voltage, 3.6);
    assert.equal(out.battery, 50);
});

test('battery percentage clamps to 0 below empty threshold', () => {
    const out = convertBattery(2.5);
    assert.equal(out.battery, 0);
});

test('battery percentage clamps to 100 above full threshold', () => {
    const out = convertBattery(5.0);
    assert.equal(out.battery, 100);
});

test('battery percentage honours custom full/empty options', () => {
    /* 3×AA alkaline: empty 3.0 V (default), full 4.5 V */
    const out = convertBattery(3.75, {battery_full_mv: 4500});
    assert.equal(out.battery, 50);
});

test('battery percentage rounds to nearest integer', () => {
    /* 3.61 V → 50.83…% → rounds to 51 */
    const out = convertBattery(3.61);
    assert.equal(out.battery, 51);
});

test('battery defaults match the firmware Kconfig defaults', () => {
    /* If these drift, the JS converter will silently misreport %. */
    assert.equal(DEFAULT_BATTERY_FULL_MV, 4200);
    assert.equal(DEFAULT_BATTERY_EMPTY_MV, 3000);
});

test('convertBattery returns undefined when full and empty thresholds are equal', () => {
    /* Prevents division by zero when a user misconfigures equal thresholds. */
    assert.equal(convertBattery(3.6, {battery_full_mv: 3600, battery_empty_mv: 3600}), undefined);
});

test('convertBattery returns undefined for null/NaN/Infinity', () => {
    assert.equal(convertBattery(null), undefined);
    assert.equal(convertBattery(NaN), undefined);
    assert.equal(convertBattery(Infinity), undefined);
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
        data: {presentValue: 3.6},
    });
    assert.equal(result.battery_voltage, 3.6);
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
