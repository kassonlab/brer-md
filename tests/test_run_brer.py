import sys

import brer


def test_brer_imported():
    assert brer
    assert "brer" in sys.modules
