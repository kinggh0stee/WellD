#pragma once

/* Shared NVS namespace and keys used across main/ and components/sensor/.
 * Centralised here so a typo in one file is caught at compile time. */

#define WELLD_NVS_NAMESPACE     "welld"
#define WELLD_NVS_KEY_FAILS     "zb_fails"
#define WELLD_NVS_KEY_OFFSET    "offset_cm"
#define WELLD_NVS_KEY_DS18B20   "ds18b20_rom"
