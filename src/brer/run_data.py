"""Handle simulation data for BRER simulations.

`RunData` manages general parameters (`GeneralParams`) and pair-specific
parameters (`PairParams`) for a single simulator for a specific phase of the
BRER method.

Parameters are initially provided through the
:py:class:`~brer.run_config.RunConfig`, and are then stored to (and restored
from) an internally managed :file:`state.json` file.

Not all parameters are applicable to all BRER phases.

See Also
--------
:py:mod:`brer.plugin_configs`

"""
import dataclasses
import json
import warnings
from dataclasses import dataclass
from dataclasses import field

from ._compat import dataclass_slots
from ._compat import List
from ._compat import MutableMapping
from .pair_data import PairData


@dataclass(**dataclass_slots)
class GeneralParams:
    """Store the parameters shared by all restraints in a single simulation.

    These include some of the "Voth" parameters: *tau*, *A*, *tolerance*

    .. versionadded:: 2.0
        The *end_time* parameter.

    .. versionchanged:: 2.0
        *ensemble_num* now defaults to 0 for consistency with :py:class:`~brer.run_config.RunConfig`

    Update general parameters before a call to
    :py:meth:`brer.run_config.RunConfig.run()` by calling
    :py:meth:`brer.run_data.RunData.set()` without a *name* argument.
    """
    name: str = field(init=False, default='general')
    A: float = 50.
    end_time: float = 0.
    ensemble_num: int = 0
    iteration: int = 0
    num_samples: int = 50
    phase: str = 'training'
    production_time: float = 10000.
    sample_period: float = 100.
    start_time: float = 0.
    tau: float = 50
    tolerance: float = 0.25


@dataclass(**dataclass_slots)
class PairParams:
    """Stores the parameters that are unique to a specific restraint.

    *PairParams* is a mutable structure for run time data. Fields such as
    *alpha* and *target* may be updated automatically while running *brer*.

    *PairParams* should not be confused with
    :py:class:`~brer.pair_data.PairData` (an input data structure).

    Update pair-specific parameters before a call to
    :py:meth:`brer.run_config.RunConfig.run()` by calling
    :py:meth:`brer.run_data.RunData.set()`, providing the pair name with the
    *name* argument.
    """
    name: str
    sites: List[int]
    logging_filename: str = None
    alpha: float = 0.
    # TODO: Are we sure we should have defaults, especially for `target`?
    target: float = 3.

    def __post_init__(self):
        logging_filename = f'{self.name}.log'
        if self.logging_filename and self.logging_filename != logging_filename:
            warnings.warn(
                f'Specified logging filename {self.logging_filename} overrides default ("'
                f'{logging_filename}")')
        else:
            self.logging_filename = logging_filename


class RunData:
    """Store (and manipulate, to a lesser extent) all the metadata for a BRER run."""

    def __init__(self):
        """The full set of metadata for a single BRER run include both the
        general parameters and the pair-specific parameters."""
        self.general_params = GeneralParams()
        self.pair_params: MutableMapping[str, PairParams] = {}
        self.__names = []

    def set(self, name=None, **kwargs):
        """method used to set either general or a pair-specific parameter.

        Parameters
        ----------
        name : str, optional
            restraint name.
            These are the same identifiers that are used in the RunConfig, by default None

        Raises
        ------
        ValueError
            if you provide a name and try to set a general parameter or
            don't provide a name and try to set a pair-specific parameter.
        """
        if len(kwargs) == 0:
            raise TypeError(
                f'Invalid signature: {self.__class__.__qualname__}.set() called without naming any '
                f'parameters.')

        for key, value in kwargs.items():
            # If a restraint name is not specified, it is assumed that the parameter is
            # a "general" parameter.
            if not name:
                if any(field.name == key for field in dataclasses.fields(self.general_params)):
                    setattr(self.general_params, key, value)
                    continue
                else:
                    if any(field.name == key for field in dataclasses.fields(PairParams)):
                        raise ValueError(
                            f'You must provide pair *name* for which to set pair parameter {key}.')
            else:
                if any(field.name == key for field in dataclasses.fields(self.pair_params[name])):
                    setattr(self.pair_params[name], key, value)
                    continue
                else:
                    if any(field.name == key for field in dataclasses.fields(GeneralParams)):
                        raise ValueError(
                            f'{key} is a general parameter but you have provided a pair name.')
            raise ValueError(f'{key} is not a valid parameter.')

    def get(self, key, *, name=None):
        """get either a general or a pair-specific parameter.

        Parameters
        ----------
        key : str
            the parameter to get.
        name : str
            if getting a pair-specific parameter, specify the restraint name. (Default
            value = None)

        Returns
        -------
            the parameter value.
        """
        if name:
            return getattr(self.pair_params[name], key)
        else:
            try:
                return getattr(self.general_params, key)
            except AttributeError as e:
                if hasattr(PairParams, key):
                    raise ValueError(
                        f'Must specify pair *name* for parameter {key}.')
                else:
                    raise e

    def as_dictionary(self):
        """Get the run metadata as a heirarchical dictionary:

        Returns
        -------
        type
            heirarchical dictionary of metadata

        Examples
        --------

        >>> ├── pair parameters
        >>> │   ├── name of pair 1
        >>> │   │   ├── alpha
        >>> │   │   ├── target
        >>> │   │   └── ...
        >>> │   ├── name of pair 2
        >>> |
        >>> ├── general parameters
        >>>     ├── A
        >>>     ├── tau
        >>>     ├── ...

        """
        pair_param_dict = dict(
            (name, dataclasses.asdict(pair_params)) for name, pair_params in self.pair_params.items())

        return {
            'general parameters': dataclasses.asdict(self.general_params),
            'pair parameters': pair_param_dict
        }

    def from_dictionary(self, data: dict):
        """Loads metadata into the class from a dictionary.

        Parameters
        ----------
        data : dict
            RunData metadata as a dictionary.
        """
        _replacements = data['general parameters'].copy()
        del _replacements['name']
        self.general_params: GeneralParams = dataclasses.replace(self.general_params,
                                                                 **_replacements)
        for name in data['pair parameters']:
            # Check our assumption about the redundancy of *name*
            assert data['pair parameters'][name]['name'] == name
            self.pair_params[name] = PairParams(**data['pair parameters'][name])

    def from_pair_data(self, pd: PairData):
        """Load some of the run metadata from a PairData object. Useful at the
        beginning of a run.

        Parameters
        ----------
        pd : PairData
            object from which metadata are loaded
        """
        name = pd.name
        self.pair_params[name] = PairParams(name=name, sites=pd.sites)

    def clear_pair_data(self):
        """Removes all the pair parameters, replace with empty dict."""
        self.pair_params.clear()

    def save_config(self, fnm='state.json'):
        """Saves the run parameters to a log file.

        Parameters
        ----------
        fnm : str, optional
            log file for state parameters, by default 'state.json'
        """
        with open(fnm, 'w') as fh:
            json.dump(self.as_dictionary(), fh, indent=4)

    def load_config(self, fnm='state.json'):
        """Load state parameters from file.

        Parameters
        ----------
        fnm : str, optional
            log file of state parameters, by default 'state.json'
        """
        with open(fnm, 'r') as fh:
            self.from_dictionary(json.load(fh))
