set(SOURCE_FILES
    harmonicpotential.h
    harmonicpotential.cpp)

add_library(harmonicpotential SHARED ${SOURCE_FILES})

target_include_directories(harmonicpotential PUBLIC
                           $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
                           $<INSTALL_INTERFACE:include>
                           )
set_target_properties(harmonicpotential PROPERTIES SKIP_BUILD_RPATH FALSE)

target_link_libraries(harmonicpotential PRIVATE Gromacs::gmxapi)
