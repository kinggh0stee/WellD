#include "sensor.h"
#include "esp_adc/adc_oneshot.h"
#include "esp_adc/adc_cali.h"
#include "esp_adc/adc_cali_scheme.h"
#include "onewire_bus.h"
#include "ds18b20.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "sdkconfig.h"
#include "nvs_flash.h"
#include "nvs.h"
#include <limits.h>

static const char *TAG = "sensor";

#define ADC_UNIT    ADC_UNIT_1
#define ADC_ATTEN   ADC_ATTEN_DB_12   /* 0 – ~3.1 V input range */
#define NUM_SAMPLES 16

#define CURRENT_MIN_UA  4000   /* 4 mA  = 0 % depth */
#define CURRENT_MAX_UA  20000  /* 20 mA = 100 % depth */

#define NVS_NAMESPACE  "welld"
#define NVS_KEY_OFFSET "offset_cm"

static int s_offset_cm = INT32_MIN;   /* sentinel: not yet loaded */

int sensor_get_offset_cm(void)
{
    if (s_offset_cm == INT32_MIN) {
        nvs_handle_t h;
        int32_t val = CONFIG_WELLD_SENSOR_OFFSET_CM;
        if (nvs_open(NVS_NAMESPACE, NVS_READONLY, &h) == ESP_OK) {
            nvs_get_i32(h, NVS_KEY_OFFSET, &val);
            nvs_close(h);
        }
        s_offset_cm = (int)val;
    }
    return s_offset_cm;
}

void sensor_set_offset_cm(int offset_cm)
{
    s_offset_cm = offset_cm;
    nvs_handle_t h;
    if (nvs_open(NVS_NAMESPACE, NVS_READWRITE, &h) == ESP_OK) {
        nvs_set_i32(h, NVS_KEY_OFFSET, (int32_t)offset_cm);
        nvs_commit(h);
        nvs_close(h);
    }
}

static int adc_read_avg(adc_channel_t channel)
{
    adc_oneshot_unit_handle_t adc_hdl;
    adc_oneshot_unit_init_cfg_t unit_cfg = { .unit_id = ADC_UNIT };
    ESP_ERROR_CHECK(adc_oneshot_new_unit(&unit_cfg, &adc_hdl));

    adc_oneshot_chan_cfg_t ch_cfg = {
        .atten    = ADC_ATTEN,
        .bitwidth = ADC_BITWIDTH_DEFAULT,
    };
    ESP_ERROR_CHECK(adc_oneshot_config_channel(adc_hdl, channel, &ch_cfg));

    int raw_sum = 0;
    for (int i = 0; i < NUM_SAMPLES; i++) {
        int raw;
        ESP_ERROR_CHECK(adc_oneshot_read(adc_hdl, channel, &raw));
        raw_sum += raw;
    }
    adc_oneshot_del_unit(adc_hdl);
    return raw_sum / NUM_SAMPLES;
}

static int raw_to_mv(int raw)
{
#if ADC_CALI_SCHEME_CURVE_FITTING_SUPPORTED
    adc_cali_handle_t cali_hdl = NULL;
    adc_cali_curve_fitting_config_t cali_cfg = {
        .unit_id  = ADC_UNIT,
        .atten    = ADC_ATTEN,
        .bitwidth = ADC_BITWIDTH_DEFAULT,
    };
    if (adc_cali_create_scheme_curve_fitting(&cali_cfg, &cali_hdl) == ESP_OK) {
        int mv;
        ESP_ERROR_CHECK(adc_cali_raw_to_voltage(cali_hdl, raw, &mv));
        adc_cali_delete_scheme_curve_fitting(cali_hdl);
        return mv;
    }
#endif
    /* Fallback: linear approximation, 3300 mV full-scale at 12-bit */
    return (raw * 3300) / 4095;
}

float sensor_level_from_mv(int volt_mv)
{
    /* I (µA) = V (mV) * 1 000 000 / R (mΩ) */
    int current_ua = (int)(((int64_t)volt_mv * 1000000LL) /
                            CONFIG_WELLD_SENSOR_SHUNT_MILLIOHMS);
    if (current_ua < 3500)   /* < 3.5 mA → loop open, transducer disconnected */
        return -1.0f;

    float ratio = (float)(current_ua - CURRENT_MIN_UA) /
                  (float)(CURRENT_MAX_UA - CURRENT_MIN_UA);
    if (ratio < 0.0f) ratio = 0.0f;
    if (ratio > 1.0f) ratio = 1.0f;
    return ratio * (CONFIG_WELLD_SENSOR_MAX_DEPTH_CM / 100.0f);
}

float sensor_read_level(void)
{
    int raw     = adc_read_avg((adc_channel_t)CONFIG_WELLD_SENSOR_ADC_CHANNEL);
    int volt_mv = raw_to_mv(raw);
    float level_m = sensor_level_from_mv(volt_mv);
    if (level_m < 0.0f) {
        ESP_LOGE(TAG, "transducer open loop (voltage=%d mV, < 3.5 mA)", volt_mv);
        return level_m;
    }
    float offset_m = sensor_get_offset_cm() / 100.0f;
    level_m += offset_m;
    if (level_m < 0.0f) level_m = 0.0f;
    int current_ua = (int)(((int64_t)volt_mv * 1000000LL) / CONFIG_WELLD_SENSOR_SHUNT_MILLIOHMS);
    if (offset_m != 0.0f)
        ESP_LOGI(TAG, "raw=%d  voltage=%d mV  current=%d µA  level=%.2f m (offset %.0f cm)",
                 raw, volt_mv, current_ua, level_m, offset_m * 100.0f);
    else
        ESP_LOGI(TAG, "raw=%d  voltage=%d mV  current=%d µA  level=%.2f m",
                 raw, volt_mv, current_ua, level_m);
    return level_m;
}

float sensor_read_temperature(void)
{
    onewire_bus_handle_t bus = NULL;
    onewire_bus_config_t bus_cfg = { .bus_gpio_num = CONFIG_WELLD_DS18B20_GPIO };
    onewire_bus_rmt_config_t rmt_cfg = { .max_rx_bytes = 10 };
    if (onewire_new_bus_rmt(&bus_cfg, &rmt_cfg, &bus) != ESP_OK) {
        ESP_LOGE(TAG, "1-Wire bus init failed");
        return -127.0f;
    }

    ds18b20_device_handle_t ds18b20 = NULL;
    onewire_device_iter_handle_t iter = NULL;
    if (onewire_new_device_iter(bus, &iter) == ESP_OK) {
        onewire_device_t device;
        esp_err_t res;
        do {
            res = onewire_device_iter_get_next(iter, &device);
            if (res == ESP_OK) {
                ds18b20_config_t ds_cfg = {};
                if (ds18b20_new_device(&device, &ds_cfg, &ds18b20) == ESP_OK) break;
            }
        } while (res != ESP_ERR_NOT_FOUND);
        onewire_del_device_iter(iter);
    }

    if (!ds18b20) {
        ESP_LOGE(TAG, "no DS18B20 found on GPIO %d", CONFIG_WELLD_DS18B20_GPIO);
        onewire_del_bus(bus);
        return -127.0f;
    }

    float temp = -127.0f;
    if (ds18b20_trigger_temperature_conversion(ds18b20) == ESP_OK) {
        vTaskDelay(pdMS_TO_TICKS(750));  /* 12-bit conversion time */
        ds18b20_get_temperature(ds18b20, &temp);
    }
    ds18b20_del_device(ds18b20);
    onewire_del_bus(bus);

    if (temp < -55.0f || temp > 125.0f) {
        ESP_LOGW(TAG, "DS18B20 reading %.1f °C outside rated range, discarding", temp);
        return -127.0f;
    }
    ESP_LOGI(TAG, "temperature=%.1f °C", temp);
    return temp;
}

float sensor_read_battery_v(void)
{
#if CONFIG_WELLD_BATT_ADC_CHANNEL >= 0
    int raw     = adc_read_avg((adc_channel_t)CONFIG_WELLD_BATT_ADC_CHANNEL);
    int volt_mv = raw_to_mv(raw);
    float batt_v = (float)volt_mv * CONFIG_WELLD_BATT_DIVIDER_RATIO / 100000.0f;
    ESP_LOGI(TAG, "battery=%.2f V", batt_v);
    return batt_v;
#else
    return -1.0f;
#endif
}
