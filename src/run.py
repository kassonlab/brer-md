"""
Run script for BRER simulations
"""

import argparse
from src.state import *
from src.pair_data import *
from src.run_configs import *
from src.directory_helper import DirectoryHelper
import os
import copy
import gmx
import sys

sys.path.append('/home/jennifer/Git/brer/build/src/pythonmodule')

run_parameters = {
    'ensemble_num': 0,
    'iteration': 0,
    'phase': 'training',
    'sites': [],
    'A': 50,
    'tau': 50,
    'tolerance': 0.25,
    'nSamples': 50,
    'parameter_filename': '',
    'logging_filename': '',
    'alpha': 0,
    'target': 0,
    'samplePeriod': 100,
    'R0': 0,
    'k': 0
}


def set_multiple_configurations(run_config, states: MultiState, pairs_data: MultiPair):
    # You will need one run configuration per restraint
    size = states.__sizeof__()
    all_restraints = []

    for i in range(size):
        new_restraint = copy.deepcopy(run_config)
        new_restraint.scan_dictionary(run_parameters)
        new_restraint.set_parameters(
            parameter_filename='{}.log'.format(states[i].name),
            logging_filename='{}.log'.format(states[i].name))
        new_restraint.scan_metadata(states[i])
        new_restraint.scan_metadata(pairs_data[i])
        all_restraints.append(new_restraint)
    return all_restraints


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', help='ensemble member', type=int)
    parser.add_argument('-s', help='tpr', type=str)
    args = parser.parse_args()

    n = args.n
    tpr = args.s

    if n is None:
        raise ValueError('Must provide a valid ensemble number.')
    if not tpr:
        raise ValueError('{} is not a valid tpr'.format(tpr))

    run_parameters['ensemble_num'] = n

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

    # Check to make sure the pair data and state data match up
    if set(pds.get_names()) != set(states.get_names()):
        raise ValueError(
            'The pair data names ({}) do not match the state data names ({})'.
            format(pds.get_names(), states.get_names()))

    sample_state = states[0]

    # Make working directory if it does not exist, change to that directory
    directory_builder = DirectoryHelper(top_dir=cwd, param_dict=run_parameters)
    directory_builder.build_working_dir()
    directory_builder.change_dir(level='phase')

    # Choose the appropriate RunConfig for the current phase of the simulation
    phase = sample_state.get('phase')
    if phase == 'training':
        run_config = TrainingRunConfig()

        # Do re-sampling if needed
        if not os.path.exists('{}/state.cpt'.format(
                directory_builder.get_dir('phase'))):
            targets = pds.re_sample()
            print('The new targets are: {}'.format(targets))
            for state in states:
                state.set('target', targets[state.name])
            states.write_to_json(filename=state_json)
        md = gmx.workflow.from_tpr(input=tpr, append_output=False)

    elif phase == 'convergence':
        run_config = ConvergenceRunConfig()
        md = gmx.workflow.from_tpr(tpr, append_output=False)

    elif phase == 'production':
        run_config = ProductionRunConfig()
        md = gmx.workflow.from_tpr(tpr, steps=5000000, append_output=False)

    else:
        raise ValueError(
            '{} is not an appropriate phase of BRER simulation'.format(phase))

    restraints = set_multiple_configurations(run_config, states, pds)

    for restraint in restraints:
        potential = restraint.build_gmxapi_plugin()
        md.add_dependency(potential)
        print(potential.params)

    print(os.getcwd())
    context = gmx.context.ParallelArrayContext(md, workdir_list=os.getcwd())
    with context as session:
        session.run()
