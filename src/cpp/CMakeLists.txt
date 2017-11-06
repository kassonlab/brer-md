set(SOURCE_FILES
    harmonicpotential.h
    harmonicpotential.cpp)

add_library(harmonicpotential SHARED ${SOURCE_FILES})

target_include_directories(harmonicpotential PUBLIC
                           $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
                           $<INSTALL_INTERFACE:include>
                           )
target_link_libraries(harmonicpotential libgromacs)
