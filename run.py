#!/usr/bin/env python
"""
Example run script for BRER simulations
"""

from run_brer import RunConfig as config

paths = {
    'tpr': '/home/jennifer/Git/run_brer/tests/syx.tpr',
    'working_dir': '/home/jennifer/test-brer',
    'state_json': '/home/jennifer/Git/run_brer/tests/state.json',
    'pairs_json': '/home/jennifer/Git/run_brer/tests/pair_data.json'
}

my_config = config(**paths)

my_config.run()
