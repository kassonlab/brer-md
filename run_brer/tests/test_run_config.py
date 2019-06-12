from run_brer.plugin_configs import TrainingPluginConfig, ConvergencePluginConfig, ProductionPluginConfig
import pytest
import os


def test_build_plugins(rc):
    root_dir = os.getcwd()
    rc.build_plugins(TrainingPluginConfig())
    rc.build_plugins(ConvergencePluginConfig())
    rc.build_plugins(ProductionPluginConfig())
    os.chdir(root_dir)


def test_logger(rc):
    rc._logger.info("Testing the logger")


def test_run(rc):
    current_dir = os.getcwd()
    rc.run_data.set(
        A=5,
        tau=0.1,
        tolerance=100,
        num_samples=2,
        sample_period=0.1,
        production_time=0.2
    )

    rc.run()
    os.chdir(current_dir)
