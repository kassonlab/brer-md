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
# For now, I will read from jsons that contain the metadata for each pair.
# The name from the json will be used as the names of each individual PairData object.
# This could certainly be done differently.

test_dir = '/home/jennifer/Git/run_brer/tests/'
my_file_names = ['{}/052_210.json'.format(test_dir), '{}/105_216.json'.format(test_dir)]

data = [json.load(open(my_file_name, 'r')) for my_file_name in my_file_names]

re_sampler = ReSampler()

for single_pair_data in data:
    name = single_pair_data['name']
    pair_data = PairData(name=name)
    pair_data.__setattr__('metadata', single_pair_data)
    re_sampler.add_pair(pair_data)

""" Get a new set of distributions if you are at the beginning of a simulation """

if state.get('iteration') == 0 and state.get('phase') == 'training':
    print(re_sampler.get_names())
