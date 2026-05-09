const {numeric, access: ea} = require('zigbee-herdsman-converters/lib/exposes');

const definition = {
    zigbeeModel: ['WellD-v1'],
    model: 'WellD-v1',
    vendor: 'WellD',
    description: 'ESP32-C6 well level monitor',
    fromZigbee: [{
        cluster: 'genAnalogInput',
        type: ['attributeReport', 'readResponse'],
        convert: (model, msg, publish, options, meta) => {
            if (msg.data.hasOwnProperty('presentValue')) {
                return {water_level: parseFloat(msg.data.presentValue.toFixed(2))};
            }
        },
    }],
    toZigbee: [],
    exposes: [
        numeric('water_level', ea.STATE)
            .withUnit('m')
            .withDescription('Water level in metres'),
    ],
};

module.exports = definition;
