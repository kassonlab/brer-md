"""
Classes to handle
1) pair metadata
2) resampling from DEER distributions at each new BRER iteration.
"""

import numpy as np
import json


class PairData:
    def __init__(self, name):
        self.__name = name
        self._distribution = []
        self._bins = []
        self._bin_width = 0.1
        self._metadata = {
            'distribution': self._distribution,
            'bins': self._bins,
            'bin_width': self._bin_width
        }

        print("Pair data for {} has been initialized".format(self.__name))

    @property
    def name(self):
        return self.__name

    @name.getter
    def name(self):
        return self.__name

    @property
    def distribution(self):
        return self._distribution

    @property
    def bins(self):
        return self._bins

    @property
    def bin_width(self):
        return self._bin_width

    @distribution.setter
    def distribution(self, distribution):
        self._distribution = distribution
        self._metadata['distribution'] = distribution

    @distribution.getter
    def distribution(self):
        return self._distribution

    @bins.setter
    def bins(self, bins):
        self._bins = bins
        self._metadata['bins'] = bins

    @bin_width.setter
    def bin_width(self, bin_width):
        self._bin_width = bin_width
        self._metadata['bin_width'] = bin_width

    def save_metadata(self, filename):
        if "json" in filename:
            json.dump(self._metadata, open(filename, 'w'))
        else:
            raise ValueError(
                "Can only write metadata to json file at the moment")


class ReSampler:
    """
    Takes multiple PairData objects and resamples from their convolved distribution space
    """

    def __init__(self):
        self._pairs = []

    def is_empty(self):
        return not self._pairs

    def add_pair(self, pair_data: PairData):
        """
        Adds a collection of single-pair data to the list
        :param pair_data: a PairData obj
        """
        self._pairs.append(pair_data)

    def get_distributions(self):
        """
        Gets the all the distributions stored in _pairs as a list
        :return: list of raw distribution data. The data are not normalized.
        """
        if not self.is_empty():
            return [pair_data.distribution for pair_data in self._pairs]
        else:
            raise IndexError("No pairs stored in this Resampler")

    def resample(self):
        """
        Re-sample from the joint space. Do normalization just in case the data aren't normalized already.
        :return: dictionary of targets, drawn from DEER distributions. The keys for each target are defined using the
        PairData object name.
        """
        answer = {}
        for pair_data in self._pairs:
            normalized = np.divide(pair_data.distribution,
                                   np.sum(pair_data.distribution))
            name = pair_data.name
            answer[name] = np.random.choice(pair_data.bins, p=normalized)
        return answer
