idf_component_register(
    SRCS "zigbee.c"
    INCLUDE_DIRS "include"
    REQUIRES freertos log app_update esp_system welld_core
)

# Convert PROJECT_VER "MAJOR.MINOR.PATCH" to OTA uint32 (0x00MMmmPP).
# Test projects that don't set PROJECT_VER get a git-derived hash like
# "822306c" — defaulting missing parts to 0 keeps that case from breaking
# component configuration (the test build doesn't actually link zigbee.c).
string(REPLACE "." ";" _ver_parts "${PROJECT_VER}")
list(LENGTH _ver_parts _ver_count)
if(_ver_count GREATER 0)
    list(GET _ver_parts 0 _ver_major)
endif()
if(_ver_count GREATER 1)
    list(GET _ver_parts 1 _ver_minor)
else()
    set(_ver_minor 0)
endif()
if(_ver_count GREATER 2)
    list(GET _ver_parts 2 _ver_patch)
else()
    set(_ver_patch 0)
endif()
if(NOT _ver_major MATCHES "^[0-9]+$")
    set(_ver_major 0)
endif()
math(EXPR _ota_ver "${_ver_major} * 16777216 + ${_ver_minor} * 65536 + ${_ver_patch}")
target_compile_definitions(${COMPONENT_LIB} PRIVATE OTA_FW_VERSION=${_ota_ver})
