import json
import os
import tempfile
from io import FileIO
from pathlib import Path

import pytest

from conda_vendor.core import conda_vendor
from tests.repodata_fixture import vendor_manifest, repodata_output


@pytest.fixture()
def minimal_environment(tmpdir_factory):
    content = """name: minimal_env
channels:
- defaults
dependencies:
- python=3.9.5"""
    fn = tmpdir_factory.mktemp("minimal_env").join("env.yml")
    fn.write(content)
    return fn


def test_solve_and_create_vendor_environment_artifacts(minimal_environment):
    result_manifest = conda_vendor(minimal_environment)
    assert "python-3.9.5-h12debd9_4.tar.bz2" in result_manifest
    # assert result_repodata == json.loads(repodata_output)
