import sys

import run_brer


def test_run_brer_imported():
    assert run_brer
    assert "run_brer" in sys.modules
