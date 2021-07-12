import json
import os
import pathlib
import tempfile
from io import FileIO
from pathlib import Path
from conda_vendor.core import (
        CondaChannel,
        create_manifest,
        create_local_channels,
        create_local_environment_yaml
)
from unittest.mock import Mock, patch
import pytest
import requests
import subprocess
import yaml

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

    starting_dir = os.getcwd()
    print(f'{starting_dir=}')

    os.chdir(tmp_path)

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

    os.chdir(starting_dir)
    assert "Remove all packages in environment" in process_out_rm_env
    assert test_env_name in process_out_rm_env

