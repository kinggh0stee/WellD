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
                if (ep === 1) return {water_level:    parseFloat(msg.data.presentValue.toFixed(2))};
                if (ep === 2) return {battery_voltage: parseFloat(msg.data.presentValue.toFixed(2))};
            },
        },
        fz.temperature,  /* handles ZCL 0x0402 Temperature Measurement on endpoint 3 */
    ],
    toZigbee: [],
    ota: false,
    exposes: [
        numeric('water_level', ea.STATE)
            .withUnit('m')
            .withDescription('Water level in metres'),
        numeric('battery_voltage', ea.STATE)
            .withUnit('V')
            .withDescription('Battery voltage'),
        numeric('temperature', ea.STATE)
            .withUnit('°C')
            .withDescription('Water temperature'),
    ],
};

module.exports = definition;
