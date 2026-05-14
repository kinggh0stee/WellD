#pragma once
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/* Pure helpers extracted from main/sensor/zigbee for unit testing.
 * No ESP-IDF or hardware dependencies — safe to call from a host harness. */

typedef enum {
    WELLD_FAIL_NONE,        /* sent ok, counter already 0 — no NVS write needed */
    WELLD_FAIL_RESET,       /* sent ok, counter was nonzero — clear it */
    WELLD_FAIL_INCREMENT,   /* send failed — bump counter */
} welld_fail_action_t;

/* True when the consecutive-failure counter loaded from NVS at boot has hit
 * the threshold and the caller should wipe NVS to force a fresh Zigbee join. */
bool welld_should_wipe_nvs(uint32_t current_count, uint32_t threshold);

/* Decide what to write to NVS for the failure counter after a Zigbee send.
 * effective_count is the value used during this wakeup (0 if NVS was wiped
 * at boot, otherwise the value loaded from NVS). */
welld_fail_action_t welld_post_send_action(uint32_t effective_count, bool sent);

/* Encode a temperature in °C as ZCL Temperature Measurement value (int16,
 * units of 0.01 °C). Returns 0x8000 — the ZCL "invalid" sentinel — when the
 * input is the sensor's -127 not-found marker. */
int16_t welld_zb_encode_temp(float temp_c);

/* Returns true when the battery reading should be sent to the coordinator.
 * sensor_read_battery_v() returns -1 when monitoring is disabled or the ADC
 * read failed; a negative reading should never be reported. */
bool welld_zb_should_report_battery(float battery_v);

/* Pack a C string into a ZCL character string (1-byte length prefix, no
 * null terminator) into out[0..out_size-1]. Truncates src to fit out_size-1
 * bytes of payload. Returns the number of bytes written (1 + payload len),
 * or 0 if out_size < 1. */
size_t welld_pack_zcl_string(char *out, size_t out_size, const char *src);
