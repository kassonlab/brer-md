from run_brer.run_data import RunData
from run_brer.pair_data import MultiPair
from run_brer.plugin_configs import *
from run_brer.directory_helper import DirectoryHelper
from copy import deepcopy
import os
import shutil
import logging
import gmx
import json


class RunConfig:
    """
    Run configuration for single BRER ensemble member
    """

    def __init__(self,
                 tpr,
                 ensemble_dir,
                 ensemble_num=1,
                 pairs_json='pair_data.json'):
        self.tpr = tpr
        self.ens_dir = ensemble_dir
        self.__names = []

        # Load the pair data from a json. Use this to set up the run metadata
        self.pairs = MultiPair()
        self.pairs.read_from_json(pairs_json)
        self.__names = self.pairs.get_names()

        self.run_data = RunData()
        self.run_data.set(ensemble_num=ensemble_num)

        self.state_json = '{}/mem_{}/state.json'.format(
            ensemble_dir, self.run_data.get('ensemble_num'))

        if os.path.exists(self.state_json):
            self.run_data.from_dictionary(json.load(open(self.state_json)))
        else:
            for pd in self.pairs:
                self.run_data.from_pair_data(pd)
            self.run_data.save_config(self.state_json)

        # List of plugins
        self.__plugins = []

        # Logging
        self._logger = logging.getLogger('BRER')
        self._logger.setLevel(logging.DEBUG)
        # create file handler which logs even debug messages
        fh = logging.FileHandler('brer.log')
        fh.setLevel(logging.DEBUG)
        # create console handler with a higher log level
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        # create formatter and add it to the handlers
        formatter = logging.Formatter(
            '%(asctime)s:%(name)s:%(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        # add the handlers to the logger
        self._logger.addHandler(fh)
        self._logger.addHandler(ch)

        self._logger.info("Initialized the run configuration: {}".format(
            self.run_data.as_dictionary()))
        self._logger.info("Names of restraints: {}".format(self.__names))

    def build_plugins(self, plugin_config):
        # One plugin per restraint.
        self.__plugins = []
        # TODO: what is the expected behavior when a list of plugins exists? Probably to wipe them.

        general_params = self.run_data.as_dictionary()['general parameters']
        for name in self.__names:
            pair_params = self.run_data.as_dictionary()['pair parameters'][
                name]
            new_restraint = deepcopy(plugin_config)
            new_restraint.scan_dictionary(general_params)
            new_restraint.scan_dictionary(pair_params)
            print(new_restraint.get_as_dictionary())
            self.__plugins.append(new_restraint.build_plugin())

    def __change_directory(self):
        dir_help = DirectoryHelper(
            top_dir=self.ens_dir,
            param_dict=self.run_data.general_params.get_as_dictionary())
        dir_help.build_working_dir()
        dir_help.change_dir('phase')

    def __train(self):
        iter_num = self.run_data.general_params.get('iteration')
        # If this is not the first BRER iteration, grab the checkpoint from the production phase of the last round
        if iter_num != 0:
            prev_iter = iter_num - 1
            # Assume we have cd into the working directory
            member_dir = os.path.dirname(os.path.dirname(os.getcwd()))
            gmx_cpt = '{}/{}/production/state.cpt'.format(
                member_dir, prev_iter)
            if os.path.exists(gmx_cpt):
                shutil.copy(gmx_cpt, '{}/state.cpt'.format(os.getcwd()))
            else:
                raise FileNotFoundError('{} does not exist.')

        # Do re-sampling
        targets = self.pairs.re_sample()
        self._logger.info('New targets: {}'.format(targets))
        for name in self.__names:
            self.run_data.set(name=name, target=targets[name])

        self.run_data.save_config(fnm=self.state_json)

        # Backup existing checkpoint. TODO: Don't backup the cpt, actually use it!!
        cpt = '{}/state.cpt'.format(os.getcwd())
        if os.path.exists(cpt):
            self._logger.warning(
                'There is a checkpoint file in your current working directory, but you are '
                'training. The cpt will be backed up and the run will start over with new targets'
            )
            shutil.move(cpt, '{}.bak'.format(cpt))

        # Build the gmxapi session.
        md = gmx.workflow.from_tpr(self.tpr, append_output=False)
        self.build_plugins(TrainingPluginConfig())
        for plugin in self.__plugins:
            md.add_dependency(plugin)
        context = gmx.context.ParallelArrayContext(
            md, workdir_list=[os.getcwd()])

        # Run it.
        with context as session:
            session.run()

        # In the future runs (convergence, production) we need the ABSOLUTE VALUE of alpha.
        for i in range(len(self.__names)):
            self.run_data.set(
                name=self.__names[i], alpha=abs(context.potentials[i].alpha))

    def __converge(self):
        md = gmx.workflow.from_tpr(self.tpr, append_output=False)
        self.build_plugins(ConvergencePluginConfig())
        for plugin in self.__plugins:
            md.add_dependency(plugin)
        context = gmx.context.ParallelArrayContext(md, workdir_list=[os.getcwd()])
        with context as session:
            session.run()
        self.run_data.set(start_time=context.potentials[0].time)

    def __production(self):
        # Get the checkpoint file from the convergence phase
        gmx_cpt = '{}/convergence/state.cpt'.format(
            os.path.dirname(os.getcwd()))

        if os.path.exists(gmx_cpt):
            shutil.copy(gmx_cpt, '{}/state.cpt'.format(os.getcwd()))
        else:
            raise FileNotFoundError('{} does not exist'.format(gmx_cpt))

        end_time = self.run_data.get('production_time') + self.run_data.get('start_time')
        md = gmx.workflow.from_tpr(
            self.tpr, end_time=end_time, append_output=False)

        self.build_plugins(ProductionPluginConfig())
        for plugin in self.__plugins:
            md.add_dependency(plugin)
        context = gmx.context.ParallelArrayContext(
            md, workdir_list=[os.getcwd()])
        with context as session:
            session.run()

    def run(self):
        phase = self.run_data.get('phase')

        self.__change_directory()

        if phase == 'training':
            self.__train()
            self.run_data.set(phase='convergence')
        elif phase == 'convergence':
            self.__converge()
            self.run_data.set(phase='production')
        else:
            self.__production()
            self.run_data.set(phase='training')

        self.run_data.save_config(self.state_json)
