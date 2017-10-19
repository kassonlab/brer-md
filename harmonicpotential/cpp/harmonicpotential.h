//
// Created by Eric Irrgang on 10/13/17.
//

#ifndef GROMACS_HARMONICPOTENTIAL_H
#define GROMACS_HARMONICPOTENTIAL_H

#include "gromacs/pulling/restraintpotential.h"

namespace plugin
{

class Harmonic : public gmx::IRestraintPotential
{
    public:
        ~Harmonic() override;

        gmx::PotentialPointData
        evaluate(gmx::vec3<real> r1,
                 gmx::vec3<real> r2,
                 double t) override;
};

}

#endif //GROMACS_HARMONICPOTENTIAL_H
