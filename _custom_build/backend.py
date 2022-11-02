"""Custom PEP517 build backend.

Note: critical details of this file borrowed from
https://github.com/pybind/cmake_example/commit/31bc276d91985c9bb94e2b4ec12f3fd528971f2c

See Also:
* https://peps.python.org/pep-0517/#in-tree-build-backends
* https://setuptools.pypa.io/en/latest/build_meta.html#dynamic-build-dependencies-and-other-build-meta-tweaks

The installer should be able to find its GROMACS dependency through the installed
gmxapi Python package. If not, the installer will look for GMXTOOLCHAINDIR,
gmxapi_ROOT, and GROMACS_DIR, in that order. (These are normally defined by the
GMXRC file.) Alternatively, you can provide additional command line input to
CMake through the CMAKE_ARGS environment variable.

Help CMake find the GROMACS compiler toolchain with
``-C  /path/to/gromacs/share/cmake/gromacs{suffix}/gromacs-hints{suffix}.cmake``.
For older GROMACS installations, use
``-DCMAKE_TOOLCHAIN_FILE=/path/to/gromacs/share/cmake/gromacs{suffix}/gromacs-toolchain{suffix}.cmake``

Example:
    export GROMACS_DIR=/path/to/gromacs
    export CMAKE_ARGS="-Dgmxapi_ROOT=$GROMACS_DIR -C $GROMACS_DIR/share/cmake/gromacs/gromacs-hints.cmake"
    pip install brer-md

"""
import os
import pathlib
import re
import subprocess
import sys
import typing
import warnings

try:
    from functools import cache
except ImportError:
    # functools.cache is not available until Python 3.9
    import functools
    cache = functools.lru_cache(maxsize=None)

from setuptools import Extension
from setuptools.command.build_ext import build_ext
from setuptools import build_meta as _orig

if hasattr(str, 'removeprefix'):
    removeprefix = str.removeprefix
else:
    # str.removeprefix was added in 3.9

    def removeprefix(s: str, __prefix: str):
        if s.startswith(__prefix):
            return s[len(__prefix):]
        else:
            return s


class BrerBuildSystemError(Exception):
    """Error processing setup.py for gmxapi Python package."""


# Note that the setuptools.build_meta module objects `build_wheel`, etc, are references
# to bound methods of a _BuildMetaBackend instance that is instantiated at import
# (as _BACKEND).
#
# As of version 65, the setuptools hooks still call a `setup.py` script under the hood
# with the traditional distutils commands. `pip` and `build` will collect command line
# arguments to be provided through the `config_settings` dict (which we can also
# process or extend as we like). Only `--global-option` and `--build-option` are
# officially allowed as root level keys, and allowed global options are not officially
# extensible. See setuptools.build_meta._ConfigSettings.

#Mandatory hooks
build_wheel = _orig.build_wheel
build_sdist = _orig.build_sdist
# If we can't get _BuildMetaBackend.build_wheel() to call run_setup() with our
# custom arguments, we will need to replace part of that call stack, such as by
# subclassing _BuildMetaBackend and overriding.
# def build_wheel():
#     # Need to override _BuildMetaBackend.run_setup()
#     return _orig.build_wheel()


#Optional hooks

prepare_metadata_for_build_wheel = _orig.prepare_metadata_for_build_wheel


def get_requires_for_build_wheel(config_settings=None):
    return _orig.get_requires_for_build_wheel(config_settings) # + [...]


def get_requires_for_build_sdist(self, config_settings=None):
    return _orig.get_requires_for_build_sdist(config_settings) # + [...]


# PEP 660: editable installs
# Ref: https://peps.python.org/pep-0660/
if hasattr(_orig, 'LEGACY_EDITABLE') and not _orig.LEGACY_EDITABLE:
    build_editable = _orig.build_editable
    get_requires_for_build_editable = _orig.get_requires_for_build_editable
    prepare_metadata_for_build_editable = _orig.prepare_metadata_for_build_editable

# gmxapi does not officially support Windows environments.
# However, we can try to be friendly or prepare for a possible future
# in which we can support more platforms.
# Convert distutils Windows platform specifiers to CMake -A arguments
PLAT_TO_CMAKE = {
    "win32": "Win32",
    "win-amd64": "x64",
    "win-arm32": "ARM",
    "win-arm64": "ARM64",
}


# A CMakeExtension needs a sourcedir instead of a file list.
# The name must be the _single_ output extension from the CMake build.
class CMakeExtension(Extension):
    def __init__(self, name, sourcedir=""):
        Extension.__init__(self, name, sources=[])
        self.sourcedir = os.path.abspath(sourcedir)


class CMakeBuild(typing.cast('setuptools.Command', build_ext)):
    """Derived distutils Command for build_extension.

    See https://github.com/pybind/cmake_example for the current version
    of the sample project from which this is borrowed.
    """

    def build_extension(self, ext):
        # The pybind11 package is only needed for `build_ext`, and may not be installed
        # in the caller's environment. By the time this function is called, though,
        # build dependencies will have been checked.
        import pybind11

        extdir = os.path.abspath(os.path.dirname(self.get_ext_fullpath(ext.name)))

        # required for auto-detection & inclusion of auxiliary "native" libs
        if not extdir.endswith(os.path.sep):
            extdir += os.path.sep

        debug = int(os.environ.get("DEBUG", 0)) if self.debug is None else self.debug
        cfg = "Debug" if debug else "Release"

        # CMake lets you override the generator - we need to check this.
        # Can be set with Conda-Build, for example.
        cmake_generator = os.environ.get("CMAKE_GENERATOR", "")

        cmake_args = [
            "-DCMAKE_LIBRARY_OUTPUT_DIRECTORY={}".format(extdir),
            "-DCMAKE_BUILD_TYPE={}".format(cfg),  # not used on MSVC, but no harm
        ]
        build_args = []
        # Adding CMake arguments set as environment variable
        # (needed e.g. to build for ARM OSx on conda-forge)
        if "CMAKE_ARGS" in os.environ:
            cmake_args += [item for item in os.environ["CMAKE_ARGS"].split(" ") if item]

        if self.compiler.compiler_type != "msvc":
            # Using Ninja-build since it a) is available as a wheel and b)
            # multithreads automatically. MSVC would require all variables be
            # exported for Ninja to pick it up, which is a little tricky to do.
            # Users can override the generator with CMAKE_GENERATOR in CMake
            # 3.15+.
            if not cmake_generator:
                try:
                    import ninja  # noqa: F401

                    cmake_args += ["-GNinja"]
                except ImportError:
                    pass

        else:

            # Single config generators are handled "normally"
            single_config = any(x in cmake_generator for x in {"NMake", "Ninja"})

            # CMake allows an arch-in-generator style for backward compatibility
            contains_arch = any(x in cmake_generator for x in {"ARM", "Win64"})

            # Specify the arch if using MSVC generator, but only if it doesn't
            # contain a backward-compatibility arch spec already in the
            # generator name.
            if not single_config and not contains_arch:
                cmake_args += ["-A", PLAT_TO_CMAKE[self.plat_name]]

            # Multi-config generators have a different way to specify configs
            if not single_config:
                cmake_args += [
                    "-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_{}={}".format(cfg.upper(), extdir)
                ]
                build_args += ["--config", cfg]

        if sys.platform.startswith("darwin"):
            # Cross-compile support for macOS - respect ARCHFLAGS if set
            archs = re.findall(r"-arch (\S+)", os.environ.get("ARCHFLAGS", ""))
            if archs:
                cmake_args += ["-DCMAKE_OSX_ARCHITECTURES={}".format(";".join(archs))]

        # Set CMAKE_BUILD_PARALLEL_LEVEL to control the parallel build level
        # across all generators.
        if "CMAKE_BUILD_PARALLEL_LEVEL" not in os.environ:
            # self.parallel is a Python 3 only way to set parallel jobs by hand
            # using -j in the build_ext call, not supported by pip or PyPA-build.
            if hasattr(self, "parallel") and self.parallel:
                # CMake 3.12+ only.
                build_args += ["-j{}".format(self.parallel)]

        if not os.path.exists(self.build_temp):
            os.makedirs(self.build_temp)

        cmake_args = update_gromacs_client_cmake_args(cmake_args)

        has_pybind = False
        for arg in cmake_args:
            if arg.upper().startswith('-DPYBIND11_ROOT'):
                has_pybind = True
        if not has_pybind:
            pybind_root = pybind11.get_cmake_dir()
            if pybind_root:
                cmake_args.append(f'-Dpybind11_ROOT={pybind_root}')

        subprocess.check_call(
            ["cmake", ext.sourcedir] + cmake_args, cwd=self.build_temp
        )
        subprocess.check_call(
            ["cmake", "--build", "."] + build_args, cwd=self.build_temp
        )


def get_gmxapi_config():
    """Get the GROMACS configuration dictionary from the gmxapi package, if available.

    Returns
    -------
    dict
        Contents vary by gmxapi version. (May be empty.)

    """
    try:
        from gmxapi.utility import config
    except ImportError:
        try:
            from gmxapi.commandline import _config as config
        except ImportError:
            config = None

    if config:
        return config()
    else:
        return {}


def _parse_cmake_defines(args: typing.Sequence[str]):
    """Handle various possible syntax for CMake ``-D`` options.

    Ref: https://cmake.org/cmake/help/latest/manual/cmake.1.html#options
    """
    for i, arg in enumerate(args):
        if arg.startswith('-D'):
            definition = removeprefix(arg, '-D')
            if not definition:
                definition = args[i+1]
            key, value = definition.split('=', maxsplit=1)
            key = key.split(':')[0]
            yield key, value


# @cache
def get_cmake_defines(args: typing.Sequence[str]):
    """Get key-value tuples for CMake variables defined as arguments.

    Ref: https://cmake.org/cmake/help/latest/manual/cmake.1.html#options
    """
    return dict(_parse_cmake_defines(args))


# @cache
def cmake_defined(key: str, args: typing.Sequence[str]):
    """Return the value of the key, if defined as a CMake argument, else None."""
    return get_cmake_defines(args).get(key, None)


def get_gmxapi_root(*, config: dict, args: typing.Sequence[str]):
    """Get the value for the gmxapi_ROOT CMake variable.

    First examine the *config* dictionary for hints. Then check the environment,
    """
    # The gmxapi CMake config file is in a path that looks something like
    # $CMAKE_INSTALL_PREFIX/share/cmake/gmxapi/gmxapiConfig.cmake
    # Various gromacs components are installed to directories that are parallel
    # to some part of this path.
    # directory contents that would indicate a viable gmxapi_ROOT.
    sentries = ('gmxapi', 'cmake', 'share', 'gmxapi-config.cmake', 'gmxapiConfig.cmake')
    # Config values that might serve as hints:
    hints = ('gmx_cmake_hints', 'gmx_cmake_toolchain', 'gmx_executable', 'gmx_bindir')

    path = config.get('gmxapi_root', None)
    if path:
        path = pathlib.Path(path).resolve()
    if path and not path.exists():
        warnings.warn(f'Installed gmxapi reports non-existent root path {path}.')
        path = None
    if not path:
        for hint in [pathlib.Path(config[key]).resolve() for key in hints if key in config]:
            guess = hint.parent
            while guess != guess.root and not path:
                for sentry in sentries:
                    if (guess / sentry).exists():
                        path = guess
                        break
                guess = guess.parent
            if path and path.exists():
                break
    # Check the environment. Let CMake defines override environment variables.
    candidate_found = False
    cmake_vars = get_cmake_defines(args)
    for key in ('gmxapi_ROOT', 'GMXAPI_ROOT', 'GMXAPI_DIR', 'GROMACS_DIR', 'CMAKE_PREFIX_PATH'):
        if key in cmake_vars:
            _var = cmake_vars[key]
        else:
            _var = os.getenv(key)
        if _var:
            candidate = pathlib.Path(_var).resolve()
            if path and (path.samefile(candidate) or candidate in path.parents):
                # Skip if candidate provides the same or less information than config path.
                continue
            for sentry in sentries:
                if (candidate / sentry).exists():
                    if path:
                        warnings.warn(
                            f'Overriding gmxapi config path {path} with -Dgmxapi_ROOT={candidate} from '
                            f'{key} environment variable.'
                        )
                    path = candidate
                    candidate_found = True
                    break
        if candidate_found:
            break
    if not path:
        # Try to guess from args.
        hint = ''
        if '-C' in args:
            hint = args[args.index('-C') + 1]
        if not hint:
            for guess in ('CMAKE_TOOLCHAIN_FILE', 'GMXTOOLCHAINDIR'):
                if guess in cmake_vars:
                    hint = cmake_vars[guess]
                else:
                    hint = os.getenv(guess)
                if hint:
                    break
        if hint and os.path.exists(hint):
            guess = pathlib.Path(hint).resolve()
            while guess != guess.root and not path:
                for sentry in sentries:
                    if (guess / sentry).exists():
                        path = guess
                        break
                guess = guess.parent
    if path:
        return str(path)
    else:
        return None


def get_cmake_hints(*, config: dict, args: typing.Sequence[str]):
    """Get a file for the -C CMake argument, if possible.

    Check the *config* dict, first. If -C is provided in *args*, use the
    user-provided path, but warn if overriding a path from *config*.

    If a hints file is not provided explicitly, try to locate a hints file from
    other values in *config* or *args*.

    Ref: https://cmake.org/cmake/help/latest/manual/cmake.1.html#options
    """
    hints_file = config.get('gmx_cmake_hints', None)
    if '-C' in args:
        hint = args[args.index('-C') + 1]
        if os.path.exists(hint):
            hint = pathlib.Path(hint).resolve()
            if hints_file is not None and not hint.samefile(hints_file):
                warnings.warn(
                    f'Overriding gmxapi configuration (hints file {hints_file}) with "-C {hint}"'
                )
            hints_file = str(hint)
    if hints_file and not os.path.exists(hints_file):
        raise BrerBuildSystemError(
            f'"-C {hints_file}" refers to non-existent CMake initial-cache file.'
        )
    return hints_file


def get_toolchain_file(*, config: dict, args: typing.Sequence[str]):
    toolchain_file = os.getenv('CMAKE_TOOLCHAIN_FILE')
    if not toolchain_file:
        toolchain_file = config.get('gmx_cmake_toolchain', None)
    if not toolchain_file:
        suffix = os.getenv('GROMACS_SUFFIX', cmake_defined('GROMACS_SUFFIX', args))
        if suffix is None:
            suffix = config.get('gmx_suffix', None)
        if suffix is None:
            if 'gmx_mpi_type' in config and 'gmx_double' in config:
                suffix = ''
                if config['gmx_mpi_type'] == 'library':
                    suffix += '_mpi'
                if config['gmx_double']:
                    suffix += '_d'
        if suffix is None:
            # Guessing the suffix is too hard on older GROMACS/gmxapi combinations.
            # See https://gitlab.com/gromacs/gromacs/-/issues/4334
            return None
        gmx_toolchain_dir = os.getenv('GMXTOOLCHAINDIR', cmake_defined('GMXTOOLCHAINDIR', args))
        if gmx_toolchain_dir and os.path.exists(gmx_toolchain_dir):
            toolchain_file = os.path.join(
                gmx_toolchain_dir,
                f'gromacs{suffix}',
                'gromacs-toolchain' + suffix + '.cmake')
    return toolchain_file


def update_gromacs_client_cmake_args(args: typing.Sequence[str]) -> typing.List[str]:
    """Try to convert information from command line environment to usable client CMake stuff.

    Normalize user input and automated GROMACS detection to produce a list of CMake arguments
    containing a ``-Dgmxapi_ROOT`` and, if possible, hints for generating the CMake build tool
    chain.

    Args:
        args: CMake args provided by CMakeBuild instance, including user input from CMAKE_ARGS.

    First, we must determine a single value of ``gmxapi_ROOT``. If available, we
    first check `gmxapi.utils.config()` or `gmxapi.commandline._config()` for as
    much information as we can derive. We allow user-provided information to
    override the gmxapi package config with a warning.

    If ``CMAKE_ARGS`` contains a ``-C`` option, the value is checked for consistency with the
    ``gmxapi_ROOT`` path.

    If ``CMAKE_ARGS`` contains both ``-C`` and ``-DCMAKE_TOOLCHAIN_FILE`` options,
    both are passed along to CMake and we assume the user knows what they are doing.

    If ``CMAKE_ARGS`` contains neither a ``-C`` option, nor a ``-DCMAKE_TOOLCHAIN_FILE`` option,
    this script attempts to locate a ``gromacs-hints.cmake`` file in order to generate
    a ``-C`` option to add to the CMake arguments for CMakeBuild.
    If the script is unable to locate a ``gromacs-hints.cmake`` file, we fall back
    to the gmxapi 0.2 scheme for ``GMXTOOLCHAINDIR``.

    This function compartmentalizes details that are likely to evolve with issues
    https://gitlab.com/gromacs/gromacs/-/issues/3273
    and
    https://gitlab.com/gromacs/gromacs/-/issues/3279

    See linked issues for more discussion or to join in the conversation.

    This logic can be simplified as support is dropped for older GROMACS or
    gmxapi versions.
    """
    args = list(str(arg) for arg in args)

    gmxapi_config = get_gmxapi_config()
    gmxapi_root = get_gmxapi_root(config=gmxapi_config, args=args)
    if gmxapi_root and cmake_defined('gmxapi_ROOT', args) is None:
        args.append(f'-Dgmxapi_ROOT={gmxapi_root}')

    cmake_hints = get_cmake_hints(config=gmxapi_config, args=args)
    if cmake_hints and '-C' not in args:
        args.extend(('-C', cmake_hints))

    if '-C' not in args:
        # Try to derive a toolchain file argument, if not already present.
        toolchain_file = cmake_defined('CMAKE_TOOLCHAIN_FILE', args)
        if not toolchain_file:
            toolchain_file = get_toolchain_file(config=gmxapi_config, args=args)
            if toolchain_file and os.path.exists(toolchain_file):
                args.append(f'-DCMAKE_TOOLCHAIN_FILE={toolchain_file}')

    return args
