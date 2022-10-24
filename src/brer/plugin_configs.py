"""Classes used to build gmxapi plugins for all phases of a BRER iteration.

Each class corresponds to ONE restraint since gmxapi plugins each correspond to one restraint.
"""
import dataclasses
import sys
import typing
from abc import ABC
from abc import abstractmethod
from functools import singledispatchmethod

assert sys.version_info.major >= 3

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
if sys.version_info.major > 3 or sys.version_info.minor >= 10:
    field_kwargs = {'kw_only': True}
else:
    field_kwargs = {}


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
    """Abstract class used to build training, convergence, and production
    plugins."""
    name: str = dataclasses.field(init=False, **field_kwargs)
    sites: List[int] = dataclasses.field(**field_kwargs)
    logging_filename: str = dataclasses.field(**field_kwargs)

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
        return cls(**{key: getattr(obj, key) for key in [field.name for field in dataclasses.fields(cls) if
                                                         field.init] if hasattr(obj, key)})

    @create_from.register
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
    name: str = dataclasses.field(init=False, default='training', **field_kwargs)

    A: float = dataclasses.field(**field_kwargs)
    num_samples: int = dataclasses.field(**field_kwargs)
    target: float = dataclasses.field(**field_kwargs)
    tau: float = dataclasses.field(**field_kwargs)
    tolerance: float = dataclasses.field(**field_kwargs)

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
    name: str = dataclasses.field(init=False, default='convergence', **field_kwargs)

    alpha: float = dataclasses.field(**field_kwargs)
    sample_period: float = dataclasses.field(**field_kwargs)
    target: float = dataclasses.field(**field_kwargs)
    tolerance: float = dataclasses.field(**field_kwargs)

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
    name: str = dataclasses.field(init=False, default='production', **field_kwargs)

    alpha: float = dataclasses.field(**field_kwargs)
    sample_period: float = dataclasses.field(**field_kwargs)
    target: float = dataclasses.field(**field_kwargs)

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
