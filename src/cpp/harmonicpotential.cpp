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
    // Our convention is to think of the second coordinate as a reference location
    // such that we consider the relative location of the site at v
    // and find the force that should be applied. For example, think
    // of a single particle harmonically bound to a site at the origin
    // and let v0 == {0,0,0}. In the convention of the PairRestraint,
    // though, we assume the reference coordinate is also a site to which
    // we will apply and equal and opposite force. In the long run,
    // considering domain decomposition, it might make more sense to
    // explicitly evaluate each site in a pair with the other as a reference.
    const auto rdiff = v - v0;
    const auto Rsquared = dot(rdiff,
                              rdiff);
    const auto R = sqrt(Rsquared);
    // TODO: find appropriate math header and namespace

    // Potential energy is 0.5 * k * (norm(r1) - R0)**2
    // Force in direction of r1 is -k * (norm(r1) - R0) * r1/norm(r1)
    gmx::PotentialPointData output;
    // output.energy = real(0.5) * k * (norm(r1) - R0) * (norm(r1) - R0);
    output.energy = real(0.5) * k * (Rsquared + (-2 * R * R0) + R0 * R0);
    // Direction of force is ill-defined when v == v0
    if (R != 0)
    {
        // F = -k * (1.0 - R0/norm(r1)) * r1
        output.force = k * (double(R0) / R - 1.0) * rdiff;
    }

    return output;
}

gmx::PotentialPointData HarmonicRestraint::evaluate(gmx::Vector r1,
                                                    gmx::Vector r2,
                                                    double t)
{
    // Use calculate() method inherited from HarmonicPotential
    return calculate(r1,
                     r2,
                     t);
}

std::vector<unsigned long int> HarmonicRestraint::sites() const
{
    return {site1_, site2_};
}

} // end namespace plugin
