idf_component_register(
    SRCS "zigbee.c"
    INCLUDE_DIRS "include"
    REQUIRES freertos log app_update esp_system welld_core esp_timer
)

# Convert PROJECT_VER "MAJOR.MINOR.PATCH" to OTA uint32 (0xMMmmPP00).
# Fail loudly on a malformed PROJECT_VER: silently shipping
# OTA_FW_VERSION=0 would defeat the OTA upgrade-gate check on the device.
if(NOT PROJECT_VER MATCHES "^[0-9]+\\.[0-9]+\\.[0-9]+$")
    message(FATAL_ERROR
        "zigbee component requires PROJECT_VER to be MAJOR.MINOR.PATCH "
        "(got '${PROJECT_VER}'). Set it in the root CMakeLists.txt.")
endif()
string(REPLACE "." ";" _ver_parts "${PROJECT_VER}")
list(GET _ver_parts 0 _ver_major)
list(GET _ver_parts 1 _ver_minor)
list(GET _ver_parts 2 _ver_patch)
# 0xMMmmPP00: major << 24 | minor << 16 | patch << 8. Must match the
# --file-version the CI workflow passes to ota_image_create.py — a mismatch
# makes the device see an identically-versioned image as an "upgrade".
math(EXPR _ota_ver "${_ver_major} * 16777216 + ${_ver_minor} * 65536 + ${_ver_patch} * 256")
target_compile_definitions(${COMPONENT_LIB} PRIVATE OTA_FW_VERSION=${_ota_ver})
