# BRER restraint plugin

[![Build Status](https://github.com/kassonlab/brer_plugin/actions/workflows/test.yml/badge.svg?branch=master)](https://github.com/kassonlab/brer_plugin/actions/workflows/test.yml)

This is the [repository](https://github.com/kassonlab/brer_plugin)
for the `brer` Python module,
a C++ extension that provides the GROMACS MD plugin for use with
https://github.com/kassonlab/run_brer

## Requirements

To build and install the GROMACS MD plugin, first install GROMACS and `gmxapi` as described for `run_brer`.

**NOTE:** For several recent versions of GROMACS, the "legacy API" needs to be enabled when GROMACS is configured.
The `GMX_INSTALL_LEGACY_API` GROMACS CMake variable is **not documented**.
Example:

    cmake /path/to/gromacs/sources -DGMX_INSTALL_LEGACY_API=ON -DGMX_THREAD_MPI=ON

You will also need a reasonably recent version of `cmake`. `cmake` is a command line tool that is often
already available, but you can be sure of getting a recent version by activating your python environment
and just doing `pip install cmake`.

## Installation

This is a simple C++ extension module that can be attached to a GROMACS molecular dynamics (MD) simulator
through the gmxapi Python interface. The module is necessary for research workflows based on the
`run_brer` Python package. See https://github.com/kassonlab/run_brer for more information.

Once you have identified your compilers and Python installation (or virtual environment), use `cmake` to
configure, build, and install.

See https://github.com/kassonlab/brer_plugin/releases for tagged releases. For development code, clone the repository and use the default branch.

### Complete example

This example assumes
* I have already activated a Python (virtual) environment in which `gmxapi` is installed, and
* A GROMACS installation is available on my `$PATH` (such as by "sourcing" the GMXRC or calling `module load gromacs` in an HPC environment)

To confirm:
* `gmx --version` (or `gmx_mpi`, `gmx_d`, etc. for other configurations) should ...
* `which python` should show a path to a python virtual environment for Python 3.7 or later.
* `pip list` should include `gmxapi`

To download, build, and install the `brer` Python module:

```bash
git clone https://github.com/kassonlab/brer_plugin.git
cd brer_plugin
mkdir build
cd build
cmake ..
make
make install
```

## References

Hays, J. M., Cafiso, D. S., & Kasson, P. M.
Hybrid Refinement of Heterogeneous Conformational Ensembles using Spectroscopic Data.
*The Journal of Physical Chemistry Letters* 2019.
DOI: [10.1021/acs.jpclett.9b01407](https://pubs.acs.org/doi/10.1021/acs.jpclett.9b01407)

Irrgang, M. E., Hays, J. M., & Kasson, P. M. gmxapi: a high-level
interface for advanced control and extension of molecular dynamics
simulations. *Bioinformatics* 2018. DOI:
[10.1093/bioinformatics/bty484](https://doi.org/10.1093/bioinformatics/bty484)
