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

# TODO: Include short test runs for training, convergence, production.
