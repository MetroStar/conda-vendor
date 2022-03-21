from requests.adapters import urldefragauth
from conda_vendor.manifest import (
    MetaManifest,
    get_conda_platform,
    LockWrapper,
    combine_metamanifests,
    deduplicate_pkg_list,
    read_manifests,
    write_combined_manifest,
)
import pytest
from requests import Response
import hashlib
import json
from ruamel.yaml import YAML
from requests import Response
from unittest import TestCase
from unittest.mock import Mock, patch, call, mock_open
from yaml import safe_load
from yaml.loader import SafeLoader
from conda_lock.src_parser import VersionedDependency, Selectors
import os


@patch("struct.calcsize")
def test_get_conda_platform(mock_struct) -> None:
    test_platform = "linux"
    mock_struct.return_value = 4
    expected = "linux-32"
    result = get_conda_platform(test_platform)
    assert expected == result
    assert mock_struct.call_count == 1


def test_get_conda_platform_custom():
    test_platforms = ["linux-64", "linux-32", "win-64", "win-32", "osx-64"]
    expected_returns = ["linux-64", "linux-32", "win-64", "win-32", "osx-64"]

    actual_returns = [get_conda_platform(custom_platform=p) for p in test_platforms]
    assert set(actual_returns) == set(expected_returns)


def test_LockWrapper_init():
    lw = LockWrapper()
    assert isinstance(lw, LockWrapper)


@patch("conda_vendor.manifest.LockWrapper.parse")
def test_LockWrapper_parse(mock):
    test_args = ["dummy_path.yaml"]
    LockWrapper.parse(*test_args)
    mock.assert_called_once_with("dummy_path.yaml")


#TODO update to use Dependencies/VersionedDependencies
def test_MetaManifest_init(minimal_environment, tmp_path):
    test_meta_manifest = MetaManifest(minimal_environment, manifest_root=tmp_path)
    expected_manifest_root = tmp_path
    expected_manifest = None
    expected_type = MetaManifest
    # TODO: use Depencencies/VersionedDependencies
    python_dep = VersionedDependency(
            name='python',
            manager='conda'
            optional=False,
            category='main',
            extras=[],
            selectors=Selectors(platform=None),
            version='3.9.5.*',
            build=None)
    pip_dep = VersionedDependency(
            name='pip',
            manager='conda',
            optional=False,
            category='main',
            extras=[],
            selectors=Selectors(platform=None),
            version='22.*',
            build=None)
    expected_env_deps = {
        "dependencies": ["python=3.9.5", "pip"],
        "channels": ["main"],
    }
    
    print(test_meta_manifest.env_deps)
    assert test_meta_manifest.platform is not None
    assert test_meta_manifest.manifest_root == expected_manifest_root
    assert test_meta_manifest.channels == ["main"]
    #TestCase().assertDictEqual(expected_env_deps, test_meta_manifest.env_deps)


# TODO: update to use Dependencies/VersionedDependencies
#def test_MetaManifest_init_fail(minimal_environment_defaults):
#
#    with pytest.raises(
#        RuntimeError, match=r"default channels are not supported."
#    ) as error:
#        MetaManifest(minimal_environment_defaults)


#TODO: update to use Dependencies/VersionedDependencies
#@patch("conda_vendor.manifest.LockWrapper.solve")
#def test_MetaManifest_solve_environment(mock, meta_manifest_fixture):
#    platform = meta_manifest_fixture.platform
#    mock_data = {"actions": {"FETCH": [{"DUMMY_KEY": "DUMMY_VAL"}], "LINK": []}}
#    mock.return_value = mock_data
#    expected = mock_data["actions"]["FETCH"]
#    result = meta_manifest_fixture.solve_environment()
#    assert mock.call_count == 1
#    mock.assert_called_with(
#        "conda",
#        ["main", "conda-forge"],
#        specs=["python=3.9.5", "conda-mirror=0.8.2", "pip"],
#        platform=platform,
#    )
#    TestCase().assertDictEqual(result[0], expected[0])


def test_get_purl(meta_manifest_fixture):

    test_fetch_entry = {
        "url": "https://conda.anaconda.org/main/linux-64/bro_4_lyfe.tar.bz2",
        "name": "bros_4_lyfe",
        "version": "24.7",
    }

    expected_purl = f"pkg:conda/bros_4_lyfe@24.7?url=https://conda.anaconda.org/main/linux-64/bro_4_lyfe.tar.bz2"

    actual_purl = meta_manifest_fixture.get_purl(test_fetch_entry)

    assert expected_purl == actual_purl


# TODO: update to use Dependencies/VersionedDependencies
#def test_get_manifest(meta_manifest_fixture):
#    test_meta_manifest = meta_manifest_fixture
#    platform = meta_manifest_fixture.platform
#    test_fetch_entries = [
#        {
#            "url": f"https://conda.anaconda.org/main/{platform}/brotlipy-0.7.0-py39h27cfd23_1003.tar.bz2",
#            "name": "brotlipy",
#            "version": "0.7.0",
#            "channel": f"https://conda.anaconda.org/main/{platform}",
#        },
#        {
#            "url": "https://conda.anaconda.org/conda-forge/noarch/ensureconda-1.4.1-pyhd8ed1ab_0.tar.bz2",
#            "name": "ensureconda",
#            "version": "1.4.1",
#            "channel": "https://conda.anaconda.org/conda-forge/noarch",
#        },
#    ]
#
#    test_env_deps_solution = {
#        "actions": {
#            "FETCH": test_fetch_entries,
#            "LINK": [],
#        }
#    }
#
#    test_meta_manifest.env_deps["solution"] = test_env_deps_solution
#
#    expected_manifest = {
#        "main": {
#            "noarch": {"repodata_url": None, "entries": []},
#            f"{platform}": {
#                "repodata_url": f"https://conda.anaconda.org/main/{platform}/repodata.json",
#                "entries": [
#                    {
#                        "url": f"https://conda.anaconda.org/main/{platform}/brotlipy-0.7.0-py39h27cfd23_1003.tar.bz2",
#                        "name": "brotlipy",
#                        "version": "0.7.0",
#                        "channel": f"https://conda.anaconda.org/main/{platform}",
#                        "purl": f"pkg:conda/brotlipy@0.7.0?url=https://conda.anaconda.org/main/{platform}/brotlipy-0.7.0-py39h27cfd23_1003.tar.bz2",
#                    }
#                ],
#            },
#        },
#        "conda-forge": {
#            "noarch": {
#                "repodata_url": "https://conda.anaconda.org/conda-forge/noarch/repodata.json",
#                "entries": [
#                    {
#                        "url": "https://conda.anaconda.org/conda-forge/noarch/ensureconda-1.4.1-pyhd8ed1ab_0.tar.bz2",
#                        "name": "ensureconda",
#                        "version": "1.4.1",
#                        "channel": "https://conda.anaconda.org/conda-forge/noarch",
#                        "purl": "pkg:conda/ensureconda@1.4.1?url=https://conda.anaconda.org/conda-forge/noarch/ensureconda-1.4.1-pyhd8ed1ab_0.tar.bz2",
#                    }
#                ],
#            },
#            f"{platform}": {"repodata_url": None, "entries": []},
#        },
#    }
#
#    actual_manifest = meta_manifest_fixture.get_manifest()
#    TestCase().maxDiff = None
#    TestCase().assertDictEqual(expected_manifest, actual_manifest)


def test_get_manifest_filename(meta_manifest_fixture):
    test_manifest_fixture = meta_manifest_fixture

    expected_default_filename = "meta_manifest.yaml"
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
            "noarch": {"repodata_url": None, "entries": []},
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
            f"{platform}": {"repodata_url": None, "entries": []},
        },
    }
    expected_path = tmp_path / "meta_manifest.yaml"
    test_manifest_fixture.manifest = expected_manifest
    test_manifest_fixture.create_manifest()

    with open(expected_path, "r") as f:
        actual_manifest = YAML(typ="safe").load(f)

    TestCase().assertDictEqual(actual_manifest, expected_manifest)


def test_add_pip_question_mark(meta_manifest_fixture):
    os.environ["CONDA_ADD_PIP_AS_PYTHON_DEPENDENCY"] = "False"

    test_manifest = meta_manifest_fixture

    expected_for_false = False
    actual_for_false = test_manifest.add_pip_question_mark()

    os.environ["CONDA_ADD_PIP_AS_PYTHON_DEPENDENCY"] = "True"
    expected_for_true = True
    actual_for_true = test_manifest.add_pip_question_mark()

    assert expected_for_false == actual_for_false
    assert expected_for_true == actual_for_true

# TODO: update for Dependency/VersionedDependency
#def test_add_pip_dependency(meta_manifest_fixture):
#    mock_env_python = {
#        "channels": ["chronotrigger"],
#        "dependencies": ["python"],
#    }
#
#    expected_env = {
#        "channels": ["chronotrigger"],
#        "dependencies": ["python", "pip"],
#    }
#    meta_manifest_fixture.env_deps = mock_env_python
#    meta_manifest_fixture.add_pip_dependency()
#    result = meta_manifest_fixture.env_deps
#
#    TestCase().assertDictEqual(result, expected_env)


def test_deduplicate_pkg_list():
    test_pkg_list = [
        {"name": "pkg1", "sha256": "sha-example1"},
        {"name": "pgh2", "sha256": "sha-example2"},
        {"name": "pkg3", "sha256": "sha-example3"},
        {"name": "pkg2", "sha256": "sha-example2"},
    ]

    expected_pkg_list = [
        {"name": "pkg1", "sha256": "sha-example1"},
        {"name": "pgh2", "sha256": "sha-example2"},
        {"name": "pkg3", "sha256": "sha-example3"},
    ]

    actual_pkg_list = deduplicate_pkg_list(test_pkg_list)

    assert actual_pkg_list == expected_pkg_list


def test_combine_metamanifests(tmp_path):
    test_manifest1 = {
        "main": {
            "noarch": {"repodata_url": "main_example.com", "entries": []},
            "linux-64": {
                "repodata_url": "https://conda.anaconda.org/main/linux-64/repodata.json",
                "entries": [
                    {"name": "pkg1", "sha256": "sha-example1"},
                    {"name": "pgh2", "sha256": "sha-example2"},
                ],
            },
        },
        "conda-forge": {
            "noarch": {
                "repodata_url": "https://conda.anaconda.org/conda-forge/noarch/repodata.json",
                "entries": [{"name": "pkg3", "sha256": "sha-example3"}],
            },
            "linux-64": {"repodata_url": "forge_example.com", "entries": []},
        },
    }
    test_manifest2 = {
        "main": {
            "noarch": {"repodata_url": "main_example.com", "entries": []},
            "linux-64": {
                "repodata_url": f"https://conda.anaconda.org/main/linux-64/repodata.json",
                "entries": [
                    {"name": "pkg4", "sha256": "sha-example4"},
                    {"name": "pkg2", "sha256": "sha-example2"},
                ],
            },
        },
    }
    expected_return = {
        "main": {
            "noarch": {"repodata_url": "main_example.com", "entries": []},
            "linux-64": {
                "repodata_url": "https://conda.anaconda.org/main/linux-64/repodata.json",
                "entries": [
                    {"name": "pkg1", "sha256": "sha-example1"},
                    {"name": "pgh2", "sha256": "sha-example2"},
                    {"name": "pkg4", "sha256": "sha-example4"},
                ],
            },
        },
        "conda-forge": {
            "noarch": {
                "repodata_url": "https://conda.anaconda.org/conda-forge/noarch/repodata.json",
                "entries": [{"name": "pkg3", "sha256": "sha-example3"}],
            },
            "linux-64": {"repodata_url": "forge_example.com", "entries": []},
        },
    }

    manifest_path_1 = tmp_path / "test_manifest1.yaml"
    manifest_path_2 = tmp_path / "test_manifest2.yaml"
    test_manifests_list = [manifest_path_1, manifest_path_2]

    with open(manifest_path_1, "w") as f:
        YAML().dump(test_manifest1, f)

    with open(manifest_path_2, "w") as f:
        YAML().dump(test_manifest2, f)


    actual_return = combine_metamanifests(test_manifests_list)
    assert actual_return == expected_return


def test_read_manifests(tmp_path):
    yaml1 = {"key1": "value1"}
    yaml2 = {"key2": "value2"}

    yaml_path1 = tmp_path / "yaml1.yaml"
    yaml_path2 = tmp_path / "yaml2.yaml"

    with open(yaml_path1, "w") as f:
        YAML().dump(yaml1, f)

    with open(yaml_path2, "w") as f:
        YAML().dump(yaml2, f)

    expected_manifest_list = [yaml1, yaml2]
    actual_manifest_list = read_manifests([yaml_path1, yaml_path2])

    assert actual_manifest_list == expected_manifest_list


def test_write_combined_manifest(tmp_path):
    test_yaml = {"key1": "value1"}
    yaml_path = tmp_path / "test_yaml.yaml"

    write_combined_manifest(yaml_path, test_yaml)

    with open(yaml_path, "r") as f:

        actual_yaml = YAML(typ="safe").load(f)


    TestCase().assertDictEqual(actual_yaml, test_yaml)
