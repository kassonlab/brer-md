//
// Created by Eric Irrgang on 2/26/18.
//

#include "ensemblepotential.h"

#include <vector>

namespace plugin
{

template<typename T>
void EnsembleResourceHandle::reduce(const std::vector<T>& input, std::vector<T>* output)
{}

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
        BlurToGrid(double min_dist, double max_dist, double sigma) :
            _min_dist{min_dist},
            _max_dist{max_dist},
            _sigma{sigma}
        {
        };

        void operator() (const std::vector<double>& distances, std::vector<double>* grid)
        {
            const auto nbins = grid->size();
            const double dx{(_max_dist - _min_dist)/nbins};
            const auto num_samples = distances.size();

            const double denominator = 1.0/(2*_sigma*_sigma);
            const double normalization = 1.0/(num_samples*sqrt(2.0*M_PI*_sigma*_sigma));
            // We aren't doing any filtering of values too far away to contribute meaningfully, which
            // is admittedly wasteful for large sigma...
            for (size_t i = 0; i < nbins; ++i)
            {
                double bin_value{0};
                const double bin_x{i*dx};
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
        const double _min_dist;
        /// Maximum value of bin
        const double _max_dist;
        const double _sigma;
};

EnsembleHarmonic::EnsembleHarmonic(size_t nbins,
                                   double min_dist,
                                   double max_dist,
                                   unsigned int nsamples,
                                   double sample_period,
                                   unsigned int nwindows,
                                   double window_update_period,
                                   double K,
                                   double sigma) :
    _nbins{nbins},
    _min_dist{min_dist},
    _max_dist{max_dist},
    _binWidth{(_max_dist - _min_dist)/_nbins},
    _histogram{nullptr},
    _experimental{nullptr},
    _nsamples{nsamples},
    _current_sample{0},
    _sample_period{sample_period},
    _next_sample_time{_sample_period},
    _distance_samples(_nsamples),
    _nwindows{nwindows},
    _current_window{0},
    _window_update_period{window_update_period},
    _next_window_update_time{_window_update_period},
    _windows(),
    _K{K},
    _sigma{sigma}
{
    // We leave _histogram and _experimental unallocated until we have valid data to put in them, so that
    // (_histogram == nullptr) == invalid histogram.
}

EnsembleHarmonic::EnsembleHarmonic(const input_param_type &params) :
    EnsembleHarmonic(params.nbins,
                     params.min_dist,
                     params.max_dist,
                     params.nsamples,
                     params.sample_period,
                     params.nwindows,
                     params.window_update_period,
                     params.K,
                     params.sigma)
{
}

gmx::PotentialPointData EnsembleHarmonic::calculate(gmx::Vector v,
                                                    gmx::Vector v0,
                                                    double t)
{
    auto rdiff = v - v0;
    const auto Rsquared = dot(rdiff, rdiff);
    const auto R = sqrt(Rsquared);

    // Store historical data every sample_period steps
    if (t >= _next_sample_time)
    {
        _distance_samples[_current_sample++] = R;
        _next_sample_time += _sample_period;
    };

    // Every nsteps:
    //   0. Drop oldest window
    //   1. Reduce historical data for this restraint in this simulation.
    //   2. Call out to the global reduction for this window.
    //   3. On update, checkpoint the historical data source.
    //   4. Update historic windows.
    //   5. Use handles retained from previous windows to reconstruct the smoothed working histogram
    if (t >= _next_window_update_time)
    {
        // Get next histogram array, recycling old one if available.
        std::unique_ptr<PairHist> new_window{new std::vector<double>(_nbins, 0.)};
        std::unique_ptr<PairHist> temp_window;
        if (_windows.size() == _nwindows)
        {
            // Recycle the oldest window.
            // \todo wrap this in a helper class that manages a buffer we can shuffle through.
            _windows.front().swap(temp_window);
            _windows.erase(_windows.begin());
        }
        else
        {
            temp_window.reset(new std::vector<double>(_nbins));
        }

        // Reduce sampled data for this restraint in this simulation, applying a Gaussian blur to fill a grid.
        auto blur = BlurToGrid(_min_dist, _max_dist, _sigma);
        assert(new_window != nullptr);
        blur(_distance_samples, new_window.get());
        // We can just do the blur locally since there aren't many bins. Bundling these operations for
        // all restraints could give us a chance at some parallelism. We should at least use some
        // threading if we can.

        // We request a handle each time before using resources to make error handling easier if there is a failure in
        // one of the ensemble member processes and to give more freedom to how resources are managed from step to step.
        auto ensemble = _ensemble.getHandle();
        // Get global reduction (sum) and checkpoint.
        assert(temp_window != nullptr);
        ensemble.reduce(*new_window, temp_window.get());

        // Update window list with smoothed data.
        _windows.emplace_back(std::move(new_window));

        // Get new histogram difference. Subtract the experimental distribution to get the values to use in our potential.
        for (auto& bin : *_histogram)
        {
            bin = 0;
        }
        for (const auto& window : _windows)
        {
            for (auto i=0 ; i < window->size(); ++i)
            {
                (*_histogram)[i] += (*window)[i] - (*_experimental)[i];
            }
        }


        // Note we do not have the integer timestep available here. Therefore, we can't guarantee that updates occur
        // with the same number of MD steps in each interval, and the interval will effectively lose digits as the
        // simulation progresses, so _update_period should be cleanly representable in binary. When we extract this
        // to a facility, we can look for a part of the code with access to the current timestep.
        _next_window_update_time += _window_update_period;
        ++_current_window;

        // Reset sample bufering.
        _current_sample = 0;
        // Clean up drift in sample times.
        _next_sample_time = t + _sample_period;
    };

    // Compute output
    gmx::PotentialPointData output;
    // Energy not needed right now.
//    output.energy = 0;
    if (R != 0) // Direction of force is ill-defined when v == v0
    {

        double dev = R;

        double f{0};

        if (dev > _max_dist)
        {
            f = _K * (_max_dist - dev);
        }
        else if (dev < _min_dist)
        {
            f = - _K * (_min_dist - dev);
        }
        else
        {
            double f_scal{0};

//  for (auto element : hij){
//      cout << "Hist element " << element << endl;
//    }
            size_t numBins = _histogram->size();
            //cout << "number of bins " << numBins << endl;
            double x, argExp;
            double normConst = sqrt(2 * M_PI) * pow(_sigma,
                                                    3.0);

            for (auto n = 0; n < numBins; n++)
            {
                x = n * _binWidth - dev;
                argExp = -0.5 * pow(x / _sigma,
                                    2.0);
                f_scal += _histogram->at(n) * x / normConst * exp(argExp);
            }
            f = -_K * f_scal;
        }

        output.force = f / norm(rdiff) * rdiff;
    }
    return output;
}

EnsembleResourceHandle EnsembleResources::getHandle()
{
    return {};
}

// Explicitly instantiate a definition.
template class RestraintModule<EnsembleRestraint>;

} // end namespace plugin
