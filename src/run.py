"""
Classes for *running* BRER simulations.
"""

from src.metadata import MetaData


class RunConfig(MetaData):
    def __init__(self):
        super().__init__('run_config')

    def scan_data(self, data):
        """
        This scans a dictionary from either a State obj or PairData obj
        and stores whatever parameters it needs for a Run.
        :param data: either type State or type PairData
        """
        for requirement in self.get_requirements():
            if requirement in data.get_dictionary().keys():
                self.set(requirement, data.get(requirement))


class TrainingRunConfig(RunConfig):
    def __init__(self):
        super(RunConfig, self).__init__(name='training')
        self.set_requirements([
            'sites', 'A', 'tau', 'tolerance', 'nSamples', 'parameter_filename'
        ])


class ConvergenceRunConfig(RunConfig):
    def __init__(self):
        super(RunConfig, self).__init__(name='convergence')
        self.set_requirements([
            'sites', 'alpha', 'target', 'tolerance', 'samplePeriod',
            'logging_filename'
        ])


class ProductionRunConfig(RunConfig):
    def __init__(self):
        super(RunConfig, self).__init__(name='production')
        self.set_requirements(['sites', 'R0', 'k'])


if __name__ == "__main__":
    pass
