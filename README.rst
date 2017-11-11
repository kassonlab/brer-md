==========================
Sample MD restraint plugin
==========================

This repository provides a complete and working implementation of a GROMACS restraint potential. It is intended as both
a tutorial and a template for implementing new custom restraint potentials.

The basics
==========

We use CMake to configure and build a C++ library and a Python module for interacting with it.

This sample project builds a C++ library named ``harmonicpotential``.
The actual filename will be something like ``libharmonicpotential.so`` or ``harmonicpotential.dll``
or something depending on your operating system.
This library is used to build a Python module named ``myplugin``.

Building and running the tests
==============================

C++ and Python tests.


Python
------

Python tests can be run from the root directory of the repository with ``pytest tests``.

This command causes the directory named ``tests`` to be explored for Python files with names like ``test_*.py`` or
``*_test.py``.
Matching files will be imported and any functions with similarly obvious names will be run and errors reported.
In particular, ``assert`` statements will be evaluated to perform individual tests.
See also https://docs.pytest.org/en/latest/goodpractices.html#test-discovery

The tests assume that the package is already installed or is available on the default Python path (such as by setting
the ``PYTHONPATH`` environment variable).
If you just run ``pytest`` with no arguments, it will discover and try to run tests from elsewhere in the repository
that were not intended, and they will fail.

