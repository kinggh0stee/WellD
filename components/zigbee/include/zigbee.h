#pragma once
#include <stdbool.h>

/* joins a Zigbee HA network and reports water level via Analog Input cluster (0x000C) */
bool zigbee_send_level(float level_m);
