cmake_minimum_required(VERSION 3.18.1)
project("tiggo_navigator" C CXX)

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
set(DATA_DIR ${NATIVE_ROOT}/data)
set(JNI_DIR ${NATIVE_ROOT}/jni)

# Исходники (только существующие файлы)
set(CORE_SOURCES
    ${CORE_DIR}/tiggo_engine.c
)

set(RENDER_SOURCES
    ${RENDER_DIR}/render_gl.c
    ${RENDER_DIR}/map_renderer.c
    ${RENDER_DIR}/route_renderer.c
    ${RENDER_DIR}/ui_renderer.c
    ${RENDER_DIR}/font_renderer.c
    ${RENDER_DIR}/shader_utils.c
)

set(DATA_SOURCES
    ${DATA_DIR}/tile_loader.c
)

set(JNI_SOURCES
    ${JNI_DIR}/jni_tiggo_bridge.c
    ${JNI_DIR}/jni_tile_loader.c
    ${JNI_DIR}/jni_navigation_ui.c
    # ${JNI_DIR}/jni_navigator.cpp  # Временно отключен - требует дополнительные заголовки
)

# Заголовки
include_directories(
    ${NATIVE_ROOT}
    ${CORE_DIR}
    ${RENDER_DIR}
    ${DATA_DIR}
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
    ${DATA_SOURCES}
    ${JNI_SOURCES}
)

# Линковка
target_link_libraries(tiggo_navigator
    ${log-lib}
    ${android-lib}
    ${EGL-lib}
    ${GLESv3-lib}
)

