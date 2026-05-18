#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
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
#include "welld_nvs.h"
#include <math.h>
#include <string.h>

static const char *TAG = "main";

#define FAIL_THRESHOLD  5           /* NVS erase + rejoin after this many failures */

/* Set by the MAX17048 ALRT ISR when GPIO14 falls (low-battery alert). */
static volatile bool s_max17048_alrt_fired = false;

/* ISR: MAX17048 ALRT line (GPIO14) went LOW — low-battery condition. */
static void IRAM_ATTR max17048_alrt_isr(void *arg)
{
    s_max17048_alrt_fired = true;
}

/* Configure GPIO CONFIG_WELLD_MAX17048_ALRT_GPIO as a falling-edge input.
 * External R27 (4.7 kΩ to 3V3) provides the pull-up — internal pull-up is
 * deliberately disabled.  The ISR just sets a flag; the main wake cycle
 * reads it after all sensor reads are done. */
static void max17048_alrt_gpio_init(void)
{
    gpio_config_t cfg = {
        .pin_bit_mask = 1ULL << CONFIG_WELLD_MAX17048_ALRT_GPIO,
        .mode         = GPIO_MODE_INPUT,
        .pull_up_en   = GPIO_PULLUP_DISABLE,   /* external R27 handles pull-up */
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type    = GPIO_INTR_NEGEDGE,
    };
    gpio_config(&cfg);

    /* gpio_install_isr_service may already have been called by sensor_i2c_init()
     * via the ADS1115 DRDY path.  ESP_ERR_INVALID_STATE is benign here. */
    esp_err_t ret = gpio_install_isr_service(0);
    if (ret != ESP_OK && ret != ESP_ERR_INVALID_STATE) {
        ESP_LOGW(TAG, "gpio_install_isr_service: %s", esp_err_to_name(ret));
        return;
    }
    gpio_isr_handler_add(CONFIG_WELLD_MAX17048_ALRT_GPIO, max17048_alrt_isr, NULL);
    ESP_LOGI(TAG, "MAX17048 ALRT interrupt configured on GPIO%d",
             CONFIG_WELLD_MAX17048_ALRT_GPIO);
}

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

/* RTC event log — small ring buffer of structured events for field debugging.
 * Preserved across deep sleep, zeroed on cold boot. Each entry is a 32-bit
 * seconds-since-boot timestamp and an 8-bit event code. */
#define RTC_LOG_MAGIC    0x574C4402UL
#define RTC_LOG_ENTRIES  16

typedef enum {
    RTC_EVT_BOOT            = 0x01,
    RTC_EVT_SENSOR_OK       = 0x02,
    RTC_EVT_ZB_SENT         = 0x03,
    RTC_EVT_ZB_FAIL         = 0x04,
    RTC_EVT_LOW_BATT_SKIP   = 0x05,
    RTC_EVT_NVS_WIPE        = 0x06,
    RTC_EVT_OTA_START       = 0x07,
    RTC_EVT_OTA_COMPLETE    = 0x08,
    RTC_EVT_OTA_ABORT       = 0x09,
    RTC_EVT_MAX17048_ALRT   = 0x0A,
} rtc_event_t;

RTC_DATA_ATTR static struct {
    uint32_t magic;
    uint8_t  head;
    uint32_t ts[RTC_LOG_ENTRIES];
    uint8_t  ev[RTC_LOG_ENTRIES];
} s_rtc_log;

static void rtc_log_init(void)
{
    if (s_rtc_log.magic != RTC_LOG_MAGIC) {
        memset(&s_rtc_log, 0, sizeof(s_rtc_log));
        s_rtc_log.magic = RTC_LOG_MAGIC;
    }
}

static void rtc_log_event(rtc_event_t ev)
{
    uint32_t now_sec = (uint32_t)(esp_timer_get_time() / 1000000LL);
    uint8_t idx = s_rtc_log.head % RTC_LOG_ENTRIES;
    s_rtc_log.ts[idx] = now_sec;
    s_rtc_log.ev[idx] = (uint8_t)ev;
    s_rtc_log.head++;
}

static void rtc_log_print(void)
{
    if (s_rtc_log.head == 0) return;
    uint8_t count = (s_rtc_log.head < RTC_LOG_ENTRIES) ? s_rtc_log.head : RTC_LOG_ENTRIES;
    uint8_t start = (s_rtc_log.head >= RTC_LOG_ENTRIES) ? s_rtc_log.head % RTC_LOG_ENTRIES : 0;
    ESP_LOGI(TAG, "RTC event log (last %u entries):", count);
    for (uint8_t i = 0; i < count; i++) {
        uint8_t idx = (start + i) % RTC_LOG_ENTRIES;
        const char *name = "unknown";
        switch (s_rtc_log.ev[idx]) {
            case RTC_EVT_BOOT:          name = "BOOT";          break;
            case RTC_EVT_SENSOR_OK:     name = "SENSOR_OK";     break;
            case RTC_EVT_ZB_SENT:       name = "ZB_SENT";       break;
            case RTC_EVT_ZB_FAIL:       name = "ZB_FAIL";       break;
            case RTC_EVT_LOW_BATT_SKIP: name = "LOW_BATT_SKIP"; break;
            case RTC_EVT_NVS_WIPE:      name = "NVS_WIPE";      break;
            case RTC_EVT_OTA_START:     name = "OTA_START";     break;
            case RTC_EVT_OTA_COMPLETE:  name = "OTA_COMPLETE";  break;
            case RTC_EVT_OTA_ABORT:     name = "OTA_ABORT";     break;
            case RTC_EVT_MAX17048_ALRT: name = "MAX17048_ALRT"; break;
        }
        ESP_LOGI(TAG, "  [%u] t=%lus  %s", i, (unsigned long)s_rtc_log.ts[idx], name);
    }
}

static uint32_t read_fail_count(void)
{
    nvs_handle_t h;
    uint32_t count = 0;
    if (nvs_open(WELLD_NVS_NAMESPACE, NVS_READONLY, &h) == ESP_OK) {
        nvs_get_u32(h, WELLD_NVS_KEY_FAILS, &count);
        nvs_close(h);
    }
    return count;
}

static void write_fail_count(uint32_t count)
{
    nvs_handle_t h;
    if (nvs_open(WELLD_NVS_NAMESPACE, NVS_READWRITE, &h) == ESP_OK) {
        esp_err_t _err = nvs_set_u32(h, WELLD_NVS_KEY_FAILS, count);
        if (_err != ESP_OK)
            ESP_LOGW(TAG, "fail counter write: %s", esp_err_to_name(_err));
        _err = nvs_commit(h);
        if (_err != ESP_OK)
            ESP_LOGW(TAG, "fail counter commit: %s", esp_err_to_name(_err));
        nvs_close(h);
    }
}

/* Power down all peripheral GPIOs, isolate them for deep sleep, and enter
 * deep sleep for the requested duration. Called from every exit path in
 * app_main() so no wake cycle leaks power through partially-driven outputs. */
static void enter_deep_sleep(uint32_t sleep_sec)
{
    gpio_set_level(CONFIG_WELLD_CHARGER_CE_GPIO, 0);
    gpio_set_level(CONFIG_WELLD_VLOOP_GPIO, 0);
    gpio_set_level(CONFIG_WELLD_BATT_DIV_EN_GPIO, 0);
    esp_sleep_config_gpio_isolate();
    esp_deep_sleep((uint64_t)sleep_sec * 1000000ULL);
}

/* One wake cycle — see CLAUDE.md for the full sequencing rationale. */
void app_main(void)
{
    int64_t wakeup_start_us = esp_timer_get_time();

    rtc_log_init();
    rtc_log_event(RTC_EVT_BOOT);

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

    /* Print any events from previous wakeups so the serial log on this boot
     * contains a short history (useful when the device is retrieved from the
     * field and powered over USB for diagnosis). */
    rtc_log_print();

    /* Initialise the I²C bus (ADS1115 + MAX17048) and power-control GPIOs.
     * Must be called before any sensor_read_level() or sensor_read_battery_v(). */
    if (sensor_i2c_init() != ESP_OK) {
        ESP_LOGE(TAG, "I2C init failed — aborting wakeup");
        enter_deep_sleep(CONFIG_WELLD_SLEEP_DURATION_SEC);
    }

    /* Configure MAX17048 ALRT falling-edge interrupt (GPIO14, external R27).
     * Must come after sensor_i2c_init() so the GPIO ISR service is already
     * installed by the ADS1115 DRDY path when available. */
    max17048_alrt_gpio_init();

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

        /* CN3791 CHRG is active-low: LOW means solar charging is in progress.
         * Assert GPIO4 HIGH (disable TP4056 CE via Q1) to prevent both chargers
         * from driving the battery simultaneously. Hardware Q3 does the same in
         * parallel; this software path ensures the GPIO state is explicit. */
        if (!gpio_get_level(CONFIG_WELLD_SOLAR_DETECT_GPIO)) {
            gpio_set_level(CONFIG_WELLD_CHARGER_CE_GPIO, 1);
            ESP_LOGI(TAG, "solar charging active (GPIO6 LOW) — USB charger disabled");
        } else {
            gpio_set_level(CONFIG_WELLD_CHARGER_CE_GPIO, 0);
        }
    }


    uint32_t fail_count = read_fail_count();
    if (welld_should_wipe_nvs(fail_count, FAIL_THRESHOLD)) {
        ESP_LOGW(TAG, "%lu consecutive Zigbee failures — erasing NVS to force rejoin",
                 (unsigned long)fail_count);
        rtc_log_event(RTC_EVT_NVS_WIPE);
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
    if (level_m >= 0.0f) {
        rtc_log_event(RTC_EVT_SENSOR_OK);
    }

    /* Check MAX17048 ALRT after all sensor reads.  The ISR flag covers both
     * edges that arrived during the wake cycle AND a pin that is already LOW
     * at boot (a persistent alert from the previous cycle).  Sample the GPIO
     * level directly as a belt-and-suspenders check in case the ISR fired
     * before we called max17048_alrt_gpio_init(). */
    if (s_max17048_alrt_fired || !gpio_get_level(CONFIG_WELLD_MAX17048_ALRT_GPIO)) {
        ESP_LOGW(TAG, "MAX17048 ALRT asserted (GPIO%d LOW) — low-battery condition",
                 CONFIG_WELLD_MAX17048_ALRT_GPIO);
        /* Clear the ALRT bit in STATUS (0x1A) so the pin de-asserts. */
        if (sensor_max17048_clear_alrt() == ESP_OK) {
            ESP_LOGI(TAG, "MAX17048 ALRT bit cleared");
        } else {
            ESP_LOGW(TAG, "MAX17048 ALRT clear failed (device absent or I2C error)");
        }
        s_max17048_alrt_fired = false;
    }

    /* Accumulate elapsed time from the previous wakeup: both the programmed sleep
     * duration and the active phase, so the rate calculation reflects wall-clock
     * time rather than just sleep time. */
    if (s_history.valid) {
        s_history.elapsed_since_last_valid_sec +=
            s_history.pending_sleep_sec + s_history.last_active_sec;
    }

    /* Flash programming requires VCC >= 2.7 V. A 20 mA Zigbee TX spike on a
     * nearly-dead cell can dip below that, corrupting NVS. If the battery is at
     * or below the empty threshold, skip the send and all NVS writes and sleep
     * as long as possible to conserve the remaining charge. */
    if (battery_v > 0.0f && battery_v < CONFIG_WELLD_BATT_EMPTY_MV / 1000.0f) {
        ESP_LOGW(TAG, "battery critically low (%.2f V < %.2f V) — skipping send",
                 battery_v, CONFIG_WELLD_BATT_EMPTY_MV / 1000.0f);
        rtc_log_event(RTC_EVT_LOW_BATT_SKIP);
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
        enter_deep_sleep(low_batt_sleep);
    }

    float rate_cm_per_hour = NAN;
    if (s_history.valid && level_m >= 0.0f) {
        rate_cm_per_hour = welld_rate_cm_per_hour(s_history.last_level_m,
                                                   level_m,
                                                   s_history.elapsed_since_last_valid_sec);
    }

    bool sent = zigbee_send(level_m, battery_v, temperature_c, rate_cm_per_hour, fail_count);

    switch (welld_post_send_action(fail_count, sent)) {
    case WELLD_FAIL_INCREMENT:
        write_fail_count(fail_count + 1);
        ESP_LOGW(TAG, "Zigbee send failed (%lu/%d)",
                 (unsigned long)(fail_count + 1), FAIL_THRESHOLD);
        rtc_log_event(RTC_EVT_ZB_FAIL);
        break;
    case WELLD_FAIL_RESET:
        write_fail_count(0);
        rtc_log_event(RTC_EVT_ZB_SENT);
        break;
    case WELLD_FAIL_NONE:
        rtc_log_event(RTC_EVT_ZB_SENT);
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

#ifdef CONFIG_WELLD_DIAGNOSTIC_MODE_ENABLED
    {
        uint32_t stay_ms = CONFIG_WELLD_DIAGNOSTIC_STAY_AWAKE_SEC * 1000U;
        ESP_LOGI(TAG, "diagnostic mode — staying awake %u ms", stay_ms);
        vTaskDelay(pdMS_TO_TICKS(stay_ms));
    }
#endif

    enter_deep_sleep(sleep_sec);
}
