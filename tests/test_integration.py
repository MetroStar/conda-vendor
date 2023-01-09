import json
import os
import pytest
import subprocess
import warnings

from click.testing import CliRunner
from pathlib import Path
from ruamel.yaml import YAML
from unittest import TestCase
from unittest.mock import Mock, patch

from conda_vendor.conda_vendor import (
    create_vendored_dir,
    hotfix_vendored_repodata_json,
    solve_environment,
    _reconstruct_repodata_json,
    download_packages,
)

# vendor command
from conda_vendor.conda_vendor import vendor

# use python_main_defaults_environment fixture
def test_vendor_dry_run(python_main_defaults_environment):
    runner = CliRunner()
    result = runner.invoke(
        vendor,
        [
            "--file",
            python_main_defaults_environment,
            "--solver",
            "conda",
            "--platform",
            "linux-64",
            "--dry-run",
        ],
    )
    assert result.exit_code == 0
    assert "Dry Run - Will Not Download Files" in result.output
    assert "Dry Run Complete!" in result.output

    json_output = result.output.split("Dry Run Complete!", 1)[1]
    fetch_actions = json.loads(json_output)
    assert any(pkg["name"] == "python" for pkg in fetch_actions)
    assert not any(pkg["name"] == "tensorflow" for pkg in fetch_actions)


# full run through and dry-run install using vendored channel
# NOTE this test expects that 'mamba' is in your path, if you need to,
# uncomment the skip decorator
# @pytest.mark.skip(reason="mamba is not installed or in $PATH")
def test_vendor_full_runthrough(
    python_main_defaults_environment, tmp_path_factory
):
    warning_message = """This test will only work correctly the first time.

    It seems to not respect the os.chdir(...) in the start.
    to rerun remove the "minimal_env" subdirectory from the working
    directory.
    """

    warnings.warn(warning_message)
    test_path = tmp_path_factory.mktemp("full-runthrough")
    os.chdir(test_path)

    runner = CliRunner()
    vendor_result = runner.invoke(
        vendor,
        ["--file", python_main_defaults_environment, "--solver", "mamba"],
    )
    assert vendor_result.exit_code == 0


# test that the LockSpecification object returned from
# get _lock_spec_for_environment_file contains the packages defined in
# the python_conda_mirror_main_conda_forge_environment test fixture
def test_get_lock_spec_for_environment_file(
    python_conda_mirror_main_conda_forge_environment,
):
    from conda_vendor.conda_vendor import (
        _parse_environment_file,
        _get_conda_platform,
    )

    lock_spec = _parse_environment_file(
        python_conda_mirror_main_conda_forge_environment,
        _get_conda_platform(),
    )
    assert any(
        versioned_dep.name == "python"
        for versioned_dep in lock_spec.dependencies
    )
    assert any(
        versioned_dep.version == "3.9.5.*"
        for versioned_dep in lock_spec.dependencies
    )


# test that solve_environment's DryRunInstall object's
# 'success' field is True
def test_solve_environment(python_conda_mirror_main_conda_forge_environment):

    env = Path(str(python_conda_mirror_main_conda_forge_environment))
    solution = solve_environment(
        env,
        "conda",
        "linux-64",
    )


def test_notsolvable_environment(python_conda_failing_env):
    env = Path(str(python_conda_failing_env))
    with pytest.raises(Exception):
        solution = solve_environment(env, "conda", "linux-64")


# this integration test runs the
# solver to make sure reconstruct_fetch_actions converts LINK to FETCH
def test_solve_environment_link2fetch(
    python_conda_mirror_main_conda_forge_environment,
):

    env = Path(str(python_conda_mirror_main_conda_forge_environment))
    package_list = solve_environment(env, "conda", "linux-64")
    assert any(package["name"] == "python" for package in package_list)
    assert any(package["version"] == "3.9.5" for package in package_list)


# this integration test runs hotfix_vendored_repodata_json
# which subsequently calls reconstruct_repodata_json
def test_hotfix_vendored_repodata_json(
    python_conda_mirror_main_conda_forge_environment, tmp_path_factory
):
    env = Path(str(python_conda_mirror_main_conda_forge_environment))
    temp_dir = tmp_path_factory.mktemp("test-hotfix-repodata")
    root = create_vendored_dir(
        "minimal_conda_forge_env", "linux-64", Path(temp_dir)
    )
    package_list = solve_environment(env, "conda", "linux-64")
    hotfix_vendored_repodata_json(package_list, root)
    assert os.path.exists(f"{str(root)}/noarch/repodata.json")
    assert os.path.exists(f"{str(root)}/linux-64/repodata.json")


# this integration test runs the download_solved_pkgs fn
def test_download_solved_pkgs(
    python_conda_mirror_main_conda_forge_environment, tmp_path_factory
):
    env = Path(str(python_conda_mirror_main_conda_forge_environment))
    temp_dir = tmp_path_factory.mktemp("test-download-target")
    root = create_vendored_dir(
        "minimal_conda_forge_env", "linux-64", Path(temp_dir)
    )
    package_list = solve_environment(env, "conda", "linux-64")
    download_packages(package_list, root, "linux-64")

    assert any(
        "python" in pkg_fn for pkg_fn in os.listdir(f"{root}/linux-64")
    )
