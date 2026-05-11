idf_component_register(
    SRCS "zigbee.c"
    INCLUDE_DIRS "include"
    REQUIRES espressif__esp-zigbee-lib espressif__esp-zboss-lib freertos esp_log app_update nvs
)
