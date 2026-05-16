/* Host-side sdkconfig stub. Mirrors the defaults in
 * components/sensor/Kconfig so sensor_pure.c builds without ESP-IDF.
 * Keep these in sync if the Kconfig defaults change. */
#pragma once

#define CONFIG_WELLD_SENSOR_SHUNT_MILLIOHMS  100000
#define CONFIG_WELLD_SENSOR_MAX_DEPTH_CM     600

/* Sensor offset default */
#define CONFIG_WELLD_SENSOR_OFFSET_CM        0

/* Rev 2 GPIO defaults (stub values for host build) */
#define CONFIG_WELLD_I2C_SDA_GPIO            10
#define CONFIG_WELLD_I2C_SCL_GPIO            11
#define CONFIG_WELLD_VLOOP_GPIO              5
#define CONFIG_WELLD_CHARGER_CE_GPIO         4
#define CONFIG_WELLD_SOLAR_DETECT_GPIO       6
#define CONFIG_WELLD_BATT_DIV_EN_GPIO        15
#define CONFIG_WELLD_MAX17048_ALRT_GPIO      14
