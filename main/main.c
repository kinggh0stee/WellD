#include "freertos/FreeRTOS.h"
#include "esp_sleep.h"
#include "esp_attr.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "nvs.h"
#include "sensor.h"
#include "zigbee.h"
#include "welld_core.h"
#include "sdkconfig.h"
#include <math.h>

static const char *TAG = "main";

#define NVS_NAMESPACE   "welld"
#define NVS_KEY_FAILS   "zb_fails"  /* consecutive Zigbee failure counter */
#define FAIL_THRESHOLD  5           /* NVS erase + rejoin after this many failures */

/* RTC slow memory: preserved across deep sleep, zeroed on cold boot.
 *
 * Tracks the last validly-read water level and the cumulative time elapsed
 * since that reading, so we can compute a rate-of-change between the
 * current and previous valid readings even when interleaving wakeups
 * produced open-loop (invalid) readings. */
RTC_DATA_ATTR static struct {
    bool     valid;                /* false on cold boot or until first good reading */
    float    last_level_m;
    uint32_t elapsed_since_last_valid_sec;  /* sum of sleep durations */
    uint32_t pending_sleep_sec;    /* sleep we entered at the previous app_main */
} s_history;

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
 *   4. Compute rate-of-change from RTC history (if available)
 *   5. Send readings over Zigbee; update fail counter based on result
 *   6. Update RTC history with this wakeup's reading
 *   7. Pick the next sleep duration (adaptive when enabled) and deep-sleep */
void app_main(void)
{
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    uint32_t fail_count = read_fail_count();
    if (welld_should_wipe_nvs(fail_count, FAIL_THRESHOLD)) {
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

    /* Account for the sleep we just woke from (zero on cold boot — RTC mem
     * is zeroed). Even if the current reading is invalid we accumulate the
     * elapsed time so the next valid reading can compute rate over the
     * full gap. */
    if (s_history.valid) {
        s_history.elapsed_since_last_valid_sec += s_history.pending_sleep_sec;
    }

    float rate_cm_per_hour = NAN;
    if (s_history.valid && level_m >= 0.0f) {
        rate_cm_per_hour = welld_rate_cm_per_hour(s_history.last_level_m,
                                                   level_m,
                                                   s_history.elapsed_since_last_valid_sec);
    }

    bool sent = zigbee_send(level_m, battery_v, temperature_c, rate_cm_per_hour);

    switch (welld_post_send_action(fail_count, sent)) {
    case WELLD_FAIL_INCREMENT:
        write_fail_count(fail_count + 1);
        ESP_LOGW(TAG, "Zigbee send failed (%lu/%d)", fail_count + 1, FAIL_THRESHOLD);
        break;
    case WELLD_FAIL_RESET:
        write_fail_count(0);
        break;
    case WELLD_FAIL_NONE:
        break;
    }

    /* Update history only on valid readings. Bad reading → history holds
     * the previous valid level + accumulating elapsed for the next good one. */
    if (level_m >= 0.0f) {
        s_history.valid                        = true;
        s_history.last_level_m                 = level_m;
        s_history.elapsed_since_last_valid_sec = 0;
    }

    /* Choose the next sleep duration. Adaptive sleep needs a valid rate
     * (which itself needs prior history) — fall back to the default
     * window on cold boot and when the current reading was open-loop. */
    uint32_t sleep_sec = CONFIG_WELLD_SLEEP_DURATION_SEC;
#if CONFIG_WELLD_ADAPTIVE_SLEEP_ENABLED
    if (!isnan(rate_cm_per_hour)) {
        sleep_sec = welld_adaptive_sleep_sec(rate_cm_per_hour,
                                             CONFIG_WELLD_SLEEP_DURATION_SEC,
                                             CONFIG_WELLD_SLEEP_MIN_SEC,
                                             CONFIG_WELLD_SLEEP_MAX_SEC);
    }
#endif
    s_history.pending_sleep_sec = sleep_sec;

    ESP_LOGI(TAG, "sleeping %lu s", (unsigned long)sleep_sec);
    esp_deep_sleep((uint64_t)sleep_sec * 1000000ULL);
}
