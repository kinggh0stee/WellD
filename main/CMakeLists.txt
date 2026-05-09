idf_component_register(
    SRCS "main.c" "wifi.c" "mqtt_pub.c"
    INCLUDE_DIRS "."
    REQUIRES sensor nvs_flash esp_wifi mqtt esp_event esp_netif
)
