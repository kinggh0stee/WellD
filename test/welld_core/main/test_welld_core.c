#include "unity.h"
#include "welld_core.h"
#include <string.h>

#define THRESHOLD 5

/* welld_should_wipe_nvs ----------------------------------------------------- */

static void test_wipe_at_threshold(void)
{
    TEST_ASSERT_TRUE(welld_should_wipe_nvs(THRESHOLD, THRESHOLD));
}

static void test_wipe_above_threshold(void)
{
    TEST_ASSERT_TRUE(welld_should_wipe_nvs(THRESHOLD + 10, THRESHOLD));
}

static void test_no_wipe_below_threshold(void)
{
    TEST_ASSERT_FALSE(welld_should_wipe_nvs(THRESHOLD - 1, THRESHOLD));
    TEST_ASSERT_FALSE(welld_should_wipe_nvs(0, THRESHOLD));
}

/* welld_post_send_action --------------------------------------------------- */

static void test_post_send_success_already_zero(void)
{
    TEST_ASSERT_EQUAL_INT(WELLD_FAIL_NONE, welld_post_send_action(0, true));
}

static void test_post_send_success_after_failures(void)
{
    TEST_ASSERT_EQUAL_INT(WELLD_FAIL_RESET, welld_post_send_action(3, true));
}

static void test_post_send_failure_increments(void)
{
    TEST_ASSERT_EQUAL_INT(WELLD_FAIL_INCREMENT, welld_post_send_action(0, false));
    TEST_ASSERT_EQUAL_INT(WELLD_FAIL_INCREMENT, welld_post_send_action(4, false));
}

/* welld_zb_encode_temp ----------------------------------------------------- */

static void test_encode_temp_positive(void)
{
    TEST_ASSERT_EQUAL_INT16(2345, welld_zb_encode_temp(23.45f));
}

static void test_encode_temp_negative(void)
{
    TEST_ASSERT_EQUAL_INT16(-1050, welld_zb_encode_temp(-10.5f));
}

static void test_encode_temp_zero(void)
{
    TEST_ASSERT_EQUAL_INT16(0, welld_zb_encode_temp(0.0f));
}

static void test_encode_temp_invalid_sentinel(void)
{
    TEST_ASSERT_EQUAL_HEX16(0x8000, (uint16_t)welld_zb_encode_temp(-127.0f));
}

/* welld_zb_should_report_battery ------------------------------------------ */

static void test_battery_reportable(void)
{
    TEST_ASSERT_TRUE(welld_zb_should_report_battery(0.0f));
    TEST_ASSERT_TRUE(welld_zb_should_report_battery(3.7f));
}

static void test_battery_not_reportable(void)
{
    TEST_ASSERT_FALSE(welld_zb_should_report_battery(-1.0f));
    TEST_ASSERT_FALSE(welld_zb_should_report_battery(-0.001f));
}

/* welld_pack_zcl_string ---------------------------------------------------- */

static void test_pack_zcl_string_short(void)
{
    char buf[18] = {0};
    size_t n = welld_pack_zcl_string(buf, sizeof(buf), "1.2.3");
    TEST_ASSERT_EQUAL_size_t(6, n);
    TEST_ASSERT_EQUAL_INT(5, (int)(unsigned char)buf[0]);
    TEST_ASSERT_EQUAL_MEMORY("1.2.3", buf + 1, 5);
}

static void test_pack_zcl_string_truncates_to_buffer(void)
{
    /* 18-byte buffer matches s_sw_build_id in zigbee.c → max 17 payload bytes */
    char buf[18] = {0};
    const char *src = "this-is-a-very-long-version-string-that-exceeds-buffer";
    size_t n = welld_pack_zcl_string(buf, sizeof(buf), src);
    TEST_ASSERT_EQUAL_size_t(18, n);
    TEST_ASSERT_EQUAL_INT(17, (int)(unsigned char)buf[0]);
    TEST_ASSERT_EQUAL_MEMORY(src, buf + 1, 17);
}

static void test_pack_zcl_string_empty(void)
{
    char buf[4] = {0xff, 0xff, 0xff, 0xff};
    size_t n = welld_pack_zcl_string(buf, sizeof(buf), "");
    TEST_ASSERT_EQUAL_size_t(1, n);
    TEST_ASSERT_EQUAL_INT(0, (int)(unsigned char)buf[0]);
}

static void test_pack_zcl_string_zero_buffer(void)
{
    char dummy = 0x55;
    TEST_ASSERT_EQUAL_size_t(0, welld_pack_zcl_string(&dummy, 0, "x"));
    TEST_ASSERT_EQUAL_INT(0x55, (int)(unsigned char)dummy);  /* untouched */
}

/* welld_rate_cm_per_hour --------------------------------------------------- */

static void test_rate_zero_change(void)
{
    TEST_ASSERT_EQUAL_FLOAT(0.0f, welld_rate_cm_per_hour(2.0f, 2.0f, 3600));
}

static void test_rate_rising(void)
{
    TEST_ASSERT_FLOAT_WITHIN(0.01f, 50.0f,
        welld_rate_cm_per_hour(2.0f, 2.5f, 3600));
}

static void test_rate_falling(void)
{
    TEST_ASSERT_FLOAT_WITHIN(0.01f, -50.0f,
        welld_rate_cm_per_hour(3.0f, 2.75f, 1800));
}

static void test_rate_open_loop_returns_zero(void)
{
    TEST_ASSERT_EQUAL_FLOAT(0.0f, welld_rate_cm_per_hour(-1.0f, 2.0f, 3600));
    TEST_ASSERT_EQUAL_FLOAT(0.0f, welld_rate_cm_per_hour(2.0f, -1.0f, 3600));
}

static void test_rate_zero_elapsed_returns_zero(void)
{
    TEST_ASSERT_EQUAL_FLOAT(0.0f, welld_rate_cm_per_hour(2.0f, 2.5f, 0));
}

/* welld_adaptive_sleep_sec ------------------------------------------------- */

static void test_adaptive_sleep_stable_stretches(void)
{
    TEST_ASSERT_EQUAL_UINT32(900, welld_adaptive_sleep_sec(0.5f, 300, 60, 1800));
}

static void test_adaptive_sleep_slow_drift(void)
{
    TEST_ASSERT_EQUAL_UINT32(600, welld_adaptive_sleep_sec(3.0f, 300, 60, 1800));
}

static void test_adaptive_sleep_normal(void)
{
    TEST_ASSERT_EQUAL_UINT32(300, welld_adaptive_sleep_sec(10.0f, 300, 60, 1800));
}

static void test_adaptive_sleep_rapid(void)
{
    TEST_ASSERT_EQUAL_UINT32(150, welld_adaptive_sleep_sec(30.0f, 300, 60, 1800));
}

static void test_adaptive_sleep_very_rapid(void)
{
    TEST_ASSERT_EQUAL_UINT32(75, welld_adaptive_sleep_sec(100.0f, 300, 60, 1800));
}

static void test_adaptive_sleep_sign_independent(void)
{
    TEST_ASSERT_EQUAL_UINT32(
        welld_adaptive_sleep_sec( 30.0f, 300, 60, 1800),
        welld_adaptive_sleep_sec(-30.0f, 300, 60, 1800));
}

static void test_adaptive_sleep_clamps_to_max(void)
{
    TEST_ASSERT_EQUAL_UINT32(1800, welld_adaptive_sleep_sec(0.0f, 900, 60, 1800));
}

static void test_adaptive_sleep_clamps_to_min(void)
{
    TEST_ASSERT_EQUAL_UINT32(60, welld_adaptive_sleep_sec(100.0f, 60, 60, 1800));
}

void app_main(void)
{
    UNITY_BEGIN();
    RUN_TEST(test_wipe_at_threshold);
    RUN_TEST(test_wipe_above_threshold);
    RUN_TEST(test_no_wipe_below_threshold);
    RUN_TEST(test_post_send_success_already_zero);
    RUN_TEST(test_post_send_success_after_failures);
    RUN_TEST(test_post_send_failure_increments);
    RUN_TEST(test_encode_temp_positive);
    RUN_TEST(test_encode_temp_negative);
    RUN_TEST(test_encode_temp_zero);
    RUN_TEST(test_encode_temp_invalid_sentinel);
    RUN_TEST(test_battery_reportable);
    RUN_TEST(test_battery_not_reportable);
    RUN_TEST(test_pack_zcl_string_short);
    RUN_TEST(test_pack_zcl_string_truncates_to_buffer);
    RUN_TEST(test_pack_zcl_string_empty);
    RUN_TEST(test_pack_zcl_string_zero_buffer);
    RUN_TEST(test_rate_zero_change);
    RUN_TEST(test_rate_rising);
    RUN_TEST(test_rate_falling);
    RUN_TEST(test_rate_open_loop_returns_zero);
    RUN_TEST(test_rate_zero_elapsed_returns_zero);
    RUN_TEST(test_adaptive_sleep_stable_stretches);
    RUN_TEST(test_adaptive_sleep_slow_drift);
    RUN_TEST(test_adaptive_sleep_normal);
    RUN_TEST(test_adaptive_sleep_rapid);
    RUN_TEST(test_adaptive_sleep_very_rapid);
    RUN_TEST(test_adaptive_sleep_sign_independent);
    RUN_TEST(test_adaptive_sleep_clamps_to_max);
    RUN_TEST(test_adaptive_sleep_clamps_to_min);
    UNITY_END();
}
