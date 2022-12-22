#!/bin/bash
set -ev

export GMX_DOUBLE=OFF
export GMX_MPI=OFF
export GMX_THREAD_MPI=ON

export GMX_SRC_DIR=gromacs-release-2019

ccache -s

pushd $HOME
 [ -d ${GMX_SRC_DIR} ] || \
    git clone \
        --depth=1 \
        -b release-2019 \
        https://gitlab.com/gromacs/gromacs.git \
        ${GMX_SRC_DIR}
 pushd ${GMX_SRC_DIR}
  pwd
  if [ -f "${PATCH_FILE}" ]; then
    echo "Applying ${PATCH_FILE}:"
    cat ${PATCH_FILE}
    patch -p1 < ${PATCH_FILE}
  fi
  rm -rf build
  mkdir build
  pushd build
   cmake -G Ninja \
         -DCMAKE_CXX_COMPILER=$CXX \
         -DGMX_ENABLE_CCACHE=ON \
         -DCMAKE_C_COMPILER=$CC \
         -DGMX_DOUBLE=$GMX_DOUBLE \
         -DGMX_MPI=$GMX_MPI \
         -DGMX_THREAD_MPI=$GMX_THREAD_MPI \
         -DGMXAPI=ON \
         -DCMAKE_INSTALL_PREFIX=$HOME/install/gromacs-release-2019 \
         ..
   cmake --build . --target install
  popd
 popd
popd
ccache -s
