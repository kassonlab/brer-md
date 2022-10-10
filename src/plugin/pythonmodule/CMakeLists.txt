pybind11_add_module(md MODULE export_plugin.cpp)
# The first argument sets the name of the target for CMake bookkeeping purposes. It is the default name of the
# shared object library that is produced, but we can override that.

# Set the name of the shared object library (and the name of the Python module) to "md".
set_target_properties(md PROPERTIES OUTPUT_NAME md)

# We can't easily/reliably let a debug build of a Python module have a "d" suffix and still be importable with the same
# name.
set_target_properties(md PROPERTIES DEBUG_POSTFIX "")

# We expect to be building against an installed GROMACS that we will continue to dynamically link against at runtime.
set_target_properties(md PROPERTIES BUILD_WITH_INSTALL_RPATH TRUE)
set_target_properties(md PROPERTIES INSTALL_RPATH_USE_LINK_PATH TRUE)

# The Python module requires the new library we wrote as well as the gmxapi that we found in the top-level
# CMakeLists.txt
target_link_libraries(md PRIVATE Gromacs::gmxapi brer_linearpotential brer_linearstoppotential brer_brerpotential)
