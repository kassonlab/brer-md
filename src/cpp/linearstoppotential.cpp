//
// Created by Jennifer Hays on 6/12/18.
//

#include "gmxapi/md/mdsignals.h"
#include "gmxapi/session.h"
#include "linearstoppotential.h"

#include <cmath>

#include <vector>

namespace plugin {
std::unique_ptr<linearstop_input_param_type>
makeLinearStopParams(double alpha, double target, double tolerance,
                     double samplePeriod, std::string logging_filename) {
  using std::make_unique;
  auto params = make_unique<linearstop_input_param_type>();
  params->alpha = alpha;
  params->tolerance = tolerance;
  params->target = target;
  params->samplePeriod = samplePeriod;
  params->logging_filename = logging_filename;

  return params;
};
LinearStop::LinearStop(double alpha, double target, double tolerance,
                       double samplePeriod, std::string logging_filename)
    : alpha_{alpha}, tolerance_{tolerance}, target_{target},
      samplePeriod_{samplePeriod}, logging_filename_{logging_filename} {};

LinearStop::LinearStop(const input_param_type &params)
    : LinearStop(params.alpha, params.target, params.tolerance,
                 params.samplePeriod, params.logging_filename) {}

void LinearStop::writeparameters(double t, const double R) {
  if (logging_file_) {
    fprintf(logging_file_->fh(), "%f\t%f\t%f\t%f\n", t, R, target_, alpha_);
    fflush(logging_file_->fh());
  }
}

void LinearStop::callback(gmx::Vector v, gmx::Vector v0, double t,
                          const Resources &resources) {

  // Update distance
  auto rdiff = v - v0;
  const auto Rsquared = dot(rdiff, rdiff);
  const auto R = sqrt(Rsquared);

  bool converged = std::abs(R - target_) < tolerance_;
  //        printf("===SUMMARY===\nR = %f\ntarget_ = %f\ntolerance =
  //        %f\nconverged = %d\n======\n",
  //               R, target_, tolerance_, converged);
  // Open logs at the beginning of the simulation
  if (!initialized_) {
    std::cout << "Initializing the LinearStop restraint" << std::endl;
    startTime_ = t;
    nextSampleTime_ = startTime_ + samplePeriod_;
    //            printf("startTime_ = %f, nextSampleTime_ = %f, samplePeriod_ =
    //            %f\n",
    //                   startTime_, nextSampleTime_, samplePeriod_);
    logging_file_ =
        std::make_unique<RAIIFile>(logging_filename_.c_str(), "a");
    if (logging_file_) {
      fprintf(logging_file_->fh(), "time\tR\ttarget\talpha\n");
      writeparameters(t, R);
    }
    initialized_ = true;
    //            printf("initialized_ = %d\n", initialized_);
  }

  // If the simulation has not converged, keep running and log
  if (!converged && (t >= nextSampleTime_)) {
    writeparameters(t, R);
    currentSample_++;
    nextSampleTime_ = (currentSample_ + 1) * samplePeriod_ + startTime_;
  }

  if (converged) {
    if (!stop_called_) {
      stop_called_ = true;
      writeparameters(t, R);
      //                fprintf(logging_file_->fh(), "Simulation converged at t
      //                == %f", t);
      logging_file_->close();
      logging_file_.reset(nullptr);
      resources.getHandle().stop();
    } else {
      // Do nothing until all stops have been called
    }
  }
}

gmx::PotentialPointData LinearStop::calculate(gmx::Vector v, gmx::Vector v0,
                                              double t) {
  // Our convention is to calculate the force that will be applied to v.
  // An equal and opposite force is applied to v0.
  time_ = t;
  auto rdiff = v - v0;
  const auto Rsquared = dot(rdiff, rdiff);
  const auto R = sqrt(Rsquared);
  // TODO: find appropriate math header and namespace

  // In White & Voth, the additional energy is alpha * f(r)/favg

  gmx::PotentialPointData output;

  output.energy = alpha_ / target_ * double(R);
  // Direction of force is ill-defined when v == v0
  if (R != 0 && R != target_) {
    if (R > target_)
      output.force = real(-(alpha_ / target_ / double(R))) * rdiff;
    else
      output.force = real((alpha_ / target_ / double(R))) * rdiff;
  }

  //    history.emplace_back(magnitude - R0);
  return output;
}

// Explicitly instantiate a definition.
template class ::plugin::RestraintModule<LinearStopRestraint>;
} // end namespace plugin
