//
// Created by Eric Irrgang on 10/13/17.
//

#include "harmonicpotential.h"
#include <cmath>

#include <array>

namespace plugin
{

gmx::PotentialPointData Harmonic::calculate(gmx::Vector v,
                                   gmx::Vector v0,
                                   gmx_unused double t)
{

    auto rdiff = v - v0;
    const auto Rsquared = dot(rdiff, rdiff);
    const auto R = sqrt(Rsquared);
    // TODO: find appropriate math header and namespace

    // Potential energy is 0.5 * k * (norm(r1) - R0)**2
    // Force in direction of r1 is -k * (norm(r1) - R0) * r1/norm(r1)
    gmx::PotentialPointData output;
    // output.energy = real(0.5) * k * (norm(r1) - R0) * (norm(r1) - R0);
    output.energy = real(0.5) * k * (Rsquared + (-2*R*R0) + R0*R0);
    // Direction of force is ill-defined when v == v0
    if (R != 0)
    {
        // F = -k * (1.0 - R0/norm(r1)) * r1
        output.force = k * (double(R0)/R - 1.0)*rdiff;
    }

//    history.emplace_back(magnitude - R0);
    return output;
}

gmx::PotentialPointData HarmonicRestraint::evaluate(gmx::Vector r1,
                                                 gmx::Vector r2,
                                                 double t)
{
    return calculate(r1, r2, t);
}

std::vector<unsigned long int> HarmonicRestraint::sites() const
{
    return {site1_, site2_};
}

} // end namespace plugin
