"""Unit tests and regression for RunData classes."""

import pytest

from brer.pair_data import PairData
from brer.run_data import GeneralParams
from brer.run_data import PairParams
from brer.run_data import RunData


def test_pair_parameters(raw_pair_data):
    """Set PairParams objects from PairData objects. Check that there are no
    missing keys.

    Parameters
    ----------
    raw_pair_data : dict
        raw pair data from conftest.py
    """
    for name in raw_pair_data:
        # Check our assumption about the redundancy of 'name'.
        assert name == raw_pair_data[name]['name']
        pd = PairData(**raw_pair_data[name])
        pp = PairParams(name, sites=pd.sites)
        for default_param in ('alpha', 'target'):
            assert hasattr(pp, default_param)


def test_run_data(tmpdir, raw_pair_data):
    """Test creation of RunData object from PairData objects and check no
    missing keys.

    Parameters
    ----------
    tmpdir : str
        pytest temporary directory
    raw_pair_data : dict
        raw pair data from conftest.py
    """
    rd = RunData()

    for name in raw_pair_data:
        # Check our assumption about the redundancy of 'name'.
        assert name == raw_pair_data[name]['name']
        pd = PairData(**raw_pair_data[name])
        rd.from_pair_data(pd)

    # Get an arbitrary but valid name.
    name = tuple(raw_pair_data.keys())[-1]
    # Test the setting function
    with pytest.raises(ValueError):
        rd.set(tau=0.1, name=name)
    with pytest.raises(ValueError):
        rd.set(alpha=1.)
    rd.set(alpha=1., name=name)

    # Test getting
    rd.get("alpha", name=name)
    with pytest.raises(ValueError):
        rd.get("alpha")

    # Test read/write of the state
    rd.save_config("{}/state.json".format(tmpdir))
    old_rd = rd
    rd = RunData()
    rd.load_config("{}/state.json".format(tmpdir))

    assert old_rd.as_dictionary() == rd.as_dictionary()

    # Test clearing pair data
    rd.clear_pair_data()
    assert rd.pair_params == {}
