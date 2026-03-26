# ── Fuzz targets (Clang + libFuzzer only) ────────────────────────────

if(NOT CMAKE_CXX_COMPILER_ID STREQUAL "Clang")
    message(STATUS "ouroboros: fuzz targets require Clang, skipping")
    return()
endif()

set(FUZZ_FLAGS "-fsanitize=fuzzer,address")

function(add_fuzz_target name source)
    add_executable(${name} ${source})
    target_link_libraries(${name} PRIVATE ouroboros)
    target_compile_options(${name} PRIVATE ${FUZZ_FLAGS})
    target_link_options(${name} PRIVATE ${FUZZ_FLAGS})
endfunction()

add_fuzz_target(fuzz_spsc FuzzSpsc.cpp)
add_fuzz_target(fuzz_mpsc FuzzMpsc.cpp)
add_fuzz_target(fuzz_spmc FuzzSpmc.cpp)
