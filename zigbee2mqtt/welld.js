const fz = require('zigbee-herdsman-converters/converters/fromZigbee');
const {numeric, access: ea} = require('zigbee-herdsman-converters/lib/exposes');

const definition = {
    zigbeeModel: ['WellD-v1'],
    model: 'WellD-v1',
    vendor: 'WellD',
    description: 'ESP32-C6 well level monitor',
    fromZigbee: [
        {
            cluster: 'genAnalogInput',
            type: ['attributeReport', 'readResponse'],
            convert: (model, msg, publish, options, meta) => {
                if (!msg.data.hasOwnProperty('presentValue')) return;
                const ep = msg.endpoint.ID;
                if (ep === 1) {
                    const val = msg.data.presentValue;
                    /* val < 0 means open-loop / transducer disconnected;
                       return null so HA marks the entity as unavailable */
                    return {water_level: val < 0 ? null : parseFloat(val.toFixed(2))};
                }
                if (ep === 2) {
                    const voltage = parseFloat(msg.data.presentValue.toFixed(2));
                    const fullMv  = (options.battery_full_mv  ?? 4200);
                    const emptyMv = (options.battery_empty_mv ?? 3000);
                    const pct = Math.min(100, Math.max(0,
                        Math.round((voltage * 1000 - emptyMv) / (fullMv - emptyMv) * 100)));
                    return {battery_voltage: voltage, battery: pct};
                }
            },
        },
        fz.temperature,
    ],
    toZigbee: [],
    ota: true,
    exposes: [
        numeric('water_level', ea.STATE)
            .withUnit('m')
            .withDescription('Water level in metres'),
        numeric('battery_voltage', ea.STATE)
            .withUnit('V')
            .withDescription('Battery voltage'),
        numeric('battery', ea.STATE)
            .withUnit('%')
            .withDescription('Battery level (requires battery_full_mv / battery_empty_mv options for accurate readings)'),
        numeric('temperature', ea.STATE)
            .withUnit('°C')
            .withDescription('Water temperature'),
    ],
    options: [
        numeric('battery_full_mv', ea.SET)
            .withDescription('Voltage (mV) at 100 % battery. Default 4200 (LiPo). Set to 4500 for 3×AA alkaline.'),
        numeric('battery_empty_mv', ea.SET)
            .withDescription('Voltage (mV) at 0 % battery. Default 3000.'),
    ],
};

module.exports = definition;
