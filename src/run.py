"""
Run script for performing multiple BRER iterations.
"""

from glob import glob
from src.state import State
from src.resampler import *
from src.directory_helper import *
from src.auxil_logger import Auxiliary

# import gmx
""" 
    Initializing the run. We have to set up both the state and the pair data.
"""
logger = Auxiliary()

# Initialize the state
ensemble_num = 1
state_filename = "../tests/state.json"  # Where you want to store metadata
state = State()
logger.initialized('BRER state')

if os.path.exists(state_filename):
    state.read_from_json(state_filename)
    logger.read_from_file(state_filename)
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
my_file_names = glob(
    '{}/[0-9][0-9][0-9]_[0-9][0-9][0-9].json'.format(test_dir))
data = [json.load(open(my_file_name, 'r')) for my_file_name in my_file_names]

logger.read_from_file(my_file_names)
num_pairs = len(data)
logger.report_parameter("number of restraints", num_pairs)

re_sampler = ReSampler()
for x in data:
    pair_data = PairData(name=x['name'])
    pair_data.load_metadata(x)
    re_sampler.add_pair(pair_data)

logger.initialized('restraint metadata')

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
    How the directory structure is organized:
    - This script should be run from your "top" directory (where 
      you are planning to run all your ensemble members)
    - The top directory contains ensemble member subdirectories 
      This script is intended to handle just ONE ensemble member, 
      so we'll only be concerned with a single member subdirectory.
    - The example below is for the first iteration (iter 0) of one 
      of the members. Future iterations would go in directories 
      1,2,...y
.   
├── 0
│   ├── converge_dist
│   │   ├── state.cpt
│   │   ├── state_prev.cpt
│   │   └── traj_comp.part0001.xtc
│   ├── production
│   │   ├── confout.part0005.gro
│   │   ├── state.cpt
│   │   ├── state_prev.cpt
│   │   ├── state_step4622560.cpt
│   │   ├── traj_comp.part0002.xtc
│   └── training_alpha
│       ├── state.cpt
│       ├── state_prev.cpt
│       └── traj_comp.part0001.xtc
├── state.json 
├── submit.slurm
└── syx.tpr


"""
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

my_dir_struct = {
    'top_dir': test_dir,
    'ensemble_num': ensemble_num,
    'iteration': state.get('iteration'),
    'phase': state.get('phase')
}

set_working_dir(my_dir_struct)
