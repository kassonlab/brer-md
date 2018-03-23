//
// Created by Eric Irrgang on 11/3/17.
//

#include "export_plugin.h"

#include "pybind11/pybind11.h"
#include "pybind11/stl.h"

#include "gmxapi/md.h"
#include "gmxapi/md/mdmodule.h"
#include "gmxapi/gmxapi.h"

#include "harmonicpotential.h"
#include "ensemblepotential.h"
#include "make_unique.h"

// Make a convenient alias to save some typing...
namespace py = pybind11;

/*!
 * \brief Templated wrapper to use in Python bindings.
 *
 * Mix-in from below. Adds a bind behavior, a getModule() method to get a gmxapi::MDModule adapter,
 * and a create() method that assures a single shared_ptr record for an object that may sometimes
 * be referred to by a raw pointer and/or have shared_from_this called.
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
         * PyRestraint<T>::getModule(). If T derives from gmxapi::MDModule, we can keep a weak pointer
         * to ourself and generate a shared_ptr on request, but std::enable_shared_from_this already
         * does that, so we use it when we can.
         * \return
         */
        std::shared_ptr<gmxapi::MDModule> getModule();

        /*!
         * \brief Factory function to get a managed pointer to a new restraint.
         *
         * \tparam ArgsT
         * \param args
         * \return
         */
        template<typename ... ArgsT>
        static std::shared_ptr<PyRestraint<T>> create(ArgsT... args)
        {
            auto newRestraint = std::make_shared<PyRestraint<T>>(args...);
            return newRestraint;
        }

        template<typename ... ArgsT>
        explicit PyRestraint(ArgsT... args) :
            T{args...}
        {}

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

template<>
std::shared_ptr<gmxapi::MDModule> PyRestraint<plugin::RestraintModule<plugin::EnsembleRestraint>>::getModule()
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
class HarmonicRestraintBuilder
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
        explicit HarmonicRestraintBuilder(py::object element)
        {
            // Params attribute should be a Python list
            auto parameter_dict = py::cast<py::dict>(element.attr("params"));
            // Get positional parameters: two ints and two doubles.
            assert(parameter_dict.contains("sites"));
            assert(parameter_dict.contains("R0"));
            assert(parameter_dict.contains("k"));
            py::list sites = parameter_dict["sites"];
            site1Index_ = py::cast<unsigned long>(sites[0]);
            site2Index_ = py::cast<unsigned long>(sites[1]);
            equilibriumPosition_ = py::cast<real>(parameter_dict["R0"]);
            springConstant_ = py::cast<real>(parameter_dict["k"]);
        };

        /*!
         * \brief Add node(s) to graph for the work element.
         *
         * \param graph networkx.DiGraph object still evolving in gmx.context.
         *
         * \todo This does not follow the latest graph building protocol as described.
         */
        void build(py::object graph)
        {
            auto potential = PyRestraint<plugin::HarmonicModule>::create(site1Index_, site2Index_, equilibriumPosition_, springConstant_);

            auto subscriber = subscriber_;
            py::list potential_list = subscriber.attr("potential");
            potential_list.append(potential);

            // does note add a launcher to the graph.
            //std::unique_ptr<RestraintLauncher>();
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
            subscriber_ = subscriber;
        };

        py::object subscriber_;
        unsigned long site1Index_;
        unsigned long site2Index_;
        real equilibriumPosition_;
        real springConstant_;
};

class EnsembleRestraintBuilder
{
    public:
        explicit EnsembleRestraintBuilder(py::object element)
        {
            // It looks like we need some boilerplate exceptions for plugins so we have something to
            // raise if the element is invalid.
            assert(py::hasattr(element, "params"));

            // Params attribute should be a Python list
            py::dict parameter_dict = element.attr("params");
            // \todo Check for the presence of these dictionary keys to avoid hard-to-diagnose error.

            // Get positional parameters.
            py::list sites = parameter_dict["sites"];
            for (auto&& site : sites)
            {
                siteIndices_.emplace_back(py::cast<unsigned long>(site));
            }

            auto nbins = py::cast<size_t>(parameter_dict["nbins"]);
            auto binWidth = py::cast<double>(parameter_dict["binWidth"]);
            auto min_dist = py::cast<double>(parameter_dict["min_dist"]);
            auto max_dist = pybind11::cast<double>(parameter_dict["max_dist"]);
            auto experimental = pybind11::cast<std::vector<double>>(parameter_dict["experimental"]);
            auto nsamples = pybind11::cast<unsigned int>(parameter_dict["nsamples"]);
            auto sample_period = pybind11::cast<double>(parameter_dict["sample_period"]);
            auto nwindows = pybind11::cast<unsigned int>(parameter_dict["nwindows"]);
            auto window_update_period = pybind11::cast<double>(parameter_dict["window_update_period"]);
            auto K = pybind11::cast<double>(parameter_dict["k"]);
            auto sigma = pybind11::cast<double>(parameter_dict["sigma"]);

            auto params = plugin::make_ensemble_params(nbins, binWidth, min_dist, max_dist, experimental, nsamples, sample_period, nwindows, window_update_period, K, sigma);
            params_ = std::move(*params);

            // Note that if we want to grab a reference to the Context or its communicator, we can get it
            // here through element.workspec._context. We need a more general API solution, but this code is
            // in the Python bindings code, so we know we are in a Python Context.
            assert(py::hasattr(element, "workspec"));
            auto workspec = element.attr("workspec");
            assert(py::hasattr(workspec, "_context"));
            context_ = workspec.attr("_context");
        }

        /*!
         * \brief Add node(s) to graph for the work element.
         *
         * \param graph networkx.DiGraph object still evolving in gmx.context.
         *
         * \todo This may not follow the latest graph building protocol as described.
         */
        void build(py::object graph)
        {
            // Temporarily subvert things to get quick-and-dirty solution for testing.
            // Need to capture Python communicator and pybind syntax in closure so EnsembleResources
            // can just call with matrix arguments.

            // This can be replaced with a subscription and delayed until launch, if necessary.
            assert(py::hasattr(context_, "ensemble_update"));
            // make a local copy of the Python object so we can capture it in the lambda
            auto update = context_.attr("ensemble_update");
            // Make a bindings-independent callable with standardizeable signature.
            auto functor = [update](const plugin::Matrix<double>& send, plugin::Matrix<double>* receive)
            {
                update(send, receive);
            };

            // To use a reduce function on the Python side, we need to provide it with a Python buffer-like object,
            // so we will create one here. Note: it looks like the SharedData element will be useful after all.
            auto resources = std::make_shared<plugin::EnsembleResources>(std::move(functor));

            auto potential = PyRestraint<plugin::RestraintModule<plugin::EnsembleRestraint>>::create(siteIndices_, params_, resources);

            auto subscriber = subscriber_;
            py::list potential_list = subscriber.attr("potential");
            potential_list.append(potential);

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
            subscriber_ = subscriber;
        };

        py::object subscriber_;
        py::object context_;
        std::vector<unsigned long int> siteIndices_;

        plugin::ensemble_input_param_type params_;
};

std::unique_ptr<HarmonicRestraintBuilder> create_harmonic_builder(const py::object element)
{
    std::unique_ptr<HarmonicRestraintBuilder> builder{new HarmonicRestraintBuilder(element)};
    return builder;
}

std::unique_ptr<EnsembleRestraintBuilder> create_ensemble_builder(const py::object element)
{
    using gmx::compat::make_unique;
    auto builder = make_unique<EnsembleRestraintBuilder>(element);
    return builder;
}

// The first argument is the name of the module when importing to Python. This should be the same as the name specified
// as the OUTPUT_NAME for the shared object library in the CMakeLists.txt file. The second argument, 'm', can be anything
// but it might as well be short since we use it to refer to aspects of the module we are defining.
PYBIND11_MODULE(myplugin, m) {
    m.doc() = "sample plugin"; // This will be the text of the module's docstring.

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
    md_module.def(py::init<>(
        []()
        {
            return PyRestraint<MyRestraint>::create();
        }),
        "Create default MyRestraint"
    );
    md_module.def("bind", &PyRestraint<MyRestraint>::bind);

    // The template parameters specify the C++ class to export and the handle type.
    // The function parameters specify the containing module and the Python name for the class.
//    py::class_<PyRestraint<MyRestraint>> potential(m, "Potential");
//    potential.def(py::init());
//    // Set the Python docstring.
//    potential.doc() = MyRestraint::docstring;


    // This bindings specification could actually be done in a templated function to automatically
    // generate parameter setters/getters

    // Builder to be returned from create_restraint,
    py::class_<HarmonicRestraintBuilder> harmonic_builder(m, "HarmonicBuilder");
    harmonic_builder.def("add_subscriber", &HarmonicRestraintBuilder::add_subscriber);
    harmonic_builder.def("build", &HarmonicRestraintBuilder::build);

    // API object to build.
    // We use a shared_ptr handle because both the Python interpreter and libgromacs may need to extend
    // the lifetime of the object.
    py::class_<PyRestraint<plugin::HarmonicModule>, std::shared_ptr<PyRestraint<plugin::HarmonicModule>>> harmonic(m, "HarmonicRestraint");
    harmonic.def(
        py::init(
            [](unsigned long int site1,
               unsigned long int site2,
               real R0,
               real k)
            {
                return PyRestraint<plugin::HarmonicModule>::create(site1, site2, R0, k);
            }
        ),
        "Construct HarmonicRestraint"
    );
    harmonic.def("bind", &PyRestraint<plugin::HarmonicModule>::bind);
    //harmonic.def_property(name, getter, setter, extra)
//    harmonic.def_property("pairs", &PyRestraint<plugin::HarmonicModule>::getPairs, &PyRestraint<plugin::HarmonicModule>::setPairs, "The indices of particle pairs to restrain");

    // Builder to be returned from create_restraint
    pybind11::class_<EnsembleRestraintBuilder> ensemble_builder(m, "EnsembleBuilder");
    ensemble_builder.def("add_subscriber", &EnsembleRestraintBuilder::add_subscriber);
    ensemble_builder.def("build", &EnsembleRestraintBuilder::build);

    using PyEnsemble = PyRestraint<plugin::RestraintModule<plugin::EnsembleRestraint>>;
    py::class_<plugin::EnsembleRestraint::input_param_type> ensemble_params(m, "EnsembleRestraintParams");
    // Builder to be returned from ensemble_restraint
    // API object to build.
    py::class_<PyEnsemble, std::shared_ptr<PyEnsemble>> ensemble(m, "EnsembleRestraint");
    // EnsembleRestraint can only be created via builder for now.
    ensemble.def("bind", &PyEnsemble::bind, "Implement binding protocol");


    /*
     * To implement gmxapi_workspec_1_0, the module needs a function that a Context can import that
     * produces a builder that translates workspec elements for session launching. The object returned
     * by our function needs to have an add_subscriber(other_builder) method and a build(graph) method.
     * The build() method returns None or a launcher. A launcher has a signature like launch(rank) and
     * returns None or a runner.
     */
    m.def("make_ensemble_params", &plugin::make_ensemble_params);
    m.def("create_restraint", [](const py::object element){ return create_harmonic_builder(element); });
    m.def("ensemble_restraint", [](const py::object element){ return create_ensemble_builder(element); });

    // Matrix utility class (temporary). Borrowed from http://pybind11.readthedocs.io/en/master/advanced/pycpp/numpy.html#arrays
    py::class_<plugin::Matrix<double>, std::shared_ptr<plugin::Matrix<double>>>(m, "Matrix", py::buffer_protocol())
        .def_buffer([](plugin::Matrix<double> &matrix) -> py::buffer_info {
            return py::buffer_info(
                matrix.data(),                               /* Pointer to buffer */
                sizeof(double),                          /* Size of one scalar */
                py::format_descriptor<double>::format(), /* Python struct-style format descriptor */
                2,                                      /* Number of dimensions */
                { matrix.rows(), matrix.cols() },                 /* Buffer dimensions */
                { sizeof(double) * matrix.cols(),             /* Strides (in bytes) for each index */
                  sizeof(double) }
            );
        });
}
