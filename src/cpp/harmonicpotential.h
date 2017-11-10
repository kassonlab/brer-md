//
// Created by Eric Irrgang on 10/13/17.
//

#ifndef GROMACS_HARMONICPOTENTIAL_H
#define GROMACS_HARMONICPOTENTIAL_H

#include "gromacs/restraint/restraintpotential.h"
#include "gromacs/utility/real.h"
#include "gmxapi/gromacsfwd.h"

namespace plugin
{

class Harmonic
{
    public:

        // Allow easier automatic generation of bindings.
        struct input_param_type {
            float whateverIwant;
        };

        struct output_type
        {};

        gmx::PotentialPointData calculate(gmx::Vector v,
                                          gmx::Vector v0,
                                          gmx_unused double t);

};


//class HarmonicAlt : public gmx::RestraintPotential<HarmonicAlt>
// We will "mix-in from below" when we instantiate a template to register this class's functionality, so no inheritance here.
class HarmonicAlt
{
    public:

        // Allow easier automatic generation of bindings.
        struct input_param_type {
            float whateverIwant;
        };

        struct output_type
        {};

        // Can/should we inherit an output type from the CRTP base class?
        // Can/should we use static_assert in default templates to try to provide more user-friendly debugging help?

//        PotentialWithScalarForce calculate();

//        PotentialWithVectorForce calculate();

//        PotentialData<HarmonicAlt> calculate(real distance);
        // Need to return this.
        gmx::PotentialPointData calculate(real distance)
        {
            real force{};
            real energy{};

            // Probably most intuitive
            // Setters force the user to explicitly _choose_ if they think they don't need energy.
            // Otherwise, directly accessing fields could be fine.
            gmx::PotentialPointData returnValue;

            returnValue.energy = energy;
//            returnValue.force = force;

//            returnValue.setForce(force);
//            returnValue.setEnergy(energy);

//            Force calculateForce = force;
//            Energy calculatedEnergy = energy;

//            gmx::PotentialPointData returnValue(force, energy);
            return returnValue;
        };

};


} // end namespace plugin

#endif //GROMACS_HARMONICPOTENTIAL_H
