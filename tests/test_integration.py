import os
import subprocess
from unittest import TestCase
from unittest.mock import Mock, patch
from ruamel.yaml import YAML
from click.testing import CliRunner

# vendor command
from conda_vendor.conda_vendor import vendor

# use python_main_defaults_environment fixture
def test_vendor(python_main_defaults_environment):
    runner = CliRunner()
    result = runner.invoke(vendor, ['--file', python_main_defaults_environment, '--solver', 'conda', '--platform', 'linux-64']) 
