# Defines targets for the C++ restraints implemented here. These CMake targets are used by the
# Python module target defined in ../pythonmodule/CMakeLists.txt

add_library(sessionresources OBJECT sessionresources.cpp)
set_target_properties(sessionresources PROPERTIES POSITION_INDEPENDENT_CODE ON)
target_link_libraries(sessionresources PUBLIC Gromacs::libgromacs Gromacs::gmxapi)

# Create a static library (archive) target for a simple restraint.
add_library(brer_linearpotential STATIC
            linearpotential.cpp
            sessionresources.cpp)
set_target_properties(brer_linearpotential PROPERTIES POSITION_INDEPENDENT_CODE ON)

target_include_directories(brer_linearpotential PUBLIC
                           $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
                           )
# RPATH management
# don't skip the full RPATH for the build tree
set_target_properties(brer_linearpotential PROPERTIES SKIP_BUILD_RPATH FALSE)
# If building with setuptools, CMake will not be performing the install
set_target_properties(brer_linearpotential PROPERTIES BUILD_WITH_INSTALL_RPATH TRUE)

target_link_libraries(brer_linearpotential PUBLIC Gromacs::libgromacs Gromacs::gmxapi sessionresources)

# Create a static library (archive) target for another simple.
add_library(brer_linearstoppotential STATIC
            linearstoppotential.cpp
            sessionresources.cpp)
set_target_properties(brer_linearstoppotential PROPERTIES POSITION_INDEPENDENT_CODE ON)

target_include_directories(brer_linearstoppotential PUBLIC
                           $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
                           )
# RPATH management
# don't skip the full RPATH for the build tree
set_target_properties(brer_linearstoppotential PROPERTIES SKIP_BUILD_RPATH FALSE)
# If building with setuptools, CMake will not be performing the install
set_target_properties(brer_linearstoppotential PROPERTIES BUILD_WITH_INSTALL_RPATH TRUE)

target_link_libraries(brer_linearstoppotential PUBLIC Gromacs::libgromacs Gromacs::gmxapi sessionresources)

# Create a static library (archive) target for BRER.
add_library(brer_brerpotential STATIC
            brerpotential.cpp
            sessionresources.cpp)
set_target_properties(brer_brerpotential PROPERTIES POSITION_INDEPENDENT_CODE ON)

target_include_directories(brer_brerpotential PUBLIC
                           $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
                           )
# RPATH management
# don't skip the full RPATH for the build tree
set_target_properties(brer_brerpotential PROPERTIES SKIP_BUILD_RPATH FALSE)
# If building with setuptools, CMake will not be performing the install
set_target_properties(brer_brerpotential PROPERTIES BUILD_WITH_INSTALL_RPATH TRUE)

target_link_libraries(brer_brerpotential PUBLIC Gromacs::libgromacs Gromacs::gmxapi sessionresources)
