#!/usr/bin/env bash
# To be run in a docker image with $HOME/develop mounted to /develop with
#     docker run -v $HOME/develop/:/develop/ -ti plugintesting bash

cd /external && \
mkdir -p gromacs-build && \
cd gromacs-build && \
rm -f CMakeCache.txt && \
cmake ../gromacs-source -DGMX_DEVELOPER_BUILD=ON \
    -DGMX_BUILD_HELP=OFF \
    -DCMAKE_BUILD_TYPE=Debug \
    -DCMAKE_CXX_FLAGS_DEBUG='-O0 -g3' \
    -DCMAKE_C_FLAGS_DEBUG='-O0 -g3' \
    -DGMX_USE_RDTSCP=OFF && \
make -j4 && \
make install
