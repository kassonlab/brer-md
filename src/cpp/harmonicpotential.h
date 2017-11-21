//
// Created by Eric Irrgang on 10/13/17.
//

#ifndef GROMACS_HARMONICPOTENTIAL_H
#define GROMACS_HARMONICPOTENTIAL_H

#include <iostream>

#include "gmxapi/gromacsfwd.h"
#include "gmxapi/md/mdmodule.h"

#include "gromacs/restraint/restraintpotential.h"
#include "gromacs/utility/real.h"

namespace plugin
{

class Harmonic
{
    public:
        Harmonic(real equilibrium, real springconstant) :
            R0{equilibrium},
            k{springconstant}
        {};

        Harmonic() :
            Harmonic{2.0, 100.0}
        {};

        // Allow easier automatic generation of bindings.
        struct input_param_type {
            float whateverIwant;
        };

        struct output_type
        {};

        gmx::PotentialPointData calculate(gmx::Vector v,
                                          gmx::Vector v0,
                                          gmx_unused double t);

        std::vector<float> history{};

        // The class will either be inherited as a mix-in or inherit a CRTP base class. Either way, it probably needs proper virtual destructor management.
        virtual ~Harmonic() {
            for (auto&& distance: history)
            {
                std::cout << distance << "\n";
            }
            std::cout << std::endl;
        }

    private:
        // set equilibrium separation distance
        // TODO: be clearer about units
        real R0;
        // set spring constant
        // TODO: be clearer about units
        real k;
};

class HarmonicRestraint : public ::gmx::IRestraintPotential, private Harmonic
{
    public:
        gmx::PotentialPointData evaluate(gmx::Vector r1,
                                         gmx::Vector r2,
                                         double t) override;
};

class HarmonicModule : public gmxapi::MDModule
{
    public:
        const char *name() override
        {
            return "HarmonicModule";
        }

        std::shared_ptr<gmx::IRestraintPotential> getRestraint() override
        {
            auto restraint = std::make_shared<HarmonicRestraint>();
            return restraint;
        }
};

} // end namespace plugin

#endif //GROMACS_HARMONICPOTENTIAL_H
