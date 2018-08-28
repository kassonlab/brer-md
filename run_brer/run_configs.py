from run_brer import TrainingPluginConfig, ConvergencePluginConfig, ProductionPluginConfig
from run_brer import MultiState, MultiPair
from run_brer import DirectoryHelper
import os
import copy
import logging
import shutil
import gmx


class RunConfig:
    def __init__(self,
                 tpr,
                 working_dir,
                 ensemble_num,
                 pairs_json='pair_data.json',
                 **kwargs):

        self.tpr = tpr
        self.working_dir = working_dir
        self.state_json = '{}/mem_{}/state.json'.format(
            working_dir, ensemble_num)
        self.pairs_json = pairs_json
        self.states = MultiState()
        self.pairs = MultiPair()
        self.run_params = {
            'ensemble_num': ensemble_num,
            'iteration': 0,
            'phase': 'training',
            'start_time': 0,
            'sites': [],
            'A': 50,
            'tau': 50,
            'tolerance': 0.25,
            'nSamples': 50,
            'parameter_filename': '',
            'logging_filename': '',
            'alpha': 0,
            'target': 0,
            'samplePeriod': 100,
            'R0': 0,
            'k': 0,
            'production_time': 10000  # 10 ns
        }

        if not os.path.exists(pairs_json):
            raise ValueError(
                'The restraint data file {} does not exist'.format(pairs_json))

        self.pairs.read_from_json(pairs_json)
        self.names = self.pairs.get_names()
        self.n_pairs = len(self.names)

        if os.path.exists(self.state_json):
            self.states.read_from_json(filename=self.state_json)
        else:
            self.states.restart(names=self.pairs.get_names())
            self.states.write_to_json(filename=self.state_json)

        # Check to make sure the pair data and state data match up
        if set(self.names) != set(self.states.get_names()):
            raise ValueError(
                'The pair data names ({}) do not match the state data names ({})'.
                format(self.names(), self.states.get_names()))

        # Load any other parameters you might need
        for key, value in kwargs.items():
            if key in self.run_params.keys():
                self.run_params[key] = value
            else:
                raise KeyError(
                    '{} is not a valid BRER run parameter'.format(key))

        self.__plugins = []

        logging.basicConfig()
        self._logger = logging.getLogger('BRER')

    def __build_plugins(self, plugin_config):
        # You will need one run configuration per restraint
        for i in range(self.n_pairs):
            new_restraint = copy.deepcopy(plugin_config)
            new_restraint.scan_dictionary(self.run_params)
            new_restraint.set_parameters(
                parameter_filename='{}.log'.format(self.names[i]),
                logging_filename='{}.log'.format(self.names[i]))
            new_restraint.scan_metadata(self.states[i])
            new_restraint.scan_metadata(self.pairs[i])
            self.__plugins.append(new_restraint.build_plugin())

    def __change_directory(self):
        dir_help = DirectoryHelper(
            top_dir=self.working_dir, param_dict=self.run_params)
        dir_help.build_working_dir()
        dir_help.change_dir('phase')

    def __train(self):

        # If this is not the first BRER iteration, grab the checkpoint from the production phase of the last round
        if self.run_params['iteration'] != 0:
            prev_iter = self.run_params['iteration'] - 1
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
        for state in self.states:
            state.set('target', targets[state.name])
        self.states.write_to_json()

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
        self.__build_plugins(TrainingPluginConfig())
        for plugin in self.__plugins:
            md.add_dependency(plugin)
        context = gmx.context.ParallelArrayContext(
            md, workdir_list=[os.getcwd()])

        # Run it.
        with context as session:
            session.run()

    def __converge(self):
        md = gmx.workflow.from_tpr(self.tpr, append_output=False)
        self.__build_plugins(ConvergencePluginConfig())
        for plugin in self.__plugins:
            md.add_dependency(plugin)
        context = gmx.context.ParallelArrayContext(
            md, workdir_list=[os.getcwd()])
        with context as session:
            session.run()

        self.run_params['start_time'] = context.potentials[0].time
        for state in self.states:
            state.set('start_time', self.run_params['start_time'])

    def __production(self):

        # Get the checkpoint file from the convergence phase
        gmx_cpt = '{}/convergence/state.cpt'.format(
            os.path.dirname(os.getcwd()))

        if os.path.exists(gmx_cpt):
            shutil.copy(gmx_cpt, '{}/state.cpt'.format(os.getcwd()))
        else:
            raise FileNotFoundError('{} does not exist'.format(gmx_cpt))

        end_time = self.run_params['production_time'] + self.run_params['start_time']
        md = gmx.workflow.from_tpr(
            self.tpr, end_time=end_time, append_output=False)

        self.__build_plugins(ProductionPluginConfig())
        for plugin in self.__plugins:
            md.add_dependency(plugin)
        context = gmx.context.ParallelArrayContext(
            md, workdir_list=[os.getcwd()])
        with context as session:
            session.run()

    def run(self, **kwargs):
        phase = self.run_params['phase']
        self.__change_directory()

        if phase == 'training':
            self.__train()
            self.run_params['phase'] = 'convergence'
        if phase == 'converge':
            self.__converge()
            self.run_params['phase'] = 'production'
        if phase == 'production':
            self.__production()
            self.run_params['iteration'] += 1
            self.run_params['phase'] = 'training'

        self.states.write_to_json(self.state_json)
