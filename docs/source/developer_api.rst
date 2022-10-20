Developer API
##############

directory_helper
================
.. automodule:: brer.directory_helper

.. autoclass:: brer.directory_helper.DirectoryHelper
    :members:

metadata
========
.. automodule:: brer.metadata

.. autoclass:: brer.metadata.MetaData
    :members:
.. autoclass:: brer.metadata.MultiMetaData
    :members:

pair_data
=========
.. automodule:: brer.pair_data

.. autoclass:: brer.pair_data.PairData
    :members:

.. autoclass:: brer.pair_data.MultiPair
    :members:

plugin_configs
==============
.. automodule:: brer.plugin_configs

.. autoclass:: brer.plugin_configs.PluginConfig
    :members:

.. autoclass:: brer.plugin_configs.TrainingPluginConfig
    :members:

.. autoclass:: brer.plugin_configs.ConvergencePluginConfig
    :members:

.. autoclass:: brer.plugin_configs.ProductionPluginConfig
    :members:

MD potentials
=============

.. automodule:: brer.md

As of 2022, we are still using the old gmxapi 0.0.7 style
`WorkElement <https://gmxapi.readthedocs.io/en/release-0_0_7/reference.html#gmx.workflow.WorkElement>`__
to connect pluggable extension code to the GROMACS simulator.
The WorkElement is constructed by the `brer.plugin_configs` module by encoding
an entry point function and its input parameters.

Entry points
------------

The following creation functions are used to support creation of gmxapi
pluggable GROMACS restraint potentials.
The entry point function consumes a
:py:class:`gmxapi.simulation.workflow.WorkElement`
to produce an opaque object that can finish setting up the interactions with the
gmxapi simulator lifetime management.

In addition to the parameters described below, all restraint potentials require
a :term:`sites` parameter.

.. glossary::

    sites
        (*list[int]*) Describe the pair distance relevant to an instance of a BRER potential.
        The list is a sequence of two or more sites, expressed as atom indices
        in the molecular model. The first and last index define the origin and tip
        of the displacement vector. In the case that this vector may be ambiguous
        with respect to periodic boundary conditions (if the sites are likely to
        ever be further apart on the molecule than half of the shortest simulation
        box dimension), additional indices can be inserted between the first and
        last element to define a sequence of vectors that can reliably sum to the
        intended vector.

.. todo:: Auto-extract the parameter structure docs once parameters are expressed more cleanly in the C++ code.

.. py:function:: linear_restraint()

    Configure the BRER potential used for the production phase.

    :param float alpha: coupling parameter.
    :param float target: site displacement distance to bias towards.
    :param float sample_period: time between samples (simulator time units)
    :param str logging_filename: output file

.. todo:: Get parameters from makeLineareStopParams docstring.

.. py:function:: linearstop_restraint()

    Configure the BRER potential used during the convergence phase.

    :param float alpha: coupling parameter.
    :param float target: site displacement distance to bias towards.
    :param float tolerance: convergence detection parameter
    :param float sample_period: time between samples (simulator time units)
    :param str logging_filename: output file

.. autofunction:: brer_restraint()

    Configure the BRER potential used for the training phase.

    :param float A: control the maximum energy input while training the coupling parameter.
    :param float tau: time constant for sample smoothing (simulator time units).
    :param float tolerance: convergence detection parameter
    :param float target: site displacement distance to bias towards.
    :param float num_samples: number of samples to average at each update.
    :param str logging_filename: output file

    During execution, the pair distance is regularly sampled. To smooth fluctuations,
    a rolling average is maintained over a period *tau*. A measurement is recorded
    and the average is updated at intervals of *tau/num_samples*.

    For additional explanation of *A*, see White and Voth, https://doi.org/10.1021/ct500320c

.. These objects are not user-facing, and their architecture will be updated a
   little bit with more expressive templating.

    Internal details
    ----------------

    At run time, :py:mod:`gmxapi.simulation` uses the entry point functions to
    create Builders that are plugged into the simulation launcher.

    .. autoclass:: LinearBuilder
        :members:

    .. autoclass:: LinearStopBuilder
        :members:

    .. autoclass:: BRERBuilder
        :members:
