# The first argument sets the name of the target for CMake bookkeeping purposes. It is the default name of the
# shared object library that is produced, but we can override that.
pybind11_add_module(sampleplugin MODULE export_plugin.cpp)

# Set the name of the shared object library (and the name of the Python module) to "myplugin"
#set_target_properties(sampleplugin PROPERTIES OUTPUT_NAME myplugin)
set_target_properties(sampleplugin PROPERTIES OUTPUT_NAME myplugin)
# We can't easily/reliably let a debug build of a Python module have a "d" suffix and still be importable with the same name.
set_target_properties(sampleplugin PROPERTIES DEBUG_POSTFIX "")

# We expect to be building against an installed GROMACS that we will continue to dynamically link against at runtime.
set_target_properties(sampleplugin PROPERTIES BUILD_WITH_INSTALL_RPATH TRUE)
set_target_properties(sampleplugin PROPERTIES INSTALL_RPATH_USE_LINK_PATH TRUE)

# The Python module requires the new library we wrote as well as the gmxapi that we found in the top-level CMakeLists.txt
target_link_libraries(sampleplugin PRIVATE Gromacs::gmxapi harmonicpotential ensemblepotential)

# We might as well add an install target.
# We can find the user's site-packages directory with `python -m site --user-site`
# After adding the pybind11 subdirectory earlier, the python executable is in the usual PYTHON_EXECUTABLE
# variable, and PYTHON_SITE_PACKAGES is also set (retrieved with `from distutils import sysconfig as s; s.get_python_lib(plat_specific=True)`)
# \todo set a reasonable default CMAKE_INSTALL_PREFIX
# \todo define an install target
