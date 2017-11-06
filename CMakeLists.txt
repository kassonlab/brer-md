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

######################################################
# The following is boiler-plate recommended by GROMACS
######################################################
# In principle, this could be deduced from GROMACS_IS_DOUBLE returned by
# find_package(GROMACS) based on the suffix alone, but it is clearer that the
# user explicitly sets what they want to get, and then need to provide a suffix
# to match.
option(GMX_DOUBLE "Use double precision" OFF)
set(GMX_SUFFIX "" CACHE STRING "Suffix for the GROMACS installation to use (empty for default)")

# This does not allow for a non-suffixed double-precision libgromacs, but
# that should be rare enough for demonstration purposes.
if (GMX_DOUBLE AND NOT GMX_SUFFIX)
    set(GROMACS_SUFFIX "_d")
else()
    set(GROMACS_SUFFIX ${GMX_SUFFIX})
endif()

find_package(GROMACS 5.1 REQUIRED)
gromacs_check_double(GMX_DOUBLE)
gromacs_check_compiler(CXX)
include_directories(${GROMACS_INCLUDE_DIRS})
add_definitions(${GROMACS_DEFINITIONS})

# Use static linking on MSVC
if (CMAKE_GENERATOR MATCHES "Visual Studio")
    string(REPLACE /MD /MT CMAKE_C_FLAGS_RELEASE ${CMAKE_C_FLAGS_RELEASE})
    set(CMAKE_C_FLAGS_RELEASE ${CMAKE_C_FLAGS_RELEASE} CACHE STRING "" FORCE)
    string(REPLACE /MD /MT CMAKE_C_FLAGS_DEBUG ${CMAKE_C_FLAGS_DEBUG})
    set(CMAKE_C_FLAGS_DEBUG ${CMAKE_C_FLAGS_DEBUG} CACHE STRING "" FORCE)
endif()
########################################################

# Assuming GROMACS is in our path or that we have set either the gmxapi_DIR or GROMACS_DIR environment variables,
# this will find the CMake configuration for the GROMACS libraries we need and define the CMake library objects
# Gromacs:gmxapi
find_package(gmxapi
             REQUIRED
             HINTS "$ENV{GROMACS_DIR}"
             )

# Now move on to building the custom code.
add_subdirectory(src)


if(BUILD_TESTING)
    enable_testing()
    add_subdirectory(tests)
endif()
