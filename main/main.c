#include "freertos/FreeRTOS.h"
#include "esp_sleep.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "nvs.h"
#include "sensor.h"
#include "zigbee.h"
#include "sdkconfig.h"

static const char *TAG = "main";

#define NVS_NAMESPACE   "welld"
#define NVS_KEY_FAILS   "zb_fails"  /* consecutive Zigbee failure counter */
#define FAIL_THRESHOLD  5           /* NVS erase + rejoin after this many failures */

/* Read the consecutive Zigbee failure counter from NVS.
 * Returns 0 if the key doesn't exist yet (first boot). */
static uint32_t read_fail_count(void)
{
    nvs_handle_t h;
    uint32_t count = 0;
    if (nvs_open(NVS_NAMESPACE, NVS_READONLY, &h) == ESP_OK) {
        nvs_get_u32(h, NVS_KEY_FAILS, &count);
        nvs_close(h);
    }
    return count;
}

static void write_fail_count(uint32_t count)
{
    nvs_handle_t h;
    if (nvs_open(NVS_NAMESPACE, NVS_READWRITE, &h) == ESP_OK) {
        nvs_set_u32(h, NVS_KEY_FAILS, count);
        nvs_commit(h);
        nvs_close(h);
    }
}

/* One wake cycle:
 *   1. Init NVS (erasing if the partition is full or version-mismatched)
 *   2. Check consecutive failure counter — wipe NVS after FAIL_THRESHOLD
 *      failures to clear stale Zigbee network state and force a fresh join
 *   3. Read all sensors before starting the radio (ADC is sensitive to
 *      RF interference from the 802.15.4 transmitter)
 *   4. Send readings over Zigbee; update fail counter based on result
 *   5. Enter deep sleep for CONFIG_WELLD_SLEEP_DURATION_SEC seconds */
void app_main(void)
{
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    uint32_t fail_count = read_fail_count();
    if (fail_count >= FAIL_THRESHOLD) {
        /* Corrupted network state suspected — wipe NVS so Zigbee does a fresh join */
        ESP_LOGW(TAG, "%lu consecutive Zigbee failures — erasing NVS to force rejoin", fail_count);
        int current_offset = sensor_get_offset_cm();
        if (current_offset != CONFIG_WELLD_SENSOR_OFFSET_CM) {
            ESP_LOGW(TAG, "NVS erase will reset sensor offset from %d cm to compile-time default (%d cm)",
                     current_offset, CONFIG_WELLD_SENSOR_OFFSET_CM);
        }
        ESP_ERROR_CHECK(nvs_flash_erase());
        ESP_ERROR_CHECK(nvs_flash_init());
        fail_count = 0;
    }

    /* Read sensors before powering the radio to avoid ADC noise */
    float level_m       = sensor_read_level();
    float battery_v     = sensor_read_battery_v();
    float temperature_c = sensor_read_temperature();
    bool sent = zigbee_send(level_m, battery_v, temperature_c);

    /* Only write NVS when the count changes — flash has limited write cycles */
    if (!sent) {
        write_fail_count(fail_count + 1);
        ESP_LOGW(TAG, "Zigbee send failed (%lu/%d)", fail_count + 1, FAIL_THRESHOLD);
    } else if (fail_count != 0) {
        write_fail_count(0);   /* reset counter; skip write when already zero */
    }

    ESP_LOGI(TAG, "sleeping %d s", CONFIG_WELLD_SLEEP_DURATION_SEC);
    esp_deep_sleep((uint64_t)CONFIG_WELLD_SLEEP_DURATION_SEC * 1000000ULL);
}
