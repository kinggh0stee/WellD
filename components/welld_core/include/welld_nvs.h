#pragma once

/* Shared NVS namespace and keys used across main/ and components/sensor/.
 * Centralised here so a typo in one file is caught at compile time. */

#define WELLD_NVS_NAMESPACE     "welld"
#define WELLD_NVS_KEY_FAILS     "zb_fails"
#define WELLD_NVS_KEY_OFFSET    "offset_cm"
#define WELLD_NVS_KEY_DS18B20   "ds18b20_rom"
/* Version string (esp_app_desc_t.version) of the last image that completed a
 * successful Zigbee send. While the stored string differs from the running
 * image's version (fresh OTA, first flash, wiped NVS) the OTA rollback
 * counter in main.c is armed; a match means the image is proven and is never
 * rolled back. Storing the version string — not a bool — self-invalidates
 * the marker whenever a new image boots. */
#define WELLD_NVS_KEY_IMG_OK    "img_ok"
