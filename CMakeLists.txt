cmake_minimum_required(VERSION 3.16)
set(PROJECT_VER "1.0.0")

# WellD is built and tested against ESP-IDF v5.3.5. Newer/older versions
# may compile but the managed-component pins (esp-zigbee-lib 1.6.8,
# esp-zboss-lib 1.6.4) were chosen against this IDF release.
set(WELLD_REQUIRED_IDF_VERSION "5.3.5")

include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(welld)

set(_actual_idf_version "${IDF_VERSION_MAJOR}.${IDF_VERSION_MINOR}.${IDF_VERSION_PATCH}")
if(NOT "${_actual_idf_version}" STREQUAL "${WELLD_REQUIRED_IDF_VERSION}")
    message(WARNING
        "WellD is pinned to ESP-IDF v${WELLD_REQUIRED_IDF_VERSION}; "
        "you are building with v${_actual_idf_version}. "
        "If you hit API errors in zigbee.c or sensor.c, switch IDF versions.")
endif()
