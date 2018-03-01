//
// Created by Eric Irrgang on 2/26/18.
//

#ifndef HARMONICRESTRAINT_ENSEMBLEPOTENTIAL_H
#define HARMONICRESTRAINT_ENSEMBLEPOTENTIAL_H

#include <vector>

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
class RestraintModule : public gmxapi::MDModule
{
    public:
        using param_t = typename R::input_param_type;

    private:
        param_t _params;
};


// Histogram for a single restrained pair.
using PairHist = std::vector<double>;


/*!
 * \brief a Roux-like pair restraint calculator for application across an ensemble of trajectories.
 */
class EnsembleHarmonic
{
    public:
        EnsembleHarmonic();

        // If dispatching this virtual function is not fast enough, the compiler may be able to better optimize a free
        // function that receives the current restraint as an argument.
        gmx::PotentialPointData calculate(gmx::Vector v,
                                          gmx::Vector v0,
                                          gmx_unused double t);

    private:
        /// Historic distribution for this restraint. An element of the array of restraints in this simulation.
        // Was `hij` in earlier code.
        PairHist _histogram;

        /// Width of bins (distance) in histogram
        double _binWidth;
        /// Harmonic force coefficient
        double _K;
        /// Smoothing factor: width of Gaussian interpolation for histogram
        double _sigma;

        /// Histogram boundaries.
        double _max_dist;
        double _min_dist;
};

/*!
 * \brief Use EnsembleHarmonic to implement a RestraintPotential
 *
 * This is boiler plate that will be templated and moved.
 */
class EnsembleRestraint : public ::gmx::IRestraintPotential, private EnsembleHarmonic
{
    public:
        EnsembleRestraint();

        struct input_param_type{};
};


// Just declare the template instantiation here for client code.
// We will explicitly instantiate a definition in the .cpp file where the input_param_type is defined.
extern template class RestraintModule<EnsembleRestraint>;

} // end namespace plugin

#endif //HARMONICRESTRAINT_ENSEMBLEPOTENTIAL_H
