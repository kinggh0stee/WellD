#pragma once

/* reads 4-20 mA transducer via ADC; maps 4 mA → 0 m, 20 mA → MAX_DEPTH_CM/100 m */
float sensor_read_level(void);

/* reads battery voltage via ADC resistor divider; returns volts, or -1 if disabled */
float sensor_read_battery_v(void);

/* reads DS18B20 on CONFIG_WELLD_DS18B20_GPIO; returns °C, or -127 if not found */
float sensor_read_temperature(void);
