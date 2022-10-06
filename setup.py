"""Python setuptools script for custom build_ext.

This script is not intended as a direct entry point. Instead of `python setup.py ...`,
please use `pip install ...`

Reference:
https://setuptools.pypa.io/en/latest/userguide/ext_modules.html#building-extension-modules
"""

from setuptools import setup


try:
    # from _custom_build.backend import CMakeBuild, CMakeExtension
    from backend import CMakeBuild, CMakeExtension
except ImportError as e:
    raise RuntimeError(
        'Could not load in-tree build backend. See installation instructions.'
    ) from e


setup(
    ext_modules=[CMakeExtension(name='brer.md', sourcedir='src/plugin')],
    cmdclass={"build_ext": CMakeBuild},
    zip_safe=False
)
