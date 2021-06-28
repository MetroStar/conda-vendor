import json
import os
import tempfile
from io import FileIO
from pathlib import Path
from conda_vendor.core import conda_vendor

def test_solve_and_create_vendor_environment_artifacts(minimal_environment):
    result_manifest = conda_vendor(minimal_environment)
    assert "python-3.9.5-h12debd9_4.tar.bz2" in result_manifest
    # assert result_repodata == json.loads(repodata_output)
