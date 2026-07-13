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

/* Resolve the outcome of one zigbee_send() cycle from its synchronisation
 * flags:
 *   sent_bit        — SENT_BIT: reports were queued and the ACK window
 *                     elapsed with no OTA transfer running.
 *   fail_bit        — FAIL_BIT: commissioning/steering failed, no coordinator
 *                     was found, or an OTA transfer failed.
 *   sent_before_ota — the ACK window elapsed but an OTA download had taken
 *                     over the radio, so SENT_BIT was deferred to keep the
 *                     caller waiting for the transfer.
 *
 * The report counts as delivered when either sent flag is set. A FAIL_BIT
 * raised after that can only be OTA-origin (stall abort, flash write or
 * finalise failure) and must NOT count as a send failure — five of those
 * would wipe NVS and force a needless rejoin. fail_bit never changes the
 * outcome: with no sent flag the send failed whether FAIL_BIT was raised or
 * the wait simply timed out. */
bool welld_send_result(bool sent_bit, bool fail_bit, bool sent_before_ota);

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

/* Compute the water-level rate of change in cm/hour.
 * prev_level_m / curr_level_m are in metres; elapsed_sec is the time between
 * the two readings (sum of intervening sleep durations).
 *
 * Returns NAN if either reading is the open-loop sentinel (-1) or elapsed
 * is 0 — NAN lets the caller distinguish "no rate available" from a
 * legitimate zero rate (stable water level). */
float welld_rate_cm_per_hour(float prev_level_m,
                             float curr_level_m,
                             uint32_t elapsed_sec);

/* Map a level rate-of-change to a sleep duration. Stable wells get longer
 * sleeps (saving battery); fast-changing wells get shorter sleeps (catching
 * transients). The result is clamped to [min_sec, max_sec].
 *
 * Five-band schedule (absolute rate, cm/h → sleep target):
 *   < 2   (idle / recovery)      → max_sec
 *   < 5   (slow drawdown)        → 2× default_sec
 *   < 10  (active pumping)       → default_sec
 *   < 20  (heavy pumping)        → ½× default_sec
 *   ≥ 20  (rapid event / fault)  → min_sec */
uint32_t welld_adaptive_sleep_sec(float rate_cm_per_hour,
                                  uint32_t default_sec,
                                  uint32_t min_sec,
                                  uint32_t max_sec);
