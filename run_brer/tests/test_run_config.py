import contextlib
import json
import logging
import os
import shutil
import tempfile

import pytest

from run_brer.run_config import RunConfig


logger = logging.getLogger()

try:
    from mpi4py import MPI
except ImportError:
    MPI = None

if MPI is not None:
    rank = MPI.COMM_WORLD.Get_rank()
else:
    rank = 0

# if rank == 0:
#     import pydevd_pycharm
#
#     pydevd_pycharm.settrace('localhost',
#                             port=33333,
#                             stdoutToServer=True,
#                             stderrToServer=True)

with_mpi_only = pytest.mark.skipif(
    MPI is None,
    reason='This test requires mpi4py and a usable MPI environment.')

@contextlib.contextmanager
def working_directory_fence():
    """Ensure restoration of working directory when leaving context manager."""
    wd = os.getcwd()
    try:
        yield wd
    finally:
        os.chdir(wd)


def test_run_config(tmpdir, data_dir):
    with working_directory_fence():
        config_params = {
            "tpr": "{}/topol.tpr".format(data_dir),
            "ensemble_num": 1,
            "ensemble_dir": tmpdir,
            "pairs_json": "{}/pair_data.json".format(data_dir)
        }
        os.makedirs("{}/mem_{}".format(tmpdir, config_params["ensemble_num"]))
        rc = RunConfig(**config_params)
        rc.run_data.set(A=5, tau=0.1, tolerance=100, num_samples=2, sample_period=0.1, production_time=0.2)

        # Training phase.
        assert rc.run_data.get('iteration') == 0
        assert rc.run_data.get('phase') == 'training'
        # Include a test for kwarg handling.
        rc.run(threads=2)

        # Convergence phase.
        assert rc.run_data.get('phase') == 'convergence'
        rc.run()

        # Production phase.
        assert rc.run_data.get('phase') == 'production'
        with pytest.raises(TypeError):
            # Test handling of kwarg collisions.
            rc.run(end_time=1.0)
        # Note that rc.__production failed, but rc.run() will have changed directory.
        # This is an unspecified side effect, but we can use it for some additional inspection.
        assert len(os.listdir()) == 0
        # Test another kwarg.
        rc.run(max_hours=0.1)


@with_mpi_only
def test_mpi_ensemble(data_dir):
    """Test a batch of multiple ensemble members in a single MPI context."""
    test_dir = os.getcwd()
    with working_directory_fence():
        comm: MPI.Comm = MPI.COMM_WORLD
        rank: int = comm.Get_rank()
        logger.info(f'rank is {rank}')
        assert rank < comm.Get_size()

        tpr_list = [os.path.join(data_dir, 'topol.tpr')] * comm.Get_size()
        config_params = {
            "tpr": tpr_list,
            "ensemble_num": None,
            "ensemble_dir": test_dir,
            "pairs_json": "{}/pair_data.json".format(data_dir)
        }
        # os.makedirs("{}/mem_{}".format(test_dir, config_params["ensemble_num"]))
        rc = RunConfig(**config_params)
        rc.run_data.set(A=5, tau=0.1, tolerance=100, num_samples=2, sample_period=0.1, production_time=0.2)

        # Training phase.
        assert rc.run_data.get('phase') == 'training'
        # Include a test for kwarg handling.
        rc.run(threads=2)

        # Convergence phase.
        assert rc.run_data.get('phase') == 'convergence'
        rc.run(threads=4)

        # Production phase.
        assert rc.run_data.get('phase') == 'production'
        with pytest.raises(TypeError):
            # Test handling of kwarg collisions.
            rc.run(end_time=1.0)
        # Note that rc.__production failed, but rc.run() will have changed directory.
        # This is an unspecified side effect, but we can use it for some additional inspection.
        assert len(os.listdir()) == 0
        # Test another kwarg.
        rc.run(threads=4, max_hours=0.1)

        if comm.Get_size() > 1:
            # TODO: Confirm that we actually ran different ensemble members.
            ...


def test_production_bootstrap(tmpdir, data_dir):
    with working_directory_fence():
        config_params = {
            "tpr": "{}/topol.tpr".format(data_dir),
            "ensemble_num": 1,
            "ensemble_dir": tmpdir,
            "pairs_json": "{}/pair_data.json".format(data_dir)
        }
        os.makedirs("{}/mem_{}".format(tmpdir, config_params["ensemble_num"]))
        rc = RunConfig(**config_params)
        rc.run_data.set(A=5, tau=0.1, tolerance=100, num_samples=2, sample_period=0.1, production_time=0.2)

        # Training phase.
        rc.run()
        # Convergence phase.
        rc.run()

        # Production phase.
        # It is a little bit difficult to test that the production phase actually
        # runs with a non-default TPR file.
        # Warning: This may need some extra conditional logic to support more gmxapi versions.
        assert rc.run_data.get('phase') == 'production'
        with tempfile.TemporaryDirectory() as directory:
            new_tpr = os.path.join(directory, 'tmp.tpr')
            shutil.copy("{}/topol.tpr".format(data_dir), new_tpr)
            gmxapi_context = rc.run(tpr_file=new_tpr, max_hours=0.01)
        element = json.loads(gmxapi_context.work.elements['tpr_input'])
        assert str(element['params']['input'][0]) == str(new_tpr)
