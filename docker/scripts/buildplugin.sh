#!/usr/bin/env bash
mkdir -p plugin-build && \
(cd plugin-build && \
gmxapi_DIR=/usr/local/gromacs cmake ../samplerestraint -DPYTHON_EXECUTABLE=`which python` && \
LD_LIBRARY_PATH=/opt/conda/lib make && \
make test) && \
PYTHONPATH=plugin-build/src/pythonmodule python -m pytest samplerestraint/tests --verbose
