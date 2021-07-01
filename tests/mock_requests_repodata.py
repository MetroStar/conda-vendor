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

class Jsoner:
    def json():
        return {'key': 'value'}

class RobMock(requests.Response):
    def __init__(self):
        pass

    def get(*args, **kwargs):
        print(f'got args, {args}')
        return Jsoner()

    def json():
        print(f'called json')
        return '404'


@pytest.fixture
def conda_channel_fixture(tmp_path, mock_requests_repodata, scope="module"):
    return CondaChannel(channel_path=tmp_path)


# TODO: .split here in names would require new static unfiltered repodata.json  .conda vs .tar

def test_generate_manifest(
    mock_requests_repodata,
    conda_channel_fixture,
    mock_conda_solve_value,
):
    # Here to show this is a throw away

    expected_repodata_dict =   {
        "info": {"subdir": "linux-64"},
        "packages": {
            "python-3.9.5-h12debd9_4.tar.bz2": {
                "build": "h12debd9_4",
                "build_number": 4,
                "depends": [
                 
                ],
                "name": "python",
                "sha256": "7fc98fe684cb716a8d19cf20a77ccce3cda3f6da968abaade63edbe006d8f3ba",
                "subdir": "linux-64",
            }
        },
        "packages.conda": {
            "tk-8.6.10-hbc83047_0.conda": {
       
                "name": "tk",
                "sha256": "99fba40357115be361759731fc5a19b7833b4884310f2851f3faadbf33484991",
                "subdir": "linux-64",

            }
        },
    }

    expected_vendor_manifest = {
        "resources": [
            {
                "url": "https://repo.anaconda.com/pkgs/main/linux-64/python-3.9.5-h12debd9_4.tar.bz2",
                "name": "python-3.9.5-h12debd9_4.tar.bz2",
                "validation": {
                    "type": "sha256",
                    "value": "7fc98fe684cb716a8d19cf20a77ccce3cda3f6da968abaade63edbe006d8f3ba",
                },
            },
            {
                "url": "https://repo.anaconda.com/pkgs/main/linux-64/tk-8.6.10-hbc83047_0.conda.conda",
                "name": "tk-8.6.10-hbc83047_0.conda",
                "validation": {
                    "type": "sha256",
                    "value": "99fba40357115be361759731fc5a19b7833b4884310f2851f3faadbf33484991",
            }}
        ]
        }
    mock_requests_get_json_data_repo.return_value = expected_vendor_manifest
    print(mock_requests_get_json_data_repo)
    conda_channel_fixture.create_directories()
    mock = RobMock()
    conda_channel_fixture.fetch(requests=mock)
    actual_result = conda_channel_fixture.generate_manifest(
        requests=mock_requests_get_json_data_repo, conda_solution=mock_conda_solve_value
    )
    expected_result = expected_vendor_manifest
    assert len(actual_result["resources"]) == len(expected_result["resources"])
    assert set(actual_result.keys()) == set(expected_result.keys())
    expected_packages = [
        dict_["name"] for dict_ in expected_result["resources"]
    ]
    actual_packages = [
        dict_["name"] for dict_ in actual_result["resources"]
    ]
    print(actual_result["resources"][0])
    print(expected_result["resources"][0])
    # print(expected_packages )
    # print(actual_packages )
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
