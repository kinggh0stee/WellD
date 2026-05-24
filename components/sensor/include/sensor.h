#pragma once
#include <stdbool.h>
#ifndef HOST_BUILD
#include "esp_err.h"
#else
#include <stdint.h>
typedef int esp_err_t;
#endif

/* reads 4-20 mA transducer via ADC; maps 4 mA → 0 m, 20 mA → MAX_DEPTH_CM/100 m;
   returns -1 if loop current is below 3.5 mA (transducer disconnected) */
float sensor_read_level(void);

/* pure level calculation from a shunt voltage in mV; exposed for unit testing */
float sensor_level_from_mv(int volt_mv);

/* pure: convert ADC mV through a resistor divider to battery volts.
   divider_ratio_x100 is the ratio * 100 (e.g. 200 = 2.00x), matching
   CONFIG_WELLD_BATT_DIVIDER_RATIO. */
float sensor_battery_from_mv(int adc_mv, int divider_ratio_x100);

/* pure: returns true when the temperature is within the DS18B20 rated range
   (-55..125 °C). Used to discard glitched readings. */
bool sensor_temp_in_range(float temp_c);

/* reads battery voltage via ADC resistor divider; returns volts, or -1 if disabled */
float sensor_read_battery_v(void);

/* reads DS18B20 on CONFIG_WELLD_DS18B20_GPIO; returns °C, or -127 if not found */
float sensor_read_temperature(void);

/* get/set the water-level offset (cm). Persisted in NVS; initialised from
   CONFIG_WELLD_SENSOR_OFFSET_CM on first boot. */
int  sensor_get_offset_cm(void);
void sensor_set_offset_cm(int offset_cm);

/* test-only: drop the in-memory offset cache so the next sensor_get_offset_cm()
   call re-reads NVS. Lets a test verify NVS round-trip without rebooting. */
void sensor_offset_cache_reset(void);

/* Initialise the shared I2C bus and register ADS1115 (0x48) only.
 * Also configures VLOOP and BATT_DIV_EN GPIO outputs and drives them LOW.
 * Must be called before any sensor_read_level() or sensor_read_battery_v(). */
esp_err_t sensor_i2c_init(void);

/* Apply temperature compensation to a raw water-level reading.
 * Corrects for water density change with temperature.
 * Returns the compensated level in metres. */
float sensor_level_temp_compensate(float level_m, float temp_c);

/* Release I2C bus driver and remove the ADS1115 DRDY ISR before deep sleep.
 * Must be called from every code path that leads to esp_deep_sleep() so the
 * I2C peripheral is not left in a partially initialised state on the next
 * wakeup and the DRDY GPIO interrupt does not fire spuriously during sleep. */
void sensor_pre_sleep_cleanup(void);

/* Self-test: exercise every peripheral and log PASS/FAIL over serial.
 * Useful for factory QA and PCB bring-up. */
void sensor_selftest(void);
