from run_brer.pair_data import PairData, MultiPair
import pytest


def test_pair_data(multi_pair_data, raw_pair_data):
    """
    Ensures that multipair constructs multiple PairData objects.
    :param multi_pair_data:
    :param raw_pair_data:
    :return:
    """
    assert (multi_pair_data.get_as_single_dataset() == raw_pair_data)
    for name in multi_pair_data.get_names():
        assert (type(
            multi_pair_data[multi_pair_data.name_to_id(name)]) == PairData)


def test_resampling(multi_pair_data):
    print(multi_pair_data.re_sample())
