cmake_minimum_required(VERSION 3.14)

# -------------------------
# size harness executable
# -------------------------
add_executable(ouroboros_size
    size/RingBufferSize.cpp
)

target_link_libraries(ouroboros_size
    PRIVATE
        ouroboros
)

target_compile_features(ouroboros_size PRIVATE cxx_std_17)

# Use size-optimized build flags for realistic footprint measurement
if(MSVC)
    target_compile_options(ouroboros_size PRIVATE /O1)
else()
    target_compile_options(ouroboros_size PRIVATE
        -Os
        -ffunction-sections
        -fdata-sections
    )
    target_link_options(ouroboros_size PRIVATE
        -Wl,--gc-sections
        -Wl,-Map=${CMAKE_CURRENT_BINARY_DIR}/ouroboros_size.map
    )
endif()

# ---- size report (code + ram segments) ----
find_program(SIZE_TOOL size)

if(SIZE_TOOL)
    add_custom_command(
        OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/size_report.txt
        COMMAND ${SIZE_TOOL} $<TARGET_FILE:ouroboros_size> > ${CMAKE_CURRENT_BINARY_DIR}/size_report.txt
        DEPENDS ouroboros_size
        VERBATIM
    )

    add_custom_target(ouroboros_size_report
        DEPENDS ${CMAKE_CURRENT_BINARY_DIR}/size_report.txt
    )
else()
    message(STATUS "size tool not found; ouroboros_size_report target will not be available")
endif()

# -------------------------
# google benchmark (vendor)
# -------------------------
set(BENCHMARK_ENABLE_TESTING OFF CACHE BOOL "" FORCE)
set(BENCHMARK_ENABLE_GTEST_TESTS OFF CACHE BOOL "" FORCE)
set(BENCHMARK_DOWNLOAD_DEPENDENCIES OFF CACHE BOOL "" FORCE)

add_subdirectory(vendor/benchmark)

# -------------------------
# perf benchmark executable
# -------------------------
add_executable(ouroboros_bench
    perf/RingBufferBench.cpp
)

target_link_libraries(ouroboros_bench
    PRIVATE
        ouroboros
        benchmark
        benchmark_main
)

target_compile_features(ouroboros_bench PRIVATE cxx_std_17)

if(NOT MSVC)
    target_compile_options(ouroboros_bench PRIVATE -O3)
endif()