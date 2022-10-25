"""Classes to handle 1) pair metadata 2) resampling from DEER distributions at
each new BRER iteration."""
import dataclasses
import json
import sys

import numpy as np

from brer.metadata import MultiMetaData

if sys.version_info.major > 3 or sys.version_info.minor >= 9:
    List = list
else:
    from typing import List

# We are trying to reduce ambiguity by confirming that the `name` field is often
# redundant with a key used to store such an object. To that end, we are trying
# to be more mindful of how these objects are constructed. We will try to prevent
# some previous usage patterns in which data structures were initialized with a
# positional *name* argument, which was then overwritten by a subsequent *set()*.
# Dataclass init arguments can be provided positionally in the order in which
# fields are defined, unless *kw_only=True* (after Py 3.10).
if sys.version_info.major >= 3 and sys.version_info.minor >= 10:
    field_kwargs = {'kw_only': True}
else:
    field_kwargs = {}


@dataclasses.dataclass(frozen=True)
class PairData:
    """Pair distance distribution.

    Essential pair data to support BRER MD plugin code. All data must be
    provided when the object is initialized. (Fields are read-only.)
    """
    # Historically, *name* has sometimes been provided as a positional argument,
    # but this led to ambiguity in the source of the final value of the field.
    # We define the *name* field first in case we overlook some legacy usage.
    name: str = dataclasses.field(**field_kwargs)

    bins: List[float] = dataclasses.field(**field_kwargs)
    distribution: List[float] = dataclasses.field(**field_kwargs)
    sites: List[int] = dataclasses.field(**field_kwargs)


class MultiPair(MultiMetaData):
    """Single class for handling multiple pair data.

    Handles resampling of targets.
    """

    def __init__(self):
        super().__init__()

    def get_as_single_dataset(self):
        single_dataset = {}
        for metadata in self._metadata_list:
            single_dataset[metadata.name] = dataclasses.asdict(metadata)
        return single_dataset

    def read_from_json(self, filename='state.json'):
        """Reads pair data from json file. For an example file, see
        pair_data.json in the data directory.

        Parameters
        ----------
        filename : str, optional
            filename of the pair data, by default 'state.json'
        """
        self._metadata_list = []
        with open(filename, 'r') as fh:
            data = json.load(fh)
        for name, metadata in data.items():
            # Schema check: @eirrgang _thinks_ these values are intentionally
            # redundant, but we should check for a while until we are sure. Then
            # we can try to make a stronger enforcement.
            assert name == metadata['name']
            # Note that in earlier versions of the software, the PairData object
            # was initialized with the name from data.keys() and then
            # overwritten with a value from data.values() by a subsequent
            # `set()`.
            metadata_obj = PairData(**metadata)
            self._metadata_list.append(metadata_obj)

    def re_sample(self):
        """Re-sample from the joint space. Do normalization just in case the
        data aren't normalized already.

        Returns
        -------
        dict
            dictionary of targets, drawn from DEER distributions.
        """
        answer = {}
        for pair_data in self._metadata_list:
            name = pair_data.name
            distribution = pair_data.distribution
            bins = pair_data.bins

            normalized = np.divide(distribution, np.sum(distribution))
            answer[name] = np.random.choice(bins, p=normalized)

        return answer
