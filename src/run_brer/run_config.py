"""RunConfig class handles the actual workflow logic."""
import collections.abc
import json
import logging
import os
import pathlib
import shutil
import warnings
from copy import deepcopy
from typing import Sequence
from typing import Union

try:
    import mpi4py.MPI as _MPI
except (ImportError, ModuleNotFoundError):
    _MPI = None

from run_brer.directory_helper import DirectoryHelper
from run_brer.pair_data import MultiPair
from run_brer.plugin_configs import ConvergencePluginConfig
from run_brer.plugin_configs import PluginConfig
from run_brer.plugin_configs import ProductionPluginConfig
from run_brer.plugin_configs import TrainingPluginConfig
from run_brer.run_data import RunData

_Path = Union[str, pathlib.Path]


def _gmxapi_missing(*args, **kwargs):
    raise RuntimeError('run_brer requires gmxapi. See https://github.com/kassonlab/run_brer#requirements')


try:
    # noinspection PyPep8Naming,PyUnresolvedReferences
    from gmxapi.simulation.context import Context as _context
    # noinspection PyUnresolvedReferences
    from gmxapi.simulation.workflow import WorkElement, from_tpr
except (ImportError, ModuleNotFoundError):
    try:
        # noinspection PyPep8Naming
        from gmx.context import Context as _context
        from gmx.workflow import from_tpr, WorkElement
    except (ImportError, ModuleNotFoundError):
        _context = _gmxapi_missing
        from_tpr = _gmxapi_missing
        WorkElement = _gmxapi_missing


class RunConfig:
    """Run configuration for single BRER ensemble member."""

    @property
    def tpr(self):
        return pathlib.Path(self._tprs[self._rank])

    def __init__(self,
                 tpr: Union[_Path, Sequence[_Path]],
                 ensemble_dir,
                 ensemble_num: int = None,
                 pairs_json='pair_data.json'):
        """The run configuration specifies the files and directory structure
        used for the run. It determines whether the run is in the training,
        convergence, or production phase, then performs the run.

        Parameters
        ----------
        tpr : str
            path (or paths) to tpr input. Must be compatible with the GROMACS version
            providing gmxapi.
        ensemble_dir : str
            path to top directory which contains the full ensemble.
        ensemble_num : int, optional
            the ensemble member to run, by default 1
        pairs_json : str, optional
            path to file containing *ALL* the pair metadata.
            An example of what such a file should look like is provided in the data
            directory,
            by default 'pair_data.json'

        Note that all instances of RunConfig need the same sized array of TPR input
        files across all ranks in an MPI ensemble because they must all be capable of
        constructing a compatible copy of the ensemble simulation work description.
        """
        if isinstance(tpr, (str, pathlib.Path, os.PathLike)):
            self._tprs = tuple([str(tpr)])
            self._ensemble_size = 1
        else:
            if not isinstance(tpr, collections.abc.Iterable):
                raise ValueError('Paramater *tpr* must be an input file or sequence of '
                                 'input files (for ensemble input).')
            self._tprs = tuple([str(name) for name in tpr])
            self._ensemble_size = len(self._tprs)
        if self._ensemble_size == 1:
            self._communicator = None
            self._rank = 0
        elif _MPI is None or _MPI.COMM_WORLD.Get_size() < self._ensemble_size:
            raise RuntimeError('Need mpi4py and one MPI rank per ensemble member.')
        else:
            communicator: _MPI.Comm = _MPI.COMM_WORLD
            assert communicator.Get_size() >= self._ensemble_size
            # TODO: Handle mismatched ensemble size.
            if communicator.Get_size() > self._ensemble_size:
                warnings.warn('run_brer does not yet attempt to handle communicators '
                              'larger than the ensemble.')
            self._communicator = communicator
            self._rank = communicator.Get_rank()

        # WARNING: Previous behavior defaulted to ensemble_num=1
        if ensemble_num is None:
            ensemble_num = self._rank
        else:
            if self._communicator is not None:
                # Greater future flexibility is described at
                # https://github.com/kassonlab/run_brer/issues/18
                raise TypeError(
                    'RunConfig does not allow *ensemble_num* with mpi4py ensembles.')

        if not os.path.exists(ensemble_dir):
            raise RuntimeError(f'Ensemble directory {ensemble_dir} does not exist!')
        self.ens_dir = ensemble_dir

        # a list of identifiers of the residue-residue pairs that will be restrained
        self.__names = []

        # Load the pair data from a json. Use this to set up the run metadata
        self.pairs = MultiPair()
        self.pairs.read_from_json(pairs_json)
        # use the same identifiers for the pairs here as those provided in the pair
        # metadata
        # file this prevents mixing up pair data amongst the different pairs (i.e.,
        # accidentally applying the restraints for pair 1 to pair 2.)
        self.__names = self.pairs.names

        self.run_data = RunData()
        self.run_data.set(ensemble_num=ensemble_num)

        member_directory = os.path.join(self.ens_dir, f'mem_{ensemble_num}')
        if not os.path.exists(member_directory):
            os.mkdir(member_directory)

        self.state_json = '{}/mem_{}/state.json'.format(ensemble_dir,
                                                        self.run_data.get('ensemble_num'))
        # If we're in the middle of a run, load the BRER checkpoint file and continue from
        # the current state.
        if os.path.exists(self.state_json):
            self.run_data.from_dictionary(json.load(open(self.state_json)))
        # Otherwise, populate the state information using the pre-loaded pair data.
        # Then save
        # the current state.
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
        fh = logging.FileHandler('brer{}.log'.format(ensemble_num))
        fh.setLevel(logging.DEBUG)
        # create console handler with a higher log level
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        # create formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        # add the handlers to the logger
        self._logger.addHandler(fh)
        self._logger.addHandler(ch)

        self._logger.info("Initialized the run configuration: {}".format(
            self.run_data.as_dictionary()))
        self._logger.info("Names of restraints: {}".format(self.__names))

        # Need to cleanly handle cancelled jobs: write out a checkpoint of the state if
        # the
        # job is exited.
        # def cleanup():
        #     """"""
        #     self.run_data.save_config(self.state_json)
        #     self._logger.info("BRER received INT signal, stopping and saving data to
        #     {}".format(self.state_json))

        # atexit.register(cleanup)

    def build_plugins(self, plugin_config: PluginConfig):
        """Builds the plugin configuration. For each pair-wise restraint,
        populate the plugin with data: both the "general" data and the data
        unique to that restraint.

        Parameters
        ----------
        plugin_config : PluginConfig
            the particular plugin configuration (Training, Convergence, Production) for
            the run.
        """

        # One plugin per restraint.
        # TODO: what is the expected behavior when a list of plugins exists? Probably
        #  wipe them.
        self.__plugins = []
        general_params = self.run_data.general_params
        # For each pair-wise restraint, populate the plugin with data: both the
        # "general" data and
        # the data unique to that restraint.
        for name in self.__names:
            pair_params = self.run_data.pair_params[name]
            new_restraint = deepcopy(plugin_config)
            new_restraint.scan_metadata(general_params)  # load general data into
            # current restraint
            new_restraint.scan_metadata(pair_params)  # load pair-specific data into
            # current restraint
            self.__plugins.append(new_restraint.build_plugin())

    def __set_workdir(self):
        # change into the current working directory (
        # ensemble_path/member_path/iteration/phase)
        dir_help = DirectoryHelper(
            top_dir=self.ens_dir,
            param_dict=self.run_data.general_params.get_as_dictionary())
        dir_help.build_working_dir()
        workdir = dir_help.change_dir('phase')
        if self._communicator is None or self._communicator.Get_size() == 1:
            self.workdirs = [workdir]
        else:
            # assert isinstance(self._communicator, MPI.Comm)
            comm_size: int = self._communicator.Get_size()
            assert comm_size > 1
            assert self._rank < comm_size
            self.workdirs = self._communicator.allgather(workdir)
            assert len(self.workdirs) == comm_size
            assert self.workdirs[self._rank] == workdir

    def __move_cpt(self):

        def safe_copy(src, dst):
            if not os.path.exists(src):
                raise RuntimeError('Missing file: {}'.format(src))
            if os.path.exists(dst):
                raise RuntimeError('Destination file already exists: {}'.format(dst))
            size = os.stat(src).st_size
            if size == 0:
                raise RuntimeError('Source file has zero size: {}'.format(src))
            target_tmp = dst + '.tmp'
            try:
                shutil.copy(src, target_tmp)
            except Exception as e:
                if os.path.exists(target_tmp):
                    os.unlink(target_tmp)
                raise e
            os.rename(target_tmp, dst)
            assert os.stat(dst).st_size > 0

        current_iter = int(self.run_data.get('iteration'))
        ens_num = int(self.run_data.get('ensemble_num'))
        phase: str = self.run_data.get('phase')

        target_dir = os.getcwd()
        # Check logic implicit in prior revisions.
        assert os.path.abspath('{}/mem_{}/{}/{}'.format(self.ens_dir,
                                                        ens_num,
                                                        current_iter,
                                                        phase)) == target_dir

        target = os.path.join(target_dir, 'state.cpt')
        # If the cpt already exists, don't overwrite it
        if os.path.exists(target):
            self._logger.info(
                "Phase is {} and state.cpt already exists: not moving any files".format(
                    phase))

        else:
            member_dir = '{}/mem_{}'.format(self.ens_dir, ens_num)
            prev_iter = current_iter - 1

            if phase in ['training', 'convergence']:
                if prev_iter > -1:
                    # Get the production cpt from previous iteration
                    source = '{}/{}/production/state.cpt'.format(member_dir, prev_iter)
                    if not os.path.exists(source):
                        raise RuntimeError(
                            'Missing checkpoint file from previous iteration: {}'.format(
                                source))
                    safe_copy(source, target)

                else:
                    pass  # Do nothing. Let mdrun generate the initial checkpoint file.

            else:
                # Get the convergence cpt from current iteration
                source = '{}/{}/convergence/state.cpt'.format(member_dir, current_iter)
                if not os.path.exists(source):
                    self._logger.error(f'os.path.exists({source}) is False! Getting '
                                       f'directory listing.')
                    self._logger.error(str(os.listdir(os.path.dirname(source))))
                    raise RuntimeError(
                        'Missing checkpoint file from convergence phase: {}'.format(
                            source))
                safe_copy(source, target)

    def __prep_input(self, tpr_file: str = None):
        if tpr_file is None:
            tpr_file = self.tpr
            # Get the checkpoint file from the previous phase
            self.__move_cpt()
        if not os.path.exists(tpr_file):
            raise RuntimeError('Missing input file: {}'.format(tpr_file))
        return tpr_file

    def __train(self, tpr_file=None, **kwargs):
        for key in ('append_output',):
            if key in kwargs:
                raise TypeError('Conflicting key word argument. Cannot accept {}.'.format(
                    key))

        # do re-sampling
        targets = self.pairs.re_sample()
        self._logger.info('New targets: {}'.format(targets))
        for name in self.__names:
            self.run_data.set(name=name, target=targets[name])

        # save the new targets to the BRER checkpoint file.
        self.run_data.save_config(fnm=self.state_json)

        workdir = self.workdirs[self._rank]

        # backup existing checkpoint.
        # TODO: Don't backup the cpt, actually use it!!
        cpt = '{}/state.cpt'.format(workdir)
        if os.path.exists(cpt):
            self._logger.warning(
                'There is a checkpoint file in your current working directory, but you '
                'are '
                'training. The cpt will be backed up and the run will start over with '
                'new targets')
            shutil.move(cpt, '{}.bak'.format(cpt))

        # If this is not the first BRER iteration, grab the checkpoint from the production
        # phase of the last round
        self.__prep_input(tpr_file)

        # Set up a dictionary to go from plugin name -> restraint name
        sites_to_name = {}

        # Build the gmxapi session.
        tpr_list: Sequence[str] = self._tprs
        md = from_tpr(tpr_list, append_output=False, **kwargs)
        self.build_plugins(TrainingPluginConfig())
        if len(self.__plugins) == 0:
            warnings.warn('No BRER restraints are being applied! User error?')
        for plugin in self.__plugins:
            plugin_name = plugin.name
            for name in self.__names:
                run_data_sites = "{}".format(self.run_data.get('sites', name=name))
                if run_data_sites == plugin_name:
                    sites_to_name[plugin_name] = name
            md.add_dependency(plugin)
        context = _context(md,
                           workdir_list=self.workdirs,
                           communicator=self._communicator)

        self._logger.info("=====TRAINING INFO======\n")
        self._logger.info(f'Working directory: {workdir}')

        # Run it.
        # WARNING: We do not yet handle situations where a rank has no work to do.
        # See https://github.com/kassonlab/run_brer/issues/18
        # and https://github.com/kassonlab/run_brer/issues/55
        with context as session:
            session.run()

        # Through at least gmxapi 0.4, the *potentials* attribute is created on
        # the Context for any Session launched with MD work to perform. An explicit
        # error message here should be more helpful than an AttributeError below,
        # but we don't really know what went wrong.
        # Ref https://github.com/kassonlab/run_brer/issues/55
        if not hasattr(context, 'potentials'):
            raise RuntimeError('Invalid gmxapi Context: missing "potentials" attribute.')

        for i in range(len(self.__names)):
            # TODO: ParallelArrayContext.potentials needs to be declared to avoid IDE
            #  warnings.
            # noinspection PyUnresolvedReferences
            current_name = sites_to_name[context.potentials[i].name]
            # In the future runs (convergence, production) we need the ABSOLUTE VALUE
            # of alpha.
            # noinspection PyUnresolvedReferences
            current_alpha = context.potentials[i].alpha
            if current_alpha == 0.0:
                raise RuntimeError('Alpha value was constrained to 0.0, which indicates something went wrong')

            # noinspection PyUnresolvedReferences
            current_target = context.potentials[i].target

            self.run_data.set(name=current_name, alpha=current_alpha)
            self.run_data.set(name=current_name, target=current_target)
            self._logger.info("Plugin {}: alpha = {}, target = {}".format(current_name,
                                                                          current_alpha,
                                                                          current_target))

        return context

    def __converge(self, tpr_file=None, **kwargs):

        for key in ('append_output',):
            if key in kwargs:
                raise TypeError('Conflicting key word argument. Cannot accept {}.'.format(
                    key))

        self.__prep_input(tpr_file)

        md = from_tpr(self._tprs, append_output=False, **kwargs)
        self.build_plugins(ConvergencePluginConfig())
        if len(self.__plugins) == 0:
            warnings.warn('No BRER restraints are being applied! User error?')
        for plugin in self.__plugins:
            md.add_dependency(plugin)

        workdir = os.getcwd()
        self._logger.info("=====CONVERGENCE INFO======\n")
        self._logger.info(f'Working directory: {workdir}')

        context = _context(md,
                           workdir_list=self.workdirs,
                           communicator=self._communicator)
        # WARNING: We do not yet handle situations where a rank has no work to do.
        # See https://github.com/kassonlab/run_brer/issues/18
        # and https://github.com/kassonlab/run_brer/issues/55
        with context as session:
            session.run()

        # Through at least gmxapi 0.4, the *potentials* attribute is created on
        # the Context for any Session launched with MD work to perform. An explicit
        # error message here should be more helpful than an AttributeError below,
        # but we don't really know what went wrong.
        # Ref https://github.com/kassonlab/run_brer/issues/55
        if not hasattr(context, 'potentials'):
            raise RuntimeError('Invalid gmxapi Context: missing "potentials" attribute.')

        # Get the absolute time (in ps) at which the convergence run finished.
        # This value will be needed if a production run needs to be restarted.
        # noinspection PyUnresolvedReferences
        self.run_data.set(start_time=context.potentials[0].time)
        for name in self.__names:
            current_alpha = self.run_data.get('alpha', name=name)
            current_target = self.run_data.get('target', name=name)
            message = f'Plugin {name}: alpha = {current_alpha}, target = {current_target}'
            self._logger.info(message)

        return context

    def __production(self, tpr_file=None, **kwargs):

        for key in ('append_output', 'end_time'):
            if key in kwargs:
                raise TypeError('Conflicting key word argument. Cannot accept {}.'.format(
                    key))

        tpr_list = list(self._tprs)
        tpr_list[self._rank] = self.__prep_input(tpr_file)
        if tpr_file is not None:
            # If bootstrap TPR is provided, we are not continuing from the
            # convergence phase trajectory.
            self.run_data.set(start_time=0.0)

        # Calculate the time (in ps) at which the trajectory for this BRER iteration should finish.
        # This should be: the end time of the convergence run + the amount of time for
        # production simulation (specified by the user).
        start_time = self.run_data.get('start_time')
        target_end_time = self.run_data.get('production_time') + start_time

        md = from_tpr(tpr_list, end_time=target_end_time, append_output=False, **kwargs)

        self.build_plugins(ProductionPluginConfig())
        if len(self.__plugins) == 0:
            warnings.warn('No BRER restraints are being applied! User error?')
        for plugin in self.__plugins:
            md.add_dependency(plugin)

        workdir = os.getcwd()
        self._logger.info("=====PRODUCTION INFO======\n")
        self._logger.info(f'Working directory: {workdir}')

        context = _context(md,
                           workdir_list=self.workdirs,
                           communicator=self._communicator
                           )
        # WARNING: We do not yet handle situations where a rank has no work to do.
        # See https://github.com/kassonlab/run_brer/issues/18
        # and https://github.com/kassonlab/run_brer/issues/55
        with context as session:
            session.run()

        # Through at least gmxapi 0.4, the *potentials* attribute is created on
        # the Context for any Session launched with MD work to perform. An explicit
        # error message here should be more helpful than an AttributeError below,
        # but we don't really know what went wrong.
        # Ref https://github.com/kassonlab/run_brer/issues/55
        if not hasattr(context, 'potentials'):
            raise RuntimeError('Invalid gmxapi Context: missing "potentials" attribute.')

        # Get the start and end times for the simulation managed by this Python interpreter.
        # Note that these are the times for all potentials in a single simulation
        # (which should be the same). We are not gathering values across any potential ensembles.
        start_times = [potential.start_time for potential in context.potentials if hasattr(
            potential, 'start_time')]
        if len(start_times) > 0:
            session_start_time = start_times[0]
            if not all(session_start_time == t for t in start_times):
                self._logger.warning('Potentials report inconsistent start times: '
                                     ', '.join(str(t) for t in start_times))
            assert session_start_time >= start_time
        else:
            # If the plugin attribute is missing, assume that the convergence phase behaved properly.
            session_start_time = start_time

        end_times = [potential.time for potential in context.potentials if hasattr(potential, 'time')]
        if len(end_times) > 0:
            session_end_time = end_times[0]
            if not all(session_end_time == t for t in end_times):
                self._logger.warning('Potentials report inconsistent end times: '
                                     ', '.join(str(t) for t in end_times))
        else:
            session_end_time = None

        if session_end_time is not None:
            self.run_data.set(end_time=session_end_time)

        trajectory_time = None
        if session_end_time is not None:
            trajectory_time = session_end_time - session_start_time

        if trajectory_time is not None:
            self._logger.info(f"{trajectory_time} ps production phase trajectory segment.")
        for name in self.__names:
            current_alpha = self.run_data.get('alpha', name=name)
            current_target = self.run_data.get('target', name=name)
            self._logger.info("Plugin {}: alpha = {}, target = {}".format(name,
                                                                          current_alpha,
                                                                          current_target))

        return context

    def run(self, tpr_file=None, **kwargs):
        """Perform the MD simulations.

        Each Python interpreter process runs a separate ensemble member.

        Parameters
        ----------
        tpr_file : str, optional
            If provided, use this input file instead of the input from the main
            configuration.
        **kwargs : optional
            Additional key word arguments are passed on to the simulator.


        After the first "iteration", run_brer bootstraps the training and convergence
        phase's trajectory with the checkpoint file from the previous iteration's
        production phase.

        At the beginning of a production phase (when there is not yet a checkpoint file),
        the checkpoint file from the convergence phase is used to start the production
        trajectory **unless** *tpr_file* is given.

        When *tpr_file* is not None, run() does not look for a bootstrapping checkpoint
        file. This can be helpful if a checkpoint file is corrupted or unavailable.
        In general, this means that the *tpr_file* argument should include
        the starting configuration you intend for the phase that you are about to run().
        If you are providing the *tpr_file* because you are changing parameters that
        render existing checkpoints incompatible, you need to either generate the file
        with the checkpoint from which you want to continue, or you may remove the
        checkpoint file from the phase directory and restart that phase.

        Example
        -------
        >>> config_params = {
        ...     "tpr": "{}/topol.tpr".format(data_dir),
        ...     "ensemble_num": 1,
        ...     "ensemble_dir": tmpdir,
        ...     "pairs_json": "{}/pair_data.json".format(data_dir)
        ... }
        >>> rc = RunConfig(**config_params)
        >>> assert rc.run_data.get('phase') == 'training'
        >>> rc.run(threads=2)
        >>> assert rc.run_data.get('phase') == 'convergence'
        >>> rc.run()
        >>> assert rc.run_data.get('phase') == 'production'
        >>> rc.run(tpr_file=new_tpr, max_hours=23.9)

        """
        phase = self.run_data.get('phase')

        self.__set_workdir()

        if phase == 'training':
            context = self.__train(tpr_file=tpr_file, **kwargs)
            if all(getattr(potential, 'converged', True) for potential in context.potentials):
                self.run_data.set(phase='convergence')
            else:
                raise RuntimeError(
                    'Training alpha value has not converged.')
        elif phase == 'convergence':
            context = self.__converge(tpr_file=tpr_file, **kwargs)
            # TODO(#18): Investigate for robustness in the case of
            #  batch workflows and MPI-enabled GROMACS.
            if all(getattr(potential, 'stop_called', True) for potential in context.potentials):
                self.run_data.set(phase='production')
        else:
            context = self.__production(tpr_file=tpr_file, **kwargs)
            requested_production_time = self.run_data.get('production_time')
            start_time = self.run_data.get('start_time')
            end_time = self.run_data.get('end_time')
            if end_time == 0.0:
                self._logger.warning(
                    'Upgrade `brer` plugin module to avoid a bug in which BRER phase may advance '
                    'prematurely. See https://github.com/kassonlab/run_brer/issues/19')
            else:
                assert end_time > start_time
                if end_time - start_time >= requested_production_time:
                    state_dir = os.path.dirname(self.state_json)
                    # The state.json file is overwritten below.
                    # We retain previous state.json files from
                    # completed BRER iteration "i" as state_i.json.
                    # See https://github.com/kassonlab/run_brer/issues/24.
                    archive_name = 'state_' + str(self.run_data.get('iteration')) + '.json'
                    prev_iter_state_json = os.path.join(state_dir, archive_name)
                    if os.path.exists(prev_iter_state_json):
                        message = 'If you intended to re-run the phase, please remove '
                        message += str(prev_iter_state_json)
                        message += '. See https://github.com/kassonlab/run_brer/issues/24'
                        raise RuntimeError(message)
                    else:
                        shutil.copy2(self.state_json, prev_iter_state_json)
                    self.run_data.set(phase='training',
                                      start_time=0,
                                      iteration=(self.run_data.get('iteration') + 1))
        self.run_data.save_config(self.state_json)
        return context
