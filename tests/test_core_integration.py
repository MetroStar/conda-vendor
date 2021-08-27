import os
import subprocess
import sys
import yaml
from unittest.mock import patch
from yaml import SafeLoader


from conda_vendor.core import create_manifest, create_local_channels, CondaChannel


def test_int_create_manifest(tmp_path, conda_channel_fixture):
    expected_python_version = "3.9.5"
    expected_mirror_version = "0.8.2"
    test_manifest_filename = "THE_TEST_MANIFEST.YAML"
    path_to_manifest = tmp_path / test_manifest_filename
    create_manifest(conda_channel_fixture, manifest_filename=test_manifest_filename)

    with path_to_manifest.open("r") as f:
        result = yaml.load(f, Loader=SafeLoader)

    yaml.dump(result, sys.stdout, indent=2)
    result_python_version = result["python"]["version"]

    result_mirror_version = result["conda-mirror"]["version"]

    assert expected_python_version == result_python_version
    assert expected_mirror_version == result_mirror_version


def test_int_create_conda_env_from_local_yaml(tmp_path, conda_channel_fixture):
    test_env_name = "the_test_conda_env"
    path_to_local_env_yaml = tmp_path / "local_yaml.yaml"
    create_local_channels(conda_channel_fixture, local_environment_name=test_env_name)

    try:
        cmd_str_clean = f"conda clean --all -y"

        process_out_clean = subprocess.check_output(
            cmd_str_clean, stderr=subprocess.STDOUT, shell=True
        ).decode("utf-8")
    except:
        pass

    cmd_str_create_env = f"conda env create -f {path_to_local_env_yaml} --offline"
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


def test_local_channel_from_manifest(
    tmp_path, minimal_conda_forge_environment, minimal_manifest
):
    test_env_name = "the_test_conda_env_from_manifest"
    test_manifest_fn = "test_manifest.yaml"
    path_to_local_env_yaml = tmp_path / "local_yaml.yaml"
    test_manifest_path = tmp_path / test_manifest_fn

    # # TODO: This just creates our manifest we should probably not do this
    # conda_channel_fixture.create_manifest(manifest_filename=test_manifest_fn)
    # print(conda_channel_fixture.manifest)

    with open(test_manifest_path, "w") as f:
        yaml.dump(minimal_manifest, f, sort_keys=False)

    test_conda_channel = CondaChannel(
        minimal_conda_forge_environment,
        channel_root=tmp_path,
        manifest_path=test_manifest_path,
    )

    create_local_channels(test_conda_channel, local_environment_name=test_env_name)
    try:
        cmd_str_clean = f"conda clean --all -y"

        process_out_clean = subprocess.check_output(
            cmd_str_clean, stderr=subprocess.STDOUT, shell=True
        ).decode("utf-8")
    except:
        pass
    cmd_str_create_env = f"conda env create -f {path_to_local_env_yaml} --offline"
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
