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

    def restart(self, **kwargs):
        """
        Resets the BRER state to iteration zero, beginning of training phase
        Can specify any of the parameters in the function call
        """
        defaults = {'iteration': 0, 'phase': 'training', 'alpha': 0, 'target': 0}
        for key, value in kwargs.items():
            defaults[key] = value
        self.set_metadata(defaults)


class MultiState(MultiMetaData):

    def __init__(self):
        super().__init__()
