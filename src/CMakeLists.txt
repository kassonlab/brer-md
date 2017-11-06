# Build a C++ library using libgmxapi to extend GROMACS.
add_subdirectory(cpp)


# Import the third-party Python bindings tools from the Pybind11 project: https://github.com/pybind
add_subdirectory(pybind11)


# Build a Python extension package from our new library.
add_subdirectory(pythonmodule)
