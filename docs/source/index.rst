.. run BRER documentation master file, created by
   sphinx-quickstart on Thu Jun 27 11:01:26 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to BRER's documentation!
====================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:


   user_api
   developer_api

brer
========

|Build Status|
|Documentation Status|

.. todo:: Restore additional project tests and reactivate badges.
    See https://github.com/kassonlab/run_brer/issues/2

.. .. |codecov| |Language grade: Python| |Total alerts|

Set of scripts for running BRER simulations using gmxapi. Details of
this method may be found at:

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
-  gmxapi for GROMACS 2019. See `recommended
   installation <https://gmxapi.readthedocs.io/en/release-0_0_7/install.html#installation>`__,
   or

   1. Install `GROMACS
      2019 <http://manual.gromacs.org/2019-current/index.html>`__,
      configured with
      ```-DGMXAPI=ON`` <http://manual.gromacs.org/2019-current/dev-manual/build-system.html#cmake-GMXAPI>`__.
      Currently, ``gmxapi`` does not support domain decomposition with
      MPI, so if you want these simulations to run fast, be sure to
      compile with GPU support.
   2. Install gmxapi 0.0.7 `Python
      package <https://github.com/kassonlab/gmxapi/tree/release-0_0_7>`__.
      This code has only been tested with `Gromacs
      2019 <http://manual.gromacs.org/documentation/2019/index.html>`__.

-  The `plugin
   code <https://github.com/jmhays/sample_restraint/tree/brer>`__ for
   BRER. Please make sure you install the ``brer`` branch, *NOT*
   ``master`` .

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
   git clone https://github.com/kassonlab/brer-md.git
   cd brer-md
   pip install .

Running BRER
------------

Launching a single ensemble member
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
hope to soon use the ``gmxapi``
`features <https://github.com/kassonlab/gmxapi>`__ that allow a user to
launch many ensemble members in one job.

.. |Documentation Status| image:: https://github.com/kassonlab/brer-md/actions/workflows/pages/pages-build-deployment/badge.svg?branch=master
   :target: https://github.com/kassonlab/brer-md/actions/workflows/pages/pages-build-deployment
.. |Language grade: Python| image:: https://img.shields.io/lgtm/grade/python/g/jmhays/run_brer.svg?logo=lgtm&logoWidth=18
.. |Total alerts| image:: https://img.shields.io/lgtm/alerts/g/jmhays/run_brer.svg?logo=lgtm&logoWidth=18
.. |Build Status| image:: https://github.com/kassonlab/brer-md/actions/workflows/test.yml/badge.svg?branch=master
   :target: https://github.com/kassonlab/brer-md/actions/workflows/test.yml
.. |codecov| image:: https://codecov.io/gh/jmhays/run_brer/branch/master/graph/badge.svg

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
