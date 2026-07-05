const fz = require('zigbee-herdsman-converters/converters/fromZigbee');
const {numeric, binary, access: ea} = require('zigbee-herdsman-converters/lib/exposes');
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
        numeric('water_level_rate', ea.STATE)
            .withUnit('cm/h')
            .withDescription('Water level rate of change. Positive = rising (recovering), negative = falling (draw-down). Only reported once two valid readings are in.'),
        numeric('zb_fails', ea.STATE)
            .withValueMin(0).withValueMax(255)
            .withDescription('Consecutive Zigbee send failures since last success. 0 = healthy. Warnings at 3+, auto-rejoin at 5.'),
        numeric('device_lqi', ea.STATE)
            .withValueMin(0).withValueMax(255)
            .withDescription('Device-side Zigbee link quality (LQI), 0-255, as measured by the device itself. Distinct from the built-in linkquality, which is the coordinator-side radio LQI. Higher is better.'),
        binary('solar_charging', ea.STATE, true, false)
            .withDescription('Solar charging active. true = charging, false = not charging.'),
    ],
    options: [
        numeric('battery_full_mv', ea.SET)
            .withValueMin(5000).withValueMax(10000)
            .withDescription('Voltage (mV) at 100 % battery. Default 8400 (2S1P 18650 Li-ion full charge).'),
        numeric('battery_empty_mv', ea.SET)
            .withValueMin(5000).withValueMax(10000)
            .withDescription('Voltage (mV) at 0 % battery. Default 6000 (2S1P 18650 minimum safe discharge).'),
    ],
};

module.exports = definition;
