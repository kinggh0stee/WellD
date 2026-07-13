/* Single source of truth for the welld_core test suite. Compiled both
 * on-device (via ESP-IDF Unity, providing app_main) and on the host
 * (via plain CMake at test/host/, providing main with -DHOST_BUILD). */

#include "unity.h"
#include "welld_core.h"
#include <math.h>
#include <string.h>

#define THRESHOLD 5

#ifdef HOST_BUILD
void setUp(void) {}
void tearDown(void) {}
#endif

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

static void test_post_send_success_at_wipe_threshold(void)
{
    /* A send that succeeds with the counter already at/above the wipe
     * threshold still resets — success always clears the counter. */
    TEST_ASSERT_EQUAL_INT(WELLD_FAIL_RESET, welld_post_send_action(5, true));
    TEST_ASSERT_EQUAL_INT(WELLD_FAIL_RESET, welld_post_send_action(1000, true));
}

static void test_post_send_failure_ignores_count(void)
{
    /* Failure increments no matter how large the counter already is. */
    TEST_ASSERT_EQUAL_INT(WELLD_FAIL_INCREMENT, welld_post_send_action(5, false));
    TEST_ASSERT_EQUAL_INT(WELLD_FAIL_INCREMENT, welld_post_send_action(0xFFFFFFFFu, false));
}

/* welld_send_result --------------------------------------------------------- */
/* Resolves the outcome of a zigbee_send() cycle from SENT_BIT / FAIL_BIT and
 * the "finish window elapsed while an OTA download owned the radio" flag.
 * Contract: success = report delivered (either sent flag), regardless of an
 * OTA-origin FAIL_BIT raised afterwards. */

static void test_send_result_sent_only(void)
{
    TEST_ASSERT_TRUE(welld_send_result(true, false, false));
}

static void test_send_result_sent_with_late_ota_fail(void)
{
    /* SENT_BIT seen, FAIL_BIT raised later (OTA abort) — still a success;
     * 5 OTA-plagued wakeups must not wipe NVS and force a rejoin. */
    TEST_ASSERT_TRUE(welld_send_result(true, true, false));
}

static void test_send_result_sent_before_ota_then_ota_fail(void)
{
    /* Report delivered, then the OTA took over the radio (SENT_BIT deferred)
     * and later failed (stall abort / write / finalise). */
    TEST_ASSERT_TRUE(welld_send_result(false, true, true));
}

static void test_send_result_sent_before_ota_no_fail(void)
{
    TEST_ASSERT_TRUE(welld_send_result(false, false, true));
}

static void test_send_result_fail_only(void)
{
    /* Init/steering failure or coordinator-not-found timeout: the report
     * itself failed — behaviour unchanged, counts as a send failure. */
    TEST_ASSERT_FALSE(welld_send_result(false, true, false));
}

static void test_send_result_timeout_no_bits(void)
{
    /* Bare wait timeout with no bits at all is equally a failure. */
    TEST_ASSERT_FALSE(welld_send_result(false, false, false));
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

static void test_encode_temp_just_above_sentinel(void)
{
    /* -126.99 °C is > -127.0, so it should encode normally, not return 0x8000 */
    TEST_ASSERT_EQUAL_INT16(-12699, welld_zb_encode_temp(-126.99f));
}

static void test_encode_temp_just_below_sentinel(void)
{
    /* -127.01 °C <= -127.0, so it must return the ZCL invalid sentinel */
    TEST_ASSERT_EQUAL_HEX16(0x8000, (uint16_t)welld_zb_encode_temp(-127.01f));
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
    char buf[4] = {(char)0xff, (char)0xff, (char)0xff, (char)0xff};
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

static void test_pack_zcl_string_null_src(void)
{
    /* NULL src is treated like an empty string */
    char buf[4] = {(char)0xff, (char)0xff, (char)0xff, (char)0xff};
    size_t n = welld_pack_zcl_string(buf, sizeof(buf), NULL);
    TEST_ASSERT_EQUAL_size_t(1, n);
    TEST_ASSERT_EQUAL_INT(0, (int)(unsigned char)buf[0]);
}

static void test_pack_zcl_string_over_255_clamped(void)
{
    /* ZCL length byte is uint8 — payloads > 255 must be clamped to 255. */
    char src[300];
    char buf[300];
    memset(src, 'A', 299);
    src[299] = '\0';
    memset(buf, 0, sizeof(buf));
    size_t n = welld_pack_zcl_string(buf, sizeof(buf), src);
    TEST_ASSERT_EQUAL_size_t(256, n);  /* 1 length byte + 255 payload */
    TEST_ASSERT_EQUAL_INT(255, (int)(unsigned char)buf[0]);
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

static void test_rate_open_loop_returns_nan(void)
{
    TEST_ASSERT_TRUE(isnan(welld_rate_cm_per_hour(-1.0f, 2.0f, 3600)));
    TEST_ASSERT_TRUE(isnan(welld_rate_cm_per_hour(2.0f, -1.0f, 3600)));
}

static void test_rate_zero_elapsed_returns_nan(void)
{
    TEST_ASSERT_TRUE(isnan(welld_rate_cm_per_hour(2.0f, 2.5f, 0)));
}

static void test_rate_accumulated_elapsed(void)
{
    /* Simulates 5 invalid wakeups each sleeping 300 s before a valid reading.
     * elapsed = 1500 s, delta = +0.5 m → 50 cm / (1500/3600 h) = 120 cm/h. */
    TEST_ASSERT_FLOAT_WITHIN(0.1f, 120.0f,
        welld_rate_cm_per_hour(2.0f, 2.5f, 1500));
}

static void test_rate_nan_after_history_invalidation(void)
{
    /* Low-battery invalidation contract (main.c): the low-battery path sets
     * s_history.valid = false and zeroes elapsed_since_last_valid_sec. On the
     * first valid reading after recovery main.c skips the rate call entirely,
     * but even a stale last_level_m paired with the zeroed elapsed counter
     * must yield NaN — never a huge false rate spike. */
    TEST_ASSERT_TRUE(isnan(welld_rate_cm_per_hour(2.0f, 4.5f, 0)));
}

static void test_rate_nan_input_propagates(void)
{
    /* Defensive: a NaN level on either side must never produce a finite rate
     * (EP4 is only reported when the rate is finite). */
    TEST_ASSERT_TRUE(isnan(welld_rate_cm_per_hour(NAN, 2.0f, 3600)));
    TEST_ASSERT_TRUE(isnan(welld_rate_cm_per_hour(2.0f, NAN, 3600)));
}

static void test_rate_both_invalid_returns_nan(void)
{
    /* Two consecutive open-loop readings → still no rate. */
    TEST_ASSERT_TRUE(isnan(welld_rate_cm_per_hour(-1.0f, -1.0f, 3600)));
}

static void test_rate_zero_level_is_valid(void)
{
    /* 0.0 m is a legitimate reading (empty well), not a sentinel — rate must
     * be computed, not NaN. 0.0 → 0.5 m over 1 h = +50 cm/h. */
    TEST_ASSERT_FLOAT_WITHIN(0.01f, 50.0f,
        welld_rate_cm_per_hour(0.0f, 0.5f, 3600));
    TEST_ASSERT_FLOAT_WITHIN(0.01f, -50.0f,
        welld_rate_cm_per_hour(0.5f, 0.0f, 3600));
}

/* welld_adaptive_sleep_sec ------------------------------------------------- */
/*
 * Five-band schedule (tuned for well behaviour):
 *   abs_rate < 2  cm/h  → max_sec        (idle / recovery)
 *   abs_rate < 5  cm/h  → default × 2   (slow drawdown)
 *   abs_rate < 10 cm/h  → default        (active pumping)
 *   abs_rate < 20 cm/h  → default / 2   (heavy pumping)
 *   abs_rate ≥ 20 cm/h  → min_sec        (rapid event)
 * Result is always clamped to [min_sec, max_sec].
 */

static void test_adaptive_sleep_stable_stretches(void)
{
    /* 0.5 cm/h: < 2.0 → max_sec = 1800 */
    TEST_ASSERT_EQUAL_UINT32(1800, welld_adaptive_sleep_sec(0.5f, 300, 60, 1800));
}

static void test_adaptive_sleep_slow_drift(void)
{
    /* 3.0 cm/h: < 5.0 → default * 2 = 600 */
    TEST_ASSERT_EQUAL_UINT32(600, welld_adaptive_sleep_sec(3.0f, 300, 60, 1800));
}

static void test_adaptive_sleep_normal(void)
{
    /* 7.0 cm/h: < 10.0 → default = 300 */
    TEST_ASSERT_EQUAL_UINT32(300, welld_adaptive_sleep_sec(7.0f, 300, 60, 1800));
}

static void test_adaptive_sleep_rapid(void)
{
    /* 15.0 cm/h: < 20.0 → default / 2 = 150 */
    TEST_ASSERT_EQUAL_UINT32(150, welld_adaptive_sleep_sec(15.0f, 300, 60, 1800));
}

static void test_adaptive_sleep_very_rapid(void)
{
    /* 100.0 cm/h: ≥ 20.0 → min_sec = 60 */
    TEST_ASSERT_EQUAL_UINT32(60, welld_adaptive_sleep_sec(100.0f, 300, 60, 1800));
}

static void test_adaptive_sleep_sign_independent(void)
{
    /* Falling and rising at the same rate should produce the same sleep */
    TEST_ASSERT_EQUAL_UINT32(
        welld_adaptive_sleep_sec( 15.0f, 300, 60, 1800),
        welld_adaptive_sleep_sec(-15.0f, 300, 60, 1800));
}

static void test_adaptive_sleep_clamps_to_max(void)
{
    /* Idle: < 2.0 → max_sec; also tests that band already returns max_sec */
    TEST_ASSERT_EQUAL_UINT32(1800, welld_adaptive_sleep_sec(0.0f, 900, 60, 1800));
}

static void test_adaptive_sleep_clamps_to_min(void)
{
    /* Very fast rate, tiny default → band returns min_sec, clamp confirms */
    TEST_ASSERT_EQUAL_UINT32(60, welld_adaptive_sleep_sec(100.0f, 60, 60, 1800));
}

static void test_adaptive_sleep_boundary_2(void)
{
    /* Exactly 2.0 cm/h: < 2.0f is false → < 5.0f → default * 2 = 600 */
    TEST_ASSERT_EQUAL_UINT32(600, welld_adaptive_sleep_sec(2.0f, 300, 60, 1800));
}

static void test_adaptive_sleep_boundary_5(void)
{
    /* Exactly 5.0 cm/h: < 5.0f is false → < 10.0f → default = 300 */
    TEST_ASSERT_EQUAL_UINT32(300, welld_adaptive_sleep_sec(5.0f, 300, 60, 1800));
}

static void test_adaptive_sleep_boundary_10(void)
{
    /* Exactly 10.0 cm/h: < 10.0f is false → < 20.0f → default / 2 = 150 */
    TEST_ASSERT_EQUAL_UINT32(150, welld_adaptive_sleep_sec(10.0f, 300, 60, 1800));
}

static void test_adaptive_sleep_boundary_20(void)
{
    /* Exactly 20.0 cm/h: < 20.0f is false → min_sec = 60 */
    TEST_ASSERT_EQUAL_UINT32(60, welld_adaptive_sleep_sec(20.0f, 300, 60, 1800));
}

static void test_adaptive_sleep_fast_band_clamps_to_min(void)
{
    /* Fast band is default / 2: with default = 100 that gives 50, which is
     * below min_sec = 60 → the clamp must lift it back to min_sec. */
    TEST_ASSERT_EQUAL_UINT32(60, welld_adaptive_sleep_sec(15.0f, 100, 60, 1800));
}

static void test_adaptive_sleep_slow_band_clamps_to_max(void)
{
    /* Slow band is default × 2: with default = 1000 that gives 2000, above
     * max_sec = 1800 → the clamp must cap it at max_sec. */
    TEST_ASSERT_EQUAL_UINT32(1800, welld_adaptive_sleep_sec(3.0f, 1000, 60, 1800));
}

static void test_adaptive_sleep_fast_band_exact_half(void)
{
    /* default / 2 lands exactly on min_sec: no clamp needed, value passes. */
    TEST_ASSERT_EQUAL_UINT32(60, welld_adaptive_sleep_sec(15.0f, 120, 60, 1800));
}

static void test_adaptive_sleep_boundary_just_below_2(void)
{
    /* 1.999 cm/h stays in the idle band → max_sec. */
    TEST_ASSERT_EQUAL_UINT32(1800, welld_adaptive_sleep_sec(1.999f, 300, 60, 1800));
}

static void test_adaptive_sleep_boundary_just_below_20(void)
{
    /* 19.999 cm/h stays in the heavy-pumping band → default / 2. */
    TEST_ASSERT_EQUAL_UINT32(150, welld_adaptive_sleep_sec(19.999f, 300, 60, 1800));
}

static int run_tests(void)
{
    UNITY_BEGIN();
    RUN_TEST(test_wipe_at_threshold);
    RUN_TEST(test_wipe_above_threshold);
    RUN_TEST(test_no_wipe_below_threshold);
    RUN_TEST(test_post_send_success_already_zero);
    RUN_TEST(test_post_send_success_after_failures);
    RUN_TEST(test_post_send_failure_increments);
    RUN_TEST(test_post_send_success_at_wipe_threshold);
    RUN_TEST(test_post_send_failure_ignores_count);
    RUN_TEST(test_send_result_sent_only);
    RUN_TEST(test_send_result_sent_with_late_ota_fail);
    RUN_TEST(test_send_result_sent_before_ota_then_ota_fail);
    RUN_TEST(test_send_result_sent_before_ota_no_fail);
    RUN_TEST(test_send_result_fail_only);
    RUN_TEST(test_send_result_timeout_no_bits);
    RUN_TEST(test_encode_temp_positive);
    RUN_TEST(test_encode_temp_negative);
    RUN_TEST(test_encode_temp_zero);
    RUN_TEST(test_encode_temp_invalid_sentinel);
    RUN_TEST(test_encode_temp_just_above_sentinel);
    RUN_TEST(test_encode_temp_just_below_sentinel);
    RUN_TEST(test_battery_reportable);
    RUN_TEST(test_battery_not_reportable);
    RUN_TEST(test_pack_zcl_string_short);
    RUN_TEST(test_pack_zcl_string_truncates_to_buffer);
    RUN_TEST(test_pack_zcl_string_empty);
    RUN_TEST(test_pack_zcl_string_zero_buffer);
    RUN_TEST(test_pack_zcl_string_null_src);
    RUN_TEST(test_pack_zcl_string_over_255_clamped);
    RUN_TEST(test_rate_zero_change);
    RUN_TEST(test_rate_rising);
    RUN_TEST(test_rate_falling);
    RUN_TEST(test_rate_open_loop_returns_nan);
    RUN_TEST(test_rate_zero_elapsed_returns_nan);
    RUN_TEST(test_rate_accumulated_elapsed);
    RUN_TEST(test_rate_nan_after_history_invalidation);
    RUN_TEST(test_rate_nan_input_propagates);
    RUN_TEST(test_rate_both_invalid_returns_nan);
    RUN_TEST(test_rate_zero_level_is_valid);
    RUN_TEST(test_adaptive_sleep_stable_stretches);
    RUN_TEST(test_adaptive_sleep_slow_drift);
    RUN_TEST(test_adaptive_sleep_normal);
    RUN_TEST(test_adaptive_sleep_rapid);
    RUN_TEST(test_adaptive_sleep_very_rapid);
    RUN_TEST(test_adaptive_sleep_sign_independent);
    RUN_TEST(test_adaptive_sleep_clamps_to_max);
    RUN_TEST(test_adaptive_sleep_clamps_to_min);
    RUN_TEST(test_adaptive_sleep_boundary_2);
    RUN_TEST(test_adaptive_sleep_boundary_5);
    RUN_TEST(test_adaptive_sleep_boundary_10);
    RUN_TEST(test_adaptive_sleep_boundary_20);
    RUN_TEST(test_adaptive_sleep_fast_band_clamps_to_min);
    RUN_TEST(test_adaptive_sleep_slow_band_clamps_to_max);
    RUN_TEST(test_adaptive_sleep_fast_band_exact_half);
    RUN_TEST(test_adaptive_sleep_boundary_just_below_2);
    RUN_TEST(test_adaptive_sleep_boundary_just_below_20);
    return UNITY_END();
}

#ifdef HOST_BUILD
int main(void) { return run_tests(); }
#else
void app_main(void) { run_tests(); }
#endif
