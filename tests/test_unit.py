import subprocess
from unittest.mock import Mock, patch
import requests
from requests import Response
import os
import pytest
import hashlib
import json
from unittest import TestCase
from yaml import safe_load
from yaml.loader import SafeLoader
import yaml
import  requests 
from requests import Response
import struct

from conda_vendor.core import(
    improved_download,
    get_conda_platform,
    CondaChannel
)



from .conftest import mock_response

@patch("requests.Session.get")
def test_improved_download(mock) -> None:
    mock.return_value = Mock(Response)
    test_url = "https://NOT_REAL.com"
    result = improved_download(test_url)
    result_called_with = mock.call_args[0][0]
    assert result_called_with == test_url
    assert mock.call_count == 1 
    assert  isinstance(result, Response)


@patch("struct.calcsize")
def test_get_conda_platform(mock_struct)-> None :
    test_platform='linux'
    mock_struct.return_value= 4 
    expected = "linux-32"
    result = get_conda_platform(test_platform)
    assert expected == result
    assert mock_struct.call_count == 1 







def test_init(minimal_environment):
    conda_channel = CondaChannel(minimal_environment)
    
    #make sure platforms includes noarch and given platform
    expected_platforms = [conda_channel.platform, 'noarch']
    for platform in expected_platforms:
        assert platform in conda_channel.valid_platforms

    #make sure specs has python in it
    assert 'python=3.9.5' in conda_channel.env_deps['specs']
    
    #make sure we have 'defaults' channel
    assert 'defaults' in conda_channel.channels


def test_init_conda_forge(minimal_conda_forge_environment):
    conda_channel = CondaChannel(minimal_conda_forge_environment)
    
    #make sure platforms includes noarch and given platform
    expected_platforms = [conda_channel.platform, 'noarch']
    for platform in expected_platforms:
        assert platform in conda_channel.valid_platforms
    
    #make sure specs has correct packages
    expected_packages = ['python=3.9.5', 'conda-mirror']
    for pkg in expected_packages:
        assert pkg in conda_channel.env_deps['specs']
    
    #make sure we have expected channels 
    expected_channels = ['defaults', 'conda-forge']
    for chan in expected_channels:
        assert chan in conda_channel.channels


def test_init_excludes_nodefaults(tmp_path):

    def create_environment(tmp_path):
        content = """name: minimal_env
channels:
- main
- nodefaults
dependencies:
- python=3.9.5"""
        fn = tmp_path / "env.yml"
        with fn.open('w') as f:
            f.write(content)
        return fn

    environment_yml = create_environment(tmp_path)
    conda_channel = CondaChannel(environment_yml)   

    #make sure we have expected channels 
    assert 'main' in conda_channel.channels
    assert 'nodefaults' not in conda_channel.channels



# assume conda_lock.solve_specs_for_arch works
@patch('conda_lock.conda_lock.solve_specs_for_arch')
def test_solve_environment(mock_solution, conda_channel_fixture):
    solution_data = {
        
    }

    assert 1==0