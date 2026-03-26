cmake_minimum_required(VERSION 3.14)

project(ouroboros
    LANGUAGES CXX
    DESCRIPTION "Lock-free SPSC ring buffer (header-only, cache-friendly)"
)

# ── Header-only library ─────────────────────────────────────────────
add_library(ouroboros INTERFACE)
target_include_directories(ouroboros INTERFACE
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/inc>
    $<INSTALL_INTERFACE:include>
)
target_compile_features(ouroboros INTERFACE cxx_std_17)

# ── Tests and examples (only when building standalone) ───────────────
if(CMAKE_SOURCE_DIR STREQUAL CMAKE_CURRENT_SOURCE_DIR)
    enable_testing()
    add_subdirectory(test)

    option(OUROBOROS_BUILD_EXAMPLES "Build examples" OFF)
    if(OUROBOROS_BUILD_EXAMPLES)
        add_subdirectory(example)
    endif()

    option(OUROBOROS_BUILD_BENCHMARKS "Build benchmarks" OFF)
    if(OUROBOROS_BUILD_BENCHMARKS)
        add_subdirectory(bench)
    endif()

    option(OUROBOROS_BUILD_FUZZ "Build fuzz tests" OFF)
    if(OUROBOROS_BUILD_FUZZ)
        add_subdirectory(test/fuzz)
    endif()
endif()