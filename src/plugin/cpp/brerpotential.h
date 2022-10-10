//
// Created by Jennifer Hays on 3/28/2018
//

#ifndef GROMACS_BRERPOTENTIAL_H
#define GROMACS_BRERPOTENTIAL_H

/*! \file
 * \brief Provide EBMetaD MD potential for GROMACS plugin.
 */
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

struct BRER_input_param_type {
  /// learned coupling constant
  double alpha{0};
  double alpha_prev{0};
  double alpha_max{0};

  /// keep track of mean and variance
  double mean{0};
  double variance{0};

  /// parameters for training coupling constant (Adagrad)
  double A{0};
  double tau{0};
  double g{0};
  double gsqrsum{0};
  double eta{0};
  bool converged{0};
  double tolerance{0.05};

  /// target distance
  double target{0};

  /// Number of samples to store during each tau window.
  unsigned int nSamples{0};
  unsigned int currentSample{0};
  double samplePeriod{0};
  double windowStartTime{0};

  std::string parameter_filename;
};

// \todo We should be able to automate a lot of the parameter setting stuff
// by having the developer specify a map of parameter names and the
// corresponding type, but that could get tricky. The statically compiled fast
// parameter structure would be generated with a recursive variadic template the
// way a tuple is. ref
// https://eli.thegreenplace.net/2014/variadic-templates-in-c/

std::unique_ptr<BRER_input_param_type>
makeBRERParams(double A, double tau, double tolerance, double target,
               unsigned int nSamples, std::string parameter_filename);
//                   double samplePeriod)

class BRER {
public:
  using input_param_type = BRER_input_param_type;

  //        EnsembleHarmonic();

  explicit BRER(const input_param_type &params);

  BRER(double alpha, double alpha_prev, double alpha_max, double mean,
       double variance, double A, double tau, double g, double gsqrsum,
       double eta, bool converged, double tolerance, double target,
       unsigned int nSamples, std::string parameter_filename);
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

  double getAlphaMax() { return alpha_max_; }
  double getTarget() { return target_; }
  bool getConverged() { return converged_;}

private:
  bool initialized_{false};

  /// learned coupling constant
  double alpha_;
  double alpha_prev_;
  double alpha_max_;

  /// keep track of mean and variance
  double mean_;
  double variance_;

  /// parameters for training coupling constant (Adagrad)
  double A_;
  double tau_;
  double g_;
  double gsqrsum_;
  double eta_;
  bool converged_;
  double tolerance_;

  /// target distance
  double target_;

  // Sampling parameters determined by the user
  unsigned int nSamples_;
  double samplePeriod_;

  unsigned int currentSample_{0};
  // Sampling parameters that are dependent on t and thus set upon
  // initialization of the plugin For now, since we don't have access to t,
  // we'll set them all to zero.
  double nextSampleTime_{0};
  double windowStartTime_{0};
  double nextUpdateTime_{0};

  std::string parameter_filename_;
  std::unique_ptr<RAIIFile> parameter_file_{nullptr};
};

// implement IRestraintPotential in terms of BRER
// To be templated and moved.
class BRERRestraint : public ::gmx::IRestraintPotential, private BRER {
public:
  using BRER::input_param_type;
  BRERRestraint(std::vector<int> sites, const input_param_type &params,
                std::shared_ptr<Resources> resources)
      : BRER(params), sites_{std::move(sites)}, resources_{
                                                    std::move(resources)} {}
  ~BRERRestraint() override = default;
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

  using BRER::getAlphaMax;
  using BRER::getTarget;
  using BRER::getConverged;

private:
  std::vector<int> sites_;
  //        double callbackPeriod_;
  //        double nextCallback_;
  std::shared_ptr<Resources> resources_;
};

// Just declare the template instantiation here for client code.
// We will explicitly instantiate a definition in the .cpp file where the
// input_param_type is defined.
extern template class RestraintModule<BRERRestraint>;

} // end namespace plugin

#endif // GROMACS_BRERPOTENTIAL_H
