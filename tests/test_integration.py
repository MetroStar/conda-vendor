import json
import os
import tempfile
from io import FileIO
from pathlib import Path
from conda_vendor.core import conda_vendor, conda_vendor_artifacts_from_specs
from unittest.mock import Mock, patch

#TODO: .split here in names would require new static unfiltered repodata.json  .conda vs .tar
@patch("requests.get")
def test_conda_vendor_artifacts_from_specs(mock_requests_download,unfiltered_repo_data_response, vendor_manifest_dict):
    mock_requests_download.get.return_value = unfiltered_repo_data_response
    specs = ["python=3.9.5"]
    actual_result = conda_vendor_artifacts_from_specs(specs)
    expected_result = vendor_manifest_dict
    assert len(actual_result["resources"]) == len(expected_result["resources"])
    assert set(actual_result.keys()) == set(expected_result.keys())
    expected_packages = [ dict_["name"].split("-")[0] for dict_ in expected_result["resources"]]
    actual_packages  = [ dict_["name"].split("-")[0]  for dict_ in actual_result["resources"]]
    assert set(expected_packages) == set(actual_packages)


#TODO: 
def test_conda_vendor(minimal_environment):
    result_manifest = conda_vendor(minimal_environment)
    assert "python-3.9.5-h12debd9_4.tar.bz2" in result_manifest
    # assert result_repodata == json.loads(repodata_output)
