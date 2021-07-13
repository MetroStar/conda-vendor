
import os
import pytest
import sys
from unittest.mock import Mock, patch
sys.path.append(os.path.dirname(__file__))
from conda_vendor.core import CondaChannel


@pytest.fixture(scope="function")
def minimal_environment(tmpdir_factory):
    content = """name: minimal_env
channels:
- main
dependencies:
- python=3.9.5"""
    fn = tmpdir_factory.mktemp("minimal_env").join("env.yml")
    fn.write(content)
    return fn


@pytest.fixture(scope="function")
def minimal_conda_forge_environment(tmpdir_factory):
    content = """name: minimal_conda_forge_env
channels:
- main
- conda-forge
dependencies:
- python=3.9.5
- conda-mirror=0.8.2
"""
    fn = tmpdir_factory.mktemp("minimal_env").join("env.yml")
    fn.write(content)
    return fn


@pytest.fixture
def minimal_conda_lock_solution():
    return {}


@pytest.fixture
def conda_channel_fixture(tmp_path, minimal_conda_forge_environment, scope="module"):
    return CondaChannel(minimal_conda_forge_environment, channel_root=tmp_path)


from unittest.mock import Mock


def mock_response(
    status=200, content=b"CONTENT", json_data=None, raise_for_status=None
):
    """
    since we typically test a bunch of different
    requests calls for a service, we are going to do
    a lot of mock responses, so its usually a good idea
    to have a helper function that builds these things
    """
    mock_resp = Mock()
    # mock raise_for_status call w/optional error
    mock_resp.raise_for_status = Mock()
    if raise_for_status:
        mock_resp.raise_for_status.side_effect = raise_for_status
    # set status code and content
    mock_resp.status_code = status
    mock_resp.content = content
    # add json data if provided
    if json_data:
        mock_resp.json = Mock(return_value=json_data)
    return mock_resp



