from src.metadata import MetaData
from abc import abstractmethod
import gmx
import sys
sys.path.append('/home/jennifer/Git/brer/build/src/pythonmodule')


class RunConfig(MetaData):
    def __init__(self):
        super().__init__('build_gmxapi_plugin_config')

    def scan_dictionary(self, dictionary):
        """
        Scans a dictionary and stores whatever parameters it needs for the build_gmxapi_plugin
        :param dictionary:
        """
        for requirement in self.get_requirements():
            if requirement in dictionary.keys():
                self.set(requirement, dictionary[requirement])

    def scan_metadata(self, data):
        """
        This scans either a State obj or PairData obj and stores whatever parameters it needs for a Run.
        :param data: either type State or type PairData
        """
        self.scan_dictionary(data.get_as_dictionary())

    def set_parameters(self, **kwargs):
        self.scan_dictionary(kwargs)

    @abstractmethod
    def build_gmxapi_plugin(self):
        pass


class TrainingRunConfig(RunConfig):
    def __init__(self):
        super(RunConfig, self).__init__(name='training')
        self.set_requirements([
            'sites', 'target', 'A', 'tau', 'tolerance', 'nSamples', 'parameter_filename'
        ])

    def build_gmxapi_plugin(self):
        if self.get_missing_keys():
            raise KeyError('Must define {}'.format(self.get_missing_keys()))
        potential = gmx.workflow.WorkElement(
            namespace="myplugin",
            operation="brmc_restraint",
            depends=[],
            params=self.get_as_dictionary()
        )
        potential.name = '{}'.format(self.get('sites'))
        return potential


class ConvergenceRunConfig(RunConfig):
    def __init__(self):
        super(RunConfig, self).__init__(name='convergence')
        self.set_requirements([
            'sites', 'alpha', 'target', 'tolerance', 'samplePeriod',
            'logging_filename'
        ])

    def build_gmxapi_plugin(self):
        pass


class ProductionRunConfig(RunConfig):
    def __init__(self):
        super(RunConfig, self).__init__(name='production')
        self.set_requirements(['sites', 'R0', 'k'])

    def build_gmxapi_plugin(self):
        pass
