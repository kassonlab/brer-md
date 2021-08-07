"""
run_brer
"""

# Handle versioneer
from ._version import get_versions
__version__ = get_versions()['version']
__git_revision__ = get_versions()['full-revisionid']
del get_versions
