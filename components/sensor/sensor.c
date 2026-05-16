#include "sensor.h"
#include "driver/i2c_master.h"
#include "driver/gpio.h"
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

#define NUM_SAMPLES 16   /* ADS1115 reads averaged to reduce quantisation noise */

#define NVS_NAMESPACE       "welld"
#define NVS_KEY_OFFSET      "offset_cm"
#define NVS_KEY_DS18B20_ROM "ds18b20_rom"

/* INT32_MIN is used as a sentinel meaning "not yet loaded from NVS".
   Avoids an NVS read on every call after the first wakeup. */
static int s_offset_cm = INT32_MIN;

/* I²C bus and device handles — initialised by sensor_i2c_init(). */
static i2c_master_bus_handle_t  s_i2c_bus = NULL;
static i2c_master_dev_handle_t  s_ads_dev = NULL;
static i2c_master_dev_handle_t  s_max_dev = NULL;

/* Configure VLOOP and BATT_DIV_EN GPIO outputs and drive them LOW at init time.
 * This ensures the TPS61023 boost and battery divider are off by default. */
static void power_gpio_init(void) {
    const int pins[] = {
        CONFIG_WELLD_VLOOP_GPIO,
        CONFIG_WELLD_BATT_DIV_EN_GPIO,
    };
    gpio_config_t cfg = {
        .mode         = GPIO_MODE_OUTPUT,
        .pull_up_en   = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type    = GPIO_INTR_DISABLE,
    };
    for (int i = 0; i < (int)(sizeof(pins)/sizeof(pins[0])); i++) {
        cfg.pin_bit_mask = 1ULL << pins[i];
        gpio_config(&cfg);
        gpio_set_level(pins[i], 0);
    }
}

/* Initialise the shared I2C bus and register ADS1115 (0x48) + MAX17048 (0x36).
 * Also configures VLOOP and BATT_DIV_EN GPIO outputs and drives them LOW.
 * Must be called before any sensor_read_level() or sensor_read_battery_v(). */
esp_err_t sensor_i2c_init(void) {
    power_gpio_init();

    i2c_master_bus_config_t bus_cfg = {
        .clk_source            = I2C_CLK_SRC_DEFAULT,
        .i2c_port              = I2C_NUM_0,
        .sda_io_num            = CONFIG_WELLD_I2C_SDA_GPIO,
        .scl_io_num            = CONFIG_WELLD_I2C_SCL_GPIO,
        .glitch_ignore_cnt     = 7,
        .flags.enable_internal_pullup = true,
    };
    esp_err_t ret = i2c_new_master_bus(&bus_cfg, &s_i2c_bus);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "I2C bus init failed: %s", esp_err_to_name(ret));
        return ret;
    }

    i2c_device_config_t ads_cfg = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address  = 0x48,
        .scl_speed_hz    = 400000,
    };
    ret = i2c_master_bus_add_device(s_i2c_bus, &ads_cfg, &s_ads_dev);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "ADS1115 add failed: %s", esp_err_to_name(ret));
        return ret;
    }

    i2c_device_config_t max_cfg = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address  = 0x36,
        .scl_speed_hz    = 400000,
    };
    /* MAX17048 is non-fatal — board may not have it */
    if (i2c_master_bus_add_device(s_i2c_bus, &max_cfg, &s_max_dev) != ESP_OK) {
        ESP_LOGW(TAG, "MAX17048 not found on I2C bus");
        s_max_dev = NULL;
    }
    return ESP_OK;
}

/* Read one ADS1115 channel in single-shot mode.
 * ch: 0 = AIN0/GND (4-20 mA shunt), 2 = AIN2/GND (battery divider)
 * PGA ±2.048 V, 860 SPS, comparator disabled.
 * Returns millivolts (signed), or INT_MIN on error. */
static int ads1115_read_mv(int ch) {
    if (!s_ads_dev) return INT_MIN;

    /* Config register (0x01):
     *  Bit 15    OS   = 1  (start single-shot)
     *  Bits 14:12 MUX = 100 (AIN0/GND) or 110 (AIN2/GND)
     *  Bits 11:9  PGA = 010 (±2.048 V)
     *  Bit 8     MODE = 1  (single-shot)
     *  Bits 7:5  DR   = 111 (860 SPS)
     *  Bits 1:0  COMP_QUE = 11 (disable)
     * High byte: AIN0 = 0xC5, AIN2 = 0xE5
     * Low byte:  0xE3 */
    uint8_t hi  = (ch == 2) ? 0xE5 : 0xC5;
    uint8_t buf[3] = {0x01, hi, 0xE3};
    if (i2c_master_transmit(s_ads_dev, buf, 3, 50) != ESP_OK) return INT_MIN;

    vTaskDelay(pdMS_TO_TICKS(3));   /* 1/860 SPS ≈ 1.2 ms; 3 ms margin */

    uint8_t ptr = 0x00;
    uint8_t data[2] = {0};
    if (i2c_master_transmit_receive(s_ads_dev, &ptr, 1, data, 2, 50) != ESP_OK)
        return INT_MIN;

    int16_t raw = (int16_t)(uint16_t)((data[0] << 8) | data[1]);
    /* ±2.048 V PGA: 1 LSB = 62.5 µV.  mv = raw * 2048 / 32768 */
    return (int)(raw * 2048L / 32768);
}

/* Returns the current level offset in cm, loading it from NVS on first call.
 * Falls back to CONFIG_WELLD_SENSOR_OFFSET_CM if no NVS value exists yet. */
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

/* Read the water level in metres, applying the NVS-stored offset.
 * Gates the TPS61023 12V boost (VLOOP GPIO) for the duration of the read.
 * Uses ADS1115 AIN0 to measure the shunt voltage across the 4-20 mA loop.
 * Returns -1.0 if the transducer loop current indicates an open circuit. */
float sensor_read_level(void)
{
    /* Gate VLOOP HIGH to enable the TPS61023 boost converter */
    gpio_set_level(CONFIG_WELLD_VLOOP_GPIO, 1);
    vTaskDelay(pdMS_TO_TICKS(5));   /* 5 ms soft-start margin */

    int volt_mv = ads1115_read_mv(0);

    /* Drive VLOOP LOW immediately after read — max ON time is 100 ms */
    gpio_set_level(CONFIG_WELLD_VLOOP_GPIO, 0);

    if (volt_mv == INT_MIN) {
        ESP_LOGE(TAG, "ADS1115 read failed on AIN0 (4-20 mA shunt)");
        return -1.0f;
    }

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

    /* Persist the ROM address when it changes (first boot, or sensor replaced).
     * Warn explicitly when we are using a different ROM than the stored one —
     * this catches a replaced sensor before NVS is updated. */
    if (ds18b20 && selected_rom != preferred_rom) {
        if (has_preferred) {
            ESP_LOGW(TAG, "DS18B20 ROM changed: stored=%016llx active=%016llx",
                     (unsigned long long)preferred_rom, (unsigned long long)selected_rom);
        }
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

/* Read battery voltage.
 * Prefers the MAX17048 VCELL register (coulomb-counted, no divider needed).
 * Falls back to ADS1115 AIN2 via the gated battery divider (GPIO15) when the
 * MAX17048 is not present or returns an error.
 * Returns -1.0 if both methods fail or battery monitoring is not available. */
float sensor_read_battery_v(void)
{
    /* Prefer MAX17048 VCELL (coulomb-counted, no divider needed) */
    if (s_max_dev) {
        float v = sensor_read_battery_vcell_v();
        if (v > 0.0f) {
            ESP_LOGI(TAG, "battery=%.2f V (MAX17048)", v);
            return v;
        }
        ESP_LOGW(TAG, "MAX17048 VCELL unavailable, falling back to divider");
    }
    /* Fallback: gate the divider, read ADS1115 AIN2, ungate */
    gpio_set_level(CONFIG_WELLD_BATT_DIV_EN_GPIO, 1);
    vTaskDelay(pdMS_TO_TICKS(1));
    int mv = ads1115_read_mv(2);
    gpio_set_level(CONFIG_WELLD_BATT_DIV_EN_GPIO, 0);
    if (mv == INT_MIN) return -1.0f;
    float batt_v = sensor_battery_from_mv(mv, CONFIG_WELLD_BATT_DIVIDER_RATIO);
    ESP_LOGI(TAG, "battery=%.2f V (divider)", batt_v);
    return batt_v;
}

/* Read battery voltage from MAX17048 VCELL register (0x02).
 * Returns volts, or -1.0f on error or device not present. */
float sensor_read_battery_vcell_v(void)
{
    if (!s_max_dev) return -1.0f;
    uint8_t reg = 0x02;
    uint8_t data[2] = {0};
    if (i2c_master_transmit_receive(s_max_dev, &reg, 1, data, 2, 50) != ESP_OK) {
        ESP_LOGW(TAG, "MAX17048 VCELL read error");
        return -1.0f;
    }
    uint16_t raw = ((uint16_t)data[0] << 8) | data[1];
    return (float)raw * 78.125e-6f;   /* 1 LSB = 78.125 µV */
}

/* Read battery state-of-charge from MAX17048 SOC register (0x04).
 * Returns 0-100 (integer percent), or -1 on error or device not present. */
int sensor_read_battery_soc(void)
{
    if (!s_max_dev) return -1;
    uint8_t reg = 0x04;
    uint8_t data[2] = {0};
    if (i2c_master_transmit_receive(s_max_dev, &reg, 1, data, 2, 50) != ESP_OK) {
        ESP_LOGW(TAG, "MAX17048 SOC read error");
        return -1;
    }
    return (int)data[0];   /* high byte = integer percent 0-100 */
}
