//
// Created by Eric Irrgang on 11/3/17.
//

#include "export_plugin.h"

#include "gmxapi/md.h"
#include "gmxapi/md/mdmodule.h"
#include "gmxapi/gmxapi.h"

#include <pybind11/pybind11.h>
#include <iostream>
#include <harmonicpotential.h>

// Make a convenient alias to save some typing...
namespace py = pybind11;

/*!
 * \brief Templated wrapper to use in Python bindings.
 *
 * Mix-in from below.
 * \tparam T
 */
template<class T>
class PyRestraint : public T, public std::enable_shared_from_this<PyRestraint<T>>
{
    public:

        void bind(py::object object);

        using T::name;

        /*!
         * \brief
         *
         * T must either derive from gmxapi::MDModule or provide a template specialization for
         * PyRestraint<T>::getModule().
         * \return
         */
        std::shared_ptr<gmxapi::MDModule> getModule();

        static std::shared_ptr<PyRestraint<T>> create()
        {
            auto newRestraint = std::make_shared<PyRestraint<T>>();
            return newRestraint;
        }
};

template<class T>
void PyRestraint<T>::bind(py::object object)
{
    PyObject* capsule = object.ptr();
    if (PyCapsule_IsValid(capsule, gmxapi::MDHolder::api_name))
    {
        auto holder = static_cast<gmxapi::MDHolder*>(PyCapsule_GetPointer(capsule, gmxapi::MDHolder::api_name));
        auto workSpec = holder->getSpec();
        std::cout << this->name() << " received " << holder->name();
        std::cout << " containing spec of size ";
        std::cout << workSpec->getModules().size();
        std::cout << std::endl;

        auto module = getModule();
        workSpec->addModule(module);
    }
    else
    {
        throw gmxapi::ProtocolError("bind method requires a python capsule as input");
    }
}

// If T is derived from gmxapi::MDModule, create a default-constructed std::shared_ptr<T>
// \todo Need a better default that can call a shared_from_this()
template<class T>
std::shared_ptr<gmxapi::MDModule> PyRestraint<T>::getModule()
{
    auto module = std::make_shared<typename std::enable_if<std::is_base_of<gmxapi::MDModule, T>::value, T>::type>();
    return module;
}

template<>
std::shared_ptr<gmxapi::MDModule> PyRestraint<plugin::HarmonicModule>::getModule()
{
    return shared_from_this();
}




class MyRestraint
{
    public:
        static const char* docstring;

        static std::string name() { return "MyRestraint"; };
};

template<>
std::shared_ptr<gmxapi::MDModule> PyRestraint<MyRestraint>::getModule()
{
    auto module = std::make_shared<gmxapi::MDModule>();
    return module;
}


// Raw string will have line breaks and indentation as written between the delimiters.
const char* MyRestraint::docstring =
R"rawdelimiter(Some sort of custom potential.
)rawdelimiter";

void export_gmxapi(py::module& mymodule)
{
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

    // Make a null restraint for testing.
    py::class_<PyRestraint<MyRestraint>, std::shared_ptr<PyRestraint<MyRestraint>>> md_module(m, "MyRestraint");
    md_module.def(py::init(&PyRestraint<MyRestraint>::create), "Create default MyRestraint");
    md_module.def("bind", &PyRestraint<MyRestraint>::bind);

    // The template parameters specify the C++ class to export and the handle type.
    // The function parameters specify the containing module and the Python name for the class.
//    py::class_<PyRestraint<MyRestraint>> potential(m, "Potential");
//    potential.def(py::init());
//    // Set the Python docstring.
//    potential.doc() = MyRestraint::docstring;

    // This bindings specification could actually be done in a templated function to automatically
    // generate parameter setters/getters
    py::class_<PyRestraint<plugin::HarmonicModule>, std::shared_ptr<PyRestraint<plugin::HarmonicModule>>> harmonic(m, "HarmonicRestraint");
    harmonic.def(py::init(&PyRestraint<plugin::HarmonicModule>::create), "Construct HarmonicRestraint");
    harmonic.def("bind", &PyRestraint<plugin::HarmonicModule>::bind);
    //harmonic.def_property(name, getter, setter, extra)
//    harmonic.def_property("pairs", &PyRestraint<plugin::HarmonicModule>::getPairs, &PyRestraint<plugin::HarmonicModule>::setPairs, "The indices of particle pairs to restrain");
    harmonic.def("set_params", &PyRestraint<plugin::HarmonicModule>::setParams, "Set a pair, spring constant, and equilibrium distance.");

}
