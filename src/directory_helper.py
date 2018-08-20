import os
from src.state import State


class DirectoryHelper:
    def __init__(self, top_dir, state: State):
        self._top_dir = top_dir
        self._ensemble_num = state.get('ensemble_num')
        self._iteration = state.get('iteration')
        self._phase = state.get('phase')

    def _get_dir(self, dirtype):
        """ Get the directory for however far you want to go down the directory tree"""
        if dirtype == 'top':
            return_dir = self._top_dir
        elif dirtype == 'ensemble_num':
            return_dir = '{}/mem_{}'.format(self._top_dir, self._ensemble_num)
        elif dirtype == 'iteration':
            return_dir = '{}/mem_{}/{}'
        elif dirtype == 'phase':
            return_dir = '{}/mem_{}/{}/{}'.format(self._top_dir, self._ensemble_num, self._iteration, self._phase)
        else:
            raise ValueError('{} is not a valid directory type for BRER simulations'.format('type'))
        return return_dir

    def build_working_dir(self):
        """
        Checks to see if the working directory for current state of BRER simulation exists. If it does not, creates the
        directory. Then changes to that directory.
        :param dir_info: A dictionary containing data on the directory structure.
        :return:
        """

        if not os.path.exists(self._get_dir('phase')):
            tree = [self._get_dir('ensemble_num'), self._get_dir('iteration')]
            for leaf in tree:
                if not os.path.exists(leaf):
                    os.mkdir(leaf)
            os.mkdir(self._get_dir('phase'))

    def change_dir(self, dirtype):
        os.chdir(self._get_dir(dirtype))
    # os.chdir(working_dir)
