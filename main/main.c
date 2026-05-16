#include "freertos/FreeRTOS.h"
#include "esp_sleep.h"
#include "esp_attr.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "nvs_flash.h"
#include "nvs.h"
#include "driver/gpio.h"
#include "sensor.h"
#include "zigbee.h"
#include "welld_core.h"
#include "sdkconfig.h"
#include <math.h>
#include <string.h>

static const char *TAG = "main";

#define NVS_NAMESPACE   "welld"
#define NVS_KEY_FAILS   "zb_fails"  /* consecutive Zigbee failure counter */
#define FAIL_THRESHOLD  5           /* NVS erase + rejoin after this many failures */

/* Bump this constant whenever the struct layout below changes.
 * A mismatch on wakeup (e.g. after an OTA that reorders fields) zeroes the
 * struct and treats the boot as cold, preventing stale data from producing a
 * spurious rate-of-change spike. Encode as 'W','E','L','D' + version byte. */
#define HISTORY_MAGIC 0x574C4401UL

/* RTC slow memory: preserved across deep sleep, zeroed on cold boot.
 *
 * Tracks the last valid water level and the cumulative time elapsed since that
 * reading (sleep duration + active phase of each intermediate wakeup) so the
 * rate-of-change calculation uses actual elapsed time rather than just the
 * programmed sleep interval. */
RTC_DATA_ATTR static struct {
    uint32_t magic;
    bool     valid;
    float    last_level_m;
    uint32_t elapsed_since_last_valid_sec;
    uint32_t pending_sleep_sec;
    uint32_t last_active_sec;   /* active-phase duration of the previous wakeup */
} s_history;

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
        esp_err_t _err = nvs_set_u32(h, NVS_KEY_FAILS, count);
        if (_err != ESP_OK)
            ESP_LOGW(TAG, "fail counter write: %s", esp_err_to_name(_err));
        _err = nvs_commit(h);
        if (_err != ESP_OK)
            ESP_LOGW(TAG, "fail counter commit: %s", esp_err_to_name(_err));
        nvs_close(h);
    }
}

/* One wake cycle — see CLAUDE.md for the full sequencing rationale. */
void app_main(void)
{
    int64_t wakeup_start_us = esp_timer_get_time();

    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    /* Detect a stale or uninitialised RTC struct: cold boot (zeroed by hardware)
     * or an OTA that changed the struct layout (magic mismatch). Either way,
     * zero the struct and re-stamp the magic so subsequent wakeups are clean. */
    if (s_history.magic != HISTORY_MAGIC) {
        memset(&s_history, 0, sizeof(s_history));
        s_history.magic = HISTORY_MAGIC;
    }

    /* Initialise the I²C bus (ADS1115 + MAX17048) and power-control GPIOs.
     * Must be called before any sensor_read_level() or sensor_read_battery_v(). */
    sensor_i2c_init();

    /* Charger interlock: read the CN3791 CHRG signal (GPIO6) and assert the
     * TP4056 CE interlock (GPIO4) when solar charging is active to prevent
     * simultaneous dual-charger operation. */
    {
        gpio_config_t out_cfg = {
            .pin_bit_mask = 1ULL << CONFIG_WELLD_CHARGER_CE_GPIO,
            .mode         = GPIO_MODE_OUTPUT,
            .pull_up_en   = GPIO_PULLUP_DISABLE,
            .pull_down_en = GPIO_PULLDOWN_DISABLE,
            .intr_type    = GPIO_INTR_DISABLE,
        };
        gpio_config(&out_cfg);

        gpio_config_t in_cfg = {
            .pin_bit_mask = 1ULL << CONFIG_WELLD_SOLAR_DETECT_GPIO,
            .mode         = GPIO_MODE_INPUT,
            .pull_up_en   = GPIO_PULLUP_ENABLE,
            .pull_down_en = GPIO_PULLDOWN_DISABLE,
            .intr_type    = GPIO_INTR_DISABLE,
        };
        gpio_config(&in_cfg);

        if (gpio_get_level(CONFIG_WELLD_SOLAR_DETECT_GPIO)) {
            gpio_set_level(CONFIG_WELLD_CHARGER_CE_GPIO, 1);
            ESP_LOGI(TAG, "solar charging active — USB charger disabled");
        } else {
            gpio_set_level(CONFIG_WELLD_CHARGER_CE_GPIO, 0);
        }
    }


    uint32_t fail_count = read_fail_count();
    if (welld_should_wipe_nvs(fail_count, FAIL_THRESHOLD)) {
        ESP_LOGW(TAG, "%lu consecutive Zigbee failures — erasing NVS to force rejoin",
                 (unsigned long)fail_count);
        /* Read the calibrated offset before wiping so it can be re-saved
         * immediately after. Without this, 5 Zigbee failures silently revert
         * the sensor to its compile-time zero reference. */
        int saved_offset = sensor_get_offset_cm();
        if (saved_offset != CONFIG_WELLD_SENSOR_OFFSET_CM)
            ESP_LOGW(TAG, "preserving sensor offset %d cm across NVS erase", saved_offset);
        ESP_ERROR_CHECK(nvs_flash_erase());
        ESP_ERROR_CHECK(nvs_flash_init());
        sensor_offset_cache_reset();
        sensor_set_offset_cm(saved_offset);
        fail_count = 0;
    }

    /* Read sensors before powering the radio. The ADC is sensitive to 802.15.4
     * RF interference, so all ADC reads must complete before zigbee_send(). */
    float level_m   = sensor_read_level();
    float battery_v = sensor_read_battery_v();
    float temperature_c = sensor_read_temperature();

    /* Accumulate elapsed time from the previous wakeup: both the programmed sleep
     * duration and the active phase, so the rate calculation reflects wall-clock
     * time rather than just sleep time. */
    if (s_history.valid) {
        s_history.elapsed_since_last_valid_sec +=
            s_history.pending_sleep_sec + s_history.last_active_sec;
    }

#if CONFIG_WELLD_BATT_ADC_CHANNEL >= 0
    /* Flash programming requires VCC >= 2.7 V. A 20 mA Zigbee TX spike on a
     * nearly-dead cell can dip below that, corrupting NVS. If the battery is at
     * or below the empty threshold, skip the send and all NVS writes and sleep
     * as long as possible to conserve the remaining charge. */
    if (battery_v > 0.0f && battery_v < CONFIG_WELLD_BATT_EMPTY_MV / 1000.0f) {
        ESP_LOGW(TAG, "battery critically low (%.2f V < %.2f V) — skipping send",
                 battery_v, CONFIG_WELLD_BATT_EMPTY_MV / 1000.0f);
        uint32_t low_batt_sleep = CONFIG_WELLD_SLEEP_DURATION_SEC;
#ifdef CONFIG_WELLD_SLEEP_MAX_SEC
        low_batt_sleep = CONFIG_WELLD_SLEEP_MAX_SEC;
#endif
        s_history.pending_sleep_sec = low_batt_sleep;
        s_history.last_active_sec =
            (uint32_t)((esp_timer_get_time() - wakeup_start_us) / 1000000LL);
        /* Reset elapsed accumulator to prevent a stale gap producing a false
         * rate spike when the battery recovers and the device resumes sending. */
        s_history.elapsed_since_last_valid_sec = 0;
        gpio_set_level(CONFIG_WELLD_CHARGER_CE_GPIO, 0);
        gpio_set_level(CONFIG_WELLD_VLOOP_GPIO, 0);
        gpio_set_level(CONFIG_WELLD_BATT_DIV_EN_GPIO, 0);
        esp_sleep_config_gpio_isolate();
        esp_deep_sleep((uint64_t)low_batt_sleep * 1000000ULL);
    }
#endif

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
        ESP_LOGW(TAG, "Zigbee send failed (%lu/%d)",
                 (unsigned long)(fail_count + 1), FAIL_THRESHOLD);
        break;
    case WELLD_FAIL_RESET:
        write_fail_count(0);
        break;
    case WELLD_FAIL_NONE:
        break;
    }

    /* Update history only on valid readings. Bad reading → history holds the
     * previous valid level + accumulating elapsed for the next good one. */
    if (level_m >= 0.0f) {
        s_history.valid                        = true;
        s_history.last_level_m                 = level_m;
        s_history.elapsed_since_last_valid_sec = 0;
    }

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
    s_history.last_active_sec =
        (uint32_t)((esp_timer_get_time() - wakeup_start_us) / 1000000LL);

    ESP_LOGI(TAG, "sleeping %lu s", (unsigned long)sleep_sec);
    gpio_set_level(CONFIG_WELLD_CHARGER_CE_GPIO, 0);
    gpio_set_level(CONFIG_WELLD_VLOOP_GPIO, 0);
    gpio_set_level(CONFIG_WELLD_BATT_DIV_EN_GPIO, 0);
    esp_sleep_config_gpio_isolate();
    esp_deep_sleep((uint64_t)sleep_sec * 1000000ULL);
}
