#pragma once

/**
 * Read the 4-20 mA pressure transducer via ADC and return the water level in metres.
 * Maps 4 mA → 0.00 m  and  20 mA → CONFIG_WELLD_SENSOR_MAX_DEPTH_CM / 100.
 */
float sensor_read_level(void);
