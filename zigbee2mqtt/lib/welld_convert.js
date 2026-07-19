/* Pure conversion helpers used by welld.js. Kept dependency-free so they can
   be unit-tested with `node --test` without installing zigbee-herdsman. */

const DEFAULT_BATTERY_FULL_MV  = 4200;   /* 1S 18650 */
const DEFAULT_BATTERY_EMPTY_MV = 3000;

/* ZCL AnalogInput presentValue must decode to a plain finite number. Anything
   else (strings, booleans, NaN, ±Infinity, missing) is a malformed report —
   reject it instead of letting `.toFixed()` throw inside the fromZigbee
   handler. Note the global `isFinite()` is NOT safe here: it coerces
   (isFinite("2.5") === true), so use Number.isFinite on the raw value. */
function finitePresentValue(presentValue) {
    if (typeof presentValue !== 'number' || !Number.isFinite(presentValue)) return undefined;
    return presentValue;
}

/* Device options may arrive from YAML as strings ("4200"); coerce, and fall
   back to the default for anything missing or non-finite. */
function optionMv(value, fallback) {
    const n = Number(value);
    return Number.isFinite(n) ? n : fallback;
}

/* Endpoint 1: water level in metres. Negative present_value means the
   transducer loop is open — surface this to HA as null so the entity goes
   unavailable rather than reading "0 m". */
function convertLevel(presentValue) {
    const value = finitePresentValue(presentValue);
    if (value === undefined) return undefined;
    if (value < 0) return null;
    return parseFloat(value.toFixed(2));
}

/* Endpoint 2: battery voltage + percentage. Percentage is linear between the
   user-configured full/empty thresholds and clamped to [0, 100]. A
   misconfigured threshold pair (full <= empty) makes the percentage
   incomputable, but the voltage reading is still valid — report it alone. */
function convertBattery(presentValue, options = {}) {
    const value = finitePresentValue(presentValue);
    if (value === undefined) return undefined;
    const voltage = parseFloat(value.toFixed(2));
    const fullMv  = optionMv(options.battery_full_mv,  DEFAULT_BATTERY_FULL_MV);
    const emptyMv = optionMv(options.battery_empty_mv, DEFAULT_BATTERY_EMPTY_MV);
    if (fullMv <= emptyMv) return {battery_voltage: voltage};
    const pct = Math.min(100, Math.max(0,
        Math.round((voltage * 1000 - emptyMv) / (fullMv - emptyMv) * 100)));
    return {battery_voltage: voltage, battery: pct};
}

/* Endpoint 4: water-level rate of change in cm/hour, signed. Positive =
   level rising (well recovering), negative = level falling (draw-down).
   Rounded to one decimal for readability. */
function convertRate(presentValue) {
    const value = finitePresentValue(presentValue);
    if (value === undefined) return undefined;
    return parseFloat(value.toFixed(1));
}

/* Endpoint 5: Zigbee failure counter (0–255 float). Truncated to integer. */
function convertFails(presentValue) {
    const value = finitePresentValue(presentValue);
    if (value === undefined) return undefined;
    return Math.min(255, Math.max(0, Math.floor(value)));
}

/* Endpoint 6: device-side Link Quality (LQI), 1–255 integer — the device's
   own view of its link, reported as an AnalogInput attribute. Published as
   `device_lqi`, NOT `linkquality`: Zigbee2MQTT overwrites `linkquality` on
   every message with the coordinator-side radio LQI, so publishing under
   that key would be permanently shadowed.

   0 means "unknown / not measured" and is NOT published: the firmware sends
   0 when no parent entry is found in its neighbor table (and firmware
   <= 1.0.2 always sent 0), and a genuine LQI of 0 cannot coexist with a
   successfully delivered report frame. Skipping 0 keeps HA from showing a
   permanent dead-link sensor; real values 1-255 flow through unchanged. */
function convertLqi(presentValue) {
    const value = finitePresentValue(presentValue);
    if (value === undefined) return undefined;
    const lqi = Math.min(255, Math.max(0, Math.round(value)));
    if (lqi === 0) return undefined;
    return lqi;
}

/* Endpoint 7: Solar charging state, 0/1 boolean. */
function convertSolar(presentValue) {
    const value = finitePresentValue(presentValue);
    if (value === undefined) return undefined;
    return value >= 0.5;
}

/* Mirrors the inline `convert` function in welld.js. Returns undefined when
   the message has no presentValue (early return) or the endpoint is unknown. */
function convertAnalogInput(msg) {
    if (!msg || !msg.data || !Object.prototype.hasOwnProperty.call(msg.data, 'presentValue')) {
        return undefined;
    }
    const ep = msg.endpoint && msg.endpoint.ID;
    if (ep === 1) {
        const level = convertLevel(msg.data.presentValue);
        if (level === undefined) return undefined;
        return {water_level: level};
    }
    if (ep === 2) return convertBattery(msg.data.presentValue, msg.options || {});
    if (ep === 4) {
        const rate = convertRate(msg.data.presentValue);
        if (rate === undefined) return undefined;
        return {water_level_rate: rate};
    }
    if (ep === 5) {
        const fails = convertFails(msg.data.presentValue);
        if (fails === undefined) return undefined;
        return {zb_fails: fails};
    }
    if (ep === 6) {
        const lqi = convertLqi(msg.data.presentValue);
        if (lqi === undefined) return undefined;
        return {device_lqi: lqi};
    }
    if (ep === 7) {
        const solar = convertSolar(msg.data.presentValue);
        if (solar === undefined) return undefined;
        return {solar_charging: solar};
    }
    return undefined;
}

module.exports = {
    convertLevel,
    convertBattery,
    convertRate,
    convertFails,
    convertLqi,
    convertSolar,
    convertAnalogInput,
    DEFAULT_BATTERY_FULL_MV,
    DEFAULT_BATTERY_EMPTY_MV,
};
