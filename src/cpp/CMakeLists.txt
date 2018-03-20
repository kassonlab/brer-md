add_library(harmonicpotential SHARED
            harmonicpotential.h
            harmonicpotential.cpp)

target_include_directories(harmonicpotential PUBLIC
                           $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
                           $<INSTALL_INTERFACE:include>
                           )
# RPATH management
# don't skip the full RPATH for the build tree
set_target_properties(harmonicpotential PROPERTIES SKIP_BUILD_RPATH FALSE)

# (but later on when installing)
# If building with setuptools, CMake will not be performing the install
set_target_properties(harmonicpotential PROPERTIES BUILD_WITH_INSTALL_RPATH TRUE)

target_link_libraries(harmonicpotential PRIVATE Gromacs::gmxapi)


add_library(ensemblepotential SHARED
            ensemblepotential.h
            ensemblepotential.cpp)

target_include_directories(ensemblepotential PUBLIC
                           $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
                           $<INSTALL_INTERFACE:include>
                           )
# RPATH management
# don't skip the full RPATH for the build tree
set_target_properties(ensemblepotential PROPERTIES SKIP_BUILD_RPATH FALSE)

# (but later on when installing)
# If building with setuptools, CMake will not be performing the install
set_target_properties(ensemblepotential PROPERTIES BUILD_WITH_INSTALL_RPATH TRUE)

target_link_libraries(ensemblepotential PRIVATE Gromacs::gmxapi)
