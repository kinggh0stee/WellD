/* Host-side sdkconfig stub. Mirrors the defaults in
 * components/sensor/Kconfig so sensor_pure.c builds without ESP-IDF.
 * Keep these in sync if the Kconfig defaults change. */
#pragma once

#define CONFIG_WELLD_SENSOR_SHUNT_MILLIOHMS  100000
#define CONFIG_WELLD_SENSOR_MAX_DEPTH_CM     600
