cmake_minimum_required(VERSION 3.16)
project(welld_host_tests C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

# Fail fast on warnings — these are tests, they have no reason to be sloppy.
add_compile_options(-Wall -Wextra -Wpedantic -Werror)

include(FetchContent)
FetchContent_Declare(
    Unity
    GIT_REPOSITORY https://github.com/ThrowTheSwitch/Unity.git
    GIT_TAG        v2.6.0
)
FetchContent_MakeAvailable(Unity)

set(REPO_ROOT ${CMAKE_CURRENT_SOURCE_DIR}/../..)

# Each executable below reuses the matching on-device test source as its
# single source of truth. The -DHOST_BUILD compile flag swaps app_main()
# for main() inside that file and skips the on-device-only test cases
# (e.g. the sensor NVS round-trip).

# ── test_welld_core ─────────────────────────────────────────────────────────
add_executable(test_welld_core
    ${REPO_ROOT}/test/welld_core/main/test_welld_core.c
    ${REPO_ROOT}/components/welld_core/welld_core.c
)
target_include_directories(test_welld_core PRIVATE
    ${REPO_ROOT}/components/welld_core/include
)
target_compile_definitions(test_welld_core PRIVATE HOST_BUILD)
target_link_libraries(test_welld_core PRIVATE unity)

# ── test_sensor_pure ────────────────────────────────────────────────────────
# stub_sdkconfig/ provides a sdkconfig.h with the Kconfig defaults
# (CONFIG_WELLD_SENSOR_SHUNT_MILLIOHMS, CONFIG_WELLD_SENSOR_MAX_DEPTH_CM).
add_executable(test_sensor_pure
    ${REPO_ROOT}/test/sensor/main/test_sensor.c
    ${REPO_ROOT}/components/sensor/sensor_pure.c
)
target_include_directories(test_sensor_pure PRIVATE
    ${REPO_ROOT}/components/sensor/include
    ${CMAKE_CURRENT_SOURCE_DIR}/stub_sdkconfig
)
target_compile_definitions(test_sensor_pure PRIVATE HOST_BUILD)
target_link_libraries(test_sensor_pure PRIVATE unity)

enable_testing()
add_test(NAME welld_core   COMMAND test_welld_core)
add_test(NAME sensor_pure  COMMAND test_sensor_pure)
