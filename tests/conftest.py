"""Configuration and fixtures for pytest."""

import json
import logging
import os
import shutil
import sys
import tempfile
import warnings
from contextlib import contextmanager

import pytest

if sys.version_info.major > 3 or sys.version_info.minor >= 10:
    from importlib.resources import files, as_file
else:
    from importlib_resources import files, as_file


@pytest.fixture(scope='session')
def simulation_input():
    source = files('brer').joinpath('data', 'topol.tpr')
    with as_file(source) as tpr_file:
        yield tpr_file


@pytest.fixture(scope='session')
def pair_data_file():
    source = files('brer').joinpath('data', 'pair_data.json')
    with as_file(source) as pair_data:
        yield pair_data


@pytest.fixture(scope='session')
def raw_pair_data():
    """
    Three DEER distributions for testing purposes.

    :return: contents of :file:`brer/data/pair_data.json`
    """
    raw_data = files('brer').joinpath('data', 'pair_data.json').read_text()
    pair_data = json.loads(raw_data)
    assert pair_data["196_228"]["distribution"][0] == 3.0993964770242886e-55
    return pair_data

# TODO: This issue should be resolved. Remove the monkey-patch.
# Need to monkey-patch subprocess.run until gmxapi can be fixed.
# MPI-related environment variables will cause GROMACS command line tools to
# try to MPI_Init_thread (and fail) even though mpi4py has already called MPI_Init.
import functools
import subprocess
env = {key: value for key, value in os.environ.items() if key.startswith('GMX')}
env['PATH'] = os.getenv('PATH')
subprocess.run = functools.partial(subprocess.run, env=env)


def pytest_addoption(parser):
    """Add a command-line user option for the pytest invocation."""
    parser.addoption(
        '--rm',
        action='store',
        default='always',
        choices=['always', 'never', 'success'],
        help='Remove temporary directories "always", "never", or on "success".'
    )


@pytest.fixture(scope='session')
def remove_tempdir(request):
    """pytest fixture to get access to the --rm CLI option."""
    return request.config.getoption('--rm')


@contextmanager
def scoped_chdir(dir):
    oldpath = os.getcwd()
    os.chdir(dir)
    try:
        yield dir
        # If the `with` block using scoped_chdir produces an exception, it will
        # be raised at this point in this function. We want the exception to
        # propagate out of the `with` block, but first we want to restore the
        # original working directory, so we skip `except` but provide a `finally`.
    finally:
        os.chdir(oldpath)


@contextmanager
def _cleandir(remove_tempdir):
    """Context manager for a clean temporary working directory.

    Arguments:
        remove_tempdir (str): whether to remove temporary directory "always",
                              "never", or on "success"

    The context manager will issue a warning for each temporary directory that
    is not removed.
    """

    newpath = tempfile.mkdtemp()

    def remove():
        shutil.rmtree(newpath)

    def warn():
        warnings.warn('Temporary directory not removed: {}'.format(newpath))

    if remove_tempdir == 'always':
        callback = remove
    else:
        callback = warn
    try:
        with scoped_chdir(newpath):
            yield newpath
        # If we get to this line, the `with` block using _cleandir did not throw.
        # Clean up the temporary directory unless the user specified `--rm never`.
        # I.e. If the user specified `--rm success`, then we need to toggle from `warn` to `remove`.
        if remove_tempdir != 'never':
            callback = remove
    finally:
        callback()


@pytest.fixture
def cleandir(remove_tempdir):
    """Provide a clean temporary working directory for a test.

    Example usage:

        import os
        import pytest

        @pytest.mark.usefixtures("cleandir")
        def test_cwd_starts_empty():
            assert os.listdir(os.getcwd()) == []
            with open("myfile", "w") as f:
                f.write("hello")

        def test_cwd_also_starts_empty(cleandir):
            assert os.listdir(os.getcwd()) == []
            assert os.path.abspath(os.getcwd()) == os.path.abspath(cleandir)
            with open("myfile", "w") as f:
                f.write("hello")

        @pytest.mark.usefixtures("cleandir")
        class TestDirectoryInit(object):
            def test_cwd_starts_empty(self):
                assert os.listdir(os.getcwd()) == []
                with open("myfile", "w") as f:
                    f.write("hello")

            def test_cwd_also_starts_empty(self):
                assert os.listdir(os.getcwd()) == []
                with open("myfile", "w") as f:
                    f.write("hello")

    Ref: https://docs.pytest.org/en/latest/fixture.html#using-fixtures-from-classes-modules-or-projects
    """
    with _cleandir(remove_tempdir) as newdir:
        yield newdir


@pytest.fixture(scope='session')
def gmxcli():
    try:
        import gmxapi.commandline
        command = gmxapi.commandline.cli_executable()
    except (ImportError, AttributeError):
        # The gmxapi version predates the cli_executable() utility.
        # Search for the cli binary.
        allowed_command_names = ['gmx', 'gmx_mpi']
        command = None
        for command_name in allowed_command_names:
            if command is not None:
                break
            command = shutil.which(command_name)
            if command is None:
                gmxbindir = os.getenv('GMXBIN')
                if gmxbindir is None:
                    gromacsdir = os.getenv('GROMACS_DIR')
                    if gromacsdir is not None and gromacsdir != '':
                        gmxbindir = os.path.join(gromacsdir, 'bin')
                if gmxbindir is None:
                    gmxapidir = os.getenv('gmxapi_DIR')
                    if gmxapidir is not None and gmxapidir != '':
                        gmxbindir = os.path.join(gmxapidir, 'bin')
                if gmxbindir is not None:
                    gmxbindir = os.path.abspath(gmxbindir)
                    command = shutil.which(command_name, path=gmxbindir)
    if command is None:
        message = "Tests need 'gmx' command line tool, but could not find it on the path."
        raise RuntimeError(message)
    try:
        assert os.access(command, os.X_OK)
    except Exception as E:
        raise RuntimeError('"{}" is not an executable gmx wrapper program'.format(command)) from E
    yield str(command)


@pytest.fixture(scope='class')
def spc_water_box(gmxcli, remove_tempdir):
    """Provide a TPR input file for a simple simulation.

    Prepare the MD input in a freshly created working directory.
    """
    try:
        import gmxapi as gmx
    except (ImportError, ModuleNotFoundError):
        current_dir = os.path.dirname(__file__)
        file_path = os.path.join(current_dir, 'data', 'topol.tpr')
        yield os.path.abspath(file_path)
    else:
        # TODO: (#2896) Fetch MD input from package / library data.
        # Example:
        #     import pkg_resources
        #     # Note: importing pkg_resources means setuptools is required for running this test.
        #     # Get or build TPR file from data bundled via setup(package_data=...)
        #     # Ref https://setuptools.readthedocs.io/en/latest/setuptools.html#including-data-files
        #     from gmx.data import tprfilename

        with _cleandir(remove_tempdir) as tempdir:

            testdir = os.path.dirname(__file__)
            with open(os.path.join(testdir, 'testdata.json'), 'r') as fh:
                testdata = json.load(fh)

            # TODO: (#2756) Don't rely on so many automagical behaviors (as described in comments below)

            structurefile = os.path.join(tempdir, 'structure.gro')
            # We let `gmx solvate` use the default solvent. Otherwise, we would do
            #     gro_input = testdata['solvent_structure']
            #     with open(structurefile, 'w') as fh:
            #         fh.write('\n'.join(gro_input))
            #         fh.write('\n')

            topfile = os.path.join(tempdir, 'topology.top')
            top_input = testdata['solvent_topology']
            # `gmx solvate` will append a line to the provided file with the molecule count,
            # so we strip the last line from the input topology.
            with open(topfile, 'w') as fh:
                fh.write('\n'.join(top_input[:-1]))
                fh.write('\n')

            assert os.path.exists(topfile)
            solvate = gmx.commandline_operation(gmxcli,
                                                arguments=['solvate', '-box', '5', '5', '5'],
                                                # We use the default solvent instead of specifying one.
                                                # input_files={'-cs': structurefile},
                                                output_files={'-p': topfile,
                                                              '-o': structurefile,
                                                              }
                                                )
            if not os.path.exists(topfile):
                raise RuntimeError(f'{topfile} does not exist.')

            logging.debug('Running solvate.')
            if solvate.output.returncode.result() != 0:
                logging.debug('Solvate error output: ' + solvate.output.erroroutput.result())
                raise RuntimeError('solvate failed in spc_water_box testing fixture.')

            # Choose an exactly representable dt of 2^-9 ps (approximately 0.002)
            dt = 2.**-9.
            mdp_input = [('integrator', 'md'),
                         ('dt', dt),
                         ('cutoff-scheme', 'Verlet'),
                         ('nsteps', 2),
                         ('nstxout', 1),
                         ('nstvout', 1),
                         ('nstfout', 1),
                         ('tcoupl', 'v-rescale'),
                         ('tc-grps', 'System'),
                         ('tau-t', 1),
                         ('ref-t', 298)]
            mdp_input = '\n'.join([' = '.join([str(item) for item in kvpair]) for kvpair in mdp_input])
            mdpfile = os.path.join(tempdir, 'md.mdp')
            with open(mdpfile, 'w') as fh:
                fh.write(mdp_input)
                fh.write('\n')
            tprfile = os.path.join(tempdir, 'topol.tpr')
            # We don't use mdout_mdp, but if we don't specify it to grompp,
            # it will be created in the current working directory.
            mdout_mdp = os.path.join(tempdir, 'mdout.mdp')

            grompp = gmx.commandline_operation(gmxcli, 'grompp',
                                               input_files={
                                                   '-f': mdpfile,
                                                   '-p': solvate.output.file['-p'],
                                                   '-c': solvate.output.file['-o'],
                                                   '-po': mdout_mdp,
                                               },
                                               output_files={'-o': tprfile})
            tprfilename = grompp.output.file['-o'].result()
            if grompp.output.returncode.result() != 0:
                logging.debug(grompp.output.erroroutput.result())
                raise RuntimeError('grompp failed in spc_water_box testing fixture.')

            # TODO: more inspection of grompp errors...
            if not os.path.exists(tprfilename):
                raise RuntimeError(f'Failed to produce {tprfilename}')

            yield tprfilename
