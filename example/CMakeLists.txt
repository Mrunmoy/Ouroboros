add_executable(basic_usage basic_usage.cpp)
target_link_libraries(basic_usage PRIVATE ouroboros)

add_executable(concurrent_spsc concurrent_spsc.cpp)
target_link_libraries(concurrent_spsc PRIVATE ouroboros pthread)
