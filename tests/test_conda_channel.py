from requests.adapters import urldefragauth
from conda_vendor.manifest import (
    MetaManifest,
    LockWrapper,
)
import pytest
from requests import Response
import hashlib
import json
import yaml
from requests import Response
from unittest import TestCase
from unittest.mock import Mock, patch, call, mock_open
from yaml import safe_load
from yaml.loader import SafeLoader
from conda_vendor.conda_channel import CondaChannel, improved_download
from .conftest import mock_response


@patch("yaml.load")
def test_load_manifest(mock, conda_channel_fixture, tmp_path):
    test_manifest_path = tmp_path / "test_manifest.yml"
    with open(test_manifest_path, "w") as y:
        y.write("test")
    conda_channel_fixture.load_manifest(test_manifest_path)
    mock.assert_called_once_with = [test_manifest_path, yaml.SafeLoader]


@patch("requests.Session.get")
def test_improved_download(mock) -> None:
    mock.return_value = Mock(Response)
    test_url = "https://NOT_REAL.com"
    result = improved_download(test_url)
    result_called_with = mock.call_args[0][0]
    assert result_called_with == test_url
    assert mock.call_count == 1
    assert isinstance(result, Response)


@patch("conda_vendor.conda_channel.CondaChannel.load_manifest")
def test_CondaChannel_init_(mock, tmp_path, get_path_location_for_manifest_fixture):
    test_channel_root = tmp_path / "test_channel_root"
    test_manifest_path = get_path_location_for_manifest_fixture

    test_manifest = {
        "main": {"superman": "is_awesome"},
        "conda-forge": {"batman": "is_better"},
    }

    expected_manifest = test_manifest
    expected_channels = ["main", "conda-forge"]

    mock.return_value = test_manifest
    expected_platform = "superman"

    test_conda_channel = CondaChannel(
        channel_root=test_channel_root, meta_manifest_path=test_manifest_path
    )

    result_channels = test_conda_channel.channels
    result_manifest = test_conda_channel.meta_manifest

    mock.assert_called_once_with(test_manifest_path)
    assert result_manifest == expected_manifest
    assert sorted(result_channels) == sorted(expected_channels)
    assert test_conda_channel.platform == expected_platform


@patch("conda_vendor.conda_channel.improved_download")
def test_CondaChannel_fetch_and_filter_repodata(mock_download, conda_channel_fixture):

    fake_manifest_subset_metadata = {
        "repodata_url": "https://url1",
        "entries": [
            {"fn": "file1"},
            {"fn": "file2"},
            {"fn": "file3"},
        ],
    }
    fake_live_repo_data_json = {
        "info": {"subdir": "fake_subdir"},
        "packages": {
            "file1": {"id": 1},
            "badfile1": {"id": 2},
            "file2": {"id": 3},
            "badfile2": {"id": 4},
        },
        "packages.conda": {
            "file3": {"id": 5},
            "badfile3": {"id": 6},
            "file4": {"id": 7},
            "badfile4": {"id": 8},
        },
    }
    mock_download.return_value = mock_response(json_data=fake_live_repo_data_json)

    fake_conda_subdir = "fake_subdir"

    expected = {
        "info": {"subdir": "fake_subdir"},
        "packages": {
            "file1": {"id": 1},
            "file2": {"id": 3},
        },
        "packages.conda": {"file3": {"id": 5}},
    }
    expected_mock_call = call("https://url1")

    result = conda_channel_fixture.fetch_and_filter_repodata(
        fake_conda_subdir, fake_manifest_subset_metadata
    )

    assert mock_download.call_args == expected_mock_call
    assert mock_download.call_count == 1
    TestCase().assertDictEqual(result, expected)


@patch("conda_vendor.conda_channel.CondaChannel.fetch_and_filter_repodata")
def test_CondaChannel_get_all_repo_data(mock, conda_channel_fixture):

    platform = conda_channel_fixture.platform

    fake_repo_data_entry = {
        "info": {"subdir": f"{platform}"},
        "packages": {},
        "packages.conda": {},
    }

    expected_calls = [
        call(
            f"{platform}",
            {
                "repodata_url": f"https://conda.anaconda.org/main/{platform}/repodata.json",
                "entries": [
                    {
                        "url": f"https://conda.anaconda.org/main/{platform}/brotlipy-0.7.0-py39h27cfd23_1003.tar.bz2",
                        "name": "brotlipy",
                        "version": "0.7.0",
                        "channel": f"https://conda.anaconda.org/main/{platform}",
                        "purl": f"pkg:conda/brotlipy@0.7.0?url=https://conda.anaconda.org/main/{platform}/brotlipy-0.7.0-py39h27cfd23_1003.tar.bz2",
                    }
                ],
            },
        ),
        call("noarch", {"repodata_url": None, "entries": []}),
        call(f"{platform}", {"repodata_url": None, "entries": []}),
        call(
            "noarch",
            {
                "repodata_url": "https://conda.anaconda.org/conda-forge/noarch/repodata.json",
                "entries": [
                    {
                        "url": "https://conda.anaconda.org/conda-forge/noarch/ensureconda-1.4.1-pyhd8ed1ab_0.tar.bz2",
                        "name": "ensureconda",
                        "version": "1.4.1",
                        "channel": "https://conda.anaconda.org/conda-forge/noarch",
                        "purl": "pkg:conda/ensureconda@1.4.1?url=https://conda.anaconda.org/conda-forge/noarch/ensureconda-1.4.1-pyhd8ed1ab_0.tar.bz2",
                    }
                ],
            },
        ),
    ]

    expected_all_repodata = {
        "main": {
            f"{platform}": {
                "info": {"subdir": f"{platform}"},
                "packages": {},
                "packages.conda": {},
            },
            "noarch": {
                "info": {"subdir": f"{platform}"},
                "packages": {},
                "packages.conda": {},
            },
        },
        "conda-forge": {
            f"{platform}": {
                "info": {"subdir": f"{platform}"},
                "packages": {},
                "packages.conda": {},
            },
            "noarch": {
                "info": {"subdir": f"{platform}"},
                "packages": {},
                "packages.conda": {},
            },
        },
    }

    mock.return_value = fake_repo_data_entry

    result = conda_channel_fixture.get_all_repo_data()
    TestCase().assertListEqual(mock.call_args_list, expected_calls)
    TestCase().assertDictEqual(result, expected_all_repodata)


def test_CondaChannel_local_channel_name(conda_channel_fixture):
    expected = "local_TEST_CHANNEL_NAME"
    result = conda_channel_fixture.local_channel_name(chan="TEST_CHANNEL_NAME")
    assert expected == result


@patch("conda_vendor.conda_channel.CondaChannel.local_channel_name")
def test_CondaChannel_local_dir(mock, conda_channel_fixture):
    mock_local_dir_name = "local_TEST_CHANNEL_NAME"
    mock.return_value = mock_local_dir_name
    test_channel_name = "TEST_CHANNEL_NAME"
    test_subdir = "dummy-64"
    expected = conda_channel_fixture.channel_root / mock_local_dir_name / test_subdir
    result = conda_channel_fixture.local_dir(chan=test_channel_name, subdir=test_subdir)
    assert result == expected
    mock.assert_called_with(test_channel_name)


@patch("conda_vendor.conda_channel.CondaChannel.local_dir")
def test_CondaChannel_make_local_dir(mock, conda_channel_fixture):
    mock_local_dir_name = "local_TEST_CHANNEL_NAME"
    test_local_dir_subdir = "dummy-64"
    expected_path = (
        conda_channel_fixture.channel_root / mock_local_dir_name / test_local_dir_subdir
    )

    test_channel_name = "TEST_CHANNEL_NAME"
    mock.return_value = expected_path
    result = conda_channel_fixture.make_local_dir(
        chan=test_channel_name, subdir=test_local_dir_subdir
    )
    assert result == expected_path
    assert expected_path.exists()
    mock.assert_called_with("TEST_CHANNEL_NAME", "dummy-64")


@patch("conda_vendor.conda_channel.CondaChannel.make_local_dir")
def test_CondaChannel_write_arch_repo_data(mock_mkdir, conda_channel_fixture):
    new_dir = conda_channel_fixture.channel_root / "tmp"
    new_dir.mkdir(exist_ok=True, parents=True)
    new_file = new_dir / "repodata.json"

    assert not new_file.exists()

    expected_chan = "dummy_chan"
    expected_subdir = "dummy_subdir"
    expected = {"data": "garbage"}

    def on_mkdir(chan, subdir):
        assert chan == expected_chan
        assert subdir == expected_subdir
        return new_dir

    mock_mkdir.side_effect = on_mkdir

    conda_channel_fixture.write_arch_repo_data(
        chan=expected_chan, subdir=expected_subdir, repo_data=expected
    )

    with new_file.open("r") as f:
        result = json.load(f)

    TestCase().assertDictEqual(result, expected)


@patch("conda_vendor.conda_channel.CondaChannel.write_arch_repo_data")
@patch("conda_vendor.conda_channel.CondaChannel.get_all_repo_data")
def test_CondaChannel_write_repo_data(mock_get, mock_write, conda_channel_fixture):
    platform = conda_channel_fixture.platform
    fake_repo_data = {
        "chan1": {platform: {"data": 1}, "noarch": {"data": 2}},
        "chan2": {platform: {"data": 3}, "noarch": {"data": 4}},
    }
    expected_calls = [
        call("chan1", platform, {"data": 1}),
        call("chan1", "noarch", {"data": 2}),
        call("chan2", platform, {"data": 3}),
        call("chan2", "noarch", {"data": 4}),
    ]
    mock_get.return_value = fake_repo_data
    conda_channel_fixture.write_repo_data()
    TestCase().assertListEqual(mock_write.call_args_list, expected_calls)


def test_CondaChannel__calc_sha256():
    test_data = b"DUMMY"
    expected = hashlib.sha256(b"DUMMY").hexdigest()
    result = CondaChannel._calc_sha256(test_data)
    assert expected == result


@patch("conda_vendor.conda_channel.improved_download")
def test_CondaChannel_download_and_validate(mock, tmp_path):
    expected_raw = b"DUMMY_DATA"
    expected_path = tmp_path / "dummy.data"
    expected_hash = hashlib.sha256(expected_raw).hexdigest()
    expected_url = "https://should_have_been_a_doctor.com"
    mock.return_value = mock_response(content=expected_raw)
    CondaChannel.download_and_validate(
        out=expected_path, url=expected_url, sha256=expected_hash
    )
    with open(expected_path, "rb") as f:
        assert f.read() == expected_raw
    mock.assert_called_with(expected_url)
    assert mock.call_count == 1


@patch("conda_vendor.conda_channel.CondaChannel.make_local_dir")
@patch("conda_vendor.conda_channel.CondaChannel.download_and_validate")
def test_CondaChannel_download_arch_binaries(
    mock_download_and_validate, mock_make_local_dir, conda_channel_fixture, tmp_path
):
    platform = conda_channel_fixture.platform
    test_channel = "dummy"
    test_subdir = "dummy-64"
    test_entries = [
        {
            "channel": f"http://fake.com/main/{platform}",
            "url": f"https://fake.com/main/{platform}/name1",
            "fn": "name1",
            "sha256": "sha1",
        }
    ]

    mock_path = tmp_path / test_channel / test_subdir
    expected_name = "name1"
    expected_destination = mock_path / expected_name
    expected_download_and_validate_calls = (
        expected_destination,
        f"https://fake.com/main/{platform}/name1",
        "sha1",
    )
    mock_make_local_dir.return_value = mock_path
    conda_channel_fixture.download_arch_binaries(
        chan=test_channel, subdir=test_subdir, entries=test_entries
    )

    mock_download_and_validate.call_count == 1
    mock_make_local_dir.call_count == 1
    mock_make_local_dir.assert_called_with("dummy", "dummy-64")
    mock_download_and_validate.assert_called_with(*expected_download_and_validate_calls)


@patch("conda_vendor.conda_channel.CondaChannel.download_arch_binaries")
def test_CondaChannel_download_binaries(mock_download, conda_channel_fixture):

    platform = conda_channel_fixture.platform
    mock_extended_data = {
        "main": {
            f"{platform}": {
                "repodata_url": "https://url1",
                "entries": [{"id": 1}, {"id": 2}],
            },
            "noarch": {"repodata_url": "https://url2", "entries": [{"id": 3}]},
        },
        "conda-forge": {
            f"{platform}": {"repodata_url": None, "entries": []},
            "noarch": {"repodata_url": "https://url3", "entries": [{"id": 4}]},
        },
    }
    conda_channel_fixture.meta_manifest = mock_extended_data

    expected_calls = [
        call("main", platform, [{"id": 1}, {"id": 2}]),
        call("main", "noarch", [{"id": 3}]),
        call("conda-forge", platform, []),
        call("conda-forge", "noarch", [{"id": 4}]),
    ]

    conda_channel_fixture.download_binaries()

    actual_calls = mock_download.call_args_list
    TestCase().assertListEqual(expected_calls, actual_calls)
