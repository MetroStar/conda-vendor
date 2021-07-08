import json
import os
import pathlib
import tempfile
from io import FileIO
from pathlib import Path
from conda_vendor.core import (
        create_manifest,
        CondaChannel,
        create_local_channels,
        create_local_environment_yaml, 
        CondaLockWrapper
)
from unittest.mock import Mock, patch
import pytest
import requests
import subprocess
import yaml



def test_generate_manifest(
    mock_requests_repodata,
    conda_channel_fixture,
    mock_conda_solve_value,
):

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

    conda_channel_fixture.create_directories()
    conda_channel_fixture.fetch()
    actual_result = conda_channel_fixture.generate_manifest(
         conda_solution=mock_conda_solve_value
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

    assert set(expected_packages) == set(actual_packages)


def test_run_create_manifest(minimal_environment, vendor_manifest_dict,conda_channel_fixture):

    expected_local_channel = "file://" + str(conda_channel_fixture.local_channel)
    result_manifest = create_manifest(minimal_environment,
                                      conda_channel=conda_channel_fixture
                                      )
    vendor_manifest_dict == result_manifest


# def test_create_local_environment_yaml(minimal_environment,conda_channel_fixture):

#     test_env_name = "THE_BEST_ENV"
#     expected_file_path =  conda_channel_fixture.channel_root / "local_yaml.yaml"
#     expected_local_channel = "file://" + str(conda_channel_fixture.local_channel)
#     result = create_local_environment_yaml(minimal_environment, conda_channel= conda_channel_fixture, local_environment_name= test_env_name)

#     with open(expected_file_path, "r") as f:
#         result_yaml = yaml.load(f, Loader=yaml.SafeLoader)
#     assert result_yaml['name'] == test_env_name
#     assert result_yaml['channels'][0] == expected_local_channel
#     assert result_yaml['channels'][1] == "nodefaults"


def test_install_from_local_channel_offline(minimal_environment, tmp_path, conda_channel_fixture):
    create_local_channels(minimal_environment, conda_channel=conda_channel_fixture)
    tmp_pkg_path = tmp_path / "local_channel"
    cmd_str = f"conda create -n OBVIOUS_DUMMY_ENV python=3.9.5 -c {tmp_pkg_path} --offline --dry-run"
    process_out = subprocess.check_output(cmd_str,
    stderr=subprocess.STDOUT,
    shell=True).decode('utf-8')
    assert "python=3.9.5" in process_out
    assert "DryRunExit: Dry run. Exiting." in process_out

def test_create_conda_env_from_local_yaml(tmp_path, conda_channel_fixture):
    test_env_name = "the_test_conda_env"
    path_to_local_env_yaml = tmp_path / "local_yaml.yaml"
    create_local_channels(conda_channel_fixture, 
        local_environment_name=test_env_name)
    try:
        cmd_str_clean = f"conda clean --all -y"

        process_out_clean = subprocess.check_output(cmd_str_clean,
                                        stderr=subprocess.STDOUT,
                                        shell=True).decode('utf-8')
    except:
        pass 
    cmd_str_create_env = f"conda env create -f {path_to_local_env_yaml} --offline"
    cmd_str_check_env  = "conda env list "
    cmd_str_list_explicit = f"conda list -n {test_env_name} --explicit"
    cmd_rm_env = f"conda env remove -n {test_env_name}"

    

    process_out_create_env = subprocess.check_output(cmd_str_create_env,
                                        stderr=subprocess.STDOUT,
                                        shell=True).decode('utf-8')

    process_out_env_list = subprocess.check_output(cmd_str_check_env,
                                          stderr=subprocess.STDOUT,
                                          shell=True).decode('utf-8')

    assert test_env_name in process_out_env_list

    process_out_list_explicit = subprocess.check_output(cmd_str_list_explicit,
                                          stderr=subprocess.STDOUT,
                                          shell=True).decode('utf-8')
    assert "https" not in process_out_list_explicit

    process_out_rm_env = subprocess.check_output(cmd_rm_env,
                                        stderr=subprocess.STDOUT,
                                        shell=True).decode('utf-8')

    assert "Remove all packages in environment" in process_out_rm_env
    assert test_env_name in process_out_rm_env

## Integration test reaches out 
def test_conda_lock_solution_with_conda_forge(minimal_conda_forge_env ):
    expected_name = "conda-mirror"
    conda_lock = CondaLockWrapper(minimal_conda_forge_env)
    solution = conda_lock.solve()
    result_names = [d["name"] for d in solution]
    assert expected_name in result_names

def test_download_binaries_with_conda_forge(conda_channel_fixture, tmp_path):
    conda_channel_fixture.download_binaries()
    print(tmp_path)
    assert 1==0

    