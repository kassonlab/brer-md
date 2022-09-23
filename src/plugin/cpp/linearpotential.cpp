#include "gmxapi/md/mdsignals.h"
#include "gmxapi/session.h"
#include "linearpotential.h"

#include <cmath>

#include <vector>

namespace plugin {
std::unique_ptr<linear_input_param_type>
makeLinearParams(double alpha, double target, double samplePeriod,
                 std::string logging_filename) {
  using std::make_unique;
  auto params = make_unique<linear_input_param_type>();
  params->alpha = alpha;
  params->target = target;
  params->samplePeriod = samplePeriod;
  params->logging_filename = logging_filename;
  return params;
};
Linear::Linear(double alpha, double target, double samplePeriod,
               std::string logging_filename)
    : alpha_{alpha}, target_{target}, samplePeriod_{samplePeriod},
      logging_filename_{logging_filename} {};

Linear::Linear(const input_param_type &params)
    : Linear(params.alpha, params.target, params.samplePeriod,
             params.logging_filename) {}

void Linear::writeparameters(double t, const double R) {
  if (logging_file_) {
    fprintf(logging_file_->fh(), "%f\t%f\t%f\t%f\n", t, R, target_, alpha_);
    fflush(logging_file_->fh());
  }
}

void Linear::callback(gmx::Vector v, gmx::Vector v0, double t,
                      const Resources &resources) {

  // Update distance
  auto rdiff = v - v0;
  const auto Rsquared = dot(rdiff, rdiff);
  const auto R = sqrt(Rsquared);

  if (!initialized_) {
    std::cout << "Initializing the Linear restraint" << std::endl;
    startTime_ = t;
    nextSampleTime_ = startTime_ + samplePeriod_;
    logging_file_ =
        std::make_unique<RAIIFile>(logging_filename_.c_str(), "a");
    if (logging_file_) {
      fprintf(logging_file_->fh(), "time\tR\ttarget\talpha\n");
      writeparameters(t, R);
    }
    initialized_ = true;
  }

  // If the simulation has not converged, keep running and log
  if (t >= nextSampleTime_) {
    writeparameters(t, R);
    currentSample_++;
    nextSampleTime_ = (currentSample_ + 1) * samplePeriod_ + startTime_;
  }
}

gmx::PotentialPointData Linear::calculate(gmx::Vector v, gmx::Vector v0,
                                          double t) {
  // Our convention is to calculate the force that will be applied to v.
  // An equal and opposite force is applied to v0.
  time_ = t;
  auto rdiff = v - v0;
  const auto Rsquared = dot(rdiff, rdiff);
  const auto R = sqrt(Rsquared);

  gmx::PotentialPointData output;

  output.energy = real(alpha_ * R / target_);
  // Direction of force is ill-defined when v == v0
  if (R != 0 && R != target_) {
    if (R > target_)
      output.force = real(-(alpha_ / target_ / double(R))) * rdiff;
    else
      output.force = real((alpha_ / target_ / double(R))) * rdiff;
  }

  return output;
}

template class ::plugin::RestraintModule<LinearRestraint>;
} // namespace plugin
