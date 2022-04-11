import os
import subprocess
import json
from unittest import TestCase
from unittest.mock import Mock, patch
from ruamel.yaml import YAML
from click.testing import CliRunner
from conda_vendor.conda_vendor import (
        hotfix_vendored_repodata_json,
        get_lock_spec_for_environment_file,
        solve_environment,
        get_fetch_actions,
        reconstruct_repodata_json,
        create_platform_dir,
        create_noarch_dir)

# vendor command
from conda_vendor.conda_vendor import vendor

# use python_main_defaults_environment fixture
def test_vendor_dry_run(python_main_defaults_environment):
    runner = CliRunner()
    result = runner.invoke(vendor, ['--file', python_main_defaults_environment, '--solver', 'conda', '--platform', 'linux-64', '--dry-run', 'True'])
    assert result.exit_code == 0
    assert 'Dry Run - Will Not Download Files' in result.output
    assert 'Dry Run Complete!' in result.output

    json_output = result.output.split('Dry Run Complete!', 1)[1]
    fetch_actions = json.loads(json_output)
    assert any(pkg['name'] == 'python' for pkg in fetch_actions)
    assert not any(pkg['name'] == 'tensorflow' for pkg in fetch_actions)


# test that the LockSpecification object returned from 
# get _lock_spec_for_environment_file contains the packages defined in
# the python_conda_mirror_main_conda_forge_environment test fixture
def test_get_lock_spec_for_environmen_file(python_conda_mirror_main_conda_forge_environment):
    lock_spec = get_lock_spec_for_environment_file(python_conda_mirror_main_conda_forge_environment)
    assert any(versioned_dep.name == 'python' for versioned_dep in lock_spec.dependencies)
    assert any(versioned_dep.version == '3.9.5.*' for versioned_dep in lock_spec.dependencies)

# test that solve_environment's DryRunInstall object's 
# 'success' field is True
def test_solve_environment(lock_spec_fixture):
    dry_run_install = solve_environment(
            lock_spec_fixture,
            'conda',
            'linux-64',
            )
    assert dry_run_install['success'] == True


# this integration test runs the 
# get_fetch_actions function which takes a DryRunInstall from a conda-lock solve,
# and subsequently run the patch_link_actions function to patch our DryRunInstall
# by converting the LINK actions to FETCH actions
def test_fetch_actions(dry_run_install_fixture):
    solver = "conda"
    platform = "linux-64"
    fetch_action_packages = get_fetch_actions(solver, platform, dry_run_install_fixture)
    assert any(fetch_action['name'] == 'python' for fetch_action in fetch_action_packages)
    assert any(fetch_action['version'] == '3.9.5' for fetch_action in fetch_action_packages)


# this integration test runs hotfix_vendored_repodata_json
# which subsequently calls reconstruct_repodata_json
def test_hotfix_vendored_repodata_json(fetch_action_packages_fixture, tmpdir):
    temp_vendored_dir = tmpdir.mkdir("test-hotfix-repodata")
    create_platform_dir(temp_vendored_dir, "linux-64")
    create_noarch_dir(temp_vendored_dir)
    hotfix_vendored_repodata_json(fetch_action_packages_fixture, temp_vendored_dir)
    assert os.path.exists(f"{temp_vendored_dir}/noarch/repodata.json")
    assert os.path.exists(f"{temp_vendored_dir}/linux-64/repodata.json")
