cmake_minimum_required(VERSION 3.16)
set(PROJECT_VER "1.2.0")

# Layer the gitignored per-machine overrides (sdkconfig.defaults.local — e.g.
# secure-boot signing on the key-holding machine) on top of the committed
# defaults. ESP-IDF reads only sdkconfig.defaults unless SDKCONFIG_DEFAULTS
# says otherwise, so without this the .local file was silently ignored. An
# explicit -DSDKCONFIG_DEFAULTS / environment value (CI variant builds) wins.
# Defaults only seed a NEW sdkconfig: after editing the .local file,
# regenerate with `idf.py set-target esp32c6` (or delete sdkconfig).
if(NOT DEFINED SDKCONFIG_DEFAULTS AND NOT DEFINED ENV{SDKCONFIG_DEFAULTS})
    set(SDKCONFIG_DEFAULTS "sdkconfig.defaults")
    if(EXISTS "${CMAKE_CURRENT_LIST_DIR}/sdkconfig.defaults.local")
        list(APPEND SDKCONFIG_DEFAULTS "sdkconfig.defaults.local")
    endif()
endif()

# WellD is built and tested against ESP-IDF v6.0.1. Newer/older versions
# may compile but the managed-component pins (esp-zigbee-lib 2.0.1,
# onewire_bus 1.1.1, ds18b20 0.3.1) were chosen against this IDF release.
set(WELLD_REQUIRED_IDF_VERSION "6.0.1")

include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(welld)

set(_actual_idf_version "${IDF_VERSION_MAJOR}.${IDF_VERSION_MINOR}.${IDF_VERSION_PATCH}")
if(NOT "${_actual_idf_version}" STREQUAL "${WELLD_REQUIRED_IDF_VERSION}")
    message(WARNING
        "WellD is pinned to ESP-IDF v${WELLD_REQUIRED_IDF_VERSION}; "
        "you are building with v${_actual_idf_version}. "
        "If you hit API errors in zigbee.c or sensor.c, switch IDF versions.")
endif()
