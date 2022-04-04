# run_brer

[![Build and test](https://github.com/kassonlab/run_brer/actions/workflows/test.yml/badge.svg?branch=master)](https://github.com/kassonlab/run_brer/actions/workflows/test.yml)
[![Documentation](https://github.com/kassonlab/run_brer/actions/workflows/pages/pages-build-deployment/badge.svg?branch=master)](https://github.com/kassonlab/run_brer/actions/workflows/pages/pages-build-deployment)

This project is hosted in a git repository at https://github.com/kassonlab/run_brer

Project documentation is available in the repository or at
[https://kassonlab.github.io/run_brer/](https://kassonlab.github.io/run_brer/).

The `run_brer` Python package provides a set of scripts for running BRER simulations using [gmxapi](https://gmxapi.org/).
Details of this method may be found in:

Hays, J. M., Cafiso, D. S., & Kasson, P. M. Hybrid Refinement of Heterogeneous Conformational Ensembles using Spectroscopic Data. *The Journal of Physical Chemistry Letters*. DOI: [10.1021/acs.jpclett.9b01407](https://pubs.acs.org/doi/10.1021/acs.jpclett.9b01407)

## Installation

### Requirements

If you're going to use a pip or a conda environment, you'll need:

- Python 3.X
- gmxapi for GROMACS 2019 or newer.
    * Install [GROMACS 2019 and gmxapi 0.0.7](https://gmxapi.readthedocs.io/en/release-0_0_7/install.html#installation),
  or
    * Install [current GROMACS and gmxapi >= 0.1](https://manual.gromacs.org/current/gmxapi/userguide/install.html)

- The [plugin code](https://github.com/kassonlab/brer_plugin) for BRER.

Otherwise, you can just use a Singularity container!

### Singularity 

By far the easiest option!

If you have the latest and greatest Singuarity (v > 3), you can pull the container from the cloud repository:

 `singularity pull library://kassonlab/default/brer:latest` 

For instructions on using the container, please see the [singularity-brer](https://github.com/kassonlab/singularity-brer) repository.

### Conda environment

I suggest running this in a conda environment rather than `pip install` . The following conda command will handle all the `gmxapi` and `sample_restraint` python dependencies, as well as the ones for this repository.

1. `conda create -n BRER numpy scipy networkx setuptools mpi4py cmake` 

    If you want to run the tests, then install `pytest` as well.

2. Source the environment and then `pip install`: 

```
source activate BRER
git clone https://github.com/kassonlab/run_brer.git
cd run_brer
pip install .
```

## Running BRER

#### Launching a single ensemble member.

An example script, `run.py` , is provided for ensemble simulations.

Let's work through it piece by piece.

```
#!/usr/bin/env python

"""
Example run script
for BRER simulations
"""

import run_brer.run_config as rc
import sys
```

The `import run_brer.run_config` statement imports a `RunConfig` object, which handles the following things _**for a single ensemble member**_:

1. Initializing/setting up parameters for the BRER run.
2. Launching the run. 

Then we provide some files and directory paths to the `RunConfig` object. 

```
init = {
    'tpr': '/home/jennifer/Git/run_brer/tests/syx.tpr',
    'ensemble_dir': '/home/jennifer/test-brer',
    'ensemble_num': 5,
    'pairs_json': '/home/jennifer/Git/run_brer/tests/pair_data.json'
}

config = rc.RunConfig(**init)
```

In order to run a BRER simulation, we need to provide :

1. a `tpr` (compatible with GROMACS 2019).
2. The path to our ensemble. This directory should contain subdirectories of the form `mem_<my ensemble number>` 
3. The ensemble number. This is an integer used to identify which ensemble member we are running and thus, the subdirectory in which we will be running our simulations.
4. The path to the DEER metadata. Please see the example json in this repository: `run_brer/data/pair_data.json` 

Finally, we launch the run!

```
config.run()
```

You may change various parameters before launching the run using `config.set(**kwargs)` . For example:

```
config = rc.RunConfig(**init)
config.set(A=100)
config.run()
```

resets the energy constant A to 100 kcal/mol/nm^2 before launching a run.

#### Launching an ensemble

Right now, the way to launch an ensemble is to launch multiple jobs. We hope to soon use the `gmxapi` [features](https://github.com/kassonlab/gmxapi) that allow a user to launch many ensemble members in one job.
