#include "freertos/FreeRTOS.h"
#include "esp_sleep.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "sensor.h"
#include "wifi.h"
#include "mqtt_pub.h"
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

    bool connected = wifi_connect();
    if (connected) {
        mqtt_publish_level(level_m);
    } else {
        ESP_LOGE(TAG, "skipping publish — no WiFi");
    }
    wifi_disconnect();

    ESP_LOGI(TAG, "sleeping %d s", CONFIG_WELLD_SLEEP_DURATION_SEC);
    esp_deep_sleep((uint64_t)CONFIG_WELLD_SLEEP_DURATION_SEC * 1000000ULL);
}
