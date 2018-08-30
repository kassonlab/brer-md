"""
Try again
"""
from run_brer.metadata import *
from run_brer.pair_data import PairData


class GeneralParams(MetaData):
    def __init__(self):
        super().__init__('general')
        self.set_requirements([
            'ensemble_num', 'iteration', 'phase', 'start_time', 'A', 'tau',
            'tolerance', 'nSamples', 'samplePeriod', 'production_time'
        ])


class PairParams(MetaData):
    def __init__(self, name):
        super().__init__(name)
        self.set_requirements(['sites', 'logging_filename', 'alpha', 'target'])


class RunData:
    def __init__(self):
        self.general_params = GeneralParams()
        self.__defaults_general = {
            'ensemble_num': 1,
            'iteration': 0,
            'phase': 'training',
            'start_time': 0,
            'A': 50,
            'tau': 50,
            'tolerance': 0.25,
            'nSamples': 50,
            'samplePeriod': 100,
            'production_time': 10000  # 10 ns
        }
        self.general_params.set_from_dictionary(self.__defaults_general)
        self.pair_params = {}
        self.__names = []

    def set(self, name=None, **kwargs):
        for key, value in kwargs.items():
            if not name:
                if key in self.general_params.get_requirements():
                    self.general_params.set(key, value)
                else:
                    raise ValueError(
                        'You have provided a name; this means you are probably trying to set a '
                        'pair-specific parameter. {} is not pair-specific'.
                        format(key))
            else:
                if key in self.pair_params[name].get_requirements():
                    self.pair_params[name].set(key, value)
                else:
                    raise ValueError(
                        '{} is not a pair-specific parameter'.format(key))

    def get(self, key, name=None):
        if key in self.general_params.get_requirements():
            return self.general_params.get(key)
        elif name:
            return self.pair_params[name].get(key)
        else:
            raise ValueError(
                'You have not provided a name, but are trying to get a pair-specific parameter. '
                'Please provide a pair name')

    def as_dictionary(self):
        pair_param_dict = {}
        for name in self.pair_params.keys():
            pair_param_dict[name] = self.pair_params[name].get_as_dictionary()

        return {
            'general parameters': self.general_params.get_as_dictionary(),
            'pair parameters': pair_param_dict
        }

    def from_dictionary(self, data):
        self.general_params.set_from_dictionary(data['general parameters'])
        for name in data['pair parameters'].keys():
            self.pair_params[name] = PairParams(name)
            self.pair_params[name].set_from_dictionary(
                data['pair parameters'][name])

    def from_pair_data(self, pd: PairData):
        name = pd.name
        self.pair_params[name] = PairParams(name)
        self.pair_params[name].set('sites', pd.get('sites'))
        self.pair_params[name].set('logging_filename', '{}.log'.format(name))
        self.pair_params[name].set('alpha', 0)
        self.pair_params[name].set('target', 3.0)

    def clear_pair_data(self):
        self.pair_params = {}

    def save_config(self, fnm='state.json'):
        json.dump(self.as_dictionary(), open(fnm, 'w'))

    def load_config(self, fnm='state.json'):
        self.from_dictionary(json.load(open(fnm)))
