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
            Harmonic{0.0, 0.0}
        {};

        // Allow easier automatic generation of bindings.
        struct input_param_type {
            float whateverIwant;
        };

        struct output_type
        {};

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
        gmx::PotentialPointData calculate(gmx::Vector v,
                                          gmx::Vector v0,
                                          gmx_unused double t);

        // Cache of historical distance data. Not thread safe
//        std::vector<float> history{};

        // The class will either be inherited as a mix-in or inherit a CRTP base class. Either way, it probably needs proper virtual destructor management.
        virtual ~Harmonic() {
//            for (auto&& distance: history)
//            {
//                std::cout << distance << "\n";
//            }
//            std::cout << std::endl;
        }

    private:
        // set equilibrium separation distance
        // TODO: be clearer about units
        real R0;
        // set spring constant
        // TODO: be clearer about units
        real k;
};

// implement IRestraintPotential in terms of Harmonic
// To be templated and moved.
class HarmonicRestraint : public ::gmx::IRestraintPotential, private Harmonic
{
    public:
        HarmonicRestraint(unsigned long int site1,
                          unsigned long int site2,
                          real R0,
                          real k) :
            Harmonic{R0, k},
            site1_{site1},
            site2_{site2}
        {};

        std::vector<unsigned long int> sites() const override;

        // \todo provide this facility automatically
        gmx::PotentialPointData evaluate(gmx::Vector r1,
                                         gmx::Vector r2,
                                         double t) override;

    private:
        unsigned long int site1_{0};
        unsigned long int site2_{0};
};

class HarmonicModule : public gmxapi::MDModule
{
    public:
        using param_t = Harmonic::input_param_type;

        HarmonicModule(unsigned long int site1,
                       unsigned long int site2,
                       real R0,
                       real k)
        {
            site1_ = site1;
            site2_ = site2;
            R0_ = R0;
            k_ = k;
        }


        const char *name() override
        {
            return "HarmonicModule";
        }

        /*!
         * \brief implement gmxapi::MDModule::getRestraint()
         *
         * \return Handle to configured library object.
         */
        std::shared_ptr<gmx::IRestraintPotential> getRestraint() override
        {
            auto restraint = std::make_shared<HarmonicRestraint>(site1_, site2_, R0_, k_);
            return restraint;
        }

        /*!
         * \brief Set restraint parameters.
         *
         * \todo generalize this
         * \param site1
         * \param site2
         * \param k
         * \param R0
         */
        void setParams(unsigned long int site1,
                        unsigned long int site2,
                        real R0,
                        real k)
        {
            site1_ = site1;
            site2_ = site2;
            R0_ = R0;
            k_ = k;
        }

    private:
        unsigned long int site1_;
        unsigned long int site2_;
        real R0_;
        real k_;
};

} // end namespace plugin

#endif //GROMACS_HARMONICPOTENTIAL_H
