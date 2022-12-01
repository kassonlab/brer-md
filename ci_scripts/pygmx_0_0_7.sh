#!/bin/bash
set -ev

pushd $HOME
 rm -rf gmxapi
 git clone --depth=1 -b release-0_0_7 https://github.com/kassonlab/gmxapi.git
 pushd gmxapi
  rm -rf build
  mkdir -p build
  pushd build
   cmake --version
   cmake .. -DCMAKE_CXX_COMPILER=$CXX -DCMAKE_C_COMPILER=$CC -DPYTHON_EXECUTABLE=`which python`
   make -j2 install
  popd
 popd
 mpiexec -n 2 `which python` -m mpi4py -m pytest --log-cli-level=WARN --pyargs gmx -s
# mpiexec -n 2 `which python` -m mpi4py -m pytest --log-cli-level=DEBUG --pyargs gmx -s --verbose
 ccache -s
popd
