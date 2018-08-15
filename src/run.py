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
state_filename = "../tests/state.json"  # Where you want to store metadata
state = State()

if os.path.exists(state_filename):
    state.read_from_json(state_filename)
else:
    state.restart()
    state.write_to_json(state_filename)

if not state.is_complete_record():
    raise ValueError(
        'You are missing parameters in your state.json file.\nProvided: {}\nRequires: {}'.
        format(state.keys, state.required_keys))

# Initialize the pair data
# For now, I will read from jsons that contain the metadata for each pair.
# The name from the json will be used as the names of each individual PairData object.
# This could certainly be done differently.

test_dir = '/home/jennifer/Git/run_brer/tests/'
my_file_names = [
    '{}/052_210.json'.format(test_dir), '{}/105_216.json'.format(test_dir)
]

data = [json.load(open(my_file_name, 'r')) for my_file_name in my_file_names]

re_sampler = ReSampler()

for single_pair_data in data:
    pair_data = PairData(name=single_pair_data['name'])
    pair_data.load_metadata(single_pair_data)
    re_sampler.add_pair(pair_data)


# Get a new set of distributions if you are at the beginning of a simulation
# Otherwise, grab the old targets.
if state.get('phase') == 'training':
    targets = re_sampler.resample()
# else:
#     targets = state.get('targets')
if state.get('phase') == 'convergence':
    pass
else:
    pass

