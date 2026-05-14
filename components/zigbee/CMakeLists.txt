idf_component_register(
    SRCS "zigbee.c"
    INCLUDE_DIRS "include"
    REQUIRES freertos log app_update esp_system
)

# Convert PROJECT_VER "MAJOR.MINOR.PATCH" to OTA uint32 (0x00MMmmPP)
string(REPLACE "." ";" _ver_parts "${PROJECT_VER}")
list(GET _ver_parts 0 _ver_major)
list(GET _ver_parts 1 _ver_minor)
list(GET _ver_parts 2 _ver_patch)
math(EXPR _ota_ver "${_ver_major} * 16777216 + ${_ver_minor} * 65536 + ${_ver_patch}")
target_compile_definitions(${COMPONENT_LIB} PRIVATE OTA_FW_VERSION=${_ota_ver})
