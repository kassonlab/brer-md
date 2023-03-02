BRER MD
=======

|Build and test| |Documentation| |codecov|

Source: https://github.com/kassonlab/brer-md

Documentation: https://kassonlab.github.io/brer-md/

The ``brer`` Python package provides a set of scripts for running
Bias-Resampling Ensemble Refinement (BRER) simulations using
`gmxapi <https://gmxapi.org/>`__. Details of the BRER
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

-  Python 3.8 or newer.
-  A GROMACS installation supporting client software builds.
-  `gmxapi <https://manual.gromacs.org/current/gmxapi>`__ for GROMACS.

``brer`` includes a simple C++ extension module that can be attached to a GROMACS
molecular dynamics (MD) simulator through the gmxapi Python interface.
GROMACS installations (and GROMACS dependencies) can be built rather specifically
for their computing environments. The ``brer`` package is distributed as source
code that must be built for a specific GROMACS installation.

.. note::
    For several recent versions of GROMACS, the “legacy API” needs
    to be enabled **explicitly** when GROMACS is configured.
    The ``GMX_INSTALL_LEGACY_API`` GROMACS CMake variable is **not documented**.
    Example::

       cmake /path/to/gromacs/sources -DGMX_INSTALL_LEGACY_API=ON -DGMX_THREAD_MPI=ON

Python environment
~~~~~~~~~~~~~~~~~~

We recommend using a separate Python virtual environment for each research project,
tied to specific versions of the software tools you use. If your computing
environment provides Python packages such as ``mpi4py`` that may be difficult
to configure, you should try to use the provided packages in your virtual environment.
Example::

    python3 -m venv --system-site-packages myprojectvenv
    . myprojectvenv/bin/activate
    myprojectvenv/bin/python -m pip install --upgrade pip

Then, follow the installation instructions for GROMACS and
`gmxapi <https://manual.gromacs.org/current/gmxapi/userguide/install.html>`__.

Build and Install
~~~~~~~~~~~~~~~~~

We recommend installing the package with
`pip <https://pip.pypa.io/en/stable/>`__.

Generally, ``pip`` will automatically install any package dependencies.

If a GROMACS installation is discoverable (you have "sourced" a GMXRC file or
defined a GROMACS_DIR environment variable), then the ``gmxapi`` Python package
will be installed automatically with the ``brer`` package.
Simply::

    pip install git+https://github.com/kassonlab/brer-md.git

If you prefer to install ``gmxapi`` separately (such as to specify an older
package version), you can provide ``--no-deps`` and ``--no-build-isolation``
to ``pip install``, and the existing ``gmxapi`` installation will be used.

You can pre-install (other) required packages using the
`requirements.txt <https://github.com/kassonlab/brer-md/blob/main/requirements.txt>`__
file.
The ``requirements.txt`` file does not include the ``gmxapi`` dependency.

Example::

    pip show gmxapi |grep Version
    # Version: 0.3.1
    wget https://github.com/kassonlab/brer-md/blob/main/requirements.txt
    pip install -r requirements.txt
    pip install --no-deps --no-build-isolation brer

The Python package builder will manage compilation of the C++ GROMACS client
using `cmake
documentation <https://cmake.org/cmake/help/latest/manual/cmake.1.html>`__.
If the GROMACS installation or C++ toolchain cannot be determined automatically,
you may need to provide additional hints.
See also `GROMACS release
notes <https://manual.gromacs.org/2022/release-notes/2022/major/portability.html#cmake-toolchain-file-replaced-with-cache-file>`__.

Example::

    gmx --version |grep prefix
    # Data prefix:  /Users/eric/install/gromacs2022
    CMAKE_ARGS="-C /Users/eric/install/gromacs2022/share/cmake/gromacs/gromacs-hints.cmake" \
    pip install brer

Running BRER
------------

Launching a single ensemble member.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An example script, ``run.py`` , is provided for ensemble simulations.

Let’s work through it piece by piece.

::

   #!/usr/bin/env python

   """
   Example run script
   for BRER simulations
   """

   import brer.run_config as rc
   import sys

The ``import brer.run_config`` statement imports a ``RunConfig``
object, which handles the following things **for a single ensemble
member**:

1. Initializing/setting up parameters for the BRER run.
2. Launching the run.

Then we provide some files and directory paths to the ``RunConfig``
object.

::

   init = {
       'tpr': '/home/jennifer/Git/brer-md/tests/syx.tpr',
       'ensemble_dir': '/home/jennifer/test-brer',
       'ensemble_num': 5,
       'pairs_json': '/home/jennifer/Git/brer-md/tests/pair_data.json'
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
   repository: ``src/brer/data/pair_data.json``

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
~~~~~~~~~~~~~~~~~~~~~

Right now, the way to launch an ensemble is to launch multiple jobs. We
hope to soon use the ``gmxapi`` features that allow a user to
launch many ensemble members in one job.

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

You will have to rebuild and reinstall the ``brer`` module.

Remove any cached built packages::

    pip cache remove brer

If you previously installed without build isolation you may have ``build`` or
``dist`` directories that should be removed, as well.

When attempting to build the package again, provide extra hints to CMake through
the Python package builder by adding strings to the CMAKE_ARGS environment
variable.

For GROMACS 2022 and newer, you would invoke ``cmake`` with something
like the following. (The exact path will depend on your installation.)

::

    CMAKE_ARGS="-C /path/to/gromacs_installation/share/cmake/gromacs/gromacs-hints.cmake" \
    pip install brer

For GROMACS 2021 and older,

::

    CMAKE_ARGS="-DCMAKE_TOOLCHAIN_FILE=/path/to/gromacs_installation/share/cmake/gromacs/gromacs-toolchain.cmake" \
    pip install brer

See `GROMACS release
notes <https://manual.gromacs.org/2022/release-notes/2022/major/portability.html#cmake-toolchain-file-replaced-with-cache-file>`__.

Problems building a GROMACS 2019 stack
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For some C++ standard library installations, GROMACS 2019 exhibits compiler errors.
The sources need to be patched. You can use the ``ci_scripts/limits.patch`` file in this
repository as a guide to manually edit the source, or use the ``patch`` command line tool.
Example::

    cd /path/to/gromacs2019/sources
    wget https://raw.githubusercontent.com/kassonlab/brer-md/main/ci_scripts/limits.patch
    patch -p1 < limits.patch

For GROMACS 2019, you will need gmxapi 0.0.7.
See https://gmxapi.readthedocs.io/en/release-0_0_7/.

You will have to prevent ``brer-md`` from trying to install a more recent version of gmxapi.
Install the dependencies explicitly, then suppress automatic dependency resolution
when installing brer-md.
Exxample::

    wget https://raw.githubusercontent.com/kassonlab/brer-md/main/requirements.txt
    pip install -r requirements.txt
    pip install --no-deps brer-md

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

.. |Build and test| image:: https://github.com/kassonlab/brer-md/actions/workflows/test.yml/badge.svg?branch=main
   :target: https://github.com/kassonlab/brer-md/actions/workflows/test.yml
.. |Documentation| image:: https://github.com/kassonlab/brer-md/actions/workflows/pages/pages-build-deployment/badge.svg?branch=main
   :target: https://github.com/kassonlab/brer-md/actions/workflows/pages/pages-build-deployment
.. |codecov| image:: https://codecov.io/gh/kassonlab/brer-md/branch/main/graph/badge.svg
   :target: https://codecov.io/gh/kassonlab/brer-md
