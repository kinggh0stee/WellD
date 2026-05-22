/* Host-side sdkconfig stub. Mirrors the defaults in
 * components/sensor/Kconfig so sensor_pure.c builds without ESP-IDF.
 * Keep these in sync if the Kconfig defaults change. */
#pragma once

#define CONFIG_WELLD_SENSOR_SHUNT_MILLIOHMS  100000
#define CONFIG_WELLD_SENSOR_MAX_DEPTH_CM     600

/* Sensor offset default */
#define CONFIG_WELLD_SENSOR_OFFSET_CM        0

/* Battery measurement — 2S1P 18650 pack (2 × 4.2 V full, 2 × 3.0 V empty).
 * BATT_DIVIDER_RATIO: PCB R7/R8 = 330 kΩ / 100 kΩ → ratio 430.
 * BATT_FULL_MV / BATT_EMPTY_MV: pack voltage at 100 % / 0 % SoC. */
#define CONFIG_WELLD_BATT_DIVIDER_RATIO      430
#define CONFIG_WELLD_BATT_FULL_MV            8400
#define CONFIG_WELLD_BATT_EMPTY_MV           6000

/* Rev 2 GPIO defaults (stub values for host build) */
#define CONFIG_WELLD_I2C_SDA_GPIO            10
#define CONFIG_WELLD_I2C_SCL_GPIO            11
#define CONFIG_WELLD_VLOOP_GPIO              5
#define CONFIG_WELLD_SOLAR_DETECT_GPIO       6
#define CONFIG_WELLD_BATT_DIV_EN_GPIO        15
#define CONFIG_WELLD_ADS1115_DRDY_GPIO       12
#define CONFIG_WELLD_USB_CHG_GPIO            4
