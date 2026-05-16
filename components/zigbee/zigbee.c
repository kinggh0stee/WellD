#include "zigbee.h"
#include "welld_core.h"
#include "esp_zigbee_core.h"
#include "esp_app_desc.h"
#include "esp_ota_ops.h"
#include "esp_system.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/event_groups.h"
#include "freertos/task.h"
#include "sdkconfig.h"
#include <math.h>
#include <string.h>

static const char *TAG = "zigbee";

#define EP_LEVEL         1
#define EP_BATTERY       2
#define EP_TEMPERATURE   3
#define EP_RATE          4
#define SEND_DELAY_MS    CONFIG_WELLD_ZIGBEE_SEND_DELAY_MS
#define TOTAL_TIMEOUT_MS 25000  /* max time to find coordinator before giving up */

/* OTA image identity — both fields must match the header of every .zigbee file
   built for this device. Using 0xFFFF (wildcard) would accept images from any
   OTA server with any manufacturer code, which is a security risk. */
#define OTA_MANUFACTURER_CODE  0x1234
#define OTA_IMAGE_TYPE         0x0001

/* Event bits used to synchronise zb_task with zigbee_send() on the main task */
#define SENT_BIT    BIT0   /* reports were queued and SEND_DELAY_MS elapsed */
#define FAIL_BIT    BIT1   /* coordinator not found, steering failed, or OTA error */
#define STOPPED_BIT BIT2   /* esp_zb_stack_main_loop_iteration loop has exited; radio is free */

/* ZCL character strings: first byte is length, no null terminator */
static char s_manufacturer[] = "\x05WellD";
static char s_model[]        = "\x08WellD-v1";
static char s_sw_build_id[18]; /* 1-byte length prefix + up to 16 chars */

/* Sensor values captured by zigbee_send() before starting zb_task */
static EventGroupHandle_t s_events;
static float s_level_m;
static float s_battery_v;
static float s_temperature_c;
static float s_rate_cm_per_hour;  /* NaN = "no history yet", do not report */

/* volatile because s_ota_in_progress is written inside zb_task (via the Zigbee
   stack callbacks) and read by the alarm callbacks in the same task context —
   volatile prevents the compiler from caching the value across calls. */
static volatile bool   s_ota_in_progress = false;
static volatile bool   s_stop_requested  = false;
static int64_t         s_ota_start_us    = 0;   /* wall-clock time when OTA began */
static esp_ota_handle_t s_ota_handle     = 0;
static const esp_partition_t *s_ota_partition = NULL;

/* Fired TOTAL_TIMEOUT_MS after the Zigbee loop starts. If OTA is in progress
   we reschedule rather than killing the loop — OTA can take many minutes.
   Uses a wall-clock check (240 s) to abort stalled downloads rather than a
   reschedule counter, so the limit is independent of TOTAL_TIMEOUT_MS.
   Once OTA finishes (reboot) or fails (clears s_ota_in_progress), the next
   fire stops the loop with FAIL_BIT to wake zigbee_send(). */
static void zb_timeout_alarm(uint8_t param)
{
    if (s_ota_in_progress) {
        int64_t elapsed_s = (esp_timer_get_time() - s_ota_start_us) / 1000000LL;
        if (elapsed_s >= 240) {
            ESP_LOGE(TAG, "OTA stalled after %lld s, aborting", (long long)elapsed_s);
            esp_ota_abort(s_ota_handle);
            s_ota_in_progress = false;
            xEventGroupSetBits(s_events, FAIL_BIT);
            s_stop_requested = true;
            return;
        }
        esp_zb_scheduler_alarm(zb_timeout_alarm, 0, TOTAL_TIMEOUT_MS);
        return;
    }
    ESP_LOGE(TAG, "timeout — no coordinator found");
    xEventGroupSetBits(s_events, FAIL_BIT);
    s_stop_requested = true;
}

/* Fired SEND_DELAY_MS after reports are queued, giving the stack time to
   transmit and receive an ACK from the coordinator. If OTA started within
   that window (coordinator responded with an image) we return early to keep
   the loop alive; zb_timeout_alarm (or an OTA failure path) stops it later. */
static void zb_finish_alarm(uint8_t param)
{
    if (s_ota_in_progress) {
        return;
    }
    xEventGroupSetBits(s_events, SENT_BIT);
    s_stop_requested = true;
}

/* OTA state machine — called by the Zigbee stack for every OTA upgrade event.
 *
 * Flow:
 *   STATUS_START   → find the next OTA partition, open an esp_ota handle
 *   STATUS_RECEIVE → write each 128-byte block to flash as it arrives
 *   STATUS_APPLY   → validate and commit the image, set boot partition, reboot
 *
 * On any failure we abort the OTA handle, clear s_ota_in_progress, and stop
 * the Zigbee loop immediately rather than waiting for zb_timeout_alarm (which
 * could be up to TOTAL_TIMEOUT_MS away after it last rescheduled itself). */
static esp_err_t zb_action_handler(esp_zb_core_action_callback_id_t callback_id,
                                    const void *message)
{
    if (callback_id != ESP_ZB_CORE_OTA_UPGRADE_VALUE_CB_ID) return ESP_OK;
    const esp_zb_zcl_ota_upgrade_value_message_t *msg = message;

    switch (msg->upgrade_status) {
    case ESP_ZB_ZCL_OTA_UPGRADE_STATUS_START:
        /* Record wall-clock start time for the 240 s stall-detection window */
        s_ota_start_us = esp_timer_get_time();
        /* esp_ota_get_next_update_partition selects whichever of ota_0/ota_1
           is not currently running, so we always write to the inactive slot */
        s_ota_partition = esp_ota_get_next_update_partition(NULL);
        if (!s_ota_partition) {
            ESP_LOGE(TAG, "OTA: no update partition found");
            break;
        }
        if (esp_ota_begin(s_ota_partition, OTA_SIZE_UNKNOWN, &s_ota_handle) == ESP_OK) {
            s_ota_in_progress = true;
            ESP_LOGI(TAG, "OTA started → %s", s_ota_partition->label);
        } else {
            ESP_LOGE(TAG, "OTA: esp_ota_begin failed");
        }
        break;

    case ESP_ZB_ZCL_OTA_UPGRADE_STATUS_RECEIVE:
        if (s_ota_in_progress && msg->payload && msg->payload_size > 0) {
            if (esp_ota_write(s_ota_handle, msg->payload, msg->payload_size) != ESP_OK) {
                ESP_LOGE(TAG, "OTA write failed — aborting");
                esp_ota_abort(s_ota_handle);
                s_ota_in_progress = false;
                /* zb_finish_alarm already returned early; stop now rather than
                   waiting up to TOTAL_TIMEOUT_MS for zb_timeout_alarm to fire */
                xEventGroupSetBits(s_events, FAIL_BIT);
                s_stop_requested = true;
            }
        }
        break;

    case ESP_ZB_ZCL_OTA_UPGRADE_STATUS_APPLY:
        if (s_ota_in_progress) {
            /* esp_ota_end validates the image SHA-256 and marks it valid.
               esp_ota_set_boot_partition updates the otadata partition so the
               bootloader selects the new image on next boot. */
            if (esp_ota_end(s_ota_handle) == ESP_OK &&
                esp_ota_set_boot_partition(s_ota_partition) == ESP_OK) {
                ESP_LOGI(TAG, "OTA complete — rebooting");
                esp_restart();
            } else {
                ESP_LOGE(TAG, "OTA finalise failed — aborting");
                s_ota_in_progress = false;
                xEventGroupSetBits(s_events, FAIL_BIT);
                s_stop_requested = true;
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

/* Queue unsolicited attribute reports to the coordinator (short addr 0x0000).
 * We set the attribute value first so the stack reads the latest value when it
 * builds the report frame, then schedule zb_finish_alarm to stop the loop
 * after SEND_DELAY_MS — long enough for the coordinator to ACK. */
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
    /* Battery voltage — Analog Input cluster, endpoint 2.
       Skip report if ADC returned -1 (disabled or read error). */
    if (welld_zb_should_report_battery(s_battery_v)) {
        esp_zb_zcl_set_attribute_val(EP_BATTERY,
            ESP_ZB_ZCL_CLUSTER_ID_ANALOG_INPUT, ESP_ZB_ZCL_CLUSTER_SERVER_ROLE,
            ESP_ZB_ZCL_ATTR_ANALOG_INPUT_PRESENT_VALUE_ID, &s_battery_v, false);
        report.zcl_basic_cmd.src_endpoint = EP_BATTERY;
        esp_zb_zcl_report_attr_cmd_req(&report);
    }
#endif

    /* Temperature — Temperature Measurement cluster (0x0402), endpoint 3.
       Skip report if DS18B20 returned -127 (not found or out of range). */
    if (s_temperature_c > -127.0f) {
        int16_t temp_zb = welld_zb_encode_temp(s_temperature_c);
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

    /* Level rate of change — Analog Input cluster, endpoint 4.
       Skip report if NaN (no previous reading to compare against). */
    if (!isnan(s_rate_cm_per_hour)) {
        esp_zb_zcl_set_attribute_val(EP_RATE,
            ESP_ZB_ZCL_CLUSTER_ID_ANALOG_INPUT, ESP_ZB_ZCL_CLUSTER_SERVER_ROLE,
            ESP_ZB_ZCL_ATTR_ANALOG_INPUT_PRESENT_VALUE_ID, &s_rate_cm_per_hour, false);
        report.zcl_basic_cmd.src_endpoint = EP_RATE;
        esp_zb_zcl_report_attr_cmd_req(&report);
    }

    /* Give the stack SEND_DELAY_MS to transmit before we declare success */
    esp_zb_scheduler_alarm(zb_finish_alarm, 0, SEND_DELAY_MS);
}

/* Called by the Zigbee stack from within the main loop task (zb_task).
 * Drives the BDB commissioning state machine:
 *   SKIP_STARTUP → INITIALIZATION → NETWORK_STEERING → send reports */
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
            /* Stack initialised; begin network steering (scan + join) */
            esp_zb_bdb_start_top_level_commissioning(ESP_ZB_BDB_MODE_NETWORK_STEERING);
        } else {
            ESP_LOGE(TAG, "init failed (err=%d)", err_status);
            xEventGroupSetBits(s_events, FAIL_BIT);
            s_stop_requested = true;
        }
        break;
    case ESP_ZB_BDB_SIGNAL_STEERING:
        if (err_status == ESP_OK) {
            if (isnan(s_rate_cm_per_hour)) {
                ESP_LOGI(TAG, "joined; reporting level=%.3f m temp=%.1f C batt=%.2f V rate=n/a",
                         s_level_m, s_temperature_c, s_battery_v);
            } else {
                ESP_LOGI(TAG, "joined; reporting level=%.3f m temp=%.1f C batt=%.2f V rate=%.1f cm/h",
                         s_level_m, s_temperature_c, s_battery_v, s_rate_cm_per_hour);
            }
            send_reports();
        } else {
            ESP_LOGE(TAG, "steering failed (err=%d)", err_status);
            xEventGroupSetBits(s_events, FAIL_BIT);
            s_stop_requested = true;
        }
        break;
    default:
        break;
    }
}

/* Create an Analog Input cluster initialised to initial_value.
 * Used for both the water level and battery voltage endpoints. */
static esp_zb_attribute_list_t *make_ai_cluster(float initial_value)
{
    esp_zb_analog_input_cluster_cfg_t cfg = {
        .out_of_service = 0,
        .present_value  = initial_value,
        .status_flags   = 0,
    };
    return esp_zb_analog_input_cluster_create(&cfg);
}

/* FreeRTOS task that owns the Zigbee radio for one wakeup cycle:
 *   1. Init the stack as an End Device
 *   2. Register clusters and endpoints
 *   3. Poll esp_zb_stack_main_loop_iteration() until s_stop_requested is set
 *   4. Set STOPPED_BIT so zigbee_send() knows the radio is released */
static void zb_task(void *pvParameters)
{
    esp_zb_platform_config_t platform_cfg = {
        .radio_config = {.radio_mode = ZB_RADIO_MODE_NATIVE},
        .host_config  = {.host_connection_mode = ZB_HOST_CONNECTION_MODE_NONE},
    };
    ESP_ERROR_CHECK(esp_zb_platform_config(&platform_cfg));

    /* Configure as a Zigbee End Device (not router/coordinator).
     * ed_timeout: how long the coordinator keeps this device in its child
     *   table between polls — 256 min >> sleep interval, so the parent
     *   never ages us out between wakeups.
     * keep_alive: poll interval in ms while awake (unused in deep-sleep
     *   architecture but required by the stack). */
    esp_zb_cfg_t nwk_cfg = {
        .esp_zb_role         = ESP_ZB_DEVICE_TYPE_ED,
        .install_code_policy = false,
        .nwk_cfg.zed_cfg = {
            .ed_timeout = ESP_ZB_ED_AGING_TIMEOUT_256MIN,
            .keep_alive = 3000,
        },
    };
    esp_zb_init(&nwk_cfg);
    /* Register OTA callback before starting the stack */
    esp_zb_core_action_handler_register(zb_action_handler);

    /* Build ZCL sw_build_id string from the app version baked in at compile time */
    welld_pack_zcl_string(s_sw_build_id, sizeof(s_sw_build_id),
                          esp_app_get_description()->version);

    /* Basic cluster — device identity visible in Zigbee2MQTT and HA */
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

    /* Endpoint 1 — water level (Analog Input).
     * Also hosts the Basic cluster (required on EP1) and the OTA client. */
    esp_zb_cluster_list_t *level_clusters = esp_zb_zcl_cluster_list_create();
    ESP_ERROR_CHECK(esp_zb_cluster_list_add_basic_cluster(level_clusters, basic_attrs,
                                                          ESP_ZB_ZCL_CLUSTER_SERVER_ROLE));
    ESP_ERROR_CHECK(esp_zb_cluster_list_add_analog_input_cluster(level_clusters,
                                                                  make_ai_cluster(s_level_m),
                                                                  ESP_ZB_ZCL_CLUSTER_SERVER_ROLE));

    /* OTA upgrade client on endpoint 1.
     * ota_upgrade_server_addr = 0xFFFF: discover the OTA server by broadcast
     *   rather than hardcoding a coordinator address.
     * ota_upgrade_query_jitter: random delay (0–100 %) before querying,
     *   prevents all devices on the network querying simultaneously. */
    esp_zb_ota_cluster_cfg_t ota_cfg = {
        .ota_upgrade_file_version        = OTA_FW_VERSION,
        .ota_upgrade_downloaded_file_ver = OTA_FW_VERSION,
        .ota_upgrade_manufacturer        = OTA_MANUFACTURER_CODE,
        .ota_upgrade_image_type          = OTA_IMAGE_TYPE,
    };
    esp_zb_zcl_ota_upgrade_client_variable_t ota_var = {
        .timer_query   = ESP_ZB_ZCL_OTA_UPGRADE_QUERY_TIMER_COUNT_DEF,
        .hw_version    = 0x0001,
        .max_data_size = 128,  /* bytes per block; larger = faster download */
    };
    uint16_t ota_server_addr = 0xFFFF;  /* discover by broadcast */
    uint8_t  ota_server_ep   = 0xFF;
    esp_zb_attribute_list_t *ota_attrs = esp_zb_ota_cluster_create(&ota_cfg);
    esp_zb_ota_cluster_add_attr(ota_attrs, ESP_ZB_ZCL_ATTR_OTA_UPGRADE_CLIENT_DATA_ID, &ota_var);
    esp_zb_ota_cluster_add_attr(ota_attrs, ESP_ZB_ZCL_ATTR_OTA_UPGRADE_SERVER_ADDR_ID, &ota_server_addr);
    esp_zb_ota_cluster_add_attr(ota_attrs, ESP_ZB_ZCL_ATTR_OTA_UPGRADE_SERVER_ENDPOINT_ID, &ota_server_ep);
    ESP_ERROR_CHECK(esp_zb_cluster_list_add_ota_cluster(level_clusters,
        ota_attrs, ESP_ZB_ZCL_CLUSTER_CLIENT_ROLE));

    ep_cfg.endpoint = EP_LEVEL;
    ESP_ERROR_CHECK(esp_zb_ep_list_add_ep(ep_list, level_clusters, ep_cfg));

#if CONFIG_WELLD_BATT_ADC_CHANNEL >= 0
    /* Endpoint 2 — battery voltage (Analog Input).
     * The Z2M converter converts this to a percentage using configurable
     * full/empty voltage thresholds, avoiding hard-coding chemistry in fw. */
    esp_zb_cluster_list_t *batt_clusters = esp_zb_zcl_cluster_list_create();
    ESP_ERROR_CHECK(esp_zb_cluster_list_add_analog_input_cluster(batt_clusters,
                                                                  make_ai_cluster(s_battery_v),
                                                                  ESP_ZB_ZCL_CLUSTER_SERVER_ROLE));
    ep_cfg.endpoint = EP_BATTERY;
    ESP_ERROR_CHECK(esp_zb_ep_list_add_ep(ep_list, batt_clusters, ep_cfg));
#endif

    /* Endpoint 3 — water temperature (Temperature Measurement, cluster 0x0402).
     * welld_zb_encode_temp returns 0x8000 (ZCL invalid) when no sensor present. */
    int16_t temp_zb = welld_zb_encode_temp(s_temperature_c);
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

    /* Endpoint 4 — level rate of change in cm/h (Analog Input).
     * Always registered so the device descriptor is stable across wakeups;
     * reports are conditionally suppressed in send_reports() when there is
     * no previous reading to compare against (first valid wakeup). */
    float initial_rate = isnan(s_rate_cm_per_hour) ? 0.0f : s_rate_cm_per_hour;
    esp_zb_cluster_list_t *rate_clusters = esp_zb_zcl_cluster_list_create();
    ESP_ERROR_CHECK(esp_zb_cluster_list_add_analog_input_cluster(rate_clusters,
                                                                  make_ai_cluster(initial_rate),
                                                                  ESP_ZB_ZCL_CLUSTER_SERVER_ROLE));
    ep_cfg.endpoint = EP_RATE;
    ESP_ERROR_CHECK(esp_zb_ep_list_add_ep(ep_list, rate_clusters, ep_cfg));

    esp_zb_device_register(ep_list);

    esp_zb_set_primary_network_channel_set(CONFIG_WELLD_ZIGBEE_CHANNEL_MASK);
    ESP_ERROR_CHECK(esp_zb_start(false));
    /* Arm the watchdog alarm before entering the blocking main loop */
    esp_zb_scheduler_alarm(zb_timeout_alarm, 0, TOTAL_TIMEOUT_MS);
    while (!s_stop_requested) {
        esp_zb_stack_main_loop_iteration();
    }
    s_stop_requested = false;
    xEventGroupSetBits(s_events, STOPPED_BIT);
    vTaskDelete(NULL);
}

/* Send sensor readings over Zigbee and block until the radio is released.
 *
 * Lifecycle:
 *   1. Store readings in module-level globals (read by zb_task/send_reports)
 *   2. Spawn zb_task which initialises the stack and joins the network
 *   3. Wait for SENT_BIT (success) or FAIL_BIT (timeout / error)
 *   4. Wait for STOPPED_BIT before returning — ensures the IEEE 802.15.4
 *      radio is fully idle before the caller enters deep sleep
 *
 * Returns true if SENT_BIT was set (coordinator acknowledged). */
bool zigbee_send(float level_m,
                 float battery_v,
                 float temperature_c,
                 float rate_cm_per_hour)
{
    s_level_m           = level_m;
    s_battery_v         = battery_v;
    s_temperature_c     = temperature_c;
    s_rate_cm_per_hour  = rate_cm_per_hour;
    s_events            = xEventGroupCreate();

    if (xTaskCreate(zb_task, "zb_task", 10240, NULL, 5, NULL) != pdPASS) {
        ESP_LOGE(TAG, "failed to create Zigbee task");
        vEventGroupDelete(s_events);
        return false;
    }

    EventBits_t bits = xEventGroupWaitBits(s_events, SENT_BIT | FAIL_BIT,
                                           pdFALSE, pdFALSE,
                                           pdMS_TO_TICKS(TOTAL_TIMEOUT_MS + 5000));
    /* Wait for the radio to be released before entering deep sleep */
    xEventGroupWaitBits(s_events, STOPPED_BIT, pdFALSE, pdFALSE, pdMS_TO_TICKS(5000));
    vEventGroupDelete(s_events);
    return (bits & SENT_BIT) != 0;
}
