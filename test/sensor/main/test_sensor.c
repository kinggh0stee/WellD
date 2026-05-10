#include "unity.h"
#include "sensor.h"

/* All cases assume default config: 100 Ω shunt, 6 m max depth.
 * At 100 Ω: I(µA) = V(mV) * 10, so 400 mV = 4 mA, 2000 mV = 20 mA. */

static void test_open_loop_zero(void)
{
    TEST_ASSERT_EQUAL_FLOAT(-1.0f, sensor_level_from_mv(0));
}

static void test_open_loop_below_threshold(void)
{
    /* 349 mV → 3490 µA → below 3500 µA open-loop threshold */
    TEST_ASSERT_EQUAL_FLOAT(-1.0f, sensor_level_from_mv(349));
}

static void test_4ma_zero_m(void)
{
    /* 400 mV = 4 mA → 0 m */
    TEST_ASSERT_FLOAT_WITHIN(0.01f, 0.0f, sensor_level_from_mv(400));
}

static void test_midscale(void)
{
    /* 1200 mV = 12 mA → 50 % of 6 m = 3 m */
    TEST_ASSERT_FLOAT_WITHIN(0.05f, 3.0f, sensor_level_from_mv(1200));
}

static void test_full_scale(void)
{
    /* 2000 mV = 20 mA → 6 m */
    TEST_ASSERT_FLOAT_WITHIN(0.01f, 6.0f, sensor_level_from_mv(2000));
}

static void test_overcurrent_clamped(void)
{
    /* above 20 mA should clamp to max depth, not exceed it */
    TEST_ASSERT_FLOAT_WITHIN(0.01f, 6.0f, sensor_level_from_mv(2500));
}

void app_main(void)
{
    UNITY_BEGIN();
    RUN_TEST(test_open_loop_zero);
    RUN_TEST(test_open_loop_below_threshold);
    RUN_TEST(test_4ma_zero_m);
    RUN_TEST(test_midscale);
    RUN_TEST(test_full_scale);
    RUN_TEST(test_overcurrent_clamped);
    UNITY_END();
}
