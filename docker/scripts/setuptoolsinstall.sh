#!/usr/bin/env bash
# Build and install the gmx python module

pip uninstall -y gmx

cd /external/gmxpy && \
gmxapi_DIR=/usr/local/gromacs python setup.py install --verbose

gmxapi_DIR=/usr/local/gromacs python setup.py test

