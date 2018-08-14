from src.resampler import *
import pytest


@pytest.fixture()
def first_distribution():
    return [1, 2, 3, 4]


@pytest.fixture()
def secon_distribution():
    return [5, 6, 7, 8]


def test_resample(first_distribution, secon_distribution):
    """ Initializing pair data """
    pd1 = PairData(name='pd1')
    pd1.__setattr__('distribution', first_distribution)
    pd2 = PairData(name='pd2')
    pd2.__setattr__('distribution', secon_distribution)

    resampler = ReSampler()
    resampler.add_pair(pd1)
    resampler.add_pair(pd2)
    if resampler.is_empty():
        raise IndexError("PairData is empty")

    if not resampler.get_distributions()[0]:
        raise IndexError("Distributions are empty")
