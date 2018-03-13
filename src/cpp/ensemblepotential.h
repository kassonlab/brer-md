//
// Created by Eric Irrgang on 2/26/18.
//

#ifndef HARMONICRESTRAINT_ENSEMBLEPOTENTIAL_H
#define HARMONICRESTRAINT_ENSEMBLEPOTENTIAL_H

#include <vector>
#include <array>

#include "gmxapi/gromacsfwd.h"
#include "gmxapi/md/mdmodule.h"

#include "gromacs/restraint/restraintpotential.h"
#include "gromacs/utility/real.h"

namespace plugin
{

/*!
 * \brief Template for MDModules from restraints.
 *
 * \tparam R a class implementing the gmx::IRestraintPotential interface.
 */
template<class R>
class RestraintModule : public gmxapi::MDModule // consider names
{
    public:
        using param_t = typename R::input_param_type;

        const char *name() override
        {
                return "RestraintModule";
        }

        std::shared_ptr<gmx::IRestraintPotential> getRestraint() override
        {
                auto restraint = std::make_shared<R>(_site1, _site2, _params);
                return restraint;
        }

        void setParams(unsigned long int site1,
                       unsigned long int site2,
                       const typename R::input_param_type& params)
        {
                _params = params;
        }

    private:
        unsigned long int _site1{0};
        unsigned long int _site2{0};
        param_t _params;
};

// Histogram for a single restrained pair.
using PairHist = std::vector<double>;

/*!
 * \brief An active handle to ensemble resources provided by the Context.
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
         * For first draft, assume an all-to-all sum.
         * \tparam T
         * \param data
         */
        template<typename T>
        void reduce(const std::vector<T>& input, std::vector<T>* output);

        /*!
         * \brief Apply a function to each input and accumulate the output.
         *
         * \tparam I Iterable.
         * \tparam T Output type.
         * \param iterable iterable object to produce inputs to function
         * \param output structure that should be present and up-to-date on all ranks.
         * \param function map each input in iterable through this function to accumulate output.
         */
        template<typename I, typename T>
        void map_reduce(const I& iterable, T* output, void (*function)(double, const PairHist&, PairHist*));
};

/*!
 * \brief Reference to workflow-level resources managed by the Context.
 *
 * Provides a connection to the higher-level workflow management with which to access resources and operations. The
 * reference provides no resources directly and we may find that it should not extend the life of a Session or Context.
 * Resources are accessed through Handle objects returned by member functions.
 */
class EnsembleResources
{
    public:
        EnsembleResourceHandle getHandle();
};

struct ensemble_input_param_type
{
    /// Width of bins (distance) in histogram
    size_t nbins{0};
    /// Histogram boundaries.
    double min_dist{0};
    double max_dist{0};
    PairHist experimental{};

    /// Number of samples to store during each window.
    unsigned int nsamples{0};
    double sample_period{0};

    /// Number of windows to use for smoothing histogram updates.
    unsigned int nwindows{0};
    double window_update_period{0};

    /// Harmonic force coefficient
    double K{0};
    /// Smoothing factor: width of Gaussian interpolation for histogram
    double sigma{0};

};


std::unique_ptr<ensemble_input_param_type>
make_ensemble_params(size_t nbins,
                     double min_dist,
                     double max_dist,
                     const std::vector<double>& experimental,
                     unsigned int nsamples,
                     double sample_period,
                     unsigned int nwindows,
                     double window_update_period,
                     double K,
                     double sigma)
{
    auto params = std::make_unique<ensemble_input_param_type>();
    params->nbins = nbins;
    params->min_dist = min_dist;
    params->max_dist = max_dist;
    params->experimental = experimental;
    params->nsamples = nsamples;
    params->sample_period = sample_period;
    params->nwindows = nwindows;
    params->window_update_period = window_update_period;
    params->K = K;
    params->sigma = sigma;

    return params;
};

/*!
 * \brief a Roux-like pair restraint calculator for application across an ensemble of trajectories.
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

//        EnsembleHarmonic();

        explicit EnsembleHarmonic(const input_param_type &params);

        EnsembleHarmonic(size_t nbins,
                                 double min_dist,
                                 double max_dist,
                                 unsigned int nsamples,
                                 double sample_period,
                                 unsigned int nwindows,
                                 double window_update_period,
                                 double K,
                                 double sigma);

        // If dispatching this virtual function is not fast enough, the compiler may be able to better optimize a free
        // function that receives the current restraint as an argument.
        gmx::PotentialPointData calculate(gmx::Vector v,
                                          gmx::Vector v0,
                                          gmx_unused double t);

    private:
        /// Width of bins (distance) in histogram
        size_t _nbins;
        /// Histogram boundaries.
        double _min_dist;
        double _max_dist;
        double _binWidth;
        /// Smoothed historic distribution for this restraint. An element of the array of restraints in this simulation.
        // Was `hij` in earlier code.
        std::unique_ptr<PairHist> _histogram;
        std::unique_ptr<PairHist> _experimental;

        /// Number of samples to store during each window.
        unsigned int _nsamples;
        unsigned int _current_sample;
        double _sample_period;
        double _next_sample_time;
        /// Accumulated list of samples during a new window.
        std::vector<double> _distance_samples;

        /// Number of windows to use for smoothing histogram updates.
        size_t _nwindows;
        size_t _current_window;
        double _window_update_period;
        double _next_window_update_time;
        /// The history of nwindows histograms for this restraint.
        std::vector<std::unique_ptr<PairHist>> _windows;

        /// Harmonic force coefficient
        double _K;
        /// Smoothing factor: width of Gaussian interpolation for histogram
        double _sigma;

        /// Ensemble resources
        EnsembleResources _ensemble;
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

        EnsembleRestraint(unsigned long int site1,
                          unsigned long int site2,
                          const input_param_type& params) :
                EnsembleHarmonic(params),
                _site1{site1},
                _site2{site2}
        {}

        std::array<unsigned long int, 2> sites() const override
        {
                return {};
        }

        gmx::PotentialPointData evaluate(gmx::Vector r1,
                                         gmx::Vector r2,
                                         double t) override
        {
                return calculate(r1, r2, t);
        };

    private:
        unsigned long int _site1{0};
        unsigned long int _site2{0};
};


// Just declare the template instantiation here for client code.
// We will explicitly instantiate a definition in the .cpp file where the input_param_type is defined.
extern template class RestraintModule<EnsembleRestraint>;

} // end namespace plugin

#endif //HARMONICRESTRAINT_ENSEMBLEPOTENTIAL_H
