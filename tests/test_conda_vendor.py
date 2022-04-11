from requests.adapters import urldefragauth
from conda_vendor.conda_vendor import get_conda_platform
import pytest
from requests import Response
import hashlib
import json
from ruamel.yaml import YAML
from requests import Response
from unittest import TestCase
from unittest.mock import Mock, patch, call, mock_open
from yaml import safe_load
from yaml.loader import SafeLoader
import os


@patch("struct.calcsize")
def test_get_conda_platform(mock_struct) -> None:
    test_platform = "linux"
    mock_struct.return_value = 4
    expected = "linux-32"
    result = get_conda_platform(test_platform)
    assert expected == result
    assert mock_struct.call_count == 1


def test_get_conda_platform_custom():
    test_platforms = ["linux-64", "linux-32", "win-64", "win-32", "osx-64"]
    expected_returns = ["linux-64", "linux-32", "win-64", "win-32", "osx-64"]

    actual_returns = [get_conda_platform(custom_platform=p) for p in test_platforms]
    assert set(actual_returns) == set(expected_returns)

