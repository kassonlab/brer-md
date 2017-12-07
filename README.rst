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

The plugin requires `libgmxapi` to build.

The Python module `gmx` is required for testing.

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

Docker
======

For a quick start, consider these instructions to set up a docker image with the dependencies installed and the
plugin ready to go.

Prepare to build the docker image
---------------------------------

Refer to the Dockerfile in this repository:

This Dockerfile is used to produce a working installation of gmxpy and libgmxapi
against which to develop plugins. The sample plugin is also built, but not installed.
These dependencies are currently in private repositories, so they should be
retrieved before building the docker image so that the sources are available in
the same directory as the Dockerfile as 'gromacs-gmxapi' and 'gmxpy'.

    # Get this repository and this Dockerfile (if you haven't already)
    mkdir docker-build-dir
    cd docker-build-dir
    git clone git@bitbucket.org:kassonlab/samplerestraint.git
    cp -r samplerestraint/docker/* ./

    # Get the dependencies
    git clone git@bitbucket.org:kassonlab/gromacs_api.git gromacs-gmxapi
    (cd gromacs-gmxapi && git checkout develop-0.0.3)
    git clone git@bitbucket.org:kassonlab/gmxpy-dev.git gmxpy
    (cd gmxpy && git checkout develop)

Build an image, create a container, and run build scripts
---------------------------------------------------------

Just build from these Dockerfiles

    # '.' uses the Dockerfile in the current directory, '-t plugintest' names the image.
    # First build gromacs in an image named gmxapi
    docker build . -f Dockerfile.gmxapi -t gmxapi
    # Then build an image named 'plugintest' with gmxpy installed.
    docker build . -t plugintest

Run a temporary container from the image, removing when done. Default command builds plugin.

    docker run --rm --init -ti plugintest

Run a shell in a temporary container from the image, removing when done.

    docker run --rm --init -ti plugintest bash

Create a container from which to run bash, then start it.

    docker --init --name buildplugincontainer -ti plugintest bash
    docker start buildplugincontainer

Run provided scripts in the running container.

    docker exec -ti buildplugincontainer bash /external/scripts/buildplugin.sh

More
----

Stop the container and save a snapshot of it as a new image.

    docker stop buildplugincontainer
    docker commit buildplugincontainer plugintest:build20171027

Start a fresh container from the checkpoint

    # Remove any old container with the same name
    docker rm buildplugincontainer

    docker create --name buildplugincontainer --init -ti plugintest:build20171027 bash
    docker start buildplugincontainer

    # or

    docker run --name buildplugincontainer --init -ti plugintest:build20171027 bash

Update the image

    # Update files without rebuilding image
    docker create --name patch plugintest
    docker cp $HOME/docker/plugintest-repo/scripts patch:/external/
    docker commit patch plugintest:build20171028
    docker rm patch

Start a temporary container from the checkpoint

    docker run --rm -v /Users/eric/develop/:/develop/ --init -ti plugintest:build20171028 bash -x scripts/setuptoolsinstall.sh
