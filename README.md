# run_brer 
[![Documentation Status](https://readthedocs.org/projects/run-brer/badge/?version=latest)](https://run-brer.readthedocs.io/en/latest/?badge=latest)
[![https://www.singularity-hub.org/static/img/hosted-singularity--hub-%23e32929.svg](https://www.singularity-hub.org/static/img/hosted-singularity--hub-%23e32929.svg)](https://singularity-hub.org/collections/1761)


master:
[![Build Status](https://travis-ci.com/jmhays/run_brer.svg?token=zQbC3QZqV1zHSGhQXUTP&branch=master)](https://travis-ci.com/jmhays/run_brer)
[![codecov](https://codecov.io/gh/jmhays/run_brer/branch/master/graph/badge.svg)](https://codecov.io/gh/jmhays/run_brer)
devel:
[![Build Status](https://travis-ci.com/jmhays/run_brer.svg?token=zQbC3QZqV1zHSGhQXUTP&branch=devel)](https://travis-ci.com/jmhays/run_brer)
[![codecov](https://codecov.io/gh/jmhays/run_brer/branch/devel/graph/badge.svg)](https://codecov.io/gh/jmhays/run_brer)

Set of scripts for running BRER simulations using gmxapi. 

## Installation
### Requirements
If you're going to use a pip or a conda environment, you'll need:
- Python 3.X
- An installation of [gromacs-gmxapi](http://github.com/kassonlab/gromacs-gmxapi). Currently, `gmxapi` does not support 
domain decomposition with MPI, so if you want these simulations to run fast, be sure to compile with GPU support.
- An installation of [gmxapi](https://github.com/kassonlab/gmxapi). 
This code has only been tested with [release 0.0.6](https://github.com/kassonlab/gmxapi/releases/tag/v0.0.6).
- The [plugin code](https://github.com/jmhays/sample_restraint/tree/deer) for BRER. Please make sure you install the 
`deer` branch, _*NOT*_ `master`.

Otherwise, you can just use a Singularity container!

### Singularity 
By far the easiest option! Just pull the container hosted on singularity hub:

`singularity pull -name myimage.simg shub://jmhays/singularity-brer`

For instructions on using the container, please see [this](https://github.com/jmhays/singularity-brer) repository.
### Conda environment
I suggest running this in a conda environment rather than `pip install`. The following conda command will handle all 
the `gmxapi` and `sample_restraint` python dependencies, as well as the ones for this repository.

1. `conda create -n BRER numpy scipy networkx setuptools mpi4py cmake`

    If you want to run the tests, then install `pytest` as well.

2. Source, the environment, then use the standard Python `setup.py` protocol:
```
source activate BRER
git clone https://github.com/jmhays/run_brer.git
cd run_brer
python setup.py install
```


## Running BRER
#### Launching a single ensemble member.
An example script, `run.py`, is provided for ensemble simulations. 

Let's work through it piece by piece.
```
#!/usr/bin/env python
"""
Example run script for BRER simulations
"""

import run_brer.run_config as rc
import sys

```
The `import run_brer.run_config` statement imports a `RunConfig` object, which handles the following things 
_**for a single ensemble member**_:
1. Initializing/setting up parameters for the BRER run.
2. Launching the run. 

Next, we add the `gmxapi` plugin to the `PYTHONPATH`. You'll need to change this line of code to reflect where you have 
installed the `brer` repository.
```
sys.path.append('/builds/brer/build/src/pythonmodule')
```
Just FYI, the path shown above is actually the correct path if you're working with the Singualrity container :)

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
1. a `tpr` (compatible with GROMACS 2017).
2. The path to our ensemble. This directory should contain subdirectories of the form `mem_<my ensemble number>`
3. The ensemble number. This is an integer used to identify which ensemble member we are running and thus, the subdirectory in which we will be running our simulations.
4. The path to the DEER metadata. Please see the example json in this repository: `run_brer/data/pair_data.json`

Finally, we launch the run!
```
config.run()
```

You may change various parameters before launching the run using `config.set(**kwargs)`. For example:
```
config = rc.RunConfig(**init)
config.set(A=100)
config.run()
```
resets the energy constant A to 100 kcal/mol/nm^2 before launching a run.


#### Launching an ensemble
Right now, the way to launch an ensemble is to launch multiple jobs. We hope to soon use the `gmxapi` 
[features](https://github.com/kassonlab/gmxapi) that allow a user to launch many ensemble members in one job.
