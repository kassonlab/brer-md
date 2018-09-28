import pytest


def test_missing_keys(run_data):
    """
    Checks that there are no missing keys after initialization of RunData object.
    :param run_data: example RunData object.
    """
    assert (not run_data.general_params.get_missing_keys())


def test_pair_parameters(run_data):
    assert (set(run_data.pair_params.keys()) == {'196_228', '105_216', '052_210'})


def test_general_parameters(run_data):
    assert (run_data.general_params.get_requirements() == [
        'ensemble_num', 'iteration', 'phase', 'start_time', 'A', 'tau', 'tolerance', 'nSamples', 'samplePeriod',
        'production_time'
    ])
