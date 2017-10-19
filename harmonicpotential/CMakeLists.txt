add_subdirectory(cpp)

if(BUILD_TESTING)
    enable_testing()
    add_subdirectory(tests)
endif()
