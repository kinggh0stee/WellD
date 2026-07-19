#include "sensor.h"
#include "driver/i2c_master.h"
#include "driver/gpio.h"
#include "onewire_bus.h"
#include "ds18b20.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"
#include "sdkconfig.h"
#include "nvs_flash.h"
#include "nvs.h"
#include "welld_nvs.h"
#include <limits.h>

static const char *TAG = "sensor";

/* INT32_MIN is used as a sentinel meaning "not yet loaded from NVS".
   Avoids an NVS read on every call after the first wakeup. */
static int s_offset_cm = INT32_MIN;

/* I²C bus and device handles — initialised by sensor_i2c_init(). */
static i2c_master_bus_handle_t  s_i2c_bus = NULL;
static i2c_master_dev_handle_t  s_ads_dev = NULL;

/* Binary semaphore released by the ADS1115 DRDY falling-edge ISR.
 * Created in ads1115_drdy_init(); NULL means DRDY GPIO is not configured. */
static SemaphoreHandle_t s_ads_drdy_sem = NULL;

/* ISR handler: DRDY (GPIO12) fell — conversion complete. */
static void IRAM_ATTR ads1115_drdy_isr(void *arg)
{
    BaseType_t woken = pdFALSE;
    xSemaphoreGiveFromISR(s_ads_drdy_sem, &woken);
    if (woken) {
        portYIELD_FROM_ISR();
    }
}

/* Configure power-control GPIO outputs and drive them to their safe-idle state.
 * GPIO5 (VLOOP) and GPIO15 (BATT_DIV_EN) are driven LOW (peripherals off).
 * GPIO4 (USB_CHG CE) is driven LOW first for safe config, then HIGH.  On the
 * current 1S board (TP4056, CE strapped high in hardware) GPIO4 is unconnected
 * and this drive is a harmless no-op; it is kept for older TP5100 boards where
 * CE was GPIO-controlled. */
static void power_gpio_init(void) {
    const int pins[] = {
        CONFIG_WELLD_VLOOP_GPIO,
        CONFIG_WELLD_BATT_DIV_EN_GPIO,
        CONFIG_WELLD_USB_CHG_GPIO,
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
    /* Legacy TP5100 boards: CE is active-HIGH, R37 pulls it LOW while GPIO4
     * floats in deep sleep; drive HIGH here to re-enable charging while awake.
     * On the current 1S board GPIO4 has no schematic connection (TP4056
     * auto-charges) — this write lands on an open pad. */
    gpio_set_level(CONFIG_WELLD_USB_CHG_GPIO, 1);
}

/* ADS1115 comparator / DRDY registers */
#define ADS1115_REG_LO_THRESH   0x02
#define ADS1115_REG_HI_THRESH   0x03

/* Configure the ADS1115 ALERT/DRDY pin as a conversion-ready signal and
 * install a falling-edge ISR on GPIO CONFIG_WELLD_ADS1115_DRDY_GPIO.
 *
 * Per the ADS1115 datasheet §9.4.4: writing Lo_thresh = 0x8000 and
 * Hi_thresh = 0x7FFF overrides the comparator and makes ALERT/DRDY pulse
 * low for one conversion period when a single-shot conversion completes.
 *
 * The GPIO is open-drain so the internal pull-up must be enabled. */
static esp_err_t ads1115_drdy_init(void)
{
    /* Write Lo_thresh = 0x8000 — MSB = 1 enables DRDY mode */
    uint8_t lo_buf[3] = { ADS1115_REG_LO_THRESH, 0x80, 0x00 };
    esp_err_t ret = i2c_master_transmit(s_ads_dev, lo_buf, 3, 50);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "ADS1115 Lo_thresh write failed: %s", esp_err_to_name(ret));
        return ret;
    }

    /* Write Hi_thresh = 0x7FFF — MSB = 0 (paired with Lo_thresh MSB = 1) */
    uint8_t hi_buf[3] = { ADS1115_REG_HI_THRESH, 0x7F, 0xFF };
    ret = i2c_master_transmit(s_ads_dev, hi_buf, 3, 50);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "ADS1115 Hi_thresh write failed: %s", esp_err_to_name(ret));
        return ret;
    }

    /* Create the binary semaphore before installing the ISR. */
    SemaphoreHandle_t sem = xSemaphoreCreateBinary();
    if (!sem) {
        ESP_LOGE(TAG, "ADS1115 DRDY semaphore alloc failed");
        return ESP_ERR_NO_MEM;
    }

    /* Configure GPIO as input with internal pull-up (open-drain output). */
    gpio_config_t drdy_cfg = {
        .pin_bit_mask = 1ULL << CONFIG_WELLD_ADS1115_DRDY_GPIO,
        .mode         = GPIO_MODE_INPUT,
        .pull_up_en   = GPIO_PULLUP_ENABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type    = GPIO_INTR_NEGEDGE,
    };
    ret = gpio_config(&drdy_cfg);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "ADS1115 DRDY GPIO config failed: %s", esp_err_to_name(ret));
        vSemaphoreDelete(sem);
        return ret;
    }

    /* Install the GPIO ISR service if not already running. Ignore
     * ESP_ERR_INVALID_STATE — it just means another component started it. */
    ret = gpio_install_isr_service(0);
    if (ret != ESP_OK && ret != ESP_ERR_INVALID_STATE) {
        ESP_LOGE(TAG, "gpio_install_isr_service: %s", esp_err_to_name(ret));
        vSemaphoreDelete(sem);
        return ret;
    }

    ret = gpio_isr_handler_add(CONFIG_WELLD_ADS1115_DRDY_GPIO, ads1115_drdy_isr, NULL);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "ADS1115 DRDY ISR add failed: %s", esp_err_to_name(ret));
        vSemaphoreDelete(sem);
        return ret;
    }

    s_ads_drdy_sem = sem;

    ESP_LOGI(TAG, "ADS1115 DRDY interrupt configured on GPIO%d",
             CONFIG_WELLD_ADS1115_DRDY_GPIO);
    return ESP_OK;
}

/* I2C bus recovery: if SDA is stuck LOW, clock out 9 pulses on SCL
 * (GPIO open-drain mode) to release any peripheral holding the bus. */
static void i2c_bus_recover(void)
{
    int sda = CONFIG_WELLD_I2C_SDA_GPIO;
    int scl = CONFIG_WELLD_I2C_SCL_GPIO;

    gpio_config_t cfg = {
        .mode         = GPIO_MODE_OUTPUT_OD,
        .pull_up_en   = GPIO_PULLUP_ENABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type    = GPIO_INTR_DISABLE,
    };

    /* Configure SDA as input to sample its level */
    cfg.pin_bit_mask = 1ULL << sda;
    gpio_config(&cfg);
    cfg.pin_bit_mask = 1ULL << scl;
    gpio_config(&cfg);

    gpio_set_level(scl, 1);
    gpio_set_level(sda, 1);
    vTaskDelay(pdMS_TO_TICKS(1));

    if (gpio_get_level(sda) == 0) {
        ESP_LOGW(TAG, "SDA stuck LOW — performing I2C bus recovery");
        for (int i = 0; i < 9; i++) {
            gpio_set_level(scl, 0);
            vTaskDelay(pdMS_TO_TICKS(1));
            gpio_set_level(scl, 1);
            vTaskDelay(pdMS_TO_TICKS(1));
            if (gpio_get_level(sda)) {
                ESP_LOGI(TAG, "SDA released after %d clock pulses", i + 1);
                break;
            }
        }
        /* Send STOP condition: SDA LOW → SCL HIGH → SDA HIGH */
        gpio_set_level(sda, 0);
        vTaskDelay(pdMS_TO_TICKS(1));
        gpio_set_level(scl, 1);
        vTaskDelay(pdMS_TO_TICKS(1));
        gpio_set_level(sda, 1);
        vTaskDelay(pdMS_TO_TICKS(1));
    }
}

/* Initialise the shared I2C bus and register ADS1115 (0x48) only.
 * ADS1115 is the only I2C device.
 * Also configures VLOOP and BATT_DIV_EN GPIO outputs and drives them LOW.
 * Must be called before any sensor_read_level() or sensor_read_battery_v(). */
esp_err_t sensor_i2c_init(void) {
    power_gpio_init();
    i2c_bus_recover();

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

    /* Configure ADS1115 DRDY interrupt (non-fatal: falls back to polling). */
    if (ads1115_drdy_init() != ESP_OK) {
        ESP_LOGW(TAG, "ADS1115 DRDY init failed — falling back to register polling");
        s_ads_drdy_sem = NULL;   /* ensure polling path is taken */
    }

    return ESP_OK;
}

/* ADS1115 register addresses */
#define ADS1115_REG_CONVERT     0x00
#define ADS1115_REG_CONFIG      0x01

#if CONFIG_WELLD_ADC_OVERSAMPLE_ENABLED
static int ads1115_read_mv(int ch);  /* defined below; needed by ads1115_read_mv_median */

static void sort3(int *a, int *b, int *c)
{
    int tmp;
    if (*a > *b) { tmp = *a; *a = *b; *b = tmp; }
    if (*b > *c) { tmp = *b; *b = *c; *c = tmp; }
    if (*a > *b) { tmp = *a; *a = *b; *b = tmp; }
}

static int ads1115_read_mv_median(int ch)
{
    int s[3];
    for (int i = 0; i < 3; i++) {
        s[i] = ads1115_read_mv(ch);
        if (s[i] == INT_MIN) return INT_MIN;
    }
    sort3(&s[0], &s[1], &s[2]);
    return s[1];  /* median */
}
#endif /* CONFIG_WELLD_ADC_OVERSAMPLE_ENABLED */

/* Config register bitfields */
#define ADS1115_OS_START        (1U << 7)
#define ADS1115_MUX_AIN0        (4U << 4)   /* AIN0 vs GND */
#define ADS1115_MUX_AIN2        (6U << 4)   /* AIN2 vs GND */
#define ADS1115_PGA_2V048       (2U << 1)   /* ±2.048 V (4-20 mA shunt, AIN0) */
#define ADS1115_PGA_4V096       (1U << 1)   /* ±4.096 V (battery, AIN2 — the 1S
                                             * ÷2 divider puts up to 2.1 V on
                                             * AIN2; ±2.048 V would clip right
                                             * at full charge) */
#define ADS1115_MODE_SINGLE     (1U << 0)
#define ADS1115_DR_860SPS       (7U << 5)
/* COMP_QUE = 00: assert after one conversion — required for DRDY mode.
 * COMP_POL = 0 (active-low), COMP_LAT = 0 (non-latching). */
#define ADS1115_COMP_QUE_ONE    (0U << 0)

/* Maximum time to wait for an ADS1115 conversion-complete signal (ms).
 * At 860 SPS one conversion takes ~1.16 ms; 10 ms gives an 8× safety margin. */
#define ADS1115_CONV_TIMEOUT_MS 10

/* Wait for an ADS1115 single-shot conversion to complete.
 *
 * Primary path (s_ads_drdy_sem != NULL): blocks on the binary semaphore
 * that the GPIO12 falling-edge ISR releases when DRDY asserts.  The
 * semaphore is drained before starting every conversion so a stale token
 * from a previous cycle cannot produce a false-ready.
 *
 * Fallback path (semaphore NULL or ISR not configured): poll the OS bit in
 * the config register, 2 ms per iteration, up to ADS1115_CONV_TIMEOUT_MS.
 *
 * Returns ESP_OK on success, ESP_ERR_TIMEOUT if the edge never arrives. */
static esp_err_t ads1115_wait_conversion_done(void)
{
    if (s_ads_drdy_sem) {
        /* Block until the ISR fires or the timeout expires. */
        if (xSemaphoreTake(s_ads_drdy_sem,
                           pdMS_TO_TICKS(ADS1115_CONV_TIMEOUT_MS)) == pdTRUE) {
            return ESP_OK;
        }
        ESP_LOGW(TAG, "ADS1115 DRDY timeout (%d ms) — DRDY edge not received",
                 ADS1115_CONV_TIMEOUT_MS);
        return ESP_ERR_TIMEOUT;
    }

    /* Polling fallback: read OS bit from config register. */
    uint8_t reg = ADS1115_REG_CONFIG;
    uint8_t cfg[2];
    for (uint32_t waited = 0; waited < ADS1115_CONV_TIMEOUT_MS; waited += 2) {
        if (i2c_master_transmit_receive(s_ads_dev, &reg, 1, cfg, 2, 50) != ESP_OK)
            return ESP_ERR_INVALID_RESPONSE;
        if (cfg[0] & ADS1115_OS_START)
            return ESP_OK;
        vTaskDelay(pdMS_TO_TICKS(2));
    }
    return ESP_ERR_TIMEOUT;
}

/* Read one ADS1115 channel in single-shot mode.
 * ch: 0 = AIN0/GND (4-20 mA shunt, PGA ±2.048 V),
 *     2 = AIN2/GND (battery divider, PGA ±4.096 V — see define above).
 * 860 SPS.  COMP_QUE = one-shot assert, required for DRDY.
 * Returns millivolts (signed), or INT_MIN on error. */
static int ads1115_read_mv(int ch) {
    if (!s_ads_dev) return INT_MIN;

    /* Drain any stale DRDY token left from a previous conversion so we block
     * on the edge that belongs to *this* conversion, not a prior one.
     * Sequence: disable IRQ → drain → write config (starts conversion) →
     * re-enable IRQ.  This ensures the interrupt is armed only after the
     * conversion has actually started; re-enabling before the I2C write
     * completes would open a race window where a noise edge could give the
     * semaphore before our conversion result is ready. */
    if (s_ads_drdy_sem) {
        gpio_intr_disable(CONFIG_WELLD_ADS1115_DRDY_GPIO);
        xSemaphoreTake(s_ads_drdy_sem, 0);
    }

    uint8_t mux = (ch == 2) ? ADS1115_MUX_AIN2 : ADS1115_MUX_AIN0;
    uint8_t pga = (ch == 2) ? ADS1115_PGA_4V096 : ADS1115_PGA_2V048;
    uint8_t buf[3] = {
        ADS1115_REG_CONFIG,
        ADS1115_OS_START | mux | pga | ADS1115_MODE_SINGLE | ADS1115_DR_860SPS,
        ADS1115_COMP_QUE_ONE   /* assert DRDY after 1 conversion */
    };
    if (i2c_master_transmit(s_ads_dev, buf, 3, 50) != ESP_OK) {
        if (s_ads_drdy_sem) gpio_intr_enable(CONFIG_WELLD_ADS1115_DRDY_GPIO);
        return INT_MIN;
    }

    /* Re-enable after the conversion is started so the ISR only fires for
     * this conversion's DRDY edge. */
    if (s_ads_drdy_sem) {
        gpio_intr_enable(CONFIG_WELLD_ADS1115_DRDY_GPIO);
        /* If the edge arrived while interrupts were masked, the ISR never
         * fired. Check the pin level now; give the semaphore if already
         * asserted. Binary semaphore ignores a redundant give. */
        if (gpio_get_level(CONFIG_WELLD_ADS1115_DRDY_GPIO) == 0) {
            xSemaphoreGive(s_ads_drdy_sem);
        }
    }

    if (ads1115_wait_conversion_done() != ESP_OK) {
        ESP_LOGW(TAG, "ADS1115 conversion timeout");
        return INT_MIN;
    }

    uint8_t ptr = ADS1115_REG_CONVERT;
    uint8_t data[2] = {0};
    if (i2c_master_transmit_receive(s_ads_dev, &ptr, 1, data, 2, 50) != ESP_OK)
        return INT_MIN;

    int16_t raw = (int16_t)(uint16_t)((data[0] << 8) | data[1]);
    /* mv = raw * FSR / 32768 (FSR in mV matches the PGA chosen above) */
    long fsr_mv = (ch == 2) ? 4096L : 2048L;
    return (int)(raw * fsr_mv / 32768);
}

/* Returns the current level offset in cm, loading it from NVS on first call.
 * Falls back to CONFIG_WELLD_SENSOR_OFFSET_CM if no NVS value exists yet. */
int sensor_get_offset_cm(void)
{
    if (s_offset_cm == INT32_MIN) {
        nvs_handle_t h;
        int32_t val = CONFIG_WELLD_SENSOR_OFFSET_CM;
        if (nvs_open(WELLD_NVS_NAMESPACE, NVS_READONLY, &h) == ESP_OK) {
            nvs_get_i32(h, WELLD_NVS_KEY_OFFSET, &val);
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
    /* Skip the NVS write if the value is already cached at this setting.
     * The cache is valid (not INT32_MIN) when sensor_get_offset_cm() has
     * been called at least once this wakeup, which is always the case when
     * sensor_set_offset_cm() is invoked from main.c after an NVS wipe. */
    if (s_offset_cm != INT32_MIN && s_offset_cm == offset_cm) return;
    s_offset_cm = offset_cm;
    nvs_handle_t h;
    if (nvs_open(WELLD_NVS_NAMESPACE, NVS_READWRITE, &h) == ESP_OK) {
        esp_err_t _err = nvs_set_i32(h, WELLD_NVS_KEY_OFFSET, (int32_t)offset_cm);
        if (_err != ESP_OK)
            ESP_LOGW(TAG, "offset write: %s", esp_err_to_name(_err));
        _err = nvs_commit(h);
        if (_err != ESP_OK)
            ESP_LOGW(TAG, "offset commit: %s", esp_err_to_name(_err));
        nvs_close(h);
    }
}

void sensor_offset_cache_reset(void)
{
    s_offset_cm = INT32_MIN;
}

/* Read the water level in metres, applying the NVS-stored offset and
 * optional temperature compensation.
 * Gates the MT3608B 12V boost (VLOOP GPIO) for the duration of the read.
 * Uses ADS1115 AIN0 to measure the shunt voltage across the 4-20 mA loop.
 * Returns -1.0 if the transducer loop current indicates an open circuit.
 * Returns -2.0 if a short-circuit is detected (>21 mA). */
float sensor_read_level(void)
{
    /* Gate VLOOP HIGH to enable the MT3608B boost converter.
     * The 12 V output caps (C20/C22) charge through the Q3 load-disconnect
     * P-FET, so the rail needs longer than the bare MT3608B soft-start
     * (< 5 ms typ) to stabilise. Hold HIGH for 10 ms before the ADC reads
     * the shunt (PCB review 2026-07: raised from 5 ms for Q3 + C20/C22).
     * Constraint from CLAUDE.md: GPIO5 must be HIGH ≥ 10 ms before any read. */
    gpio_set_level(CONFIG_WELLD_VLOOP_GPIO, 1);
    vTaskDelay(pdMS_TO_TICKS(10));  /* MT3608B soft-start + Q3/C20/C22 rail settle */

    int volt_mv;
#if CONFIG_WELLD_ADC_OVERSAMPLE_ENABLED
    volt_mv = ads1115_read_mv_median(0);
#else
    volt_mv = ads1115_read_mv(0);
#endif

    /* Drive VLOOP LOW immediately after read — max ON time is 100 ms */
    gpio_set_level(CONFIG_WELLD_VLOOP_GPIO, 0);

    if (volt_mv == INT_MIN) {
        ESP_LOGE(TAG, "ADS1115 read failed on AIN0 (4-20 mA shunt)");
        return -1.0f;
    }

    int current_ua = (int)(((int64_t)volt_mv * 1000000LL) / CONFIG_WELLD_SENSOR_SHUNT_MILLIOHMS);

    /* Short-circuit detection: >21 mA (2100 mV on 100 Ω shunt) */
    if (current_ua > 21000) {
        ESP_LOGE(TAG, "transducer short-circuit (voltage=%d mV, %d µA > 21 mA)",
                 volt_mv, current_ua);
        return -2.0f;
    }

    float level_m = sensor_level_from_mv(volt_mv);
    if (level_m < 0.0f) {
        ESP_LOGE(TAG, "transducer open loop (voltage=%d mV, %d µA < 3.5 mA)",
                 volt_mv, current_ua);
        return level_m;
    }
    float offset_m = sensor_get_offset_cm() / 100.0f;
    level_m += offset_m;
    if (level_m < 0.0f) level_m = 0.0f;

    if (offset_m != 0.0f)
        ESP_LOGI(TAG, "voltage=%d mV  current=%d µA  level=%.2f m (offset %.0f cm)",
                 volt_mv, current_ua, level_m, offset_m * 100.0f);
    else
        ESP_LOGI(TAG, "voltage=%d mV  current=%d µA  level=%.2f m",
                 volt_mv, current_ua, level_m);
    return level_m;
}

/* Apply temperature compensation to a raw water-level reading.
 * Water density decreases with temperature, so a pressure transducer
 * reads slightly high in warm water and low in cold water.
 * level_m = raw / (1 + alpha * (temp_c - 20.0))
 * Returns the compensated level. */
float sensor_level_temp_compensate(float level_m, float temp_c)
{
#if CONFIG_WELLD_TEMP_COMPENSATION_ENABLED
    float alpha = CONFIG_WELLD_TEMP_COMPENSATION_PPM_PER_C / 1e6f;
    float factor = 1.0f + alpha * (temp_c - 20.0f);
    if (factor <= 0.0f) factor = 1.0f;
    float compensated = level_m / factor;
    ESP_LOGI(TAG, "temp-comp: raw=%.3f m temp=%.1f°C factor=%.5f compensated=%.3f m",
             level_m, temp_c, factor, compensated);
    return compensated;
#else
    (void)temp_c;
    return level_m;
#endif
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
        if (nvs_open(WELLD_NVS_NAMESPACE, NVS_READONLY, &nvs_h) == ESP_OK) {
            has_preferred = nvs_get_u64(nvs_h, WELLD_NVS_KEY_DS18B20, &preferred_rom) == ESP_OK;
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
        if (nvs_open(WELLD_NVS_NAMESPACE, NVS_READWRITE, &nvs_h) == ESP_OK) {
            nvs_set_u64(nvs_h, WELLD_NVS_KEY_DS18B20, selected_rom);
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
    /* Set resolution; default is 12-bit (750 ms). 9-bit = 94 ms, saves battery. */
    ds18b20_set_resolution(ds18b20, (ds18b20_resolution_t)CONFIG_WELLD_DS18B20_RESOLUTION_BITS);
    if (ds18b20_trigger_temperature_conversion_for_all(bus) == ESP_OK) {
        uint32_t conv_ms;
        switch (CONFIG_WELLD_DS18B20_RESOLUTION_BITS) {
            case 9:  conv_ms = 94;  break;
            case 10: conv_ms = 188; break;
            case 11: conv_ms = 375; break;
            default: conv_ms = 750; break;
        }
        vTaskDelay(pdMS_TO_TICKS(conv_ms));
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

/* Read battery voltage via the gated resistor divider on ADS1115 AIN2.
 * Divider is the only voltage measurement path.
 * R7/R8 = 100 kΩ / 100 kΩ (ratio 2.0 on the 1S board; Kconfig-set). Gate
 * BATT_DIV_EN (GPIO15) for
 * 1 ms before reading, then drive LOW to prevent quiescent divider drain.
 * Returns -1.0 if ADS1115 read fails. */
float sensor_read_battery_v(void)
{
    gpio_set_level(CONFIG_WELLD_BATT_DIV_EN_GPIO, 1);
    vTaskDelay(pdMS_TO_TICKS(1));
#if CONFIG_WELLD_ADC_OVERSAMPLE_ENABLED
    int mv = ads1115_read_mv_median(2);
#else
    int mv = ads1115_read_mv(2);
#endif
    gpio_set_level(CONFIG_WELLD_BATT_DIV_EN_GPIO, 0);
    if (mv == INT_MIN) return -1.0f;
    float batt_v = sensor_battery_from_mv(mv, CONFIG_WELLD_BATT_DIVIDER_RATIO);
    ESP_LOGI(TAG, "battery=%.2f V (divider)", batt_v);
    return batt_v;
}

/* Remove the ADS1115 DRDY ISR and delete the I2C master bus before deep sleep.
 *
 * Without this:
 *   - The ADS1115 DRDY GPIO12 ISR remains installed.  If DRDY happens to
 *     glitch during the deep-sleep entry window the ISR fires, waking the
 *     CPU before it has entered sleep.
 *   - The I2C master bus handle (s_i2c_bus) is left open.  On the next
 *     wakeup sensor_i2c_init() calls i2c_new_master_bus() again; ESP-IDF
 *     will return ESP_ERR_INVALID_STATE because port 0 is still claimed,
 *     causing the whole I2C init to fail silently.
 *
 * Call this from every path that leads to esp_deep_sleep(). */
void sensor_pre_sleep_cleanup(void)
{
    /* Remove ADS1115 DRDY ISR so GPIO12 cannot wake us prematurely. */
    if (s_ads_drdy_sem) {
        gpio_isr_handler_remove(CONFIG_WELLD_ADS1115_DRDY_GPIO);
        vSemaphoreDelete(s_ads_drdy_sem);
        s_ads_drdy_sem = NULL;
    }

    /* Delete device handle before deleting the bus. */
    if (s_ads_dev) {
        i2c_master_bus_rm_device(s_ads_dev);
        s_ads_dev = NULL;
    }

    /* Release the I2C master bus so the next wakeup's i2c_new_master_bus()
     * finds port 0 unclaimed. */
    if (s_i2c_bus) {
        i2c_del_master_bus(s_i2c_bus);
        s_i2c_bus = NULL;
    }
}

/* Self-test: exercise every peripheral and log PASS/FAIL.
 * Useful for factory QA and PCB bring-up. */
void sensor_selftest(void)
{
    ESP_LOGI(TAG, "=== SELF-TEST START ===");

    /* I2C bus */
    bool i2c_ok = (s_i2c_bus != NULL);
    ESP_LOGI(TAG, "[I2C bus] %s", i2c_ok ? "PASS" : "FAIL");

    /* ADS1115 loopback: read config register */
    bool ads_ok = false;
    if (s_ads_dev) {
        uint8_t reg = ADS1115_REG_CONFIG;
        uint8_t cfg[2];
        ads_ok = (i2c_master_transmit_receive(s_ads_dev, &reg, 1, cfg, 2, 50) == ESP_OK);
    }
    ESP_LOGI(TAG, "[ADS1115] %s", ads_ok ? "PASS" : "FAIL");

    /* VLOOP GPIO toggle. The pin is normally configured GPIO_MODE_OUTPUT,
     * whose input buffer is disabled — gpio_get_level() would always read 0
     * and the test would fail even on good hardware. Temporarily enable the
     * input buffer for the readback, then restore output-only mode. */
    bool vloop_ok = true;
    gpio_set_direction(CONFIG_WELLD_VLOOP_GPIO, GPIO_MODE_INPUT_OUTPUT);
    gpio_set_level(CONFIG_WELLD_VLOOP_GPIO, 1);
    vTaskDelay(pdMS_TO_TICKS(1));
    if (gpio_get_level(CONFIG_WELLD_VLOOP_GPIO) != 1) vloop_ok = false;
    gpio_set_level(CONFIG_WELLD_VLOOP_GPIO, 0);
    gpio_set_direction(CONFIG_WELLD_VLOOP_GPIO, GPIO_MODE_OUTPUT);
    ESP_LOGI(TAG, "[VLOOP GPIO] %s", vloop_ok ? "PASS" : "FAIL");

    /* DS18B20 presence */
    onewire_bus_handle_t bus = NULL;
    onewire_bus_config_t bus_cfg = { .bus_gpio_num = CONFIG_WELLD_DS18B20_GPIO };
    onewire_bus_rmt_config_t rmt_cfg = { .max_rx_bytes = 10 };
    bool ds_ok = (onewire_new_bus_rmt(&bus_cfg, &rmt_cfg, &bus) == ESP_OK);
    if (ds_ok) {
        onewire_device_iter_handle_t iter = NULL;
        ds_ok = (onewire_new_device_iter(bus, &iter) == ESP_OK);
        if (ds_ok) {
            onewire_device_t device;
            ds_ok = (onewire_device_iter_get_next(iter, &device) == ESP_OK);
            onewire_del_device_iter(iter);
        }
        onewire_bus_del(bus);
    }
    ESP_LOGI(TAG, "[DS18B20] %s", ds_ok ? "PASS" : "ABSENT");

    /* Solar detect GPIO */
    bool solar_ok = true;
    ESP_LOGI(TAG, "[Solar detect GPIO] %s (level=%d)", solar_ok ? "PASS" : "FAIL",
             gpio_get_level(CONFIG_WELLD_SOLAR_DETECT_GPIO));

    ESP_LOGI(TAG, "=== SELF-TEST END ===");
}
