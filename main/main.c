#include "freertos/FreeRTOS.h"
#include "esp_sleep.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "sensor.h"
#include "zigbee.h"
#include "sdkconfig.h"

static const char *TAG = "main";

void app_main(void)
{
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    float level_m = sensor_read_level();
    zigbee_send_level(level_m);

    ESP_LOGI(TAG, "sleeping %d s", CONFIG_WELLD_SLEEP_DURATION_SEC);
    esp_deep_sleep((uint64_t)CONFIG_WELLD_SLEEP_DURATION_SEC * 1000000ULL);
}
