idf_component_register(
    SRCS "zigbee.c"
    INCLUDE_DIRS "include"
    REQUIRES freertos log app_update nvs
)
