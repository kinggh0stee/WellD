#include "zigbee.h"
#include "esp_zigbee_core.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/event_groups.h"
#include "freertos/task.h"

static const char *TAG = "zigbee";

#define ZB_ENDPOINT      1
#define SEND_DELAY_MS    2000
#define TOTAL_TIMEOUT_MS 25000

#define SENT_BIT    BIT0
#define FAIL_BIT    BIT1
#define STOPPED_BIT BIT2

static EventGroupHandle_t s_events;
static float s_level_m;

static void zb_timeout_alarm(uint8_t param)
{
    ESP_LOGE(TAG, "timeout — no coordinator found");
    xEventGroupSetBits(s_events, FAIL_BIT);
    esp_zb_stop();
}

static void zb_finish_alarm(uint8_t param)
{
    xEventGroupSetBits(s_events, SENT_BIT);
    esp_zb_stop();
}

static void send_report(void)
{
    esp_zb_zcl_set_attribute_val(ZB_ENDPOINT,
        ESP_ZB_ZCL_CLUSTER_ID_ANALOG_INPUT, ESP_ZB_ZCL_CLUSTER_SERVER_ROLE,
        ESP_ZB_ZCL_ATTR_ANALOG_INPUT_PRESENT_VALUE_ID, &s_level_m, false);

    esp_zb_zcl_report_attr_cmd_t report = {
        .zcl_basic_cmd = {
            .dst_addr_u.addr_short = 0x0000,
            .dst_endpoint          = 1,
            .src_endpoint          = ZB_ENDPOINT,
        },
        .address_mode = ESP_ZB_APS_ADDR_MODE_16_ENDP_PRESENT,
        .clusterID    = ESP_ZB_ZCL_CLUSTER_ID_ANALOG_INPUT,
        .attributeID  = ESP_ZB_ZCL_ATTR_ANALOG_INPUT_PRESENT_VALUE_ID,
        .direction    = ESP_ZB_ZCL_CMD_DIRECTION_TO_CLI,
    };
    esp_zb_zcl_report_attr_cmd_req(&report);
    esp_zb_scheduler_alarm(zb_finish_alarm, 0, SEND_DELAY_MS);
}

/* Called by the Zigbee stack from within the main loop task. */
void esp_zb_app_signal_handler(esp_zb_app_signal_t *signal_struct)
{
    uint32_t *p_sg_p     = signal_struct->p_app_signal;
    esp_err_t err_status = signal_struct->esp_err_status;

    switch ((esp_zb_app_signal_type_t)*p_sg_p) {
    case ESP_ZB_ZDO_SIGNAL_SKIP_STARTUP:
        esp_zb_bdb_start_top_level_commissioning(ESP_ZB_BDB_MODE_INITIALIZATION);
        break;
    case ESP_ZB_BDB_SIGNAL_DEVICE_FIRST_START:
    case ESP_ZB_BDB_SIGNAL_DEVICE_REBOOT:
        if (err_status == ESP_OK) {
            esp_zb_bdb_start_top_level_commissioning(ESP_ZB_BDB_MODE_NETWORK_STEERING);
        } else {
            ESP_LOGE(TAG, "init failed (err=%d)", err_status);
            xEventGroupSetBits(s_events, FAIL_BIT);
            esp_zb_stop();
        }
        break;
    case ESP_ZB_BDB_SIGNAL_STEERING:
        if (err_status == ESP_OK) {
            ESP_LOGI(TAG, "joined; reporting %.2f m", s_level_m);
            send_report();
        } else {
            ESP_LOGE(TAG, "steering failed (err=%d)", err_status);
            xEventGroupSetBits(s_events, FAIL_BIT);
            esp_zb_stop();
        }
        break;
    default:
        break;
    }
}

static void zb_task(void *pvParameters)
{
    esp_zb_platform_config_t platform_cfg = {
        .radio_config = ESP_ZB_DEFAULT_RADIO_CONFIG(),
        .host_config  = ESP_ZB_DEFAULT_HOST_CONFIG(),
    };
    ESP_ERROR_CHECK(esp_zb_platform_config(&platform_cfg));

    esp_zb_cfg_t nwk_cfg = {
        .esp_zb_role         = ESP_ZB_DEVICE_TYPE_ED,
        .install_code_policy = false,
        .nwk_cfg.zed_cfg = {
            .ed_timeout = ESP_ZB_ED_AGING_TIMEOUT_64MIN,
            .keep_alive = 3000,
        },
    };
    esp_zb_init(&nwk_cfg);

    /* ZCL character strings: first byte is length, no null terminator */
    static char s_manufacturer[] = "\x05WellD";
    static char s_model[]        = "\x08WellD-v1";
    esp_zb_basic_cluster_cfg_t basic_cfg = {
        .zcl_version = ESP_ZB_ZCL_BASIC_ZCL_VERSION_DEFAULT_VALUE,
        .power_source = 0x03,  /* battery */
    };
    esp_zb_attribute_list_t *basic_attrs = esp_zb_basic_cluster_create(&basic_cfg);
    esp_zb_basic_cluster_add_attr(basic_attrs,
        ESP_ZB_ZCL_ATTR_BASIC_MANUFACTURER_NAME_ID, s_manufacturer);
    esp_zb_basic_cluster_add_attr(basic_attrs,
        ESP_ZB_ZCL_ATTR_BASIC_MODEL_IDENTIFIER_ID,  s_model);

    esp_zb_analog_input_cluster_cfg_t ai_cfg = {
        .out_of_service = 0,
        .present_value  = s_level_m,
        .status_flags   = 0,
    };
    esp_zb_attribute_list_t *ai_attrs = esp_zb_analog_input_cluster_create(&ai_cfg);

    esp_zb_cluster_list_t *clusters = esp_zb_zcl_cluster_list_create();
    ESP_ERROR_CHECK(esp_zb_cluster_list_add_basic_cluster(clusters, basic_attrs,
                                                          ESP_ZB_ZCL_CLUSTER_SERVER_ROLE));
    ESP_ERROR_CHECK(esp_zb_cluster_list_add_analog_input_cluster(clusters, ai_attrs,
                                                                  ESP_ZB_ZCL_CLUSTER_SERVER_ROLE));

    esp_zb_ep_list_t *ep_list = esp_zb_ep_list_create();
    esp_zb_endpoint_config_t ep_cfg = {
        .endpoint           = ZB_ENDPOINT,
        .app_profile_id     = ESP_ZB_AF_HA_PROFILE_ID,
        .app_device_id      = ESP_ZB_HA_SIMPLE_SENSOR_DEVICE_ID,
        .app_device_version = 0,
    };
    ESP_ERROR_CHECK(esp_zb_ep_list_add_ep(ep_list, clusters, ep_cfg));
    esp_zb_device_register(ep_list);

    esp_zb_set_primary_network_channel_set(ESP_ZB_TRANSCEIVER_ALL_CHANNELS_MASK);
    ESP_ERROR_CHECK(esp_zb_start(false));
    esp_zb_scheduler_alarm(zb_timeout_alarm, 0, TOTAL_TIMEOUT_MS);
    esp_zb_main_loop_iteration();
    xEventGroupSetBits(s_events, STOPPED_BIT);
    vTaskDelete(NULL);
}

bool zigbee_send_level(float level_m)
{
    s_level_m = level_m;
    s_events  = xEventGroupCreate();

    if (xTaskCreate(zb_task, "zb_task", 8192, NULL, 5, NULL) != pdPASS) {
        ESP_LOGE(TAG, "failed to create Zigbee task");
        vEventGroupDelete(s_events);
        return false;
    }

    EventBits_t bits = xEventGroupWaitBits(s_events, SENT_BIT | FAIL_BIT,
                                           pdFALSE, pdFALSE,
                                           pdMS_TO_TICKS(TOTAL_TIMEOUT_MS + 5000));
    /* Wait for the task to exit so the 802.15.4 radio is released before
       the caller can start WiFi on the same antenna. */
    xEventGroupWaitBits(s_events, STOPPED_BIT, pdFALSE, pdFALSE, pdMS_TO_TICKS(5000));
    vEventGroupDelete(s_events);
    return (bits & SENT_BIT) != 0;
}
