"""BRER data for site pairs.

Coordinate the experimental reference data and molecular model data for the
labeled / restrained pairs.

Support the statistical (re)sampling of target pair distances when beginning a
BRER iteration.
"""
import dataclasses
import json
import os
import pathlib
import typing
import warnings
from typing import Iterator

import numpy as np

from ._compat import dataclass_kw_only
from ._compat import List
from ._compat import Mapping


@dataclasses.dataclass(frozen=True)
class PairData:
    """Pair distance distribution.

    Essential pair data to support BRER MD plugin code. All data must be
    provided when the object is initialized. (Fields are read-only.)

    Fields here correspond to the fields for each named pair
    (JSON *objects*) in a :file:`pair_data.json` file (the *pairs_json* argument
    of :py:func:`~brer.run_config.RunConfig()`).

    .. versionchanged:: 2.0

        When reading from
        :file:`pair_data.json` or :file:`state.json`, the *name* used for
        PairData comes from the object key, not from the *name* field of the object.
        The *name* field in the serialized (JSON) representation is ignored
        when reading, but is preserved for backward compatibility when writing.

    """
    # Historically, *name* has sometimes been provided as a positional argument,
    # but this led to ambiguity in the source of the final value of the field.
    # We define the *name* field first in case we overlook some legacy usage.
    name: str = dataclasses.field(**dataclass_kw_only)
    """Identifier for the pair of sites on the molecule.
    
    This string is chosen by the researcher. For example, the name may
    include identifiers for the two residues in a scheme that can be easily
    cross-referenced with experimental data.
    """

    bins: List[float] = dataclasses.field(**dataclass_kw_only)
    """Histogram edges for the distance distribution data.
    
    (Simulation length units.)
    """

    distribution: List[float] = dataclasses.field(**dataclass_kw_only)
    """Site distance distribution.
    
    Histogram values (weights or relative probabilities) for distances between
    the sites. (Generally derived from experimental data.)
    """

    sites: List[int] = dataclasses.field(**dataclass_kw_only)
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


class PairDataCollection(Mapping[str, PairData]):
    """Data for all the restrained pairs in a BRER simulation.

    Source data for the pair restraints is provided through a JSON file
    (*pairs_json*). The JSON file contains one *JSON object* for each
    `PairData` to be read.

    For each object, the object key is assumed to be the
    `PairData.name` of a pair.
    The JSON object contents are used to initialize a
    `PairData` for each named pair.

    The data file is usually constructed manually by the researcher after
    inspection of a molecular model and available experimental data. An example
    of what such a file should look like is provided in the :file:`brer/data`
    directory of the installed package or
    `in the source <https://github.com/kassonlab/brer-md/tree/main/src/brer/data>`__
    repository.

    Note that JSON is not a Python-specific file format, but
    :py:mod:`json` may be helpful.

    A *PairDataCollection* can be initialized from a sequence of `PairData`
    objects, or created from a JSON pair data file by using `create_from()`.

    """

    def __init__(self, *pairs: PairData):
        if len(pairs) < 1 or not all(isinstance(pair, PairData) for pair in pairs):
            raise TypeError('Must be initialized with one or more PairData instances.')
        self._pairs = {pair.name: pair for pair in pairs}

    def __getitem__(self, key: str) -> PairData:
        return self._pairs[key]

    def __iter__(self) -> Iterator[str]:
        yield from self._pairs

    def __len__(self) -> int:
        return len(self._pairs)

    @staticmethod
    def create_from(filename: typing.Union[str, os.PathLike, pathlib.Path]):
        """Reads pair data from json file.

        Parameters
        ----------
        filename :
            filename of the pair data


        """
        pairs = []
        with open(filename, 'r') as fh:
            for name, obj in json.load(fh).items():
                kwargs = {}
                for key, value in obj.items():
                    if key == 'name':
                        message = '*name* field is ignored from brer-md 2.0.'
                        if name == value:
                            warnings.warn(message, DeprecationWarning)
                        else:
                            message += f' Using {name} instead of {value}.'
                            warnings.warn(message, UserWarning)
                    else:
                        kwargs[key] = value
                pairs.append(PairData(name=name, **kwargs))
        return PairDataCollection(*pairs)

    def as_dict(self):
        """Encode the full collection as a single Python dictionary."""
        return {pair.name: dataclasses.asdict(pair) for pair in self._pairs.values()}


def sample(pair_data: PairData):
    """Choose a bin edge according to the probability distribution."""
    distribution = pair_data.distribution
    bins = pair_data.bins

    normalized = np.divide(distribution, np.sum(distribution))
    return np.random.choice(bins, p=normalized)


def sample_all(pairs: PairDataCollection):
    """Get a mapping of pair names to freshly sampled targets."""
    return {name: sample(pair) for name, pair in pairs.items()}
