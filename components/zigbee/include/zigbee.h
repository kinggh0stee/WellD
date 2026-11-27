#pragma once
#include <stdbool.h>
#include <stdint.h>

/* Rejoins (or, when factory-new, steers onto) a Zigbee HA network, reports
 * all readings and sends an OTA Query Next Image to the coordinator:
 *   ep1 = water level (m)
 *   ep2 = battery voltage (V) — only when CONFIG_WELLD_BATT_REPORT_ENABLED
 *   ep3 = temperature (°C)    — only when DS18B20 is present
 *   ep4 = level rate of change (cm/h, signed) — only when finite (not first
 *         valid wakeup, not open-loop transducer)
 *   ep5 = Zigbee failure counter (0–255 float) — always reported
 *   ep6 = link quality (LQI, 0–255 float) — always reported
 *   ep7 = solar charging state (0/1 float) — always reported
 *
 * store_count > 0 triggers burst-reporting of previously-failed readings
 * from the RTC store-and-forward buffer (up to STORE_ENTRIES).
 *
 * Pass any of battery_v, temperature_c, or rate_cm_per_hour as the
 * documented sentinel (-1, -127, NaN respectively) to skip that endpoint.
 *
 * Returns once the cycle is resolved, with the stack parked under its lock —
 * call at most once per boot and deep-sleep afterwards. An OTA offered by
 * the coordinator is downloaded before returning; a completed OTA reboots
 * and never returns. */
bool zigbee_send(float level_m,
                 float battery_v,
                 float temperature_c,
                 float rate_cm_per_hour,
                 uint32_t zb_fails,
                 bool solar_charging,
                 uint8_t store_count,
                 const float *store_level_m,
                 const float *store_battery_v,
                 const float *store_temp_c);

/* True when an OTA download started during zigbee_send() and was aborted
 * (stall, malformed .zigbee file, flash write or image validation failure,
 * or aborted by the server). */
bool zigbee_ota_aborted(void);
