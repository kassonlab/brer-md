"""
Run script for performing multiple BRER iterations.
"""

import os
from src.state import State
from src.resampler import *
# import gmx
""" 
    Initializing the run. We have to set up both the state and the pair data.
"""

# Initialize the state
state_filename = "state.json"  # Where you want to store metadata
state = State()

if os.path.exists(state_filename):
    state.read_from_json(state_filename)
else:
    state.restart()
    state.write_to_json(state_filename)

# Initialize the pair data
# For now, I will read from a json that contains distributions labeled by residue numbers.
# The keys from the json will be used as the names of each individual PairData object.
# This could certainly be done differently.

data = json.load(
    open('/home/jennifer/Git/run_brer/tests/distributions.json', 'r'))
names = list(data.keys())
print(names)
num_pairs = len(names)

re_sampler = ReSampler()

for i in range(num_pairs):
    name = names[i]
    pair_data = PairData(name=name)
    pair_data.__setattr__('distribution', data[name])
    re_sampler.add_pair(pair_data)

""" Get a new set of distributions if you are at the beginning of a simulation """

if state.get('iteration') == 0 and state.get('phase') == 'training':
    pass
