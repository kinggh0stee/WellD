const fz = require('zigbee-herdsman-converters/converters/fromZigbee');
const {numeric, access: ea} = require('zigbee-herdsman-converters/lib/exposes');
const {convertAnalogInput} = require('./lib/welld_convert');

const definition = {
    zigbeeModel: ['WellD-v1'],
    model: 'WellD-v1',
    vendor: 'WellD',
    description: 'ESP32-C6 well level monitor',
    fromZigbee: [
        {
            cluster: 'genAnalogInput',
            type: ['attributeReport', 'readResponse'],
            convert: (model, msg, publish, options, meta) =>
                convertAnalogInput({...msg, options}),
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
