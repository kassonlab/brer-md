#!/bin/bash
set -ev

pushd $HOME
 [ -d run_ebmetad ] || git clone --depth=1 --no-single-branch https://github.com/jmhays/run_brer.git
 pushd run_brer
  git branch -a
  if [ "${TRAVIS_BRANCH}" != "master" ] ; then
   git checkout devel
  else
   git checkout master
  fi
  $PYTHON setup.py install
  PYTHONPATH=$HOME/sample_restraint/build/src/pythonmodule $PYTHON -m pytest --cov=./run_brer
 popd
popd
