# The first argument sets the name of the target for CMake bookkeeping purposes. It is the default name of the
# shared object library that is produced, but we can override that.
pybind11_add_module(sampleplugin MODULE export_plugin.cpp)

# Set the name of the shared object library (and the name of the Python module) to "myplugin"
#set_target_properties(sampleplugin PROPERTIES OUTPUT_NAME myplugin)
set_target_properties(sampleplugin PROPERTIES OUTPUT_NAME myplugin)

# The Python module requires the new library we wrote as well as the gmxapi that we found in the top-level CMakeLists.txt
target_link_libraries(sampleplugin PRIVATE Gromacs::gmxapi harmonicpotential)
