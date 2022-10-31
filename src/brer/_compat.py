"""Compatibility support for older Python versions.

Provide some imports and alternative definitions depending on Python version
so that we don't have to have `sys.version_info` conditionals scattered around
the package.

* Built-in and :py:mod:`collections.abc` containers are not Generic before 3.9.
* Dataclasses allow tighter control in Python 3.10

"""
__all__ = ['Iterable', 'List', 'Mapping', 'MutableMapping', 'dataclass_kw_only', 'dataclass_slots']

import collections.abc
import sys
import typing

assert sys.version_info.major >= 3
_T = typing.TypeVar('_T')

if sys.version_info.major > 3 or sys.version_info.minor >= 9:
    List: typing.Generic[_T] = list
    """Generic list type."""
else:
    from typing import List

if sys.version_info.major > 3 or sys.version_info.minor >= 9:
    Iterable = collections.abc.Iterable
    Mapping = collections.abc.Mapping
    MutableMapping = collections.abc.MutableMapping
else:
    Iterable = typing.Iterable
    Mapping = typing.Mapping
    MutableMapping = typing.MutableMapping

dataclass_kw_only: collections.abc.Mapping
"""Require keyword arguments for dataclass initialization.

We are trying to reduce ambiguity by confirming that the ``name`` field is often
redundant with a key used to store such an object. To that end, we are trying
to be more mindful of how these objects are constructed. We will try to prevent
some previous usage patterns in which data structures were initialized with a
positional *name* argument, which was then overwritten by a subsequent *set()*.
Dataclass init arguments can be provided positionally in the order in which
fields are defined, unless *kw_only=True* (after Py 3.10).
"""

dataclass_slots: collections.abc.Mapping
"""Disallow adding attributes to instances.

In Python >= 3.10, the *slots* option to dataclasses will help keep fields
from accidentally getting added to instances.
"""

if sys.version_info.major > 3 or sys.version_info.minor >= 10:
    dataclass_kw_only = {'kw_only': True}
    dataclass_slots = {'slots': True}
else:
    dataclass_kw_only = {}
    dataclass_slots = {}
