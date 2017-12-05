cmake_minimum_required(VERSION 3.4.3)
project(harmonicRestraint)

# This project requires GROMACS to build. It should be sufficient to source the GMXRC, but you can also set the
# GROMACS_DIR environment variable to help CMake find the GROMACS installation.

# Note that the code will need to be built separately for different versions of Python and for substantially different
# versions of GROMACS. If building from the command line, you can specify a Python executable with the PYTHON_EXECUTABLE
# variable. For instance, to make sure you are building for your default Python, cmake -DPYTHON_EXECUTABLE=`which python`.

set(CMAKE_CXX_STANDARD 11)

# CMake modules are in a subdirectory to keep this file cleaner
list(APPEND CMAKE_MODULE_PATH ${CMAKE_CURRENT_SOURCE_DIR}/cmake)

option(BUILD_TESTING "set ON to build testing framework" OFF)

# Assuming GROMACS is in our path or that we have set either the gmxapi_DIR or GROMACS_DIR environment variables,
# this will find the CMake configuration for the GROMACS libraries we need and define the CMake library objects
# Gromacs:gmxapi
find_package(gmxapi
             0.0.3 REQUIRED
             HINTS "$ENV{GROMACS_DIR}"
             )

if(gmxapi_FOUND)
    message("gmxapi found")
endif()
message("Found gmxapi version ${gmxapi_VERSION_MAJOR}.${gmxapi_VERSION_MINOR}.${gmxapi_VERSION_PATCH}")

# Now move on to building the custom code.
add_subdirectory(src)

if(BUILD_TESTING)
    enable_testing()
    add_subdirectory(tests)
endif()
