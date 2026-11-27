#include "welld_core.h"
#include <math.h>
#include <string.h>

welld_fail_action_t welld_post_send_action(uint32_t effective_count, bool sent)
{
    if (!sent) return WELLD_FAIL_INCREMENT;
    return effective_count == 0 ? WELLD_FAIL_NONE : WELLD_FAIL_RESET;
}

uint32_t welld_fail_backoff_sleep_sec(uint32_t consecutive_fails,
                                      uint32_t threshold,
                                      uint32_t normal_sec,
                                      uint32_t backoff_sec)
{
    if (threshold == 0 || consecutive_fails < threshold) return normal_sec;
    return backoff_sec > normal_sec ? backoff_sec : normal_sec;
}

bool welld_send_result(bool sent_bit, bool fail_bit, bool sent_before_ota)
{
    if (sent_bit || sent_before_ota) {
        /* Report delivered. Any FAIL_BIT alongside is OTA-origin (the OTA
         * failure is logged separately) — never a send failure. */
        return true;
    }
    /* No sent flag: failure regardless of fail_bit — an explicit FAIL_BIT
     * (init/steering error, timeout watchdog) and a bare wait timeout are
     * equally fatal to the report. */
    (void)fail_bit;
    return false;
}

welld_batt_state_t welld_battery_state(float battery_v, uint32_t empty_mv)
{
    /* Written as !(v >= min) so NaN lands in INVALID too. */
    if (!(battery_v >= (float)WELLD_BATT_PLAUSIBLE_MIN_MV / 1000.0f)) {
        return WELLD_BATT_INVALID;
    }
    return battery_v <= (float)empty_mv / 1000.0f ? WELLD_BATT_LOW : WELLD_BATT_OK;
}

int16_t welld_zb_encode_temp(float temp_c)
{
    if (temp_c <= -127.0f) {
        return (int16_t)0x8000;  /* ZCL invalid sentinel */
    }
    return (int16_t)(temp_c * 100.0f + (temp_c >= 0.0f ? 0.5f : -0.5f));
}

bool welld_zb_should_report_battery(float battery_v)
{
    return battery_v >= 0.0f;
}

size_t welld_pack_zcl_string(char *out, size_t out_size, const char *src)
{
    if (out_size < 1) return 0;
    size_t max_payload = out_size - 1;
    size_t len = src ? strlen(src) : 0;
    if (len > max_payload) len = max_payload;
    if (len > 255) len = 255;  /* ZCL length byte is uint8 */
    out[0] = (char)len;
    if (len > 0) memcpy(out + 1, src, len);
    return 1 + len;
}

float welld_rate_cm_per_hour(float prev_level_m,
                             float curr_level_m,
                             uint32_t elapsed_sec)
{
    /* -1.0f = open-loop transducer sentinel. Either reading invalid → no rate. */
    if (prev_level_m < 0.0f || curr_level_m < 0.0f) return NAN;
    if (elapsed_sec == 0) return NAN;
    float delta_cm = (curr_level_m - prev_level_m) * 100.0f;
    float hours    = (float)elapsed_sec / 3600.0f;
    return delta_cm / hours;
}

/* Adaptive sleep — five-band rate-of-change schedule tuned for well behaviour:
 *
 *  Band                  Typical scenario         Sleep target
 *  abs_rate < 2 cm/h     Idle / recovery          max_sec  (e.g. 30 min)
 *  2–5 cm/h              Slow drawdown            default × 2
 *  5–10 cm/h             Active pumping           default
 *  10–20 cm/h            Heavy pumping            default / 2
 *  ≥ 20 cm/h             Rapid event / failure    min_sec  (e.g. 2 min)
 *
 * The result is always clamped to [min_sec, max_sec] so extreme base values
 * cannot produce unsafe sleep durations. */
uint32_t welld_adaptive_sleep_sec(float rate_cm_per_hour,
                                  uint32_t default_sec,
                                  uint32_t min_sec,
                                  uint32_t max_sec)
{
    float    abs_rate = fabsf(rate_cm_per_hour);
    uint32_t scaled;

    if      (abs_rate < 2.0f)   scaled = max_sec;
    else if (abs_rate < 5.0f)   scaled = default_sec * 2;
    else if (abs_rate < 10.0f)  scaled = default_sec;
    else if (abs_rate < 20.0f)  scaled = default_sec / 2;
    else                        scaled = min_sec;

    if (scaled < min_sec) scaled = min_sec;
    if (scaled > max_sec) scaled = max_sec;
    return scaled;
}

/* ── Zigbee OTA upgrade file parser ─────────────────────────────────────── */

enum {
    OTA_PARSE_HDR_PREFIX,   /* file id (4) + header version (2) + header length (2) */
    OTA_PARSE_HDR_SKIP,     /* rest of the header up to hdr_len (not needed here) */
    OTA_PARSE_ELEM_HDR,     /* element tag (2) + element length (4) */
    OTA_PARSE_ELEM_VAL,     /* element value */
    OTA_PARSE_ERROR,
};

#define OTA_HDR_PREFIX_LEN  8U
#define OTA_ELEM_HDR_LEN    6U

static uint16_t le16(const uint8_t *b)
{
    return (uint16_t)(b[0] | (b[1] << 8));
}

static uint32_t le32(const uint8_t *b)
{
    return (uint32_t)b[0] | ((uint32_t)b[1] << 8) |
           ((uint32_t)b[2] << 16) | ((uint32_t)b[3] << 24);
}

void welld_ota_parser_init(welld_ota_parser_t *p, uint32_t file_size)
{
    memset(p, 0, sizeof(*p));
    p->file_size = file_size;
    p->state = OTA_PARSE_HDR_PREFIX;
}

/* Copy up to `want` bytes of a fixed-size field into p->scratch. Returns the
 * number of bytes taken from data; the field is complete when
 * p->scratch_len == want. */
static size_t ota_take_field(welld_ota_parser_t *p, const uint8_t *data,
                             size_t len, size_t want)
{
    size_t n = want - p->scratch_len;
    if (n > len) n = len;
    memcpy(p->scratch + p->scratch_len, data, n);
    p->scratch_len = (uint8_t)(p->scratch_len + n);
    return n;
}

static bool ota_fail(welld_ota_parser_t *p)
{
    p->state = OTA_PARSE_ERROR;
    return false;
}

bool welld_ota_parser_feed(welld_ota_parser_t *p, const uint8_t *data,
                           size_t len, welld_ota_sink_t sink, void *ctx)
{
    if (p->state == OTA_PARSE_ERROR) return false;
    if (len > 0 && !data) return ota_fail(p);
    if (p->file_size != 0 && len > (size_t)(p->file_size - p->consumed)) {
        return ota_fail(p);   /* more data than the announced file size */
    }

    while (len > 0) {
        size_t n = 0;
        switch (p->state) {
        case OTA_PARSE_HDR_PREFIX:
            n = ota_take_field(p, data, len, OTA_HDR_PREFIX_LEN);
            if (p->scratch_len == OTA_HDR_PREFIX_LEN) {
                p->hdr_len = le16(p->scratch + 6);
                if (le32(p->scratch) != WELLD_OTA_FILE_IDENTIFIER ||
                    p->hdr_len < WELLD_OTA_HEADER_MIN_LEN ||
                    p->hdr_len > WELLD_OTA_HEADER_MAX_LEN ||
                    (p->file_size != 0 && p->hdr_len > p->file_size)) {
                    return ota_fail(p);
                }
                p->scratch_len = 0;
                p->state = OTA_PARSE_HDR_SKIP;
            }
            break;

        case OTA_PARSE_HDR_SKIP: {
            uint32_t left = p->hdr_len - p->consumed;
            n = len < left ? len : left;
            if (n == left) p->state = OTA_PARSE_ELEM_HDR;
            break;
        }

        case OTA_PARSE_ELEM_HDR:
            n = ota_take_field(p, data, len, OTA_ELEM_HDR_LEN);
            if (p->scratch_len == OTA_ELEM_HDR_LEN) {
                p->elem_tag       = le16(p->scratch);
                p->elem_remaining = le32(p->scratch + 2);
                p->scratch_len    = 0;
                if (p->elem_tag == WELLD_OTA_TAG_UPGRADE_IMAGE) {
                    if (p->image_seen || p->elem_remaining == 0) return ota_fail(p);
                    p->image_seen = true;
                }
                if (p->file_size != 0 &&
                    p->elem_remaining > p->file_size - (p->consumed + (uint32_t)n)) {
                    return ota_fail(p);   /* element runs past the end of the file */
                }
                if (p->elem_remaining > 0) p->state = OTA_PARSE_ELEM_VAL;
            }
            break;

        case OTA_PARSE_ELEM_VAL:
            n = len < p->elem_remaining ? len : p->elem_remaining;
            if (p->elem_tag == WELLD_OTA_TAG_UPGRADE_IMAGE) {
                if (!sink || !sink(ctx, data, n)) return ota_fail(p);
                p->image_bytes += (uint32_t)n;
            }
            p->elem_remaining -= (uint32_t)n;
            if (p->elem_remaining == 0) p->state = OTA_PARSE_ELEM_HDR;
            break;

        default:
            return ota_fail(p);
        }
        p->consumed += (uint32_t)n;
        data += n;
        len  -= n;
    }
    return true;
}

bool welld_ota_parser_complete(const welld_ota_parser_t *p)
{
    return p->state == OTA_PARSE_ELEM_HDR && p->scratch_len == 0 &&
           p->image_seen &&
           (p->file_size == 0 || p->consumed == p->file_size);
}
