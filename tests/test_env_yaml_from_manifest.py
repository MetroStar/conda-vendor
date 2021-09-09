# TODO: Utils ? like load so we don't duplicate code ?
from unittest import TestCase
from unittest.mock import patch

import pytest
import yaml
from yaml import SafeLoader

from conda_vendor.env_yaml_from_manifest import YamlFromManifest


@pytest.fixture
def yml_man_fixture(tmp_path, get_path_location_for_manifest_fixture):
    test_meta_manifest_path = get_path_location_for_manifest_fixture
    return YamlFromManifest(
        channel_root=tmp_path, meta_manifest_path=test_meta_manifest_path
    )


def test_YamlFromManifest_init_(yml_man_fixture):
    test_manifest_path = yml_man_fixture.meta_manifest_path
    with open(test_manifest_path, "r") as f:
        expected = yaml.load(f, Loader=SafeLoader)
    result = yml_man_fixture.meta_manifest
    TestCase().assertDictEqual(expected, result)


def test_get_packages_from_manifest(yml_man_fixture):
    expected_packages = ["brotlipy=0.7.0", "ensureconda=1.4.1"]
    result_packages = yml_man_fixture.get_packages_from_manifest()
    TestCase().assertListEqual(expected_packages, result_packages)


def test_get_local_channels_paths(tmp_path, yml_man_fixture):
    test_channel_names = ["local_conda-forge", "local_main"]
    expected_channels = [str(tmp_path / c) for c in test_channel_names]
    result_channels = yml_man_fixture.get_local_channels_paths(tmp_path)
    print(expected_channels)
    print(result_channels)
    TestCase().assertCountEqual(expected_channels, result_channels)


def test_create_yaml(tmp_path, yml_man_fixture):
    test_env_name = "test_env"
    expected_env_yaml = {
        "name": "test_env",
        "channels": [f"{tmp_path}/local_main", f"{tmp_path}/local_conda-forge"],
        "dependencies": ["brotlipy=0.7.0", "ensureconda=1.4.1"],
    }
    result = yml_man_fixture.create_yaml(tmp_path, test_env_name)
    TestCase().assertDictEqual(expected_env_yaml, result)
