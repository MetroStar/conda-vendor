from requests.adapters import urldefragauth
from conda_vendor.manifest import (
    MetaManifest,
    get_conda_platform,
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


@patch("struct.calcsize")
def test_get_conda_platform(mock_struct) -> None:
    test_platform = "linux"
    mock_struct.return_value = 4
    expected = "linux-32"
    result = get_conda_platform(test_platform)
    assert expected == result
    assert mock_struct.call_count == 1


def test_LockWrapper_init():
    lw = LockWrapper()
    assert isinstance(lw, LockWrapper)


@patch("conda_vendor.manifest.LockWrapper.parse")
def test_LockWrapper_parse(mock):
    test_args = ["dummy_path.yaml", "dummy-64"]
    LockWrapper.parse(*test_args)
    print(mock.call_args)
    mock.assert_called_once_with("dummy_path.yaml", "dummy-64")


def test_MetaManifest_init(minimal_environment, tmp_path):
    test_meta_manifest = MetaManifest(minimal_environment, manifest_root=tmp_path)
    expected_manifest_root = tmp_path
    expected_manifest = None
    expected_type = MetaManifest
    expected_env_deps = {
        "specs": ["python=3.9.5"],
        "channels": ["main"],
        "environment": {
            "name": "minimal_env",
            "channels": ["main"],
            "dependencies": ["python=3.9.5"],
        },
    }

    assert test_meta_manifest.platform is not None
    assert test_meta_manifest.manifest_root == expected_manifest_root
    assert test_meta_manifest.channels == ["main"]
    TestCase().assertDictEqual(expected_env_deps, test_meta_manifest.env_deps)


def test_MetaManifest_init_fail(minimal_environment_defaults):

    with pytest.raises(
        RuntimeError, match=r"default channels are not supported."
    ) as error:
        MetaManifest(minimal_environment_defaults)


@patch("conda_vendor.manifest.LockWrapper.solve")
def test_MetaManifest_solve_environment(mock, meta_manifest_fixture):
    platform = meta_manifest_fixture.platform
    mock_data = {"actions": {"FETCH": [{"DUMMY_KEY": "DUMMY_VAL"}], "LINK": []}}
    mock.return_value = mock_data
    expected = mock_data["actions"]["FETCH"]
    result = meta_manifest_fixture.solve_environment()
    assert mock.call_count == 1
    mock.assert_called_with(
        "conda",
        ["main", "conda-forge"],
        specs=["python=3.9.5", "conda-mirror=0.8.2"],
        platform=platform,
    )
    TestCase().assertDictEqual(result[0], expected[0])


def test_get_purl(meta_manifest_fixture):

    test_fetch_entry = {
        "url": "https://conda.anaconda.org/main/linux-64/bro_4_lyfe.tar.bz2",
        "name": "bros_4_lyfe",
        "version": "24.7",
    }

    expected_purl = f"pkg:conda/bros_4_lyfe@24.7?url=https://conda.anaconda.org/main/linux-64/bro_4_lyfe.tar.bz2"

    actual_purl = meta_manifest_fixture.get_purl(test_fetch_entry)

    assert expected_purl == actual_purl


def test_get_manifest(meta_manifest_fixture):
    test_meta_manifest = meta_manifest_fixture
    platform = meta_manifest_fixture.platform
    test_fetch_entries = [
        {
            "url": f"https://conda.anaconda.org/main/{platform}/brotlipy-0.7.0-py39h27cfd23_1003.tar.bz2",
            "name": "brotlipy",
            "version": "0.7.0",
            "channel": f"https://conda.anaconda.org/main/{platform}",
        },
        {
            "url": "https://conda.anaconda.org/conda-forge/noarch/ensureconda-1.4.1-pyhd8ed1ab_0.tar.bz2",
            "name": "ensureconda",
            "version": "1.4.1",
            "channel": "https://conda.anaconda.org/conda-forge/noarch",
        },
    ]

    test_env_deps_solution = {
        "actions": {
            "FETCH": test_fetch_entries,
            "LINK": [],
        }
    }

    test_meta_manifest.env_deps["solution"] = test_env_deps_solution

    expected_manifest = {
        "main": {
            "noarch": {"repodata_url": [], "entries": []},
            f"{platform}": {
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
        },
        "conda-forge": {
            "noarch": {
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
            f"{platform}": {"repodata_url": [], "entries": []},
        },
    }

    actual_manifest = meta_manifest_fixture.get_manifest()
    print("actual_manifest", actual_manifest)
    print("result", meta_manifest_fixture.get_manifest())
    TestCase().maxDiff = None
    TestCase().assertDictEqual(expected_manifest, actual_manifest)


def test_get_manifest_filename(meta_manifest_fixture):
    test_manifest_fixture = meta_manifest_fixture

    expected_default_filename = "vendor_manifest.yaml"
    actual_default_filename = test_manifest_fixture.get_manifest_filename()

    expected_custom_filename = "woah-johnny.yaml"
    actual_custom_filename = test_manifest_fixture.get_manifest_filename(
        "woah-johnny.yaml"
    )

    assert expected_default_filename == actual_default_filename
    assert expected_custom_filename == actual_custom_filename


def test_create_manifest(meta_manifest_fixture, tmp_path):
    test_manifest_fixture = meta_manifest_fixture
    platform = test_manifest_fixture.platform
    expected_manifest = {
        "main": {
            "noarch": {"repodata_url": [], "entries": []},
            f"{platform}": {
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
        },
        "conda-forge": {
            "noarch": {
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
            f"{platform}": {"repodata_url": [], "entries": []},
        },
    }
    expected_path = tmp_path / "vendor_manifest.yaml"
    test_manifest_fixture.manifest = expected_manifest
    test_manifest_fixture.create_manifest()

    with open(expected_path, "r") as f:
        actual_manifest = yaml.load(f, Loader=SafeLoader)

    TestCase().assertDictEqual(actual_manifest, expected_manifest)
