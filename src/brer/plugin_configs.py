"""Classes used to build gmxapi plugins for all phases of a BRER iteration.

Each class corresponds to one restraint potential provided by :py:mod`brer.md`.
Each instance corresponds to one restrained pair in a single simulation phase.
"""
import dataclasses
import typing
from abc import ABC
from abc import abstractmethod
from functools import singledispatchmethod

from ._compat import dataclass_kw_only
from ._compat import List


def _get_workelement() -> typing.Type:
    try:
        # noinspection PyUnresolvedReferences
        from gmxapi.simulation.workflow import WorkElement
    except (ImportError, ModuleNotFoundError):
        # Fall-back for gmxapi < 0.1.0
        try:
            # noinspection PyUnresolvedReferences
            from gmx.workflow import WorkElement
        except (ImportError, ModuleNotFoundError):
            WorkElement = None
    if WorkElement is None:
        raise RuntimeError('brer requires gmxapi. See https://github.com/kassonlab/brer_md#requirements')
    return WorkElement


@dataclasses.dataclass
class PluginConfig(ABC):
    """Abstract class for the BRER potential configurations.

    Provide base class functionality and required interface to build ``training``,
    ``convergence``, and ``production`` phase pluggable MD potentials.
    """
    name: str = dataclasses.field(init=False, **dataclass_kw_only)
    sites: List[int] = dataclasses.field(**dataclass_kw_only)
    logging_filename: str = dataclasses.field(**dataclass_kw_only)

    @abstractmethod
    def build_plugin(self):
        """Abstract method for building a plugin.

        To be determined by the phase of the simulation (training,
        convergence, production)
        """
        pass

    @singledispatchmethod
    @classmethod
    def create_from(cls, obj):
        """Get an instance of the appropriate type from the provided data structure.

        Source *obj* is either a :py:class:`~collections.abc.Mapping` or an object
        with the fields necessary to initialize a *cls* instance.

        Extra fields in *obj* are ignored.
        """
        if cls is PluginConfig:
            raise NotImplementedError
        return cls(**{key: getattr(obj, key) for key in [field.name for field in dataclasses.fields(cls) if
                                                         field.init] if hasattr(obj, key)})

    @create_from.register(dict)
    @classmethod
    def _(cls, obj: dict):
        return cls(**{key: obj[key] for key in [field.name for field in dataclasses.fields(cls) if
                                                field.init] if key in obj})


@dataclasses.dataclass
class TrainingPluginConfig(PluginConfig):
    """Configure BRER potential for the training phase.

    The BRER training phase uses the MD potential provided by :py:func:`brer.brer_restraint`.

    See https://pubs.acs.org/doi/10.1021/acs.jpclett.9b01407 for details.
    """
    name: str = dataclasses.field(init=False, default='training', **dataclass_kw_only)

    A: float = dataclasses.field(**dataclass_kw_only)
    num_samples: int = dataclasses.field(**dataclass_kw_only)
    target: float = dataclasses.field(**dataclass_kw_only)
    tau: float = dataclasses.field(**dataclass_kw_only)
    tolerance: float = dataclasses.field(**dataclass_kw_only)

    def build_plugin(self):
        """Builds training phase plugin for BRER simulations.

        Returns
        -------
        WorkElement
            a gmxapi WorkElement to be added to the workflow graph
        """
        WorkElement = _get_workelement()
        potential = WorkElement(
            namespace="brer.md",
            operation="brer_restraint",
            depends=[],
            params=dataclasses.asdict(self)
        )
        potential.name = str(self.sites)
        return potential


@dataclasses.dataclass
class ConvergencePluginConfig(PluginConfig):
    """Configure BRER potential for the convergence phase.

    The BRER convergence phase uses the MD potential provided by :py:func:`brer.linearstop_restraint`.

    See https://pubs.acs.org/doi/10.1021/acs.jpclett.9b01407 for details.
    """
    name: str = dataclasses.field(init=False, default='convergence', **dataclass_kw_only)

    alpha: float = dataclasses.field(**dataclass_kw_only)
    sample_period: float = dataclasses.field(**dataclass_kw_only)
    target: float = dataclasses.field(**dataclass_kw_only)
    tolerance: float = dataclasses.field(**dataclass_kw_only)

    def build_plugin(self):
        """Builds convergence phase plugin for BRER simulations.

        Returns
        -------
        WorkElement
            a gmxapi WorkElement to be added to the workflow graph

        Raises
        ------
        ValueError
            If inappropriate values are detected for any fields.
        """
        if self.alpha == 0.0:
            raise ValueError('Read a non-sensical alpha value: 0.0')
        WorkElement = _get_workelement()
        potential = WorkElement(
            namespace="brer.md",
            operation="linearstop_restraint",
            depends=[],
            params=dataclasses.asdict(self))
        potential.name = str(self.sites)
        return potential


@dataclasses.dataclass
class ProductionPluginConfig(PluginConfig):
    """Configure BRER potential for the convergence phase.

    The BRER production phase uses the MD potential provided by :py:func:`brer.linear_restraint`.

    See https://pubs.acs.org/doi/10.1021/acs.jpclett.9b01407 for details.
    """
    name: str = dataclasses.field(init=False, default='production', **dataclass_kw_only)

    alpha: float = dataclasses.field(**dataclass_kw_only)
    sample_period: float = dataclasses.field(**dataclass_kw_only)
    target: float = dataclasses.field(**dataclass_kw_only)

    def build_plugin(self):
        """Builds production phase plugin for BRER simulations.

        Returns
        -------
        WorkElement
            a gmxapi WorkElement to be added to the workflow graph

        Raises
        ------
        ValueError
            If inappropriate values are detected for any fields.
        """
        if self.alpha == 0.0:
            raise ValueError('Read a non-sensical alpha value: 0.0')
        WorkElement = _get_workelement()
        potential = WorkElement(
            namespace="brer.md",
            operation="linear_restraint",
            depends=[],
            params=dataclasses.asdict(self))
        potential.name = str(self.sites)
        return potential
