"""BRER data for site pairs.

Coordinate the experimental reference data and molecular model data for the
labeled / restrained pairs.

Support the statistical (re)sampling of target pair distances when beginning a
BRER iteration.
"""
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

    Fields here correspond to the fields for each named pair
    (JSON *objects*) in a :file:`pair_data.json` file (the *pairs_json* argument
    of :py:func:`~brer.run_config.RunConfig()`).
    """
    # Historically, *name* has sometimes been provided as a positional argument,
    # but this led to ambiguity in the source of the final value of the field.
    # We define the *name* field first in case we overlook some legacy usage.
    name: str = dataclasses.field(**field_kwargs)
    """Identifier for the pair of sites on the molecule.
    
    This string is chosen by the researcher. For example, the name may
    include identifiers for the two residues in a scheme that can be easily
    cross-referenced with experimental data.
    """

    bins: List[float] = dataclasses.field(**field_kwargs)
    """Histogram edges for the distance distribution data.
    
    (Simulation length units.)
    """

    distribution: List[float] = dataclasses.field(**field_kwargs)
    """Site distance distribution.
    
    Histogram values (weights or relative probabilities) for distances between
    the sites. (Generally derived from experimental data.)
    """

    sites: List[int] = dataclasses.field(**field_kwargs)
    """Indices defining the distance vector.
    
    A list of indices for sites in the molecular model. The first and last
    list elements are the sites associated with the distance data. Additional
    indices can be inserted in the list to define a chain of distance vectors
    that will be added without applying periodic boundary conditions.
    
    If, at any point in the simulation, the two molecular sites in the pair
    might be farther apart than half of the shortest simulation box dimension,
    the distance might accidentally get calculated between sites on different
    molecule "images" (periodic boundary conditions). To make sure that site-site
    distances are calculated on the same molecule, provide a sequence of sites
    on the molecule (that are never more than half a box-length apart) so that
    the correct vector between sites is unambiguous.
    """


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
