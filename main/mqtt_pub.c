#include "mqtt_pub.h"
#include <stdio.h>
#include "mqtt_client.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/event_groups.h"
#include "sdkconfig.h"

static const char *TAG = "mqtt";
#define CONNECTED_BIT BIT0

static EventGroupHandle_t s_events;

static void on_mqtt(void *arg, esp_event_base_t base, int32_t id, void *data)
{
    if (id == MQTT_EVENT_CONNECTED) {
        xEventGroupSetBits(s_events, CONNECTED_BIT);
    } else if (id == MQTT_EVENT_ERROR) {
        esp_mqtt_event_handle_t ev = data;
        ESP_LOGE(TAG, "error type=%d", ev->error_handle->error_type);
    }
}

void mqtt_publish_level(float level_m)
{
    s_events = xEventGroupCreate();

    esp_mqtt_client_config_t cfg = {
        .broker.address.uri = CONFIG_WELLD_MQTT_BROKER_URL,
    };
    esp_mqtt_client_handle_t client = esp_mqtt_client_init(&cfg);
    ESP_ERROR_CHECK(esp_mqtt_client_register_event(client, ESP_EVENT_ANY_ID,
                                                   on_mqtt, NULL));
    ESP_ERROR_CHECK(esp_mqtt_client_start(client));

    EventBits_t bits = xEventGroupWaitBits(s_events, CONNECTED_BIT,
                                           pdFALSE, pdFALSE,
                                           pdMS_TO_TICKS(10000));
    if (bits & CONNECTED_BIT) {
        char topic[80], payload[16];
        snprintf(topic,   sizeof(topic),   "%s/level", CONFIG_WELLD_MQTT_TOPIC_PREFIX);
        snprintf(payload, sizeof(payload), "%.2f",      level_m);
        int msg_id = esp_mqtt_client_publish(client, topic, payload, 0, 1, 1);
        ESP_LOGI(TAG, "published %s m → %s (msg_id=%d)", payload, topic, msg_id);
    } else {
        ESP_LOGE(TAG, "broker connection timeout");
    }

    esp_mqtt_client_stop(client);
    esp_mqtt_client_destroy(client);
    vEventGroupDelete(s_events);
}
