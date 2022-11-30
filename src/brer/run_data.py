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
import collections.abc
import dataclasses
import json
import os
import pathlib
import typing
import warnings
from dataclasses import dataclass
from dataclasses import field

from ._compat import dataclass_slots
from ._compat import List
from ._compat import Mapping
from ._compat import MutableMapping
from .pair_data import PairDataCollection


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

    *logging_filename* is derived from the pair *name* (user-provided;
    usually derived from the residue IDs defining the pair).
    Overriding the default produces a warning.

    .. versionchanged:: 2.0

        *sites* is required to initialize the object.


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
    """Store (and manipulate, to a lesser extent) all the metadata for a BRER run.

    The full set of metadata for a single BRER run includes both the general
    parameters and the pair-specific parameters.

    Key-value pairs provided to *general_params* will be used to update the
    default values of a new :py:class:`GeneralParams` instance.

    *pair_params* is a mapping of named `PairParams` instances.

    Both general and pair-specific parameters may be updated with *set()*.

    This is the BRER program state data structure. We avoid the name "state"
    because of potential confusion with concepts like energetic, conformational,
    or thermodynamic state, but we use the filename :file:`state.json` for the
    serialized object. RunData instances can be serialized to a file with
    :py:meth:`~brer.run_data.RunData.save_config()` or deserialized (restored from a file)
    with :py:meth:`~brer.run_data.RunData.create_from()`.


    Examples
    --------
    ::

        ├── pair parameters
        │   ├── name of pair 1
        │   │   ├── alpha
        │   │   ├── target
        │   │   └── ...
        │   ├── name of pair 2
        |
        ├── general parameters
            ├── A
            ├── tau
            ├── ...


    """
    general_params: GeneralParams
    pair_params: MutableMapping[str, PairParams]

    def __init__(self, *,
                 general_params: GeneralParams,
                 pair_params: Mapping[str, PairParams]):
        if not isinstance(general_params, GeneralParams):
            raise ValueError('*general_params* must be a GeneralParams instance.')
        if not all(isinstance(obj, PairParams) for obj in pair_params.values()):
            raise ValueError('*pair_params* must be a collection of PairParams instances.')

        self.pair_params = dict()
        for name, obj in pair_params.items():
            replacements = dict()
            if not obj.name:
                replacements[name] = name
            elif obj.name != name:
                raise ValueError(f'*pair_params* key {name} does not match *name* field in {obj}.')
            self.pair_params[name] = dataclasses.replace(obj, **replacements)

        self.general_params = general_params

    def set(self, name=None, **kwargs):
        """Set either general or pair-specific parameters.

        When a *name* argument is present, sets pair-specific parameters for
        the named restraint.

        When *name* is not provided, sets general parameters.

        Parameters
        ----------
        name : str, default=None
            Restraint name, as used in the `brer.run_config.RunConfig`.

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
        """Get either a general or a pair-specific parameter.

        Parameters
        ----------
        key : str
            The parameter to get.
        name : str, default=None
            If getting a pair-specific parameter, specify the restraint name.

        Returns
        -------
        typing.Any
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
        """Get the run metadata as a hierarchical dictionary.

        Returns
        -------
        dict
            hierarchical dictionary of metadata


        For historical reasons, the top level dictionary keys are not exact string
        matches for the object attributes.

        """
        pair_param_dict = dict(
            (name, dataclasses.asdict(pair_params)) for name, pair_params in self.pair_params.items())

        return {
            'general parameters': dataclasses.asdict(self.general_params),
            'pair parameters': dict((key, value) for key, value in pair_param_dict.items() if key != 'name')
        }

    def save_config(self, fnm='state.json'):
        """Saves the run parameters to a log file.

        Parameters
        ----------
        fnm : str, default='state.json'
            Log file for state parameters.
        """
        with open(fnm, 'w') as fh:
            json.dump(self.as_dictionary(), fh, indent=4)

    @typing.overload
    @classmethod
    def create_from(cls,
                    source: typing.Union[str, os.PathLike, pathlib.Path],
                    ensemble_num: int = None) -> 'RunData':
        ...

    @typing.overload
    @classmethod
    def create_from(cls, source: Mapping[str, dict], ensemble_num: int = None) -> 'RunData':
        ...

    @typing.overload
    @classmethod
    def create_from(cls, source: PairDataCollection, ensemble_num: int = None) -> 'RunData':
        ...

    @classmethod
    def create_from(cls, source, *, ensemble_num: int = None):
        """Create a new instance from provided data.

        Warns if *ensemble_num* is specified but contradicts *source*.
        If *ensemble_num* is not specified and is not found in *source*, the
        default value is determined by :py:class:`GeneralParams`.

        *source* is usually either a :file:`state.json` file or a

        Parameters
        ----------
        source :
            File or Python objects from which to initialize RunData.
        ensemble_num :
            Member index in the ensemble (if any).

        """
        if isinstance(source, (str, os.PathLike, pathlib.Path)):
            if not os.path.exists(source):
                raise ValueError(f'Source file not found: {source}')
            else:
                with open(source, 'r') as fh:
                    data = json.load(fh)
                return cls.create_from(source=data, ensemble_num=ensemble_num)
        elif isinstance(source, PairDataCollection):
            # PairParams comes from PairData names and sites and default values.
            pair_params = {name: PairParams(name=name, sites=pair.sites) for name, pair in source.items()}
            # GeneralParams comes from defaults
            run_data = cls(general_params=GeneralParams(), pair_params=pair_params)
            if ensemble_num is not None:
                run_data.set(ensemble_num=ensemble_num)
            return run_data
        elif isinstance(source, collections.abc.Mapping):
            # Check for *ensemble_num* agreement.
            general_params = source['general parameters']
            if 'name' in general_params:
                del general_params['name']
            general_params = GeneralParams(**general_params)
            if ensemble_num is not None:
                _source_id = general_params.ensemble_num
                if ensemble_num != _source_id:
                    warnings.warn(f'Caller provided ensemble_num={ensemble_num} overrides {_source_id} '
                                  f'from {source}.')
                    general_params.ensemble_num = ensemble_num
            pair_params = {name: PairParams(name=name, sites=fields['sites']) for name, fields in
                           source['pair parameters'].items()}
            return RunData(general_params=general_params, pair_params=pair_params)
        else:
            raise ValueError(f'{source} is not a valid source of RunData.')
