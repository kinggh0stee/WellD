/* Single source of truth for the sensor test suite. Pure-math tests are
 * shared between on-device (ESP-IDF Unity, app_main) and host (plain
 * CMake at test/host/, main + -DHOST_BUILD) builds. NVS round-trip
 * tests run on-device only — flash isn't available on the host. */

#include "unity.h"
#include "sensor.h"
#include <math.h>

#ifndef HOST_BUILD
#include "nvs_flash.h"
#endif

#ifdef HOST_BUILD
void setUp(void) {}
void tearDown(void) {}
#endif

/* All level cases assume default config: 100 Ω shunt, 6 m max depth.
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

static void test_battery_zero_adc(void)
{
    /* 0 mV ADC reading (dead/disconnected battery) must return 0.0 V */
    TEST_ASSERT_EQUAL_FLOAT(0.0f, sensor_battery_from_mv(0, 200));
}

static void test_battery_no_divider(void)
{
    /* ratio_x100 = 100 means a 1:1 direct measurement (no resistor divider) */
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 3.3f, sensor_battery_from_mv(3300, 100));
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

/* Water-density correction, 20 °C reference. Tabulated fresh-water density
 * (kg/m³): 10 °C 999.70, 20 °C 998.21, 25 °C 997.05, 30 °C 995.65. The exact
 * correction for a reading taken at T is rho20 / rhoT. */
static void test_temp_factor_unity_at_reference(void)
{
    TEST_ASSERT_EQUAL_FLOAT(1.0f, sensor_temp_level_factor(20.0f, 207));
    TEST_ASSERT_EQUAL_FLOAT(1.0f, sensor_temp_level_factor(5.0f, 0));  /* coeff 0 = off */
}

static void test_temp_factor_warm_water_raises_level(void)
{
    /* Warm water is less dense: a given column presses less, the transducer
     * under-reads, so the correction must RAISE the level. The pre-1.2.1
     * formula lowered it. */
    float f = sensor_temp_level_factor(30.0f, 207);
    TEST_ASSERT_TRUE(f > 1.0f);
    TEST_ASSERT_FLOAT_WITHIN(1e-5f, 1.0f / (1.0f - 0.00207f), f);
    TEST_ASSERT_FLOAT_WITHIN(0.0006f, 998.21f / 995.65f, f);
}

static void test_temp_factor_cold_water_lowers_level(void)
{
    float f = sensor_temp_level_factor(10.0f, 207);
    TEST_ASSERT_TRUE(f < 1.0f);
    TEST_ASSERT_FLOAT_WITHIN(1e-5f, 1.0f / 1.00207f, f);
    TEST_ASSERT_FLOAT_WITHIN(0.0006f, 998.21f / 999.70f, f);
    /* 150 ppm/°C is exact at 10 °C (documented Kconfig tip). */
    TEST_ASSERT_FLOAT_WITHIN(0.00002f, 998.21f / 999.70f,
                             sensor_temp_level_factor(10.0f, 150));
}

static void test_temp_factor_tracks_density_near_reference(void)
{
    TEST_ASSERT_FLOAT_WITHIN(0.0002f, 998.21f / 997.05f,
                             sensor_temp_level_factor(25.0f, 207));
}

static void test_temp_factor_degenerate_inputs(void)
{
    TEST_ASSERT_EQUAL_FLOAT(1.0f, sensor_temp_level_factor(NAN, 207));
    /* Denominator 1 - 500e-6 * 2000 = 0: refuse rather than divide by 0. */
    TEST_ASSERT_EQUAL_FLOAT(1.0f, sensor_temp_level_factor(2020.0f, 500));
}

#ifndef HOST_BUILD
/* NVS round-trip tests need real flash — on-device only. */

static void test_offset_round_trip(void)
{
    sensor_set_offset_cm(-42);
    sensor_offset_cache_reset();   /* force re-read from NVS */
    TEST_ASSERT_EQUAL_INT(-42, sensor_get_offset_cm());

    sensor_set_offset_cm(123);
    sensor_offset_cache_reset();
    TEST_ASSERT_EQUAL_INT(123, sensor_get_offset_cm());
}

static void test_offset_clamped_on_set(void)
{
    sensor_set_offset_cm(9999);
    sensor_offset_cache_reset();
    TEST_ASSERT_EQUAL_INT(600, sensor_get_offset_cm());

    sensor_set_offset_cm(-9999);
    sensor_offset_cache_reset();
    TEST_ASSERT_EQUAL_INT(-600, sensor_get_offset_cm());
}
#endif  /* !HOST_BUILD */

static int run_tests(void)
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
    RUN_TEST(test_battery_zero_adc);
    RUN_TEST(test_battery_no_divider);
    RUN_TEST(test_temp_in_range);
    RUN_TEST(test_temp_factor_unity_at_reference);
    RUN_TEST(test_temp_factor_warm_water_raises_level);
    RUN_TEST(test_temp_factor_cold_water_lowers_level);
    RUN_TEST(test_temp_factor_tracks_density_near_reference);
    RUN_TEST(test_temp_factor_degenerate_inputs);
#ifndef HOST_BUILD
    RUN_TEST(test_offset_round_trip);
    RUN_TEST(test_offset_clamped_on_set);
#endif
    return UNITY_END();
}

#ifdef HOST_BUILD
int main(void) { return run_tests(); }
#else
void app_main(void)
{
    /* NVS is required for the offset round-trip tests. The other tests do
     * not depend on it but a single init keeps the test app simple. */
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        nvs_flash_erase();
        nvs_flash_init();
    }
    run_tests();
}
#endif
