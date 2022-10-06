run_brer
========

|Build and test| |Documentation| |codecov|

This project is hosted in a git repository at
https://github.com/kassonlab/run_brer

Project documentation is available in the repository or at
https://kassonlab.github.io/run_brer/.

The ``run_brer`` Python package provides a set of scripts for running
BRER simulations using `gmxapi <https://gmxapi.org/>`__. Details of this
method may be found in:

Hays, J. M., Cafiso, D. S., & Kasson, P. M. Hybrid Refinement of
Heterogeneous Conformational Ensembles using Spectroscopic Data. *The
Journal of Physical Chemistry Letters*. DOI:
`10.1021/acs.jpclett.9b01407 <https://pubs.acs.org/doi/10.1021/acs.jpclett.9b01407>`__

Installation
------------

Requirements
~~~~~~~~~~~~

If you’re going to use a pip or a conda environment, you’ll need:

-  Python 3.X
-  gmxapi for GROMACS 2019 or newer.

   -  Install `GROMACS 2019 and gmxapi
      0.0.7 <https://gmxapi.readthedocs.io/en/release-0_0_7/install.html#installation>`__,
      or
   -  Install `current GROMACS and gmxapi >=
      0.1 <https://manual.gromacs.org/current/gmxapi/userguide/install.html>`__

-  The `plugin code <https://github.com/kassonlab/brer_plugin>`__ for
   BRER.

Otherwise, you can just use a Singularity container!

Singularity
~~~~~~~~~~~

By far the easiest option!

If you have the latest and greatest Singuarity (v > 3), you can pull the
container from the cloud repository:

``singularity pull library://kassonlab/default/brer:latest``

For instructions on using the container, please see the
`singularity-brer <https://github.com/kassonlab/singularity-brer>`__
repository.

Conda environment
~~~~~~~~~~~~~~~~~

I suggest running this in a conda environment rather than
``pip install`` . The following conda command will handle all the
``gmxapi`` and ``sample_restraint`` python dependencies, as well as the
ones for this repository.

1. ``conda create -n BRER numpy scipy networkx setuptools mpi4py cmake``

   If you want to run the tests, then install ``pytest`` as well.

2. Source the environment and then ``pip install``:

::

   source activate BRER
   git clone https://github.com/kassonlab/run_brer.git
   cd run_brer
   pip install .

Running BRER
------------

Launching a single ensemble member.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

An example script, ``run.py`` , is provided for ensemble simulations.

Let’s work through it piece by piece.

::

   #!/usr/bin/env python

   """
   Example run script
   for BRER simulations
   """

   import run_brer.run_config as rc
   import sys

The ``import run_brer.run_config`` statement imports a ``RunConfig``
object, which handles the following things **for a single ensemble
member**:

1. Initializing/setting up parameters for the BRER run.
2. Launching the run.

Then we provide some files and directory paths to the ``RunConfig``
object.

::

   init = {
       'tpr': '/home/jennifer/Git/run_brer/tests/syx.tpr',
       'ensemble_dir': '/home/jennifer/test-brer',
       'ensemble_num': 5,
       'pairs_json': '/home/jennifer/Git/run_brer/tests/pair_data.json'
   }

   config = rc.RunConfig(**init)

In order to run a BRER simulation, we need to provide :

1. a ``tpr`` (compatible with GROMACS 2019).
2. The path to our ensemble. This directory should contain
   subdirectories of the form ``mem_<my ensemble number>``
3. The ensemble number. This is an integer used to identify which
   ensemble member we are running and thus, the subdirectory in which we
   will be running our simulations.
4. The path to the DEER metadata. Please see the example json in this
   repository: ``run_brer/data/pair_data.json``

Finally, we launch the run!

::

   config.run()

You may change various parameters before launching the run using
``config.set(**kwargs)`` . For example:

::

   config = rc.RunConfig(**init)
   config.set(A=100)
   config.run()

resets the energy constant A to 100 kcal/mol/nm^2 before launching a
run.

Launching an ensemble
^^^^^^^^^^^^^^^^^^^^^

Right now, the way to launch an ensemble is to launch multiple jobs. We
hope to soon use the ``gmxapi``
`features <https://github.com/kassonlab/gmxapi>`__ that allow a user to
launch many ensemble members in one job.

BRER restraint plugin
=====================

|Build Status|

This is the `repository <https://github.com/kassonlab/brer_plugin>`__
for the ``brer`` Python module, a C++ extension that provides the
GROMACS MD plugin for use with https://github.com/kassonlab/run_brer

.. _requirements-1:

Requirements
------------

To build and install the GROMACS MD plugin, first install GROMACS and
``gmxapi`` as described for ``run_brer``.

**NOTE:** For several recent versions of GROMACS, the “legacy API” needs
to be enabled when GROMACS is configured. The ``GMX_INSTALL_LEGACY_API``
GROMACS CMake variable is **not documented**. Example:

::

   cmake /path/to/gromacs/sources -DGMX_INSTALL_LEGACY_API=ON -DGMX_THREAD_MPI=ON

You will also need a reasonably recent version of ``cmake``. ``cmake``
is a command line tool that is often already available, but you can be
sure of getting a recent version by activating your python environment
and just doing ``pip install cmake``.

.. _installation-1:

Installation
------------

This is a simple C++ extension module that can be attached to a GROMACS
molecular dynamics (MD) simulator through the gmxapi Python interface.
The module is necessary for research workflows based on the ``run_brer``
Python package. See https://github.com/kassonlab/run_brer for more
information.

Once you have identified your compilers and Python installation (or
virtual environment), use ``cmake`` to configure, build, and install.
Refer to `cmake
documentation <https://cmake.org/cmake/help/latest/manual/cmake.1.html>`__
for usage and options. Note that GROMACS installs a CMake hints (or
toolchain) file to help you specify the correct compiler toolchain to
``cmake``. See `GROMACS release
notes <https://manual.gromacs.org/2022/release-notes/2022/major/portability.html#cmake-toolchain-file-replaced-with-cache-file>`__.

See https://github.com/kassonlab/brer_plugin/releases for tagged
releases. For development code, clone the repository and use the default
branch.

Complete example
~~~~~~~~~~~~~~~~

This example assumes \* I have already activated a Python (virtual)
environment in which ``gmxapi`` is installed, and \* A GROMACS
installation is available on my ``$PATH`` (such as by “sourcing” the
GMXRC or calling ``module load gromacs`` in an HPC environment) \* I am
using GROMACS 2022, which provides a CMake “hints” file, which I will
(optionally) provide when calling ``cmake``.

To confirm: \* ``gmx --version`` (or ``gmx_mpi``, ``gmx_d``, etc. for
other configurations) should … \* ``which python`` should show a path to
a python virtual environment for Python 3.7 or later. \* ``pip list``
should include ``gmxapi``

To download, build, and install the ``brer`` Python module:

.. code:: bash

   git clone https://github.com/kassonlab/brer_plugin.git
   cd brer_plugin
   mkdir build
   cd build
   cmake ..
   make
   make install

In the example above, the ``-C`` argument is usually optional. (See
below.)

Troubleshooting
---------------

Mismatched compiler toolchain
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

One of the most common installation problems is related to incompatible
compiler toolchains between GROMACS, gmxapi, and the plugin module. \*
CMake may warn “You are compiling with a different C++ compiler from the
one that was used to compile GROMACS.” \* When you ``import`` the
``brer`` module, you may get an error like the following.
``ImportError: dlopen(...): symbol not found in flat namespace '__ZN6gmxapi10MDWorkSpec9addModuleENSt3__110shared_ptrINS_8MDModuleEEE'``

You can either set the ``CMAKE_CXX_COMPILER``, explicitly, or you can
use the GROMACS-installed CMake hints file.

You will have to rebuild and reinstall the ``brer`` module. First,
remove the ``CMakeCache.txt`` file from the build directory.

For GROMACS 2022 and newer, you would invoke ``cmake`` with something
like the following. (The exact path will depend on your installation.)

::

   cmake .. -C /path/to/gromacs_installation/share/cmake/gromacs/gromacs-hints.cmake

For GROMACS 2021 and older,

::

   cmake .. -DCMAKE_TOOLCHAIN_FILE=/path/to/gromacs_installation/share/cmake/gromacs/gromacs-toolchain.cmake

See `GROMACS release
notes <https://manual.gromacs.org/2022/release-notes/2022/major/portability.html#cmake-toolchain-file-replaced-with-cache-file>`__.

References
----------

Hays, J. M., Cafiso, D. S., & Kasson, P. M. Hybrid Refinement of
Heterogeneous Conformational Ensembles using Spectroscopic Data. *The
Journal of Physical Chemistry Letters* 2019. DOI:
`10.1021/acs.jpclett.9b01407 <https://pubs.acs.org/doi/10.1021/acs.jpclett.9b01407>`__

Irrgang, M. E., Hays, J. M., & Kasson, P. M. gmxapi: a high-level
interface for advanced control and extension of molecular dynamics
simulations. *Bioinformatics* 2018. DOI:
`10.1093/bioinformatics/bty484 <https://doi.org/10.1093/bioinformatics/bty484>`__

.. |Build and test| image:: https://github.com/kassonlab/run_brer/actions/workflows/test.yml/badge.svg?branch=master
   :target: https://github.com/kassonlab/run_brer/actions/workflows/test.yml
.. |Documentation| image:: https://github.com/kassonlab/run_brer/actions/workflows/pages/pages-build-deployment/badge.svg?branch=master
   :target: https://github.com/kassonlab/run_brer/actions/workflows/pages/pages-build-deployment
.. |codecov| image:: https://codecov.io/gh/kassonlab/run_brer/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/kassonlab/run_brer
.. |Build Status| image:: https://github.com/kassonlab/brer_plugin/actions/workflows/test.yml/badge.svg?branch=master
   :target: https://github.com/kassonlab/brer_plugin/actions/workflows/test.yml
