#include "zigbee.h"
#include "esp_zigbee_core.h"
#include "esp_app_desc.h"
#include "esp_ota_ops.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/event_groups.h"
#include "freertos/task.h"
#include "sdkconfig.h"
#include <string.h>

static const char *TAG = "zigbee";

#define EP_LEVEL         1
#define EP_BATTERY       2
#define EP_TEMPERATURE   3
#define SEND_DELAY_MS    CONFIG_WELLD_ZIGBEE_SEND_DELAY_MS
#define TOTAL_TIMEOUT_MS 25000

#define SENT_BIT    BIT0
#define FAIL_BIT    BIT1
#define STOPPED_BIT BIT2

/* ZCL character strings: first byte is length, no null terminator */
static char s_manufacturer[] = "\x05WellD";
static char s_model[]        = "\x08WellD-v1";
static char s_sw_build_id[18]; /* 1-byte length prefix + up to 16 chars */

static EventGroupHandle_t s_events;
static float s_level_m;
static float s_battery_v;
static float s_temperature_c;

static volatile bool   s_ota_in_progress = false;
static esp_ota_handle_t s_ota_handle     = 0;
static const esp_partition_t *s_ota_partition = NULL;

static void zb_timeout_alarm(uint8_t param)
{
    if (s_ota_in_progress) {
        esp_zb_scheduler_alarm(zb_timeout_alarm, 0, TOTAL_TIMEOUT_MS);
        return;
    }
    ESP_LOGE(TAG, "timeout — no coordinator found");
    xEventGroupSetBits(s_events, FAIL_BIT);
    esp_zb_stop();
}

static void zb_finish_alarm(uint8_t param)
{
    if (s_ota_in_progress) {
        return;   /* OTA started after send — keep the loop alive */
    }
    xEventGroupSetBits(s_events, SENT_BIT);
    esp_zb_stop();
}

static esp_err_t zb_action_handler(esp_zb_core_action_callback_id_t callback_id,
                                    const void *message)
{
    if (callback_id != ESP_ZB_CORE_OTA_UPGRADE_VALUE_CB_ID) return ESP_OK;
    const esp_zb_zcl_ota_upgrade_value_message_t *msg = message;

    switch (msg->upgrade_status) {
    case ESP_ZB_ZCL_OTA_UPGRADE_STATUS_START:
        s_ota_partition = esp_ota_get_next_update_partition(NULL);
        if (!s_ota_partition) {
            ESP_LOGE(TAG, "OTA: no update partition found");
            break;
        }
        if (esp_ota_begin(s_ota_partition, OTA_SIZE_UNKNOWN, &s_ota_handle) == ESP_OK) {
            s_ota_in_progress = true;
            ESP_LOGI(TAG, "OTA started → %s", s_ota_partition->label);
        }
        break;

    case ESP_ZB_ZCL_OTA_UPGRADE_STATUS_RECEIVE:
        if (s_ota_in_progress && msg->payload && msg->payload_size > 0) {
            if (esp_ota_write(s_ota_handle, msg->payload, msg->payload_size) != ESP_OK) {
                ESP_LOGE(TAG, "OTA write failed — aborting");
                esp_ota_abort(s_ota_handle);
                s_ota_in_progress = false;
                xEventGroupSetBits(s_events, FAIL_BIT);
                esp_zb_stop();
            }
        }
        break;

    case ESP_ZB_ZCL_OTA_UPGRADE_STATUS_APPLY:
        if (s_ota_in_progress) {
            if (esp_ota_end(s_ota_handle) == ESP_OK &&
                esp_ota_set_boot_partition(s_ota_partition) == ESP_OK) {
                ESP_LOGI(TAG, "OTA complete — rebooting");
                esp_restart();
            } else {
                ESP_LOGE(TAG, "OTA finalise failed — aborting");
                s_ota_in_progress = false;
                xEventGroupSetBits(s_events, FAIL_BIT);
                esp_zb_stop();
            }
        }
        break;

    case ESP_ZB_ZCL_OTA_UPGRADE_STATUS_FINISH:
        ESP_LOGI(TAG, "OTA finished by stack");
        break;

    default:
        break;
    }
    return ESP_OK;
}

static void send_reports(void)
{
    /* Water level — Analog Input cluster, endpoint 1 */
    esp_zb_zcl_set_attribute_val(EP_LEVEL,
        ESP_ZB_ZCL_CLUSTER_ID_ANALOG_INPUT, ESP_ZB_ZCL_CLUSTER_SERVER_ROLE,
        ESP_ZB_ZCL_ATTR_ANALOG_INPUT_PRESENT_VALUE_ID, &s_level_m, false);

    esp_zb_zcl_report_attr_cmd_t report = {
        .zcl_basic_cmd = {
            .dst_addr_u.addr_short = 0x0000,
            .dst_endpoint          = 1,
            .src_endpoint          = EP_LEVEL,
        },
        .address_mode = ESP_ZB_APS_ADDR_MODE_16_ENDP_PRESENT,
        .clusterID    = ESP_ZB_ZCL_CLUSTER_ID_ANALOG_INPUT,
        .attributeID  = ESP_ZB_ZCL_ATTR_ANALOG_INPUT_PRESENT_VALUE_ID,
        .direction    = ESP_ZB_ZCL_CMD_DIRECTION_TO_CLI,
    };
    esp_zb_zcl_report_attr_cmd_req(&report);

#if CONFIG_WELLD_BATT_ADC_CHANNEL >= 0
    /* Battery voltage — Analog Input cluster, endpoint 2 */
    if (s_battery_v >= 0.0f) {
        esp_zb_zcl_set_attribute_val(EP_BATTERY,
            ESP_ZB_ZCL_CLUSTER_ID_ANALOG_INPUT, ESP_ZB_ZCL_CLUSTER_SERVER_ROLE,
            ESP_ZB_ZCL_ATTR_ANALOG_INPUT_PRESENT_VALUE_ID, &s_battery_v, false);
        report.zcl_basic_cmd.src_endpoint = EP_BATTERY;
        esp_zb_zcl_report_attr_cmd_req(&report);
    }
#endif

    /* Temperature — Temperature Measurement cluster (0x0402), endpoint 3 */
    if (s_temperature_c > -127.0f) {
        int16_t temp_zb = (int16_t)(s_temperature_c * 100.0f);
        esp_zb_zcl_set_attribute_val(EP_TEMPERATURE,
            ESP_ZB_ZCL_CLUSTER_ID_TEMP_MEASUREMENT, ESP_ZB_ZCL_CLUSTER_SERVER_ROLE,
            ESP_ZB_ZCL_ATTR_TEMP_MEASUREMENT_VALUE_ID, &temp_zb, false);

        esp_zb_zcl_report_attr_cmd_t temp_report = {
            .zcl_basic_cmd = {
                .dst_addr_u.addr_short = 0x0000,
                .dst_endpoint          = 1,
                .src_endpoint          = EP_TEMPERATURE,
            },
            .address_mode = ESP_ZB_APS_ADDR_MODE_16_ENDP_PRESENT,
            .clusterID    = ESP_ZB_ZCL_CLUSTER_ID_TEMP_MEASUREMENT,
            .attributeID  = ESP_ZB_ZCL_ATTR_TEMP_MEASUREMENT_VALUE_ID,
            .direction    = ESP_ZB_ZCL_CMD_DIRECTION_TO_CLI,
        };
        esp_zb_zcl_report_attr_cmd_req(&temp_report);
    }

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
            ESP_LOGI(TAG, "joined; reporting level=%.2f m battery=%.2f V temp=%.1f °C",
                     s_level_m, s_battery_v, s_temperature_c);
            send_reports();
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

static esp_zb_attribute_list_t *make_ai_cluster(float initial_value)
{
    esp_zb_analog_input_cluster_cfg_t cfg = {
        .out_of_service = 0,
        .present_value  = initial_value,
        .status_flags   = 0,
    };
    return esp_zb_analog_input_cluster_create(&cfg);
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
            .ed_timeout = ESP_ZB_ED_AGING_TIMEOUT_256MIN,
            .keep_alive = 3000,
        },
    };
    esp_zb_init(&nwk_cfg);
    esp_zb_core_action_handler_register(zb_action_handler);

    /* Build ZCL sw_build_id string from the app version baked in at compile time */
    const char *ver = esp_app_get_description()->version;
    size_t ver_len = strlen(ver);
    if (ver_len > 16) ver_len = 16;
    s_sw_build_id[0] = (char)ver_len;
    memcpy(s_sw_build_id + 1, ver, ver_len);

    /* Basic cluster with device identity */
    esp_zb_basic_cluster_cfg_t basic_cfg = {
        .zcl_version = ESP_ZB_ZCL_BASIC_ZCL_VERSION_DEFAULT_VALUE,
        .power_source = 0x03,  /* battery */
    };
    esp_zb_attribute_list_t *basic_attrs = esp_zb_basic_cluster_create(&basic_cfg);
    esp_zb_basic_cluster_add_attr(basic_attrs,
        ESP_ZB_ZCL_ATTR_BASIC_MANUFACTURER_NAME_ID, s_manufacturer);
    esp_zb_basic_cluster_add_attr(basic_attrs,
        ESP_ZB_ZCL_ATTR_BASIC_MODEL_IDENTIFIER_ID,  s_model);
    esp_zb_basic_cluster_add_attr(basic_attrs,
        ESP_ZB_ZCL_ATTR_BASIC_SW_BUILD_ID,          s_sw_build_id);

    esp_zb_ep_list_t *ep_list = esp_zb_ep_list_create();
    esp_zb_endpoint_config_t ep_cfg = {
        .app_profile_id     = ESP_ZB_AF_HA_PROFILE_ID,
        .app_device_id      = ESP_ZB_HA_SIMPLE_SENSOR_DEVICE_ID,
        .app_device_version = 0,
    };

    /* Endpoint 1 — water level (Analog Input) */
    esp_zb_cluster_list_t *level_clusters = esp_zb_zcl_cluster_list_create();
    ESP_ERROR_CHECK(esp_zb_cluster_list_add_basic_cluster(level_clusters, basic_attrs,
                                                          ESP_ZB_ZCL_CLUSTER_SERVER_ROLE));
    ESP_ERROR_CHECK(esp_zb_cluster_list_add_analog_input_cluster(level_clusters,
                                                                  make_ai_cluster(s_level_m),
                                                                  ESP_ZB_ZCL_CLUSTER_SERVER_ROLE));

    /* OTA upgrade client on endpoint 1 */
    esp_zb_ota_upgrade_cluster_cfg_t ota_cfg = {
        .ota_upgrade_downloaded_file_ver = 0x00000001,
        .ota_upgrade_manufacturer        = 0xFFFF,
        .ota_upgrade_image_type          = 0xFFFF,
        .ota_upgrade_query_jitter        = 100,
        .ota_upgrade_current_time        = 0,
        .ota_upgrade_server_addr         = 0xFFFF,
        .ota_upgrade_server_ep           = 0xFF,
    };
    esp_zb_ota_upgrade_client_variable_t ota_var = {
        .timer_query   = ESP_ZB_ZCL_OTA_UPGRADE_QUERY_TIMER_COUNT_DEF,
        .hw_version    = 0x0001,
        .max_data_size = 64,
    };
    esp_zb_attribute_list_t *ota_attrs = esp_zb_ota_upgrade_cluster_create(&ota_cfg);
    esp_zb_ota_upgrade_cluster_add_attr(ota_attrs,
        ESP_ZB_ZCL_ATTR_OTA_UPGRADE_CLIENT_DATA_ID, &ota_var);
    ESP_ERROR_CHECK(esp_zb_cluster_list_add_ota_upgrade_cluster(level_clusters,
        ota_attrs, ESP_ZB_ZCL_CLUSTER_CLIENT_ROLE));

    ep_cfg.endpoint = EP_LEVEL;
    ESP_ERROR_CHECK(esp_zb_ep_list_add_ep(ep_list, level_clusters, ep_cfg));

#if CONFIG_WELLD_BATT_ADC_CHANNEL >= 0
    /* Endpoint 2 — battery voltage (Analog Input) */
    esp_zb_cluster_list_t *batt_clusters = esp_zb_zcl_cluster_list_create();
    ESP_ERROR_CHECK(esp_zb_cluster_list_add_analog_input_cluster(batt_clusters,
                                                                  make_ai_cluster(s_battery_v),
                                                                  ESP_ZB_ZCL_CLUSTER_SERVER_ROLE));
    ep_cfg.endpoint = EP_BATTERY;
    ESP_ERROR_CHECK(esp_zb_ep_list_add_ep(ep_list, batt_clusters, ep_cfg));
#endif

    /* Endpoint 3 — water temperature (Temperature Measurement, 0x0402) */
    int16_t temp_zb = (s_temperature_c > -127.0f) ? (int16_t)(s_temperature_c * 100.0f) : 0x8000;
    esp_zb_temperature_meas_cluster_cfg_t temp_cfg = {
        .measured_value = temp_zb,
        .min_value      = -4000,   /* -40.00 °C */
        .max_value      =  12500,  /* 125.00 °C */
    };
    esp_zb_cluster_list_t *temp_clusters = esp_zb_zcl_cluster_list_create();
    ESP_ERROR_CHECK(esp_zb_cluster_list_add_temperature_meas_cluster(temp_clusters,
                                                                      esp_zb_temperature_meas_cluster_create(&temp_cfg),
                                                                      ESP_ZB_ZCL_CLUSTER_SERVER_ROLE));
    ep_cfg.endpoint = EP_TEMPERATURE;
    ESP_ERROR_CHECK(esp_zb_ep_list_add_ep(ep_list, temp_clusters, ep_cfg));

    esp_zb_device_register(ep_list);

    esp_zb_set_primary_network_channel_set(CONFIG_WELLD_ZIGBEE_CHANNEL_MASK);
    ESP_ERROR_CHECK(esp_zb_start(false));
    esp_zb_scheduler_alarm(zb_timeout_alarm, 0, TOTAL_TIMEOUT_MS);
    esp_zb_main_loop_iteration();
    xEventGroupSetBits(s_events, STOPPED_BIT);
    vTaskDelete(NULL);
}

bool zigbee_send(float level_m, float battery_v, float temperature_c)
{
    s_level_m      = level_m;
    s_battery_v    = battery_v;
    s_temperature_c = temperature_c;
    s_events       = xEventGroupCreate();

    if (xTaskCreate(zb_task, "zb_task", 8192, NULL, 5, NULL) != pdPASS) {
        ESP_LOGE(TAG, "failed to create Zigbee task");
        vEventGroupDelete(s_events);
        return false;
    }

    EventBits_t bits = xEventGroupWaitBits(s_events, SENT_BIT | FAIL_BIT,
                                           pdFALSE, pdFALSE,
                                           pdMS_TO_TICKS(TOTAL_TIMEOUT_MS + 5000));
    /* wait for the radio to be released before entering deep sleep */
    xEventGroupWaitBits(s_events, STOPPED_BIT, pdFALSE, pdFALSE, pdMS_TO_TICKS(5000));
    vEventGroupDelete(s_events);
    return (bits & SENT_BIT) != 0;
}
