#include "sensor.h"
#include "driver/i2c_master.h"
#include "driver/gpio.h"
#include "onewire_bus.h"
#include "ds18b20.h"
#include "esp_log.h"
#include "esp_rom_sys.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"
#include "sdkconfig.h"
#include "nvs_flash.h"
#include "nvs.h"
#include "welld_nvs.h"
#include <limits.h>

static const char *TAG = "sensor";

/* Ticks that guarantee AT LEAST `ms` milliseconds when passed to vTaskDelay()
 * or used as a blocking timeout. pdMS_TO_TICKS() rounds down and the first
 * tick of a delay can be almost zero long, so at the default
 * CONFIG_FREERTOS_HZ=100 pdMS_TO_TICKS(1) is 0 (no delay at all) and
 * pdMS_TO_TICKS(10) is 1 tick (anywhere from ~0 to 10 ms). Round up and add
 * one tick so every settle time and timeout below is a real minimum whatever
 * the tick rate. */
static TickType_t ticks_at_least_ms(uint32_t ms)
{
    return (TickType_t)(((uint64_t)ms * configTICK_RATE_HZ + 999U) / 1000U) + 1U;
}

static void delay_at_least_ms(uint32_t ms)
{
    vTaskDelay(ticks_at_least_ms(ms));
}

/* INT32_MIN is used as a sentinel meaning "not yet loaded from NVS".
   Avoids an NVS read on every call after the first wakeup. */
static int s_offset_cm = INT32_MIN;

/* I²C bus and device handles — initialised by sensor_i2c_init(). */
static i2c_master_bus_handle_t  s_i2c_bus = NULL;
static i2c_master_dev_handle_t  s_ads_dev = NULL;

/* Binary semaphore released by the ADS1115 DRDY falling-edge ISR.
 * Created in ads1115_drdy_init(); NULL means DRDY GPIO is not configured. */
static SemaphoreHandle_t s_ads_drdy_sem = NULL;

/* ISR handler: DRDY (GPIO22) fell — conversion complete. */
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
 * The chargers (TP4056, CN3791) are autonomous — no charger-enable GPIO. */
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

/* ADS1115 comparator / DRDY registers */
#define ADS1115_REG_LO_THRESH   0x02
#define ADS1115_REG_HI_THRESH   0x03

/* Configure the ADS1115 ALERT/DRDY pin as a conversion-ready signal and
 * install a falling-edge ISR on GPIO CONFIG_WELLD_ADS1115_DRDY_GPIO.
 *
 * ADS1115 datasheet (SBAS444, "Conversion Ready Pin"): set the MSB of
 * Hi_thresh to 1 and the MSB of Lo_thresh to 0, with COMP_QUE != 11, and
 * ALERT/RDY asserts (low, COMP_POL = 0) at the end of each single-shot
 * conversion. The reset values (Lo_thresh 0x8000, Hi_thresh 0x7FFF) are the
 * opposite — they leave the pin in plain comparator mode with the thresholds
 * at the rails, so it never asserts.
 *
 * The GPIO is open-drain so the internal pull-up must be enabled. */
static esp_err_t ads1115_drdy_init(void)
{
    /* Hi_thresh = 0x8000 — MSB = 1 */
    uint8_t hi_buf[3] = { ADS1115_REG_HI_THRESH, 0x80, 0x00 };
    esp_err_t ret = i2c_master_transmit(s_ads_dev, hi_buf, 3, 50);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "ADS1115 Hi_thresh write failed: %s", esp_err_to_name(ret));
        return ret;
    }

    /* Lo_thresh = 0x0000 — MSB = 0 */
    uint8_t lo_buf[3] = { ADS1115_REG_LO_THRESH, 0x00, 0x00 };
    ret = i2c_master_transmit(s_ads_dev, lo_buf, 3, 50);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "ADS1115 Lo_thresh write failed: %s", esp_err_to_name(ret));
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
 * (GPIO open-drain mode) to release any peripheral holding the bus.
 *
 * The pins must be INPUT_OUTPUT_OD: with plain OUTPUT_OD the input buffer is
 * off and gpio_get_level() always reads 0, so every wakeup "saw" a stuck bus,
 * logged a warning and clocked recovery pulses that could never detect the
 * release. Half-periods are 5 µs (100 kHz standard-mode timing). */
static void i2c_bus_recover(void)
{
    int sda = CONFIG_WELLD_I2C_SDA_GPIO;
    int scl = CONFIG_WELLD_I2C_SCL_GPIO;

    gpio_config_t cfg = {
        .mode         = GPIO_MODE_INPUT_OUTPUT_OD,
        .pull_up_en   = GPIO_PULLUP_ENABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type    = GPIO_INTR_DISABLE,
    };

    cfg.pin_bit_mask = 1ULL << sda;
    gpio_config(&cfg);
    cfg.pin_bit_mask = 1ULL << scl;
    gpio_config(&cfg);

    gpio_set_level(scl, 1);
    gpio_set_level(sda, 1);
    esp_rom_delay_us(10);

    if (gpio_get_level(sda) == 0) {
        ESP_LOGW(TAG, "SDA stuck LOW — performing I2C bus recovery");
        for (int i = 0; i < 9; i++) {
            gpio_set_level(scl, 0);
            esp_rom_delay_us(5);
            gpio_set_level(scl, 1);
            esp_rom_delay_us(5);
            if (gpio_get_level(sda)) {
                ESP_LOGI(TAG, "SDA released after %d clock pulses", i + 1);
                break;
            }
        }
        /* Send STOP condition: SDA LOW → SCL HIGH → SDA HIGH */
        gpio_set_level(sda, 0);
        esp_rom_delay_us(5);
        gpio_set_level(scl, 1);
        esp_rom_delay_us(5);
        gpio_set_level(sda, 1);
        esp_rom_delay_us(5);
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

/* Config register bitfields. The register is written MSB first, so the two
 * bytes are built separately:
 *   MSB (bits 15:8): OS | MUX[2:0] | PGA[2:0] | MODE
 *   LSB (bits 7:0):  DR[2:0] | COMP_MODE | COMP_POL | COMP_LAT | COMP_QUE[1:0] */
#define ADS1115_OS_START        (1U << 7)   /* MSB: start / conversion done */
#define ADS1115_MUX_AIN0        (4U << 4)   /* MSB: AIN0 vs GND */
#define ADS1115_MUX_AIN2        (6U << 4)   /* MSB: AIN2 vs GND */
/* MSB: ±4.096 V for both channels. AIN2: the 1S ÷2 divider reaches 2.1 V at
 * full charge (±2.048 V would clip there). AIN0: 20 mA × 100 Ω = 2.0 V sits at
 * the very top of ±2.048 V, which clips at 20.47 mA and made the >21 mA
 * short-circuit check unreachable. Inputs still may not exceed VDD (3.3 V);
 * the shunt Kconfig range keeps 21 mA well below it. */
#define ADS1115_PGA_4V096       (1U << 1)
#define ADS1115_FSR_MV          4096L
#define ADS1115_MODE_SINGLE     (1U << 0)   /* MSB */
#define ADS1115_DR_860SPS       (7U << 5)   /* LSB: 860 SPS, ~1.16 ms/conversion */
/* LSB: COMP_QUE = 00 (assert after one conversion — anything but 11 keeps
 * ALERT/RDY enabled), COMP_POL = 0 (active-low), COMP_LAT = 0. */
#define ADS1115_COMP_QUE_ONE    (0U << 0)

/* Maximum time to wait for an ADS1115 conversion to complete (ms).
 * At 860 SPS one conversion takes ~1.16 ms; 10 ms gives an 8× safety margin. */
#define ADS1115_CONV_TIMEOUT_MS 10

/* Poll the config register's OS bit (1 = no conversion in progress) until
 * the deadline. Returns ESP_OK, ESP_ERR_TIMEOUT or ESP_ERR_INVALID_RESPONSE. */
static esp_err_t ads1115_poll_os(int64_t deadline_us)
{
    uint8_t reg = ADS1115_REG_CONFIG;
    uint8_t cfg[2];
    for (;;) {
        if (i2c_master_transmit_receive(s_ads_dev, &reg, 1, cfg, 2, 50) != ESP_OK)
            return ESP_ERR_INVALID_RESPONSE;
        if (cfg[0] & ADS1115_OS_START)
            return ESP_OK;
        if (esp_timer_get_time() >= deadline_us)
            return ESP_ERR_TIMEOUT;
        esp_rom_delay_us(200);
    }
}

/* Wait for an ADS1115 single-shot conversion to complete.
 *
 * Primary path (s_ads_drdy_sem != NULL): blocks on the binary semaphore
 * that the DRDY falling-edge ISR releases. The semaphore is drained before
 * every conversion; the OS bit is then confirmed over I2C, so a stray edge
 * (or a token from the previous conversion) can never hand back the previous
 * channel's result.
 *
 * Fallback path (semaphore NULL): poll the OS bit every 200 µs.
 *
 * Both paths use a tick-rate-independent deadline of at least
 * ADS1115_CONV_TIMEOUT_MS. Returns ESP_OK, or ESP_ERR_TIMEOUT /
 * ESP_ERR_INVALID_RESPONSE. */
static esp_err_t ads1115_wait_conversion_done(void)
{
    int64_t deadline_us = esp_timer_get_time() + ADS1115_CONV_TIMEOUT_MS * 1000LL;
    if (s_ads_drdy_sem &&
        xSemaphoreTake(s_ads_drdy_sem, ticks_at_least_ms(ADS1115_CONV_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGW(TAG, "ADS1115 DRDY edge not received within %d ms — polling",
                 ADS1115_CONV_TIMEOUT_MS);
    }
    return ads1115_poll_os(deadline_us);
}

/* Read one ADS1115 channel in single-shot mode.
 * ch: 0 = AIN0/GND (4-20 mA shunt), 2 = AIN2/GND (battery divider); both on
 * the ±4.096 V range (see ADS1115_PGA_4V096). 860 SPS. COMP_QUE = one-shot
 * assert, required for DRDY.
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
    uint8_t buf[3] = {
        ADS1115_REG_CONFIG,
        /* MSB */ ADS1115_OS_START | mux | ADS1115_PGA_4V096 | ADS1115_MODE_SINGLE,
        /* LSB */ ADS1115_DR_860SPS | ADS1115_COMP_QUE_ONE
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
    /* mv = raw * FSR / 32768 (FSR matches ADS1115_PGA_4V096) */
    return (int)(raw * ADS1115_FSR_MV / 32768);
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

float sensor_apply_level_offset(float column_m)
{
    int offset_cm = sensor_get_offset_cm();
    float level_m = sensor_level_with_offset(column_m, offset_cm);
    if (offset_cm != 0) {
        ESP_LOGI(TAG, "level=%.2f m with the %+d cm offset", level_m, offset_cm);
    }
    return level_m;
}

/* Minimum VLOOP on-time before the shunt is sampled: MT3608B soft-start plus
 * the Q3/C20/C22 rail settle. CONFIG_WELLD_VLOOP_SETTLE_MS (>= this) adds the
 * transducer's own start-up time. */
#define VLOOP_RAIL_SETTLE_MS  10
/* AIN0 at or above this during a long warm-up = dead short (see
 * sensor_read_level()). */
#define LOOP_DEAD_SHORT_MV    3000

/* Read the water column above the transducer in metres (no offset, no
 * temperature compensation — see sensor.h for the order).
 * Gates the MT3608B 12V boost (VLOOP GPIO) for the duration of the read.
 * Uses ADS1115 AIN0 to measure the shunt voltage across the 4-20 mA loop.
 * Returns -1.0 if the transducer loop current indicates an open circuit.
 * Returns -2.0 if a short-circuit is detected (>21 mA). */
float sensor_read_level(void)
{
    /* Gate VLOOP HIGH to enable the MT3608B boost converter. The 12 V output
     * caps (C20/C22) charge through the Q3 load-disconnect P-FET, so the rail
     * needs longer than the bare MT3608B soft-start (< 5 ms typ): at least
     * VLOOP_RAIL_SETTLE_MS (PCB review 2026-07: raised from 5 ms). The
     * transducer may need longer still to reach a valid output —
     * CONFIG_WELLD_VLOOP_SETTLE_MS (default = the 10 ms rail minimum). */
    gpio_set_level(CONFIG_WELLD_VLOOP_GPIO, 1);
    delay_at_least_ms(VLOOP_RAIL_SETTLE_MS);
#if CONFIG_WELLD_VLOOP_SETTLE_MS > VLOOP_RAIL_SETTLE_MS
    {
        /* Long transducer warm-up: once the rail is up, check for a dead
         * short before waiting out the rest. VLOOP has no current limit on
         * its way to LOOP+, so a shorted cable holds the boost at its switch
         * limit into the D9 clamp (and draws amps from the cell) for as long
         * as VLOOP stays on. LOOP_DEAD_SHORT_MV pins AIN0 near the top of its
         * range: >= 23 mA even at the 130 ohm maximum shunt, above NAMUR
         * alarm currents a healthy transducer may show while starting. */
        int probe_mv = ads1115_read_mv(0);
        if (probe_mv != INT_MIN && probe_mv >= LOOP_DEAD_SHORT_MV) {
            gpio_set_level(CONFIG_WELLD_VLOOP_GPIO, 0);
            ESP_LOGE(TAG, "transducer short-circuit at warm-up (voltage=%d mV) — loop switched off",
                     probe_mv);
            return -2.0f;
        }
    }
    delay_at_least_ms(CONFIG_WELLD_VLOOP_SETTLE_MS - VLOOP_RAIL_SETTLE_MS);
#endif

    int volt_mv;
#if CONFIG_WELLD_ADC_OVERSAMPLE_ENABLED
    volt_mv = ads1115_read_mv_median(0);
#else
    volt_mv = ads1115_read_mv(0);
#endif

    /* Drive VLOOP LOW immediately after the read: on time is the settle
     * time plus one conversion (or three with oversampling). */
    gpio_set_level(CONFIG_WELLD_VLOOP_GPIO, 0);

    if (volt_mv == INT_MIN) {
        ESP_LOGE(TAG, "ADS1115 read failed on AIN0 (4-20 mA shunt)");
        return -1.0f;
    }

    int current_ua = (int)(((int64_t)volt_mv * 1000000LL) / CONFIG_WELLD_SENSOR_SHUNT_MILLIOHMS);

    /* Short-circuit detection: >21 mA (2100 mV on 100 Ω shunt — measurable
     * now that AIN0 uses the ±4.096 V range) */
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
    /* The water column only: the offset is applied by
     * sensor_apply_level_offset() after the density correction. */
    ESP_LOGI(TAG, "voltage=%d mV  current=%d µA  level=%.2f m",
             volt_mv, current_ua, level_m);
    return level_m;
}

/* Apply temperature compensation to a raw water-level reading.
 * The transducer measures pressure; its metre scale assumes water at
 * CONFIG_WELLD_TEMP_COMPENSATION_REF_C (4 °C = the conventional metre of
 * water, 1000 kg/m3). Water at another temperature has a different density,
 * so the level is multiplied by rho(ref)/rho(T) — see
 * sensor_temp_level_factor() in sensor_pure.c (host-tested against tabulated
 * densities). Before 1.2.1 this divided by (1 + 207 ppm * (T - 20)): wrong
 * sign and a 20 °C reference. Returns the compensated level. */
float sensor_level_temp_compensate(float level_m, float temp_c)
{
#if CONFIG_WELLD_TEMP_COMPENSATION_ENABLED
    float factor = sensor_temp_level_factor(temp_c,
                                            CONFIG_WELLD_TEMP_COMPENSATION_REF_C);
    float compensated = level_m * factor;
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
    /* ds18b20_resolution_t is an index (DS18B20_RESOLUTION_9B = 0 … _12B = 3),
     * not a bit count: passing the raw Kconfig value (11) indexed past the
     * driver's 4-entry resolution table. */
    _Static_assert(CONFIG_WELLD_DS18B20_RESOLUTION_BITS >= 9 &&
                   CONFIG_WELLD_DS18B20_RESOLUTION_BITS <= 12,
                   "DS18B20 resolution must be 9..12 bits");
    if (ds18b20_set_resolution(ds18b20, (ds18b20_resolution_t)(DS18B20_RESOLUTION_9B +
                               (CONFIG_WELLD_DS18B20_RESOLUTION_BITS - 9))) != ESP_OK) {
        ESP_LOGW(TAG, "DS18B20 resolution write failed — converting at 12-bit timing");
    }
    /* The per-device trigger blocks for the conversion time of the resolution
     * the driver last set successfully (100/200/400/800 ms for 9–12 bit), so
     * no extra delay is needed here. (The _for_all variant always blocks a
     * fixed 800 ms whatever the resolution — with the old extra wait on top
     * that was ~1.2 s of awake time per wakeup at 11-bit.) */
    if (ds18b20_trigger_temperature_conversion(ds18b20) == ESP_OK &&
        ds18b20_get_temperature(ds18b20, &temp) != ESP_OK) {
        temp = -127.0f;   /* CRC error or the 85 °C power-on value */
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
    /* ≥1 ms for Q2/Q5 to switch and the divider node (τ = 50 kΩ × C8 1 nF)
     * to settle. Busy-wait: vTaskDelay(pdMS_TO_TICKS(1)) is no delay at all
     * at the default 100 Hz tick, which started the conversion on a still-
     * rising node and read the battery low. */
    esp_rom_delay_us(1000);
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
 *   - The ADS1115 DRDY GPIO22 ISR remains installed.  If DRDY happens to
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
    /* Remove ADS1115 DRDY ISR so GPIO22 cannot wake us prematurely. */
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
    esp_rom_delay_us(100);
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
