cmake_minimum_required(VERSION 3.25)

# Resolve the vcpkg toolchain before project() when the caller named none.
if(NOT DEFINED CMAKE_TOOLCHAIN_FILE)
    if(DEFINED ENV{VCPKG_ROOT})
        set(sushihub_gui_vcpkg_root "$ENV{VCPKG_ROOT}")
    else()
        set(sushihub_gui_vcpkg_root "${CMAKE_CURRENT_LIST_DIR}/../../dependencies/vcpkg")
    endif()
    if(EXISTS "${sushihub_gui_vcpkg_root}/scripts/buildsystems/vcpkg.cmake")
        set(CMAKE_TOOLCHAIN_FILE "${sushihub_gui_vcpkg_root}/scripts/buildsystems/vcpkg.cmake"
            CACHE STRING "vcpkg toolchain")
    endif()
endif()

project(sushihub_gui VERSION 0.1.0 LANGUAGES CXX)

option(SUSHIHUB_GUI_BUILD_TESTS "Build the GoogleTest suites." ON)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(sushihub_gui_warnings INTERFACE)
if(MSVC)
    target_compile_options(sushihub_gui_warnings INTERFACE /W4 /permissive-)
else()
    target_compile_options(sushihub_gui_warnings INTERFACE -Wall -Wextra -Wpedantic)
endif()

add_subdirectory(src)

if(SUSHIHUB_GUI_BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()
