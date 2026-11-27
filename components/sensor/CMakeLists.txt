idf_component_register(
    SRCS "sensor.c" "sensor_pure.c"
    INCLUDE_DIRS "include"
    REQUIRES espressif__onewire_bus espressif__ds18b20 nvs_flash esp_driver_i2c esp_driver_gpio driver esp_timer welld_core
)
