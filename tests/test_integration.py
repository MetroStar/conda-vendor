import os
import subprocess
from unittest import TestCase
from unittest.mock import Mock, patch

import yaml

from conda_vendor.cli import (
    create_ironbank_from_meta_manifest,
    create_local_channels_from_meta_manifest,
    create_meta_manifest_from_env_yml,
    create_yaml_from_manifest,
)
from conda_vendor.custom_manifest import IBManifest


def test_create_meta_manifest_from_env_yml(tmp_path, minimal_conda_forge_environment):

    test_manifest_filename = "test_metamanifest.yaml"
    expected_manifest_path = tmp_path / test_manifest_filename
    expected_packages = ["python=3.9.5", "conda-mirror=0.8.2"]

    def test_get_packages_from_manifest(meta_manifest, expected_packages):
        """
        Just a helper to make sure we got the packages we asked for
        """
        i_bank_pkg_list = []
        for channel_dict in meta_manifest.values():
            for platform_dict in channel_dict.values():
                for package_dict in platform_dict["entries"]:
                    name = package_dict["name"]
                    version = package_dict["version"]
                    dep_entry = f"{name}={version}"
                    if dep_entry in expected_packages:
                        i_bank_pkg_list.append(dep_entry)
        return i_bank_pkg_list

    create_meta_manifest_from_env_yml(
        minimal_conda_forge_environment, tmp_path, test_manifest_filename
    )
    with open(expected_manifest_path) as f:
        actual_manifest = yaml.load(f, Loader=yaml.SafeLoader)

    assert "main" in actual_manifest.keys()
    assert "conda-forge" in actual_manifest.keys()
    result_packages = test_get_packages_from_manifest(
        actual_manifest, expected_packages
    )
    TestCase().assertCountEqual(result_packages, expected_packages)


def test_create_local_channels_from_meta_manifest(
    tmp_path, minimal_conda_forge_environment
):
    test_env_name = "the_test_env"
    test_manifest_filename = "test_metamanifest.yaml"
    channel_root = tmp_path
    test_manifest_path = tmp_path / test_manifest_filename
    path_to_env_yaml = tmp_path / f"local_{test_env_name}.yaml"

    create_meta_manifest_from_env_yml(
        minimal_conda_forge_environment, tmp_path, test_manifest_filename
    )

    create_yaml_from_manifest(
        channel_root=tmp_path,
        meta_manifest_path=test_manifest_path,
        env_name=test_env_name,
    )

    create_local_channels_from_meta_manifest(
        channel_root=tmp_path, meta_manifest_path=test_manifest_path
    )

    try:
        cmd_str_clean = f"conda clean --all -y"

        process_out_clean = subprocess.check_output(
            cmd_str_clean, stderr=subprocess.STDOUT, shell=True
        ).decode("utf-8")
    except:
        pass

    cmd_str_create_env = f"conda env create -f {path_to_env_yaml} --offline"
    cmd_str_check_env = "conda env list "
    cmd_str_list_explicit = f"conda list -n {test_env_name} --explicit"
    cmd_rm_env = f"conda env remove -n {test_env_name}"

    new_env = os.environ.copy()
    new_env["CONDA_ADD_PIP_AS_PYTHON_DEPENDENCY"] = "False"

    process_out_create_env = subprocess.check_output(
        cmd_str_create_env, stderr=subprocess.STDOUT, env=new_env, shell=True
    ).decode("utf-8")

    process_out_env_list = subprocess.check_output(
        cmd_str_check_env, stderr=subprocess.STDOUT, shell=True
    ).decode("utf-8")

    assert test_env_name in process_out_env_list

    process_out_list_explicit = subprocess.check_output(
        cmd_str_list_explicit, stderr=subprocess.STDOUT, shell=True
    ).decode("utf-8")
    assert "https" not in process_out_list_explicit

    process_out_rm_env = subprocess.check_output(
        cmd_rm_env, stderr=subprocess.STDOUT, shell=True
    ).decode("utf-8")

    assert "Remove all packages in environment" in process_out_rm_env
    assert test_env_name in process_out_rm_env


@patch("conda_vendor.custom_manifest.IBManifest.__init__")
@patch("conda_vendor.custom_manifest.IBManifest.write_custom_manifest")
def test_create_ironbank_from_meta_manifest(
    mock_c, mock_i, tmp_path, get_path_location_for_manifest_fixture
):
    mock_i.return_value = None
    meta_manifest_path = get_path_location_for_manifest_fixture
    output_manifest_dir = tmp_path

    create_ironbank_from_meta_manifest(meta_manifest_path, output_manifest_dir)
    mock_c.assert_called_once_with(output_manifest_dir)
    mock_i.assert_called_once_with(meta_manifest_path)


@patch("conda_vendor.env_yaml_from_manifest.YamlFromManifest.__init__")
@patch("conda_vendor.env_yaml_from_manifest.YamlFromManifest.create_yaml")
def test_create_yaml_from_manifest(
    mock_c, mock_i, tmp_path, get_path_location_for_manifest_fixture
):
    mock_i.return_value = None

    meta_manifest_path = get_path_location_for_manifest_fixture
    channel_root = tmp_path

    env_name = "forgin-georgin"
    create_yaml_from_manifest(channel_root, meta_manifest_path, env_name)

    mock_c.assert_called_once_with(channel_root, env_name)
    mock_i.assert_called_once_with(channel_root, meta_manifest_path=meta_manifest_path)
