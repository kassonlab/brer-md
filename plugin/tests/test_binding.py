# The myplugin module must be locatable by Python.
# If you configured CMake in the build directory ``/path/to/repo/build`` then,
# assuming you are in ``/path/to/repo``, run the tests with something like
#     PYTHONPATH=./cmake-build-debug/src/pythonmodule mpiexec -n 2 python -m mpi4py -m pytest tests/

# This test is not currently run automatically in any way. Build the module, point your PYTHONPATH at it,
# and run pytest in the tests directory.

import logging
import os

import pytest

try:
    import gmxapi as gmx
    from gmxapi.simulation.context import Context as _context
    from gmxapi.simulation.workflow import WorkElement, from_tpr
    from gmxapi.version import api_is_at_least
except (ImportError, ModuleNotFoundError):
    import gmx
    from gmx import get_context as _context
    from gmx.version import api_is_at_least
    from gmx.workflow import from_tpr, WorkElement

nompi = lambda f: f
try:
    from mpi4py import MPI
    if MPI.Is_initialized():
        rank = MPI.COMM_WORLD.Get_rank()
        if MPI.COMM_WORLD.Get_size() > 1:
            nompi = pytest.mark.skip(reason='Test cannot run in a multirank MPI environment.')
    else:
        rank = 0

    # Get a fixture for tests that should only run with 2 MPI ranks.
    withmpi_only = pytest.mark.skipif(
        not MPI.Is_initialized() or MPI.COMM_WORLD.Get_size() < 2,
        reason="Test requires at least 2 MPI ranks, but MPI is not initialized or too small.")
except (ImportError, ModuleNotFoundError):
    withmpi_only = pytest.mark.skip(
        reason="Test requires at least 2 MPI ranks, but mpi4py is not available.")
    rank = ''

logging.getLogger().setLevel(logging.DEBUG)
# create console handler
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter and add it to the handler
formatter = logging.Formatter(f'%(asctime)s:%(name)s:%(levelname)s:{rank} %(message)s')
ch.setFormatter(formatter)
# add the handlers to the logger
logging.getLogger().addHandler(ch)

logger = logging.getLogger()


def test_import():
    # Suppress inspection warning outside of testing context.
    # noinspection PyUnresolvedReferences
    import brer
    assert brer
