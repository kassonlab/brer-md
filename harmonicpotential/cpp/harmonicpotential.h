//
// Created by Eric Irrgang on 10/13/17.
//

#ifndef GROMACS_HARMONICPOTENTIAL_H
#define GROMACS_HARMONICPOTENTIAL_H

#include "gromacs/pulling/restraintpotential.h"

namespace plugin
{

class Harmonic : public gmx::RestraintPotential
{
    public:
        ~Harmonic() override;

        gmx::vec3<real> calculateForce(gmx::vec3<real> r1,
                                       gmx::vec3<real> r2) override;
};

}

#endif //GROMACS_HARMONICPOTENTIAL_H
