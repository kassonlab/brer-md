import contextlib
import os

import pytest

from run_brer.run_config import RunConfig


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
        rc.run(threads=2)
        rc.run()
        with pytest.raises(TypeError):
            rc.run(end_time=1.0)
        rc.run(max_hours=0.1)
