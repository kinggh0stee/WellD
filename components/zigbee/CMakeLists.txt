idf_component_register(
    SRCS "zigbee.c"
    INCLUDE_DIRS "include"
    REQUIRES esp_zigbee_core freertos esp_log
)
