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
        self._sites = []
        self._metadata = {
            'distribution': self._distribution,
            'bins': self._bins,
            'sites': self._sites
        }

    # Set a name for the particular pair. Helps keep all the distributions and indices clear during run.
    @property
    def name(self):
        return self.__name

    @name.getter
    def name(self):
        return self.__name

    @property
    def distribution(self):
        return self._distribution

    @distribution.setter
    def distribution(self, distribution):
        self._distribution = distribution
        self._metadata['distribution'] = distribution

    @distribution.getter
    def distribution(self):
        return self._distribution

    @property
    def bins(self):
        return self._bins

    @bins.setter
    def bins(self, bins):
        self._bins = bins
        self._metadata['bins'] = bins

    @property
    def sites(self):
        return self._sites

    @sites.getter
    def sites(self):
        return self._sites

    @sites.setter
    def sites(self, sites):
        self._sites = sites
        self._metadata['sites'] = sites

    def load_metadata(self, metadata):
        self.__setattr__('distribution', metadata['distribution'])
        self.__setattr__('bins', metadata['bins'])
        self.__setattr__('sites', metadata['sites'])

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

    def add_pair(self, pair_data):
        """
        Adds a collection of single-pair data to the list
        :param pair_data: a PairData obj or list of PairData obj
        """
        if isinstance(pair_data, PairData):
            self._pairs.append(pair_data)
        elif isinstance(pair_data, list):
            for pd in pair_data:
                self._pairs.append(pd)
        else:
            raise ValueError('{} is not of type list or PairData'.format(
                type(pair_data)))

    def get_names(self):
        return [pair.name for pair in self._pairs]

    def get_distributions(self):
        """
        Gets the all the distributions stored in _pairs as a list
        :return: list of raw distribution data. The data are not normalized.
        """
        if not self.is_empty():
            return [pair_data.distribution for pair_data in self._pairs]
        else:
            raise IndexError("This ReSampler is empty!")

    def get_pair_data(self, name):
        if not self.is_empty():
            try:
                return self._pairs[self.get_names().index(name)]
            except ValueError:
                print("No matching pair data for name {}!".format(name))
        else:
            raise IndexError("This ReSampler is empty!")

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
