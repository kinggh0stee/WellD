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

/* Density of air-free pure water relative to its maximum (~3.98 °C), from
 * Tanaka et al., Metrologia 38 (2001) 301 — the CIPM formula, within a few
 * ppm of the tables over 0–40 °C. Its a5 (999.97495 kg/m3) cancels in the
 * ratio below. */
static float water_density_rel(float t)
{
    const float a1 = -3.983035f, a2 = 301.797f, a3 = 522528.9f, a4 = 69.34881f;
    float d = t + a1;
    return 1.0f - (d * d) * (t + a2) / (a3 * (t + a4));
}

/* The transducer measures pressure p = rho * g * h, and its metre scale
 * assumes water at ref_temp_c — 4 °C for the conventional metre of water
 * column (9.80665 kPa, 1000 kg/m3), which nearly every datasheet uses:
 *
 *     h_true = p / (rho(T) * g) = h_raw * rho(ref) / rho(T)
 *
 * Water away from ~4 °C is less dense, so a given column presses less and
 * reads LOW: the factor is >= 1 for a 4 °C reference (0.03 % at 10 °C,
 * 0.43 % at 30 °C). Outside 0–40 °C (ice, or a probe out of the water) the
 * correction is skipped. */
float sensor_temp_level_factor(float temp_c, int ref_temp_c)
{
    if (!(temp_c >= 0.0f && temp_c <= 40.0f)) return 1.0f;   /* also rejects NaN */
    if (ref_temp_c < 0 || ref_temp_c > 40) return 1.0f;
    return water_density_rel((float)ref_temp_c) / water_density_rel(temp_c);
}
