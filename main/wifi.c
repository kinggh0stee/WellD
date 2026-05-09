#include "wifi.h"
#include <string.h>
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_log.h"
#include "esp_netif.h"
#include "freertos/FreeRTOS.h"
#include "freertos/event_groups.h"
#include "sdkconfig.h"

static const char *TAG = "wifi";

#define CONNECTED_BIT  BIT0
#define FAIL_BIT       BIT1
#define MAX_RETRIES    5

/* Survive deep sleep — stores the last-known AP channel and BSSID so the
   driver can skip the full scan on subsequent wakeups. */
static RTC_DATA_ATTR struct {
    uint8_t bssid[6];
    uint8_t channel;
    bool    valid;
} s_rtc;

static EventGroupHandle_t s_events;
static int s_retries;

static void on_wifi(void *arg, esp_event_base_t base, int32_t id, void *data)
{
    if (id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
    } else if (id == WIFI_EVENT_STA_CONNECTED) {
        wifi_event_sta_connected_t *ev = data;
        memcpy(s_rtc.bssid, ev->bssid, 6);
        s_rtc.channel = ev->channel;
        s_rtc.valid   = true;
    } else if (id == WIFI_EVENT_STA_DISCONNECTED) {
        s_rtc.valid = false;
        if (s_retries++ < MAX_RETRIES) {
            esp_wifi_connect();
        } else {
            xEventGroupSetBits(s_events, FAIL_BIT);
        }
    }
}

static void on_ip(void *arg, esp_event_base_t base, int32_t id, void *data)
{
    ip_event_got_ip_t *ev = data;
    ESP_LOGI(TAG, "IP: " IPSTR, IP2STR(&ev->ip_info.ip));
    s_retries = 0;
    xEventGroupSetBits(s_events, CONNECTED_BIT);
}

bool wifi_connect(void)
{
    s_events  = xEventGroupCreate();
    s_retries = 0;

    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_netif_create_default_wifi_sta();

    wifi_init_config_t init = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&init));

    ESP_ERROR_CHECK(esp_event_handler_register(WIFI_EVENT, ESP_EVENT_ANY_ID,
                                               on_wifi, NULL));
    ESP_ERROR_CHECK(esp_event_handler_register(IP_EVENT, IP_EVENT_STA_GOT_IP,
                                               on_ip, NULL));

    wifi_config_t cfg = {
        .sta = {
            .ssid     = CONFIG_WELLD_WIFI_SSID,
            .password = CONFIG_WELLD_WIFI_PASSWORD,
        },
    };
    if (s_rtc.valid) {
        cfg.sta.channel   = s_rtc.channel;
        cfg.sta.bssid_set = true;
        memcpy(cfg.sta.bssid, s_rtc.bssid, 6);
    }

    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &cfg));
    ESP_ERROR_CHECK(esp_wifi_start());

    EventBits_t bits = xEventGroupWaitBits(s_events,
                                           CONNECTED_BIT | FAIL_BIT,
                                           pdFALSE, pdFALSE,
                                           pdMS_TO_TICKS(15000));
    if (bits & CONNECTED_BIT) {
        return true;
    }
    ESP_LOGE(TAG, "WiFi connection failed");
    return false;
}

void wifi_disconnect(void)
{
    esp_wifi_disconnect();
    esp_wifi_stop();
    esp_wifi_deinit();
    esp_event_loop_delete_default();
    vEventGroupDelete(s_events);
}
