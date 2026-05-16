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
#include <assert.h>
#include <limits.h>

static const char *TAG = "sensor";

#define ADC_UNIT    ADC_UNIT_1
#define ADC_ATTEN   ADC_ATTEN_DB_12   /* 0 – ~3.1 V input range */
#define NUM_SAMPLES 16                 /* averaged to reduce quantisation noise */

#define NVS_NAMESPACE       "welld"
#define NVS_KEY_OFFSET      "offset_cm"
#define NVS_KEY_DS18B20_ROM "ds18b20_rom"

/* Shared ADC and calibration handles, managed by sensor_adc_acquire / sensor_adc_release.
 * NULL until acquire is called; level and battery reads assert these are non-NULL. */
static adc_oneshot_unit_handle_t s_adc_hdl  = NULL;
static adc_cali_handle_t         s_cali_hdl = NULL;

/* INT32_MIN is used as a sentinel meaning "not yet loaded from NVS".
   Avoids an NVS read on every call after the first wakeup. */
static int s_offset_cm = INT32_MIN;

/* Create the ADC unit and calibration handles shared across all ADC reads in one
 * wakeup. Call once before any sensor_read_level() or sensor_read_battery_v() call;
 * pair every acquire with a sensor_adc_release(). */
void sensor_adc_acquire(void)
{
    adc_oneshot_unit_init_cfg_t unit_cfg = { .unit_id = ADC_UNIT };
    ESP_ERROR_CHECK(adc_oneshot_new_unit(&unit_cfg, &s_adc_hdl));

#if ADC_CALI_SCHEME_CURVE_FITTING_SUPPORTED
    adc_cali_curve_fitting_config_t cali_cfg = {
        .unit_id  = ADC_UNIT,
        .atten    = ADC_ATTEN,
        .bitwidth = ADC_BITWIDTH_DEFAULT,
    };
    if (adc_cali_create_scheme_curve_fitting(&cali_cfg, &s_cali_hdl) != ESP_OK)
        s_cali_hdl = NULL;
#endif
}

/* Release the handles created by sensor_adc_acquire(). */
void sensor_adc_release(void)
{
    if (s_cali_hdl) {
#if ADC_CALI_SCHEME_CURVE_FITTING_SUPPORTED
        adc_cali_delete_scheme_curve_fitting(s_cali_hdl);
#endif
        s_cali_hdl = NULL;
    }
    if (s_adc_hdl) {
        adc_oneshot_del_unit(s_adc_hdl);
        s_adc_hdl = NULL;
    }
}

/* Read NUM_SAMPLES from channel, applying per-sample curve-fitting calibration
 * to correct ADC non-linearity before accumulating. Samples are spaced 1 ms
 * apart so 16 samples span ~15 ms, averaging out 50/60 Hz ripple induced by
 * nearby AC wiring on the 4-20 mA loop cable.
 *
 * Requires sensor_adc_acquire() to have been called first. */
static int adc_read_avg_mv(adc_channel_t channel)
{
    assert(s_adc_hdl != NULL);

    adc_oneshot_chan_cfg_t ch_cfg = {
        .atten    = ADC_ATTEN,
        .bitwidth = ADC_BITWIDTH_DEFAULT,
    };
    ESP_ERROR_CHECK(adc_oneshot_config_channel(s_adc_hdl, channel, &ch_cfg));

    int mv_sum = 0;
    for (int i = 0; i < NUM_SAMPLES; i++) {
        int raw;
        ESP_ERROR_CHECK(adc_oneshot_read(s_adc_hdl, channel, &raw));
        int mv;
        if (s_cali_hdl && adc_cali_raw_to_voltage(s_cali_hdl, raw, &mv) == ESP_OK) {
            /* per-sample calibration: correct non-linearity before summing */
        } else {
            mv = (raw * 3300) / 4095;
        }
        mv_sum += mv;
        if (i < NUM_SAMPLES - 1) vTaskDelay(pdMS_TO_TICKS(1));
    }
    return mv_sum / NUM_SAMPLES;
}

int sensor_get_offset_cm(void)
{
    if (s_offset_cm == INT32_MIN) {
        nvs_handle_t h;
        int32_t val = CONFIG_WELLD_SENSOR_OFFSET_CM;
        if (nvs_open(NVS_NAMESPACE, NVS_READONLY, &h) == ESP_OK) {
            nvs_get_i32(h, NVS_KEY_OFFSET, &val);
            nvs_close(h);
        }
        if (val < -600) val = -600;
        if (val >  600) val =  600;
        s_offset_cm = (int)val;
    }
    return s_offset_cm;
}

void sensor_set_offset_cm(int offset_cm)
{
    if (offset_cm < -600) offset_cm = -600;
    if (offset_cm >  600) offset_cm =  600;
    s_offset_cm = offset_cm;
    nvs_handle_t h;
    if (nvs_open(NVS_NAMESPACE, NVS_READWRITE, &h) == ESP_OK) {
        nvs_set_i32(h, NVS_KEY_OFFSET, (int32_t)offset_cm);
        nvs_commit(h);
        nvs_close(h);
    }
}

void sensor_offset_cache_reset(void)
{
    s_offset_cm = INT32_MIN;
}

/* Read water level in metres. Returns -1.0 on open-loop / disconnected transducer. */
float sensor_read_level(void)
{
    int volt_mv = adc_read_avg_mv((adc_channel_t)CONFIG_WELLD_SENSOR_ADC_CHANNEL);
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
        ESP_LOGI(TAG, "voltage=%d mV  current=%d µA  level=%.2f m (offset %.0f cm)",
                 volt_mv, current_ua, level_m, offset_m * 100.0f);
    else
        ESP_LOGI(TAG, "voltage=%d mV  current=%d µA  level=%.2f m",
                 volt_mv, current_ua, level_m);
    return level_m;
}

/* Scan the 1-Wire bus for a DS18B20. Prefers the ROM address stored in NVS from
 * the previous discovery so the same sensor is always read when multiple devices
 * share the bus. Falls back to the first valid DS18B20 found and updates NVS.
 * Returns -127.0 if no sensor is found or the reading is outside the rated range. */
float sensor_read_temperature(void)
{
    onewire_bus_handle_t bus = NULL;
    onewire_bus_config_t bus_cfg = { .bus_gpio_num = CONFIG_WELLD_DS18B20_GPIO };
    onewire_bus_rmt_config_t rmt_cfg = { .max_rx_bytes = 10 };
    if (onewire_new_bus_rmt(&bus_cfg, &rmt_cfg, &bus) != ESP_OK) {
        ESP_LOGE(TAG, "1-Wire bus init failed");
        return -127.0f;
    }

    uint64_t preferred_rom = 0;
    bool has_preferred = false;
    {
        nvs_handle_t nvs_h;
        if (nvs_open(NVS_NAMESPACE, NVS_READONLY, &nvs_h) == ESP_OK) {
            has_preferred = nvs_get_u64(nvs_h, NVS_KEY_DS18B20_ROM, &preferred_rom) == ESP_OK;
            nvs_close(nvs_h);
        }
    }

    ds18b20_device_handle_t ds18b20 = NULL;
    uint64_t selected_rom = 0;
    onewire_device_iter_handle_t iter = NULL;
    if (onewire_new_device_iter(bus, &iter) == ESP_OK) {
        onewire_device_t device;
        esp_err_t res;
        do {
            res = onewire_device_iter_get_next(iter, &device);
            if (res != ESP_OK) continue;
            ds18b20_config_t ds_cfg = {};
            ds18b20_device_handle_t candidate = NULL;
            if (ds18b20_new_device_from_enumeration(&device, &ds_cfg, &candidate) != ESP_OK)
                continue;
            bool is_preferred = has_preferred && device.address == preferred_rom;
            if (!ds18b20 || is_preferred) {
                if (ds18b20) ds18b20_del_device(ds18b20);
                ds18b20 = candidate;
                selected_rom = device.address;
                if (is_preferred) break;
            } else {
                ds18b20_del_device(candidate);
            }
        } while (res != ESP_ERR_NOT_FOUND);
        onewire_del_device_iter(iter);
    }

    /* Persist the ROM address when it changes (first boot, or sensor replaced). */
    if (ds18b20 && selected_rom != preferred_rom) {
        nvs_handle_t nvs_h;
        if (nvs_open(NVS_NAMESPACE, NVS_READWRITE, &nvs_h) == ESP_OK) {
            nvs_set_u64(nvs_h, NVS_KEY_DS18B20_ROM, selected_rom);
            nvs_commit(nvs_h);
            nvs_close(nvs_h);
        }
        ESP_LOGI(TAG, "DS18B20 ROM 0x%016llx %s NVS",
                 (unsigned long long)selected_rom,
                 has_preferred ? "updated in" : "stored to");
    }

    if (!ds18b20) {
        ESP_LOGE(TAG, "no DS18B20 found on GPIO %d", CONFIG_WELLD_DS18B20_GPIO);
        onewire_bus_del(bus);
        return -127.0f;
    }

    float temp = -127.0f;
    if (ds18b20_trigger_temperature_conversion_for_all(bus) == ESP_OK) {
        vTaskDelay(pdMS_TO_TICKS(750));  /* 12-bit conversion time per datasheet */
        ds18b20_get_temperature(ds18b20, &temp);
    }
    ds18b20_del_device(ds18b20);
    onewire_bus_del(bus);

    if (!sensor_temp_in_range(temp)) {
        ESP_LOGW(TAG, "DS18B20 reading %.1f °C outside rated range, discarding", temp);
        return -127.0f;
    }
    ESP_LOGI(TAG, "temperature=%.1f °C", temp);
    return temp;
}

/* Read battery voltage through an external resistor divider.
 * Returns -1.0 if battery monitoring is disabled at build time. */
float sensor_read_battery_v(void)
{
#if CONFIG_WELLD_BATT_ADC_CHANNEL >= 0
    int volt_mv = adc_read_avg_mv((adc_channel_t)CONFIG_WELLD_BATT_ADC_CHANNEL);
    float batt_v = sensor_battery_from_mv(volt_mv, CONFIG_WELLD_BATT_DIVIDER_RATIO);
    ESP_LOGI(TAG, "battery=%.2f V", batt_v);
    return batt_v;
#else
    return -1.0f;
#endif
}
