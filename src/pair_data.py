"""
Classes to handle
1) pair metadata
2) resampling from DEER distributions at each new BRER iteration.
"""

import numpy as np
from src.metadata import MetaData, MultiMetaData


class PairData(MetaData):
    def __init__(self, name):
        super().__init__(name=name)
        self.set_requirements(['distribution', 'bins', 'sites'])


class MultiPair(MultiMetaData):
    def __init__(self):
        super().__init__()

    def re_sample(self):
        """
        Re-sample from the joint space. Do normalization just in case the data aren't normalized already.
        :return: dictionary of targets, drawn from DEER distributions.
        """
        answer = {}
        for pair_data in self._metadata_list:
            name = pair_data.__getattribute__('name')
            distribution = pair_data.get('distribution')
            bins = pair_data.get('bins')

            normalized = np.divide(distribution, np.sum(distribution))
            answer[name] = np.random.choice(bins, p=normalized)

        return answer

