import json
import os
import pathlib
import tempfile
from io import FileIO
from pathlib import Path
from conda_vendor.core import conda_vendor, CondaChannel
from unittest.mock import Mock, patch
import pytest
import requests


@pytest.fixture
def conda_channel_fixture(tmp_path, mock_requests_repodata, scope="module"):
    return CondaChannel(channel_path=tmp_path)


# TODO: .split here in names would require new static unfiltered repodata.json  .conda vs .tar
@patch("requests.get")
def test_conda_vendor_artifacts_from_specs(
    mock_requests_data_repo,
    vendor_manifest_dict,
    conda_channel_fixture,
    mock_conda_solve_value,
):
    # Here to show this is a throw away
    mock_requests_data_repo.json.return_value = "FOO_BAR"
    mock_requests_data_repo.return_value = "FOO_BAR2"

    conda_channel_fixture.create_directories()
    actual_result = conda_channel_fixture.conda_vendor_artifacts_from_solutions(
        requests=mock_requests_data_repo, conda_solution=mock_conda_solve_value
    )
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


#TODO: NEEDS more work reaches out to internet but we want a test to do this 
def test_run_conda_vendor(minimal_environment,tmp_path,vendor_manifest_dict

):  
    expected_manifest = vendor_manifest_dict
    result_manifest = conda_vendor(minimal_environment,outpath=tmp_path)
    print("result_manifest", result_manifest)
    expected_manifest == result_manifest
    # assert "python-3.9.5-h12debd9_4.tar.bz2" in result_manifest


def test_install_from_local_channel_offline():
    pass
