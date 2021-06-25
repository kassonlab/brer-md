import contextlib
import json
import os
import shutil
import tempfile

import pytest

from run_brer.run_config import RunConfig

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
        rc.run_data.set(A=5, tau=0.1, tolerance=10000, num_samples=2, sample_period=0.001,
                        production_time=10000.)

        # Training phase.
        assert rc.run_data.get('iteration') == 0
        assert rc.run_data.get('phase') == 'training'
        # Include a test for kwarg handling.
        rc.run(threads=num_cpus)

        # Convergence phase.
        assert rc.run_data.get('phase') == 'convergence'
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
        rc.run_data.set(A=5,
                        tau=0.1,
                        tolerance=100,
                        num_samples=2,
                        sample_period=0.1,
                        production_time=0.2)

        # Training phase.
        assert rc.run_data.get('phase') == 'training'
        rc.run()
        # Convergence phase.
        assert rc.run_data.get('phase') == 'convergence'
        rc.run()

        # Production phase.
        # It is a little bit difficult to test that the production phase actually
        # runs with a non-default TPR file.
        # Warning: This may need some extra conditional logic to support more gmxapi
        # versions.

        # Test production bootstrap option.
        # TODO: Merge with test_run_config once issue #19 is resolved.
        assert rc.run_data.get('phase') == 'production'
        with tempfile.TemporaryDirectory() as directory:
            new_tpr = os.path.join(directory, 'tmp.tpr')
            shutil.copy("{}/topol.tpr".format(data_dir), new_tpr)
            gmxapi_context = rc.run(tpr_file=new_tpr, max_hours=0.001)
        element = json.loads(gmxapi_context.work.elements['tpr_input'])
        assert str(element['params']['input'][0]) == str(new_tpr)
