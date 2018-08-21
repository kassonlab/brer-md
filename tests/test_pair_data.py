from src.pair_data import *
import pytest
import json

my_path = './tests'
@pytest.fixture()
def first_dataset():
    return json.load(open('{}/052_210.json'.format(my_path)))


@pytest.fixture()
def secon_dataset():
    return json.load(open('{}/105_216.json'.format(my_path)))


def test_multi_pair_data(first_dataset, secon_dataset):
    """ Initializing pair data """
    pd1 = PairData(name=first_dataset['name'])
    pd1.set_from_dictionary(first_dataset)
    pd2 = PairData(name=secon_dataset['name'])
    pd2.set_from_dictionary(secon_dataset)

    multi = MultiPair()
    multi.ingest_data([pd1, pd2])


def test_resample(first_dataset, secon_dataset):
    """ Initializing pair data """

    pd1 = PairData(name=first_dataset['name'])
    pd1.set_from_dictionary(first_dataset)
    pd2 = PairData(name=secon_dataset['name'])
    pd2.set_from_dictionary(secon_dataset)

    multi = MultiPair()
    multi.ingest_data([pd1, pd2])
    if not multi.re_sample():
        raise IndexError("Distributions are empty")
