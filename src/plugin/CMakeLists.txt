cmake_minimum_required(VERSION 3.15)
# If you are using this repository as a template, you should probably change the
# project name and adopt your own versioning scheme.
project(brer_restraint VERSION 0.0.8)

# Only interpret if() arguments as variables or keywords when unquoted.
cmake_policy(SET CMP0054 NEW)
# honor the language standard settings for try_compile()
cmake_policy(SET CMP0067 NEW)
# Allow gmxapi_ROOT hint.
cmake_policy(SET CMP0074 NEW)
# If the user provides a hint for the Python installation with Python3_ROOT_DIR,
# prevent FindPython3 from overriding the choice with a newer Python version.
cmake_policy(SET CMP0094 NEW) #3.15
if (POLICY CMP0139) #3.24
    cmake_policy(SET CMP0139 NEW)
endif ()

if(NOT Python3_FIND_VIRTUALENV)
    # We advocate using Python venvs to manage package availability, so by default
    # we want to preferentially discover user-space software.
    set(Python3_FIND_VIRTUALENV FIRST)
endif()

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_VISIBILITY_PRESET hidden)
enable_language(CXX)

find_package(Python3 3.7 COMPONENTS Interpreter Development)
find_package(pybind11 2.6 QUIET CONFIG)
# If we are not running through setup.py, we may need to look for the pybind11 headers.
if (NOT pybind11_FOUND)
    execute_process(
        COMMAND
        "${Python3_EXECUTABLE}" -c
        "import pybind11; print(pybind11.get_cmake_dir())"
        OUTPUT_VARIABLE _tmp_dir
        OUTPUT_STRIP_TRAILING_WHITESPACE)
    list(APPEND CMAKE_PREFIX_PATH "${_tmp_dir}")
    # The following should only run once, and if it runs more often than that, we would want to
    # know about it. So we don't use `QUIET` here.
    find_package(pybind11 2.6 CONFIG)
endif ()
if (NOT pybind11_FOUND)
    message(FATAL_ERROR "Python package build dependencies not found with interpreter ${Python3_EXECUTABLE}. "
            "See https://manual.gromacs.org/current/gmxapi/userguide/install.html")
endif ()

# Workaround for issue #4563 for GROMACS releases that won't be patched:
# Find GROMACS package early.
find_package(GROMACS 2019 REQUIRED
             NAMES gromacs${GROMACS_SUFFIX} gromacs_mpi gromacs_d gromacs_mpi_d
             HINTS "$ENV{GROMACS_DIR}" ${gmxapi_ROOT}
             )
if (NOT DEFINED GROMACS_IS_DOUBLE)
    message(AUTHOR_WARNING "GROMACS_IS_DOUBLE undefined.")
endif ()
if(NOT TARGET Gromacs::libgromacs)
    if(TARGET libgromacs)
        add_library(Gromacs::libgromacs ALIAS libgromacs)
    else()
        message(FATAL_ERROR "Could not find a libgromacs CMake target.")
    endif()
endif()

find_package(gmxapi REQUIRED)

#
# Get details of GROMACS installation needed by the Python package at run time.
#

if (GROMACS_IS_DOUBLE)
    set(_gmx_double "true")
else()
    set(_gmx_double "false")
endif()
unset(_gmx_double)

# Build a C++ library using libgmxapi to extend GROMACS.
# We process this subdirectory first to reaffirm that this code does not depend
# on other substantial infrastructure, such as a particular Python bindings
# framework or the Googletest framework.
add_subdirectory(cpp)

# Build a Python extension package from our new library.
add_subdirectory(pythonmodule)
