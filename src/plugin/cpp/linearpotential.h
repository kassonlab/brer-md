#ifndef GROMACS_LINEARPOTENTIAL_H
#define GROMACS_LINEARPOTENTIAL_H

#include <array>
#include <iostream>
#include <memory>
#include <mutex>
#include <vector>

#include "gmxapi/gromacsfwd.h"
#include "gmxapi/md/mdmodule.h"
#include "gmxapi/session.h"

#include "gromacs/restraint/restraintpotential.h"
#include "gromacs/utility/real.h"

#include "sessionresources.h"

namespace plugin {

struct linear_input_param_type {
  double alpha{0};
  double target{0};
  double samplePeriod{0};
  std::string logging_filename{""};
};

std::unique_ptr<linear_input_param_type>
makeLinearParams(double alpha, double target, double samplePeriod,
                 std::string logging_filename);

class Linear {
public:
  using input_param_type = linear_input_param_type;

  explicit Linear(const input_param_type &params);

  Linear(double alpha, double target, double samplePeriod,
         std::string filename);

  gmx::PotentialPointData calculate(gmx::Vector v, gmx::Vector v0,
                                    double t);

  void writeparameters(double t, const double R);

  void callback(gmx::Vector v, gmx::Vector v0, double t,
                const Resources &resources);

  double getTime() const { return time_; }
  double getStartTime() const { return startTime_; }

private:
  bool initialized_{false};
  double time_{0};

  double alpha_;

  /// target distance
  double target_;

  // Sample interval
  double samplePeriod_;
  double startTime_{0};
  double nextSampleTime_{0};
  unsigned int currentSample_{0};

  std::string logging_filename_;
  std::unique_ptr<RAIIFile> logging_file_{nullptr};
};

class LinearRestraint : public ::gmx::IRestraintPotential, private Linear {
public:
  using Linear::input_param_type;

  LinearRestraint(const std::vector<int> &sites, const input_param_type &params,
                  std::shared_ptr<Resources> resources)
      : Linear(params), sites_{sites}, resources_{std::move(resources)} {}

  std::vector<int> sites() const override { return sites_; }
  ~LinearRestraint() override = default;

  gmx::PotentialPointData evaluate(gmx::Vector r1, gmx::Vector r2,
                                   double t) override {
    return calculate(r1, r2, t);
  };

  void update(gmx::Vector v, gmx::Vector v0, double t) override {
    callback(v, v0, t, *resources_);
  };

  void bindSession(gmxapi::SessionResources *session) override {
    resources_->setSession(session);
  }

  void setResources(std::unique_ptr<Resources> &&resources) {
    resources_ = std::move(resources);
  }

  using Linear::getTime;
  using Linear::getStartTime;

private:
  std::vector<int> sites_;
  std::shared_ptr<Resources> resources_;
};

extern template class RestraintModule<LinearRestraint>;
} // namespace plugin

#endif // GROMACS_LINEARPOTENTIAL_H
