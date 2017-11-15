//
// Created by Eric Irrgang on 11/3/17.
//

#include "export_plugin.h"

#include "gmxapi/md.h"
#include "gmxapi/md/mdmodule.h"
#include "gmxapi/gmxapi.h"

#include <pybind11/pybind11.h>

// Make a convenient alias to save some typing...
namespace py = pybind11;

// No, let's not have a dependency on gmxpy
//class PYBIND11_EXPORT GmxapiDerived: public gmxpy::MDModule
//{
//    public:
//        using gmxpy::MDModule::MDModule;
//};
//
//template<class T>
//class PYBIND11_EXPORT Restraint : public T, public gmxpy::PyMDModule
//{
//
//};

class MyRestraint
{
    public:
        static const char* docstring;

        void bind(gmxapi::MDHolder wrapper);

        std::shared_ptr<gmxapi::MDModule> getModule();
};

std::shared_ptr<gmxapi::MDModule> MyRestraint::getModule()
{
    auto module = std::make_shared<gmxapi::MDModule>();
    return module;
}

void MyRestraint::bind(gmxapi::MDHolder mdholder)
{
    auto workSpec = mdholder.getSpec();
    auto module = getModule();
    workSpec->addModule(module);
}

// Raw string will have line breaks and indentation as written between the delimiters.
const char* MyRestraint::docstring =
R"rawdelimiter(Some sort of custom potential.
)rawdelimiter";



void export_gmxapi(py::module& mymodule)
{
    py::class_<gmxapi::MDHolder> md_holder(mymodule, "MDholder", "Wrapper for gmxapi object", py::module_local());
//    py::class_< ::gmxapi::MDModule, std::shared_ptr<::gmxapi::MDModule> >
//        gmxapi_mdmodule(mymodule, "MDModule", py::module_local());
};

// The first argument is the name of the module when importing to Python. This should be the same as the name specified
// as the OUTPUT_NAME for the shared object library in the CMakeLists.txt file. The second argument, 'm', can be anything
// but it might as well be short since we use it to refer to aspects of the module we are defining.
PYBIND11_MODULE(myplugin, m) {
    m.doc() = "sample plugin"; // This will be the text of the module's docstring.

    export_gmxapi(m);
    // New plan: Instead of inheriting from gmx.core.MDModule, we can use a local import of
    // gmxapi::MDModule in both gmxpy and in extension modules. When md.add_potential() is
    // called, instead of relying on a binary interface to the MDModule, it will pass itself
    // as an argument to that module's bind() method. Then, all MDModules are dependent only
    // on libgmxapi as long as they provide the required function name. This is in line with
    // the Pythonic idiom of designing interfaces around functions instead of classes.
    //
    // Example: calling md.add_potential(mypotential) in Python causes to be called mypotential.bind(api_object), where api_object is a member of `md` that is a type exposed directly from gmxapi with
    // module_local bindings. To interact properly, then, mypotential just has to be something with a
    // bind() method that takes the same sort of gmxapi object, such as is defined locally. For simplicity
    // and safety, this gmxapi object will be something like
    // class MdContainer { public: shared_ptr<Md> md; };
    // and the bind method will grab and operate on the member pointer. It is possible to work
    // with the reference counting and such in Python, but it is easier and more compatible with
    // other Python extensions if we just keep the bindings as simple as possible and manage
    // object lifetime and ownership entirely in C++.
    //
    // We can provide a header or document in gmxapi or gmxpy specifically with the the set of containers
    // necessary to interact with gmxpy in a bindings-agnostic way, and in gmxpy and/or this repo, we can provide an export
    // function that provides pybind11 bindings.

    py::class_<MyRestraint> md_module(m, "MyRestraint");
    md_module.def(py::init<>(), "");
    md_module.def("bind", &MyRestraint::bind);
// where &MyRestraint::bind is a function like bind(::gmxapi::MDContainer& container){ return container->md->add_potential(this->getRestraint();)});


    // Our plugin subclasses gmxpy.core.MDModule, so we need to import that class.
//    auto gmx_core = py::module::import("gmx.core");
//    py::object plugin_base = (py::object) gmx_core.attr("GmxapiMDModule");

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
