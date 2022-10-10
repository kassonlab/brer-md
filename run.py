#!/usr/bin/env python
"""
Example run script for BRER simulations
"""

import brer.run_config as rc
import sys

sys.path.append('/home/jennifer/Git/brer/build/src/pythonmodule')

init = {
    'tpr': '/home/jennifer/Git/brer-md/src/brer/data/topol.tpr',
    'ensemble_dir': '/home/jennifer/test-brer',
    'ensemble_num': 5,
    'pairs_json': '/home/jennifer/Git/brer-md/src/brer/data/pair_data.json'
}

config = rc.RunConfig(**init)

config.run_data.set(A=100)

config.run()
