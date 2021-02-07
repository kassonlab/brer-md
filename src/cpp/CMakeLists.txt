# Defines targets for the C++ restraints implemented here. These CMake targets are used by the
# unit tests and by the Python module target defined in ../pythonmodule/CMakeLists.txt

# Create a static library (archive) target for a simple restraint.
add_library(gmxapi_extension_linearpotential STATIC
            linearpotential.h
            linearpotential.cpp
            sessionresources.cpp)
set_target_properties(gmxapi_extension_linearpotential PROPERTIES POSITION_INDEPENDENT_CODE ON)

target_include_directories(gmxapi_extension_linearpotential PUBLIC
                           $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
                           $<INSTALL_INTERFACE:include>
                           )
# RPATH management
# don't skip the full RPATH for the build tree
set_target_properties(gmxapi_extension_linearpotential PROPERTIES SKIP_BUILD_RPATH FALSE)

# (but later on when installing)
# If building with setuptools, CMake will not be performing the install
set_target_properties(gmxapi_extension_linearpotential PROPERTIES BUILD_WITH_INSTALL_RPATH TRUE)

target_link_libraries(gmxapi_extension_linearpotential PRIVATE Gromacs::gmxapi)

# Create a static library (archive) target for another simple.
add_library(gmxapi_extension_linearstoppotential STATIC
            linearstoppotential.h
            linearstoppotential.cpp
            sessionresources.cpp)
set_target_properties(gmxapi_extension_linearstoppotential PROPERTIES POSITION_INDEPENDENT_CODE ON)

target_include_directories(gmxapi_extension_linearstoppotential PUBLIC
                           $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
                           $<INSTALL_INTERFACE:include>
                           )
# RPATH management
# don't skip the full RPATH for the build tree
set_target_properties(gmxapi_extension_linearstoppotential PROPERTIES SKIP_BUILD_RPATH FALSE)

# (but later on when installing)
# If building with setuptools, CMake will not be performing the install
set_target_properties(gmxapi_extension_linearstoppotential PROPERTIES BUILD_WITH_INSTALL_RPATH TRUE)

target_link_libraries(gmxapi_extension_linearstoppotential PRIVATE Gromacs::gmxapi)

# Create a static library (archive) target for BRER.
add_library(gmxapi_extension_brerpotential STATIC
            brerpotential.h
            brerpotential.cpp
            sessionresources.cpp)
set_target_properties(gmxapi_extension_brerpotential PROPERTIES POSITION_INDEPENDENT_CODE ON)

target_include_directories(gmxapi_extension_brerpotential PUBLIC
                           $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
                           $<INSTALL_INTERFACE:include>
                           )
# RPATH management
# don't skip the full RPATH for the build tree
set_target_properties(gmxapi_extension_brerpotential PROPERTIES SKIP_BUILD_RPATH FALSE)

# (but later on when installing)
# If building with setuptools, CMake will not be performing the install
set_target_properties(gmxapi_extension_brerpotential PROPERTIES BUILD_WITH_INSTALL_RPATH TRUE)

target_link_libraries(gmxapi_extension_brerpotential PRIVATE Gromacs::gmxapi)
