//
// Created by Eric Irrgang on 2/26/18.
//

#include "ensemblepotential.h"

#include <vector>

namespace plugin
{

// Explicit instantiation.
template class ::plugin::Matrix<double>;

void EnsembleResourceHandle::reduce(const ::plugin::Matrix<double>& send, ::plugin::Matrix<double>* receive) const
{
    assert(_reduce);
    (*_reduce)(send, receive);
}

template<typename T_I, typename T_O>
void EnsembleResourceHandle::map_reduce(const T_I &iterable,
                                        T_O *output,
                                        void (*function)(double, const PairHist & input,
                                                 PairHist * output)
                                        )
{}

/*!
 * \brief Apply a Gaussian blur when building a density grid for a list of values.
 *
 * Normalize such that the area under each sample is 1.0/num_samples.
 */
class BlurToGrid
{
    public:
        BlurToGrid(double low, double width, double sigma) :
            low_{low},
            binWidth_{width},
            _sigma{sigma}
        {
        };

        void operator() (const std::vector<double>& distances, std::vector<double>* grid)
        {
            const auto nbins = grid->size();
            const auto num_samples = distances.size();

            const double denominator = 1.0/(2*_sigma*_sigma);
            const double normalization = 1.0/(num_samples*sqrt(2.0*M_PI*_sigma*_sigma));
            // We aren't doing any filtering of values too far away to contribute meaningfully, which
            // is admittedly wasteful for large sigma...
            for (size_t i = 0; i < nbins; ++i)
            {
                double bin_value{0};
                const double bin_x{i*binWidth_};
                for(const auto distance : distances)
                {
                    const double relative_distance{bin_x - distance};
                    const auto numerator = -relative_distance*relative_distance;
                    bin_value += normalization*exp(numerator*denominator);
                }
                grid->at(i) = bin_value;
            }
        };

    private:
        /// Minimum value of bin zero
        const double low_;

        /// Size of each bin
        const double binWidth_;

        /// Smoothing factor
        const double _sigma;

};

EnsembleHarmonic::EnsembleHarmonic(size_t nbins,
                                   double binWidth,
                                   double min_dist,
                                   double max_dist,
                                   PairHist experimental,
                                   unsigned int nsamples,
                                   double sample_period,
                                   unsigned int nwindows,
                                   double window_update_period,
                                   double K,
                                   double sigma) :
    nBins_{nbins},
    binWidth_{binWidth},
    minDist_{min_dist},
    maxDist_{max_dist},
    histogram_(nBins_, 0),
    experimental_{std::move(experimental)},
    nSamples_{nsamples},
    currentSample_{0},
    samplePeriod_{sample_period},
    nextSampleTime_{samplePeriod_},
    distanceSamples_(nSamples_),
    nWindows_{nwindows},
    currentWindow_{0},
    windowUpdatePeriod_{window_update_period},
    nextWindowUpdateTime_{windowUpdatePeriod_},
    windows_(),
    k_{K},
    sigma_{sigma}
{}

EnsembleHarmonic::EnsembleHarmonic(const input_param_type &params) :
    EnsembleHarmonic(params.nbins,
                     params.binWidth,
                     params.min_dist,
                     params.max_dist,
                     params.experimental,
                     params.nsamples,
                     params.sample_period,
                     params.nwindows,
                     params.window_update_period,
                     params.K,
                     params.sigma)
{
}

// Todo: reference coordinate for PBC problems.
void EnsembleHarmonic::callback(gmx::Vector v,
                                gmx::Vector v0,
                                double t,
                                const EnsembleResources &resources)
{
    auto rdiff = v - v0;
    const auto Rsquared = dot(rdiff,
                              rdiff);
    const auto R = sqrt(Rsquared);

    // Store historical data every sample_period steps
    {
        std::lock_guard<std::mutex> lock(samples_mutex_);
        if (t >= nextSampleTime_)
        {
            distanceSamples_[currentSample_++] = R;
            nextSampleTime_ += samplePeriod_;
        };
    }

    // Every nsteps:
    //   0. Drop oldest window
    //   1. Reduce historical data for this restraint in this simulation.
    //   2. Call out to the global reduction for this window.
    //   3. On update, checkpoint the historical data source.
    //   4. Update historic windows.
    //   5. Use handles retained from previous windows to reconstruct the smoothed working histogram
    {
        std::lock_guard<std::mutex> lock_windows(windows_mutex_);
        // Since we reset the samples state at the bottom, we should probably grab the mutex here for
        // better exception safety.
        std::lock_guard<std::mutex> lock_samples(samples_mutex_);
        if (t >= nextWindowUpdateTime_)
        {
            // Get next histogram array, recycling old one if available.
            std::unique_ptr<Matrix<double>> new_window = gmx::compat::make_unique<Matrix<double>>(1,
                                                                                                  nBins_);
            std::unique_ptr<Matrix<double>> temp_window;
            if (windows_.size() == nWindows_)
            {
                // Recycle the oldest window.
                // \todo wrap this in a helper class that manages a buffer we can shuffle through.
                windows_[0].swap(temp_window);
                windows_.erase(windows_.begin());
            }
            else
            {
                auto new_temp_window = gmx::compat::make_unique<Matrix<double>>(1,
                                                                                nBins_);
                assert(new_temp_window);
                temp_window.swap(new_temp_window);
            }

            // Reduce sampled data for this restraint in this simulation, applying a Gaussian blur to fill a grid.
            // Todo: update with new interpretatino of max/min dist
            auto blur = BlurToGrid(0.,
                                   binWidth_,
                                   sigma_);
            assert(new_window != nullptr);
            // Todo: when this callback code is extracted, we should adjust the arithmetic so that the times for the two update periods can't drift due to floating point precision problems.
            assert(currentSample_ == distanceSamples_.size());
            blur(distanceSamples_,
                 new_window->vector());
            // We can just do the blur locally since there aren't many bins. Bundling these operations for
            // all restraints could give us a chance at some parallelism. We should at least use some
            // threading if we can.

            // We request a handle each time before using resources to make error handling easier if there is a failure in
            // one of the ensemble member processes and to give more freedom to how resources are managed from step to step.
            auto ensemble = resources.getHandle();
            // Get global reduction (sum) and checkpoint.
            assert(temp_window != nullptr);
            // Todo: in reduce function, give us a mean instead of a sum.
            ensemble.reduce(*new_window,
                            temp_window.get());

            // Update window list with smoothed data.
            windows_.emplace_back(std::move(new_window));

            // Get new histogram difference. Subtract the experimental distribution to get the values to use in our potential.
            for (auto &bin : histogram_)
            {
                bin = 0;
            }
            for (const auto &window : windows_)
            {
                for (size_t i = 0; i < window->cols(); ++i)
                {
                    histogram_.at(i) += (window->vector()->at(i) - experimental_.at(i))/windows_.size();
                }
            }


            // Note we do not have the integer timestep available here. Therefore, we can't guarantee that updates occur
            // with the same number of MD steps in each interval, and the interval will effectively lose digits as the
            // simulation progresses, so _update_period should be cleanly representable in binary. When we extract this
            // to a facility, we can look for a part of the code with access to the current timestep.
            nextWindowUpdateTime_ += windowUpdatePeriod_;
            ++currentWindow_;

            // Reset sample bufering.
            currentSample_ = 0;
            // Clean up drift in sample times.
            nextSampleTime_ = t + samplePeriod_;
        };
    }

}

gmx::PotentialPointData EnsembleHarmonic::calculate(gmx::Vector v,
                                                    gmx::Vector v0,
                                                    double t)
{
    auto rdiff = v - v0;
    const auto Rsquared = dot(rdiff,
                              rdiff);
    const auto R = sqrt(Rsquared);


    // Compute output
    gmx::PotentialPointData output;
    // Energy not needed right now.
//    output.energy = 0;

    if (R != 0) // Direction of force is ill-defined when v == v0
    {

        double f{0};

        // Todo: update maxDist and minDist interpretration: flat bottom potential.
        if (R > maxDist_)
        {
            f = k_ * (maxDist_ - R);
        }
        else if (R < minDist_)
        {
            f = -k_ * (minDist_ - R);
        }
        else
        {
            double f_scal{0};

            //  for (auto element : hij){
            //      cout << "Hist element " << element << endl;
            //    }
            size_t numBins = histogram_.size();
            //cout << "number of bins " << numBins << endl;
            double x, argExp;
            double normConst = sqrt(2 * M_PI) * pow(sigma_,
                                                    3.0);

            for (size_t n = 0; n < numBins; n++)
            {
                x = n * binWidth_ - R;
                argExp = -0.5 * pow(x / sigma_,
                                    2.0);
                f_scal += histogram_.at(n) * x / normConst * exp(argExp);
            }
            f = -k_ * f_scal;
        }

        output.force = f / norm(rdiff) * rdiff;
    }
    return output;
}

EnsembleResourceHandle EnsembleResources::getHandle() const
{
    auto handle = EnsembleResourceHandle();
    assert(bool(reduce_));
    handle._reduce = &reduce_;
    return handle;
}

// Explicitly instantiate a definition.
template class ::plugin::RestraintModule<EnsembleRestraint>;

} // end namespace plugin
