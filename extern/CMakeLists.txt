# We need to build and install the packages at configure time in order to use their generated
# import targets. I don't think we can make find_package dependent on an import target or a
# ExternalProject target, so we'll just resolve things during the configure phase of CMake.
#
# If we can exclusively use the libgromacs import target for required information and not
# exported CMake variables, then we should be able to use a regular ExternalProject target here,
# I think.

# In order to make it easy to do all of this non-interactively while building a Docker image, we require
# that the repositories have already been downloaded. This is easiest by using the `--recurse-submodules`
# option when cloning this repository. This gets easier when the required repository becomes public.
# \todo: check for whether the external repositories have been downloaded.
# \todo: rely on public repository for Docker build or have option.

# Configure the CMake project
file(MAKE_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/gromacs-build)

set(_configure_command "${CMAKE_COMMAND} -G \"${CMAKE_GENERATOR}\"
                    ${CMAKE_CURRENT_LIST_DIR}/gromacs
                    -DCMAKE_INSTALL_PREFIX=${CMAKE_CURRENT_BINARY_DIR}/gromacs
                    -DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE}")
message("Executing subprocess: ${_configure_command}"
        )
execute_process(COMMAND "${_configure_command}"
                RESULT_VARIABLE result
                OUTPUT_VARIABLE output
                ERROR_VARIABLE error
                WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/gromacs-build)
if (${result})
    message("${error}")
    message("${output}")
    message("${result}")
endif()

# Build and install the CMake project
set(_build_install_command "${CMAKE_COMMAND} --build ${CMAKE_CURRENT_BINARY_DIR}/gromacs-build --target install")
message("Executing subprocess: ${_build_install_command}")
execute_process(COMMAND ${CMAKE_COMMAND} --build ${CMAKE_CURRENT_BINARY_DIR}/gromacs-build --target install
                RESULT_VARIABLE result
                WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/gromacs-build)
if (${result})
    message("${error}")
    message("${output}")
    message("${result}")
endif()

