"""Unit tests and regression for RunData classes."""
import json
import tempfile

import pytest

from brer.pair_data import PairData
from brer.pair_data import PairDataCollection
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
    for key, data in raw_pair_data.items():
        # We removed the *name* field from input pair_data.json in 2.0.
        assert 'name' not in data
        pd = PairData(name=key, **data)
        pp = PairParams(key, sites=pd.sites)
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
    pairs = PairDataCollection(*[PairData(name=name, **pair) for name, pair in raw_pair_data.items()])
    rd = RunData.create_from(pairs)

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
    rd = RunData.create_from("{}/state.json".format(tmpdir))

    assert old_rd.as_dictionary() != rd.as_dictionary()
    rd.set(alpha=1., name=name)
    # Confirm that the restored data is the same as the original.
    assert old_rd.as_dictionary() == rd.as_dictionary()

    with tempfile.NamedTemporaryFile(suffix='.json', mode='w') as tmp:
        test_data = raw_pair_data.copy()
        for name in test_data:
            test_data[name]['name'] = name
        json.dump(obj=test_data, fp=tmp)
        tmp.flush()
        # Tolerates redundant *name* field in the pair_data.json file,
        # but issues deprecation warning.
        with pytest.deprecated_call():
            PairDataCollection.create_from(tmp.name)

    with tempfile.NamedTemporaryFile(suffix='.json', mode='w') as tmp:
        test_data = raw_pair_data.copy()
        for name in test_data:
            test_data[name]['name'] = f'{name}_different'
        json.dump(test_data, tmp)
        tmp.flush()
        # Tolerates redundant *name* field. Warns if inconsistent.
        with pytest.warns(match='instead of'):
            PairDataCollection.create_from(tmp.name)
