"""Unit tests and regression for PairData classes."""
import dataclasses
import json

from brer.pair_data import PairData
from brer.pair_data import PairDataCollection
from brer.pair_data import sample_all


def test_pair_data_collection(raw_pair_data, pair_data_file):
    """Ensure correct structure and typing of PairData collections."""
    with open(pair_data_file, 'r') as fh:
        pairs = PairDataCollection(*(PairData(name=name, **obj) for name, obj in json.load(fh).items()))

    for name in pairs:
        assert isinstance(pairs[name], PairData)

    assert set(pairs.keys()) == set(raw_pair_data.keys())
    for pair_name, pair_data in pairs.items():
        for key, value in dataclasses.asdict(pair_data).items():
            if key != 'name':
                assert value == raw_pair_data[pair_name][key]
        for key, value in raw_pair_data[pair_name].items():
            assert getattr(pair_data, key) == value

    assert pairs == PairDataCollection.create_from(pair_data_file)


def test_pair_data_helpers(pair_data_file):
    """Test the module functions for accessing PairData and PairDataCollection."""
    pairs = PairDataCollection.create_from(pair_data_file)
    samples = sample_all(pairs)
    assert set(samples.keys()) == set(pairs.keys())
    for pair in pairs:
        assert samples[pair] >= min(pairs[pair].bins)
        assert samples[pair] <= max(pairs[pair].bins)
