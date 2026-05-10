#pragma once

/* reads 4-20 mA transducer via ADC; maps 4 mA → 0 m, 20 mA → MAX_DEPTH_CM/100 m;
   returns -1 if loop current is below 3.5 mA (transducer disconnected) */
float sensor_read_level(void);

/* pure level calculation from a shunt voltage in mV; exposed for unit testing */
float sensor_level_from_mv(int volt_mv);

/* reads battery voltage via ADC resistor divider; returns volts, or -1 if disabled */
float sensor_read_battery_v(void);

/* reads DS18B20 on CONFIG_WELLD_DS18B20_GPIO; returns °C, or -127 if not found */
float sensor_read_temperature(void);
