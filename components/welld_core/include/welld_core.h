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

/* Decide what to write to NVS for the failure counter after a Zigbee send.
 * effective_count is the consecutive-failure count loaded from NVS at boot. */
welld_fail_action_t welld_post_send_action(uint32_t effective_count, bool sent);

/* Sleep duration for the next cycle once this wakeup's send outcome is known.
 * consecutive_fails counts failures INCLUDING this wakeup (0 after a
 * successful send). From `threshold` failures on, the sleep is stretched to
 * `backoff_sec` so a coordinator outage does not cost a full radio-on search
 * every normal interval; an already-longer normal_sec is never shortened.
 * threshold == 0 disables the backoff. */
uint32_t welld_fail_backoff_sleep_sec(uint32_t consecutive_fails,
                                      uint32_t threshold,
                                      uint32_t normal_sec,
                                      uint32_t backoff_sec);

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
 * finalise failure) and must NOT count as a send failure — a run of those
 * would push the device into failure backoff for no reason. fail_bit never
 * changes the outcome: with no sent flag the send failed whether FAIL_BIT
 * was raised or the wait simply timed out. */
bool welld_send_result(bool sent_bit, bool fail_bit, bool sent_before_ota);

/* A battery reading below this cannot come from a running device: the DW01A
 * isolates the cell at 2.4 V and the HT7333-fed rail browns the ESP32-C6 out
 * well above that. Anything lower means the measurement path failed (divider
 * not fitted on a dev board, Q5/R7 open, AIN2 floating near 0 V). */
#define WELLD_BATT_PLAUSIBLE_MIN_MV 2000U

/* ...nor can one above this percentage of the full-charge voltage: with R8
 * open, AIN2 is pulled up to the ADS1115 input clamp and a 1S pack reads
 * ~7 V. */
#define WELLD_BATT_PLAUSIBLE_MAX_PCT_OF_FULL 125U

typedef enum {
    WELLD_BATT_INVALID,  /* read failed (-1), NaN or implausible: report the
                          * battery as unknown and skip the low-battery guard */
    WELLD_BATT_LOW,      /* at/below the empty threshold: skip the send */
    WELLD_BATT_OK,
} welld_batt_state_t;

/* Classify a battery reading in volts against the empty and full-charge
 * thresholds (mV). Without the plausibility window a missing divider reads a
 * few mV of noise — "critically low" — and the device would never report
 * again, while an open R8 would read ~7 V and disable the guard silently.
 * full_mv == 0 disables the upper bound. */
welld_batt_state_t welld_battery_state(float battery_v, uint32_t empty_mv,
                                       uint32_t full_mv);

/* Encode a temperature in °C as ZCL Temperature Measurement value (int16,
 * units of 0.01 °C). Returns 0x8000 — the ZCL "invalid" sentinel — when the
 * input is the sensor's -127 not-found marker. */
int16_t welld_zb_encode_temp(float temp_c);

/* EP2 present value for a battery reading: the reading itself when it is a
 * finite, non-negative voltage, otherwise -1.0 — the "battery unknown"
 * sentinel (read failed or implausible). It is always reported, so the Z2M
 * converter can publish battery_voltage / battery as null instead of leaving
 * the last good value on show while the low-battery guard is blind. */
float welld_zb_battery_present_value(float battery_v);

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

/* ── Zigbee OTA upgrade file parser (ZCL spec 07-5123, §11.4) ─────────────────
 *
 * esp-zigbee-lib 2.x hands the OTA client the raw .zigbee file stream: the
 * OTA header (file identifier 0x0BEEF11E, header length, …, optional fields)
 * followed by sub-elements (2-byte tag, 4-byte length, value). Only the value
 * of the Upgrade Image element (tag 0x0000) is the ESP app image that may be
 * written to the OTA partition — writing the raw stream makes esp_ota_write()
 * reject the first byte (0x1E, not the 0xE9 image magic). This streaming
 * parser accepts arbitrary block boundaries and forwards only upgrade-image
 * bytes to a sink callback. All multi-byte fields are little-endian. */

#define WELLD_OTA_FILE_IDENTIFIER    0x0BEEF11EUL
#define WELLD_OTA_HEADER_MIN_LEN     56U     /* mandatory header fields */
#define WELLD_OTA_HEADER_MAX_LEN     69U     /* + every optional field */
#define WELLD_OTA_TAG_UPGRADE_IMAGE  0x0000U

/* Receives one contiguous run of upgrade-image bytes; return false to abort. */
typedef bool (*welld_ota_sink_t)(void *ctx, const uint8_t *data, size_t len);

typedef struct {
    uint32_t file_size;       /* total file size announced at start, 0 = unknown */
    uint32_t consumed;        /* file bytes consumed so far */
    uint32_t hdr_len;         /* OTA header length field */
    uint32_t elem_remaining;  /* bytes left in the current element's value */
    uint32_t image_bytes;     /* upgrade-image bytes handed to the sink */
    uint16_t elem_tag;        /* tag of the element being consumed */
    uint8_t  scratch[8];      /* fixed-size field assembled across blocks */
    uint8_t  scratch_len;
    uint8_t  state;           /* internal parse state */
    bool     image_seen;      /* an upgrade-image element header was parsed */
} welld_ota_parser_t;

/* Reset the parser for a new download of `file_size` bytes (0 = unknown). */
void welld_ota_parser_init(welld_ota_parser_t *p, uint32_t file_size);

/* Consume one received block. Upgrade-image bytes are passed to sink(ctx, …)
 * in order. Returns false — and stays failed for every later call — on a
 * malformed stream (bad file identifier, impossible header length, duplicate
 * or empty image element, data past the announced file size) or when the
 * sink returns false. */
bool welld_ota_parser_feed(welld_ota_parser_t *p, const uint8_t *data,
                           size_t len, welld_ota_sink_t sink, void *ctx);

/* True once the stream ended cleanly on an element boundary, exactly one
 * upgrade-image element was received in full, and (when the size was
 * announced) the whole file was consumed. */
bool welld_ota_parser_complete(const welld_ota_parser_t *p);
