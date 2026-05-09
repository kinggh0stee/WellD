idf_component_register(
    SRCS "main.c" "wifi.c" "mqtt_pub.c"
    INCLUDE_DIRS "."
    REQUIRES sensor zigbee nvs_flash esp_wifi espressif__mqtt esp_event esp_netif
)
