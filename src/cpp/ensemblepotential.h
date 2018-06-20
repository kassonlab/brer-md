//
// Created by Eric Irrgang on 2/26/18.
//

#ifndef HARMONICRESTRAINT_ENSEMBLEPOTENTIAL_H
#define HARMONICRESTRAINT_ENSEMBLEPOTENTIAL_H

/*! \file
 * \brief Provide restrained ensemble MD potential for GROMACS plugin.
 *
 * The restraint implemented here uses a facility provided by gmxapi to perform averaging of some
 * array data across an ensemble of simulations. Simpler pair restraints can use less of this
 * example code.
 *
 * Contains a lot of boiler plate that is being generalized and migrate out of this file, but other
 * pair restraints can be implemented by following the example in this and ``ensemblepotential.cpp``.
 * The ``CMakeLists.txt`` file will need to be updated if you add additional source files, and
 * ``src/pythonmodule/export_plugin.cpp`` will need to be updated if you add or change the name of
 * potentials.
 */

#include <vector>
#include <array>
#include <mutex>

#include "gmxapi/gromacsfwd.h"
#include "gmxapi/md/mdmodule.h"

#include "gromacs/restraint/restraintpotential.h"
#include "gromacs/utility/real.h"

// We do not require C++14, so we have a back-ported C++14 feature for C++11 code.
#include "make_unique.h"

namespace plugin
{

// Histogram for a single restrained pair.
using PairHist = std::vector<double>;

// Stop-gap for cross-language data exchange pending SharedData implementation and inclusion of Eigen.
// Adapted from pybind docs.
template<class T>
class Matrix {
    public:
        Matrix(size_t rows, size_t cols) :
            rows_(rows),
            cols_(cols),
            data_(rows_*cols_, 0)
        {
        }

        explicit Matrix(std::vector<T>&& captured_data) :
            rows_{1},
            cols_{captured_data.size()},
            data_{std::move(captured_data)}
        {
        }

        std::vector<T> *vector() { return &data_; }
        T* data() { return data_.data(); };
        size_t rows() const { return rows_; }
        size_t cols() const { return cols_; }
    private:
        size_t rows_;
        size_t cols_;
        std::vector<T> data_;
};

// Defer implicit instantiation to ensemblepotential.cpp
extern template class Matrix<double>;

/*!
 * \brief An active handle to ensemble resources provided by the Context.
 *
 * gmxapi version 0.1.0 will provide this functionality through SessionResources.
 *
 * The semantics of holding this handle aren't determined yet, but it should be held as briefly as possible since it
 * may involve locking global resources or preventing the simulation from advancing. Basically, though, it allows the
 * Context implementation flexibility in how or where it provides services.
 */
class EnsembleResourceHandle
{
    public:
        /*!
         * \brief Ensemble reduce.
         *
         * \param send Matrices to be summed across the ensemble using Context resources.
         * \param receive destination of reduced data instead of updating internal Matrix.
         */
        void reduce(const Matrix<double> &send,
                    Matrix<double> *receive) const;

        // to be abstracted and hidden in an upcoming version...
        const std::function<void(const Matrix<double>&, Matrix<double>*)>* _reduce;
};

/*!
 * \brief Reference to workflow-level resources managed by the Context.
 *
 * Provides a connection to the higher-level workflow management with which to access resources and operations. The
 * reference provides no resources directly and we may find that it should not extend the life of a Session or Context.
 * Resources are accessed through Handle objects returned by member functions.
 *
 * gmxapi version 0.1.0 will provide this functionality through SessionResources.
 */
class EnsembleResources
{
    public:
        /*!
         * \brief Create a new resources object.
         *
         * This constructor is called by the framework during Session launch to provide the plugin
         * potential with external resources.
         *
         * \param reduce ownership of a function object providing ensemble averaging of a 2D matrix.
         */
        explicit EnsembleResources(std::function<void(const Matrix<double>&, Matrix<double>*)>&& reduce) :
            reduce_(reduce)
        {};

        /*!
         * \brief Get a handle to the resources for the current timestep.
         *
         * Objects should not keep resource handles open for longer than a single block of code.
         * calculate() and callback() functions get a handle to the resources for the current time step
         * by calling getHandle().
         *
         * \return resource handle
         *
         * In this release, the only facility provided by the resources is a function object for
         * the ensemble averaging function provided by the Context.
         */
        EnsembleResourceHandle getHandle() const;

    private:
//        std::shared_ptr<Matrix> _matrix;
        std::function<void(const Matrix<double>&, Matrix<double>*)> reduce_;
};

/*!
 * \brief Template for MDModules from restraints.
 *
 * Allows a GROMACS module to be produced easily from the provided class. Refer to
 * src/pythonmodule/export_plugin.cpp for how this template is used.
 *
 * \tparam R a class implementing the gmx::IRestraintPotential interface.
 *
 * The template type parameter should define a ``input_param_type`` member type.
 *
 * \todo move this to a template header in gmxapi
 */
template<class R>
class RestraintModule : public gmxapi::MDModule
{
    public:
        using param_t = typename R::input_param_type;

        /*!
         * \brief Construct a named restraint module.
         *
         * Objects of this type are created during Session launch, so this code really doesn't belong
         * here. The Director / Builder for the restraint uses a generic interface to pass standard
         * parameters for pair restraints: a list of sites, a (custom) parameters structure, and
         * resources provided by the Session.
         *
         * \param name
         * \param sites
         * \param params
         * \param resources
         */
        RestraintModule(std::string name,
                        std::vector<unsigned long int> sites,
                        const typename R::input_param_type& params,
                        std::shared_ptr<EnsembleResources> resources) :
            sites_{std::move(sites)},
            params_{params},
            resources_{std::move(resources)},
            name_{std::move(name)}
        {

        };

        ~RestraintModule() override = default;

        /*!
         * \brief Implement gmxapi::MDModule interface to get module name.
         *
         * name is provided during the building stage.
         * \return
         */
        // \todo make member function const
        const char *name() override
        {
                return name_.c_str();
        }

        /*!
         * \brief Implement gmxapi::MDModule interface to create a restraint for libgromacs.
         *
         * \return Ownership of a new restraint instance
         *
         * Note this interface is not stable but requires other GROMACS and gmxapi infrastructure
         * to mature before it is clear whether we will be creating a new instance or sharing ownership
         * of the object. A future version may use a std::unique_ptr.
         */
        std::shared_ptr<gmx::IRestraintPotential> getRestraint() override
        {
                auto restraint = std::make_shared<R>(sites_, params_, resources_);
                return restraint;
        }

    private:
        std::vector<unsigned long int> sites_;
        param_t params_;

        // Need to figure out if this is copyable or who owns it.
        std::shared_ptr<EnsembleResources> resources_;

        const std::string name_;
};

/*!
 * \brief A simple plain-old-data structure to hold input parameters to the potential calculations.
 *
 * This structure will be initialized when the Session is launched. It is currently populated by
 * keyword arguments processed in ``export_plugin.cpp`` in the EnsembleRestraintBuilder using the
 * helper function makeEnsembleParams() defined below.
 *
 * Restraint potentials will express their (const) input parameters by defining a structure like this and
 * providing a type alias for ``input_param_type``.
 *
 * Example:
 *
 *      class EnsembleHarmonic
 * {
 *    public:
 *        using input_param_type = ensemble_input_param_type;
 *        // ...
 * }
 *
 * In future versions, a developer will continue to define a custom structure to hold their input
 * parameters, but the meaning of the parameters and the key words with which they are expressed in
 * Python will be specified with syntax similar to the pybind11 syntax in ``export_plugin.cpp``.
 *
 */
struct ensemble_input_param_type
{
    /// distance histogram parameters
    size_t nBins{0};
    double binWidth{0.};

    /// Flat-bottom potential boundaries.
    double minDist{0};
    double maxDist{0};

    /// Experimental reference distribution.
    PairHist experimental{};

    /// Number of samples to store during each window.
    unsigned int nSamples{0};
    double samplePeriod{0};

    /// Number of windows to use for smoothing histogram updates.
    unsigned int nWindows{0};

    /// Harmonic force coefficient
    double k{0};
    /// Smoothing factor: width of Gaussian interpolation for histogram
    double sigma{0};

};

std::unique_ptr<ensemble_input_param_type>
makeEnsembleParams(size_t nbins,
                   double binWidth,
                   double minDist,
                   double maxDist,
                   const std::vector<double> &experimental,
                   unsigned int nSamples,
                   double samplePeriod,
                   unsigned int nWindows,
                   double k,
                   double sigma);

/*!
 * \brief a residue-pair bias calculator for use in restrained-ensemble simulations.
 *
 * Applies a force between two sites according to the difference between an experimentally observed
 * site pair distance distribution and the distance distribution observed earlier in the simulation
 * trajectory. The sampled distribution is averaged from the previous `nwindows` histograms from all
 * ensemble members. Each window contains a histogram populated with `nsamples` distances recorded at
 * `sample_period` step intervals.
 *
 * \internal
 * During a the window_update_period steps of a window, the potential applied is a harmonic function of
 * the difference between the sampled and experimental histograms. At the beginning of the window, this
 * difference is found and a Gaussian blur is applied.
 */
class EnsembleHarmonic
{
    public:
        using input_param_type = ensemble_input_param_type;

        /* No default constructor. Parameters must be provided. */
//        EnsembleHarmonic();

        /*!
         * \brief Constructor called by the wrapper code to produce a new instance.
         *
         * This constructor is called once per simulation per GROMACS process. Note that until
         * gmxapi 0.0.8 there is only one instance per simulation in a thread-MPI simulation.
         *
         * \param params
         */
        explicit EnsembleHarmonic(const input_param_type &params);

        /*!
         * \brief Deprecated constructor taking a parameter list.
         *
         * \param nbins
         * \param binWidth
         * \param minDist
         * \param maxDist
         * \param experimental
         * \param nSamples
         * \param samplePeriod
         * \param nWindows
         * \param k
         * \param sigma
         */
        EnsembleHarmonic(size_t nbins,
                         double binWidth,
                         double minDist,
                         double maxDist,
                         PairHist experimental,
                         unsigned int nSamples,
                         double samplePeriod,
                         unsigned int nWindows,
                         double k,
                         double sigma);

        /*!
         * \brief Evaluates the pair restraint potential.
         *
         * In parallel simulations, the gmxapi framework does not make guarantees about where or
         * how many times this function is called. It should be simple and stateless; it should not
         * update class member data (see ``ensemblepotential.cpp``. For a more controlled API hook
         * and to manage state in the object, use ``callback()``.
         *
         * \param v position of the site for which force is being calculated.
         * \param v0 reference site (other member of the pair).
         * \param t current simulation time (ps).
         * \return container for force and potential energy data.
         */
        // Implementation note for the future: If dispatching this virtual function is not fast
        // enough, the compiler may be able to better optimize a free
        // function that receives the current restraint as an argument.
        gmx::PotentialPointData calculate(gmx::Vector v,
                                          gmx::Vector v0,
                                          gmx_unused double t);

        /*!
         * \brief An update function to be called on the simulation master rank/thread periodically by the Restraint framework.
         *
         * Defining this function in a plugin potential is optional. If the function is defined,
         * the restraint framework calls this function (on the first rank only in a parallel simulation) before calling calculate().
         *
         * The callback may use resources provided by the Session in the callback to perform updates
         * to the local or global state of an ensemble of simulations. Future gmxapi releases will
         * include additional optimizations, allowing call-back frequency to be expressed, and more
         * general Session resources, as well as more flexible call signatures.
         */
        void callback(gmx::Vector v,
                      gmx::Vector v0,
                      double t,
                      const EnsembleResources &resources);

    private:
        /// Width of bins (distance) in histogram
        size_t nBins_;
        double binWidth_;

        /// Flat-bottom potential boundaries.
        double minDist_;
        double maxDist_;
        /// Smoothed historic distribution for this restraint. An element of the array of restraints in this simulation.
        // Was `hij` in earlier code.
        PairHist histogram_;
        PairHist experimental_;

        /// Number of samples to store during each window.
        unsigned int nSamples_;
        unsigned int currentSample_;
        double samplePeriod_;
        double nextSampleTime_;
        /// Accumulated list of samples during a new window.
        std::vector<double> distanceSamples_;

        /// Number of windows to use for smoothing histogram updates.
        size_t nWindows_;
        size_t currentWindow_;
        double windowStartTime_;
        double nextWindowUpdateTime_;
        /// The history of nwindows histograms for this restraint.
        std::vector<std::unique_ptr<Matrix<double>>> windows_;

        /// Harmonic force coefficient
        double k_;
        /// Smoothing factor: width of Gaussian interpolation for histogram
        double sigma_;
};

/*!
 * \brief Use EnsembleHarmonic to implement a RestraintPotential
 *
 * This is boiler plate that will be templated and moved.
 */
class EnsembleRestraint : public ::gmx::IRestraintPotential, private EnsembleHarmonic
{
    public:
        using EnsembleHarmonic::input_param_type;

        EnsembleRestraint(const std::vector<unsigned long> &sites,
                          const input_param_type &params,
                          std::shared_ptr<EnsembleResources> resources
        ) :
                EnsembleHarmonic(params),
                sites_{sites},
                resources_{std::move(resources)}
        {}

        /*!
         * \brief Implement required interface of gmx::IRestraintPotential
         *
         * \return list of configured site indices.
         *
         * \todo remove to template header
         * \todo abstraction of site references
         */
        std::vector<unsigned long int> sites() const override
        {
                return sites_;
        }

        /*!
         * \brief Implement the interface gmx::IRestraintPotential
         *
         * Dispatch to calculate() method.
         *
         * \param r1 coordinate of first site
         * \param r2 reference coordinate (second site)
         * \param t simulation time
         * \return calculated force and energy
         *
         * \todo remove to template header.
         */
        gmx::PotentialPointData evaluate(gmx::Vector r1,
                                         gmx::Vector r2,
                                         double t) override
        {
                return calculate(r1, r2, t);
        };

        /*!
         * \brief An update function to be called on the simulation master rank/thread periodically by the Restraint framework.
         *
         * Implements optional override of gmx::IRestraintPotential::update
         *
         * This boilerplate will disappear into the Restraint template in an upcoming gmxapi release.
         */
        void update(gmx::Vector v,
                    gmx::Vector v0,
                    double t) override
        {
            // Todo: use a callback period to mostly bypass this and avoid excessive mutex locking.
            callback(v,
                     v0,
                     t,
                     *resources_);
        };

        /*!
         * \brief Allow the Session to provide a resource object.
         *
         * \param resources object to take ownership of.
         */
        void setResources(std::unique_ptr<EnsembleResources>&& resources)
        {
            resources_ = std::move(resources);
        }

    private:
        std::vector<unsigned long int> sites_;
//        double callbackPeriod_;
//        double nextCallback_;
        std::shared_ptr<EnsembleResources> resources_;
};


// Important: Just declare the template instantiation here for client code.
// We will explicitly instantiate a definition in the .cpp file where the input_param_type is defined.
extern template class RestraintModule<EnsembleRestraint>;

} // end namespace plugin

#endif //HARMONICRESTRAINT_ENSEMBLEPOTENTIAL_H
