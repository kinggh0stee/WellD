/* Pure math helpers from the sensor component. No ESP-IDF or hardware
 * dependencies — safe to compile and exercise from a host harness.
 *
 * On ESP-IDF, sdkconfig.h supplies CONFIG_WELLD_SENSOR_SHUNT_MILLIOHMS
 * and CONFIG_WELLD_SENSOR_MAX_DEPTH_CM. The host test harness provides
 * its own sdkconfig.h stub with the same defaults from
 * components/sensor/Kconfig. */

#include "sensor.h"
#include "sdkconfig.h"
#include <assert.h>
#include <stdint.h>

#define CURRENT_MIN_UA  4000   /* 4 mA  = 0 % depth */
#define CURRENT_MAX_UA  20000  /* 20 mA = 100 % depth */

float sensor_level_from_mv(int volt_mv)
{
    _Static_assert(CONFIG_WELLD_SENSOR_SHUNT_MILLIOHMS > 0,
                   "shunt resistance must be positive");
    _Static_assert(CONFIG_WELLD_SENSOR_MAX_DEPTH_CM > 0,
                   "max depth must be positive");
    /* I (µA) = V (mV) * 1 000 000 / R (mΩ) */
    int current_ua = (int)(((int64_t)volt_mv * 1000000LL) /
                            CONFIG_WELLD_SENSOR_SHUNT_MILLIOHMS);
    if (current_ua < 3500)   /* < 3.5 mA → loop open, transducer disconnected */
        return -1.0f;

    float ratio = (float)(current_ua - CURRENT_MIN_UA) /
                  (float)(CURRENT_MAX_UA - CURRENT_MIN_UA);
    if (ratio < 0.0f) ratio = 0.0f;
    if (ratio > 1.0f) ratio = 1.0f;
    return ratio * (CONFIG_WELLD_SENSOR_MAX_DEPTH_CM / 100.0f);
}

float sensor_battery_from_mv(int adc_mv, int divider_ratio_x100)
{
    assert(divider_ratio_x100 > 0);
    return (float)adc_mv * (float)divider_ratio_x100 / 100000.0f;
}

bool sensor_temp_in_range(float temp_c)
{
    return temp_c >= -55.0f && temp_c <= 125.0f;
}

/* The transducer measures pressure p = rho * g * h, and the 4-20 mA -> metres
 * scaling assumes 20 °C water. With rho(T) ~= rho20 * (1 - beta * (T - 20))
 * (beta = volumetric expansion coefficient, ~207 ppm/°C near 20 °C):
 *
 *     h_true = p / (rho(T) * g) = h_raw * rho20 / rho(T)
 *            = h_raw / (1 - beta * (T - 20))
 *
 * Warm water is less dense, so a given column presses less and reads LOW:
 * the factor is > 1 above 20 °C and < 1 below it. */
float sensor_temp_level_factor(float temp_c, int ppm_per_c)
{
    float denom = 1.0f - (float)ppm_per_c * 1e-6f * (temp_c - 20.0f);
    if (!(denom > 0.0f)) return 1.0f;   /* also rejects NaN */
    return 1.0f / denom;
}
