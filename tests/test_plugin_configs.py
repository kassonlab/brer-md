"""Unit tests and regression for PluginConfig classes."""
import dataclasses

import pytest

from brer.plugin_configs import ConvergencePluginConfig
from brer.plugin_configs import ProductionPluginConfig
from brer.plugin_configs import TrainingPluginConfig
from brer.run_data import GeneralParams
from brer.run_data import PairParams


def test_plugins(raw_pair_data):
    """Build all three test plugins and check that they have all the required
    data to run.

    Parameters
    ----------
    raw_pair_data : dict
        A set of pair-specific parameters. Provided in conftest.py
    """
    tpc: TrainingPluginConfig
    cpc: ConvergencePluginConfig
    ppc: ProductionPluginConfig

    general_parameter_defaults = dataclasses.asdict(GeneralParams())
    name = list(raw_pair_data.keys())[0]
    sites = raw_pair_data[name]["sites"]
    pp = PairParams(name=name, sites=sites)

    param_dict = general_parameter_defaults.copy()
    param_dict.update(**dataclasses.asdict(pp))

    # 'target' is a run-time parameter, and needs to be provided.
    # Here we choose an arbitrary value.
    param_dict['target'] = 1.0

    tpc = TrainingPluginConfig.create_from(param_dict)

    # 'alpha' is a required parameter for convergence and production phases.
    param_dict['alpha'] = 0.0
    cpc = ConvergencePluginConfig.create_from(param_dict)
    ppc = ProductionPluginConfig.create_from(param_dict)

    tpc.build_plugin()

    # By default, alpha is 0.0, which doesn't make sense in the convergence and production phases.
    assert cpc.alpha == 0.0
    with pytest.raises(ValueError):
        cpc.build_plugin()
    with pytest.raises(ValueError):
        ppc.build_plugin()

    cpc.alpha = 1.0
    cpc.build_plugin()

    ppc.alpha = 1.0
    ppc.build_plugin()
