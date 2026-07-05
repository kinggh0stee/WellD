#include "zigbee.h"
#include "welld_core.h"
#include "esp_zigbee.h"
#include "ezbee/zcl/zcl_core.h"
#include "ezbee/zcl/cluster/basic_desc.h"
#include "ezbee/zcl/cluster/analog_input_desc.h"
#include "ezbee/zcl/cluster/temperature_measurement_desc.h"
#include "ezbee/zcl/cluster/ota_upgrade_desc.h"
#include "ezbee/zcl/cluster/ota_upgrade.h"
#include "ezbee/zcl/zcl_general_cmd.h"
#include "ezbee/zha.h"
#include "esp_app_desc.h"
#include "esp_ota_ops.h"
#include "esp_system.h"
#include "esp_random.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/event_groups.h"
#include "freertos/task.h"
#include "freertos/timers.h"
#include "sdkconfig.h"
#include <math.h>
#include <string.h>

static const char *TAG = "zigbee";

#define EP_LEVEL         1
#define EP_BATTERY       2
#define EP_TEMPERATURE   3
#define EP_RATE          4
#define EP_FAILS         5
#define EP_LQI           6
#define EP_SOLAR         7
#define SEND_DELAY_MS    CONFIG_WELLD_ZIGBEE_SEND_DELAY_MS
#define TOTAL_TIMEOUT_MS 25000  /* max time to find coordinator before giving up */

/* OTA image identity — both fields must match the header of every .zigbee file
   built for this device. Using 0xFFFF (wildcard) would accept images from any
   OTA server with any manufacturer code (a security risk — a rogue OTA server
   on the same Zigbee network could flash arbitrary firmware).
   0x1234 / 0x0001 are placeholder values; a production deployment should use
   an allocated Zigbee Alliance manufacturer code for 0x1234. The device
   rejects images where either field mismatches, making these a meaningful
   access-control check even with placeholder values. */
#define OTA_MANUFACTURER_CODE  0x1234
#define OTA_IMAGE_TYPE         0x0001

/* Event bits used to synchronise zb_task with zigbee_send() on the main task */
#define SENT_BIT    BIT0   /* reports were queued and SEND_DELAY_MS elapsed */
#define FAIL_BIT    BIT1   /* coordinator not found, steering failed, or OTA error */
#define STOPPED_BIT BIT2   /* mainloop has exited; radio is free */

/* ZCL character strings: first byte is length, no null terminator */
static char s_manufacturer[] = "\x05WellD";
static char s_model[]        = "\x08WellD-v1";
static char s_sw_build_id[18]; /* 1-byte length prefix + up to 16 chars */

/* Sensor values written by zigbee_send() (main task) and read by zb_task.
 * A portMEMORY_BARRIER() in zigbee_send() orders the writes against the
 * xTaskCreate() call so the compiler cannot move them past task creation. */
static EventGroupHandle_t s_events;
static float s_level_m;
static float s_battery_v;
static float s_temperature_c;
static float s_rate_cm_per_hour;  /* NaN = "no history yet", do not report */
static bool  s_solar_charging;
static uint8_t s_store_count;
static const float *s_store_level_m;
static const float *s_store_battery_v;
static const float *s_store_temp_c;

/* volatile because s_ota_in_progress is written inside zb_task (via the Zigbee
   stack callbacks) and read by the alarm callbacks in the same task context —
   volatile prevents the compiler from caching the value across calls. */
static volatile bool   s_ota_in_progress  = false;
static volatile bool   s_ota_begin_failed = false;
static int64_t         s_ota_start_us    = 0;   /* wall-clock time when OTA began */
static esp_ota_handle_t s_ota_handle     = 0;
static const esp_partition_t *s_ota_partition = NULL;
static uint32_t        s_zb_fails        = 0;   /* copied from main task before xTaskCreate */

/* FreeRTOS software timers replace esp_zb_scheduler_alarm so we avoid
   including the deprecated compat header. Timer callbacks post work items
   into the Zigbee task queue via esp_zigbee_task_queue_post(). */
static TimerHandle_t s_timeout_timer = NULL;
static TimerHandle_t s_finish_timer  = NULL;

/* Forward declarations */
static void do_stop_sent(void *ctx);
static void do_timeout_check(void *ctx);

/* Fired TOTAL_TIMEOUT_MS after the Zigbee loop starts. If OTA is in progress
   we reschedule rather than killing the loop — OTA can take many minutes.
   Uses a wall-clock check (CONFIG_WELLD_OTA_STALL_TIMEOUT_SEC) to abort
   stalled downloads rather than a reschedule counter, so the limit is
   independent of TOTAL_TIMEOUT_MS.
   Once OTA finishes (reboot) or fails (clears s_ota_in_progress), the next
   fire stops the loop with FAIL_BIT to wake zigbee_send(). */
static void timeout_timer_cb(TimerHandle_t xTimer)
{
    esp_zigbee_task_queue_post(do_timeout_check, NULL);
}

/* Executed inside the Zigbee task context (via task_queue_post). */
static void do_timeout_check(void *ctx)
{
    if (s_ota_in_progress) {
        int64_t elapsed_s = (esp_timer_get_time() - s_ota_start_us) / 1000000LL;
        if (elapsed_s >= CONFIG_WELLD_OTA_STALL_TIMEOUT_SEC) {
            ESP_LOGE(TAG, "OTA stalled after %lld s, aborting", (long long)elapsed_s);
            esp_ota_abort(s_ota_handle);
            s_ota_in_progress = false;
            xEventGroupSetBits(s_events, FAIL_BIT);
            esp_zigbee_deinit();
            return;
        }
        /* Reschedule for another TOTAL_TIMEOUT_MS */
        xTimerReset(s_timeout_timer, 0);
        return;
    }
    ESP_LOGE(TAG, "timeout — no coordinator found");
    xEventGroupSetBits(s_events, FAIL_BIT);
    esp_zigbee_deinit();
}

/* Fired SEND_DELAY_MS after reports are queued, giving the stack time to
   transmit and receive an ACK from the coordinator. If OTA started within
   that window (coordinator responded with an image) we return early to keep
   the loop alive; do_timeout_check (or an OTA failure path) stops it later. */
static void finish_timer_cb(TimerHandle_t xTimer)
{
    esp_zigbee_task_queue_post(do_stop_sent, NULL);
}

static void do_stop_sent(void *ctx)
{
    if (s_ota_in_progress) {
        return;
    }
    if (s_ota_begin_failed) {
        xEventGroupSetBits(s_events, FAIL_BIT);
    } else {
        xEventGroupSetBits(s_events, SENT_BIT);
    }
    esp_zigbee_deinit();
}

/* OTA state machine — called by the Zigbee stack for every OTA upgrade event.
 *
 * Flow:
 *   PROGRESS_START     → find the next OTA partition, open an esp_ota handle
 *   PROGRESS_RECEIVING → write each 128-byte block to flash as it arrives
 *   PROGRESS_APPLY     → validate and commit the image, set boot partition, reboot
 *
 * On any failure we abort the OTA handle, clear s_ota_in_progress, and stop
 * the Zigbee loop immediately rather than waiting for do_timeout_check. */
static void zb_action_handler(ezb_zcl_core_action_callback_id_t callback_id, void *message)
{
    if (callback_id != EZB_ZCL_CORE_OTA_UPGRADE_CLIENT_PROGRESS_CB_ID) return;
    ezb_zcl_ota_upgrade_client_progress_message_t *msg = message;

    switch (msg->in.progress) {
    case EZB_ZCL_OTA_UPGRADE_PROGRESS_START:
        /* Record wall-clock start time for the stall-detection window */
        s_ota_start_us = esp_timer_get_time();
        /* esp_ota_get_next_update_partition selects whichever of ota_0/ota_1
           is not currently running, so we always write to the inactive slot */
        s_ota_partition = esp_ota_get_next_update_partition(NULL);
        if (!s_ota_partition) {
            ESP_LOGE(TAG, "OTA: no update partition found");
            msg->out.result = EZB_ZCL_STATUS_ABORT;
            return;
        }
        if (esp_ota_begin(s_ota_partition, OTA_SIZE_UNKNOWN, &s_ota_handle) == ESP_OK) {
            s_ota_in_progress = true;
            ESP_LOGI(TAG, "OTA started → %s", s_ota_partition->label);
        } else {
            ESP_LOGE(TAG, "OTA: esp_ota_begin failed");
            msg->out.result = EZB_ZCL_STATUS_ABORT;
            s_ota_begin_failed = true;
        }
        break;

    case EZB_ZCL_OTA_UPGRADE_PROGRESS_RECEIVING:
        if (s_ota_in_progress &&
            msg->in.receiving.block != NULL &&
            msg->in.receiving.block_size > 0) {
            if (esp_ota_write(s_ota_handle,
                              msg->in.receiving.block,
                              msg->in.receiving.block_size) != ESP_OK) {
                ESP_LOGE(TAG, "OTA write failed — aborting");
                esp_ota_abort(s_ota_handle);
                s_ota_in_progress = false;
                /* do_stop_sent already returned early; stop now */
                msg->out.result = EZB_ZCL_STATUS_ABORT;
                xEventGroupSetBits(s_events, FAIL_BIT);
                esp_zigbee_deinit();
            }
        }
        break;

    case EZB_ZCL_OTA_UPGRADE_PROGRESS_APPLY:
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
                msg->out.result = EZB_ZCL_STATUS_ABORT;
                xEventGroupSetBits(s_events, FAIL_BIT);
                esp_zigbee_deinit();
            }
        }
        break;

    case EZB_ZCL_OTA_UPGRADE_PROGRESS_ABORT:
        ESP_LOGW(TAG, "OTA aborted by stack");
        if (s_ota_in_progress) {
            esp_ota_abort(s_ota_handle);
            s_ota_in_progress = false;
            xEventGroupSetBits(s_events, FAIL_BIT);
            esp_zigbee_deinit();
        }
        break;

    case EZB_ZCL_OTA_UPGRADE_PROGRESS_FINISH:
        ESP_LOGI(TAG, "OTA finished by stack");
        break;

    default:
        break;
    }
}

/* Queue unsolicited attribute reports to the coordinator (short addr 0x0000).
 * We set the attribute value first so the stack reads the latest value when it
 * builds the report frame, then start the finish timer to stop the loop
 * after SEND_DELAY_MS — long enough for the coordinator to ACK. */
static void send_reports(void)
{
    /* Helper: build a report cmd for an Analog Input cluster endpoint */
    ezb_zcl_report_attr_cmd_t report = {
        .cmd_ctrl = {
            .dst_addr  = EZB_ADDRESS_SHORT(0x0000),
            .dst_ep    = 1,
            .src_ep    = EP_LEVEL,
            .cluster_id = EZB_ZCL_CLUSTER_ID_ANALOG_INPUT,
            .manuf_code = EZB_ZCL_STD_MANUF_CODE,
            .fc = { .direction = 1 },  /* to client */
        },
        .payload = { .attr_id = EZB_ZCL_ATTR_ANALOG_INPUT_PRESENT_VALUE_ID },
    };

    /* Store-and-forward burst: re-send previously-failed readings FIRST,
       oldest to newest, then the current reading below. Zigbee2MQTT keeps the
       last-received value per attribute, so the current reading must be the
       final report on each endpoint — bursting after it would leave the
       coordinator showing the oldest backlog entry until the next wakeup. */
    for (uint8_t i = 0; i < s_store_count; i++) {
        float burst_level = s_store_level_m[i];
        if (burst_level >= 0.0f) {
            ezb_zcl_set_attr_value(EP_LEVEL,
                EZB_ZCL_CLUSTER_ID_ANALOG_INPUT, EZB_ZCL_CLUSTER_SERVER,
                EZB_ZCL_ATTR_ANALOG_INPUT_PRESENT_VALUE_ID,
                EZB_ZCL_STD_MANUF_CODE, &burst_level, false);
            report.cmd_ctrl.src_ep = EP_LEVEL;
            ezb_zcl_report_attr_cmd_req(&report);
        }
#if CONFIG_WELLD_BATT_ADC_CHANNEL >= 0
        /* Same compile-time gate as the EP_BATTERY endpoint registration:
           without it the burst would report on an unregistered endpoint. */
        float burst_batt = s_store_battery_v[i];
        if (welld_zb_should_report_battery(burst_batt)) {
            ezb_zcl_set_attr_value(EP_BATTERY,
                EZB_ZCL_CLUSTER_ID_ANALOG_INPUT, EZB_ZCL_CLUSTER_SERVER,
                EZB_ZCL_ATTR_ANALOG_INPUT_PRESENT_VALUE_ID,
                EZB_ZCL_STD_MANUF_CODE, &burst_batt, false);
            report.cmd_ctrl.src_ep = EP_BATTERY;
            ezb_zcl_report_attr_cmd_req(&report);
        }
#endif
        if (s_store_temp_c[i] > -127.0f) {
            int16_t temp_zb = welld_zb_encode_temp(s_store_temp_c[i]);
            ezb_zcl_set_attr_value(EP_TEMPERATURE,
                EZB_ZCL_CLUSTER_ID_TEMPERATURE_MEASUREMENT, EZB_ZCL_CLUSTER_SERVER,
                EZB_ZCL_ATTR_TEMPERATURE_MEASUREMENT_MEASURED_VALUE_ID,
                EZB_ZCL_STD_MANUF_CODE, &temp_zb, false);
            ezb_zcl_report_attr_cmd_t burst_temp = {
                .cmd_ctrl = {
                    .dst_addr   = EZB_ADDRESS_SHORT(0x0000),
                    .dst_ep     = 1,
                    .src_ep     = EP_TEMPERATURE,
                    .cluster_id = EZB_ZCL_CLUSTER_ID_TEMPERATURE_MEASUREMENT,
                    .manuf_code = EZB_ZCL_STD_MANUF_CODE,
                    .fc = { .direction = 1 },
                },
                .payload = { .attr_id = EZB_ZCL_ATTR_TEMPERATURE_MEASUREMENT_MEASURED_VALUE_ID },
            };
            ezb_zcl_report_attr_cmd_req(&burst_temp);
        }
    }

    /* Water level — Analog Input cluster, endpoint 1 */
    ezb_zcl_set_attr_value(EP_LEVEL,
        EZB_ZCL_CLUSTER_ID_ANALOG_INPUT, EZB_ZCL_CLUSTER_SERVER,
        EZB_ZCL_ATTR_ANALOG_INPUT_PRESENT_VALUE_ID,
        EZB_ZCL_STD_MANUF_CODE, &s_level_m, false);

    report.cmd_ctrl.src_ep = EP_LEVEL;
    report.cmd_ctrl.cluster_id = EZB_ZCL_CLUSTER_ID_ANALOG_INPUT;
    report.payload.attr_id = EZB_ZCL_ATTR_ANALOG_INPUT_PRESENT_VALUE_ID;
    ezb_zcl_report_attr_cmd_req(&report);

#if CONFIG_WELLD_BATT_ADC_CHANNEL >= 0
    /* Battery voltage — Analog Input cluster, endpoint 2.
       Skip report if ADC returned -1 (disabled or read error). */
    if (welld_zb_should_report_battery(s_battery_v)) {
        ezb_zcl_set_attr_value(EP_BATTERY,
            EZB_ZCL_CLUSTER_ID_ANALOG_INPUT, EZB_ZCL_CLUSTER_SERVER,
            EZB_ZCL_ATTR_ANALOG_INPUT_PRESENT_VALUE_ID,
            EZB_ZCL_STD_MANUF_CODE, &s_battery_v, false);
        report.cmd_ctrl.src_ep = EP_BATTERY;
        ezb_zcl_report_attr_cmd_req(&report);
    }
#endif

    /* Temperature — Temperature Measurement cluster (0x0402), endpoint 3.
       Skip report if DS18B20 returned -127 (not found or out of range). */
    if (s_temperature_c > -127.0f) {
        int16_t temp_zb = welld_zb_encode_temp(s_temperature_c);
        ezb_zcl_set_attr_value(EP_TEMPERATURE,
            EZB_ZCL_CLUSTER_ID_TEMPERATURE_MEASUREMENT, EZB_ZCL_CLUSTER_SERVER,
            EZB_ZCL_ATTR_TEMPERATURE_MEASUREMENT_MEASURED_VALUE_ID,
            EZB_ZCL_STD_MANUF_CODE, &temp_zb, false);

        ezb_zcl_report_attr_cmd_t temp_report = {
            .cmd_ctrl = {
                .dst_addr   = EZB_ADDRESS_SHORT(0x0000),
                .dst_ep     = 1,
                .src_ep     = EP_TEMPERATURE,
                .cluster_id = EZB_ZCL_CLUSTER_ID_TEMPERATURE_MEASUREMENT,
                .manuf_code = EZB_ZCL_STD_MANUF_CODE,
                .fc = { .direction = 1 },
            },
            .payload = { .attr_id = EZB_ZCL_ATTR_TEMPERATURE_MEASUREMENT_MEASURED_VALUE_ID },
        };
        ezb_zcl_report_attr_cmd_req(&temp_report);
    }

    /* Level rate of change — Analog Input cluster, endpoint 4.
       Skip report if NaN (no previous reading to compare against). */
    if (!isnan(s_rate_cm_per_hour)) {
        ezb_zcl_set_attr_value(EP_RATE,
            EZB_ZCL_CLUSTER_ID_ANALOG_INPUT, EZB_ZCL_CLUSTER_SERVER,
            EZB_ZCL_ATTR_ANALOG_INPUT_PRESENT_VALUE_ID,
            EZB_ZCL_STD_MANUF_CODE, &s_rate_cm_per_hour, false);
        report.cmd_ctrl.src_ep = EP_RATE;
        ezb_zcl_report_attr_cmd_req(&report);
    }

    /* Zigbee failure counter — Analog Input cluster, endpoint 5.
       Reported as a float so the Z2M converter can treat it uniformly. */
    {
        float fails_f = (float)s_zb_fails;
        ezb_zcl_set_attr_value(EP_FAILS,
            EZB_ZCL_CLUSTER_ID_ANALOG_INPUT, EZB_ZCL_CLUSTER_SERVER,
            EZB_ZCL_ATTR_ANALOG_INPUT_PRESENT_VALUE_ID,
            EZB_ZCL_STD_MANUF_CODE, &fails_f, false);
        report.cmd_ctrl.src_ep = EP_FAILS;
        ezb_zcl_report_attr_cmd_req(&report);
    }

    /* Link quality (LQI) — Analog Input cluster, endpoint 6.
       TODO: read actual LQI from stack when API is available.
       For now report 0 (unknown) so the endpoint is stable. */
    {
        float lqi_f = 0.0f;
        ezb_zcl_set_attr_value(EP_LQI,
            EZB_ZCL_CLUSTER_ID_ANALOG_INPUT, EZB_ZCL_CLUSTER_SERVER,
            EZB_ZCL_ATTR_ANALOG_INPUT_PRESENT_VALUE_ID,
            EZB_ZCL_STD_MANUF_CODE, &lqi_f, false);
        report.cmd_ctrl.src_ep = EP_LQI;
        ezb_zcl_report_attr_cmd_req(&report);
    }

    /* Solar charging state — Analog Input cluster, endpoint 7.
       1.0 = charging, 0.0 = not charging. */
    {
        float solar_f = s_solar_charging ? 1.0f : 0.0f;
        ezb_zcl_set_attr_value(EP_SOLAR,
            EZB_ZCL_CLUSTER_ID_ANALOG_INPUT, EZB_ZCL_CLUSTER_SERVER,
            EZB_ZCL_ATTR_ANALOG_INPUT_PRESENT_VALUE_ID,
            EZB_ZCL_STD_MANUF_CODE, &solar_f, false);
        report.cmd_ctrl.src_ep = EP_SOLAR;
        ezb_zcl_report_attr_cmd_req(&report);
    }

    /* Give the stack SEND_DELAY_MS to transmit before we declare success */
    xTimerStart(s_finish_timer, 0);
}

/* Application signal handler — called by the Zigbee stack from within the
 * mainloop task context. Drives the BDB commissioning state machine:
 *   SKIP_STARTUP → INITIALIZATION → NETWORK_STEERING → send reports
 * Returns true when the signal is handled (prevents further propagation). */
static bool zb_signal_handler(const ezb_app_signal_t *signal)
{
    ezb_app_signal_type_t sig_type = ezb_app_signal_get_type(signal);

    switch (sig_type) {
    case EZB_ZDO_SIGNAL_SKIP_STARTUP:
        if (CONFIG_WELLD_ZIGBEE_BACKOFF_MAX_MS > 0) {
            uint32_t backoff_ms = esp_random() % CONFIG_WELLD_ZIGBEE_BACKOFF_MAX_MS;
            if (backoff_ms > 0) {
                vTaskDelay(pdMS_TO_TICKS(backoff_ms));
                ESP_LOGI(TAG, "Zigbee steering backoff %lu ms", (unsigned long)backoff_ms);
            }
        }
        ezb_bdb_start_top_level_commissioning(EZB_BDB_MODE_INITIALIZATION);
        return true;

    case EZB_BDB_SIGNAL_DEVICE_FIRST_START:
    case EZB_BDB_SIGNAL_DEVICE_REBOOT: {
        const ezb_bdb_signal_simple_params_t *params = ezb_app_signal_get_params(signal);
        if (params->status == EZB_BDB_STATUS_SUCCESS) {
            /* Stack initialised; begin network steering (scan + join) */
            ezb_bdb_start_top_level_commissioning(EZB_BDB_MODE_NETWORK_STEERING);
        } else {
            ESP_LOGE(TAG, "init failed (status=%d)", params->status);
            xEventGroupSetBits(s_events, FAIL_BIT);
            esp_zigbee_deinit();
        }
        return true;
    }

    case EZB_BDB_SIGNAL_STEERING: {
        const ezb_bdb_signal_simple_params_t *params = ezb_app_signal_get_params(signal);
        if (params->status == EZB_BDB_STATUS_SUCCESS) {
            if (isnan(s_rate_cm_per_hour)) {
                ESP_LOGI(TAG, "joined; reporting level=%.3f m temp=%.1f C batt=%.2f V rate=n/a",
                         s_level_m, s_temperature_c, s_battery_v);
            } else {
                ESP_LOGI(TAG, "joined; reporting level=%.3f m temp=%.1f C batt=%.2f V rate=%.1f cm/h",
                         s_level_m, s_temperature_c, s_battery_v, s_rate_cm_per_hour);
            }
            send_reports();
        } else {
            ESP_LOGE(TAG, "steering failed (status=%d)", params->status);
            xEventGroupSetBits(s_events, FAIL_BIT);
            esp_zigbee_deinit();
        }
        return true;
    }

    default:
        return false;
    }
}

/* Create an Analog Input cluster initialised to initial_value.
 * Used for both the water level and battery voltage endpoints. */
static ezb_zcl_cluster_desc_t make_ai_cluster(float initial_value)
{
    ezb_zcl_analog_input_cluster_server_config_t cfg = {
        .out_of_service = 0,
        .present_value  = initial_value,
        .status_flags   = 0,
    };
    return ezb_zcl_analog_input_create_cluster_desc(&cfg, EZB_ZCL_CLUSTER_SERVER);
}

/* FreeRTOS task that owns the Zigbee radio for one wakeup cycle:
 *   1. Init the stack as an End Device
 *   2. Register clusters and endpoints
 *   3. Call esp_zigbee_launch_mainloop() — blocks until esp_zigbee_deinit()
 *   4. Set STOPPED_BIT so zigbee_send() knows the radio is released */
static void zb_task(void *pvParameters)
{
    /* Combined init: platform config + device config in one call */
    esp_zigbee_config_t zb_cfg = {
        .device_config = {
            .device_type         = EZB_NWK_DEVICE_TYPE_END_DEVICE,
            .install_code_policy = false,
            .zed_config = {
                /* ed_timeout: how long the coordinator keeps this device in its child
                   table between polls — 256 min >> sleep interval, so the parent
                   never ages us out between wakeups. */
                .ed_timeout = EZB_NWK_ED_TIMEOUT_256MIN,
                /* keep_alive: poll interval in ms while awake (unused in deep-sleep
                   architecture but required by the stack). */
                .keep_alive = 3000,
            },
        },
        .platform_config = {
            .radio_config = { .radio_mode = ESP_ZIGBEE_RADIO_MODE_NATIVE },
        },
    };
    ESP_ERROR_CHECK(esp_zigbee_init(&zb_cfg));

    /* Register OTA and ZCL action callback before starting the stack */
    ezb_zcl_core_action_handler_register(zb_action_handler);
    /* Register app signal handler */
    ezb_app_signal_add_handler(zb_signal_handler);

    /* Build ZCL sw_build_id string from the app version baked in at compile time.
     * ZCL Basic cluster SW Build ID max is 16 chars; buffer is sized accordingly.
     * esp_app_desc_t.version is 32 bytes — longer strings are truncated to 16. */
    _Static_assert(sizeof(s_sw_build_id) >= 17,
                   "s_sw_build_id must hold ZCL length byte + 16 chars");
    {
        const char *ver = esp_app_get_description()->version;
        size_t vlen = strlen(ver);
        size_t packed = welld_pack_zcl_string(s_sw_build_id, sizeof(s_sw_build_id), ver);
        if (packed < vlen + 1)
            ESP_LOGW(TAG, "sw_build_id truncated: '%s' → %u chars", ver,
                     (unsigned)(packed - 1));
    }

    /* Basic cluster — device identity visible in Zigbee2MQTT and HA */
    ezb_zcl_basic_cluster_server_config_t basic_cfg = {
        .zcl_version  = EZB_ZCL_BASIC_ZCL_VERSION_DEFAULT_VALUE,
        .power_source = 0x03,  /* battery */
    };
    ezb_zcl_cluster_desc_t basic_desc = ezb_zcl_basic_create_cluster_desc(&basic_cfg,
                                                                           EZB_ZCL_CLUSTER_SERVER);
    ezb_zcl_basic_cluster_desc_add_attr(basic_desc,
        EZB_ZCL_ATTR_BASIC_MANUFACTURER_NAME_ID, s_manufacturer);
    ezb_zcl_basic_cluster_desc_add_attr(basic_desc,
        EZB_ZCL_ATTR_BASIC_MODEL_IDENTIFIER_ID,  s_model);
    ezb_zcl_basic_cluster_desc_add_attr(basic_desc,
        EZB_ZCL_ATTR_BASIC_SW_BUILD_ID_ID,       s_sw_build_id);

    /* Build the device descriptor and add all endpoints to it */
    ezb_af_device_desc_t dev_desc = ezb_af_create_device_desc();

    ezb_af_ep_config_t ep_cfg = {
        .app_profile_id     = EZB_AF_HA_PROFILE_ID,
        .app_device_id      = EZB_ZHA_SIMPLE_SENSOR_DEVICE_ID,
        .app_device_version = 0,
    };

    /* Endpoint 1 — water level (Analog Input).
     * Also hosts the Basic cluster (required on EP1) and the OTA client. */
    ep_cfg.ep_id = EP_LEVEL;
    ezb_af_ep_desc_t level_ep = ezb_af_create_endpoint_desc(&ep_cfg);
    ezb_af_endpoint_add_cluster_desc(level_ep, basic_desc);
    ezb_af_endpoint_add_cluster_desc(level_ep, make_ai_cluster(s_level_m));

    /* OTA upgrade client on endpoint 1.
     * upgrade_server_id = 0xFFFFFFFFFFFFFFFF: discover the OTA server by broadcast
     *   rather than hardcoding a coordinator address.
     * manufacturer_id / image_type_id: must match every .zigbee file built for
     *   this device — see comment on OTA_MANUFACTURER_CODE above. */
    ezb_zcl_ota_upgrade_cluster_client_config_t ota_cfg = {
        .upgrade_server_id    = 0xFFFFFFFFFFFFFFFFULL,
        .file_offset          = EZB_ZCL_OTA_UPGRADE_FILE_OFFSET_DEFAULT_VALUE,
        .image_upgrade_status = EZB_ZCL_OTA_UPGRADE_IMAGE_UPGRADE_STATUS_DEFAULT_VALUE,
        .manufacturer_id      = OTA_MANUFACTURER_CODE,
        .image_type_id        = OTA_IMAGE_TYPE,
    };
    ezb_zcl_cluster_desc_t ota_desc = ezb_zcl_ota_upgrade_create_cluster_desc(&ota_cfg,
                                                                               EZB_ZCL_CLUSTER_CLIENT);
    /* Advertise the running firmware version so the coordinator can gate upgrades.
     * Without this the attribute defaults to 0xFFFFFFFF (unknown), defeating
     * downgrade protection and causing spurious re-upgrade offers. */
    static const uint32_t s_ota_current_ver   = OTA_FW_VERSION;
    static const uint32_t s_ota_downloaded_ver = EZB_ZCL_OTA_UPGRADE_DOWNLOADED_FILE_VERSION_DEFAULT_VALUE;
    ezb_zcl_ota_upgrade_cluster_desc_add_attr(ota_desc,
        EZB_ZCL_ATTR_OTA_UPGRADE_CURRENT_FILE_VERSION_ID, &s_ota_current_ver);
    ezb_zcl_ota_upgrade_cluster_desc_add_attr(ota_desc,
        EZB_ZCL_ATTR_OTA_UPGRADE_DOWNLOADED_FILE_VERSION_ID, &s_ota_downloaded_ver);
    ezb_zcl_ota_upgrade_set_download_block_size(EP_LEVEL, 128);
    ezb_zcl_ota_upgrade_set_hw_version(EP_LEVEL, 0x0001);
    ezb_af_endpoint_add_cluster_desc(level_ep, ota_desc);
    ezb_af_device_add_endpoint_desc(dev_desc, level_ep);

#if CONFIG_WELLD_BATT_ADC_CHANNEL >= 0
    /* Endpoint 2 — battery voltage (Analog Input).
     * The Z2M converter converts this to a percentage using configurable
     * full/empty voltage thresholds, avoiding hard-coding chemistry in fw. */
    ep_cfg.ep_id = EP_BATTERY;
    ezb_af_ep_desc_t batt_ep = ezb_af_create_endpoint_desc(&ep_cfg);
    ezb_af_endpoint_add_cluster_desc(batt_ep, make_ai_cluster(s_battery_v));
    ezb_af_device_add_endpoint_desc(dev_desc, batt_ep);
#endif

    /* Endpoint 3 — water temperature (Temperature Measurement, cluster 0x0402).
     * welld_zb_encode_temp returns 0x8000 (ZCL invalid) when no sensor present. */
    int16_t temp_zb = welld_zb_encode_temp(s_temperature_c);
    ezb_zcl_temperature_measurement_cluster_server_config_t temp_cfg = {
        .measured_value = temp_zb,
        .min_measured_value = -4000,   /* -40.00 °C */
        .max_measured_value =  12500,  /* 125.00 °C */
    };
    ep_cfg.ep_id = EP_TEMPERATURE;
    ezb_af_ep_desc_t temp_ep = ezb_af_create_endpoint_desc(&ep_cfg);
    ezb_af_endpoint_add_cluster_desc(temp_ep,
        ezb_zcl_temperature_measurement_create_cluster_desc(&temp_cfg, EZB_ZCL_CLUSTER_SERVER));
    ezb_af_device_add_endpoint_desc(dev_desc, temp_ep);

    /* Endpoint 4 — level rate of change in cm/h (Analog Input).
     * Always registered so the device descriptor is stable across wakeups;
     * reports are conditionally suppressed in send_reports() when there is
     * no previous reading to compare against (first valid wakeup). */
    float initial_rate = isnan(s_rate_cm_per_hour) ? 0.0f : s_rate_cm_per_hour;
    ep_cfg.ep_id = EP_RATE;
    ezb_af_ep_desc_t rate_ep = ezb_af_create_endpoint_desc(&ep_cfg);
    ezb_af_endpoint_add_cluster_desc(rate_ep, make_ai_cluster(initial_rate));
    ezb_af_device_add_endpoint_desc(dev_desc, rate_ep);

    /* Endpoint 5 — Zigbee failure counter (Analog Input).
       Always registered so the descriptor is stable across wakeups. */
    float initial_fails = (float)s_zb_fails;
    ep_cfg.ep_id = EP_FAILS;
    ezb_af_ep_desc_t fails_ep = ezb_af_create_endpoint_desc(&ep_cfg);
    ezb_af_endpoint_add_cluster_desc(fails_ep, make_ai_cluster(initial_fails));
    ezb_af_device_add_endpoint_desc(dev_desc, fails_ep);

    /* Endpoint 6 — Link Quality (LQI) (Analog Input). */
    ep_cfg.ep_id = EP_LQI;
    ezb_af_ep_desc_t lqi_ep = ezb_af_create_endpoint_desc(&ep_cfg);
    ezb_af_endpoint_add_cluster_desc(lqi_ep, make_ai_cluster(0.0f));
    ezb_af_device_add_endpoint_desc(dev_desc, lqi_ep);

    /* Endpoint 7 — Solar charging state (Analog Input). */
    float initial_solar = s_solar_charging ? 1.0f : 0.0f;
    ep_cfg.ep_id = EP_SOLAR;
    ezb_af_ep_desc_t solar_ep = ezb_af_create_endpoint_desc(&ep_cfg);
    ezb_af_endpoint_add_cluster_desc(solar_ep, make_ai_cluster(initial_solar));
    ezb_af_device_add_endpoint_desc(dev_desc, solar_ep);

    ESP_ERROR_CHECK(ezb_af_device_desc_register(dev_desc));

    ezb_bdb_set_primary_channel_set(CONFIG_WELLD_ZIGBEE_CHANNEL_MASK);
    ESP_ERROR_CHECK(esp_zigbee_start(false));

    /* Arm the watchdog timer before entering the blocking mainloop */
    xTimerStart(s_timeout_timer, 0);

    /* Blocking — returns when esp_zigbee_deinit() is called */
    esp_zigbee_launch_mainloop();

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
                 float rate_cm_per_hour,
                 uint32_t zb_fails,
                 bool solar_charging,
                 uint8_t store_count,
                 const float *store_level_m,
                 const float *store_battery_v,
                 const float *store_temp_c)
{
    s_ota_begin_failed  = false;
    s_level_m           = level_m;
    s_battery_v         = battery_v;
    s_temperature_c     = temperature_c;
    s_rate_cm_per_hour  = rate_cm_per_hour;
    s_zb_fails          = zb_fails;
    s_solar_charging    = solar_charging;
    s_store_count       = store_count;
    s_store_level_m     = store_level_m;
    s_store_battery_v   = store_battery_v;
    s_store_temp_c      = store_temp_c;
    portMEMORY_BARRIER();  /* prevent compiler from moving writes past xTaskCreate */
    s_events            = xEventGroupCreate();

    /* Create the one-shot timers. pdFALSE = one-shot (auto-reload off). */
    s_timeout_timer = xTimerCreate("zb_timeout", pdMS_TO_TICKS(TOTAL_TIMEOUT_MS),
                                   pdFALSE, NULL, timeout_timer_cb);
    s_finish_timer  = xTimerCreate("zb_finish",  pdMS_TO_TICKS(SEND_DELAY_MS),
                                   pdFALSE, NULL, finish_timer_cb);

    if (!s_timeout_timer || !s_finish_timer) {
        ESP_LOGE(TAG, "failed to create Zigbee timers");
        if (s_timeout_timer) xTimerDelete(s_timeout_timer, 0);
        if (s_finish_timer)  xTimerDelete(s_finish_timer, 0);
        vEventGroupDelete(s_events);
        return false;
    }

    if (xTaskCreate(zb_task, "zb_task", 10240, NULL, 5, NULL) != pdPASS) {
        ESP_LOGE(TAG, "failed to create Zigbee task");
        xTimerDelete(s_timeout_timer, 0);
        xTimerDelete(s_finish_timer, 0);
        vEventGroupDelete(s_events);
        return false;
    }

    /* Wait for SENT/FAIL. During an OTA download neither bit is set for
     * potentially many minutes (do_stop_sent returns early while
     * s_ota_in_progress), so keep re-waiting while OTA is running instead of
     * falling through on timeout: returning here would delete the event group
     * and timers still used by zb_task (use-after-free) and let the caller
     * enter deep sleep with the radio mid-transfer. The wait is still
     * bounded — the stall watchdog in do_timeout_check aborts a hung OTA
     * with FAIL_BIT after CONFIG_WELLD_OTA_STALL_TIMEOUT_SEC, and a
     * successful OTA ends in esp_restart(). */
    EventBits_t bits;
    do {
        bits = xEventGroupWaitBits(s_events, SENT_BIT | FAIL_BIT,
                                   pdFALSE, pdFALSE,
                                   pdMS_TO_TICKS(TOTAL_TIMEOUT_MS + 5000));
    } while ((bits & (SENT_BIT | FAIL_BIT)) == 0 && s_ota_in_progress);
    /* Wait for the radio to be released before entering deep sleep */
    xEventGroupWaitBits(s_events, STOPPED_BIT, pdFALSE, pdFALSE, pdMS_TO_TICKS(5000));

    xTimerDelete(s_timeout_timer, 0);
    xTimerDelete(s_finish_timer, 0);
    s_timeout_timer = NULL;
    s_finish_timer  = NULL;

    vEventGroupDelete(s_events);
    return (bits & SENT_BIT) != 0;
}
