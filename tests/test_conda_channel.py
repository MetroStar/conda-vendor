import hashlib
import json
from unittest import TestCase
from unittest.mock import Mock, call, mock_open, patch

import pytest
from ruamel.yaml import YAML
from requests import Response
from requests.adapters import urldefragauth
from yaml import safe_load
from ruamel.yaml import YAML
from conda_vendor.conda_vendor import improved_download

from .conftest import mock_response


@patch("requests.Session.get")
def test_improved_download(mock) -> None:
    mock.return_value = Mock(Response)
    test_url = "https://NOT_REAL.com"
    result = improved_download(test_url)
    result_called_with = mock.call_args[0][0]
    assert result_called_with == test_url
    assert mock.call_count == 1
    assert isinstance(result, Response)


#@patch("conda_vendor.conda_channel.improved_download")
#def test_CondaChannel_fetch_and_filter_repodata(mock_download, conda_channel_fixture):
#
#    fake_manifest_subset_metadata = {
#        "repodata_url": "https://url1",
#        "entries": [
#            {"fn": "file1"},
#            {"fn": "file2"},
#            {"fn": "file3"},
#        ],
#    }
#    fake_live_repo_data_json = {
#        "info": {"subdir": "fake_subdir"},
#        "packages": {
#            "file1": {"id": 1},
#            "badfile1": {"id": 2},
#            "file2": {"id": 3},
#            "badfile2": {"id": 4},
#        },
#        "packages.conda": {
#            "file3": {"id": 5},
#            "badfile3": {"id": 6},
#            "file4": {"id": 7},
#            "badfile4": {"id": 8},
#        },
#    }
#    mock_download.return_value = mock_response(json_data=fake_live_repo_data_json)
#
#    fake_conda_subdir = "fake_subdir"
#
#    expected = {
#        "info": {"subdir": "fake_subdir"},
#        "packages": {
#            "file1": {"id": 1},
#            "file2": {"id": 3},
#        },
#        "packages.conda": {"file3": {"id": 5}},
#    }
#    expected_mock_call = call("https://url1")
#
#    result = conda_channel_fixture.fetch_and_filter_repodata(
#        fake_conda_subdir, fake_manifest_subset_metadata
#    )
#
#    assert mock_download.call_args == expected_mock_call
#    assert mock_download.call_count == 1
#    TestCase().assertDictEqual(result, expected)


#@patch("conda_vendor.conda_channel.improved_download")
#def test_CondaChannel_download_and_validate(mock, tmp_path):
#    expected_raw = b"DUMMY_DATA"
#    expected_path = tmp_path / "dummy.data"
#    expected_hash = hashlib.sha256(expected_raw).hexdigest()
#    expected_url = "https://should_have_been_a_doctor.com"
#    mock.return_value = mock_response(content=expected_raw)
#    CondaChannel.download_and_validate(
#        out=expected_path, url=expected_url, sha256=expected_hash
#    )
#    with open(expected_path, "rb") as f:
#        assert f.read() == expected_raw
#    mock.assert_called_with(expected_url)
#    assert mock.call_count == 1
