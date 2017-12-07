#!/usr/bin/env bash
cd /external && \
mkdir -p plugin-build && \
cd plugin-build && \
gmxapi_DIR=/usr/local/gromacs cmake ../samplerestraint -DPYTHON_EXECUTABLE=`which python` && \
make && \
make test && \
cd /external && \
PYTHONPATH=plugin-build/src/pythonmodule python -m pytest samplerestraint/tests --verbose
