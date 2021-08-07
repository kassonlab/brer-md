#!/bin/bash
set -ev

$PYTHON -m pip install .
pushd run_brer/tests
  $PYTHON -m pytest -rA -l --log-cli-level=info --cov=run_brer .
popd