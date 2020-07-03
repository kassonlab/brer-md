#!/bin/bash
set -ev

$PYTHON setup.py install
# PYTHONPATH=$HOME/sample_restraint/build/src/pythonmodule $PYTHON -m pytest --cov=./run_brer
$PYTHON -m pytest --cov=run_brer --pyargs run_brer -s
