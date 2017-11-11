//
// Created by Eric Irrgang on 11/3/17.
//

#include "export_plugin.h"

#include <pybind11/pybind11.h>

// Make a convenient alias to save some typing...
namespace py = pybind11;

namespace gmxpy{
class MDModule
{
    public:
        MDModule() = default;
        std::shared_ptr<gmxapi::MDModule> module;
        const char* name() {return "gmxpy::MDModule";};
};
} // end namespace gmxpy

class PYBIND11_EXPORT GmxapiDerived: public gmxpy::MDModule
{
    public:
        using gmxpy::MDModule::MDModule;
};

template<class T>
class PYBIND11_EXPORT Restraint : public T, public gmxpy::PyMDModule
{

};

class MyRestraint
{
    public:
        static const char* docstring;
};

// Raw string will have line breaks and indentation as written between the delimiters.
const char* MyRestraint::docstring =
R"rawdelimiter(Some sort of custom potential.
)rawdelimiter";


// The first argument is the name of the module when importing to Python. This should be the same as the name specified
// as the OUTPUT_NAME for the shared object library in the CMakeLists.txt file. The second argument, 'm', can be anything
// but it might as well be short since we use it to refer to aspects of the module we are defining.
PYBIND11_MODULE(myplugin, m) {
    m.doc() = "sample plugin"; // This will be the text of the module's docstring.

    // Our plugin subclasses gmxpy.core.MDModule, so we need to import that class.
    auto gmx_core = py::module::import("gmx.core");
    py::object plugin_base = (py::object) gmx_core.attr("GmxapiMDModule");

//    py::class_< GmxapiDerived >(m, "Derived", plugin_base);

    // Moving forward, we can look into breaking this dependency with a portable
    // C struct that contains a pointer to a gmxapi_md_module or a function pointer
    // or something. It is probably informative to look at how ndarrays are generally
    // interoperable.
    // hmmm... linking dependency...

    // The template parameters specify the C++ class to export and the handle type.
    // The function parameters specify the containing module and the Python name for the class.
//    py::class_<Restraint<MyRestraint>> potential(m, "Potential");
//    potential.def(py::init());
//    // Set the Python docstring.
//    potential.doc() = MyRestraint::docstring;
}
