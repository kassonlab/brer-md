#!/bin/bash
set -ev

export GMX_DOUBLE=OFF

export GMX_SRC_DIR=gromacs-2020

ccache -s

pushd $HOME
 [ -d $GMX_SRC_DIR ] || \
    git clone \
        --depth=1 \
        -b release-2020 \
        https://github.com/gromacs/gromacs.git \
        ${GMX_SRC_DIR}
 pushd ${GMX_SRC_DIR}
  pwd
  rm -rf build
  mkdir build
  pushd build
   cmake -DCMAKE_CXX_COMPILER=$CXX \
         -DGMX_ENABLE_CCACHE=ON \
         -DCMAKE_C_COMPILER=$CC \
         -DGMX_DOUBLE=$GMX_DOUBLE \
         -DGMX_MPI=$GMX_MPI \
         -DGMX_THREAD_MPI=$GMX_THREAD_MPI \
         -DGMXAPI=ON \
         -DCMAKE_INSTALL_PREFIX=$HOME/install/gromacs_2020 \
         ..
   make -j2 install
  popd
 popd
popd
ccache -s
