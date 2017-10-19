//
// Created by Eric Irrgang on 10/13/17.
//

#include <cmath>
#include "harmonicpotential.h"

namespace plugin
{

Harmonic::~Harmonic() = default;

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
gmx::vec3<real> Harmonic::calculateForce(gmx::vec3<real> v,
                                         gmx::vec3<real> v0)
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

    // Direction of force is ill-defined when v == v0
    //real magnitude = 0;
    gmx::vec3<real> force{};
    if (R != 0)
    {
        // Force in direction of r1 is -k * (norm(r1) - R0) * r1/norm(r1)
        // F = -k * (1.0 - R0/norm(r1)) * r1
        force = k * (double(R0)/norm(r1) - 1.0) * r1;
    }

    return force;
}
} // end namespace plugin
