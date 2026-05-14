/* Pure conversion helpers used by welld.js. Kept dependency-free so they can
   be unit-tested with `node --test` without installing zigbee-herdsman. */

const DEFAULT_BATTERY_FULL_MV  = 4200;
const DEFAULT_BATTERY_EMPTY_MV = 3000;

/* Endpoint 1: water level in metres. Negative present_value means the
   transducer loop is open — surface this to HA as null so the entity goes
   unavailable rather than reading "0 m". */
function convertLevel(presentValue) {
    if (presentValue < 0) return null;
    return parseFloat(presentValue.toFixed(2));
}

/* Endpoint 2: battery voltage + percentage. Percentage is linear between the
   user-configured full/empty thresholds and clamped to [0, 100]. */
function convertBattery(presentValue, options = {}) {
    const voltage = parseFloat(presentValue.toFixed(2));
    const fullMv  = options.battery_full_mv  ?? DEFAULT_BATTERY_FULL_MV;
    const emptyMv = options.battery_empty_mv ?? DEFAULT_BATTERY_EMPTY_MV;
    const pct = Math.min(100, Math.max(0,
        Math.round((voltage * 1000 - emptyMv) / (fullMv - emptyMv) * 100)));
    return {battery_voltage: voltage, battery: pct};
}

/* Mirrors the inline `convert` function in welld.js. Returns undefined when
   the message has no presentValue (early return) or the endpoint is unknown. */
function convertAnalogInput(msg) {
    if (!msg || !msg.data || !Object.prototype.hasOwnProperty.call(msg.data, 'presentValue')) {
        return undefined;
    }
    const ep = msg.endpoint && msg.endpoint.ID;
    if (ep === 1) return {water_level: convertLevel(msg.data.presentValue)};
    if (ep === 2) return convertBattery(msg.data.presentValue, msg.options || {});
    return undefined;
}

module.exports = {
    convertLevel,
    convertBattery,
    convertAnalogInput,
    DEFAULT_BATTERY_FULL_MV,
    DEFAULT_BATTERY_EMPTY_MV,
};
