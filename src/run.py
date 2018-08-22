"""
Classes for *running* BRER simulations.
"""

import argparse
from src.state import *
from src.pair_data import *
from src.directory_helper import DirectoryHelper
import os


class RunConfig(MetaData):
    def __init__(self):
        super().__init__('run_config')

    def scan_data(self, data):
        """
        This scans a dictionary from either a State obj or PairData obj
        and stores whatever parameters it needs for a Run.
        :param data: either type State or type PairData
        """
        for requirement in self.get_requirements():
            if requirement in data.get_dictionary().keys():
                self.set(requirement, data.get(requirement))


class TrainingRunConfig(RunConfig):
    def __init__(self):
        super(RunConfig, self).__init__(name='training')
        self.set_requirements([
            'sites', 'A', 'tau', 'tolerance', 'nSamples', 'parameter_filename'
        ])


class ConvergenceRunConfig(RunConfig):
    def __init__(self):
        super(RunConfig, self).__init__(name='convergence')
        self.set_requirements([
            'sites', 'alpha', 'target', 'tolerance', 'samplePeriod',
            'logging_filename'
        ])


class ProductionRunConfig(RunConfig):
    def __init__(self):
        super(RunConfig, self).__init__(name='production')
        self.set_requirements(['sites', 'R0', 'k'])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', help='ensemble member', type=int)
    args = parser.parse_args()

    n = args.n

    # assumes that you're running this script from top level directory
    cwd = '/home/jennifer/Git/run_brer/tests'
    state_json = '{}/state.json'.format(cwd)
    pairs_json = '{}/pair_data.json'.format(cwd)

    pds = MultiPair()
    if not os.path.exists(pairs_json):
        raise ValueError(
            'The restraint data file {} does not exist'.format(pairs_json))

    pds.read_from_json(pairs_json)

    states = MultiState()
    if os.path.exists(state_json):
        states.read_from_json(filename=state_json)
    else:
        states.restart(names=pds.get_names())
        states.write_to_json(filename=state_json)

    num_restraints = states.__sizeof__()

    sample_state = states[0]
    print(
        sample_state.__getattribute__('name'),
        sample_state.get_as_dictionary())

    general_params = {
        'ensemble_num': n,
        'iteration': sample_state.get('iteration'),
        'phase': sample_state.get('phase')
    }

    directory_builder = DirectoryHelper(top_dir=cwd, param_dict=general_params)

    directory_builder.build_working_dir()
    directory_builder.change_dir('phase')

    # Check to make sure the pair data and state data match up
    if set(pds.get_names()) != set(states.get_names()):
        raise ValueError(
            'The pair data names ({}) do not match the state data names ({})'.
            format(pds.get_names(), states.get_names()))

    # Make working directory if it does not exist

    phase = general_params['phase']

    if phase == 'training':
        run_config = TrainingRunConfig()
        # Do re-sampling if needed
        if not os.path.exists('{}/state.cpt'.format(directory_builder.get_dir('phase'))):
            targets = pds.re_sample()
            print(targets)
    elif phase == 'convergence':
        run_config = ConvergenceRunConfig()
    else:
        run_config = ProductionRunConfig()

    all_restraints = [run_config]*num_restraints

    for restraint in range(num_restraints):
        all_restraints[restraint].scan_data(states[restraint])