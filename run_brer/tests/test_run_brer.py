import run_brer
import sys


def test_run_brer_imported():
    assert run_brer
    assert "run_brer" in sys.modules
