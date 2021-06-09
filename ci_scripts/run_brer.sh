#!/bin/bash
set -ev

$PYTHON setup.py install
$PYTHON -m pytest -rA -l --log-cli-level=info --cov=run_brer --pyargs run_brer
