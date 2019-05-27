# Defines targets for the C++ restraints implemented here. These CMake targets are used by the
# unit tests and by the Python module target defined in ../pythonmodule/CMakeLists.txt

# Create a shared object library for a simple restraint.
add_library(linearpotential STATIC
            linearpotential.h
            linearpotential.cpp
            sessionresources.cpp)
set_target_properties(linearpotential PROPERTIES POSITION_INDEPENDENT_CODE ON)

target_include_directories(linearpotential PUBLIC
                           $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
                           $<INSTALL_INTERFACE:include>
                           )
# RPATH management
# don't skip the full RPATH for the build tree
set_target_properties(linearpotential PROPERTIES SKIP_BUILD_RPATH FALSE)

# (but later on when installing)
# If building with setuptools, CMake will not be performing the install
set_target_properties(linearpotential PROPERTIES BUILD_WITH_INSTALL_RPATH TRUE)

target_link_libraries(linearpotential PRIVATE Gromacs::gmxapi)

# Create a shared object library for a simple restraint.
add_library(linearstoppotential STATIC
            linearstoppotential.h
            linearstoppotential.cpp
            sessionresources.cpp)
set_target_properties(linearstoppotential PROPERTIES POSITION_INDEPENDENT_CODE ON)

target_include_directories(linearstoppotential PUBLIC
                           $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
                           $<INSTALL_INTERFACE:include>
                           )
# RPATH management
# don't skip the full RPATH for the build tree
set_target_properties(linearstoppotential PROPERTIES SKIP_BUILD_RPATH FALSE)

# (but later on when installing)
# If building with setuptools, CMake will not be performing the install
set_target_properties(linearstoppotential PROPERTIES BUILD_WITH_INSTALL_RPATH TRUE)

target_link_libraries(linearstoppotential PRIVATE Gromacs::gmxapi)
