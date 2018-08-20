"""
Run script for performing multiple BRER iterations.
"""

from glob import glob
from abc import ABC, abstractmethod
from src.state import State
from src.resampler import *
from src.directory_helper import *
# from src.auxil_logger import Auxiliary
import logging

# import gmx


def expected_parameters(phase):
    params = []
    if phase == 'training':
        params = ['sites', 'A', 'tau', 'target', 'nSamples', 'parameter_filename']
    return params


class RunConfiguration(ABC):
    """ Abstract base class for BRER runs """
    def __init__(self, tpr_filename, state: State):
        self.tpr_filename = tpr_filename  # path to tpr for run
        self.working_dir = ''  # path to working directory. Will be set later in each subclass
        self.pair_data = []  # pair data. Will be loaded from json.
        self.state = state

        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger('BRER')

    def build_working_directory(self, top_dir):
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
        """
        Checks to see if the working directory for current state of BRER simulation exists. If it does not, creates the
        directory. Then changes to that directory.
        :param dir_info: A dictionary containing data on the directory structure.
        :return:
        """
        top_dir = top_dir
        ensemble_num = self.state.get('ensemble_num')
        iteration = self.state.get('iteration')
        phase = self.state.get('phase')

        working_dir = '{}/mem_{}/{}/{}'.format(top_dir, ensemble_num, iteration,
                                               phase)
        if not os.path.exists(working_dir):
            tree = [
                '{}/mem_{}'.format(top_dir, ensemble_num), '{}/mem_{}/{}'.format(
                    top_dir, ensemble_num, iteration)
            ]
            for leaf in tree:
                if not os.path.exists(leaf):
                    os.mkdir(leaf)
            os.mkdir(working_dir)

    @abstractmethod
    def run(self):
        pass


class RunTraining(RunConfiguration):
    """
    This class implements the training run of BRER
    """
    def __init__(self, tpr_filename):
        super().__init__(tpr_filename=tpr_filename)
# class Run:
#     def __init__(self, tpr_filename):
#         self._logger = Auxiliary()
#         self._directory_structure = {}
#         self._brer_state = State()
#         self._tpr_filename = tpr_filename
#         self._num_pairs = 0
#         self._re_sampler = ReSampler()
#
#     @property
#     def tpr_filename(self):
#         return self._tpr_filename
#     @tpr_filename.getter
#     def tpr_filename(self):
#         return self._tpr_filename
#
#     @property
#     def num_pairs(self):
#         return self._num_pairs
#     @num_pairs.getter
#     def num_pairs(self):
#         return self._num_pairs
#
#     def initialize(self, top_directory: str, state_filename: str, ensemble_num: int, pair_data_filenames: list):
#         """
#             Initializing the run. We have to set up both the state and the pair data.
#         """
#
#         # Initialize the state
#
#         if os.path.exists(state_filename):
#             self._brer_state.read_from_json(state_filename)
#             self._logger.read_from_file(state_filename)
#         else:
#             self._brer_state.restart()
#             self._brer_state.write_to_json(state_filename)
#
#         if not self._brer_state.is_complete_record():
#             raise ValueError(
#                 'You are missing parameters in your state.json file.\nProvided: {}\nRequires: {}'.
#                 format(self._brer_state.keys, self._brer_state.required_keys))
#
#         # Initialize the pair data
#         # For now, I will read from jsons that contain the metadata for each pair.
#         # The name from the json will be used as the names of each individual PairData object.
#         # This could certainly be done differently.
#
#         data = [
#             json.load(open(my_file_name, 'r'))
#             for my_file_name in pair_data_filenames
#         ]
#
#         self._logger.read_from_file(my_file_names)
#         self._num_pairs = len(data)
#         self._logger.report_parameter("number of restraints", self._num_pairs)
#
#         for x in data:
#             pair_data = PairData(name=x['name'])
#             pair_data.load_metadata(x)
#             self._re_sampler.add_pair(pair_data)
#
#         self._logger.initialized('restraint metadata')
#
#
#         self._directory_structure = {
#             'top_dir': top_directory,
#             'ensemble_num': ensemble_num,
#             'iteration': self._brer_state.get('iteration'),
#             'phase': self._brer_state.get('phase')
#         }
#
#         set_working_dir(self._directory_structure)
#
#         if (self._brer_state.get('phase') == 'training') and (
#                 not os.path.exists(self._brer_state.get('gmx_cpt'))):
#             new_targets = self._re_sampler.resample()
#             self._brer_state.set('targets', new_targets)
#
#         self._logger.initialized('targets: {}'.format(
#             self._brer_state.get('targets')))
#
#     def run(self, **kwargs):
#         """
#         Runs single iteration of BRER. Can restart from either the convergence phase or the production phase of the
#         simulation. Training coming soon.
#         :param kwargs:
#         :return:
#         """
#         pass


if __name__ == "__main__":

    top_dir = '/home/jennifer/Git/run_brer/tests/'
    my_file_names = glob(
        '{}/[0-9][0-9][0-9]_[0-9][0-9][0-9].json'.format(top_dir))

    run = Run('syx.tpr')
    """Now initialize the run and cd to run directory"""
    run.initialize(top_dir, '{}/state.json'.format(top_dir), 1, my_file_names)
    run.run(
        A=50,
        tau=50,
        alpha_tol=2.5,
        dist_tol=2.5,
        num_samples=25,
        sample_period=100)

