//
// Created by Eric Irrgang on 10/13/17.
//

#include <cmath>
#include "harmonicpotential.h"

namespace plugin
{

/*!
 * \brief Calculate harmonic force on particle at position v in reference to position v0.
 *
 * \param v position at which to evaluate force
 * \param v0 position of harmonic bond reference
 * \return F = -k ((v - v0)/|v - v0| - R0);
 *
 * R0 == 1.0 is the equilibrium distance in the harmonic potential.
 * k == 1.0 is the spring constant.
 *
 * In the case of a pair of harmonically bonded particles, the force on particle i is evaluated with particle j as
 * the reference point with
 * \code
 * auto force = calculateForce(r_i, r_j);
 * \endcode
 *
 * The force on particle j is the opposite as the force vector for particle i. E.g.
 * \code
 * assert(-1 * force, calculateForce(r_j, r_i));
 * \endcode
 */
gmx::PotentialPointData Harmonic::calculate(gmx::Vector v,
                                   gmx::Vector v0,
                                   gmx_unused double t)
{
    // set equilibrium separation distance
    // TODO: be clearer about units
    real R0{1.0};
    // set spring constant
    // TODO: be clearer about units
    real k{1.0};
    auto r1 = v - v0;
    // TODO: find appropriate math header and namespace

    auto R = sqrt(dot(r1, r1));

    gmx::PotentialPointData output;
    // Potential energy is 0.5 * k * (norm(r1) - R0)**2
    // Force in direction of r1 is -k * (norm(r1) - R0) * r1/norm(r1)
    const auto r1squared = dot(r1, r1);
    const auto magnitude = sqrt(r1squared);
    // output.energy = real(0.5) * k * (norm(r1) - R0) * (norm(r1) - R0);
    output.energy = real(0.5) * k * (r1squared + (-2*magnitude*R0) + R0*R0);
    // Direction of force is ill-defined when v == v0
    if (R != 0)
    {
        // F = -k * (1.0 - R0/norm(r1)) * r1
        output.force = k * (double(R0)/magnitude - 1.0)*r1;
    }

    return output;
}

} // end namespace plugin
