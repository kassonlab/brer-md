//
// Created by Eric Irrgang on 11/3/17.
//

#include "export_plugin.h"

#include "gmxapi/md.h"
#include "gmxapi/md/mdmodule.h"
#include "gmxapi/gmxapi.h"

#include "pybind11/pybind11.h"
#include "pybind11/stl.h"

#include "harmonicpotential.h"

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

/*!
 * \brief Allow the Context to launch this graph node.
 *
 * Produced by RestraintBuilder::build(), objects of this type are functors that fit the Session launch(rank)
 * call signature.
 */
class RestraintLauncher
{
    public:
        /*!
         * \brief Use objects as functors.
         *
         * \param rank Index of this worker in the ensemble of simulations.
         *
         * Called once by the Context when launching a Session, performs start-up tasks for the API object(s).
         */
        void operator()(int rank)
        {};
};

/*!
 * \brief Graph updater for Restraint element.
 *
 * Returned by create_builder(), translates the workflow operation into API operations.
 */
class RestraintBuilder
{
    public:
        /*!
         * \brief Create directly from workflow element.
         *
         * \param element a Python object implementing the gmx.workflow.WorkElement interface.
         *
         * It doesn't make sense to take a py::object here. We could take a serialized version of the element
         * iff we also got a reference to the current context, but right now we use the gmx.workflow.WorkElement's
         * reference to the WorkSpec, which has a reference to the Context, to get, say, the communicator.
         * Arguably, a builder provided by the restraint shouldn't do such a thing.
         *
         * Either the builder / translator / DAG updater should be Context agnostic or should actually be
         * implemented in the Context, in which case we need some better convention about what that translation
         * should look like and what resources need to be provided by the module to do it.
         */
        explicit RestraintBuilder(py::object element)
        {
            // Params attribute should be a Python list
            py::list parameter_list = element.attr("params");
            // Get positional parameters: two ints and two doubles.
            _site1_index = py::cast<unsigned long>(parameter_list[0]);
            _site2_index = py::cast<unsigned long>(parameter_list[1]);
            _equilibrium_position = py::cast<real>(parameter_list[2]);
            _spring_constant = py::cast<real>(parameter_list[3]);
        };

        /*!
         * \brief Add node(s) to graph for the work element.
         *
         * \param graph networkx.DiGraph object still evolving in gmx.context.
         */
        void build(py::object graph)
        {
            auto potential = PyRestraint<plugin::HarmonicModule>::create();
            potential->setParams(_site1_index, _site2_index, _equilibrium_position, _spring_constant);

            auto subscriber = _subscriber;
            py::list potential_list = subscriber.attr("potential");
            potential_list.append(potential);
            std::unique_ptr<RestraintLauncher>();
        };

        /*!
         * \brief Accept subscription of an MD task.
         *
         * \param subscriber Python object with a 'potential' attribute that is a Python list.
         *
         * During build, an object is added to the subscriber's self.potential, which is then bound with
         * system.add_potential(potential) during the subscriber's launch()
         */
        void add_subscriber(py::object subscriber)
        {
            assert(py::hasattr(subscriber, "potential"));
            _subscriber = subscriber;
        };

        py::object _subscriber;
        unsigned long _site1_index;
        unsigned long _site2_index;
        real _equilibrium_position;
        real _spring_constant;
};

std::unique_ptr<RestraintBuilder> create_builder(const py::object element)
{
    std::unique_ptr<RestraintBuilder> builder{new RestraintBuilder(element)};
    return builder;
}

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


    py::class_<RestraintBuilder> builder(m, "Builder");
    builder.def("add_subscriber", &RestraintBuilder::add_subscriber);
    builder.def("build", &RestraintBuilder::build);

    // This bindings specification could actually be done in a templated function to automatically
    // generate parameter setters/getters
    py::class_<PyRestraint<plugin::HarmonicModule>, std::shared_ptr<PyRestraint<plugin::HarmonicModule>>> harmonic(m, "HarmonicRestraint");
    harmonic.def(py::init(&PyRestraint<plugin::HarmonicModule>::create), "Construct HarmonicRestraint");
    harmonic.def("bind", &PyRestraint<plugin::HarmonicModule>::bind);
    //harmonic.def_property(name, getter, setter, extra)
//    harmonic.def_property("pairs", &PyRestraint<plugin::HarmonicModule>::getPairs, &PyRestraint<plugin::HarmonicModule>::setPairs, "The indices of particle pairs to restrain");
    harmonic.def("set_params", &PyRestraint<plugin::HarmonicModule>::setParams, "Set a pair, spring constant, and equilibrium distance.");

    /*
     * To implement gmxapi_workspec_1_0, the module needs a function that a Context can import that
     * produces a builder that translates workspec elements for session launching. The object returned
     * by our function needs to have an add_subscriber(other_builder) method and a build(graph) method.
     * The build() method returns None or a launcher. A launcher has a signature like launch(rank) and
     * returns None or a runner.
     */
    m.def("create_restraint", [](const py::object element){ return create_builder(element); });
}
