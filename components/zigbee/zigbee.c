#include "zigbee.h"
#include "welld_core.h"
#include "welld_nvs.h"
#include "esp_zigbee.h"
#include "ezbee/bdb.h"
#include "ezbee/zcl/zcl_core.h"
#include "ezbee/zcl/cluster/basic_desc.h"
#include "ezbee/zcl/cluster/analog_input_desc.h"
#include "ezbee/zcl/cluster/temperature_measurement_desc.h"
#include "ezbee/zcl/cluster/ota_upgrade_desc.h"
#include "ezbee/zcl/cluster/ota_upgrade.h"
#include "ezbee/zcl/zcl_general_cmd.h"
#include "ezbee/nwk.h"
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
#define OTA_HW_VERSION         0x0001   /* advertised in Query Next Image */

/* Event bits used to synchronise zb_task with zigbee_send() on the main task.
 * A FAIL_BIT raised after the report was already delivered (SENT_BIT or
 * s_sent_before_ota) is OTA-origin and does not fail the send — the outcome
 * is resolved by welld_send_result().
 *
 * There is deliberately no "stack stopped" bit: esp-zigbee-lib 2.x's
 * esp_zigbee_launch_mainloop() only returns if select() fails, so the stack
 * cannot be torn down from inside its own callbacks (esp_zigbee_deinit()
 * there frees the task queue, lock and radio workflow the loop is still
 * using, and the loop then spins on an empty workflow list instead of
 * returning). zigbee_send() parks the stack under its lock instead and the
 * caller deep-sleeps — the same end state as the SDK's deep-sleep end-device
 * example, which enters deep sleep from inside the running stack. */
#define SENT_BIT    BIT0   /* reports were queued and the finish window elapsed */
#define FAIL_BIT    BIT1   /* coordinator not found, steering failed, or OTA error */

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
/* Set when the finish window elapsed while an OTA download owned the radio:
   the report was delivered but SENT_BIT stays clear so zigbee_send() keeps
   waiting for the transfer. A later OTA-origin FAIL_BIT must not turn that
   delivered report into a send failure (see welld_send_result). */
static volatile bool   s_sent_before_ota  = false;
static volatile bool   s_ota_aborted      = false;  /* see zigbee_ota_aborted() */
static int64_t         s_ota_last_block_us = 0; /* time of the last OTA progress */
static esp_ota_handle_t s_ota_handle     = 0;
static const esp_partition_t *s_ota_partition = NULL;
static welld_ota_parser_t s_ota_parser;     /* strips the .zigbee header/elements */
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
   we reschedule rather than ending the cycle — a Zigbee OTA of a ~650 KB
   image takes many minutes. The stall check measures time since the last
   OTA progress (CONFIG_WELLD_OTA_STALL_TIMEOUT_SEC), not since the start, so
   a slow-but-moving transfer is never cut off while a hung one is.
   Once OTA finishes (reboot) or fails (clears s_ota_in_progress), the next
   fire raises FAIL_BIT to wake zigbee_send(). */
static void timeout_timer_cb(TimerHandle_t xTimer)
{
    esp_zigbee_task_queue_post(do_timeout_check, NULL);
}

/* Abort an OTA download in progress and release zigbee_send(). */
static void ota_fail(const char *why)
{
    ESP_LOGE(TAG, "OTA failed: %s — aborting", why);
    s_ota_aborted = true;
    if (s_ota_in_progress) {
        esp_ota_abort(s_ota_handle);
        s_ota_in_progress = false;
    }
    xEventGroupSetBits(s_events, FAIL_BIT);
}

/* Executed inside the Zigbee task context (via task_queue_post). */
static void do_timeout_check(void *ctx)
{
    if (s_ota_in_progress) {
        int64_t idle_s = (esp_timer_get_time() - s_ota_last_block_us) / 1000000LL;
        if (idle_s >= CONFIG_WELLD_OTA_STALL_TIMEOUT_SEC) {
            ESP_LOGE(TAG, "OTA stalled: no block for %lld s", (long long)idle_s);
            ota_fail("stall timeout");
            return;
        }
        /* Reschedule for another TOTAL_TIMEOUT_MS */
        xTimerReset(s_timeout_timer, 0);
        return;
    }
    ESP_LOGE(TAG, "timeout — no coordinator found");
    xEventGroupSetBits(s_events, FAIL_BIT);
}

/* Fired SEND_DELAY_MS after reports are queued, giving the stack time to
   transmit and receive an ACK from the coordinator. If OTA started within
   that window (coordinator responded with an image) we return early to keep
   the cycle alive; do_timeout_check (or an OTA failure path) ends it later. */
static void finish_timer_cb(TimerHandle_t xTimer)
{
    esp_zigbee_task_queue_post(do_stop_sent, NULL);
}

static void do_stop_sent(void *ctx)
{
    if (s_ota_in_progress) {
        /* The report frames had the full finish window before the OTA
           download took over the radio. Record the delivery separately:
           SENT_BIT must stay clear so zigbee_send() keeps waiting for the
           transfer to finish, but if that transfer later fails (FAIL_BIT)
           the already-delivered report must not count as a send failure. */
        s_sent_before_ota = true;
        return;
    }
    if (s_ota_begin_failed) {
        /* esp_ota_begin failed, but only after the report window elapsed —
           the sensor report itself went out. Report send success; the OTA
           error was already logged in zb_action_handler. */
        ESP_LOGW(TAG, "OTA begin failed; report already delivered — send still succeeds");
    }
    xEventGroupSetBits(s_events, SENT_BIT);
}

/* welld_ota_parser sink: write one run of upgrade-image bytes to flash. */
static bool ota_write_sink(void *ctx, const uint8_t *data, size_t len)
{
    (void)ctx;
    return esp_ota_write(s_ota_handle, data, len) == ESP_OK;
}

/* OTA client progress — called by the Zigbee stack for every stage, per the
 * esp-zigbee-sdk 2.0.1 OTA client contract:
 *
 *   START     → open an esp_ota handle on the inactive slot, reset the parser
 *   RECEIVING → the block is a slice of the raw .zigbee FILE (OTA header and
 *               sub-element headers included); only the Upgrade Image
 *               element's bytes are written to flash (welld_ota_parser)
 *   CHECK     → the whole file arrived and parsed cleanly
 *   APPLY     → esp_ota_end() (image validation) + set the boot partition
 *   FINISH    → reboot into the new image
 *   ABORT     → drop the partial image
 *
 * msg->out.result tells the stack whether to continue (SUCCESS) or abort. */
static void ota_progress(ezb_zcl_ota_upgrade_client_progress_message_t *msg)
{
    msg->out.result = EZB_ZCL_STATUS_SUCCESS;

    switch (msg->in.progress) {
    case EZB_ZCL_OTA_UPGRADE_PROGRESS_START: {
        uint32_t file_size = msg->in.start.image_size;
        s_ota_last_block_us = esp_timer_get_time();
        /* esp_ota_get_next_update_partition selects whichever of ota_0/ota_1
           is not currently running, so we always write to the inactive slot */
        s_ota_partition = esp_ota_get_next_update_partition(NULL);
        if (!s_ota_partition) {
            ESP_LOGE(TAG, "OTA: no update partition found");
            msg->out.result = EZB_ZCL_STATUS_ABORT;
            s_ota_begin_failed = true;
            return;
        }
        /* Erase only what the file needs (it is a few dozen bytes larger
           than the app image) instead of the whole 1.5 MB slot, and let
           esp_ota_begin reject a file that cannot fit. */
        if (esp_ota_begin(s_ota_partition, file_size ? file_size : OTA_SIZE_UNKNOWN,
                          &s_ota_handle) != ESP_OK) {
            ESP_LOGE(TAG, "OTA: esp_ota_begin failed (file %lu bytes)",
                     (unsigned long)file_size);
            msg->out.result = EZB_ZCL_STATUS_ABORT;
            s_ota_begin_failed = true;
            return;
        }
        welld_ota_parser_init(&s_ota_parser, file_size);
        s_ota_in_progress = true;
        ESP_LOGI(TAG, "OTA started → %s (file v0x%08lx, %lu bytes)", s_ota_partition->label,
                 (unsigned long)msg->in.start.file_version, (unsigned long)file_size);
        break;
    }

    case EZB_ZCL_OTA_UPGRADE_PROGRESS_RECEIVING:
        if (!s_ota_in_progress) {
            msg->out.result = EZB_ZCL_STATUS_ABORT;
            break;
        }
        s_ota_last_block_us = esp_timer_get_time();
        if (!welld_ota_parser_feed(&s_ota_parser, msg->in.receiving.block,
                                   msg->in.receiving.block_size, ota_write_sink, NULL)) {
            msg->out.result = EZB_ZCL_STATUS_ABORT;
            ota_fail("malformed .zigbee file or flash write error");
        }
        break;

    case EZB_ZCL_OTA_UPGRADE_PROGRESS_CHECK:
        if (!s_ota_in_progress || !welld_ota_parser_complete(&s_ota_parser)) {
            msg->out.result = EZB_ZCL_STATUS_ABORT;
            ota_fail("incomplete image");
        }
        break;

    case EZB_ZCL_OTA_UPGRADE_PROGRESS_APPLY:
        /* esp_ota_end validates the image (and its signature under Secure
           Boot); esp_ota_set_boot_partition updates otadata so the
           bootloader selects the new image on the next boot. */
        if (!s_ota_in_progress) {
            msg->out.result = EZB_ZCL_STATUS_ABORT;
            break;
        }
        /* esp_ota_end frees the handle whatever its result — clear the flag
           first so ota_fail() cannot esp_ota_abort() a consumed handle. */
        s_ota_in_progress = false;
        esp_err_t end_err = esp_ota_end(s_ota_handle);
        s_ota_handle = 0;
        if (end_err != ESP_OK || esp_ota_set_boot_partition(s_ota_partition) != ESP_OK) {
            msg->out.result = EZB_ZCL_STATUS_ABORT;
            ota_fail("image validation or boot-partition update");
            break;
        }
        /* Keep zigbee_send() waiting until FINISH reboots us; restart the
           stall window for the server's upgrade-time delay. (Should the
           stall check fire anyway, the new image is already the boot
           partition and takes over at the next wakeup.) */
        s_ota_in_progress   = true;
        s_ota_last_block_us = esp_timer_get_time();
        ESP_LOGI(TAG, "OTA image applied (%lu bytes)", (unsigned long)s_ota_parser.image_bytes);
        break;

    case EZB_ZCL_OTA_UPGRADE_PROGRESS_FINISH:
        ESP_LOGI(TAG, "OTA complete — rebooting");
        esp_restart();
        break;

    case EZB_ZCL_OTA_UPGRADE_PROGRESS_ABORT:
        ESP_LOGW(TAG, "OTA aborted by stack");
        if (s_ota_in_progress) ota_fail("aborted by stack");
        break;

    default:
        break;
    }
}

static void zb_action_handler(ezb_zcl_core_action_callback_id_t callback_id, void *message)
{
    switch (callback_id) {
    case EZB_ZCL_CORE_OTA_UPGRADE_CLIENT_PROGRESS_CB_ID:
        ota_progress(message);
        break;
    case EZB_ZCL_CORE_OTA_UPGRADE_QUERY_NEXT_IMAGE_RSP_CB_ID: {
        /* Accept whatever the server offers — the stack has already matched
           manufacturer code / image type and starts the download (PROGRESS_
           START) when the status is SUCCESS. */
        ezb_zcl_ota_upgrade_query_next_image_rsp_message_t *rsp = message;
        if (rsp->in.image.status == EZB_ZCL_OTA_UPGRADE_STATUS_CODE_SUCCESS) {
            ESP_LOGI(TAG, "OTA: server offers v0x%08lx (%lu bytes)",
                     (unsigned long)rsp->in.image.file_version,
                     (unsigned long)rsp->in.image.size);
        }
        rsp->out.result = EZB_ZCL_STATUS_SUCCESS;
        break;
    }
    default:
        break;
    }
}

/* Ask the OTA server (the coordinator, endpoint 1 on Zigbee2MQTT) for a newer
 * image. A sleepy device has to ask: an Image Notify from the server only
 * reaches it if it happens to poll its parent in the few seconds it is awake.
 * Zigbee2MQTT answers "no image" until an update is requested for the device,
 * then serves the file on the device's next query. */
static void send_ota_query(void)
{
    ezb_zcl_ota_upgrade_query_next_image_req_cmd_t query = {
        .cmd_ctrl = {
            .dst_addr        = EZB_ADDRESS_SHORT(0x0000),
            .dst_ep          = 1,
            .src_ep          = EP_LEVEL,
            .dis_default_rsp = true,
        },
        .payload = {
            .fc           = 0x01,   /* hardware version present */
            .manuf_code   = OTA_MANUFACTURER_CODE,
            .image_type   = OTA_IMAGE_TYPE,
            .file_version = OTA_FW_VERSION,
            .hw_version   = OTA_HW_VERSION,
        },
    };
    if (ezb_zcl_ota_upgrade_query_next_image_cmd_req(&query) != EZB_ERR_NONE) {
        ESP_LOGW(TAG, "OTA query not sent");
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
#if CONFIG_WELLD_BATT_REPORT_ENABLED
        /* Same compile-time gate as the EP_BATTERY endpoint registration:
           without it the burst would report on an unregistered endpoint. */
        float burst_batt = welld_zb_battery_present_value(s_store_battery_v[i]);
        ezb_zcl_set_attr_value(EP_BATTERY,
            EZB_ZCL_CLUSTER_ID_ANALOG_INPUT, EZB_ZCL_CLUSTER_SERVER,
            EZB_ZCL_ATTR_ANALOG_INPUT_PRESENT_VALUE_ID,
            EZB_ZCL_STD_MANUF_CODE, &burst_batt, false);
        report.cmd_ctrl.src_ep = EP_BATTERY;
        ezb_zcl_report_attr_cmd_req(&report);
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

#if CONFIG_WELLD_BATT_REPORT_ENABLED
    /* Battery voltage — Analog Input cluster, endpoint 2. Always reported:
       an unknown battery (read failed or implausible) goes out as -1, which
       the converter publishes as null, so the last good voltage does not
       stay on show while the low-battery guard is blind. */
    float batt_pv = welld_zb_battery_present_value(s_battery_v);
    ezb_zcl_set_attr_value(EP_BATTERY,
        EZB_ZCL_CLUSTER_ID_ANALOG_INPUT, EZB_ZCL_CLUSTER_SERVER,
        EZB_ZCL_ATTR_ANALOG_INPUT_PRESENT_VALUE_ID,
        EZB_ZCL_STD_MANUF_CODE, &batt_pv, false);
    report.cmd_ctrl.src_ep = EP_BATTERY;
    ezb_zcl_report_attr_cmd_req(&report);
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
       Device-side reading: walk the stack's neighbor table and take the LQI
       of the parent entry (an end device has exactly one parent; its link is
       the one that matters). Runs in zb_task with the network up. 0 = no
       parent entry found = "unknown" — the Z2M converter skips publishing 0,
       so a failed lookup can never masquerade as a dead link. */
    {
        float lqi_f = 0.0f;
        ezb_nwk_info_iterator_t nbr_it = EZB_NWK_INFO_ITERATOR_INIT;
        ezb_nwk_neighbor_info_t nbr;
        while (ezb_nwk_get_next_neighbor(&nbr_it, &nbr) == EZB_ERR_NONE) {
            if (nbr.relationship == EZB_NWK_RELATIONSHIP_PARENT) {
                lqi_f = (float)nbr.lqi;
                break;
            }
        }
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

    /* Ask the coordinator for a newer firmware image (see send_ota_query). */
    send_ota_query();

    /* Give the stack SEND_DELAY_MS to transmit before we declare success */
    xTimerStart(s_finish_timer, 0);
}

static void log_and_send_reports(const char *how)
{
    if (isnan(s_rate_cm_per_hour)) {
        ESP_LOGI(TAG, "%s; reporting level=%.3f m temp=%.1f C batt=%.2f V rate=n/a",
                 how, s_level_m, s_temperature_c, s_battery_v);
    } else {
        ESP_LOGI(TAG, "%s; reporting level=%.3f m temp=%.1f C batt=%.2f V rate=%.1f cm/h",
                 how, s_level_m, s_temperature_c, s_battery_v, s_rate_cm_per_hour);
    }
    send_reports();
}

/* Application signal handler — called by the Zigbee stack from within the
 * mainloop task context. Drives the BDB commissioning state machine:
 *   SKIP_STARTUP → INITIALIZATION → (already on a network) send reports
 *                                 → (factory-new) NETWORK_STEERING → send reports
 * Every deep-sleep wakeup is a "reboot" for the stack: with network state in
 * zb_storage, BDB initialisation resumes the existing membership (rejoining
 * the parent if needed) and DEVICE_REBOOT reports success — no steering. Only
 * a factory-new device (first boot, or after the GPIO factory reset) steers,
 * which needs permit-join open on the coordinator. This mirrors the SDK's
 * deep_sleep_end_device example; steering a node that is already on a
 * network is the BDB "open the network" procedure, not a join.
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
        if (params->status != EZB_BDB_STATUS_SUCCESS) {
            ESP_LOGE(TAG, "init/rejoin failed (status=%d)", params->status);
            xEventGroupSetBits(s_events, FAIL_BIT);
        } else if (ezb_bdb_is_factory_new()) {
            /* No stored network: scan + join (needs permit-join). */
            ESP_LOGI(TAG, "factory-new — starting network steering");
            ezb_bdb_start_top_level_commissioning(EZB_BDB_MODE_NETWORK_STEERING);
        } else {
            log_and_send_reports("rejoined");
        }
        return true;
    }

    case EZB_BDB_SIGNAL_STEERING: {
        const ezb_bdb_signal_simple_params_t *params = ezb_app_signal_get_params(signal);
        if (params->status == EZB_BDB_STATUS_SUCCESS) {
            log_and_send_reports("joined");
        } else {
            ESP_LOGE(TAG, "steering failed (status=%d)", params->status);
            xEventGroupSetBits(s_events, FAIL_BIT);
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
 *   3. Run esp_zigbee_launch_mainloop() — it does not return in normal
 *      operation; zigbee_send() parks it under the stack lock once the cycle
 *      is resolved and the caller deep-sleeps (see SENT_BIT/FAIL_BIT). */
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
            /* NVS partition for the stack's network datasets (keys, PAN,
               parent, frame counters) — must exist in partitions.csv and be
               initialised by app_main before this task runs: the platform
               layer abort()s if it cannot open it. */
            .storage_partition_name = WELLD_ZB_STORAGE_PARTITION,
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
    ezb_zcl_ota_upgrade_set_hw_version(EP_LEVEL, OTA_HW_VERSION);
    ezb_af_endpoint_add_cluster_desc(level_ep, ota_desc);
    ezb_af_device_add_endpoint_desc(dev_desc, level_ep);

#if CONFIG_WELLD_BATT_REPORT_ENABLED
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

    /* Does not return in normal operation (only on an internal select()
       failure) — zigbee_send() parks the loop under the stack lock. */
    esp_zigbee_launch_mainloop();

    ESP_LOGE(TAG, "Zigbee mainloop exited unexpectedly");
    xEventGroupSetBits(s_events, FAIL_BIT);
    vTaskDelete(NULL);
}

/* Send sensor readings over Zigbee and block until the outcome is known.
 *
 * Lifecycle:
 *   1. Store readings in module-level globals (read by zb_task/send_reports)
 *   2. Spawn zb_task which initialises the stack and rejoins (or, when
 *      factory-new, steers onto) the network
 *   3. Wait for SENT_BIT (success) or FAIL_BIT (timeout / error) — kept
 *      waiting while an OTA download runs
 *   4. Park the stack: stop the timers and take the Zigbee lock, which the
 *      mainloop releases around each select(), so zb_task freezes outside
 *      any stack processing — no frame, dataset (NVS) write or flash
 *      operation in flight. The caller deep-sleeps next, which powers the
 *      radio down. Nothing is freed: the event group, timers and task live
 *      until deep sleep resets the chip (zigbee_send() runs once per boot).
 *
 * Returns true when the report was delivered — either SENT_BIT, or the
 * finish window elapsed before an OTA download took over the radio. An OTA
 * failure after that point does not fail the send (welld_send_result). */
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
    s_sent_before_ota   = false;
    s_ota_aborted       = false;
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

    /* Scale the finish (ACK) window with the store-and-forward backlog: each
       backlog entry adds up to 3 extra report frames (level, battery,
       temperature) on top of the ~7 current-reading frames, so a full
       8-entry burst is ~31 frames and a single SEND_DELAY_MS window sized
       for one reading can elapse before the tail of the burst has gone out.
       Clamped to a hardcoded 4× the configured value (deliberately not a
       Kconfig tunable) so a corrupted store count can never keep the radio
       alive much longer than a normal cycle. */
    uint32_t finish_ms = (uint32_t)SEND_DELAY_MS * (1U + store_count);
    if (finish_ms > (uint32_t)SEND_DELAY_MS * 4U) {
        finish_ms = (uint32_t)SEND_DELAY_MS * 4U;
    }

    /* Create the one-shot timers. pdFALSE = one-shot (auto-reload off). */
    s_timeout_timer = xTimerCreate("zb_timeout", pdMS_TO_TICKS(TOTAL_TIMEOUT_MS),
                                   pdFALSE, NULL, timeout_timer_cb);
    s_finish_timer  = xTimerCreate("zb_finish",  pdMS_TO_TICKS(finish_ms),
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
     * falling through on timeout and deep-sleeping mid-transfer. The wait is
     * still bounded — the stall watchdog in do_timeout_check aborts an OTA
     * that receives no block for CONFIG_WELLD_OTA_STALL_TIMEOUT_SEC, and a
     * successful OTA ends in esp_restart(). */
    EventBits_t bits;
    do {
        bits = xEventGroupWaitBits(s_events, SENT_BIT | FAIL_BIT,
                                   pdFALSE, pdFALSE,
                                   pdMS_TO_TICKS(TOTAL_TIMEOUT_MS + 5000));
    } while ((bits & (SENT_BIT | FAIL_BIT)) == 0 && s_ota_in_progress);

    /* Park the stack (step 4 above). */
    xTimerStop(s_timeout_timer, 0);
    xTimerStop(s_finish_timer, 0);
    if (!esp_zigbee_lock_acquire(pdMS_TO_TICKS(2000))) {
        ESP_LOGW(TAG, "Zigbee lock not acquired — sleeping with the stack running");
    }

    /* Success = report delivered (SENT_BIT, or the finish window elapsed
       before an OTA took over). An OTA-origin FAIL_BIT never fails the send. */
    return welld_send_result((bits & SENT_BIT) != 0,
                             (bits & FAIL_BIT) != 0,
                             s_sent_before_ota);
}

bool zigbee_ota_aborted(void)
{
    return s_ota_aborted;
}
