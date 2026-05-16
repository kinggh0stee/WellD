idf_component_register(
    SRCS "main.c"
    INCLUDE_DIRS "."
    REQUIRES sensor zigbee welld_core nvs_flash esp_timer
)
