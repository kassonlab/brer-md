"""
Run script for performing multiple BRER iterations.
"""

import os
from src.state import State
from src.resampler import *
# import gmx

""" Initializing the run. """
state_filename = "state.json"  # Where you want to store metadata:w
state = State()

if os.path.exists(state_filename):
    state.read_from_json(state_filename)
else:
    state.restart()
    state.write_to_json(state_filename)


