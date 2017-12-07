//
// Created by Eric Irrgang on 11/9/17.
//

#include "testingconfiguration.h"

#include <memory>

#include "gmxapi/context.h"
#include "gmxapi/md/mdmodule.h"
#include "gmxapi/md.h"
#include "gmxapi/session.h"
#include "gmxapi/status.h"
#include "gmxapi/system.h"

#include "gromacs/math/vectypes.h"
#include "gromacs/restraint/restraintpotential.h"
#include "gromacs/utility/classhelpers.h"
#include "gromacs/utility/arrayref.h"

#include <gtest/gtest.h>

namespace
{

const auto filename = plugin::testing::sample_tprfilename;

class NullRestraint : public gmx::IRestraintPotential
{
    public:
        gmx::PotentialPointData evaluate(gmx::Vector r1,
                                         gmx::Vector r2,
                                         double t) override
        {
            return {};
        }

        std::array<unsigned long, 2> sites() const override
        {
            return {0,0};
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
            auto restraint = std::make_shared<NullRestraint>();
            return restraint;
        }
};


TEST(ApiRestraint, MdAndPlugin)
{

    {
        auto system = gmxapi::fromTprFile(filename);
        std::shared_ptr<gmxapi::Context> context = gmxapi::defaultContext();

        auto module = std::make_shared<SimpleApiModule>();
        system->setRestraint(module);

        auto session = system->launch(context);

        gmxapi::Status status;
        ASSERT_NO_THROW(status = session->run());
//        ASSERT_TRUE(module->force_called() > 0);
//        ASSERT_NO_THROW(session->run(1000));
        ASSERT_TRUE(status.success());
    }

}

} // end anonymous namespace
