cmake_minimum_required(VERSION 3.18.1)
project("tiggo_navigator" C)

# C стандарт (как в TurboDog, не C++)
set(CMAKE_C_STANDARD 99)
set(CMAKE_C_STANDARD_REQUIRED ON)

# Настройки компиляции (C, не C++)
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Wall -Wextra -O3 -ffast-math")
set(CMAKE_C_FLAGS_DEBUG "${CMAKE_C_FLAGS_DEBUG} -g -O0")

# Директории исходников
set(NATIVE_ROOT ${CMAKE_CURRENT_SOURCE_DIR}/native)
set(CORE_DIR ${NATIVE_ROOT}/core)
set(RENDER_DIR ${NATIVE_ROOT}/render)
set(ASYNC_DIR ${NATIVE_ROOT}/async)
set(DATA_DIR ${NATIVE_ROOT}/data)
set(UTILS_DIR ${NATIVE_ROOT}/utils)
set(JNI_DIR ${NATIVE_ROOT}/jni)

# Исходники
set(CORE_SOURCES
    ${CORE_DIR}/tiggo_engine.c
    ${CORE_DIR}/route_calculator.c
    ${CORE_DIR}/gps_processor.c
    ${CORE_DIR}/navigation_state.c
)

set(RENDER_SOURCES
    ${RENDER_DIR}/render_gl.c
    ${RENDER_DIR}/map_renderer.c
    ${RENDER_DIR}/route_renderer.c
    ${RENDER_DIR}/ui_renderer.c
)

set(ASYNC_SOURCES
    ${ASYNC_DIR}/task_queue.c
    ${ASYNC_DIR}/thread_pool.c
    ${ASYNC_DIR}/async_loader.c
)

set(DATA_SOURCES
    ${DATA_DIR}/yandex_bridge.c
    ${DATA_DIR}/data_converter.c
    ${DATA_DIR}/cache_manager.c
)

set(UTILS_SOURCES
    ${UTILS_DIR}/math_utils.c
    ${UTILS_DIR}/geometry_utils.c
    ${UTILS_DIR}/log_utils.c
)

set(JNI_SOURCES
    ${JNI_DIR}/jni_tiggo_bridge.c
    ${JNI_DIR}/jni_renderer.c
    ${JNI_DIR}/jni_utils.c
)

# Заголовки
include_directories(
    ${NATIVE_ROOT}
    ${CORE_DIR}
    ${RENDER_DIR}
    ${ASYNC_DIR}
    ${DATA_DIR}
    ${UTILS_DIR}
    ${JNI_DIR}
)

# Библиотеки
find_library(log-lib log)
find_library(android-lib android)
find_library(EGL-lib EGL)
find_library(GLESv3-lib GLESv3)

# Создание нативной библиотеки
add_library(tiggo_navigator SHARED
    ${CORE_SOURCES}
    ${RENDER_SOURCES}
    ${ASYNC_SOURCES}
    ${DATA_SOURCES}
    ${UTILS_SOURCES}
    ${JNI_SOURCES}
)

# Линковка
target_link_libraries(tiggo_navigator
    ${log-lib}
    ${android-lib}
    ${EGL-lib}
    ${GLESv3-lib}
)

