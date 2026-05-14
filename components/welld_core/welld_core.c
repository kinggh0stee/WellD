#include "welld_core.h"
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
    return (int16_t)(temp_c * 100.0f);
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
