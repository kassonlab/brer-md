# from run_brer.run_data import RunData
# from run_brer.run_config import RunConfig
# from run_brer.pair_data import MultiPair
import json
import os
from pathlib import Path

import pytest


@pytest.fixture()
def data_dir():
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    return '{}/data'.format(parent_dir)


# @pytest.fixture()
# def multi_pair_data(tmpdir, data_dir):
#     """
#     Tests read/write functionality for MultiPair
#     Returns a MultiPair() object for further testing.
#     :param tmpdir:
#     :param data_dir:
#     :return:
#     """

#     multi_pair_data = MultiPair()
#     multi_pair_data.read_from_json('{}/pair_data.json'.format(data_dir))
#     multi_pair_data.write_to_json('{}/pair_data.json'.format(tmpdir))
#     return multi_pair_data


# @pytest.fixture()
# def run_data(multi_pair_data):
#     """
#     Constructs a RunData object from pair data.
#     :param multi_pair_data: MultiPair object used for initialization.
#     :return: Initialized RunData obj.
#     """
#     run_data = RunData()
#     for name in multi_pair_data.get_names():
#         idx = multi_pair_data.name_to_id(name)
#         run_data.from_pair_data(multi_pair_data[idx])
#     return run_data


# @pytest.fixture()
# def rc(tmpdir, data_dir):
#     init = {
#         'tpr': '{}/topol.tpr'.format(data_dir),
#         'ensemble_dir': tmpdir,
#         'ensemble_num': 1,
#         'pairs_json': '{}/pair_data.json'.format(data_dir)
#     }
#     os.mkdir('{}/mem_{}'.format(tmpdir, 1))
#     config = RunConfig(**init)
#     config.run_data.set(tolerance=100, A=10, tau=0.02, production_time=0.02)
#     return RunConfig(**init)


@pytest.fixture(scope='session')
def raw_pair_data():
    """
    Three DEER distributions for testing purposes.

    :return: contents of :file:`run_brer/data/pair_data.json`
    """
    data_file = Path(__file__).parent.parent / 'data' / 'pair_data.json'
    with open(data_file, 'r') as fh:
        pair_data = json.load(fh)
    assert pair_data["196_228"]["distribution"][0] == 3.0993964770242886e-55
    return pair_data
