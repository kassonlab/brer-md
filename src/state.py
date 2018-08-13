"""
BRER State class

This records the current state of a BRER simulation:
1. Iteration number.
2. Whether the simulation has finished training, convergence, or production phase.
"""

import json


class State(object):
    """
    Stores five critical parameters for BRER restarts:
    1. The iteration number
    2. The phase of the simulation ('training', 'convergence', 'production')
    3. The coupling constant 'alpha'
    4. The target distance 'target'
    5. The gmx checkpoint file 'gmx_cpt'
    """

    def __init__(self, initial_state=None):
        """
        All parameters are stored in dictionary for easy storage of these metadata.
        """
        if not initial_state:
            self._state = {}
        else:
            self._state = initial_state
        self._required_keys = [
            'iteration', 'phase', 'alpha', 'target', 'gmx_cpt'
        ]

    def state(self):
        return self._state

    def set(self, key, value):
        """
        Update a parameter 'key' of the BRER state.
        :param key: Any of 'iteration', 'phase', or 'gmx_cpt'
        :param value: Sets BRER state to this 'value'
        """
        self._state[key] = value

    @property
    def keys(self):
        return list(self._state.keys())

    @property
    def required_keys(self):
        return self._required_keys

    def is_complete_record(self):
        return set(self.keys) == set(self.required_keys)

    def restart(self):
        """
        Resets the BRER state to iteration zero, beginning of training phase
        """
        self._state['iteration'] = 0
        self._state['phase'] = 'training'
        self._state['alpha'] = 0
        self._state['target'] = 0
        self._state['gmx_cpt'] = 'state.cpt'

    def write_to_json(self, json_filename='state.json'):
        """
        Writes metadata on BRER state
        :param json_filename:
        """
        json.dump(self.state, open(json_filename, 'w'))
