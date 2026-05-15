/* Host-side unit tests for the pure subset of components/sensor.
 * Mirrors the pure-function tests in test/sensor/main/test_sensor.c;
 * the NVS offset round-trip tests stay on-device because they need flash.
 *
 * All level cases assume default config: 100 Ω shunt, 6 m max depth.
 * At 100 Ω: I(µA) = V(mV) * 10, so 400 mV = 4 mA, 2000 mV = 20 mA. */

#include "unity.h"
#include "sensor.h"

void setUp(void) {}
void tearDown(void) {}

static void test_open_loop_zero(void)
{
    TEST_ASSERT_EQUAL_FLOAT(-1.0f, sensor_level_from_mv(0));
}

static void test_open_loop_below_threshold(void)
{
    /* 349 mV → 3490 µA → below 3500 µA open-loop threshold */
    TEST_ASSERT_EQUAL_FLOAT(-1.0f, sensor_level_from_mv(349));
}

static void test_open_loop_threshold_boundary(void)
{
    /* 350 mV → 3500 µA → exactly at threshold; code uses < 3500, so this is
     * treated as live (not open-loop). Falls in the 3.5–4 mA dead band: the
     * raw ratio is negative and gets clamped to 0 → 0 m. */
    TEST_ASSERT_FLOAT_WITHIN(0.01f, 0.0f, sensor_level_from_mv(350));
}

static void test_dead_band_negative_ratio_clamped(void)
{
    /* 380 mV → 3.8 mA → ratio = (3800-4000)/16000 = -0.0125 → clamped to 0 */
    TEST_ASSERT_FLOAT_WITHIN(0.01f, 0.0f, sensor_level_from_mv(380));
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

static void test_battery_2x_divider(void)
{
    /* 1500 mV at the ADC * 2.00x = 3.00 V */
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 3.0f, sensor_battery_from_mv(1500, 200));
}

static void test_battery_3x_divider(void)
{
    /* 1100 mV at the ADC * 3.00x = 3.30 V (a 3:1 divider) */
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 3.3f, sensor_battery_from_mv(1100, 300));
}

static void test_temp_in_range(void)
{
    TEST_ASSERT_TRUE(sensor_temp_in_range(25.0f));
    TEST_ASSERT_TRUE(sensor_temp_in_range(-55.0f));   /* lower bound inclusive */
    TEST_ASSERT_TRUE(sensor_temp_in_range(125.0f));   /* upper bound inclusive */
    TEST_ASSERT_FALSE(sensor_temp_in_range(-127.0f)); /* sensor not-found marker */
    TEST_ASSERT_FALSE(sensor_temp_in_range(125.1f));
    TEST_ASSERT_FALSE(sensor_temp_in_range(-55.1f));
}

int main(void)
{
    UNITY_BEGIN();
    RUN_TEST(test_open_loop_zero);
    RUN_TEST(test_open_loop_below_threshold);
    RUN_TEST(test_open_loop_threshold_boundary);
    RUN_TEST(test_dead_band_negative_ratio_clamped);
    RUN_TEST(test_4ma_zero_m);
    RUN_TEST(test_midscale);
    RUN_TEST(test_full_scale);
    RUN_TEST(test_overcurrent_clamped);
    RUN_TEST(test_battery_2x_divider);
    RUN_TEST(test_battery_3x_divider);
    RUN_TEST(test_temp_in_range);
    return UNITY_END();
}
