#!/bin/bash
set -ev

$PYTHON -m pip install .
$PYTHON -m pytest -rA -l --log-cli-level=info --cov=run_brer tests
