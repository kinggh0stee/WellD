#pragma once
#include <stdbool.h>

/* joins a Zigbee HA network and reports all readings:
   ep1 = water level (m), ep2 = battery voltage (V), ep3 = temperature (°C) */
bool zigbee_send(float level_m, float battery_v, float temperature_c);
