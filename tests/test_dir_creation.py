from src.directory_helper import set_working_dir
import pytest
import os


@pytest.fixture()
def working_dir():
    my_dir_struct = {
        'top_dir': '{}/tests'.format(os.getcwd()),
        'ensemble_num': 1,
        'iteration': 0,
        'phase': 'training'
    }
    return my_dir_struct


# TODO: Do a quick pytest loop to build directories for one iteration
def test_set_working_dir(working_dir):
    set_working_dir(working_dir)
