#include "sensor.h"
#include "esp_adc/adc_oneshot.h"
#include "esp_adc/adc_cali.h"
#include "esp_adc/adc_cali_scheme.h"
#include "esp_log.h"
#include "sdkconfig.h"

static const char *TAG = "sensor";

#define ADC_UNIT     ADC_UNIT_1
#define ADC_CHANNEL  ((adc_channel_t)CONFIG_WELLD_SENSOR_ADC_CHANNEL)
#define ADC_ATTEN    ADC_ATTEN_DB_12   /* 0 – ~3.1 V input range */
#define NUM_SAMPLES  16

#define CURRENT_MIN_UA  4000   /* 4 mA  = 0 % depth */
#define CURRENT_MAX_UA  20000  /* 20 mA = 100 % depth */

float sensor_read_level(void)
{
    adc_oneshot_unit_handle_t adc_hdl;
    adc_oneshot_unit_init_cfg_t unit_cfg = { .unit_id = ADC_UNIT };
    ESP_ERROR_CHECK(adc_oneshot_new_unit(&unit_cfg, &adc_hdl));

    adc_oneshot_chan_cfg_t ch_cfg = {
        .atten    = ADC_ATTEN,
        .bitwidth = ADC_BITWIDTH_DEFAULT,
    };
    ESP_ERROR_CHECK(adc_oneshot_config_channel(adc_hdl, ADC_CHANNEL, &ch_cfg));

    adc_cali_handle_t cali_hdl = NULL;
    bool calibrated = false;
#if ADC_CALI_SCHEME_CURVE_FITTING_SUPPORTED
    adc_cali_curve_fitting_config_t cali_cfg = {
        .unit_id  = ADC_UNIT,
        .atten    = ADC_ATTEN,
        .bitwidth = ADC_BITWIDTH_DEFAULT,
    };
    calibrated = (adc_cali_create_scheme_curve_fitting(&cali_cfg, &cali_hdl) == ESP_OK);
#endif

    int raw_sum = 0;
    for (int i = 0; i < NUM_SAMPLES; i++) {
        int raw;
        ESP_ERROR_CHECK(adc_oneshot_read(adc_hdl, ADC_CHANNEL, &raw));
        raw_sum += raw;
    }
    int raw_avg = raw_sum / NUM_SAMPLES;

    int voltage_mv;
    if (calibrated) {
        ESP_ERROR_CHECK(adc_cali_raw_to_voltage(cali_hdl, raw_avg, &voltage_mv));
        adc_cali_delete_scheme_curve_fitting(cali_hdl);
    } else {
        /* Fallback: linear approximation, 3300 mV full-scale at 12-bit */
        voltage_mv = (raw_avg * 3300) / 4095;
    }
    adc_oneshot_del_unit(adc_hdl);

    /* I (µA) = V (mV) * 1 000 000 / R (mΩ)
     * Example: 400 mV / 100 000 mΩ → 4 000 µA = 4 mA */
    int current_ua = (int)(((int64_t)voltage_mv * 1000000LL) /
                            CONFIG_WELLD_SENSOR_SHUNT_MILLIOHMS);

    float ratio = (float)(current_ua - CURRENT_MIN_UA) /
                  (float)(CURRENT_MAX_UA - CURRENT_MIN_UA);
    if (ratio < 0.0f) ratio = 0.0f;
    if (ratio > 1.0f) ratio = 1.0f;

    float level_m = ratio * (CONFIG_WELLD_SENSOR_MAX_DEPTH_CM / 100.0f);
    ESP_LOGI(TAG, "raw=%d  voltage=%d mV  current=%d µA  level=%.2f m",
             raw_avg, voltage_mv, current_ua, level_m);
    return level_m;
}
