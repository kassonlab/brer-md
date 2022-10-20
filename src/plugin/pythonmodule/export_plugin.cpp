/*! \file
 * \brief Provide Python bindings and helper functions for setting up restraint
 * potentials.
 * \author Jennifer Hays Wagner <jmhays@gmail.com>
 */

#include "export_plugin.h"

#include <cassert>

#include <memory>

#include "gmxapi/exceptions.h"
#include "gmxapi/gmxapi.h"
#include "gmxapi/md.h"
#include "gmxapi/md/mdmodule.h"

#include "brerpotential.h"
#include "linearpotential.h"
#include "linearstoppotential.h"

// Make a convenient alias to save some typing...
namespace py = pybind11;

namespace {
////////////////////////////////
// Begin PyRestraint static code
/*!
 * \brief Templated wrapper to use in Python bindings.
 *
 * Boilerplate
 *
 * Mix-in from below. Adds a bind behavior, a getModule() method to get a
 * gmxapi::MDModule adapter, and a create() method that assures a single
 * shared_ptr record for an object that may sometimes be referred to by a raw
 * pointer and/or have shared_from_this called. \tparam T class implementing
 * gmx::IRestraintPotential
 *
 */
template <class T>
class PyRestraint : public T,
                    public std::enable_shared_from_this<PyRestraint<T>>
{
public:
  void bind(py::object object);

  using T::name;

  /*!
   * \brief
   *
   * T must either derive from gmxapi::MDModule or provide a template
   * specialization for PyRestraint<T>::getModule(). If T derives from
   * gmxapi::MDModule, we can keep a weak pointer to ourself and generate a
   * shared_ptr on request, but std::enable_shared_from_this already does that,
   * so we use it when we can. \return
   */
  std::shared_ptr<gmxapi::MDModule> getModule();

  /*!
   * \brief Factory function to get a managed pointer to a new restraint.
   *
   * \tparam ArgsT
   * \param args
   * \return
   */
  template <typename... ArgsT>
  static std::shared_ptr<PyRestraint<T>> create(ArgsT... args)
  {
    auto newRestraint = std::make_shared<PyRestraint<T>>(args...);
    return newRestraint;
  }

  template <typename... ArgsT>
  explicit PyRestraint(ArgsT... args) : T{args...} {}
};

/*!
 * \brief Implement the gmxapi binding protocol for restraints.
 *
 * All restraints will use this same code automatically.
 *
 * \tparam T restraint class exported below.
 * \param object Python Capsule object to allow binding with a simple C API.
 */
template <class T>
void PyRestraint<T>::bind(py::object object)
{
  PyObject *capsule = object.ptr();
  if (PyCapsule_IsValid(capsule, gmxapi::MDHolder::api_name))
  {
    auto holder = static_cast<gmxapi::MDHolder *>(
        PyCapsule_GetPointer(capsule, gmxapi::MDHolder::api_name));
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
    throw gmxapi::ProtocolError(
        "bind method requires a python capsule as input");
  }
}
// end PyRestraint static code
//////////////////////////////

/*!
 * \brief Interact with the restraint framework and gmxapi when launching a
 * simulation.
 *
 * This should be generalized and removed from here. Unfortunately, some things
 * need to be standardized first. If a potential follows the example of
 * EnsembleRestraint or HarmonicRestraint, the template specializations below
 * can be mimicked to give GROMACS access to the potential.
 *
 * \tparam T class implementing the gmxapi::MDModule interface.
 * \return shared ownership of a T object via the gmxapi::MDModule interface.
 */
// If T is derived from gmxapi::MDModule, create a default-constructed
// std::shared_ptr<T> \todo Need a better default that can call a
// shared_from_this()

template <class T>
std::shared_ptr<gmxapi::MDModule> PyRestraint<T>::getModule()
{
  auto module = std::make_shared<typename std::enable_if<
      std::is_base_of<gmxapi::MDModule, T>::value, T>::type>();
  return module;
}

template <>
std::shared_ptr<gmxapi::MDModule>
PyRestraint<plugin::RestraintModule<plugin::LinearRestraint>>::getModule()
{
  return shared_from_this();
}

template <>
std::shared_ptr<gmxapi::MDModule>
PyRestraint<plugin::RestraintModule<plugin::LinearStopRestraint>>::getModule()
{
  return shared_from_this();
}

template <>
std::shared_ptr<gmxapi::MDModule>
PyRestraint<plugin::RestraintModule<plugin::BRERRestraint>>::getModule()
{
  return shared_from_this();
}

// Start Linear Restraint
class LinearRestraintBuilder
{
public:
  explicit LinearRestraintBuilder(py::object element)
  {
    name_ = py::cast<std::string>(element.attr("name"));
    assert(!name_.empty());
    // Params attribute should be a Python list
    auto parameter_dict = py::cast<py::dict>(element.attr("params"));

    assert(parameter_dict.contains("sites"));
    assert(parameter_dict.contains("target"));
    assert(parameter_dict.contains("alpha"));
    assert(parameter_dict.contains("sample_period"));
    assert(parameter_dict.contains("logging_filename"));

    py::list sites = parameter_dict["sites"];
    for (auto &&site : sites)
    {
      siteIndices_.emplace_back(py::cast<int>(site));
    }

    auto alpha = py::cast<double>(parameter_dict["alpha"]);
    auto samplePeriod = py::cast<double>(parameter_dict["sample_period"]);
    auto target = py::cast<double>(parameter_dict["target"]);
    auto logging_filename =
        py::cast<std::string>(parameter_dict["logging_filename"]);

    auto params =
        plugin::makeLinearParams(alpha, target, samplePeriod, logging_filename);
    params_ = std::move(*params);

    assert(py::hasattr(element, "workspec"));
    auto workspec = element.attr("workspec");
    assert(py::hasattr(workspec, "_context"));
    context_ = workspec.attr("_context");
  }

  void build(py::object graph)
  {
    // Temporarily subvert things to get quick-and-dirty solution for testing.
    // Need to capture Python communicator and pybind syntax in closure so
    // EnsembleResources can just call with matrix arguments.
    if (!subscriber_)
    {
      return;
    }
    else
    {
      if (!py::hasattr(subscriber_, "potential"))
        throw gmxapi::ProtocolError("Invalid subscriber");
    }
    // This can be replaced with a subscription and delayed until launch, if
    // necessary.
    if (!py::hasattr(context_, "ensemble_update"))
    {
      throw gmxapi::ProtocolError("context does not have 'ensemble_update'.");
    }
    // make a local copy of the Python object so we can capture it in the lambda
    auto update = context_.attr("ensemble_update");
    // Make a callable with standardizeable signature.
    const std::string name{name_};
    auto functor = [update, name](const plugin::Matrix<double> &send,
                                  plugin::Matrix<double> *receive) {
      update(send, receive, py::str(name));
    };

    // To use a reduce function on the Python side, we need to provide it with a
    // Python buffer-like object, so we will create one here. Note: it looks
    // like the SharedData element will be useful after all.
    auto resources =
        std::make_shared<plugin::Resources>(std::move(functor));

    auto potential =
        PyRestraint<plugin::RestraintModule<plugin::LinearRestraint>>::create(
            name_, siteIndices_, params_, resources);

    auto subscriber = subscriber_;
    py::list potentialList = subscriber.attr("potential");
    potentialList.append(potential);
  };
  void addSubscriber(py::object subscriber)
  {
    assert(py::hasattr(subscriber, "potential"));
    subscriber_ = subscriber;
  };

  py::object subscriber_;
  py::object context_;
  std::vector<int> siteIndices_;

  plugin::linear_input_param_type params_;

  std::string name_;
};

/*!
 * \brief Factory function to create a new builder for use during Session
 * launch.
 *
 * \param element WorkElement provided through Context
 * \return ownership of new builder object
 */

std::unique_ptr<LinearRestraintBuilder>
createLinearBuilder(const py::object element)
{
  using std::make_unique;
  auto builder = make_unique<LinearRestraintBuilder>(element);
  return builder;
}

// Start LinearStop Restraint
class LinearStopRestraintBuilder
{
public:
  explicit LinearStopRestraintBuilder(py::object element)
  {
    name_ = py::cast<std::string>(element.attr("name"));
    assert(!name_.empty());
    // Params attribute should be a Python list
    auto parameter_dict = py::cast<py::dict>(element.attr("params"));

    assert(parameter_dict.contains("sites"));
    assert(parameter_dict.contains("target"));
    assert(parameter_dict.contains("alpha"));
    assert(parameter_dict.contains("sample_period"));
    assert(parameter_dict.contains("tolerance"));
    assert(parameter_dict.contains("logging_filename"));

    py::list sites = parameter_dict["sites"];
    for (auto &&site : sites)
    {
      siteIndices_.emplace_back(py::cast<int>(site));
    }

    auto alpha = py::cast<double>(parameter_dict["alpha"]);
    auto samplePeriod = py::cast<double>(parameter_dict["sample_period"]);
    auto tolerance = py::cast<double>(parameter_dict["tolerance"]);
    auto target = py::cast<double>(parameter_dict["target"]);
    auto logging_filename =
        py::cast<std::string>(parameter_dict["logging_filename"]);

    auto params = plugin::makeLinearStopParams(alpha, target, tolerance,
                                               samplePeriod, logging_filename);
    params_ = std::move(*params);

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
    // Need to capture Python communicator and pybind syntax in closure so
    // EnsembleResources can just call with matrix arguments.
    if (!subscriber_)
    {
      return;
    }
    else
    {
      if (!py::hasattr(subscriber_, "potential"))
        throw gmxapi::ProtocolError("Invalid subscriber");
    }
    // This can be replaced with a subscription and delayed until launch, if
    // necessary.
    if (!py::hasattr(context_, "ensemble_update"))
    {
      throw gmxapi::ProtocolError("context does not have 'ensemble_update'.");
    }
    // make a local copy of the Python object so we can capture it in the lambda
    auto update = context_.attr("ensemble_update");
    // Make a callable with standardizeable signature.
    const std::string name{name_};
    auto functor = [update, name](const plugin::Matrix<double> &send,
                                  plugin::Matrix<double> *receive) {
      update(send, receive, py::str(name));
    };

    // To use a reduce function on the Python side, we need to provide it with a
    // Python buffer-like object, so we will create one here. Note: it looks
    // like the SharedData element will be useful after all.
    auto resources =
        std::make_shared<plugin::Resources>(std::move(functor));

    auto potential =
        PyRestraint<plugin::RestraintModule<plugin::LinearStopRestraint>>::
            create(name_, siteIndices_, params_, resources);

    auto subscriber = subscriber_;
    py::list potentialList = subscriber.attr("potential");
    potentialList.append(potential);
  };
  void addSubscriber(py::object subscriber)
  {
    assert(py::hasattr(subscriber, "potential"));
    subscriber_ = subscriber;
  };

  py::object subscriber_;
  py::object context_;
  std::vector<int> siteIndices_;

  plugin::linearstop_input_param_type params_;

  std::string name_;
};

/*!
 * \brief Factory function to create a new builder for use during Session
 * launch.
 *
 * \param element WorkElement provided through Context
 * \return ownership of new builder object
 */

std::unique_ptr<LinearStopRestraintBuilder>
createLinearStopBuilder(const py::object element)
{
  using std::make_unique;
  auto builder = make_unique<LinearStopRestraintBuilder>(element);
  return builder;
}

// Start BRER Restraint
class BRERRestraintBuilder
{
public:
  explicit BRERRestraintBuilder(py::object element)
  {
    name_ = py::cast<std::string>(element.attr("name"));
    assert(!name_.empty());
    // Params attribute should be a Python list
    auto parameter_dict = py::cast<py::dict>(element.attr("params"));

    assert(parameter_dict.contains("sites"));
    assert(parameter_dict.contains("target"));
    assert(parameter_dict.contains("A"));
    assert(parameter_dict.contains("tau"));
    assert(parameter_dict.contains("num_samples"));
    assert(parameter_dict.contains("tolerance"));
    assert(parameter_dict.contains("logging_filename"));

    py::list sites = parameter_dict["sites"];
    for (auto &&site : sites)
    {
      siteIndices_.emplace_back(py::cast<int>(site));
    }

    auto A = py::cast<double>(parameter_dict["A"]);
    auto tau = py::cast<double>(parameter_dict["tau"]);
    auto nSamples = py::cast<double>(parameter_dict["num_samples"]);
    auto tolerance = py::cast<double>(parameter_dict["tolerance"]);
    auto target = py::cast<double>(parameter_dict["target"]);
    auto logging_filename =
        py::cast<std::string>(parameter_dict["logging_filename"]);

    auto params = plugin::makeBRERParams(A, tau, tolerance, target, nSamples,
                                         logging_filename);
    params_ = std::move(*params);

    assert(py::hasattr(element, "workspec"));
    auto workspec = element.attr("workspec");
    assert(py::hasattr(workspec, "_context"));
    context_ = workspec.attr("_context");
  }

  void build(py::object graph)
  {
    if (!subscriber_)
    {
      return;
    }
    else
    {
      if (!py::hasattr(subscriber_, "potential"))
        throw gmxapi::ProtocolError("Invalid subscriber");
    }
    // Temporarily subvert things to get quick-and-dirty solution for testing.
    // Need to capture Python communicator and pybind syntax in closure so
    // EnsembleResources can just call with matrix arguments.

    // This can be replaced with a subscription and delayed until launch, if
    // necessary.
    if (!py::hasattr(context_, "ensemble_update"))
    {
      throw gmxapi::ProtocolError("context does not have 'ensemble_update'.");
    }
    // make a local copy of the Python object so we can capture it in the lambda
    auto update = context_.attr("ensemble_update");
    // Make a callable with standardizeable signature.
    const std::string name{name_};
    auto functor = [update, name](const plugin::Matrix<double> &send,
                                  plugin::Matrix<double> *receive) {
      update(send, receive, py::str(name));
    };

    // To use a reduce function on the Python side, we need to provide it with a
    // Python buffer-like object, so we will create one here. Note: it looks
    // like the SharedData element will be useful after all.
    auto resources =
        std::make_shared<plugin::Resources>(std::move(functor));

    auto potential =
        PyRestraint<plugin::RestraintModule<plugin::BRERRestraint>>::create(
            name_, siteIndices_, params_, resources);

    auto subscriber = subscriber_;
    py::list potentialList = subscriber.attr("potential");
    potentialList.append(potential);
  };
  void addSubscriber(py::object subscriber)
  {
    assert(py::hasattr(subscriber, "potential"));
    subscriber_ = subscriber;
  };

  py::object subscriber_;
  py::object context_;
  std::vector<int> siteIndices_;

  plugin::BRER_input_param_type params_;

  std::string name_;
};

/*!
 * \brief Factory function to create a new builder for use during Session
 * launch.
 *
 * \param element WorkElement provided through Context
 * \return ownership of new builder object
 */

std::unique_ptr<BRERRestraintBuilder>
createBRERBuilder(const py::object element)
{
  using std::make_unique;
  auto builder = make_unique<BRERRestraintBuilder>(element);
  return builder;
}
} // end anonymous namespace

//////////////////////////////////////////////////////////////////////////////////////////////////
// The PYBIND11_MODULE block uses the pybind11 framework (ref https://github.com/pybind/pybind11 )
// to generate Python bindings to the C++ code elsewhere in this repository. A copy of the pybind11
// source code is included with this repository. Use syntax from the examples below when exposing
// a new potential, along with its builder and parameters structure. In future releases, there will
// be less code to include elsewhere, but more syntax in the block below to define and export the
// interface to a plugin. pybind11 is not required to write a GROMACS extension module or for
// compatibility with the ``gmx`` module provided with gmxapi. It is sufficient to implement the
// various protocols, C API and Python function names, but we do not provide example code
// for other Python bindings frameworks.
//////////////////////////////////////////////////////////////////////////////////////////////////

// The first argument is the name of the module when importing to Python. This should be the same as the name specified
// as the OUTPUT_NAME for the shared object library in the CMakeLists.txt file. The second argument, 'm', can be anything
// but it might as well be short since we use it to refer to aspects of the module we are defining.
PYBIND11_MODULE(md, m){
  m.doc() = "MD potentials for BRER simulation workflows."; // This will be the text of the module's docstring.

  // Matrix utility class (temporary). Borrowed from
  // http://pybind11.readthedocs.io/en/master/advanced/pycpp/numpy.html#arrays
  py::class_<plugin::Matrix<double>, std::shared_ptr<plugin::Matrix<double>>>(
      m, "Matrix", py::buffer_protocol())
      .def_buffer([](plugin::Matrix<double> &matrix) -> py::buffer_info {
        return py::buffer_info(
            matrix.data(),                           /* Pointer to buffer */
            sizeof(double),                          /* Size of one scalar */
            py::format_descriptor<double>::format(), /* Python struct-style
                                                        format descriptor */
            2,                                       /* Number of dimensions */
            {matrix.rows(), matrix.cols()},          /* Buffer dimensions */
            {sizeof(double) *
                 matrix.cols(), /* Strides (in bytes) for each index */
             sizeof(double)});
      });

  //////////////////////////////////////////////////////////////////////////
  // Begin LinearRestraint
  //
  // Define Builder to be returned from ensemble_restraint Python function
  // defined further down.
  pybind11::class_<LinearRestraintBuilder> linearBuilder(m, "LinearBuilder");
  linearBuilder.def("add_subscriber", &LinearRestraintBuilder::addSubscriber);
  linearBuilder.def("build", &LinearRestraintBuilder::build);

  // Get more concise name for the template instantiation...
  using PyLinear =
      PyRestraint<plugin::RestraintModule<plugin::LinearRestraint>>;

  // Export a Python class for our parameters struct
  py::class_<plugin::LinearRestraint::input_param_type> linearParams(
      m, "LinearRestraintParams");
  m.def("make_linear_params", &plugin::makeLinearParams);

  // API object to build.
  py::class_<PyLinear, std::shared_ptr<PyLinear>> linear(
    m,
    "LinearRestraint",
    "The BRER potential used for the production phase."
  );
  // EnsembleRestraint can only be created via builder for now.
  linear.def("bind", &PyLinear::bind, "Implement binding protocol");
  linear.def_property_readonly(
      "time",
      [](PyLinear *potential) {
        return static_cast<plugin::LinearRestraint *>(
                   potential->getRestraint().get())
            ->getTime();
      },
      "Simulation time for the last call to the force calculator.");
  linear.def_property_readonly(
      "start_time",
      [](PyLinear *potential) {
        return static_cast<plugin::LinearRestraint *>(
                   potential->getRestraint().get())
            ->getStartTime();
      },
      "Simulation time at which the plugin potential was initialized.");

  m.def(
    "linear_restraint",
    [](const py::object element) { return createLinearBuilder(element); },
    "Configure the BRER potential used for the production phase.");
  //
  // End LinearRestraint
  ///////////////////////////////////////////////////////////////////////////
  //////////////////////////////////////////////////////////////////////////
  // Begin LinearStopRestraint
  //
  // Define Builder to be returned from linear_stop_restraint Python function
  // defined further down.
  pybind11::class_<LinearStopRestraintBuilder> linearStopBuilder(
      m, "LinearStopBuilder");
  linearStopBuilder.def("add_subscriber",
                        &LinearStopRestraintBuilder::addSubscriber);
  linearStopBuilder.def("build", &LinearStopRestraintBuilder::build);

  // Get more concise name for the template instantiation...
  using PyLinearStop =
      PyRestraint<plugin::RestraintModule<plugin::LinearStopRestraint>>;

  // Export a Python class for our parameters struct
  py::class_<plugin::LinearStopRestraint::input_param_type> linearStopParams(
      m, "LinearStopRestraintParams");
  m.def("make_linearStop_params", &plugin::makeLinearStopParams);

  // API object to build.
  py::class_<PyLinearStop, std::shared_ptr<PyLinearStop>> linearStop(
      m,
      "LinearStopRestraint",
      "The BRER potential used during the convergence phase."
  );
  // EnsembleRestraint can only be created via builder for now.
  linearStop.def("bind", &PyLinearStop::bind, "Implement binding protocol");
  linearStop.def_property_readonly("stop_called", [](PyLinearStop *potential) {
    return static_cast<plugin::LinearStopRestraint *>(potential->getRestraint().get())
        ->getStopCalled();
  });
  linearStop.def_property_readonly("time", [](PyLinearStop *potential) {
    return static_cast<plugin::LinearStopRestraint *>(potential->getRestraint().get())
        ->getTime();
  });

  m.def(
    "linearstop_restraint",
    [](const py::object element) {
      return createLinearStopBuilder(element);
    },
    "Configure the BRER potential used during the convergence phase."
  );
  //
  // End LinearStopRestraint
  ///////////////////////////////////////////////////////////////////////////
  //////////////////////////////////////////////////////////////////////////
  // Begin BRERRestraint
  //
  // Define Builder to be returned from brer_restraint Python function
  // defined further down.
  pybind11::class_<BRERRestraintBuilder> brerBuilder(m, "BRERBuilder");
  brerBuilder.def("add_subscriber", &BRERRestraintBuilder::addSubscriber);
  brerBuilder.def("build", &BRERRestraintBuilder::build);

  // Get more concise name for the template instantiation...
  using PyBRER = PyRestraint<plugin::RestraintModule<plugin::BRERRestraint>>;

  // Export a Python class for our parameters struct
  py::class_<plugin::BRERRestraint::input_param_type> brerParams(
      m, "BRERRestraintParams");

  // API object to build.
  py::class_<PyBRER, std::shared_ptr<PyBRER>> brer(
    m,
    "BRERRestraint",
    "The self-tuning potential for the BRER training phase.");
  // EnsembleRestraint can only be created via builder for now.
  brer.def("bind", &PyBRER::bind, "Implement binding protocol");
  brer.def("make_brer_params", &plugin::makeBRERParams);
  brer.def_property_readonly("name", &PyBRER::name, "Get the name");
  brer.def_property_readonly("alpha", [](PyBRER *potential) {
    return static_cast<plugin::BRERRestraint *>(potential->getRestraint().get())
        ->getAlphaMax();
  });
  brer.def_property_readonly("target", [](PyBRER *potential) {
    return static_cast<plugin::BRERRestraint *>(potential->getRestraint().get())
        ->getTarget();
  });
  brer.def_property_readonly("converged", [](PyBRER *potential) {
    return static_cast<plugin::BRERRestraint *>(potential->getRestraint().get())
        ->getConverged();
    });

  m.def(
    "brer_restraint",
    [](const py::object element) { return createBRERBuilder(element); },
    "Configure the self-tuning potential for the BRER training phase.");
  //
  // End BRERRestraint
  ///////////////////////////////////////////////////////////////////////////
}
