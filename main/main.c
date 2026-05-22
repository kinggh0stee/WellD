#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_sleep.h"
#include "esp_attr.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "esp_system.h"
#include "esp_ota_ops.h"
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
#include <stdint.h>

static const char *TAG = "main";

#define FAIL_THRESHOLD  5           /* NVS erase + rejoin after this many failures */


/* OTA rollback: count consecutive boots without a successful Zigbee send.
 * If the new OTA image is broken (crashes before send), we roll back to
 * the previous partition after 3 failed boot attempts. */
#define BOOT_ATTEMPTS_MAGIC  0x574C4403UL
#define BOOT_ATTEMPTS_LIMIT  3

RTC_DATA_ATTR static struct {
    uint32_t magic;
    uint8_t  count;   /* increments each boot, cleared on ZB_SENT */
} s_boot_attempts;

static void boot_attempts_init(void)
{
    if (s_boot_attempts.magic != BOOT_ATTEMPTS_MAGIC) {
        memset(&s_boot_attempts, 0, sizeof(s_boot_attempts));
        s_boot_attempts.magic = BOOT_ATTEMPTS_MAGIC;
    }
    s_boot_attempts.count++;
    if (s_boot_attempts.count >= BOOT_ATTEMPTS_LIMIT) {
        ESP_LOGW(TAG, "boot attempt %d/%d — rolling back to previous firmware",
                 s_boot_attempts.count, BOOT_ATTEMPTS_LIMIT);
        const esp_partition_t *run = esp_ota_get_running_partition();
        const esp_partition_t *prev = esp_ota_get_last_invalid_partition();
        if (prev && prev != run) {
            esp_err_t err = esp_ota_set_boot_partition(prev);
            if (err == ESP_OK) {
                ESP_LOGI(TAG, "OTA rollback → %s", prev->label);
                esp_restart();
            } else {
                ESP_LOGE(TAG, "rollback failed: %s", esp_err_to_name(err));
            }
        } else {
            ESP_LOGW(TAG, "no previous partition to roll back to");
        }
        s_boot_attempts.count = 0;
    }
}

static void boot_attempts_clear(void)
{
    s_boot_attempts.count = 0;
}

/* Factory reset: hold GPIO13 LOW at boot to erase NVS and force rejoin.
 * Internal pull-up keeps it HIGH by default; short to GND for reset. */
static bool factory_reset_check(void)
{
#ifdef CONFIG_WELLD_FACTORY_RESET_GPIO
    gpio_config_t cfg = {
        .pin_bit_mask = 1ULL << CONFIG_WELLD_FACTORY_RESET_GPIO,
        .mode         = GPIO_MODE_INPUT,
        .pull_up_en   = GPIO_PULLUP_ENABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type    = GPIO_INTR_DISABLE,
    };
    gpio_config(&cfg);
    vTaskDelay(pdMS_TO_TICKS(10));  /* let pull-up settle */
    if (!gpio_get_level(CONFIG_WELLD_FACTORY_RESET_GPIO)) {
        ESP_LOGW(TAG, "factory reset GPIO held LOW — erasing NVS");
        ESP_ERROR_CHECK(nvs_flash_erase());
        ESP_ERROR_CHECK(nvs_flash_init());
        ESP_LOGI(TAG, "NVS erased; rebooting for clean join");
        esp_restart();
        return true;  /* never reached */
    }
#endif
    return false;
}

/* Power-profiling: time spent in each phase of the wake cycle (us).
 * Logged before deep sleep to help optimize battery life. */
static struct {
    int64_t t_i2c_init;
    int64_t t_sensors;
    int64_t t_zigbee;
    int64_t t_total;
} s_profile;

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

/* Store-and-forward buffer: readings saved when Zigbee send fails.
 * On the next successful send, the backlog is burst-reported so the
 * coordinator receives the full history (preserving rate accuracy).
 * Preserved across deep sleep, zeroed on cold boot. */
#define STORE_MAGIC      0x574C4404UL
#define STORE_ENTRIES    8

RTC_DATA_ATTR static struct {
    uint32_t magic;
    uint8_t  count;
    uint32_t sleep_sec[STORE_ENTRIES];   /* sleep duration preceding each stored reading */
    float    level_m[STORE_ENTRIES];
    float    battery_v[STORE_ENTRIES];
    float    temp_c[STORE_ENTRIES];
} s_store;

static void store_push(float level_m, float battery_v, float temp_c, uint32_t sleep_sec)
{
    if (s_store.count >= STORE_ENTRIES) {
        /* shift oldest out */
        for (int i = 0; i < STORE_ENTRIES - 1; i++) {
            s_store.level_m[i]   = s_store.level_m[i + 1];
            s_store.battery_v[i] = s_store.battery_v[i + 1];
            s_store.temp_c[i]    = s_store.temp_c[i + 1];
            s_store.sleep_sec[i] = s_store.sleep_sec[i + 1];
        }
        s_store.count = STORE_ENTRIES - 1;
    }
    int idx = s_store.count++;
    s_store.level_m[idx]   = level_m;
    s_store.battery_v[idx] = battery_v;
    s_store.temp_c[idx]    = temp_c;
    s_store.sleep_sec[idx] = sleep_sec;
}

static void store_clear(void)
{
    s_store.count = 0;
}

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
    RTC_EVT_FACTORY_RESET   = 0x0B,
    RTC_EVT_BROWNOUT        = 0x0C,
    RTC_EVT_WATCHDOG        = 0x0D,
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
            case RTC_EVT_FACTORY_RESET: name = "FACTORY_RESET"; break;
            case RTC_EVT_BROWNOUT:      name = "BROWNOUT";      break;
            case RTC_EVT_WATCHDOG:      name = "WATCHDOG";      break;
        }
        ESP_LOGI(TAG, "  [%u] t=%lus  %s", i, (unsigned long)s_rtc_log.ts[idx], name);
    }
}

/* NVS wear-leveling: cache the last-written value so we skip redundant
 * commits. Flash endurance is ~100k cycles; at 288 wakeups/day this
 * extends NVS life from ~1 year to effectively unlimited. */
static uint32_t s_cached_fail_count = UINT32_MAX;

static uint32_t read_fail_count(void)
{
    nvs_handle_t h;
    uint32_t count = 0;
    if (nvs_open(WELLD_NVS_NAMESPACE, NVS_READONLY, &h) == ESP_OK) {
        nvs_get_u32(h, WELLD_NVS_KEY_FAILS, &count);
        nvs_close(h);
    }
    s_cached_fail_count = count;
    return count;
}

static void write_fail_count(uint32_t count)
{
    if (count == s_cached_fail_count) {
        return;  /* no change → skip NVS write entirely */
    }
    nvs_handle_t h;
    if (nvs_open(WELLD_NVS_NAMESPACE, NVS_READWRITE, &h) == ESP_OK) {
        esp_err_t _err = nvs_set_u32(h, WELLD_NVS_KEY_FAILS, count);
        if (_err != ESP_OK)
            ESP_LOGW(TAG, "fail counter write: %s", esp_err_to_name(_err));
        _err = nvs_commit(h);
        if (_err != ESP_OK)
            ESP_LOGW(TAG, "fail counter commit: %s", esp_err_to_name(_err));
        nvs_close(h);
        s_cached_fail_count = count;
    }
}

/* Power down all peripheral GPIOs, isolate them for deep sleep, and enter
 * deep sleep for the requested duration. Called from every exit path in
 * app_main() so no wake cycle leaks power through partially-driven outputs.
 *
 * Sequence:
 *  1. sensor_pre_sleep_cleanup() — removes ADS1115 DRDY ISR (prevents a
 *     spurious GPIO12 edge from waking the CPU during sleep entry) and
 *     deletes the I2C master bus (prevents port 0 staying claimed across
 *     wakeups).
 *  2. Drive power-control outputs LOW: GPIO5 (VLOOP), GPIO15 (BATT_DIV_EN),
 *     GPIO4 (USB_CHG CE). All are already LOW after sensor reads; driven LOW
 *     again here as a belt-and-suspenders guard before isolation.
 *  3. esp_sleep_config_gpio_isolate() — disconnects all GPIO pads from the
 *     GPIO matrix so outputs hold their last state but draw no dynamic
 *     current.  The power-control outputs are already LOW before this call
 *     so they remain LOW in isolation.  For GPIO4 specifically, floating
 *     during sleep lets R37 (4.7 kΩ) passively hold TP5100 CE LOW so the
 *     USB charger is off while the MCU sleeps. */
static void enter_deep_sleep(uint32_t sleep_sec)
{
    sensor_pre_sleep_cleanup();
    gpio_set_level(CONFIG_WELLD_VLOOP_GPIO, 0);
    gpio_set_level(CONFIG_WELLD_BATT_DIV_EN_GPIO, 0);
    gpio_set_level(CONFIG_WELLD_USB_CHG_GPIO, 0);
    esp_sleep_config_gpio_isolate();
    esp_deep_sleep((uint64_t)sleep_sec * 1000000ULL);
}

/* One wake cycle — see CLAUDE.md for the full sequencing rationale. */
void app_main(void)
{
    int64_t wakeup_start_us = esp_timer_get_time();

    rtc_log_init();
    rtc_log_event(RTC_EVT_BOOT);

    /* Log boot reason for field diagnostics */
    esp_reset_reason_t reason = esp_reset_reason();
    switch (reason) {
        case ESP_RST_BROWNOUT:
            ESP_LOGW(TAG, "boot reason: brownout");
            rtc_log_event(RTC_EVT_BROWNOUT);
            break;
        case ESP_RST_TASK_WDT:
        case ESP_RST_WDT:
            ESP_LOGW(TAG, "boot reason: watchdog timeout");
            rtc_log_event(RTC_EVT_WATCHDOG);
            break;
        case ESP_RST_DEEPSLEEP:
            ESP_LOGI(TAG, "boot reason: deep-sleep wakeup");
            break;
        case ESP_RST_SW:
            ESP_LOGI(TAG, "boot reason: software restart (OTA)");
            break;
        default:
            ESP_LOGI(TAG, "boot reason: %d", (int)reason);
            break;
    }

    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    /* Factory reset: check GPIO before any other logic */
    factory_reset_check();

    /* OTA rollback protection: count boots without a successful send */
    boot_attempts_init();

    /* Detect a stale or uninitialised RTC struct: cold boot (zeroed by hardware)
     * or an OTA that changed the struct layout (magic mismatch). Either way,
     * zero the struct and re-stamp the magic so subsequent wakeups are clean. */
    if (s_history.magic != HISTORY_MAGIC) {
        memset(&s_history, 0, sizeof(s_history));
        s_history.magic = HISTORY_MAGIC;
    }
    if (s_store.magic != STORE_MAGIC) {
        memset(&s_store, 0, sizeof(s_store));
        s_store.magic = STORE_MAGIC;
    }

    /* Print any events from previous wakeups so the serial log on this boot
     * contains a short history (useful when the device is retrieved from the
     * field and powered over USB for diagnosis). */
    rtc_log_print();

    /* Initialise the I²C bus (ADS1115 only) and power-control GPIOs.
     * Must be called before any sensor_read_level() or sensor_read_battery_v(). */
    int64_t t0 = esp_timer_get_time();
    if (sensor_i2c_init() != ESP_OK) {
        ESP_LOGE(TAG, "I2C init failed — aborting wakeup");
        enter_deep_sleep(CONFIG_WELLD_SLEEP_DURATION_SEC);
    }
    s_profile.t_i2c_init = esp_timer_get_time() - t0;

    /* Read the CN3791 CHRG signal (GPIO6) to determine whether solar charging
     * is active. Active-low: LOW means solar charging is in progress.
     * Reported to Zigbee coordinator via zigbee_send(); no GPIO4 interlock in
     * the 2S hardware design (TP4056 removed). */
    bool solar_charging = false;
    {
        gpio_config_t in_cfg = {
            .pin_bit_mask = 1ULL << CONFIG_WELLD_SOLAR_DETECT_GPIO,
            .mode         = GPIO_MODE_INPUT,
            .pull_up_en   = GPIO_PULLUP_ENABLE,
            .pull_down_en = GPIO_PULLDOWN_DISABLE,
            .intr_type    = GPIO_INTR_DISABLE,
        };
        gpio_config(&in_cfg);
        solar_charging = !gpio_get_level(CONFIG_WELLD_SOLAR_DETECT_GPIO);
        if (solar_charging) {
            ESP_LOGI(TAG, "solar charging active (GPIO6 LOW)");
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
    t0 = esp_timer_get_time();
    float level_m   = sensor_read_level();
    float battery_v = sensor_read_battery_v();
    float temperature_c = sensor_read_temperature();
    s_profile.t_sensors = esp_timer_get_time() - t0;
    if (level_m >= 0.0f) {
        rtc_log_event(RTC_EVT_SENSOR_OK);
    }

    /* Temperature compensation for water density */
    if (level_m >= 0.0f && temperature_c > -127.0f) {
        level_m = sensor_level_temp_compensate(level_m, temperature_c);
    }

#ifdef CONFIG_WELLD_SELFTEST_ENABLED
    sensor_selftest();
#endif

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

    /* Zigbee send with store-and-forward burst */
    t0 = esp_timer_get_time();
    bool sent = zigbee_send(level_m, battery_v, temperature_c, rate_cm_per_hour, fail_count,
                            solar_charging, s_store.count, s_store.level_m, s_store.battery_v,
                            s_store.temp_c);
    s_profile.t_zigbee = esp_timer_get_time() - t0;

    switch (welld_post_send_action(fail_count, sent)) {
    case WELLD_FAIL_INCREMENT:
        write_fail_count(fail_count + 1);
        ESP_LOGW(TAG, "Zigbee send failed (%lu/%d)",
                 (unsigned long)(fail_count + 1), FAIL_THRESHOLD);
        rtc_log_event(RTC_EVT_ZB_FAIL);
        /* Save reading for next successful send */
        store_push(level_m, battery_v, temperature_c, CONFIG_WELLD_SLEEP_DURATION_SEC);
        break;
    case WELLD_FAIL_RESET:
        write_fail_count(0);
        rtc_log_event(RTC_EVT_ZB_SENT);
        store_clear();
        boot_attempts_clear();
        break;
    case WELLD_FAIL_NONE:
        rtc_log_event(RTC_EVT_ZB_SENT);
        store_clear();
        boot_attempts_clear();
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

    s_profile.t_total = esp_timer_get_time() - wakeup_start_us;
    ESP_LOGI(TAG, "profile: i2c=%lld us sensors=%lld us zigbee=%lld us total=%lld us",
             s_profile.t_i2c_init, s_profile.t_sensors, s_profile.t_zigbee, s_profile.t_total);

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
