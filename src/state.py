"""
BRER State class

This records the current state of a BRER simulation:
1. Iteration number.
2. Whether the simulation has finished training, convergence, or production phase.
3. Some other items for restarts like the coupling constant and the name of the checkpoint file (used for extracting
time information)
"""

from src.metadata import MetaData, MultiMetaData


class State(MetaData):
    """
    Stores five critical parameters for BRER restarts:
    1. The iteration number
    2. The phase of the simulation ('training', 'convergence', 'production')
    3. The coupling constant 'alpha'
    4. The target distance 'target'
    5. The name of the State object. This allows us to check that pair data and state data match when we combine the
    data from each.
    """

    def __init__(self, name):
        super().__init__(name=name)
        self.set_requirements(['iteration', 'phase', 'alpha', 'target'])
        self.__defaults = {'iteration': 0, 'phase': 'training', 'alpha': 0, 'target': 0}

    def restart(self, **kwargs):
        """
        Resets the BRER state to iteration zero, beginning of training phase
        Can specify any of the parameters in the function call
        """
        for key, value in kwargs.items():
            self.__defaults[key] = value
        self.set_from_dictionary(self.__defaults)


class MultiState(MultiMetaData):
    def __init__(self):
        super().__init__()

    def set_names(self, names):
        self._names = names
        for name in self._names:
            self._metadata_list.append(State(name=name))

    def restart(self, names=None, **kwargs):
        if names is not None:
            self.set_names(names)
        else:
            names = self.get_names()

        if not names:
            raise IndexError('Names are empty. Must specify names of state objects.')

        for state in self._metadata_list:
            state.restart(**kwargs)


class GeneralData(MetaData):
    def __init__(self, name):
        super().__init__(name=name)
        self.set_requirements(['ensemble_num', 'iteration', 'phase'])
