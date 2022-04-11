import os
import subprocess
import json
from unittest import TestCase
from unittest.mock import Mock, patch
from ruamel.yaml import YAML
from click.testing import CliRunner
from conda_vendor.conda_vendor import (
        hotfix_vendored_repodata_json,
        get_lock_spec_for_environment_file)

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
