idf_component_register(
    SRCS "sensor.c" "sensor_pure.c"
    INCLUDE_DIRS "include"
    REQUIRES esp_adc espressif__onewire_bus espressif__ds18b20 nvs_flash
)
