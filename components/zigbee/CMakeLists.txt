idf_component_register(
    SRCS "zigbee.c"
    INCLUDE_DIRS "include"
    REQUIRES espressif__esp_zigbee_lib freertos esp_log app_update nvs
)
