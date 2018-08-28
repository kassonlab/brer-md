#!/usr/bin/env python
"""
Example run script for BRER simulations
"""

from run_brer import RunConfig as config
import sys

sys.path.append('/home/jennifer/Git/brer/build/src/pythonmodule')

init = {
    'tpr': '/home/jennifer/Git/run_brer/tests/syx.tpr',
    'working_dir': '/home/jennifer/test-brer',
    'ensemble_num': 0,
    'pairs_json': '/home/jennifer/Git/run_brer/tests/pair_data.json'
}

my_config = config(**init)

my_config.run()
