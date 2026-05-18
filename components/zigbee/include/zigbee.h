#pragma once
#include <stdbool.h>

/* Joins a Zigbee HA network and reports all readings:
 *   ep1 = water level (m)
 *   ep2 = battery voltage (V) — only when CONFIG_WELLD_BATT_ADC_CHANNEL >= 0
 *   ep3 = temperature (°C)    — only when DS18B20 is present
 *   ep4 = level rate of change (cm/h, signed) — only when finite (not first
 *         valid wakeup, not open-loop transducer)
 *   ep5 = Zigbee failure counter (0–255 float) — always reported
 *
 * Pass any of battery_v, temperature_c, or rate_cm_per_hour as the
 * documented sentinel (-1, -127, NaN respectively) to skip that endpoint. */
bool zigbee_send(float level_m,
                 float battery_v,
                 float temperature_c,
                 float rate_cm_per_hour,
                 uint32_t zb_fails);
