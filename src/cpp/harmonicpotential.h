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
        HarmonicRestraint(unsigned long int site1,
                          unsigned long int site2,
                          real R0,
                          real k) :
            Harmonic{R0, k},
            site1_{site1},
            site2_{site2}
        {};

        std::array<unsigned long, 2> sites() const override;

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
        unsigned long int site1_{0};
        unsigned long int site2_{0};
        real R0_{0};
        real k_{0};
};

} // end namespace plugin

#endif //GROMACS_HARMONICPOTENTIAL_H
