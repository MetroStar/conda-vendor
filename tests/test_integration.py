import json
import os
import tempfile
from io import FileIO
from pathlib import Path
from conda_vendor.core import conda_vendor, CondaChannel
from unittest.mock import Mock, patch
import pytest


@pytest.fixture
def conda_channel_fixture(tmp_path, mock_requests_repodata, scope="module"):
    return CondaChannel(channel_path=tmp_path)


# TODO: .split here in names would require new static unfiltered repodata.json  .conda vs .tar
def test_conda_vendor_artifacts_from_specs(
    mock_requests_repodata,
    vendor_manifest_dict,
    conda_channel_fixture,
    mock_conda_solve_value,
):


    conda_channel_fixture.create_directories()
    specs = ["python=3.9.5"]
    actual_result = conda_channel_fixture.conda_vendor_artifacts_from_solutions(requests=mock_requests_repodata, conda_solution = mock_conda_solve_value )
    expected_result = vendor_manifest_dict
    assert len(actual_result["resources"]) == len(expected_result["resources"])
    assert set(actual_result.keys()) == set(expected_result.keys())
    expected_packages = [
        dict_["name"].split("-")[0] for dict_ in expected_result["resources"]
    ]
    actual_packages = [
        dict_["name"].split("-")[0] for dict_ in actual_result["resources"]
    ]
    assert set(expected_packages) == set(actual_packages)

@patch("conda_vendor.core.CondaLockWrapper")
def test_run_conda_vendor(
    mock_CondaLockWrapper,
    minimal_environment,
    mock_conda_solve_value,
    mock_conda_parse_value,
):
    mock_CondaLockWrapper.parse.return_value = mock_conda_parse_value
    mock_CondaLockWrapper.solve.return_value = mock_conda_solve_value
    result_manifest = conda_vendor(minimal_environment)
    print("result_manifest", result_manifest)
    assert "python-3.9.5-h12debd9_4.tar.bz2" in result_manifest
    # assert result_repodata == json.loads(repodata_output)


def test_install_from_local_channel_offline():
    pass
