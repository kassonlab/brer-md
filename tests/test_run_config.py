import contextlib
import json
import logging
import os
import shutil
import tempfile

import pytest

from brer.run_config import RunConfig

logger = logging.getLogger()

try:
    from mpi4py import MPI
except ImportError:
    MPI = None

# To use PyCharm debug server, you would need something like the following:
# if rank == 0:
#     import pydevd_pycharm
#
#     pydevd_pycharm.settrace('localhost',
#                             port=33333,
#                             stdoutToServer=True,
#                             stderrToServer=True)

with_mpi_only = pytest.mark.skipif(
    MPI is None or MPI.COMM_WORLD.Get_size() < 2,
    reason='This test requires mpi4py and a usable MPI environment.')

# Try to get a reasonable number of threads to use.
try:
    num_cpus: int = len(os.sched_getaffinity(0))
except Exception:
    num_cpus = 4


@contextlib.contextmanager
def working_directory_fence():
    """Ensure restoration of working directory when leaving context manager."""
    wd = os.getcwd()
    try:
        yield wd
    finally:
        os.chdir(wd)


def test_run_config(tmpdir, pair_data_file, simulation_input):
    with working_directory_fence():
        config_params = {
            "tpr": simulation_input,
            "ensemble_num": 1,
            "ensemble_dir": tmpdir,
            "pairs_json": pair_data_file
        }
        os.makedirs(
            "{}/mem_{}".format(tmpdir, config_params["ensemble_num"]),
            exist_ok=True
        )
        rc = RunConfig(**config_params)
        rc.run_data.set(A=5,
                        tau=0.1,
                        tolerance=0.1,
                        num_samples=2,
                        sample_period=0.001,
                        production_time=10000.)

        # Training phase.
        assert rc.run_data.get('iteration') == 0
        assert rc.run_data.get('phase') == 'training'

        # With a tight tolerance and short run time, it can't have converged.
        # See https://github.com/kassonlab/run_brer/issues/8
        with pytest.raises(RuntimeError):
            rc.run(max_hours=0.0001)
        assert rc.run_data.get('phase') == 'training'

        # Allow the training phase to converge.
        rc.run_data.set(tolerance=10000)
        # Include a test for kwarg handling.
        rc.run(threads=num_cpus)

        # Convergence phase.
        assert rc.run_data.get('phase') == 'convergence'
        # Check that bad alpha is caught.
        _original_alpha = [None] * len(rc.run_data.pair_params)
        for i, name in enumerate(rc.run_data.pair_params):
            _original_alpha[i] = rc.run_data.get('alpha', name=name)
            rc.run_data.set(name=name, alpha=0.0)
        with pytest.raises(ValueError):
            rc.run()
        # Set alpha back so we can continue.
        for i, name in enumerate(rc.run_data.pair_params):
            rc.run_data.set(name=name, alpha=_original_alpha[i])
        # Check robustness to early termination.
        rc.run_data.set(tolerance=0.01)
        rc.run(max_hours=0.001)
        assert rc.run_data.get('phase') == 'convergence'

        # Finish convergence phase.
        rc.run_data.set(tolerance=10000)
        rc.run()

        # Production phase.
        assert rc.run_data.get('phase') == 'production'
        with pytest.raises(TypeError):
            # Test handling of kwarg collisions.
            rc.run(end_time=1.0)
        # Note that rc.__production failed, but rc.run() will have changed directory.
        # This is an unspecified side effect, but we can use it for some additional
        # inspection.
        assert len(os.listdir()) == 0
        # Test another kwarg.
        rc.run(max_hours=0.001)
        assert rc.run_data.get('phase') == 'production'

        # Test the production phase bootstrapping option.
        # It is a little difficult to test that the production phase actually
        # runs with a non-default TPR file.
        # Warning: This may need some extra conditional logic to support more gmxapi
        # versions.
        with tempfile.TemporaryDirectory() as directory:
            new_tpr = os.path.join(directory, 'tmp.tpr')
            shutil.copy(simulation_input, new_tpr)
            gmxapi_context = rc.run(tpr_file=new_tpr, max_hours=0.001)
        element = json.loads(gmxapi_context.work.elements['tpr_input'])
        assert str(element['params']['input'][0]) == str(new_tpr)
        assert rc.run_data.get('phase') == 'production'
        assert rc.run_data.get('iteration') == 0


@with_mpi_only
def test_mpi_ensemble(tmpdir, pair_data_file, simulation_input):
    """Test a batch of multiple ensemble members in a single MPI context."""
    with working_directory_fence():
        comm: MPI.Comm = MPI.COMM_WORLD
        rank: int = comm.Get_rank()
        logger.info(f'rank is {rank}')
        assert rank < comm.Get_size()

        tpr_list = [simulation_input] * comm.Get_size()
        config_params = {
            "tpr": tpr_list,
            "ensemble_num": None,
            "ensemble_dir": tmpdir,
            "pairs_json": pair_data_file
        }
        os.makedirs(
            "{}/mem_{}".format(tmpdir, config_params["ensemble_num"]),
            exist_ok=True
        )
        rc = RunConfig(**config_params)
        rc.run_data.set(A=5,
                        tau=0.1,
                        tolerance=100,
                        num_samples=2,
                        sample_period=0.1,
                        production_time=0.2)

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
        # This is an unspecified side effect, but we can use it for some additional
        # inspection.
        assert len(os.listdir()) == 0
        # Test another kwarg.
        rc.run(threads=4, max_hours=0.001)

        if comm.Get_size() > 1:
            # TODO(https://github.com/kassonlab/run_brer/issues/7): Confirm that we actually ran different ensemble members.
            ...
