cmake_minimum_required(VERSION 3.16)
set(PROJECT_VER "1.1.1")

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
