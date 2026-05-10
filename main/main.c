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
#define NVS_KEY_FAILS   "zb_fails"
#define FAIL_THRESHOLD  5

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
        ESP_LOGW(TAG, "%lu consecutive Zigbee failures, erasing NVS to force rejoin", fail_count);
        ESP_ERROR_CHECK(nvs_flash_erase());
        ESP_ERROR_CHECK(nvs_flash_init());
        fail_count = 0;
    }

    float level_m       = sensor_read_level();
    float battery_v     = sensor_read_battery_v();
    float temperature_c = sensor_read_temperature();
    bool sent = zigbee_send(level_m, battery_v, temperature_c);

    write_fail_count(sent ? 0 : fail_count + 1);
    if (!sent)
        ESP_LOGW(TAG, "Zigbee send failed (%lu/%d)", fail_count + 1, FAIL_THRESHOLD);

    ESP_LOGI(TAG, "sleeping %d s", CONFIG_WELLD_SLEEP_DURATION_SEC);
    esp_deep_sleep((uint64_t)CONFIG_WELLD_SLEEP_DURATION_SEC * 1000000ULL);
}
