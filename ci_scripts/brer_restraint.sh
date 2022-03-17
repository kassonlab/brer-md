#!/bin/bash
set -ev

pushd $HOME
  [ -d brer_plugin ] || git clone --depth=1 https://github.com/kassonlab/brer_plugin.git
  pushd brer_plugin
    rm -rf build
    mkdir build
    pushd build
      cmake .. -DPYTHON_EXECUTABLE=$PYTHON
      make -j2 install
      make -j2 test
      $PYTHON -c "import brer"
    popd
    pushd tests
      $PYTHON -m pytest
      mpiexec -n 2 $PYTHON -m mpi4py -m pytest --log-cli-level=DEBUG -s --verbose
    popd
  popd
popd
