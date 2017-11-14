//
// Created by Eric Irrgang on 10/13/17.
//

#include "testingconfiguration.h"

#include <iostream>
#include <memory>

#include "harmonicpotential.h"

#include "gmxapi/context.h"
#include "gmxapi/runner.h"
#include "gmxapi/md/mdmodule.h"
#include "gmxapi/md/runnerstate.h"
#include "gmxapi/md.h"
#include "gmxapi/gmxapi.h"
#include "gmxapi/status.h"
#include "gmxapi/system.h"

#include "gromacs/math/vectypes.h"
#include "gromacs/restraint/restraintpotential.h"
#include "gromacs/restraint/vectortype.h"
#include "gromacs/utility/classhelpers.h"
#include "gromacs/utility/arrayref.h"

#include <gtest/gtest.h>

namespace {

using gmx::detail::vec3;

std::ostream& operator<<(std::ostream& stream, const gmx::Vector& vec)
{
    stream << "(" << vec.x << "," << vec.y << "," << vec.z << ")";
    return stream;
}

const auto filename = plugin::testing::sample_tprfilename;


template<class T>
class SimpleRestraint : public ::gmx::IRestraintPotential, private T
{
    public:
        gmx::PotentialPointData evaluate(gmx::Vector r1,
                                         gmx::Vector r2,
                                         double t) override
        {
            std::cout << "time: " << t << ": |r2 - r1| = |" << r2 << " -  " << r1 << "| = |" << r2 - r1 << "| = " << norm(r2 - r1) << "\n";
            return T::calculate(r1, r2, t);
        }
};

class SimpleApiModule : public gmxapi::MDModule
{
    public:
        const char *name() override
        {
            return "NullApiModule";
        }

        std::shared_ptr<gmx::IRestraintPotential> getRestraint() override
        {
            auto restraint = std::make_shared<SimpleRestraint<::plugin::Harmonic>>();
            return restraint;
        }
};


TEST(HarmonicPotentialPlugin, Build)
{
    ASSERT_TRUE(true);
    ASSERT_FALSE(false);

    plugin::Harmonic puller;
}

TEST(HarmonicPotentialPlugin, ForceCalc)
{
    constexpr vec3<real> zerovec = gmx::detail::make_vec3<real>(0, 0, 0);
    // define some unit vectors
    const vec3<real> e1{real(1), real(0), real(0)};
    const vec3<real> e2{real(0), real(1), real(0)};
    const vec3<real> e3{real(0), real(0), real(1)};

    const real R0{1.0};
    const real k{1.0};

    // store temporary values long enough for inspection
    vec3<real> force{};

    plugin::Harmonic puller{R0, k};

    // When input vectors are equal, output vector is meaningless and magnitude is set to zero.
    auto calculateForce = [&puller](const vec3<real>& a, const vec3<real>& b) { return puller.calculate(a,b,0).force; };
    ASSERT_EQ(real(0.0), norm(calculateForce(e1, e1)));

    // Default equilibrium distance is 1.0, so force should be zero when norm(r12) == 1.0.
    force = calculateForce(zerovec, e1);
    ASSERT_EQ(zerovec, force) << " where force is (" << force.x << ", " << force.y << ", " << force.z << ")\n";

    force = calculateForce(e1, zerovec);
    ASSERT_EQ(zerovec, force) << " where force is (" << force.x << ", " << force.y << ", " << force.z << ")\n";

    force = calculateForce(e1, 2*e1);
    ASSERT_EQ(zerovec, force) << " where force is (" << force.x << ", " << force.y << ", " << force.z << ")\n";

    // -kx should give vector (1, 0, 0) when vector r1 == r2 - (2, 0, 0)
    force = calculateForce(-2*e1, zerovec);
    ASSERT_EQ(real(1), force.x);
    force = calculateForce(-2*e1, zerovec);
    ASSERT_EQ(e1, force) << " where force is (" << force.x << ", " << force.y << ", " << force.z << ")\n";

    // -kx should give vector (-2, 0, 0) when vector r1 == r2 + (2, 0, 0)
    force = calculateForce(2*e1, -e1);
    ASSERT_EQ(-2*e1, force) << " where force is (" << force.x << ", " << force.y << ", " << force.z << ")\n";
}

TEST(HarmonicPotentialPlugin, Bind)
{

    {
        auto system = gmxapi::fromTprFile(filename);
        std::shared_ptr<gmxapi::Context> context = gmxapi::defaultContext();
        auto runner = system->runner();

        auto session = runner->initialize(context);

        auto module = std::make_shared<plugin::HarmonicModule>();
        session->setRestraint(module);

        gmxapi::Status status;
        ASSERT_NO_THROW(status = session->run());
//        ASSERT_TRUE(module->force_called() > 0);
//        ASSERT_NO_THROW(session->run(1000));
        ASSERT_TRUE(status.success());
    }

}

} // end anonymous namespace

int main(int argc, char* argv[])
{
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
