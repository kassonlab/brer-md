//
// Created by Jennifer Hays on 6/12/18.
//

#ifndef GROMACS_LINEARSTOPPOTENTIAL_H
#define GROMACS_LINEARSTOPPOTENTIAL_H

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

struct linearstop_input_param_type {
  double alpha{0};
  double tolerance{0.5};
  double target{0};
  double samplePeriod{0};
  std::string logging_filename;
};

std::unique_ptr<linearstop_input_param_type>
makeLinearStopParams(double alpha, double target, double tolerance,
                     double samplePeriod, std::string logging_filename);
//                   double samplePeriod)

class LinearStop {
public:
  using input_param_type = linearstop_input_param_type;

  explicit LinearStop(const input_param_type &params);

  LinearStop(double alpha, double target, double tolerance, double samplePeriod,
             std::string filename);

  // If dispatching this virtual function is not fast enough, the compiler may
  // be able to better optimize a free function that receives the current
  // restraint as an argument.
  gmx::PotentialPointData calculate(gmx::Vector v, gmx::Vector v0,
                                    double t);

  void writeparameters(double t, const double R);

  // An update function to be called on the simulation master rank/thread
  // periodically by the Restraint framework.
  void callback(gmx::Vector v, gmx::Vector v0, double t,
                const Resources &resources);

  double getTime() { return time_; }
  bool getStopCalled() { return stop_called_; }

private:
  bool initialized_{false};
  double time_{0};

  double alpha_;
  double tolerance_;

  /// target distance
  double target_;

  // Sample interval
  double samplePeriod_;
  double startTime_{0};
  double nextSampleTime_{0};
  unsigned int currentSample_{0};

  std::string logging_filename_;
  std::unique_ptr<RAIIFile> logging_file_{nullptr};
  bool stop_called_{false};
};

// implement IRestraintPotential in terms of LinearStop
// To be templated and moved.
class LinearStopRestraint : public ::gmx::IRestraintPotential,
                            private LinearStop {
public:
  using LinearStop::input_param_type;
  LinearStopRestraint(const std::vector<int> &sites,
                      const input_param_type &params,
                      std::shared_ptr<Resources> resources)
      : LinearStop(params), sites_{sites}, resources_{std::move(resources)} {}

  ~LinearStopRestraint() override = default;
  
  std::vector<int> sites() const override { return sites_; }

  gmx::PotentialPointData evaluate(gmx::Vector r1, gmx::Vector r2,
                                   double t) override {
    return calculate(r1, r2, t);
  };

  // An update function to be called on the simulation master rank/thread
  // periodically by the Restraint framework.
  void update(gmx::Vector v, gmx::Vector v0, double t) override {
    // Todo: use a callback period to mostly bypass this and avoid excessive
    // mutex locking.
    callback(v, v0, t, *resources_);
  };

  /*!
   * \brief Implement the binding protocol that allows access to Session
   * resources.
   *
   * The client receives a non-owning pointer to the session and cannot extent
   * the life of the session. In the future we can use a more formal handle
   * mechanism.
   *
   * \param session pointer to the current session
   */
  void bindSession(gmxapi::SessionResources *session) override {
    resources_->setSession(session);
  }

  void setResources(std::unique_ptr<Resources> &&resources) {
    resources_ = std::move(resources);
  }

  using LinearStop::getTime;
  using LinearStop::getStopCalled;

private:
  std::vector<int> sites_;
  std::shared_ptr<Resources> resources_;
};

// Just declare the template instantiation here for client code.
// We will explicitly instantiate a definition in the .cpp file where the
// input_param_type is defined.
extern template class RestraintModule<LinearStopRestraint>;
} // end namespace plugin

#endif // GROMACS_LINEARSTOPPOTENTIAL_H
