#pragma once

/* Shared NVS namespace, keys and partition labels used across main/ and
 * components/.
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

/* Label of the dedicated NVS partition (partitions.csv) holding the Zigbee
 * stack's network datasets. Separate from the default "nvs" partition that
 * holds the keys above, so erasing WellD's own keys never touches the
 * Zigbee join state and vice versa. app_main initialises it; zigbee.c
 * passes it to esp_zigbee_init(). */
#define WELLD_ZB_STORAGE_PARTITION  "zb_storage"
