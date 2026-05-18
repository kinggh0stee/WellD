#include "welld_core.h"
#include <math.h>
#include <string.h>

bool welld_should_wipe_nvs(uint32_t current_count, uint32_t threshold)
{
    return current_count >= threshold;
}

welld_fail_action_t welld_post_send_action(uint32_t effective_count, bool sent)
{
    if (!sent) return WELLD_FAIL_INCREMENT;
    return effective_count == 0 ? WELLD_FAIL_NONE : WELLD_FAIL_RESET;
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
