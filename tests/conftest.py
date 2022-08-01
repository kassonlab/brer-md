import json
import sys

import pytest

if sys.version_info.major > 3 or sys.version_info.minor >= 10:
    from importlib.resources import files, as_file
else:
    from importlib_resources import files, as_file


@pytest.fixture(scope='session')
def simulation_input():
    source = files('run_brer').joinpath('data', 'topol.tpr')
    with as_file(source) as tpr_file:
        yield tpr_file


@pytest.fixture(scope='session')
def pair_data_file():
    source = files('run_brer').joinpath('data', 'pair_data.json')
    with as_file(source) as pair_data:
        yield pair_data


@pytest.fixture(scope='session')
def raw_pair_data():
    """
    Three DEER distributions for testing purposes.

    :return: contents of :file:`run_brer/data/pair_data.json`
    """
    raw_data = files('run_brer').joinpath('data', 'pair_data.json').read_text()
    pair_data = json.loads(raw_data)
    assert pair_data["196_228"]["distribution"][0] == 3.0993964770242886e-55
    return pair_data
