//
// Created by Eric Irrgang on 2/26/18.
//

#include "ensemblepotential.h"

#include <vector>

namespace plugin
{

EnsembleHarmonic::EnsembleHarmonic() :
    _binWidth{0},
    _K{0},
    _sigma{0},
    _max_dist{0},
    _min_dist{0}
{}

gmx::PotentialPointData EnsembleHarmonic::calculate(gmx::Vector v,
                                                    gmx::Vector v0,
                                                    double t)
{
    auto rdiff = v - v0;
    const auto Rsquared = dot(rdiff, rdiff);
    const auto R = sqrt(Rsquared);

    gmx::PotentialPointData output;
    // Energy not needed right now.
//    output.energy = 0;
    if (R != 0) // Direction of force is ill-defined when v == v0
    {

        double dev = R;

        double f{0};
//        if (_histogram.empty())
//        {
//            // Load from filesystem on first step.
//            _histogram = getRouxHistogram(getenv("HISTDIF"), _binWidth, _sigma, _min_dist, _max_dist);
//            assert(!_histogram.empty());
//            assert(_min_dist!=0);
//            assert(_max_dist!=0);
//        }
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
            size_t numBins = _histogram.size();
            //cout << "number of bins " << numBins << endl;
            double x, argExp;
            double normConst = sqrt(2 * M_PI) * pow(_sigma,
                                                    3.0);

            for (auto n = 0; n < numBins; n++)
            {
                x = n * _binWidth - dev;
                argExp = -0.5 * pow(x / _sigma,
                                    2.0);
                f_scal += _histogram[n] * x / normConst * exp(argExp);
            }
            f = -_K * f_scal;
        }

        output.force = f / norm(rdiff) * rdiff;
    }
    return output;
}

EnsembleRestraint::EnsembleRestraint()
{}

// Explicitly instantiate a definition.
template class RestraintModule<EnsembleRestraint>;

} // end namespace plugin
