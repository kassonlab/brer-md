//
// Created by Eric Irrgang on 3/24/18.
//

#include "testingconfiguration.h"

#include <iostream>
#include <vector>

#include "ensemblepotential.h"

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

TEST(EnsembleBoundingPotentialPlugin, ForceCalc)
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

    // Get a dummy EnsembleResources. We aren't testing that here.
    auto dummyFunc = [](const plugin::Matrix<double>&, plugin::Matrix<double>*){
        return;};
    auto resource = std::make_shared<plugin::EnsembleResources>(dummyFunc);

    // Define a reference distribution with a triangular peak at the 1.0 bin.
    const std::vector<double>
        experimental{{0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1}};


    plugin::EnsembleHarmonic restraint{10, // nbins
                                       1.0, // binWidth
                                       5.0, // minDist
                                       5.0, // maxDist
                                       experimental, // experimental reference histogram
                                       1, // nSamples
                                       0.001, // samplePeriod
                                       1, // nWindows
                                       100., // k
                                       1.0 // sigma
    };

    auto calculateForce =
        [&restraint](const vec3<real>& a, const vec3<real>& b, double t)
        {
            return restraint.calculate(a,b,t).force;
        };

    // Atoms should be driven towards each other when above maxDist and and away under minDist.
    force = calculateForce(e1, 3*e1, 0.001);
    ASSERT_LT(force.x, 0.) << " where force is (" << force.x << ", " << force.y << ", " << force.z << ")\n";
    force = calculateForce(e1, 7*e1, 0.001);
    ASSERT_GT(force.x, 0.) << " where force is (" << force.x << ", " << force.y << ", " << force.z << ")\n";
}

} // end anonymous namespace

int main(int argc, char* argv[])
{
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
